"""
NATS Multi-Agent Communication Demo

This script demonstrates multiple agents communicating via NATS like a Slack system:
- Agents announce their presence
- Agents send direct messages
- Agents request information from each other
- Agents hand off tasks to each other
"""

import asyncio
import logging
from nats_ooda_agent import NATSOODAAgent, tools, client
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_weather_agent():
    """Create a weather-focused agent"""
    return NATSOODAAgent(
        name="Weather-Bot",
        instructions="""
        You are a weather specialist bot. Your primary function is to provide weather information.
        When you receive requests, always try to use your get_current_weather tool to provide accurate information.
        Be concise and helpful in your responses.
        
        Available tools:
        {tools}
        """.format(tools=json.dumps(tools, indent=2)),
        model="qwen/qwen3-32b",
        tools=tools
    )


def create_coordinator_agent():
    """Create a coordinator agent that can delegate to other agents"""
    return NATSOODAAgent(
        name="Task-Coordinator",
        instructions="""
        You are a task coordinator. Your job is to understand user requests and coordinate with other agents.
        
        When you receive a task:
        1. Analyze what type of task it is
        2. Identify which agent would be best suited to handle it
        3. Delegate or request information from the appropriate agent
        
        You can work with:
        - Weather-Bot: For weather-related queries
        - Other agents as they become available
        
        Be efficient and always acknowledge when you're delegating tasks.
        
        Available tools:
        {tools}
        """.format(tools=json.dumps(tools, indent=2)),
        model="qwen/qwen3-32b",
        tools=tools
    )


def create_general_assistant():
    """Create a general purpose assistant agent"""
    return NATSOODAAgent(
        name="General-Assistant",
        instructions="""
        You are a general purpose assistant. You can handle a variety of tasks and queries.
        When you don't have the capability to handle something, you can ask other agents for help.
        
        You can use the weather tool and coordinate with other agents as needed.
        
        Available tools:
        {tools}
        """.format(tools=json.dumps(tools, indent=2)),
        model="qwen/qwen3-32b",
        tools=tools
    )


async def run_agent_instance(agent, capabilities, description):
    """Run an agent instance with NATS connectivity"""
    try:
        await agent.connect_nats(
            capabilities=capabilities,
            description=description
        )
        logger.info(f"Agent {agent.name} is now online and listening")
        
        # Keep agent running
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info(f"Agent {agent.name} is shutting down")
        await agent.disconnect_nats()
    except Exception as error:
        logger.error(f"Error running agent {agent.name}: {error}")
        await agent.disconnect_nats()


async def demo_interaction(coordinator, weather_bot, assistant):
    """Demo script showing agent interactions"""
    await asyncio.sleep(2)  # Wait for agents to connect
    
    logger.info("\n" + "="*60)
    logger.info("DEMO: Coordinator broadcasting to all agents")
    logger.info("="*60)
    await coordinator.broadcast_message(
        "Hello all agents! I'm the new coordinator. Let's work together!",
        metadata={"demo": "broadcast"}
    )
    
    await asyncio.sleep(2)
    
    logger.info("\n" + "="*60)
    logger.info("DEMO: Coordinator sending direct message to Weather-Bot")
    logger.info("="*60)
    await coordinator.send_direct_message(
        "Weather-Bot",
        "What's the weather like in San Francisco today?",
        metadata={"demo": "direct_message"}
    )
    
    await asyncio.sleep(3)
    
    logger.info("\n" + "="*60)
    logger.info("DEMO: Assistant requesting information from Weather-Bot")
    logger.info("="*60)
    response = await assistant.request_from_agent(
        "Weather-Bot",
        "I need weather information for Tokyo and London. Can you help?",
        timeout=10
    )
    if response:
        logger.info(f"Assistant received response: {response[:100]}...")
    else:
        logger.warning("No response received from Weather-Bot")
    
    await asyncio.sleep(2)
    
    logger.info("\n" + "="*60)
    logger.info("DEMO: Coordinator handing off task to General-Assistant")
    logger.info("="*60)
    await coordinator.handoff_to_agent(
        "General-Assistant",
        "Please handle this user query: 'What's the weather in Paris and should I bring an umbrella?'",
        metadata={
            "demo": "handoff",
            "original_requester": "user",
            "priority": "high"
        }
    )
    
    await asyncio.sleep(3)
    
    logger.info("\n" + "="*60)
    logger.info("DEMO: General-Assistant requesting from Weather-Bot after handoff")
    logger.info("="*60)
    weather_response = await assistant.request_from_agent(
        "Weather-Bot",
        "What's the weather in Paris?",
        timeout=10
    )
    if weather_response:
        logger.info(f"Assistant got weather data: {weather_response[:100]}...")
        
        # Now assistant can respond back
        await assistant.send_direct_message(
            "Task-Coordinator",
            f"Task completed! Here's the weather info: {weather_response[:150]}...",
            metadata={"task_status": "completed"}
        )
    
    await asyncio.sleep(2)
    
    logger.info("\n" + "="*60)
    logger.info("DEMO COMPLETE - Agents will continue running")
    logger.info("Press Ctrl+C to stop all agents")
    logger.info("="*60)


async def main():
    """Main demo orchestrator"""
    logger.info("Starting NATS Multi-Agent Communication Demo")
    logger.info("Make sure NATS server is running on localhost:4222")
    logger.info("If not, run: docker run -p 4222:4222 -p 8222:8222 nats:latest")
    logger.info("")
    
    # Create agents
    weather_bot = create_weather_agent()
    coordinator = create_coordinator_agent()
    assistant = create_general_assistant()
    
    # Create tasks for each agent
    tasks = [
        asyncio.create_task(run_agent_instance(
            weather_bot,
            capabilities=["weather_lookup", "temperature_info"],
            description="Specialized weather information agent"
        )),
        asyncio.create_task(run_agent_instance(
            coordinator,
            capabilities=["task_coordination", "delegation", "routing"],
            description="Task coordinator that routes requests to appropriate agents"
        )),
        asyncio.create_task(run_agent_instance(
            assistant,
            capabilities=["general_assistance", "weather_lookup", "multi_agent_coordination"],
            description="General purpose assistant that can work with other agents"
        )),
    ]
    
    # Create demo interaction task
    demo_task = asyncio.create_task(demo_interaction(coordinator, weather_bot, assistant))
    tasks.append(demo_task)
    
    try:
        # Wait for all tasks
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("\nShutting down all agents...")
        for task in tasks:
            task.cancel()
        
        # Wait for cleanup
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All agents shut down successfully")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║         NATS Multi-Agent Communication Demo                    ║
    ║                                                                ║
    ║  This demo shows agents communicating like Slack:              ║
    ║  - Broadcasting announcements to all agents                    ║
    ║  - Sending direct messages                                     ║
    ║  - Making requests and getting responses                       ║
    ║  - Handing off tasks between agents                            ║
    ║                                                                ║
    ║  Prerequisites:                                                ║
    ║  - NATS server running on localhost:4222                       ║
    ║  - LM Studio running on localhost:1234                         ║
    ║                                                                ║
    ║  Press Ctrl+C to stop                                          ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo terminated by user")

