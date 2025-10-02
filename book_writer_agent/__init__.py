"""
Book Writer Agent Module

An autonomous agent that can research topics and write comprehensive books
using web search and file management capabilities.
"""

from .book_writer_agent import BookWriterAgent, create_book_writer_agent

__all__ = ['BookWriterAgent', 'create_book_writer_agent']