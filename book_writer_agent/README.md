# Book Writer Agent

An autonomous agent that can research topics and write comprehensive books using web search and file management capabilities.

## Features

- **Web Research**: Uses Tavily API for comprehensive web searches
- **File Management**: Read, write, update, and list files in a working directory
- **Autonomous Operation**: Follows OODA loop pattern for continuous improvement
- **Markdown Support**: Creates structured markdown files for book content
- **Context Management**: Handles long conversations with intelligent consolidation

## Setup

1. **Install Dependencies**:
   ```bash
   pip install tavily-python openai pathlib
   ```

2. **Set Environment Variables**:
   ```bash
   export TAVILY_API_KEY="your_tavily_api_key_here"
   ```

3. **Configure LM Studio**:
   - Ensure LM Studio is running on `http://127.0.0.1:1234`
   - Load a compatible model (e.g., Qwen 3 32B)

## Usage

### Basic Usage

```python
from book_writer_agent import create_book_writer_agent

# Create an agent for a specific topic
topic = "Introduction to Machine Learning"
agent = create_book_writer_agent(topic)

# Start the book writing process
kickoff_message = f"""
I want you to write a comprehensive book about '{topic}'. 
Please start by conducting research and creating an outline.
"""

# Run the agent autonomously
messages = agent.agentic_run(kickoff_message)
```

### Test the Agent

```bash
cd book_writer_agent
python test_book_writer.py
```

## Agent Capabilities

### Tools Available

1. **web_search**: Search the web using Tavily API
2. **read_file**: Read files from the working directory
3. **write_file**: Write content to files
4. **update_file**: Append or replace file content
5. **list_files**: List all files in the working directory

### Workflow Phases

1. **Research & Planning**: Conduct web research and create outlines
2. **Chapter Development**: Write detailed chapter outlines and content
3. **Writing & Refinement**: Create complete chapters with citations
4. **Final Assembly**: Review and assemble the complete book

## File Structure

The agent creates a structured workspace:

```
book_workspace/
├── research_notes.md      # Compiled research findings
├── book_outline.md        # Detailed book structure
├── table_of_contents.md   # Chapter listings
├── sources.md             # Citations and references
├── chapter_01.md          # Individual chapters
├── chapter_02.md
└── ...
```

## Configuration

Key configuration options in `config.py`:

- `MAX_ITERATIONS`: Maximum autonomous iterations (default: 50)
- `MAX_SEARCH_RESULTS`: Maximum web search results (default: 10)
- `CONTEXT_CONSOLIDATION_THRESHOLD`: When to consolidate context (default: 50000 chars)
- `DEFAULT_CHAPTER_WORD_COUNT`: Target words per chapter (default: 3000)

## Requirements

- Python 3.8+
- OpenAI-compatible API (LM Studio)
- Tavily API key
- Internet connection for web searches

## Error Handling

The agent includes robust error handling for:
- Missing API keys
- Network connectivity issues
- File system errors
- Model response errors

## Limitations

- Requires active internet connection for web searches
- Dependent on LM Studio being available
- Limited by the underlying language model's capabilities
- File operations are restricted to the working directory for security
