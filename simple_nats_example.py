"""
Simple NATS Agent Example

This is the simplest possible example of two agents communicating via NATS.
Use this as a starting point for your own multi-agent systems.
"""

import asyncio
import logging
from nats_ooda_agent import NATSOODAAgent, tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """
    Simple example: Two agents, one sends a message, the other receives and responds.
    """
    
    # Create Agent 1: The Sender
    sender = NATSOODAAgent(
        name="Sender",
        instructions="You are a helpful agent that can send messages to other agents.",
        model="qwen/qwen3-32b",
        tools=tools
    )
    
    # Create Agent 2: The Receiver
    receiver = NATSOODAAgent(
        name="Receiver",
        instructions="You are a helpful agent that receives messages and responds to them.",
        model="qwen/qwen3-32b",
        tools=tools
    )
    
    # Connect both agents to NATS
    logger.info("Connecting agents to NATS...")
    
    # Connect receiver first (so it's ready to receive)
    await receiver.connect_nats(
        capabilities=["receive_messages"],
        description="A simple receiver agent"
    )
    
    # Connect sender
    await sender.connect_nats(
        capabilities=["send_messages"],
        description="A simple sender agent"
    )
    
    # Wait a moment for connections to stabilize
    await asyncio.sleep(1)
    
    logger.info("\n" + "="*60)
    logger.info("Example 1: Direct Message (async)")
    logger.info("="*60)
    
    # Send a direct message (fire-and-forget)
    await sender.send_direct_message(
        to_agent="Receiver",
        content="Hello! Can you help me with something?",
        metadata={"example": "direct_message"}
    )
    
    # Wait for receiver to process
    await asyncio.sleep(3)
    
    logger.info("\n" + "="*60)
    logger.info("Example 2: Request/Response (sync)")
    logger.info("="*60)
    
    # Send a request and wait for response
    response = await sender.request_from_agent(
        to_agent="Receiver",
        content="What's 2+2?",
        timeout=10
    )
    
    if response:
        logger.info(f"Sender received response: {response[:200]}")
    else:
        logger.warning("No response received")
    
    logger.info("\n" + "="*60)
    logger.info("Example 3: Broadcast")
    logger.info("="*60)
    
    # Broadcast to all agents
    await sender.broadcast_message(
        content="This is a broadcast message to all agents!",
        metadata={"example": "broadcast"}
    )
    
    await asyncio.sleep(2)
    
    logger.info("\n" + "="*60)
    logger.info("Examples complete! Press Ctrl+C to stop.")
    logger.info("="*60)
    
    # Keep agents running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down agents...")
    finally:
        await sender.disconnect_nats()
        await receiver.disconnect_nats()
        logger.info("Agents disconnected. Goodbye!")


if __name__ == "__main__":
    print("""
    ┌──────────────────────────────────────────────────────┐
    │         Simple NATS Agent Communication              │
    │                                                      │
    │  This demo shows the basics:                         │
    │  1. Direct messages (async)                          │
    │  2. Request/response (sync)                          │
    │  3. Broadcasting                                     │
    │                                                      │
    │  Prerequisites:                                      │
    │  - NATS: docker run -p 4222:4222 nats:latest        │
    │  - LM Studio running on localhost:1234              │
    │                                                      │
    │  Press Ctrl+C to stop                                │
    └──────────────────────────────────────────────────────┘
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo stopped by user")

