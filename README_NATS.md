# NATS Agent Communication Quick Start

## Overview

This project now includes a NATS-based communication system that enables agents to communicate like they're on Slack. Agents can send direct messages, make requests, hand off tasks, and broadcast announcements.

## Quick Start

### 1. Install Dependencies

```bash
source env/bin/activate
pip install nats-py
```

### 2. Start NATS Server

Using Docker:
```bash
docker run -p 4222:4222 -p 8222:8222 nats:latest
```

Or install NATS locally:
```bash
# macOS
brew install nats-server
nats-server

# Or download from https://nats.io/download/
```

### 3. Start LM Studio

- Open LM Studio
- Load a model (e.g., Qwen 3 32B)
- Start the server on `localhost:1234`

### 4. Run the Demo

```bash
python demo_nats_agents.py
```

## What You'll See

The demo creates three agents that communicate:

1. **Weather-Bot** - Specialized weather agent
2. **Task-Coordinator** - Routes tasks to appropriate agents
3. **General-Assistant** - Multi-purpose collaborative agent

The demo shows:
- Agents announcing their presence
- Broadcasting to all agents
- Direct messages between agents
- Request/response patterns
- Task handoffs with metadata

## Architecture

### Channel Structure

```
agents.all                    # All agents subscribe here
├── Announcements            # Agent joins/leaves
├── Heartbeats              # Status updates every 30s
└── Broadcasts              # System-wide messages

agents.direct.{name}         # Direct messages to specific agent
└── Kicks off agentic_run() automatically

agents.request.{name}        # Request/reply pattern
└── Synchronous communication with timeout

agents.handoff.{from}.to.{to}  # Task handoff tracking
```

### Message Format

```python
{
    "message_type": "request|response|handoff|announcement|heartbeat",
    "from_agent": "Agent-Name",
    "to_agent": "Target-Agent",
    "content": "Message content",
    "metadata": {"key": "value"},
    "timestamp": "ISO-8601",
    "message_id": "uuid",
    "in_reply_to": "parent-uuid",
    "priority": 1-5
}
```

## Using NATS in Your Agents

### Create a NATS-Enabled Agent

```python
from nats_ooda_agent import NATSOODAAgent

agent = NATSOODAAgent(
    name="My-Agent",
    instructions="You are a helpful assistant...",
    model="qwen/qwen3-32b",
    tools=your_tools
)

# Connect and run
await agent.run_with_nats(
    capabilities=["capability1", "capability2"],
    description="What this agent does"
)
```

### Communication Methods

```python
# Send direct message (async, kicks off agent)
await agent.send_direct_message(
    to_agent="Target-Agent",
    content="Please do this task...",
    metadata={"priority": "high"}
)

# Make request (sync, wait for response)
response = await agent.request_from_agent(
    to_agent="Target-Agent",
    content="What's the status?",
    timeout=10
)

# Hand off task
await agent.handoff_to_agent(
    to_agent="Target-Agent",
    content="Continuing this task...",
    metadata={"context": "..."}
)

# Broadcast to all
await agent.broadcast_message(
    content="System announcement",
    metadata={"type": "announcement"}
)
```

## Adding NATS to Existing Agents

To add NATS capabilities to any agent:

```python
from nats_agent_mixin import NATSAgentMixin

class MyAgent(NATSAgentMixin):
    def __init__(self, name, ...):
        self.name = name
        # ... your init code
        super().__init__()  # Initialize NATS mixin
    
    def run(self, message):
        # Your existing run method
        pass
    
    def agentic_run(self, message):
        # Your existing agentic_run method
        pass

# Use it
agent = MyAgent(...)
await agent.connect_nats(capabilities=[...], description="...")
```

## Configuration

### Environment Variables

```bash
export NATS_URL="nats://localhost:4222"  # NATS server URL
```

### Custom Configuration

```python
from nats_config import NATSConfig

custom_config = NATSConfig(
    nats_url="nats://remote-server:4222",
    connection_timeout=10,
    message_timeout=60
)

agent = NATSOODAAgent(..., nats_config=custom_config)
```

## Message Flow Examples

### Direct Message Flow
```
Agent A: "Please process this data"
   ↓ (publish to agents.direct.agent_b)
Agent B: Receives message
   ↓ (kicks off agentic_run)
Agent B: Processes autonomously
   ↓ (optional completion notification)
Agent A: Receives notification
```

### Request/Response Flow
```
Agent A: "What's the weather in Tokyo?"
   ↓ (request to agents.request.weather_bot)
Weather-Bot: Processes with run()
   ↓ (reply with weather data)
Agent A: Receives response within timeout
```

### Task Handoff Flow
```
Coordinator: "This task is for you"
   ↓ (handoff to agents.direct.specialist)
   ↓ (logged to agents.handoff.coordinator.to.specialist)
Specialist: Receives high-priority task
   ↓ (processes via agentic_run)
Specialist: "Task completed"
   ↓ (completion message back)
Coordinator: Acknowledges completion
```

## Monitoring

### NATS Monitoring UI

NATS provides a monitoring interface at `http://localhost:8222`

### Agent Discovery

All agents announce themselves and send heartbeats. You can track available agents by subscribing to `agents.all`:

```python
async def monitor_agents():
    nc = await nats.connect("nats://localhost:4222")
    
    async def message_handler(msg):
        message = AgentMessage.from_bytes(msg.data)
        if message.message_type in ["announcement", "heartbeat"]:
            print(f"{message.from_agent}: {message.metadata['status']}")
    
    await nc.subscribe("agents.all", cb=message_handler)
```

## Troubleshooting

### NATS Won't Start
```bash
# Check if port is in use
lsof -i :4222

# Check Docker container
docker ps
docker logs <container-id>
```

### Agents Not Connecting
```bash
# Verify NATS is running
nc -zv localhost 4222

# Check logs
tail -f logs/agent_activity.log
```

### Messages Not Received
- Verify agent names match exactly (case-sensitive)
- Check agent is connected (look for "Connected to NATS" in logs)
- Ensure recipient agent has `agentic_run()` or `run()` method

### LM Studio Issues
- Verify LM Studio is running
- Check model is loaded
- Confirm server is on port 1234

## Production Considerations

### Security
- Enable NATS authentication (token/user/pass/NKeys)
- Use TLS for encrypted connections
- Implement message signing
- Add rate limiting

### Scalability
- Use NATS clustering for HA
- Enable JetStream for message persistence
- Implement queue groups for load balancing
- Add monitoring and alerting

### Reliability
- Set up proper error handling
- Implement retry logic
- Add circuit breakers
- Use message acknowledgments

## Files Reference

- `nats_config.py` - Configuration and message formats
- `nats_agent_mixin.py` - Mixin class for NATS capabilities
- `nats_ooda_agent.py` - NATS-enabled OODA agent
- `demo_nats_agents.py` - Multi-agent demo
- `devlog/nats_agent_communication.md` - Detailed documentation

## Next Steps

1. Create specialized agents for your use case
2. Define agent capabilities and routing rules
3. Implement task workflows across multiple agents
4. Add monitoring and observability
5. Deploy to production with proper security

## Support

For detailed documentation, see `devlog/nats_agent_communication.md`

For NATS documentation, visit https://docs.nats.io/

