"""
Trip Planner Agent with NATS Communication

This agent plans day trips to nearby cities. It uses NATS to communicate
with the Weather Agent to check weather conditions before making recommendations.
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


def get_nearby_cities(from_city: str) -> str:
    """Get a list of nearby cities for day trips"""
    # Simulated database of nearby cities
    city_recommendations = {
        "San Francisco": ["Napa Valley", "Berkeley", "San Jose", "Santa Cruz", "Monterey"],
        "Boston": ["Providence", "Portland ME", "Newport", "Cape Cod", "Salem"],
        "New York": ["Philadelphia", "Princeton", "New Haven", "Atlantic City", "The Hamptons"],
        "Los Angeles": ["San Diego", "Santa Barbara", "Palm Springs", "Big Bear", "Malibu"],
        "Seattle": ["Portland OR", "Vancouver BC", "Tacoma", "Bellingham", "Olympic National Park"],
    }
    
    nearby = city_recommendations.get(from_city, ["Wine Country", "Beach Town", "Mountain Resort"])
    return json.dumps({
        "from_city": from_city,
        "nearby_cities": nearby,
        "distance_range": "1-3 hours drive"
    })


def get_activities(city: str, weather_condition: str = "sunny") -> str:
    """Get recommended activities for a city based on weather"""
    
    outdoor_activities = [
        "hiking", "beach visit", "outdoor dining", "wine tasting", 
        "botanical gardens", "harbor cruise", "bike riding", "kayaking"
    ]
    
    indoor_activities = [
        "museum visit", "art gallery", "shopping", "indoor market",
        "aquarium", "historic sites", "restaurants", "theater"
    ]
    
    # Choose activities based on weather
    if "rain" in weather_condition.lower() or "cloud" in weather_condition.lower():
        activities = random.sample(indoor_activities, 3)
        note = "Indoor activities recommended due to weather"
    else:
        activities = random.sample(outdoor_activities, 2) + [random.choice(indoor_activities)]
        note = "Mix of outdoor and indoor activities"
    
    return json.dumps({
        "city": city,
        "weather": weather_condition,
        "recommended_activities": activities,
        "note": note
    })


class TripPlannerAgent(NATSAgentMixin):
    """
    Trip Planner Agent that uses NATS to communicate with Weather Agent.
    
    This agent:
    - Plans day trips to nearby cities
    - Checks weather via NATS communication with Weather Agent
    - Recommends activities based on weather conditions
    - Provides complete trip itineraries
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
        
        # Tool function registry
        self.tool_functions = {
            "get_nearby_cities": get_nearby_cities,
            "get_activities": get_activities
        }
        
        logger.info(f"TripPlannerAgent '{self.name}' initialized")
    
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
        if result and "</think>" in result:
            result = result.split("</think>")[1]
        
        print(result)
        
        # Handle tool calls if there are any
        if completion.choices[0].message.tool_calls:
            print("Tool calls found")
            for tool_call in completion.choices[0].message.tool_calls:
                messages = self.handle_tool_call(tool_call, messages)
        
        return messages
    
    def handle_tool_call(self, tool_call, messages):
        """Handle tool calls"""
        function_name = tool_call.function.name
        tool_call_arguments = json.loads(tool_call.function.arguments)
        
        result = None
        
        if function_name in self.tool_functions:
            # Call the tool function with the arguments
            tool_func = self.tool_functions[function_name]
            try:
                # Get the function parameters and call it
                if function_name == "get_nearby_cities":
                    result = tool_func(tool_call_arguments.get("from_city"))
                elif function_name == "get_activities":
                    result = tool_func(
                        tool_call_arguments.get("city"),
                        tool_call_arguments.get("weather_condition", "sunny")
                    )
            except Exception as error:
                logger.error(f"Error calling tool {function_name}: {error}")
                result = json.dumps({"error": str(error)})
        else:
            result = json.dumps({"error": f"Unknown tool: {function_name}"})
        
        messages.append({"role": "tool", "content": result})
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
        
        This method will automatically reach out to Weather Agent via NATS
        when planning trips.
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
        """
        try:
            # Connect to NATS
            await self.connect_nats(
                capabilities=capabilities or ["trip_planning", "activity_recommendations", "weather_aware_planning"],
                description=description or "Trip Planner Agent that checks weather before recommending destinations"
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


# Tool definitions for the Trip Planner
trip_planner_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_nearby_cities",
            "description": "Get a list of nearby cities that are good for day trips from a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_city": {
                        "type": "string",
                        "description": "The city you're starting from, e.g. 'San Francisco' or 'Boston'",
                    }
                },
                "required": ["from_city"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_activities",
            "description": "Get recommended activities for a destination city based on the weather conditions",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The destination city name",
                    },
                    "weather_condition": {
                        "type": "string",
                        "description": "The weather condition (sunny, rainy, cloudy, etc.)",
                    }
                },
                "required": ["city"],
            },
        }
    }
]


async def main():
    """Main entry point for running the Trip Planner agent"""
    agent = TripPlannerAgent(
        name="Trip-Planner",
        instructions=f"""
        You are an expert trip planning assistant that specializes in planning day trips to nearby cities.
        
        Your workflow:
        1. When a user asks for a day trip recommendation, first use get_nearby_cities to find options
        2. IMPORTANT: Before recommending any destination, you MUST check the weather by sending a NATS 
           request to the Weather-Bot agent. Use request_from_agent() to ask about the weather.
        3. Once you have the weather information, use get_activities to recommend activities
        4. Provide a complete day trip itinerary including:
           - Destination recommendation based on weather
           - Weather conditions
           - Recommended activities (weather-appropriate)
           - Estimated travel time
           - Best time to go
           - What to bring
        
        CRITICAL: You do NOT have a weather tool yourself. You MUST communicate with the Weather-Bot
        agent via NATS to get weather information. This is a demonstration of multi-agent communication.
        
        When checking weather, ask Weather-Bot: "What's the weather in [city name]?"
        
        Available tools:
        {json.dumps(trip_planner_tools, indent=2)}
        
        Remember: Always check weather with Weather-Bot via NATS before making recommendations!
        """,
        model="qwen/qwen3-32b",
        tools=trip_planner_tools
    )
    
    # Run the agent with NATS
    await agent.run_with_nats(
        capabilities=["trip_planning", "activity_recommendations", "multi_agent_coordination"],
        description="Trip planner that coordinates with Weather Agent for weather-aware recommendations"
    )


if __name__ == "__main__":
    asyncio.run(main())

