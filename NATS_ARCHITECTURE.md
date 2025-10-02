# NATS Agent Communication Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        NATS Message Broker                       │
│                     (localhost:4222)                             │
│                                                                  │
│  Channels:                                                       │
│  ├─ agents.all (broadcast)                                       │
│  ├─ agents.direct.{agent_name} (direct messages)                │
│  ├─ agents.request.{agent_name} (request/reply)                 │
│  ├─ agents.response.{agent}.{id} (responses)                    │
│  └─ agents.handoff.{from}.to.{to} (task handoffs)               │
└─────────────────────────────────────────────────────────────────┘
           ↑              ↑                    ↑
           │              │                    │
    ┌──────┴────┐  ┌──────┴────┐      ┌──────┴────┐
    │  Agent A  │  │  Agent B  │  ... │  Agent N  │
    │           │  │           │      │           │
    │ - OODA    │  │ - OODA    │      │ - OODA    │
    │ - Tools   │  │ - Tools   │      │ - Tools   │
    │ - NATS    │  │ - NATS    │      │ - NATS    │
    └───────────┘  └───────────┘      └───────────┘
```

## Component Layers

```
┌────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Weather Bot  │  │ Coordinator  │  │  Assistant   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                   Agent Framework Layer                     │
│  ┌──────────────────────────────────────────────────┐     │
│  │          NATSAgentMixin                          │     │
│  │  - connect_nats()                                │     │
│  │  - send_direct_message()                         │     │
│  │  - request_from_agent()                          │     │
│  │  - handoff_to_agent()                            │     │
│  │  - broadcast_message()                           │     │
│  └──────────────────────────────────────────────────┘     │
│                            ↕                               │
│  ┌──────────────────────────────────────────────────┐     │
│  │          NATSOODAAgent                           │     │
│  │  - run() / agentic_run()                         │     │
│  │  - prompt() / handle_tool_call()                 │     │
│  │  - consolidate_context()                         │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                  Configuration Layer                        │
│  ┌──────────────────────────────────────────────────┐     │
│  │          nats_config.py                          │     │
│  │  - NATSConfig (connection, channels)             │     │
│  │  - AgentMetadata (capabilities, status)          │     │
│  │  - AgentMessage (message format)                 │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                   Transport Layer                           │
│  ┌──────────────────────────────────────────────────┐     │
│  │          NATS Client (nats.py)                   │     │
│  │  - TCP connections                                │     │
│  │  - Pub/Sub                                       │     │
│  │  - Request/Reply                                 │     │
│  │  - Auto-reconnect                                │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                     NATS Server                             │
│  - Message routing                                          │
│  - Topic/channel management                                 │
│  - Persistence (optional with JetStream)                    │
└────────────────────────────────────────────────────────────┘
```

## Message Flow Diagrams

### 1. Direct Message (Fire-and-Forget)

```
Agent A                    NATS Server              Agent B
   |                           |                        |
   |-- publish(direct.B) ----->|                        |
   |    "Do this task"         |                        |
   |                           |---- deliver ---------->|
   |                           |                        |
   |                           |                 [kicks off]
   |                           |                 agentic_run()
   |                           |                        |
   |                           |<-- publish(direct.A) --|
   |                           |    "Task complete"     |
   |<-------- deliver ---------|                        |
   |                           |                        |
```

### 2. Request/Response (Synchronous)

```
Agent A                    NATS Server              Agent B
   |                           |                        |
   |-- request(request.B) ---->|                        |
   |    "What's status?"       |                        |
   |    reply_inbox: _INBOX.X  |---- deliver ---------->|
   |                           |                        |
   |         [WAITING]         |                 [processes]
   |         timeout=10s       |                   run()
   |                           |                        |
   |                           |<---- publish(_INBOX.X) |
   |                           |      "Status: OK"      |
   |<-------- deliver ---------|                        |
   |                           |                        |
   [receives response]         |                        |
```

### 3. Broadcast (All Agents)

```
Agent A          NATS Server     Agent B    Agent C    Agent D
   |                 |               |          |          |
   |-- publish(all) ->|               |          |          |
   |  "Announcement"  |               |          |          |
   |                  |-- deliver --->|          |          |
   |                  |-- deliver ---------------->         |
   |                  |-- deliver --------------------------->
   |                  |               |          |          |
```

### 4. Task Handoff

```
Coordinator         NATS Server         Specialist
     |                   |                   |
     |-- publish(direct.specialist) -------->|
     |   type: handoff   |                   |
     |   priority: high  |                   |
     |                   |                   |
     |-- publish(handoff.coord.to.spec) --->|
     |   [for tracking]  |                   |
     |                   |            [receives high]
     |                   |            [priority task]
     |                   |            agentic_run()
     |                   |                   |
     |                   |<-- direct message |
     |<--- deliver ------|    "Completed"    |
```

## Agent Lifecycle

```
┌─────────────────┐
│  Agent Created  │
└────────┬────────┘
         │
         ↓
┌─────────────────────────┐
│ connect_nats()          │
│ - Connect to server     │
│ - Register metadata     │
│ - Subscribe to channels │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│ announce_presence()     │
│ - Broadcast to all      │
│ - Share capabilities    │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│ Background Tasks        │
│ ├─ Heartbeat loop      │
│ ├─ Message handler     │
│ └─ Agent processing    │
└────────┬────────────────┘
         │
         │ [Running]
         │
         ↓
┌─────────────────────────┐
│ disconnect_nats()       │
│ - Send offline msg      │
│ - Cancel tasks          │
│ - Close connection      │
└────────┬────────────────┘
         │
         ↓
┌─────────────────┐
│  Agent Stopped  │
└─────────────────┘
```

## Message Processing Pipeline

```
Incoming NATS Message
         │
         ↓
┌─────────────────────────┐
│ Subscription Callback   │
│ (_handle_*_message)     │
└────────┬────────────────┘
         │
         ↓
┌─────────────────────────┐
│ Parse AgentMessage      │
│ from bytes              │
└────────┬────────────────┘
         │
         ↓
    ┌────┴────┐
    │ Type?   │
    └────┬────┘
         │
    ┌────┼────────────┬────────────┐
    │    │            │            │
    ↓    ↓            ↓            ↓
[direct] [request] [handoff] [announcement]
    │    │            │            │
    ↓    ↓            ↓            ↓
agentic_ run()     agentic_    log/track
run()    + reply   run()
         │
         ↓
    [Background Task]
         │
         ↓
    [LLM Processing]
         │
         ↓
    [Tool Execution]
         │
         ↓
    [Response/Completion]
         │
         ↓
    [Send Reply/Notification]
```

## Channel Naming Convention

```
agents.all
  └─ All agents broadcast channel

agents.direct.{agent_name}
  ├─ agents.direct.weather_bot
  ├─ agents.direct.task_coordinator
  └─ agents.direct.general_assistant

agents.request.{agent_name}
  ├─ agents.request.weather_bot
  ├─ agents.request.task_coordinator
  └─ agents.request.general_assistant

agents.response.{agent}.{request_id}
  └─ agents.response.weather_bot.uuid-1234-5678

agents.handoff.{from}.to.{to}
  ├─ agents.handoff.coordinator.to.specialist
  └─ agents.handoff.specialist.to.coordinator
```

## Scaling Patterns

### Horizontal Scaling

```
         NATS Cluster
    ┌──────┬──────┬──────┐
    │      │      │      │
    │  N1  │  N2  │  N3  │
    │      │      │      │
    └───┬──┴───┬──┴───┬──┘
        │      │      │
    ┌───┴───┬──┴───┬──┴───┐
    │       │      │      │
  Agent   Agent  Agent  Agent
  Pool 1  Pool 2 Pool 3 Pool N
    │       │      │      │
  [A1]    [B1]   [C1]   [N1]
  [A2]    [B2]   [C2]   [N2]
  [A3]    [B3]   [C3]   [N3]
```

### Load Balancing (Queue Groups)

```
NATS Server
    │
    └─ agents.work.processing (queue group: workers)
         │
    ┌────┼────┬────┬────┐
    │    │    │    │    │
  Worker Worker Worker Worker
    1     2     3     N

Messages distributed round-robin
```

## Error Handling Flow

```
┌─────────────────┐
│ Message Arrives │
└────────┬────────┘
         │
         ↓
    ┌────────┐
    │ Parse  │
    └───┬────┘
        │
    ┌───┴───┐
    │ Error?│
    └───┬───┘
        │
    Yes ↓ No
  ┌─────┴──────┐
  │            │
  ↓            ↓
[Log]    [Process]
[Skip]   └───┬───┘
         │
     ┌───┴───┐
     │ Error?│
     └───┬───┘
         │
     Yes ↓ No
   ┌─────┴──────┐
   │            │
   ↓            ↓
[Log]      [Success]
[Retry?]   [Reply]
[Notify]
```

## Security Layers (Future)

```
┌────────────────────────────────────┐
│  Application Layer Security        │
│  - Message signing                 │
│  - Content validation              │
│  - Agent authorization             │
└────────────────────────────────────┘
              ↕
┌────────────────────────────────────┐
│  NATS Security                     │
│  - Authentication (NKeys/JWT)      │
│  - TLS encryption                  │
│  - Subject permissions             │
└────────────────────────────────────┘
              ↕
┌────────────────────────────────────┐
│  Network Security                  │
│  - Firewall rules                  │
│  - VPN/private network             │
│  - Rate limiting                   │
└────────────────────────────────────┘
```

## Data Structures

### AgentMetadata
```json
{
  "name": "Weather-Bot",
  "description": "Weather information specialist",
  "capabilities": ["weather_lookup", "temperature_info"],
  "tools": ["get_current_weather"],
  "status": "available",
  "model": "qwen/qwen3-32b",
  "version": "1.0.0",
  "registered_at": "2025-10-02T12:00:00Z",
  "last_heartbeat": "2025-10-02T12:05:30Z"
}
```

### AgentMessage
```json
{
  "message_type": "request",
  "from_agent": "Task-Coordinator",
  "to_agent": "Weather-Bot",
  "content": "What's the weather in Paris?",
  "metadata": {
    "user_id": "12345",
    "session_id": "abc-def"
  },
  "timestamp": "2025-10-02T12:05:45Z",
  "message_id": "uuid-1234-5678-90ab",
  "in_reply_to": null,
  "priority": 2
}
```

## Performance Characteristics

```
Latency Breakdown:
├─ NATS pub/sub: ~1ms
├─ Message parsing: <1ms
├─ Agent dispatch: <1ms
├─ LLM inference: 100-5000ms (variable)
├─ Tool execution: 10-1000ms (variable)
└─ Response send: ~1ms

Total: ~100-5000ms (LLM dominated)

Throughput:
├─ NATS: Millions msgs/sec
├─ Agent: 1-10 requests/sec (LLM limited)
└─ System: N * agent_throughput
```

## Monitoring Points

```
Agent Level:
├─ Messages received/sent
├─ Request/response latency
├─ Tool call frequency
├─ Error rates
└─ Agent uptime

NATS Level:
├─ Connection count
├─ Message throughput
├─ Subscription count
├─ Queue depth
└─ Server resources

System Level:
├─ Active agents
├─ End-to-end latency
├─ Task completion rate
├─ Error distribution
└─ Resource utilization
```

