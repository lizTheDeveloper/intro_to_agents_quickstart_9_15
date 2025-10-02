# DataAnalysisAssistant

AI agent for data analysis tasks with web search, file processing, and URL fetching capabilities

## Usage

```python
from dataanalysisassistant_agent import DataanalysisassistantAgent

agent = DataanalysisassistantAgent(
    name="DataAnalysisAssistant",
    model="qwen/qwen3-32b"
)

# Run the agent
messages = agent.agentic_run("Your task here")
print("Task completed!")
```

## Tools

web_search, fetch_url, read_file, write_file, list_files

## Configuration

Make sure to set up the required environment variables:
- TAVILY_API_KEY (if using web search)

## Generated on

2025-10-01T17:48:32.296845
