"""
Configuration management for First Mate Agent
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


class LMStudioConfig(BaseSettings):
    """LM Studio configuration"""
    base_url: str = Field(default="http://127.0.0.1:1234/v1", description="LM Studio base URL")
    api_key: str = Field(default="lm-studio", description="LM Studio API key")
    model: str = Field(default="qwen/qwen3-32b", description="Model name to use")
    temperature: float = Field(default=0.7, description="Model temperature")
    max_tokens: int = Field(default=2000, description="Maximum tokens per response")
    
    class Config:
        env_prefix = "LM_STUDIO_"


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    url: str = Field(default="sqlite:///./first_mate.db", description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL queries")
    
    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    """Redis configuration"""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    
    class Config:
        env_prefix = "REDIS_"


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}", description="Log format")
    rotation: str = Field(default="1 day", description="Log rotation")
    retention: str = Field(default="30 days", description="Log retention")
    log_dir: str = Field(default="./logs", description="Log directory")
    
    class Config:
        env_prefix = "LOG_"


class AgentConfig(BaseSettings):
    """Agent configuration"""
    name: str = Field(default="First-Mate Agent", description="Agent name")
    max_context_length: int = Field(default=8000, description="Maximum context length")
    context_consolidation_threshold: int = Field(default=6000, description="Context consolidation threshold")
    memory_retention_days: int = Field(default=90, description="Memory retention in days")
    
    class Config:
        env_prefix = "AGENT_"


class Config(BaseSettings):
    """Main configuration class"""
    lm_studio: LMStudioConfig = Field(default_factory=LMStudioConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    
    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global config instance
config = Config()

# Ensure directories exist
config.data_dir.mkdir(exist_ok=True)
config.logs_dir.mkdir(exist_ok=True)
