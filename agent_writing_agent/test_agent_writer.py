#!/usr/bin/env python3
"""
Test script for the Agent Writing Agent
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the agent
sys.path.append(str(Path(__file__).parent.parent))

from agent_writing_agent import create_agent_writing_agent

def test_basic_functionality():
    """Test basic agent functionality"""
    print("Creating Agent Writing Agent...")
    
    # Create the agent
    agent = create_agent_writing_agent(working_directory="./test_workspace")
    
    print(f"Agent created: {agent.name}")
    print(f"Working directory: {agent.working_directory}")
    print(f"Available tools: {len(agent.tools)}")
    
    # Test file operations
    print("\nTesting file operations...")
    
    # Test write file
    result = agent.write_file("test.txt", "Hello, this is a test file!")
    print(f"Write file result: {result}")
    
    # Test read file
    content = agent.read_file("test.txt")
    print(f"Read file content: {content}")
    
    # Test list files
    files = agent.list_files()
    print(f"Files in directory: {files}")
    
    return agent

def test_agent_creation():
    """Test creating a new agent"""
    print("\n" + "="*50)
    print("Testing Agent Creation")
    print("="*50)
    
    agent = create_agent_writing_agent(working_directory="./test_workspace")
    
    # Test creating a simple agent
    kickoff_message = """
    Please create a simple data analysis agent that can:
    1. Read CSV files
    2. Perform basic data analysis
    3. Generate reports
    
    Use the basic_agent template and include read_file and write_file tools.
    Name it "Data Analyst Agent" and provide appropriate instructions.
    """
    
    print("Running agent creation task...")
    messages = agent.run(kickoff_message)
    
    print(f"Task completed. Total messages: {len(messages)}")
    
    # Check if agent was created
    agent_files = list(agent.working_directory.rglob("*.py"))
    print(f"Python files created: {[f.name for f in agent_files]}")
    
    return agent

def test_web_enabled_agent_creation():
    """Test creating a web-enabled agent"""
    print("\n" + "="*50)
    print("Testing Web-Enabled Agent Creation")
    print("="*50)
    
    agent = create_agent_writing_agent(working_directory="./test_workspace")
    
    # Test creating a web-enabled agent
    kickoff_message = """
    Please create a research assistant agent that can:
    1. Search the web for information
    2. Fetch content from URLs
    3. Save research findings to files
    4. Compile research reports
    
    Use the web_enabled_agent template and include all web tools.
    Name it "Research Assistant Agent" and provide detailed instructions for conducting research.
    """
    
    print("Running web-enabled agent creation task...")
    messages = agent.run(kickoff_message)
    
    print(f"Task completed. Total messages: {len(messages)}")
    
    # Check if agent was created
    agent_files = list(agent.working_directory.rglob("*.py"))
    print(f"Python files created: {[f.name for f in agent_files]}")
    
    return agent

def main():
    """Main test function"""
    print("Agent Writing Agent Test Suite")
    print("="*50)
    
    try:
        # Test basic functionality
        agent = test_basic_functionality()
        
        # Test agent creation
        test_agent_creation()
        
        # Test web-enabled agent creation (only if TAVILY_API_KEY is available)
        if os.getenv("TAVILY_API_KEY"):
            test_web_enabled_agent_creation()
        else:
            print("\nSkipping web-enabled agent test (TAVILY_API_KEY not set)")
        
        print("\n" + "="*50)
        print("All tests completed successfully!")
        print(f"Check the '{agent.working_directory}' directory for created files.")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
