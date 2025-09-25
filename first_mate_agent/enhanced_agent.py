"""
Enhanced Agent class for First Mate Agent
Extends the original Agent with advanced capabilities
"""
import json
import random
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from .lm_client import lm_client
from .config import config
from .logger import logger


def get_current_weather(location: str, unit: str = "celsius") -> str:
    """Get current weather for a location"""
    return f"The weather in {location} is Sunny and {random.randint(40, 80)} degrees {unit}."


class EnhancedAgent:
    """Enhanced Agent with advanced capabilities"""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str = None,
        tools: List[Dict[str, Any]] = None,
        max_context_length: int = None
    ):
        self.name = name
        self.instructions = instructions
        self.model = model or config.lm_studio.model
        self.tools = tools or []
        self.max_context_length = max_context_length or config.agent.max_context_length
        self.context_consolidation_threshold = config.agent.context_consolidation_threshold
        
        # Initialize message history
        self.messages = [
            {"role": "system", "content": self.instructions}
        ]
        
        # Tool function registry
        self.tool_functions = {
            "get_current_weather": get_current_weather
        }
        
        logger.info(f"Enhanced Agent '{self.name}' initialized with {len(self.tools)} tools")
    
    def add_tool(self, tool_name: str, tool_function: Callable, tool_schema: Dict[str, Any]):
        """Add a new tool to the agent"""
        self.tools.append(tool_schema)
        self.tool_functions[tool_name] = tool_function
        logger.info(f"Added tool '{tool_name}' to agent")
    
    def consolidate_context(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Consolidate context when it gets too long"""
        try:
            # Use LM Studio to consolidate context
            consolidated_content = lm_client.consolidate_context(messages)
            
            # Recreate messages list with consolidated context
            consolidated_messages = [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": f"Previous conversation summary: {consolidated_content}"}
            ]
            
            logger.info("Context consolidated successfully")
            return consolidated_messages
            
        except Exception as error:
            logger.error(f"Context consolidation failed: {error}")
            # Fallback: keep only recent messages
            return messages[-10:] if len(messages) > 10 else messages
    
    def should_consolidate_context(self) -> bool:
        """Check if context should be consolidated"""
        total_tokens = sum(len(str(msg).split()) for msg in self.messages)
        return total_tokens > self.context_consolidation_threshold
    
    def prompt(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Process a prompt and handle tool calls"""
        try:
            # Check if context needs consolidation
            if self.should_consolidate_context():
                logger.info("Context length exceeded threshold, consolidating...")
                messages = self.consolidate_context(messages)
            
            # Get completion from LM Studio
            completion = lm_client.chat_completion(
                messages=messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto"
            )
            
            # Extract content and handle thinking tags
            content = completion["content"]
            if "<think>" in content and "</think>" in content:
                # Extract the response after thinking
                content = content.split("</think>")[-1].strip()
            
            logger.debug(f"Agent response: {content[:100]}...")
            
            # Add assistant response to messages
            messages.append({"role": "assistant", "content": content})
            
            # Handle tool calls if present
            if completion.get("tool_calls"):
                logger.info(f"Processing {len(completion['tool_calls'])} tool calls")
                for tool_call in completion["tool_calls"]:
                    messages = self.handle_tool_call(tool_call, messages)
            
            return messages
            
        except Exception as error:
            logger.error(f"Prompt processing failed: {error}")
            # Add error message to conversation
            messages.append({
                "role": "assistant", 
                "content": f"I encountered an error: {str(error)}. Please try again."
            })
            return messages
    
    def _extract_tool_calls_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from text response (since LM Studio library doesn't support them directly)"""
        tool_calls = []
        
        # Look for patterns like "I'll use get_current_weather(location='Boston')"
        import re
        
        for tool in self.tools:
            tool_name = tool["function"]["name"]
            # Simple pattern matching for tool calls
            pattern = rf"{tool_name}\s*\(\s*([^)]+)\s*\)"
            matches = re.findall(pattern, response, re.IGNORECASE)
            
            for match in matches:
                # Parse arguments (simple implementation)
                args = {}
                if match:
                    # Split by comma and parse key=value pairs
                    arg_pairs = match.split(',')
                    for pair in arg_pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip("'\"")
                            args[key] = value
                
                tool_calls.append({
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(args)
                    }
                })
        
        return tool_calls
    
    def handle_tool_call_from_text(self, tool_call: Dict[str, Any], messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Handle a tool call extracted from text"""
        try:
            tool_name = tool_call["function"]["name"]
            tool_arguments = json.loads(tool_call["function"]["arguments"])
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_arguments}")
            
            # Find and execute the tool function
            if tool_name in self.tool_functions:
                tool_function = self.tool_functions[tool_name]
                result = tool_function(**tool_arguments)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "content": str(result)
                })
                
                logger.info(f"Tool '{tool_name}' executed successfully")
            else:
                error_msg = f"Tool '{tool_name}' not found"
                logger.error(error_msg)
                messages.append({
                    "role": "tool",
                    "content": error_msg
                })
            
            return messages
            
        except Exception as error:
            logger.error(f"Tool call handling failed: {error}")
            messages.append({
                "role": "tool",
                "content": f"Tool execution failed: {str(error)}"
            })
            return messages
    
    def handle_tool_call(self, tool_call: Any, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Handle a tool call"""
        try:
            tool_name = tool_call.function.name
            tool_arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_arguments}")
            
            # Find and execute the tool function
            if tool_name in self.tool_functions:
                tool_function = self.tool_functions[tool_name]
                result = tool_function(**tool_arguments)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call.id
                })
                
                logger.info(f"Tool '{tool_name}' executed successfully")
            else:
                error_msg = f"Tool '{tool_name}' not found"
                logger.error(error_msg)
                messages.append({
                    "role": "tool",
                    "content": error_msg,
                    "tool_call_id": tool_call.id
                })
            
            return messages
            
        except Exception as error:
            logger.error(f"Tool call handling failed: {error}")
            messages.append({
                "role": "tool",
                "content": f"Tool execution failed: {str(error)}",
                "tool_call_id": tool_call.id
            })
            return messages
    
    def run(self, kickoff_message: str) -> List[Dict[str, str]]:
        """Run a single interaction"""
        logger.info(f"Running single interaction: {kickoff_message[:50]}...")
        
        self.messages.append({"role": "user", "content": kickoff_message})
        results = self.prompt(self.messages)
        self.messages = results
        
        return self.messages
    
    def agentic_run(self, kickoff_message: str, max_iterations: int = 10) -> List[Dict[str, str]]:
        """Run an agentic loop with automatic continuation"""
        logger.info(f"Starting agentic run: {kickoff_message[:50]}...")
        
        # Initial run
        self.messages.append({"role": "user", "content": kickoff_message})
        results = self.prompt(self.messages)
        self.messages = results
        
        # Agentic loop
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agentic iteration {iteration}/{max_iterations}")
            
            # Check if task is complete
            check_messages = self.messages.copy()
            check_messages.append({
                "role": "user", 
                "content": "Has the original task been completed? Respond with only 'yes' (completed) or 'no' (continue) with no other text."
            })
            
            try:
                completion = lm_client.chat_completion(check_messages)
                response = completion["content"].lower().strip()
                
                if "yes" in response:
                    logger.info("Task completed successfully")
                    break
                elif "no" in response:
                    # Continue with the task
                    self.messages.append({
                        "role": "user", 
                        "content": "Please continue working on the original task."
                    })
                    results = self.prompt(self.messages)
                    self.messages = results
                else:
                    logger.warning(f"Unexpected completion response: {response}")
                    break
                    
            except Exception as error:
                logger.error(f"Agentic loop error: {error}")
                break
        
        if iteration >= max_iterations:
            logger.warning(f"Agentic run reached maximum iterations ({max_iterations})")
        
        return self.messages
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        try:
            summary_prompt = (
                "Provide a concise summary of this conversation, including key decisions, "
                "actions taken, and current status. Focus on the most important points:\n\n"
                + "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages])
            )
            
            response = lm_client.chat_completion([
                {"role": "user", "content": summary_prompt}
            ])
            
            return response["content"]
            
        except Exception as error:
            logger.error(f"Failed to generate conversation summary: {error}")
            return "Unable to generate summary due to error."
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.messages = [{"role": "system", "content": self.instructions}]
        logger.info("Conversation reset")


# Default tools configuration
DEFAULT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        }
    }
]


# Create default agent instance
def create_default_agent() -> EnhancedAgent:
    """Create a default First Mate Agent instance"""
    return EnhancedAgent(
        name=config.agent.name,
        instructions=f"""
        You are a helpful assistant that can use function tools to help the user.
        You are part of the First Mate Agent system designed to assist users with various tasks.
        You can use the get_current_weather tool for real-time access to the weather.
        Always be helpful, accurate, and proactive in your assistance.
        """,
        tools=DEFAULT_TOOLS
    )
