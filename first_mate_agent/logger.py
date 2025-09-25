"""
Centralized logging system for First Mate Agent
"""
import sys
from pathlib import Path
from loguru import logger
from .config import config


def setup_logging():
    """Set up centralized logging configuration"""
    # Remove default handler
    logger.remove()
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        format=config.logging.format,
        level=config.logging.level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File handler for all logs
    log_file = config.logs_dir / "first_mate.log"
    logger.add(
        log_file,
        format=config.logging.format,
        level=config.logging.level,
        rotation=config.logging.rotation,
        retention=config.logging.retention,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Error file handler
    error_log_file = config.logs_dir / "first_mate_errors.log"
    logger.add(
        error_log_file,
        format=config.logging.format,
        level="ERROR",
        rotation=config.logging.rotation,
        retention=config.logging.retention,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Agent-specific log file
    agent_log_file = config.logs_dir / "agent_activity.log"
    logger.add(
        agent_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="1 day",
        retention="7 days",
        compression="zip",
        filter=lambda record: "agent" in record["name"].lower()
    )
    
    logger.info("Logging system initialized")
    return logger


# Initialize logging
setup_logging()

# Export logger for use in other modules
__all__ = ["logger"]
