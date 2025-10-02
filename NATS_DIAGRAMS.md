# NATS Agent Communication - Mermaid Diagrams

This document contains visual diagrams explaining how agents connect and communicate via NATS.

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "NATS Message Broker"
        NATS[NATS Server<br/>localhost:4222]
        
        subgraph "Channels"
            ALL[agents.all<br/>broadcast]
            DM1[agents.direct.weather-bot]
            DM2[agents.direct.trip-planner]
            REQ1[agents.request.weather-bot]
            REQ2[agents.request.trip-planner]
        end
    end
    
    subgraph "Weather Bot Agent"
        WB[Weather Bot]
        WB_TOOL[get_current_weather]
        WB --> WB_TOOL
    end
    
    subgraph "Trip Planner Agent"
        TP[Trip Planner]
        TP_TOOL1[get_nearby_cities]
        TP_TOOL2[get_activities]
        TP --> TP_TOOL1
        TP --> TP_TOOL2
    end
    
    subgraph "User/Client"
        USER[User Terminal]
    end
    
    WB -.subscribe.-> ALL
    WB -.subscribe.-> DM1
    WB -.subscribe.-> REQ1
    
    TP -.subscribe.-> ALL
    TP -.subscribe.-> DM2
    TP -.subscribe.-> REQ2
    
    WB -.publish.-> ALL
    TP -.publish.-> ALL
    
    USER -->|send request| DM2
    TP -->|request weather| REQ1
    WB -->|reply weather| TP
    
    style NATS fill:#4A90E2,stroke:#333,stroke-width:4px,color:#fff
    style WB fill:#50C878,stroke:#333,stroke-width:2px
    style TP fill:#FFB347,stroke:#333,stroke-width:2px
    style USER fill:#9B59B6,stroke:#333,stroke-width:2px
```

## 2. Message Flow Sequence - Trip Planning Request

```mermaid
sequenceDiagram
    participant User
    participant NATS as NATS Server
    participant TP as Trip-Planner
    participant WB as Weather-Bot
    participant LLM as LM Studio

    Note over TP,WB: Both agents connect on startup
    TP->>NATS: connect()
    WB->>NATS: connect()
    
    TP->>NATS: subscribe(agents.all)
    TP->>NATS: subscribe(agents.direct.trip-planner)
    TP->>NATS: subscribe(agents.request.trip-planner)
    
    WB->>NATS: subscribe(agents.all)
    WB->>NATS: subscribe(agents.direct.weather-bot)
    WB->>NATS: subscribe(agents.request.weather-bot)
    
    TP->>NATS: announce presence
    WB->>NATS: announce presence
    NATS-->>TP: broadcast announcements
    NATS-->>WB: broadcast announcements
    
    Note over User,WB: User sends trip planning request
    
    User->>NATS: publish(agents.direct.trip-planner)<br/>"Plan day trip from SF"
    NATS->>TP: deliver message
    
    activate TP
    TP->>TP: agentic_run() kicks off
    TP->>TP: get_nearby_cities("San Francisco")
    TP->>TP: Needs weather data!
    
    Note over TP,WB: Trip-Planner requests weather from Weather-Bot
    
    TP->>NATS: request(agents.request.weather-bot)<br/>"What's weather in Napa?"
    NATS->>WB: deliver request
    
    activate WB
    WB->>WB: run() processes request
    WB->>WB: get_current_weather("Napa")
    WB->>LLM: generate response
    LLM-->>WB: formatted weather info
    WB->>NATS: reply("Sunny, 72°F")
    deactivate WB
    
    NATS->>TP: deliver weather response
    TP->>TP: get_activities("Napa", "sunny")
    TP->>LLM: generate itinerary
    LLM-->>TP: complete trip plan
    
    TP->>NATS: publish(agents.direct.user)<br/>Complete itinerary
    deactivate TP
    NATS->>User: deliver trip plan
```

## 3. Channel Architecture

```mermaid
graph LR
    subgraph "Broadcast Channel"
        ALL[agents.all]
        ALL_ANN[Announcements]
        ALL_HB[Heartbeats]
        ALL_SYS[System Messages]
        
        ALL --> ALL_ANN
        ALL --> ALL_HB
        ALL --> ALL_SYS
    end
    
    subgraph "Weather-Bot Channels"
        WB_DIRECT[agents.direct.weather-bot]
        WB_REQUEST[agents.request.weather-bot]
        WB_RESPONSE[agents.response.weather-bot.*]
        
        WB_DIRECT -.kickoff.-> AGENTIC_RUN[agentic_run]
        WB_REQUEST -.process.-> RUN[run + reply]
    end
    
    subgraph "Trip-Planner Channels"
        TP_DIRECT[agents.direct.trip-planner]
        TP_REQUEST[agents.request.trip-planner]
        TP_RESPONSE[agents.response.trip-planner.*]
        
        TP_DIRECT -.kickoff.-> AGENTIC_RUN2[agentic_run]
        TP_REQUEST -.process.-> RUN2[run + reply]
    end
    
    subgraph "Handoff Channels"
        HANDOFF[agents.handoff.*]
        H1[from.to.destination]
        HANDOFF --> H1
    end
    
    style ALL fill:#E74C3C,color:#fff
    style WB_DIRECT fill:#50C878,color:#fff
    style WB_REQUEST fill:#3498DB,color:#fff
    style TP_DIRECT fill:#FFB347,color:#333
    style TP_REQUEST fill:#9B59B6,color:#fff
    style HANDOFF fill:#F39C12,color:#fff
```

## 4. Agent Lifecycle Flow

```mermaid
stateDiagram-v2
    [*] --> Created: Agent instantiated
    Created --> Connecting: connect_nats()
    Connecting --> Connected: TCP connection established
    Connected --> Subscribing: Subscribe to channels
    Subscribing --> Announcing: announce_presence()
    Announcing --> Ready: Published to agents.all
    
    Ready --> Processing: Message received
    Processing --> Ready: Message handled
    
    Ready --> Requesting: request_from_agent()
    Requesting --> Waiting: Waiting for response
    Waiting --> Ready: Response received
    Waiting --> Ready: Timeout
    
    Ready --> Heartbeat: Every 30 seconds
    Heartbeat --> Ready: Heartbeat sent
    
    Ready --> Disconnecting: disconnect_nats()
    Disconnecting --> OfflineAnnounce: Send offline message
    OfflineAnnounce --> Closed: Connection closed
    Closed --> [*]
    
    note right of Ready
        Agent is actively listening
        for NATS messages on:
        - agents.all
        - agents.direct.{name}
        - agents.request.{name}
    end note
    
    note right of Processing
        Direct message triggers
        agentic_run() in background
        
        Request message triggers
        run() and sends reply
    end note
```

## 5. Request/Response Pattern

```mermaid
sequenceDiagram
    participant A as Trip-Planner
    participant N as NATS
    participant B as Weather-Bot
    
    Note over A,B: Synchronous Request/Response
    
    A->>A: Need weather data
    A->>N: request(agents.request.weather-bot)<br/>with reply_inbox
    activate A
    Note over A: Waiting...<br/>timeout=10s
    
    N->>B: deliver to subscriber
    activate B
    B->>B: parse request
    B->>B: run("What's weather in X?")
    B->>B: get_current_weather("X")
    B->>N: publish(reply_inbox)<br/>weather data
    deactivate B
    
    N->>A: deliver response
    deactivate A
    A->>A: continue processing
    
    Note over A,B: Alternative: Timeout
    
    A->>N: request(agents.request.weather-bot)
    activate A
    Note over A: Waiting...<br/>10 seconds
    Note over A: Timeout!
    deactivate A
    A->>A: handle timeout<br/>response = None
```

## 6. Multi-Agent Coordination Pattern

```mermaid
graph TD
    START([User Request]) --> TP[Trip-Planner<br/>Receives Request]
    TP --> PARSE[Parse Request:<br/>From SF, need trip]
    PARSE --> CITIES[Tool: get_nearby_cities]
    CITIES --> DECIDE{Need Weather<br/>for each city?}
    
    DECIDE -->|Yes| NATS_REQ[NATS Request<br/>to Weather-Bot]
    NATS_REQ --> WAIT[Wait for<br/>Weather Response]
    WAIT --> WEATHER[Receive Weather:<br/>Sunny, 72°F]
    
    WEATHER --> ACTIVITIES[Tool: get_activities<br/>based on weather]
    DECIDE -->|No| ACTIVITIES
    
    ACTIVITIES --> PLAN[Generate Trip Plan]
    PLAN --> LLM[LM Studio<br/>Format Response]
    LLM --> RESPOND[Send Complete<br/>Itinerary]
    RESPOND --> END([User Receives Plan])
    
    style START fill:#9B59B6,color:#fff
    style NATS_REQ fill:#E74C3C,color:#fff
    style WAIT fill:#F39C12,color:#333
    style WEATHER fill:#50C878,color:#fff
    style END fill:#3498DB,color:#fff
```

## 7. Component Interaction Map

```mermaid
graph TB
    subgraph "Infrastructure Layer"
        NATS[NATS Server<br/>Port 4222]
        LMS[LM Studio<br/>Port 1234]
    end
    
    subgraph "Agent Layer"
        subgraph "Weather-Bot"
            WB_MIXIN[NATSAgentMixin]
            WB_OODA[NATSOODAAgent]
            WB_TOOLS[Tools:<br/>get_current_weather]
            
            WB_OODA --> WB_MIXIN
            WB_OODA --> WB_TOOLS
        end
        
        subgraph "Trip-Planner"
            TP_MIXIN[NATSAgentMixin]
            TP_CLASS[TripPlannerAgent]
            TP_TOOLS[Tools:<br/>get_nearby_cities<br/>get_activities]
            
            TP_CLASS --> TP_MIXIN
            TP_CLASS --> TP_TOOLS
        end
    end
    
    subgraph "Configuration Layer"
        CONFIG[nats_config.py]
        CHANNELS[Channel Definitions]
        MESSAGES[Message Formats]
        METADATA[Agent Metadata]
        
        CONFIG --> CHANNELS
        CONFIG --> MESSAGES
        CONFIG --> METADATA
    end
    
    WB_MIXIN -.uses.-> CONFIG
    TP_MIXIN -.uses.-> CONFIG
    
    WB_MIXIN <-->|pub/sub| NATS
    TP_MIXIN <-->|pub/sub| NATS
    
    WB_OODA -->|API calls| LMS
    TP_CLASS -->|API calls| LMS
    
    TP_CLASS -.NATS request.-> WB_OODA
    
    style NATS fill:#4A90E2,color:#fff
    style LMS fill:#2ECC71,color:#fff
    style WB_MIXIN fill:#50C878,color:#fff
    style TP_MIXIN fill:#FFB347,color:#333
    style CONFIG fill:#95A5A6,color:#fff
```

## 8. Message Types & Routing

```mermaid
graph LR
    MSG[Agent Message] --> TYPE{Message Type}
    
    TYPE -->|announcement| ALL[agents.all<br/>All subscribers receive]
    TYPE -->|heartbeat| ALL
    
    TYPE -->|request| REQ[agents.request.{agent}<br/>Expects reply]
    REQ --> REPLY[Reply to inbox]
    
    TYPE -->|response| RESP[Direct to requester<br/>via reply channel]
    
    TYPE -->|handoff| HAND[agents.handoff.{from}.to.{to}<br/>AND<br/>agents.direct.{to}]
    HAND --> DIRECT[Kick off agent]
    
    TYPE -->|direct| DM[agents.direct.{agent}<br/>Async kickoff]
    DM --> AGENT_RUN[agentic_run]
    
    ALL --> SUB1[All agents<br/>listening]
    REPLY --> WAIT[Waiting requester]
    RESP --> ORIG[Original requester]
    DIRECT --> TARGET[Target agent]
    
    style MSG fill:#3498DB,color:#fff
    style ALL fill:#E74C3C,color:#fff
    style REQ fill:#9B59B6,color:#fff
    style DM fill:#FFB347,color:#333
    style HAND fill:#F39C12,color:#333
```

## 9. Data Flow - Complete Trip Planning

```mermaid
flowchart TD
    USER[User: Plan trip from SF] --> NATS1[NATS]
    NATS1 --> TP1[Trip-Planner<br/>receives on direct channel]
    
    TP1 --> CHECK1{Have<br/>destination?}
    CHECK1 -->|No| TOOL1[get_nearby_cities<br/>Returns: Napa, Berkeley, etc]
    CHECK1 -->|Yes| TOOL2
    
    TOOL1 --> SELECT[Select: Napa Valley]
    
    SELECT --> CHECK2{Have<br/>weather?}
    CHECK2 -->|No| NATS_OUT[NATS Request:<br/>agents.request.weather-bot]
    
    NATS_OUT --> WB1[Weather-Bot<br/>receives request]
    WB1 --> WB_TOOL[get_current_weather<br/>Napa Valley]
    WB_TOOL --> WB_LLM[LM Studio:<br/>Format response]
    WB_LLM --> NATS_BACK[NATS Reply:<br/>via reply inbox]
    
    NATS_BACK --> TP2[Trip-Planner<br/>receives weather]
    CHECK2 -->|Yes| TOOL2
    TP2 --> TOOL2[get_activities<br/>Napa, sunny]
    
    TOOL2 --> ACT_DATA[Activities:<br/>wine tasting,<br/>hiking, outdoor dining]
    
    ACT_DATA --> LLM2[LM Studio:<br/>Generate itinerary]
    LLM2 --> PLAN[Complete Trip Plan:<br/>- Destination: Napa<br/>- Weather: Sunny 72F<br/>- Activities: ...]
    
    PLAN --> NATS_FINAL[NATS:<br/>Response to user]
    NATS_FINAL --> USER_RECV[User receives<br/>complete itinerary]
    
    style USER fill:#9B59B6,color:#fff
    style NATS1 fill:#4A90E2,color:#fff
    style TP1 fill:#FFB347,color:#333
    style WB1 fill:#50C878,color:#fff
    style NATS_OUT fill:#E74C3C,color:#fff
    style PLAN fill:#2ECC71,color:#fff
    style USER_RECV fill:#3498DB,color:#fff
```

## 10. Network Topology

```mermaid
graph TB
    subgraph "Physical Machine: localhost"
        subgraph "Port 4222"
            NATS_SERVER[NATS Server Process<br/>PID: 99822]
        end
        
        subgraph "Port 1234"
            LM_STUDIO[LM Studio<br/>Qwen 3 32B Model]
        end
        
        subgraph "Python Processes"
            PROC1[run_trip_weather_agents.py<br/>Process 1]
            
            subgraph "Process 1 - Threads/Tasks"
                TASK1[asyncio Task:<br/>Weather-Bot]
                TASK2[asyncio Task:<br/>Trip-Planner]
            end
            
            PROC1 --> TASK1
            PROC1 --> TASK2
        end
        
        subgraph "Client Process"
            CLIENT[interact_with_trip_planner.py<br/>Terminal Client]
        end
    end
    
    TASK1 <-->|TCP/NATS Protocol| NATS_SERVER
    TASK2 <-->|TCP/NATS Protocol| NATS_SERVER
    CLIENT <-->|TCP/NATS Protocol| NATS_SERVER
    
    TASK1 <-->|HTTP/OpenAI API| LM_STUDIO
    TASK2 <-->|HTTP/OpenAI API| LM_STUDIO
    
    style NATS_SERVER fill:#4A90E2,color:#fff
    style LM_STUDIO fill:#2ECC71,color:#fff
    style TASK1 fill:#50C878,color:#fff
    style TASK2 fill:#FFB347,color:#333
    style CLIENT fill:#9B59B6,color:#fff
```

## How to View These Diagrams

### In GitHub
If you push this file to GitHub, the Mermaid diagrams will render automatically.

### In VS Code
Install the "Markdown Preview Mermaid Support" extension to see the diagrams.

### Online
Copy any diagram code block and paste it into:
- https://mermaid.live/
- https://mermaid-js.github.io/mermaid-live-editor/

### Command Line
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate images
mmdc -i NATS_DIAGRAMS.md -o diagrams/
```

## Diagram Legend

| Color | Meaning |
|-------|---------|
| 🔵 Blue | NATS/Infrastructure |
| 🟢 Green | Weather-Bot |
| 🟠 Orange | Trip-Planner |
| 🟣 Purple | User/Client |
| 🔴 Red | Broadcast/Critical paths |
| ⚪ Gray | Configuration/Support |

## Key Takeaways from Diagrams

1. **Central Hub**: NATS is the central message broker all agents connect to
2. **Pub/Sub**: Agents subscribe to their specific channels and publish to others
3. **Async Communication**: Messages are delivered asynchronously via NATS
4. **Request/Reply**: Built-in support for synchronous request/response patterns
5. **Isolation**: Agents don't need to know about each other directly
6. **Scalability**: Easy to add more agents - just connect to NATS
7. **Observability**: All communication flows through NATS and can be monitored

