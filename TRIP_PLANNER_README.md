# Trip Planner & Weather Agent Example

This example demonstrates **real multi-agent coordination** where the Trip Planner agent needs to coordinate with the Weather Bot agent to complete its task.

## The Scenario

**Trip Planner Agent** helps users plan day trips to nearby cities, but it doesn't have its own weather tool. Instead, it must:

1. Receive a trip planning request
2. Contact **Weather Bot** via NATS to get weather information
3. Use the weather data to recommend appropriate activities
4. Return a complete trip itinerary

This shows how agents can specialize and coordinate with each other!

## Agents Involved

### 1. Weather-Bot
- **Role**: Weather information provider
- **Tools**: `get_current_weather(location, unit)`
- **NATS Channels**: 
  - Subscribes to: `agents.request.weather_bot`
  - Announces on: `agents.all`

### 2. Trip-Planner
- **Role**: Day trip planning specialist
- **Tools**: 
  - `get_nearby_cities(from_city)` - Find nearby destinations
  - `get_activities(city, weather_condition)` - Recommend activities
- **NATS Coordination**: Requests weather from Weather-Bot
- **NATS Channels**:
  - Subscribes to: `agents.direct.trip_planner`
  - Requests from: `agents.request.weather_bot`

## Running the Example

### Prerequisites

1. **NATS Server** running:
   ```bash
   docker run -p 4222:4222 -p 8222:8222 nats:latest
   ```

2. **LM Studio** with a model loaded:
   - Running on `localhost:1234`
   - Model loaded (e.g., Qwen 3 32B)

3. **Virtual environment** activated:
   ```bash
   source env/bin/activate
   ```

### Option 1: Automated Demo (Recommended)

This runs a complete demo showing all the interactions:

```bash
python demo_trip_weather_interaction.py
```

**What you'll see:**
- Both agents connecting and announcing presence
- Trip-Planner receiving trip requests
- Trip-Planner asking Weather-Bot for weather
- Weather-Bot responding with weather data
- Trip-Planner using weather to make recommendations

### Option 2: Manual Interaction

Run the agents in one terminal, interact from another:

**Terminal 1 - Run the agents:**
```bash
python run_trip_weather_agents.py
```

**Terminal 2 - Send requests:**
```bash
# Interactive mode
python interact_with_trip_planner.py

# Or quick test mode
python interact_with_trip_planner.py --test
```

### Option 3: Run Agents Individually

**Terminal 1 - Weather Bot:**
```bash
python nats_ooda_agent.py
# (or modify to run Weather-Bot specifically)
```

**Terminal 2 - Trip Planner:**
```bash
python trip_planner_agent.py
```

## Example Interactions

### Request 1: San Francisco Day Trip
```
User: "I'm in San Francisco and want a day trip tomorrow. 
       Check the weather and recommend a nearby city with activities."

Trip-Planner: 
  1. Uses get_nearby_cities("San Francisco")
  2. Sends NATS request to Weather-Bot for Napa Valley weather
  3. Receives weather: "Sunny, 72°F"
  4. Uses get_activities("Napa Valley", "sunny")
  5. Returns complete itinerary with outdoor activities
```

### Request 2: Boston Coastal Trip
```
User: "I'm in Boston, recommend a coastal town for tomorrow."

Trip-Planner:
  1. Uses get_nearby_cities("Boston")
  2. Sends NATS request for Cape Cod weather
  3. Receives weather: "Cloudy, 65°F"  
  4. Uses get_activities("Cape Cod", "cloudy")
  5. Recommends mix of indoor and outdoor activities
```

## Message Flow

```
User Terminal
     │
     ├─── "Plan a day trip from SF" ─────┐
     │                                    │
     ↓                                    ↓
NATS Server ──────────────────→ Trip-Planner
                                     │
                                     │ (needs weather)
                                     │
                                     ├─── "What's weather in Napa?" ──┐
                                     │                                 │
                                     ↓                                 ↓
                              NATS Server ──────────────────→ Weather-Bot
                                     ↑                                 │
                                     │                                 │
                                     │        (get_current_weather)    │
                                     │                                 │
                                     ├──── "Sunny, 72°F" ──────────────┘
                                     │
                                     ↓
                              Trip-Planner
                                     │
                                     │ (plan with weather data)
                                     │
                                     ├─── Complete Itinerary ──────────→ User
```

## File Structure

```
├── trip_planner_agent.py              # Trip Planner agent implementation
├── nats_ooda_agent.py                 # Weather Bot implementation
├── demo_trip_weather_interaction.py   # Automated demo
├── run_trip_weather_agents.py         # Run both agents
├── interact_with_trip_planner.py      # Send requests to Trip-Planner
├── TRIP_PLANNER_README.md            # This file
└── nats_agent_mixin.py               # NATS communication layer
```

## Key Features Demonstrated

### 1. Multi-Agent Coordination
- Trip-Planner doesn't have weather capability
- Must coordinate with Weather-Bot
- Shows agent specialization

### 2. Request/Response Pattern
- Trip-Planner uses `request_from_agent()`
- Waits for Weather-Bot response
- Timeout handling (10 seconds)

### 3. Agent Specialization
- **Weather-Bot**: Single purpose - weather data
- **Trip-Planner**: Complex planning, delegates weather lookup

### 4. Real-World Workflow
- Natural task decomposition
- Agent-to-agent dependency
- Asynchronous communication

## Customization

### Add More Cities

Edit `trip_planner_agent.py`:
```python
city_recommendations = {
    "San Francisco": ["Napa", "Berkeley", ...],
    "YourCity": ["Nearby1", "Nearby2", ...],
}
```

### Add More Activities

Edit `get_activities()` function:
```python
outdoor_activities = ["hiking", "beach", "your_activity"]
indoor_activities = ["museum", "shopping", "your_activity"]
```

### Change Models

Both agents use `qwen/qwen3-32b` by default. Change in agent creation:
```python
model="your-model-name"
```

## Troubleshooting

### Trip-Planner Doesn't Ask for Weather

**Symptom**: Trip-Planner makes recommendations without checking weather

**Solutions**:
1. Check that both agents are connected to NATS
2. Verify Weather-Bot is responding (check logs)
3. Ensure instructions emphasize weather coordination
4. Try with a more capable model

### Weather-Bot Not Responding

**Symptom**: Trip-Planner times out waiting for weather

**Solutions**:
1. Check Weather-Bot logs for errors
2. Verify Weather-Bot is subscribed to correct channel
3. Check NATS connection for both agents
4. Increase timeout in request_from_agent()

### NATS Connection Errors

```bash
# Verify NATS is running
docker ps | grep nats

# Check NATS port
nc -zv localhost 4222

# View NATS logs
docker logs <nats-container-id>
```

### LM Studio Issues

**Symptom**: Agents timeout or don't respond

**Solutions**:
1. Verify LM Studio is running
2. Check model is loaded
3. Test API: `curl http://localhost:1234/v1/models`
4. Check LM Studio has enough memory

## Advanced Usage

### Monitor All Agent Communication

```python
import asyncio
import nats
from nats_config import AgentMessage

async def monitor():
    nc = await nats.connect("nats://localhost:4222")
    
    async def handler(msg):
        agent_msg = AgentMessage.from_bytes(msg.data)
        print(f"[{agent_msg.message_type}] {agent_msg.from_agent} → {agent_msg.to_agent}")
        print(f"  {agent_msg.content[:80]}...")
    
    await nc.subscribe("agents.>", cb=handler)
    
    while True:
        await asyncio.sleep(1)

asyncio.run(monitor())
```

### Add Your Own Agent

Create a new agent that coordinates with these:

```python
from nats_agent_mixin import NATSAgentMixin

class RestaurantAgent(NATSAgentMixin):
    # Can request weather from Weather-Bot
    # Can request trip info from Trip-Planner
    # Adds restaurant recommendations
```

### Create Agent Workflows

Chain multiple agents together:

```
User → Trip-Planner → Weather-Bot
                    ↓
                Restaurant-Agent → Review-Scraper
                    ↓
                Complete Itinerary
```

## Performance

- **NATS latency**: ~1ms
- **Agent coordination**: 2-5 seconds (LLM processing)
- **Weather lookup**: ~1-2 seconds
- **Complete trip plan**: 5-10 seconds total

## Next Steps

1. ✅ Run the demo to see agents working together
2. ✅ Try the interactive mode to send custom requests
3. ✅ Read the logs to understand the message flow
4. ✅ Create your own specialized agent
5. ✅ Build multi-agent workflows for your use case

## Related Documentation

- **[README_NATS.md](README_NATS.md)** - NATS system overview
- **[NATS_ARCHITECTURE.md](NATS_ARCHITECTURE.md)** - Architecture diagrams
- **[devlog/nats_agent_communication.md](devlog/nats_agent_communication.md)** - Technical details

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review NATS logs for connection issues
3. Check LM Studio logs for model issues
4. Review agent logs for processing issues

---

**This example demonstrates the power of multi-agent systems where specialized agents coordinate to solve complex tasks!** 🚀

