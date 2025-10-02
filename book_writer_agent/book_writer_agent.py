import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI
from tavily import TavilyClient
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookWriterAgent:
    def __init__(self, name: str, model: str, working_directory: str = "./book_workspace", goal: str = "write a book about a given topic"):
        self.name = name
        self.model = model
        self.working_directory = Path(working_directory)
        self.working_directory.mkdir(exist_ok=True)
        self.goal = goal
        self.instructions = f"""
You are an expert book writer agent tasked with researching and writing a comprehensive book.
{self.goal}

Your capabilities include:
1. Web search using Tavily API for research
2. File management (read, write, update, list files)
3. Markdown file creation and management

Your workflow should follow these phases:

PHASE 1: RESEARCH & PLANNING
- Conduct comprehensive web research on the topic
- Create and maintain a research_notes.md file with all findings
- Develop a detailed book outline in book_outline.md
- Create a table of contents in table_of_contents.md

PHASE 2: CHAPTER DEVELOPMENT
- For each chapter, conduct specific research
- Write detailed chapter outlines
- Create individual chapter files (chapter_01.md, chapter_02.md, etc.)
- Maintain citations and sources in sources.md

PHASE 3: WRITING & REFINEMENT
- Write complete chapters based on research and outlines
- Continuously refine and improve content
- Ensure consistency in style, tone, and voice
- Cross-reference between chapters for coherence

PHASE 4: FINAL ASSEMBLY
- Review all chapters for completeness
- Create introduction.md and conclusion.md
- Assemble final book structure
- Perform final editing and quality checks

Key principles:
- Always cite sources and maintain research integrity
- Write in a clear, engaging style appropriate for the general audience
- Ensure logical flow and structure throughout the book
- Use markdown formatting for professional presentation
- Save all work incrementally to avoid data loss

Working directory: {working_directory}

Begin by conducting initial research on the topic and creating your research plan.
Save research plans in the research_plan.md file.
Save outlines in the outline.md file. The outline file helps you both keep track of the whole book's structure, and what you've researched, written, edited, iterated on, and finished.
Save the "situation report" in your outline.md file.
Save citations in the citations subfolder.

Please generate a tool call if needed.

"""
        
        
        # Initialize OpenAI client (LM Studio)
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
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
                    "name": "read_file",
                    "description": "Read the contents of a file in the working directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "The name of the file to read"
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
                    "description": "Write content to a file in the working directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "The name of the file to write to"
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
                    "name": "update_file",
                    "description": "Update or append content to an existing file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "The name of the file to update"
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to append or update"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["append", "replace"],
                                "description": "Whether to append to or replace the file content"
                            }
                        },
                        "required": ["filename", "content", "mode"]
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
            }
        ]

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
            response = requests.get(url)
            return response.text
        except Exception as e:
            logger.error(f"URL fetch error: {e}")
            return f"Error fetching URL: {str(e)}"

    def read_file(self, filename: str) -> str:
        """Read file from working directory"""
        try:
            file_path = self.working_directory / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"File '{filename}' does not exist in the working directory."
        except Exception as e:
            logger.error(f"File read error: {e}")
            return f"Error reading file '{filename}': {str(e)}"

    def write_file(self, filename: str, content: str) -> str:
        """Write content to file in working directory"""
        try:
            file_path = self.working_directory / filename
            with open(file_path, 'w') as f:
                f.write(content)
            return f"Successfully wrote content to '{filename}'"
        except Exception as e:
            logger.error(f"File write error: {e}")
            return f"Error writing to file '{filename}': {str(e)}"

    def update_file(self, filename: str, content: str, mode: str) -> str:
        """Update file content (append or replace)"""
        try:
            file_path = self.working_directory / filename
            
            if mode == "append":
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully appended content to '{filename}'"
            elif mode == "replace":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully replaced content in '{filename}'"
            else:
                return f"Invalid mode '{mode}'. Use 'append' or 'replace'."
        except Exception as e:
            logger.error(f"File update error: {e}")
            return f"Error updating file '{filename}': {str(e)}"

    def list_files(self) -> str:
        """List all files in working directory"""
        try:
            files = []
            for file_path in self.working_directory.iterdir():
                if file_path.is_file():
                    files.append({
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            return json.dumps(files, indent=2)
        except Exception as e:
            logger.error(f"List files error: {e}")
            return f"Error listing files: {str(e)}"

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
        elif function_name == "read_file":
            result = self.read_file(filename=arguments.get("filename"))
        elif function_name == "write_file":
            result = self.write_file(
                filename=arguments.get("filename"),
                content=arguments.get("content")
            )
        elif function_name == "update_file":
            result = self.update_file(
                filename=arguments.get("filename"),
                content=arguments.get("content"),
                mode=arguments.get("mode")
            )
        elif function_name == "list_files":
            result = self.list_files()
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
                "content": f"Consolidate the following conversation into a concise summary that preserves all important information, decisions, and context about the book writing project: {". ".join([json.dumps(message.get("content")) for message in messages])}"
            }],
            tools=self.tools,
            tool_choice="auto"
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
            print(completion.choices[0].message)
            
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
                "content": "Has the original book writing task been completed, or should we continue? Respond with only 'yes' (continue) or 'no' (stop) with no other text."
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
                "content": "Please continue with the book writing task. Focus on the next logical step in your plan."
            })
            self.messages = self.prompt(self.messages)
            
            iterations += 1
            
            # Consolidate context if messages get too long
            if len(" ".join([json.dumps(message.get("content")) for message in self.messages])) > 50000:  # Rough token estimate
                logger.info("Consolidating context due to length")
                self.messages = self.consolidate_context(self.messages)
        
        if iterations >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations})")
        
        return self.messages


def create_book_writer_agent(topic: str, working_directory: str = "./book_workspace") -> BookWriterAgent:
    """Factory function to create a book writer agent for a specific topic"""
    
    

    agent = BookWriterAgent(
        name="Book Writer Agent",
        model="qwen/qwen3-32b",
        working_directory=working_directory,
        goal=f"write a comprehensive book about {topic} that is throughly researched and cites it's sources"
    )
    
    return agent


if __name__ == "__main__":
    # Example usage
    topic = "Cool hot rods from the 1970s"
    agent = create_book_writer_agent(topic)
    
    kickoff_message = f"""
    I want you to write a comprehensive book about '{topic}'. 
    You may have already begun this task, so check your working directory for any files that may be related to the task and orient yourself before beginning. 
    If you have not begun, please start by:

    1. Conducting initial research on the topic
    2. Creating a research plan
    3. Developing a preliminary book outline
    4. Setting up your working files
    
    Take your time to do thorough research and create a well-structured plan before beginning to write.
    """
    
    # Run the agent
    messages = agent.agentic_run(kickoff_message)
    
    print(f"\nBook writing session completed. Check the '{agent.working_directory}' directory for all generated files.")
