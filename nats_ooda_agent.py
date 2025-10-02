"""
NATS-enabled OODA Agent

This agent extends the basic OODA agent with NATS messaging capabilities,
allowing it to communicate with other agents via a Slack-like messaging system.
"""

from openai import OpenAI
import json
import random
import asyncio
import logging

from nats_agent_mixin import NATSAgentMixin
from nats_config import nats_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client for LM Studio
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")


def get_current_weather(location: str, unit: str = "celsius"):
    """Get the current weather for a location"""
    return f"The weather in {location} is Sunny and {random.randint(40, 80)} degrees {unit}."


class NATSOODAAgent(NATSAgentMixin):
    """
    OODA Agent with NATS messaging capabilities.
    
    This agent can:
    - Run autonomously using the OODA loop
    - Communicate with other agents via NATS
    - Receive direct messages and requests
    - Hand off tasks to other agents
    """
    
    def __init__(self, name: str, instructions: str, model: str, tools: list):
        self.name = name
        self.instructions = instructions
        self.messages = [
            {"role": "system", "content": self.instructions}
        ]
        self.model = model
        self.tools = tools
        
        # Initialize NATS mixin
        super().__init__(nats_config=nats_config)
        
        logger.info(f"NATSOODAAgent '{self.name}' initialized")
    
    def consolidate_context(self, messages):
        """Ask a language model to consolidate the context"""
        completion = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{
                "role": "user",
                "content": "Consolidate the following messages into a single message. Do not lose any information." + json.dumps(messages)
            }],
            tools=self.tools,
            tool_choice="auto"
        )
        
        # Recreate the messages list with the consolidated context
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": completion.choices[0].message.content}
        ]
        return messages
    
    def prompt(self, messages):
        """Send a prompt to the language model"""
        completion = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        print(completion.choices[0].message)
        result = completion.choices[0].message.content
        
        # Handle thinking tags
        if "</think>" in result:
            result = result.split("</think>")[1]
        
        print(result)
        
        # Handle tool calls if there are any
        if completion.choices[0].message.tool_calls:
            print("Tool calls found")
            for tool_call in completion.choices[0].message.tool_calls:
                messages = self.handle_tool_call(tool_call, messages)
        
        return messages
    
    def handle_tool_call(self, tool_call, messages):
        """Handle tool calls - Act phase of OODA"""
        for tool in self.tools:
            if tool.get("function").get("name") == tool_call.function.name:
                if tool_call.function.name == "get_current_weather":
                    tool_call_arguments = json.loads(tool_call.function.arguments)
                    result = get_current_weather(
                        tool_call_arguments.get("location"),
                        tool_call_arguments.get("unit", "celsius")
                    )
                    messages.append({"role": "tool", "content": result})
                    return messages
        
        return messages
    
    def run(self, kickoff_message):
        """Run the agent once with a kickoff message"""
        self.messages.append({"role": "user", "content": kickoff_message})
        results = self.prompt(self.messages)
        self.messages = results
        return self.messages
    
    def agentic_run(self, kickoff_message):
        """
        Run the agent with the OODA loop until completion.
        
        This method:
        1. Runs the kickoff message (Observe)
        2. Decides whether to continue (Orient/Decide)
        3. Acts and loops until complete
        """
        # First run the kickoff message
        self.messages.append({"role": "user", "content": kickoff_message})
        results = self.prompt(self.messages)
        self.messages = results
        
        # Then run the agentic loop
        continue_flag = "yes"
        
        while continue_flag == "yes":
            messages = self.messages.copy()  # Observe
            messages.append({
                "role": "user",
                "content": "Has the original kickoff prompt been completed, or should we continue? Respond with only yes (continue) or no (stop) with no other text."
            })
            results = self.prompt(messages)  # Decide
            continue_flag = results[-1].get("content", "").lower()
            
            if continue_flag == "no":
                break
            
            self.messages.append({
                "role": "user",
                "content": "Please continue with the original prompt."
            })  # Decide
            results = self.prompt(self.messages)  # Act
            self.messages = results
        
        return self.messages
    
    async def run_with_nats(self, capabilities=None, description=None):
        """
        Connect to NATS and run the agent, listening for messages.
        
        This method:
        1. Connects to NATS
        2. Announces presence
        3. Listens for incoming messages
        4. Keeps the agent running until interrupted
        """
        try:
            # Connect to NATS
            await self.connect_nats(
                capabilities=capabilities or ["weather", "general_assistance"],
                description=description or "OODA Loop Agent with tool calling capabilities"
            )
            
            logger.info(f"Agent '{self.name}' is now listening for messages on NATS")
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down agent...")
        except Exception as error:
            logger.error(f"Error in run_with_nats: {error}")
        finally:
            await self.disconnect_nats()


# Tool definitions
tools = [
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


async def main():
    """Main entry point for running the NATS OODA agent"""
    agent = NATSOODAAgent(
        name="Weather-Assistant",
        instructions=f"""
        You are a helpful assistant that can use function tools to help the user.
        You can use the get_current_weather tool for real-time access to the weather.
        
        When you receive a message via NATS from another agent, treat it as a request
        and fulfill it to the best of your ability using your available tools.
        
        Available tools:
        {json.dumps(tools, indent=2)}
        """,
        model="qwen/qwen3-32b",
        tools=tools
    )
    
    # Run the agent with NATS
    await agent.run_with_nats(
        capabilities=["weather_lookup", "general_assistance", "tool_calling"],
        description="Weather assistant agent that can look up weather information"
    )


if __name__ == "__main__":
    asyncio.run(main())

