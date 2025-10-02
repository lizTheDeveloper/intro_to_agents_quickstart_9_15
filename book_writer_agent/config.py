"""
Configuration settings for the Book Writer Agent
"""

import os
from pathlib import Path
from typing import Dict, Any

class BookWriterConfig:
    """Configuration class for Book Writer Agent"""
    
    # API Configuration
    OPENAI_BASE_URL = "http://127.0.0.1:1234/v1"
    OPENAI_API_KEY = "lm-studio"
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Model Configuration
    DEFAULT_MODEL = "qwen/qwen3-32b"
    
    # Agent Configuration
    MAX_ITERATIONS = 50
    CONTEXT_CONSOLIDATION_THRESHOLD = 50000  # characters
    MAX_SEARCH_RESULTS = 10
    
    # File Configuration
    DEFAULT_WORKING_DIRECTORY = "book_workspace"
    SUPPORTED_FILE_EXTENSIONS = ['.md', '.txt', '.json']
    
    # Book Writing Configuration
    DEFAULT_CHAPTER_WORD_COUNT = 3000
    MIN_RESEARCH_SOURCES = 5
    MAX_RESEARCH_SOURCES = 20
    
    # Quality Thresholds
    MIN_CONTENT_LENGTH = 500  # minimum words per chapter
    CITATION_REQUIRED = True
    
    @classmethod
    def get_working_directory(cls, topic: str) -> Path:
        """Generate working directory path based on topic"""
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_topic = safe_topic.replace(' ', '_').lower()
        return Path(cls.DEFAULT_WORKING_DIRECTORY) / safe_topic
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        if not cls.TAVILY_API_KEY:
            issues.append("TAVILY_API_KEY environment variable not set")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

# Book structure templates
BOOK_TEMPLATES = {
    "outline_template": """# {title}

## Book Overview
- **Topic**: {topic}
- **Target Audience**: {audience}
- **Estimated Length**: {length} words
- **Writing Style**: {style}

## Table of Contents

{chapters}

## Research Notes
- Key themes to explore
- Important sources to investigate
- Questions to answer

## Writing Plan
1. Research Phase
2. Outline Development
3. Chapter Writing
4. Review and Revision
""",
    
    "chapter_template": """# Chapter {number}: {title}

## Chapter Overview
{overview}

## Key Points
{key_points}

## Research Sources
{sources}

## Content

{content}

## Notes
- Word count: {word_count}
- Status: {status}
- Last updated: {timestamp}
""",
    
    "research_template": """# Research Notes for {topic}

## Research Summary
{summary}

## Key Findings
{findings}

## Sources
{sources}

## Questions for Further Research
{questions}

## Research Timeline
{timeline}
"""
}