#!/usr/bin/env python3
"""
Demo script to test the terminal functionality of the Agent Writing Agent
"""

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from agent_writing_agent import create_agent_writing_agent

def test_terminal_functionality():
    """Test terminal command execution"""
    print("Testing Agent Writing Agent - Terminal Functionality")
    print("=" * 60)
    
    # Create the agent
    agent = create_agent_writing_agent(working_directory="./demo_workspace")
    
    print(f"\nAgent created: {agent.name}")
    print(f"Working directory: {agent.working_directory}")
    
    # Test 1: Simple command
    print("\n" + "-" * 60)
    print("Test 1: Running 'ls -la' command")
    print("-" * 60)
    result = agent.run_terminal_command("ls -la")
    print(result)
    
    # Test 2: Python version check
    print("\n" + "-" * 60)
    print("Test 2: Checking Python version")
    print("-" * 60)
    result = agent.run_terminal_command("python --version")
    print(result)
    
    # Test 3: Create a test file and verify
    print("\n" + "-" * 60)
    print("Test 3: Creating and verifying a test file")
    print("-" * 60)
    agent.write_file("test_script.py", "print('Hello from test script!')")
    result = agent.run_terminal_command("python test_script.py")
    print(result)
    
    # Test 4: List files in directory
    print("\n" + "-" * 60)
    print("Test 4: Listing files")
    print("-" * 60)
    files = agent.list_files()
    print(files)
    
    # Test 5: Check if pip is available
    print("\n" + "-" * 60)
    print("Test 5: Checking pip availability")
    print("-" * 60)
    result = agent.run_terminal_command("pip --version")
    print(result)
    
    print("\n" + "=" * 60)
    print("All terminal functionality tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_terminal_functionality()

