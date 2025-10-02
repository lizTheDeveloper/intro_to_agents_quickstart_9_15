"""
Run Trip Planner and Weather Bot Agents

This script runs both agents and keeps them listening for NATS messages.
You can then use another script or the Python REPL to send messages to them.

Usage:
    Terminal 1: python run_trip_weather_agents.py
    Terminal 2: python interact_with_trip_planner.py
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


async def run_weather_bot():
    """Run the Weather Bot"""
    weather_bot = NATSOODAAgent(
        name="Weather-Bot",
        instructions="""
        You are a weather specialist bot. Your primary function is to provide weather information.
        
        When you receive requests about weather, use your get_current_weather tool to get the data.
        Provide clear, concise weather information including temperature and conditions.
        
        Be helpful and respond quickly to other agents requesting weather data.
        """,
        model="qwen/qwen3-32b",
        tools=weather_tools
    )
    
    await weather_bot.run_with_nats(
        capabilities=["weather_lookup", "temperature_info"],
        description="Weather information provider"
    )


async def run_trip_planner():
    """Run the Trip Planner"""
    trip_planner = TripPlannerAgent(
        name="Trip-Planner",
        instructions="""
        You are an expert trip planning assistant specializing in day trips.
        
        Your workflow:
        1. When asked for a day trip, use get_nearby_cities to find options
        2. IMPORTANT: Check weather by contacting Weather-Bot via NATS
           - You must use request_from_agent() to ask Weather-Bot
           - Example: await self.request_from_agent("Weather-Bot", "What's the weather in Napa?")
        3. Use get_activities to recommend activities based on weather
        4. Provide a complete itinerary
        
        You do NOT have a weather tool - you must coordinate with Weather-Bot!
        Always mention when you're checking weather with Weather-Bot so the coordination is visible.
        """,
        model="qwen/qwen3-32b",
        tools=trip_planner_tools
    )
    
    await trip_planner.run_with_nats(
        capabilities=["trip_planning", "activity_recommendations", "multi_agent_coordination"],
        description="Trip planner that coordinates with Weather-Bot"
    )


async def main():
    """Run both agents concurrently"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     Running Weather Bot and Trip Planner Agents            ║
    ║                                                            ║
    ║  Both agents are now listening on NATS                     ║
    ║                                                            ║
    ║  Agents running:                                           ║
    ║  • Weather-Bot  - answers weather queries                  ║
    ║  • Trip-Planner - plans trips, coordinates with Weather    ║
    ║                                                            ║
    ║  You can now interact with them:                           ║
    ║  1. From another terminal: python interact_with_trip_planner.py  ║
    ║  2. Send NATS messages directly                            ║
    ║  3. Watch the logs here to see the interaction             ║
    ║                                                            ║
    ║  Press Ctrl+C to stop both agents                          ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Starting both agents...")
    logger.info("Weather-Bot and Trip-Planner will announce their presence on NATS")
    logger.info("")
    
    # Run both agents concurrently
    try:
        await asyncio.gather(
            run_weather_bot(),
            run_trip_planner()
        )
    except KeyboardInterrupt:
        logger.info("\n\nShutting down agents...")
    except Exception as error:
        logger.error(f"Error: {error}")


if __name__ == "__main__":
    print("\n" + "="*65)
    print("Prerequisites:")
    print("  1. NATS server: docker run -p 4222:4222 nats:latest")
    print("  2. LM Studio on localhost:1234 with model loaded")
    print("="*65 + "\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Agents stopped")

