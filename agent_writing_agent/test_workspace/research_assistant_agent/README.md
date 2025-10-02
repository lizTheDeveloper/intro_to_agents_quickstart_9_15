# Research Assistant Agent

Conducts comprehensive research tasks including web searching, content fetching, data organization, and report generation

## Usage

```python
from research_assistant_agent_agent import ResearchAssistantAgent

agent = ResearchAssistantAgent(
    name="Research Assistant Agent",
    model="qwen/qwen3-32b"
)

# Run the agent
messages = agent.agentic_run("Your task here")
print("Task completed!")
```

## Tools

web_search, fetch_url, write_file, read_file, list_files

## Configuration

Make sure to set up the required environment variables:
- TAVILY_API_KEY (if using web search)

## Generated on

2025-10-01T17:44:40.089476
