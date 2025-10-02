#!/usr/bin/env python3
"""
Demonstration script for the Book Writer Agent

This script shows how to use the Book Writer Agent to create a book on any topic.
"""

import os
import sys
from pathlib import Path

# Import the book writer agent
from book_writer_agent import create_book_writer_agent
from book_writer_agent.config import BookWriterConfig

def main():
    """Main demonstration function"""
    
    print("=" * 60)
    print("Book Writer Agent Demonstration")
    print("=" * 60)
    
    # Check if Tavily API key is set
    if not os.getenv("TAVILY_API_KEY"):
        print("\n⚠️  WARNING: TAVILY_API_KEY environment variable not set.")
        print("   The agent will work but web search functionality will be limited.")
        print("   To enable web search, set your Tavily API key:")
        print("   export TAVILY_API_KEY='your_api_key_here'")
        print()
    
    # Get topic from user or use default
    topic = input("Enter a book topic (or press Enter for default): ").strip()
    if not topic:
        topic = "The Basics of Python Programming"
    
    print(f"\n📚 Creating book writer agent for topic: '{topic}'")
    
    # Create the agent
    agent = create_book_writer_agent(topic)
    
    print(f"📁 Working directory: {agent.working_directory}")
    print(f"🔧 Agent initialized with {len(agent.tools)} tools")
    
    # Create the kickoff message
    kickoff_message = f"""
    I want you to write a comprehensive book about '{topic}'.
    
    Please follow this process:
    1. Start with initial research on the topic using web search
    2. Create a detailed book outline with 5-7 chapters
    3. Set up your working files (outline, research notes, table of contents)
    4. Write a compelling introduction
    5. Write the first chapter with proper research and citations
    
    Focus on creating high-quality, well-researched content. Use markdown formatting
    and maintain professional writing standards throughout.
    """
    
    print("\n🚀 Starting book writing process...")
    print("   This may take several minutes depending on the complexity.")
    print("   Press Ctrl+C to interrupt if needed.")
    print("\n" + "=" * 60)
    
    try:
        # Run the agent with limited iterations for demo
        messages = agent.agentic_run(kickoff_message, max_iterations=15)
        
        print("\n" + "=" * 60)
        print("✅ Book writing session completed!")
        print(f"📊 Total messages exchanged: {len(messages)}")
        
        # Show generated files
        if agent.working_directory.exists():
            files = list(agent.working_directory.glob("*"))
            if files:
                print(f"\n📄 Generated files in '{agent.working_directory}':")
                for file in sorted(files):
                    size = file.stat().st_size
                    print(f"   • {file.name} ({size:,} bytes)")
                
                # Show a preview of the main files
                preview_files = ['book_outline.md', 'introduction.md', 'chapter_01.md']
                for preview_file in preview_files:
                    file_path = agent.working_directory / preview_file
                    if file_path.exists():
                        print(f"\n📖 Preview of {preview_file}:")
                        print("-" * 40)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Show first 500 characters
                            preview = content[:500]
                            if len(content) > 500:
                                preview += "..."
                            print(preview)
                        print("-" * 40)
            else:
                print("\n❌ No files were generated.")
        
        print(f"\n🎉 Demo completed! Check '{agent.working_directory}' for all generated content.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user.")
        print(f"   Partial results may be available in '{agent.working_directory}'")
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
