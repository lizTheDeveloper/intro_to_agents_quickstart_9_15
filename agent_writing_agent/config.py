"""
Configuration settings for the Agent Writing Agent
"""

import os
from pathlib import Path
from typing import Dict, Any

class AgentWritingConfig:
    """Configuration class for Agent Writing Agent"""
    
    # API Configuration
    OPENAI_BASE_URL ="https://api.groq.com/openai/v1"
    OPENAI_API_KEY = os.environ.get("GROQ_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Model Configuration
    DEFAULT_MODEL = "qwen/qwen3-32b"
    
    # Agent Configuration
    MAX_ITERATIONS = 30
    CONTEXT_CONSOLIDATION_THRESHOLD = 50000  # characters
    MAX_SEARCH_RESULTS = 10
    
    # File Configuration
    DEFAULT_WORKING_DIRECTORY = "agent_workspace"
    SUPPORTED_FILE_EXTENSIONS = ['.py', '.md', '.txt', '.json', '.yaml', '.yml']
    
    # Agent Creation Configuration
    DEFAULT_AGENT_TEMPLATE = "basic_agent"
    AGENT_TEMPLATES_DIR = "templates"
    
    @classmethod
    def get_working_directory(cls, agent_name: str) -> Path:
        """Generate working directory path based on agent name"""
        safe_name = "".join(c for c in agent_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_').lower()
        return Path(cls.DEFAULT_WORKING_DIRECTORY) / safe_name
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        if not cls.TAVILY_API_KEY:
            issues.append("TAVILY_API_KEY environment variable not set")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

# Agent templates
AGENT_TEMPLATES = {
    "basic_agent": """import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class {class_name}:
    def __init__(self, name: str, model: str, working_directory: str = "./{working_dir}", goal: str = "{goal}"):
        self.name = name
        self.model = model
        self.working_directory = Path(working_directory)
        self.working_directory.mkdir(exist_ok=True)
        self.goal = goal
        self.instructions = '''
{instructions}
'''
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )
        
        # Initialize messages with system prompt
        self.messages = [
            {{"role": "system", "content": self.instructions}}
        ]
        
        # Define tools
        self.tools = {tools}

    def handle_tool_call(self, tool_call, messages: List[Dict]) -> List[Dict]:
        \"\"\"Handle tool calls and return updated messages\"\"\"
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        result = ""
        
        {tool_handlers}
        
        # Add tool result to messages
        messages.append({{
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        }})
        
        return messages

    def consolidate_context(self, messages: List[Dict]) -> List[Dict]:
        \"\"\"Consolidate context when messages get too long\"\"\"
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{{
                "role": "user", 
                "content": f"Consolidate the following conversation into a concise summary that preserves all important information: {{json.dumps([msg.get('content', '') for msg in messages])}}"
            }}]
        )
        
        consolidated_messages = [
            {{"role": "system", "content": self.instructions}},
            {{"role": "user", "content": completion.choices[0].message.content}}
        ]
        
        return consolidated_messages

    def prompt(self, messages: List[Dict]) -> List[Dict]:
        \"\"\"Send prompt to language model and handle response\"\"\"
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = completion.choices[0].message
            
            # Add assistant response to messages
            messages.append({{
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": response_message.tool_calls
            }})
            
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
                
                messages.append({{
                    "role": "assistant",
                    "content": follow_up.choices[0].message.content
                }})
            
            return messages
            
        except Exception as e:
            logger.error(f"Prompt error: {{e}}")
            messages.append({{
                "role": "assistant",
                "content": f"Error processing request: {{str(e)}}"
            }})
            return messages

    def run(self, kickoff_message: str) -> List[Dict]:
        \"\"\"Run a single interaction\"\"\"
        self.messages.append({{"role": "user", "content": kickoff_message}})
        self.messages = self.prompt(self.messages)
        return self.messages

    def agentic_run(self, kickoff_message: str, max_iterations: int = 20) -> List[Dict]:
        \"\"\"Run the agent autonomously until task completion\"\"\"
        # Initial run
        self.messages.append({{"role": "user", "content": kickoff_message}})
        self.messages = self.prompt(self.messages)
        
        # Autonomous loop
        iterations = 0
        while iterations < max_iterations:
            # Check if task is complete
            check_messages = self.messages.copy()
            check_messages.append({{
                "role": "user", 
                "content": "Has the original task been completed, or should we continue? Respond with only 'yes' (continue) or 'no' (stop) with no other text."
            }})
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=check_messages
            )
            
            continue_flag = completion.choices[0].message.content.lower().strip()
            
            if continue_flag == "no":
                logger.info("Task completed successfully")
                break
            
            # Continue with the task
            self.messages.append({{
                "role": "user", 
                "content": "Please continue with the task. Focus on the next logical step."
            }})
            self.messages = self.prompt(self.messages)
            
            iterations += 1
            
            # Consolidate context if messages get too long
            if len(" ".join([json.dumps(message.get("content", "")) for message in self.messages])) > 50000:
                logger.info("Consolidating context due to length")
                self.messages = self.consolidate_context(self.messages)
        
        if iterations >= max_iterations:
            logger.warning(f"Reached maximum iterations ({{max_iterations}})")
        
        return self.messages

if __name__ == "__main__":
    # Example usage
    agent = {class_name}(
        name="{agent_name}",
        model="qwen/qwen3-32b"
    )
    
    # Run the agent
    messages = agent.agentic_run("Your task here")
    print("Task completed!")
""",

    "web_enabled_agent": """import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI
from tavily import TavilyClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class {class_name}:
    def __init__(self, name: str, model: str, working_directory: str = "./{working_dir}", goal: str = "{goal}"):
        self.name = name
        self.model = model
        self.working_directory = Path(working_directory)
        self.working_directory.mkdir(exist_ok=True)
        self.goal = goal
        self.instructions = '''
{instructions}
'''
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )
        
        # Initialize Tavily client
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if tavily_api_key:
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
        else:
            self.tavily_client = None
            logger.warning("TAVILY_API_KEY not found in environment variables")
        
        # Initialize messages with system prompt
        self.messages = [
            {{"role": "system", "content": self.instructions}}
        ]
        
        # Define tools
        self.tools = {tools}

    def web_search(self, query: str, max_results: int = 5) -> str:
        \"\"\"Perform web search using Tavily API\"\"\"
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
                results.append({{
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'score': result.get('score', 0)
                }})
            
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Web search error: {{e}}")
            return f"Error performing web search: {{str(e)}}"
    
    def fetch_url(self, url: str) -> str:
        \"\"\"Fetch the contents of a URL\"\"\"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"URL fetch error: {{e}}")
            return f"Error fetching URL: {{str(e)}}"

    def read_file(self, filename: str) -> str:
        \"\"\"Read file from working directory\"\"\"
        try:
            file_path = self.working_directory / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"File '{{filename}}' does not exist in the working directory."
        except Exception as e:
            logger.error(f"File read error: {{e}}")
            return f"Error reading file '{{filename}}': {{str(e)}}"

    def write_file(self, filename: str, content: str) -> str:
        \"\"\"Write content to file in working directory\"\"\"
        try:
            file_path = self.working_directory / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote content to '{{filename}}'"
        except Exception as e:
            logger.error(f"File write error: {{e}}")
            return f"Error writing to file '{{filename}}': {{str(e)}}"

    def list_files(self) -> str:
        \"\"\"List all files in working directory\"\"\"
        try:
            files = []
            for file_path in self.working_directory.iterdir():
                if file_path.is_file():
                    files.append({{
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }})
            return json.dumps(files, indent=2)
        except Exception as e:
            logger.error(f"List files error: {{e}}")
            return f"Error listing files: {{str(e)}}"

    def handle_tool_call(self, tool_call, messages: List[Dict]) -> List[Dict]:
        \"\"\"Handle tool calls and return updated messages\"\"\"
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        result = ""
        
        {tool_handlers}
        
        # Add tool result to messages
        messages.append({{
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        }})
        
        return messages

    def consolidate_context(self, messages: List[Dict]) -> List[Dict]:
        \"\"\"Consolidate context when messages get too long\"\"\"
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{{
                "role": "user", 
                "content": f"Consolidate the following conversation into a concise summary that preserves all important information: {{json.dumps([msg.get('content', '') for msg in messages])}}"
            }}]
        )
        
        consolidated_messages = [
            {{"role": "system", "content": self.instructions}},
            {{"role": "user", "content": completion.choices[0].message.content}}
        ]
        
        return consolidated_messages

    def prompt(self, messages: List[Dict]) -> List[Dict]:
        \"\"\"Send prompt to language model and handle response\"\"\"
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = completion.choices[0].message
            
            # Add assistant response to messages
            messages.append({{
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": response_message.tool_calls
            }})
            
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
                
                messages.append({{
                    "role": "assistant",
                    "content": follow_up.choices[0].message.content
                }})
            
            return messages
            
        except Exception as e:
            logger.error(f"Prompt error: {{e}}")
            messages.append({{
                "role": "assistant",
                "content": f"Error processing request: {{str(e)}}"
            }})
            return messages

    def run(self, kickoff_message: str) -> List[Dict]:
        \"\"\"Run a single interaction\"\"\"
        self.messages.append({{"role": "user", "content": kickoff_message}})
        self.messages = self.prompt(self.messages)
        return self.messages

    def agentic_run(self, kickoff_message: str, max_iterations: int = 20) -> List[Dict]:
        \"\"\"Run the agent autonomously until task completion\"\"\"
        # Initial run
        self.messages.append({{"role": "user", "content": kickoff_message}})
        self.messages = self.prompt(self.messages)
        
        # Autonomous loop
        iterations = 0
        while iterations < max_iterations:
            # Check if task is complete
            check_messages = self.messages.copy()
            check_messages.append({{
                "role": "user", 
                "content": "Has the original task been completed, or should we continue? Respond with only 'yes' (continue) or 'no' (stop) with no other text."
            }})
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=check_messages
            )
            
            continue_flag = completion.choices[0].message.content.lower().strip()
            
            if continue_flag == "no":
                logger.info("Task completed successfully")
                break
            
            # Continue with the task
            self.messages.append({{
                "role": "user", 
                "content": "Please continue with the task. Focus on the next logical step."
            }})
            self.messages = self.prompt(self.messages)
            
            iterations += 1
            
            # Consolidate context if messages get too long
            if len(" ".join([json.dumps(message.get("content", "")) for message in self.messages])) > 50000:
                logger.info("Consolidating context due to length")
                self.messages = self.consolidate_context(self.messages)
        
        if iterations >= max_iterations:
            logger.warning(f"Reached maximum iterations ({{max_iterations}})")
        
        return self.messages

if __name__ == "__main__":
    # Example usage
    agent = {class_name}(
        name="{agent_name}",
        model="qwen/qwen3-32b"
    )
    
    # Run the agent
    messages = agent.agentic_run("Your task here")
    print("Task completed!")
"""
}
