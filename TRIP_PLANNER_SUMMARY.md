# Trip Planner & Weather Bot - Quick Reference

## What Is This?

A working example of **two AI agents coordinating via NATS** to complete a task:
- **Trip-Planner**: Plans day trips, but needs weather info
- **Weather-Bot**: Provides weather information on request

Trip-Planner must ask Weather-Bot for weather data before making recommendations.

## Quick Start (30 seconds)

```bash
# Terminal 1: Start NATS
docker run -p 4222:4222 nats:latest

# Terminal 2: Start agents (make sure LM Studio is running)
source env/bin/activate
python demo_trip_weather_interaction.py
```

**Watch the magic happen!** You'll see:
1. Both agents connect to NATS
2. Trip-Planner receives a trip request
3. Trip-Planner sends NATS message to Weather-Bot
4. Weather-Bot responds with weather data
5. Trip-Planner uses weather to plan activities

## Files You Need

| File | Purpose |
|------|---------|
| `trip_planner_agent.py` | Trip planning agent |
| `nats_ooda_agent.py` | Weather bot (reused) |
| `demo_trip_weather_interaction.py` | Automated demo ⭐ |
| `run_trip_weather_agents.py` | Run both agents |
| `interact_with_trip_planner.py` | Send manual requests |

## The Interaction Pattern

```
User: "Plan a day trip from San Francisco"
  ↓
Trip-Planner: "Let me check the weather..."
  ↓
[NATS] Trip-Planner → Weather-Bot: "What's the weather in Napa?"
  ↓
[NATS] Weather-Bot → Trip-Planner: "Sunny, 72°F"
  ↓
Trip-Planner: "Great! Here's your itinerary for Napa Valley..."
```

## Manual Interaction

**Terminal 1:**
```bash
python run_trip_weather_agents.py
```

**Terminal 2:**
```bash
python interact_with_trip_planner.py
```

Then type requests like:
- "Plan a day trip from San Francisco"
- "I'm in Boston, recommend a coastal town"
- "Suggest activities in Seattle for tomorrow"

## Key Features Shown

✅ **Agent Specialization**: Each agent has specific capabilities  
✅ **Agent Coordination**: Trip-Planner needs Weather-Bot's help  
✅ **Request/Response**: Synchronous NATS communication with timeout  
✅ **Real Workflow**: Practical multi-agent task decomposition  
✅ **Observable**: Watch the coordination in the logs  

## Customization

### Add Your City

Edit `trip_planner_agent.py`:
```python
city_recommendations = {
    "YourCity": ["Nearby1", "Nearby2", "Nearby3"]
}
```

### Add Activities

Edit `get_activities()`:
```python
outdoor_activities = ["your_activity", ...]
```

### Add Another Agent

Create a new agent that uses `NATSAgentMixin`:
```python
class RestaurantAgent(NATSAgentMixin):
    # Can coordinate with Trip-Planner and Weather-Bot!
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Agents don't connect | Check NATS is running on 4222 |
| No weather response | Verify Weather-Bot is running |
| Slow responses | Check LM Studio has model loaded |
| Connection timeouts | Increase timeout in requests |

## Architecture

```
┌─────────────┐         ┌─────────────┐
│ Trip-       │◄───────►│ Weather-    │
│ Planner     │  NATS   │ Bot         │
└─────────────┘         └─────────────┘
      │                        │
      │   Tools:              │   Tools:
      │   • get_nearby_cities │   • get_current_weather
      │   • get_activities    │
      │                        │
      │   Coordinates via NATS │
      └────────────────────────┘
```

## What You Learn

1. **Multi-agent coordination patterns**
2. **Agent specialization and delegation**
3. **NATS request/response communication**
4. **Real-world agent task decomposition**
5. **How to build agent workflows**

## Next Steps

1. ✅ Run `demo_trip_weather_interaction.py`
2. ✅ Watch the logs to see coordination
3. ✅ Try interactive mode for custom requests
4. ✅ Read `TRIP_PLANNER_README.md` for details
5. ✅ Create your own coordinating agents!

## Full Documentation

- **[TRIP_PLANNER_README.md](TRIP_PLANNER_README.md)** - Complete guide
- **[README_NATS.md](README_NATS.md)** - NATS system overview
- **[NATS_ARCHITECTURE.md](NATS_ARCHITECTURE.md)** - Architecture details

---

**Perfect for learning multi-agent coordination!** 🎓

