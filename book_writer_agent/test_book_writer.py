#!/usr/bin/env python3
"""
Test script for the Book Writer Agent
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from book_writer_agent import create_book_writer_agent
from book_writer_agent.config import BookWriterConfig

def test_book_writer_agent():
    """Test the book writer agent with a simple topic"""
    
    # Check configuration
    config_status = BookWriterConfig.validate_config()
    if not config_status["valid"]:
        print("Configuration issues found:")
        for issue in config_status["issues"]:
            print(f"  - {issue}")
        print("\nPlease set the TAVILY_API_KEY environment variable and try again.")
        return
    
    # Create agent for a test topic
    topic = "Introduction to Machine Learning"
    print(f"Creating book writer agent for topic: '{topic}'")
    
    agent = create_book_writer_agent(topic)
    
    print(f"Working directory: {agent.working_directory}")
    print(f"Agent initialized with {len(agent.tools)} tools")
    
    # Test message
    kickoff_message = f"""
    I want you to write a short book about '{topic}' suitable for beginners.
    
    Please start by:
    1. Conducting initial research on machine learning basics
    2. Creating a simple book outline with 3-5 chapters
    3. Setting up your working files (outline, research notes)
    4. Writing a brief introduction chapter
    
    Keep this as a focused, beginner-friendly book. Don't make it too long for this test.
    """
    
    print("\nStarting book writing process...")
    print("=" * 50)
    
    try:
        # Run the agent (limit iterations for testing)
        messages = agent.agentic_run(kickoff_message, max_iterations=10)
        
        print("\nBook writing session completed!")
        print(f"Total messages exchanged: {len(messages)}")
        print(f"Check the '{agent.working_directory}' directory for generated files.")
        
        # List generated files
        if agent.working_directory.exists():
            files = list(agent.working_directory.glob("*"))
            if files:
                print("\nGenerated files:")
                for file in files:
                    print(f"  - {file.name} ({file.stat().st_size} bytes)")
            else:
                print("\nNo files were generated.")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_book_writer_agent()
