# Intro to Agents Quickstart

A collection of autonomous agents built using the OODA (Observe, Orient, Decide, Act) loop pattern with LM Studio integration.

## 🚀 NEW: Multi-Agent Communication via NATS

Agents can now communicate with each other using NATS messaging - like Slack for AI agents! See **[README_NATS.md](README_NATS.md)** for details.

**Features**:
- 📢 Broadcast announcements to all agents
- 💬 Direct messages between specific agents
- 🤝 Request/response patterns with timeouts
- 🔄 Task handoff between agents
- 💓 Automatic agent discovery via heartbeats
- 📊 Channel-based routing (agents.all, agents.direct.{name}, etc.)

**Quick Start NATS**:
```bash
# Start NATS server
docker run -p 4222:4222 -p 8222:8222 nats:latest

# Run multi-agent demo (3 agents)
python demo_nats_agents.py

# Or run Trip Planner & Weather Bot example (2 agents coordinating)
python demo_trip_weather_interaction.py
```

**Example: Trip Planner coordinating with Weather Bot** 🌤️ ✈️
See `TRIP_PLANNER_README.md` for a complete example of two agents working together!
- Trip-Planner agent plans day trips
- Weather-Bot provides weather information  
- Trip-Planner requests weather from Weather-Bot via NATS
- Shows real multi-agent coordination

## Agents Available

### 1. NATS-Enabled OODA Agent 🌐
Autonomous agents with inter-agent communication capabilities via NATS.

**Location**: `nats_ooda_agent.py`, `nats_agent_mixin.py`, `nats_config.py`
**Features**:
- Full OODA loop autonomy
- NATS messaging for multi-agent coordination
- Direct messaging and broadcasting
- Request/response patterns
- Task handoff between agents
- Agent discovery and heartbeats

### 2. First Mate Agent
An enhanced autonomous agent with memory, context management, and tool calling capabilities.

**Location**: `first_mate_agent/`
**Features**:
- Context consolidation for long conversations
- Tool calling support
- Centralized logging
- Configuration management

### 3. Book Writer Agent 📚
An autonomous agent that researches topics and writes comprehensive books using web search and file management.

**Location**: `book_writer_agent/`
**Features**:
- Web research using Tavily API
- Markdown-based file management
- Autonomous book writing workflow
- Citation and source management
- Structured chapter organization

## Quick Start

### Prerequisites

1. **Python Environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **LM Studio Setup**:
   - Install and run LM Studio
   - Load a compatible model (e.g., Qwen 3 32B)
   - Ensure it's running on `http://127.0.0.1:1234`

3. **API Keys** (for Book Writer Agent):
   ```bash
   export TAVILY_API_KEY="your_tavily_api_key_here"
   ```

### Running the Book Writer Agent

```bash
# Quick demo
python demo_book_writer.py

# Or use programmatically
python -c "
from book_writer_agent import create_book_writer_agent
agent = create_book_writer_agent('Your Topic Here')
messages = agent.agentic_run('Write a book about this topic')
"
```

### Running the OODA Agent

```bash
python ooda_agent.py
```

## Project Structure

```
intro_to_agents_quickstart_9_15/
├── book_writer_agent/          # Book writing agent
│   ├── book_writer_agent.py    # Main agent implementation
│   ├── config.py               # Configuration settings
│   ├── test_book_writer.py     # Test script
│   └── README.md               # Detailed documentation
├── first_mate_agent/           # Enhanced agent framework
│   ├── enhanced_agent.py       # Core agent class
│   ├── config.py               # Configuration
│   └── logger.py               # Logging setup
├── plans/                      # Project planning documents
├── devlog/                     # Development logs
├── logs/                       # Runtime logs
├── demo_book_writer.py         # Book writer demo script
├── ooda_agent.py               # Basic OODA agent
└── requirements.txt            # Python dependencies
```

## Book Writer Agent Workflow

The Book Writer Agent follows a structured approach:

1. **Research Phase**: Conducts web searches on the topic
2. **Planning Phase**: Creates detailed outlines and structure
3. **Writing Phase**: Generates chapters with proper citations
4. **Refinement Phase**: Reviews and improves content quality

### Generated Files

The agent creates a structured workspace:

```
book_workspace/
├── research_notes.md      # Compiled research findings
├── book_outline.md        # Detailed book structure
├── table_of_contents.md   # Chapter listings
├── sources.md             # Citations and references
├── introduction.md        # Book introduction
├── chapter_01.md          # Individual chapters
├── chapter_02.md
└── conclusion.md          # Book conclusion
```

## Configuration

### Environment Variables

- `TAVILY_API_KEY`: Required for web search functionality
- `OPENAI_API_KEY`: Optional, defaults to LM Studio

### Agent Settings

Key configuration options in `book_writer_agent/config.py`:

- `MAX_ITERATIONS`: Maximum autonomous iterations (default: 50)
- `MAX_SEARCH_RESULTS`: Maximum web search results (default: 10)
- `DEFAULT_CHAPTER_WORD_COUNT`: Target words per chapter (default: 3000)

## Features

### OODA Loop Implementation
All agents follow the Observe-Orient-Decide-Act pattern:
- **Observe**: Gather information from environment and tools
- **Orient**: Analyze and understand the current situation
- **Decide**: Choose the best course of action
- **Act**: Execute the decision and observe results

### Tool Integration
- **Web Search**: Tavily API for comprehensive research
- **File Management**: Read, write, update markdown files
- **Context Management**: Intelligent conversation consolidation
- **Error Handling**: Robust error recovery and logging

### Autonomous Operation
- Self-directed task completion
- Iterative improvement cycles
- Progress tracking and status updates
- Automatic context consolidation

## Development

### Adding New Tools

1. Define the tool schema in the agent's `tools` list
2. Implement the tool function
3. Add tool handling in `handle_tool_call` method
4. Test the integration

### Extending Agents

1. Inherit from the base agent class
2. Add specialized tools and capabilities
3. Customize the instruction prompt
4. Implement domain-specific workflows

## Troubleshooting

### Common Issues

1. **LM Studio Connection**: Ensure LM Studio is running on the correct port
2. **API Keys**: Verify environment variables are set correctly
3. **Memory Issues**: Monitor context length and consolidation
4. **File Permissions**: Ensure write access to working directories

### Logging

Check the `logs/` directory for detailed execution logs:
- `agent_activity.log`: General agent activities
- `first_mate.log`: First Mate agent specific logs
- `first_mate_errors.log`: Error logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This project is for educational purposes. Please respect API terms of service and usage limits.

## Resources

- [LM Studio Documentation](https://lmstudio.ai/docs)
- [Tavily API Documentation](https://tavily.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## Next Steps

- Add more specialized agents (research, writing, analysis)
- Implement multi-agent collaboration
- Add web interface for agent management
- Integrate with more external APIs and tools
