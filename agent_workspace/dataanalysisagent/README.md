# DataAnalysisAgent

AI agent for data analysis tasks including web research, file operations, and dataset retrieval

## Usage

```python
from dataanalysisagent_agent import DataanalysisagentAgent

agent = DataanalysisagentAgent(
    name="DataAnalysisAgent",
    model="qwen/qwen3-32b"
)

# Run the agent
messages = agent.agentic_run("Your task here")
print("Task completed!")
```

## Tools

read_file, write_file, list_files

## Configuration

Make sure to set up the required environment variables:
- TAVILY_API_KEY (if using web search)

## Generated on

2025-10-01T17:44:45.006564
