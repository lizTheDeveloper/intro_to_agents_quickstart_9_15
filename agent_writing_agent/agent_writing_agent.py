import os
import json
import logging
import requests
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI
from tavily import TavilyClient
try:
    from .config import AgentWritingConfig, AGENT_TEMPLATES
except ImportError:
    from config import AgentWritingConfig, AGENT_TEMPLATES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dangerous command patterns to block
BLOCKED_COMMAND_PATTERNS = [
    r'\brm\s+-rf\b',  # rm -rf
    r'\bmkfs\b',  # format filesystem
    r'\bdd\s+if=',  # disk copy
    r'\b>?\s*/dev/sd[a-z]',  # direct disk writes
    r'\bshutdown\b',  # system shutdown
    r'\breboot\b',  # system reboot
    r'\bkill\s+-9\s+1\b',  # kill init
    r'\bfork\s*bomb\b',  # fork bomb
    r':\(\)\{.*:\|:&\};:',  # fork bomb pattern
    r'\bchmod\s+777\s+/',  # dangerous permissions on root
    r'\bchown\s+.*\s+/',  # change ownership of root
    r'\bmv\s+.*\s+/etc',  # move files to system dirs
    r'\bmv\s+.*\s+/bin',
    r'\bmv\s+.*\s+/usr',
    r'\bmv\s+.*\s+/var',
    r'\brm\s+.*\s+/etc',  # delete system files
    r'\brm\s+.*\s+/bin',
    r'\brm\s+.*\s+/usr',
    r'\bcurl.*sudo',  # curl to sudo
    r'\bwget.*sudo',  # wget to sudo
]

class AgentWritingAgent:
    def __init__(self, name: str, model: str, working_directory: str = "./agent_workspace", goal: str = "create and manage AI agents"):
        self.name = name
        self.model = model
        self.working_directory = Path(working_directory).resolve()
        self.working_directory.mkdir(exist_ok=True)
        self.venv_path = self.working_directory / "venv"
        self.goal = goal

        # Ensure virtual environment exists
        self._setup_virtual_environment()
        self.instructions = f"""
You are an expert AI agent creator and manager. Your primary role is to design, create, and manage other AI agents based on user requirements.

Your capabilities include:
1. Web search using Tavily API for research on agent design patterns and best practices
2. URL fetching to gather documentation and examples
3. File management (read, write, update, list files) for creating agent code
4. Terminal command execution for testing agents, installing dependencies, and running commands
5. Agent architecture design and implementation
6. Code generation for Python-based AI agents

⚠️  CRITICAL SECURITY CONSTRAINTS - READ CAREFULLY ⚠️

FILE OPERATIONS:
- ALL file operations are STRICTLY CONFINED to: {self.working_directory}
- You CANNOT read or write files outside this directory
- Paths with ".." or absolute paths outside the working directory will be BLOCKED
- This is enforced automatically - attempts to escape will fail

PYTHON PACKAGE INSTALLATION:
- A virtual environment is set up at: {self.venv_path}
- ALWAYS use the virtual environment for pip install commands
- Use: source {self.venv_path}/bin/activate && pip install <package>
- NEVER install packages globally with pip
- NEVER run pip commands without activating the virtual environment first

TERMINAL COMMANDS:
- Dangerous system commands (rm -rf, mkfs, dd, shutdown, etc.) are BLOCKED
- You cannot modify system directories (/etc, /bin, /usr, /var)
- You cannot change permissions or ownership of system files
- All commands run from the working directory by default
- Commands are monitored and logged for security

ALLOWED OPERATIONS:
✓ Create and modify files within {self.working_directory}
✓ Install Python packages in the virtual environment
✓ Run safe commands (git, ls, cat, python, pytest, etc.)
✓ Test and validate generated agents
✓ Read and write agent code and documentation

BLOCKED OPERATIONS:
✗ File access outside {self.working_directory}
✗ Global pip installations
✗ Destructive system commands
✗ Modifying system files or directories
✗ Privilege escalation attempts

Your workflow should follow these phases:

PHASE 1: REQUIREMENTS ANALYSIS
- Understand the user's requirements for the new agent
- Research best practices and design patterns for the specific use case
- Identify necessary tools and capabilities for the agent
- Create a detailed specification document

PHASE 2: AGENT DESIGN
- Design the agent architecture based on requirements
- Select appropriate tools and APIs
- Create system prompts and instructions
- Plan the agent's workflow and decision-making process

PHASE 3: IMPLEMENTATION
- Generate the agent code using appropriate templates
- Implement required tools and functions
- Create configuration files and documentation
- Set up proper error handling and logging
- Use the virtual environment for any package installations

PHASE 4: TESTING & VALIDATION
- Create test scripts for the agent
- Validate functionality and performance
- Generate usage examples and documentation
- Provide deployment instructions

Key principles:
- Follow the OODA loop pattern (Observe, Orient, Decide, Act) for agent design
- Implement robust error handling and logging
- Use modular, maintainable code structure
- Include comprehensive documentation
- Follow Python best practices and conventions
- Ensure agents are secure and handle edge cases properly
- ALWAYS respect the security boundaries defined above

Working directory: {self.working_directory}
Virtual environment: {self.venv_path}

Available agent templates:
- basic_agent: Simple agent with core functionality
- web_enabled_agent: Agent with web search and URL fetching capabilities

You can create custom agents by combining and modifying these templates based on requirements.

Please generate tool calls as needed to research, design, and implement agents. Remember to respect all security constraints.
"""
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url=AgentWritingConfig.OPENAI_BASE_URL,
            api_key=AgentWritingConfig.OPENAI_API_KEY
        )
        
        # Initialize Tavily client
        tavily_api_key = AgentWritingConfig.TAVILY_API_KEY
        if tavily_api_key:
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
        else:
            self.tavily_client = None
            logger.warning("TAVILY_API_KEY not found in environment variables")
        
        # Initialize messages with system prompt
        self.messages = [
            {"role": "system", "content": self.instructions}
        ]
        
        # Define tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information using Tavily API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find information about"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of search results to return (default: 5)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_url",
                    "description": "Fetch the contents of a URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to fetch"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file. SECURITY: File must be within the working directory. Paths with '..' or absolute paths outside working directory will be rejected.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "The name of the file to read (relative to working directory)"
                            }
                        },
                        "required": ["filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. SECURITY: File must be within the working directory. Paths with '..' or absolute paths outside working directory will be rejected.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "The name of the file to write to (relative to working directory)"
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file"
                            }
                        },
                        "required": ["filename", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List all files in the working directory",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Execute a terminal command. SECURITY: Dangerous commands (rm -rf, mkfs, dd, shutdown, etc.) are BLOCKED. For pip install, use virtual environment: source venv/bin/activate && pip install <package>. Working directory must be within workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The terminal command to execute. For pip: use 'source venv/bin/activate && pip install <package>'"
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Optional working directory (must be within workspace, defaults to agent's working directory)"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_agent",
                    "description": "Create a new AI agent based on specifications",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "agent_name": {
                                "type": "string",
                                "description": "Name of the agent to create"
                            },
                            "agent_description": {
                                "type": "string",
                                "description": "Description of what the agent should do"
                            },
                            "template_type": {
                                "type": "string",
                                "enum": ["basic_agent", "web_enabled_agent"],
                                "description": "Type of agent template to use"
                            },
                            "tools": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of tools the agent should have"
                            },
                            "instructions": {
                                "type": "string",
                                "description": "Detailed instructions for the agent's behavior"
                            }
                        },
                        "required": ["agent_name", "agent_description", "template_type", "instructions"]
                    }
                }
            }
        ]

    def _setup_virtual_environment(self):
        """Set up a Python virtual environment for isolated package installation"""
        if not self.venv_path.exists():
            try:
                logger.info(f"Creating virtual environment at {self.venv_path}")
                subprocess.run(
                    ["python3", "-m", "venv", str(self.venv_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                logger.info("Virtual environment created successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create virtual environment: {e}")
                logger.warning("Continuing without virtual environment")
            except Exception as e:
                logger.error(f"Error setting up virtual environment: {e}")
                logger.warning("Continuing without virtual environment")

    def _validate_path(self, filename: str) -> Optional[Path]:
        """
        Validate that a file path is within the working directory.
        Returns the resolved path if valid, None if invalid.
        """
        try:
            # Create the full path
            file_path = self.working_directory / filename
            # Resolve to absolute path (follows symlinks, resolves ..)
            resolved_path = file_path.resolve()

            # Check if the resolved path is within working directory
            try:
                resolved_path.relative_to(self.working_directory)
                return resolved_path
            except ValueError:
                logger.error(f"Security violation: Path '{filename}' attempts to escape working directory")
                return None

        except Exception as e:
            logger.error(f"Path validation error for '{filename}': {e}")
            return None

    def _validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate that a command is safe to execute.
        Returns (is_valid, error_message).
        """
        # Check against blocked patterns
        for pattern in BLOCKED_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                error_msg = f"Security violation: Command blocked due to dangerous pattern. Command: '{command}'"
                logger.error(error_msg)
                return False, error_msg

        # Warn about pip install without virtual environment
        if re.search(r'\bpip3?\s+install\b', command, re.IGNORECASE):
            if 'venv/bin/activate' not in command and str(self.venv_path) not in command:
                warning_msg = (
                    f"WARNING: pip install detected without virtual environment activation. "
                    f"Consider using: source {self.venv_path}/bin/activate && {command}"
                )
                logger.warning(warning_msg)
                # Still allow but warn

        return True, ""

    def web_search(self, query: str, max_results: int = 5) -> str:
        """Perform web search using Tavily API"""
        if not self.tavily_client:
            return "Error: Tavily API client not initialized. Please set TAVILY_API_KEY environment variable."

        try:
            response = self.tavily_client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )

            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'score': result.get('score', 0)
                })

            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Error performing web search: {str(e)}"

    def fetch_url(self, url: str) -> str:
        """Fetch the contents of a URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"URL fetch error: {e}")
            return f"Error fetching URL: {str(e)}"

    def read_file(self, filename: str) -> str:
        """Read file from working directory with path validation"""
        try:
            # Validate path is within working directory
            file_path = self._validate_path(filename)
            if file_path is None:
                return f"Security Error: Cannot read '{filename}' - path is outside the working directory"

            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"File '{filename}' does not exist in the working directory."
        except Exception as e:
            logger.error(f"File read error: {e}")
            return f"Error reading file '{filename}': {str(e)}"

    def write_file(self, filename: str, content: str) -> str:
        """Write content to file in working directory with path validation"""
        try:
            # Validate path is within working directory
            file_path = self._validate_path(filename)
            if file_path is None:
                return f"Security Error: Cannot write to '{filename}' - path is outside the working directory"

            # Create subdirectories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote content to '{filename}'"
        except Exception as e:
            logger.error(f"File write error: {e}")
            return f"Error writing to file '{filename}': {str(e)}"

    def list_files(self) -> str:
        """List all files in working directory"""
        try:
            files = []
            for file_path in self.working_directory.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.working_directory)
                    files.append({
                        'name': str(relative_path),
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            return json.dumps(files, indent=2)
        except Exception as e:
            logger.error(f"List files error: {e}")
            return f"Error listing files: {str(e)}"

    def run_terminal_command(self, command: str, working_directory: str = None) -> str:
        """Execute a terminal command with security validation"""
        try:
            # Validate the command for dangerous patterns
            is_valid, error_msg = self._validate_command(command)
            if not is_valid:
                return json.dumps({
                    "command": command,
                    "error": error_msg,
                    "success": False
                }, indent=2)

            # Use the specified working directory or default to agent's working directory
            cwd = working_directory if working_directory else str(self.working_directory)

            # Validate working directory is within our workspace
            if working_directory:
                try:
                    cwd_path = Path(cwd).resolve()
                    cwd_path.relative_to(self.working_directory)
                except (ValueError, Exception) as e:
                    logger.error(f"Working directory '{cwd}' is outside the allowed workspace")
                    return json.dumps({
                        "command": command,
                        "error": f"Security Error: Working directory must be within {self.working_directory}",
                        "success": False
                    }, indent=2)

            # Log the command for security/audit purposes
            logger.info(f"Executing command: {command} in directory: {cwd}")

            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=(60 * 3)  # 3 min timeout
            )

            # Format the output
            output = {
                "command": command,
                "working_directory": cwd,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }

            if result.returncode == 0:
                logger.info(f"Command executed successfully: {command}")
            else:
                logger.warning(f"Command failed with exit code {result.returncode}: {command}")

            return json.dumps(output, indent=2)

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return json.dumps({
                "command": command,
                "error": "Command execution timed out after 3 minutes",
                "success": False
            }, indent=2)
        except Exception as e:
            logger.error(f"Terminal command error: {e}")
            return json.dumps({
                "command": command,
                "error": f"Error executing command: {str(e)}",
                "success": False
            }, indent=2)

    def create_agent(self, agent_name: str, agent_description: str, template_type: str, 
                    tools: List[str] = None, instructions: str = "") -> str:
        """Create a new AI agent based on specifications"""
        try:
            if tools is None:
                tools = []
            
            # Generate class name
            class_name = "".join(word.capitalize() for word in agent_name.replace("-", "_").replace(" ", "_").split("_"))
            if not class_name.endswith("Agent"):
                class_name += "Agent"
            
            # Generate working directory name
            working_dir = agent_name.lower().replace(" ", "_").replace("-", "_") + "_workspace"
            
            # Get template
            template = AGENT_TEMPLATES.get(template_type, AGENT_TEMPLATES["basic_agent"])
            
            # Generate tools configuration
            tools_config = []
            tool_handlers = []
            
            if "web_search" in tools or template_type == "web_enabled_agent":
                tools_config.append({
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "max_results": {"type": "integer", "description": "Max results (default: 5)"}
                            },
                            "required": ["query"]
                        }
                    }
                })
                tool_handlers.append('''if function_name == "web_search":
            result = self.web_search(
                query=arguments.get("query"),
                max_results=arguments.get("max_results", 5)
            )''')
            
            if "fetch_url" in tools or template_type == "web_enabled_agent":
                tools_config.append({
                    "type": "function",
                    "function": {
                        "name": "fetch_url",
                        "description": "Fetch contents of a URL",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "description": "URL to fetch"}
                            },
                            "required": ["url"]
                        }
                    }
                })
                tool_handlers.append('''elif function_name == "fetch_url":
            result = self.fetch_url(url=arguments.get("url"))''')
            
            if "read_file" in tools or template_type in ["basic_agent", "web_enabled_agent"]:
                tools_config.append({
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Read file contents",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "filename": {"type": "string", "description": "File to read"}
                            },
                            "required": ["filename"]
                        }
                    }
                })
                tool_handlers.append('''elif function_name == "read_file":
            result = self.read_file(filename=arguments.get("filename"))''')
            
            if "write_file" in tools or template_type in ["basic_agent", "web_enabled_agent"]:
                tools_config.append({
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "description": "Write content to file",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "filename": {"type": "string", "description": "File to write to"},
                                "content": {"type": "string", "description": "Content to write"}
                            },
                            "required": ["filename", "content"]
                        }
                    }
                })
                tool_handlers.append('''elif function_name == "write_file":
            result = self.write_file(
                filename=arguments.get("filename"),
                content=arguments.get("content")
            )''')
            
            if "list_files" in tools or template_type in ["basic_agent", "web_enabled_agent"]:
                tools_config.append({
                    "type": "function",
                    "function": {
                        "name": "list_files",
                        "description": "List files in working directory",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                })
                tool_handlers.append('''elif function_name == "list_files":
            result = self.list_files()''')
            
            # Add default handler
            tool_handlers.append('''else:
            result = f"Unknown function: {function_name}"''')
            
            # Format the template
            agent_code = template.format(
                class_name=class_name,
                agent_name=agent_name,
                working_dir=working_dir,
                goal=agent_description,
                instructions=instructions,
                tools=json.dumps(tools_config, indent=8),
                tool_handlers="\n        ".join(tool_handlers)
            )
            
            # Create agent directory
            agent_dir = self.working_directory / agent_name.lower().replace(" ", "_").replace("-", "_")
            agent_dir.mkdir(exist_ok=True)
            
            # Write agent file
            agent_file = agent_dir / f"{agent_name.lower().replace(' ', '_').replace('-', '_')}_agent.py"
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(agent_code)
            
            # Create __init__.py
            init_file = agent_dir / "__init__.py"
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(f'"""\\n{agent_description}\\n"""\\n\\nfrom .{agent_name.lower().replace(" ", "_").replace("-", "_")}_agent import {class_name}\\n\\n__all__ = ["{class_name}"]')
            
            # Create README
            readme_file = agent_dir / "README.md"
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(f"""# {agent_name}

{agent_description}

## Usage

```python
from {agent_name.lower().replace(' ', '_').replace('-', '_')}_agent import {class_name}

agent = {class_name}(
    name="{agent_name}",
    model="qwen/qwen3-32b"
)

# Run the agent
messages = agent.agentic_run("Your task here")
print("Task completed!")
```

## Tools

{', '.join(tools) if tools else 'Basic agent tools'}

## Configuration

Make sure to set up the required environment variables:
- TAVILY_API_KEY (if using web search)

## Generated on

{datetime.now().isoformat()}
""")
            
            return f"Successfully created agent '{agent_name}' in directory '{agent_dir}'"
            
        except Exception as e:
            logger.error(f"Agent creation error: {e}")
            return f"Error creating agent: {str(e)}"

    def handle_tool_call(self, tool_call, messages: List[Dict]) -> List[Dict]:
        """Handle tool calls and return updated messages"""
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        result = ""
        
        if function_name == "web_search":
            result = self.web_search(
                query=arguments.get("query"),
                max_results=arguments.get("max_results", 5)
            )
        elif function_name == "fetch_url":
            result = self.fetch_url(url=arguments.get("url"))
        elif function_name == "read_file":
            result = self.read_file(filename=arguments.get("filename"))
        elif function_name == "write_file":
            result = self.write_file(
                filename=arguments.get("filename"),
                content=arguments.get("content")
            )
        elif function_name == "list_files":
            result = self.list_files()
        elif function_name == "run_terminal_command":
            result = self.run_terminal_command(
                command=arguments.get("command"),
                working_directory=arguments.get("working_directory")
            )
        elif function_name == "create_agent":
            result = self.create_agent(
                agent_name=arguments.get("agent_name"),
                agent_description=arguments.get("agent_description"),
                template_type=arguments.get("template_type"),
                tools=arguments.get("tools", []),
                instructions=arguments.get("instructions", "")
            )
        else:
            result = f"Unknown function: {function_name}"
        
        # Add tool result to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })
        
        return messages

    def consolidate_context(self, messages: List[Dict]) -> List[Dict]:
        """Consolidate context when messages get too long"""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user", 
                "content": f"Consolidate the following conversation into a concise summary that preserves all important information about agent creation and management: {json.dumps([msg.get('content', '') for msg in messages])}"
            }]
        )
        
        consolidated_messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": completion.choices[0].message.content}
        ]
        
        return consolidated_messages

    def prompt(self, messages: List[Dict]) -> List[Dict]:
        """Send prompt to language model and handle response"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = completion.choices[0].message
            
            # Add assistant response to messages
            messages.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": response_message.tool_calls
            })
            
            # Handle tool calls if present
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    messages = self.handle_tool_call(tool_call, messages)
                
                # Get follow-up response after tool calls
                follow_up = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                messages.append({
                    "role": "assistant",
                    "content": follow_up.choices[0].message.content
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Prompt error: {e}")
            messages.append({
                "role": "assistant",
                "content": f"Error processing request: {str(e)}"
            })
            return messages

    def run(self, kickoff_message: str) -> List[Dict]:
        """Run a single interaction"""
        self.messages.append({"role": "user", "content": kickoff_message})
        self.messages = self.prompt(self.messages)
        return self.messages

    def agentic_run(self, kickoff_message: str, max_iterations: int = 20) -> List[Dict]:
        """Run the agent autonomously until task completion"""
        # Initial run
        self.messages.append({"role": "user", "content": kickoff_message})
        self.messages = self.prompt(self.messages)
        
        # Autonomous loop
        iterations = 0
        while iterations < max_iterations:
            # Check if task is complete
            check_messages = self.messages.copy()
            check_messages.append({
                "role": "user", 
                "content": "Has the original agent creation task been completed, or should we continue? Respond with only 'yes' (continue) or 'no' (stop) with no other text."
            })
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=check_messages
            )
            
            continue_flag = completion.choices[0].message.content.lower().strip()
            
            if continue_flag == "no":
                logger.info("Task completed successfully")
                break
            
            # Continue with the task
            self.messages.append({
                "role": "user", 
                "content": "Please continue with the agent creation task. Focus on the next logical step."
            })
            self.messages = self.prompt(self.messages)
            
            iterations += 1
            
            # Consolidate context if messages get too long
            if len(" ".join([json.dumps(message.get("content", "")) for message in self.messages])) > AgentWritingConfig.CONTEXT_CONSOLIDATION_THRESHOLD:
                logger.info("Consolidating context due to length")
                self.messages = self.consolidate_context(self.messages)
        
        if iterations >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations})")
        
        return self.messages


def create_agent_writing_agent(working_directory: str = "./agent_workspace") -> AgentWritingAgent:
    """Factory function to create an agent writing agent"""
    agent = AgentWritingAgent(
        name="Agent Writing Agent",
        model=AgentWritingConfig.DEFAULT_MODEL,
        working_directory=working_directory,
        goal="create and manage AI agents based on user requirements"
    )
    
    return agent


if __name__ == "__main__":
    # Example usage
    agent = create_agent_writing_agent()
    
    kickoff_message = """
    I want you to create a new AI agent that can help with data analysis tasks. 
    The agent should be able to:
    1. Search the web for data analysis techniques and best practices
    2. Read and write files for data processing
    3. Fetch URLs to gather datasets or documentation
    
    Please create this agent with appropriate tools and instructions.
    """
    
    # Run the agent
    messages = agent.agentic_run(kickoff_message)
    
    print(f"\nAgent creation session completed. Check the '{agent.working_directory}' directory for all generated files.")
