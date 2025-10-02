"""
Interact with Trip Planner Agent

This script lets you send messages to the Trip Planner agent and see it
coordinate with the Weather Bot. Run this AFTER starting run_trip_weather_agents.py

Usage:
    Terminal 1: python run_trip_weather_agents.py
    Terminal 2: python interact_with_trip_planner.py
"""

import asyncio
import logging
import nats
from nats_config import AgentMessage, nats_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_trip_request(message: str):
    """Send a trip planning request to Trip-Planner"""
    
    # Connect to NATS
    nc = await nats.connect("nats://0.0.0.0:4222")
    logger.info("Connected to NATS")
    
    # Create message
    agent_message = AgentMessage(
        message_type="request",
        from_agent="User-Terminal",
        to_agent="Trip-Planner",
        content=message,
        priority=2
    )
    
    # Send to Trip-Planner's direct channel
    channel = nats_config.get_direct_channel("Trip-Planner")
    await nc.publish(channel, agent_message.to_bytes())
    
    logger.info(f"✓ Sent message to Trip-Planner: {message[:80]}...")
    logger.info("  Watch the other terminal to see Trip-Planner coordinate with Weather-Bot!")
    
    # Close connection
    await nc.close()


async def interactive_mode():
    """Interactive mode - keep asking for input"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     Interactive Trip Planner Client                        ║
    ║                                                           ║
    ║  Send trip planning requests to the Trip-Planner agent    ║
    ║  and watch it coordinate with Weather-Bot!                ║
    ║                                                           ║
    ║  Example requests:                                         ║
    ║  • "Plan a day trip from San Francisco"                   ║
    ║  • "I'm in Boston, recommend a coastal town visit"        ║
    ║  • "Suggest a day trip from Seattle with activities"      ║
    ║                                                           ║
    ║  Type 'quit' or 'exit' to stop                            ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    while True:
        try:
            message = input("\n📝 Your trip request (or 'quit'): ").strip()
            
            if message.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not message:
                continue
            
            await send_trip_request(message)
            print("✓ Message sent! Check the agents terminal for the interaction.\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as error:
            logger.error(f"Error: {error}")


async def quick_test():
    """Send some predefined test messages"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     Quick Test Mode                                        ║
    ║                                                           ║
    ║  Sending 3 test trip requests to Trip-Planner...          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    test_requests = [
        "I'm in San Francisco and want a day trip tomorrow. Check the weather and recommend a nearby city with activities.",
        "Plan a day trip from Boston to a coastal town. I need weather information first.",
        "I'm in Seattle - what's a good nearby city for a day trip? Please check the weather before recommending."
    ]
    
    for i, request in enumerate(test_requests, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Request {i}/3")
        logger.info(f"{'='*60}")
        await send_trip_request(request)
        await asyncio.sleep(2)
    
    logger.info(f"\n{'='*60}")
    logger.info("All test requests sent!")
    logger.info("Check the agents terminal to see the coordination.")
    logger.info(f"{'='*60}\n")


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        await quick_test()
    else:
        await interactive_mode()


if __name__ == "__main__":
    print("\n" + "="*65)
    print("Make sure run_trip_weather_agents.py is running first!")
    print("="*65 + "\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nStopped")

