# Data Analyst Agent

Analyzes CSV data and generates summary reports

## Usage

```python
from data_analyst_agent_agent import DataAnalystAgent

agent = DataAnalystAgent(
    name="Data Analyst Agent",
    model="qwen/qwen3-32b"
)

# Run the agent
messages = agent.agentic_run("Your task here")
print("Task completed!")
```

## Tools

read_file, write_file

## Configuration

Make sure to set up the required environment variables:
- TAVILY_API_KEY (if using web search)

## Generated on

2025-10-01T17:41:42.637649
