import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAnalystAgent:
    def __init__(self, name: str, model: str, working_directory: str = "./data_analyst_agent_workspace", goal: str = "Agent for reading CSV files, performing basic data analysis, and generating reports"):
        self.name = name
        self.model = model
        self.working_directory = Path(working_directory)
        self.working_directory.mkdir(exist_ok=True)
        self.goal = goal
        self.instructions = '''
When analyzing data files:
1. Use read_file to load CSV contents
2. Analyze using pandas (describe(), null value checks)
3. Generate summary statistics and write results
4. Include data quality checks in reports
'''
        
        # Initialize OpenAI client
        self.client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio"
        )
        
        # Initialize messages with system prompt
        self.messages = [
            {"role": "system", "content": self.instructions}
        ]
        
        # Define tools
        self.tools = [
        {
                "type": "function",
                "function": {
                        "name": "read_file",
                        "description": "Read file contents",
                        "parameters": {
                                "type": "object",
                                "properties": {
                                        "filename": {
                                                "type": "string",
                                                "description": "File to read"
                                        }
                                },
                                "required": [
                                        "filename"
                                ]
                        }
                }
        },
        {
                "type": "function",
                "function": {
                        "name": "write_file",
                        "description": "Write content to file",
                        "parameters": {
                                "type": "object",
                                "properties": {
                                        "filename": {
                                                "type": "string",
                                                "description": "File to write to"
                                        },
                                        "content": {
                                                "type": "string",
                                                "description": "Content to write"
                                        }
                                },
                                "required": [
                                        "filename",
                                        "content"
                                ]
                        }
                }
        },
        {
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
        }
]

    def handle_tool_call(self, tool_call, messages: List[Dict]) -> List[Dict]:
        """Handle tool calls and return updated messages"""
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        result = ""
        
        elif function_name == "read_file":
            result = self.read_file(filename=arguments.get("filename"))
        elif function_name == "write_file":
            result = self.write_file(
                filename=arguments.get("filename"),
                content=arguments.get("content")
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
                "content": f"Consolidate the following conversation into a concise summary that preserves all important information: {json.dumps([msg.get('content', '') for msg in messages])}"
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
                "content": "Has the original task been completed, or should we continue? Respond with only 'yes' (continue) or 'no' (stop) with no other text."
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
                "content": "Please continue with the task. Focus on the next logical step."
            })
            self.messages = self.prompt(self.messages)
            
            iterations += 1
            
            # Consolidate context if messages get too long
            if len(" ".join([json.dumps(message.get("content", "")) for message in self.messages])) > 50000:
                logger.info("Consolidating context due to length")
                self.messages = self.consolidate_context(self.messages)
        
        if iterations >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations})")
        
        return self.messages

if __name__ == "__main__":
    # Example usage
    agent = DataAnalystAgent(
        name="Data Analyst Agent",
        model="qwen/qwen3-32b"
    )
    
    # Run the agent
    messages = agent.agentic_run("Your task here")
    print("Task completed!")
