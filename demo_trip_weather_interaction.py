"""
Demo: Trip Planner and Weather Agent Interaction

This demo shows two agents communicating via NATS:
1. Weather-Bot: Provides weather information
2. Trip-Planner: Plans day trips and asks Weather-Bot for weather data

This demonstrates real multi-agent coordination where one agent needs
information from another agent to complete its task.
"""

import asyncio
import logging
from nats_ooda_agent import NATSOODAAgent, tools as weather_tools
from trip_planner_agent import TripPlannerAgent, trip_planner_tools

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_weather_agent():
    """Create the Weather Bot agent"""
    return NATSOODAAgent(
        name="Weather-Bot",
        instructions="""
        You are a weather specialist bot. Your primary function is to provide weather information.
        
        When you receive requests about weather:
        1. Use your get_current_weather tool to get the weather data
        2. Provide clear, concise weather information
        3. Always include the temperature and general conditions
        
        Be helpful and respond quickly to other agents requesting weather data.
        
        Available tools: get_current_weather(location, unit)
        """,
        model="qwen/qwen3-32b",
        tools=weather_tools
    )


def create_trip_planner():
    """Create the Trip Planner agent"""
    return TripPlannerAgent(
        name="Trip-Planner",
        instructions="""
        You are an expert trip planning assistant specializing in day trips to nearby cities.
        
        Your workflow when planning a trip:
        1. Use get_nearby_cities tool to find destination options
        2. CRITICAL: You MUST ask Weather-Bot for weather information via NATS before recommending
           - Use the request_from_agent method (it's available in your NATS capabilities)
           - Wait for Weather-Bot's response
           - Do NOT proceed without weather information
        3. Use get_activities tool to recommend activities based on the weather
        4. Provide a complete itinerary
        
        Example of checking weather:
        "I need to check the weather in [city]. Let me ask Weather-Bot..."
        Then call: await self.request_from_agent("Weather-Bot", "What's the weather in [city]?")
        
        You have two local tools: get_nearby_cities, get_activities
        You do NOT have a weather tool - you must ask Weather-Bot via NATS!
        
        Always be explicit about coordinating with Weather-Bot so users can see the interaction.
        """,
        model="qwen/qwen3-32b",
        tools=trip_planner_tools
    )


async def run_agent_instance(agent, capabilities, description):
    """Run an agent instance with NATS connectivity"""
    try:
        await agent.connect_nats(
            capabilities=capabilities,
            description=description
        )
        logger.info(f"✓ Agent {agent.name} is online and ready")
        
        # Keep agent running
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info(f"Agent {agent.name} is shutting down")
        await agent.disconnect_nats()
    except Exception as error:
        logger.error(f"Error running agent {agent.name}: {error}")
        await agent.disconnect_nats()


async def simulate_user_requests(trip_planner):
    """Simulate user requests to demonstrate the interaction"""
    
    # Wait for agents to connect and announce
    await asyncio.sleep(3)
    
    logger.info("\n" + "="*70)
    logger.info("SCENARIO 1: User asks Trip-Planner for a day trip from San Francisco")
    logger.info("="*70)
    logger.info("Watch as Trip-Planner coordinates with Weather-Bot...\n")
    
    # Send a direct message to Trip-Planner asking for a day trip
    await trip_planner.send_direct_message(
        "Trip-Planner",
        "I'm in San Francisco and want to plan a day trip for tomorrow. Can you recommend a nearby city and plan activities? I need you to check the weather first to make good recommendations.",
        metadata={"scenario": "1", "user": "demo_user"}
    )
    
    # Wait for the trip planner to process (it will contact Weather-Bot)
    logger.info("⏳ Waiting for Trip-Planner to coordinate with Weather-Bot...")
    await asyncio.sleep(8)
    
    logger.info("\n" + "="*70)
    logger.info("SCENARIO 2: Direct request/response pattern")
    logger.info("="*70)
    logger.info("Trip-Planner makes a direct request to Weather-Bot...\n")
    
    # Demonstrate Trip-Planner making a direct request to Weather-Bot
    response = await trip_planner.request_from_agent(
        "Weather-Bot",
        "What's the weather like in Napa Valley? I need to know for trip planning.",
        timeout=10
    )
    
    if response:
        logger.info(f"✓ Trip-Planner received weather data: {response[:150]}...")
    else:
        logger.warning("✗ No response from Weather-Bot")
    
    await asyncio.sleep(3)
    
    logger.info("\n" + "="*70)
    logger.info("SCENARIO 3: Planning another trip (Boston)")
    logger.info("="*70)
    
    await trip_planner.send_direct_message(
        "Trip-Planner",
        "I'm in Boston and want to visit a coastal town tomorrow. Check the weather and recommend the best destination with activities.",
        metadata={"scenario": "3", "user": "demo_user"}
    )
    
    await asyncio.sleep(8)
    
    logger.info("\n" + "="*70)
    logger.info("DEMO COMPLETE!")
    logger.info("="*70)
    logger.info("You've seen:")
    logger.info("  ✓ Trip-Planner receiving user requests")
    logger.info("  ✓ Trip-Planner asking Weather-Bot for weather data")
    logger.info("  ✓ Weather-Bot responding with weather information")
    logger.info("  ✓ Trip-Planner using weather data to plan trips")
    logger.info("")
    logger.info("Agents will continue running. Press Ctrl+C to stop.")
    logger.info("="*70 + "\n")


async def main():
    """Main demo orchestrator"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     Trip Planner & Weather Agent Interaction Demo               ║
    ║                                                                  ║
    ║  This demo shows real multi-agent coordination:                  ║
    ║                                                                  ║
    ║  Agents:                                                         ║
    ║  • Weather-Bot  - Provides weather information                   ║
    ║  • Trip-Planner - Plans trips, consults Weather-Bot             ║
    ║                                                                  ║
    ║  What you'll see:                                                ║
    ║  1. Both agents connecting to NATS                               ║
    ║  2. Trip-Planner receiving trip planning requests                ║
    ║  3. Trip-Planner requesting weather from Weather-Bot             ║
    ║  4. Weather-Bot responding with weather data                     ║
    ║  5. Trip-Planner using weather to make recommendations          ║
    ║                                                                  ║
    ║  Prerequisites:                                                  ║
    ║  • NATS server: docker run -p 4222:4222 nats:latest            ║
    ║  • LM Studio running on localhost:1234 with a model loaded      ║
    ║                                                                  ║
    ║  Press Ctrl+C to stop all agents                                 ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Starting multi-agent demo...")
    logger.info("Make sure NATS server is running on localhost:4222")
    logger.info("Make sure LM Studio is running on localhost:1234")
    logger.info("")
    
    # Create agents
    weather_bot = create_weather_agent()
    trip_planner = create_trip_planner()
    
    # Create tasks for each agent
    agent_tasks = [
        asyncio.create_task(run_agent_instance(
            weather_bot,
            capabilities=["weather_lookup", "temperature_info", "weather_forecasts"],
            description="Weather information provider for other agents"
        )),
        asyncio.create_task(run_agent_instance(
            trip_planner,
            capabilities=["trip_planning", "activity_recommendations", "multi_agent_coordination"],
            description="Trip planner that coordinates with Weather-Bot for weather-aware planning"
        )),
    ]
    
    # Create the demo scenario task
    demo_task = asyncio.create_task(simulate_user_requests(trip_planner))
    
    try:
        # Wait for all tasks
        await asyncio.gather(*agent_tasks, demo_task)
    except KeyboardInterrupt:
        logger.info("\n\nShutting down all agents...")
        
        # Cancel all tasks
        for task in agent_tasks + [demo_task]:
            task.cancel()
        
        # Wait for cleanup
        await asyncio.gather(*agent_tasks, demo_task, return_exceptions=True)
        
        logger.info("✓ All agents shut down successfully")
        logger.info("Goodbye!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("IMPORTANT: This demo requires two things running:")
    print("  1. NATS server on localhost:4222")
    print("  2. LM Studio on localhost:1234 with a model loaded")
    print("="*70 + "\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Demo terminated by user")

