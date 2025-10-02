"""
NATS Configuration for Agent Communication

This module provides configuration settings for NATS-based agent communication,
including connection details, channel naming conventions, and message formats.
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class NATSConfig:
    """Configuration for NATS connection and agent communication"""
    
    # NATS Server connection
    nats_url: str = field(default_factory=lambda: os.getenv("NATS_URL", "nats://localhost:4222"))
    connection_timeout: int = 5
    max_reconnect_attempts: int = 10
    reconnect_time_wait: int = 2
    
    # Channel naming conventions
    all_agents_channel: str = "agents.all"
    agent_prefix: str = "agents.direct"
    request_prefix: str = "agents.request"
    response_prefix: str = "agents.response"
    handoff_prefix: str = "agents.handoff"
    
    # Message settings
    message_timeout: int = 30  # seconds
    max_message_size: int = 1048576  # 1MB
    
    # JetStream settings (optional, for persistence)
    use_jetstream: bool = False
    stream_name: str = "AGENT_MESSAGES"
    
    def get_direct_channel(self, agent_name: str) -> str:
        """Get the direct message channel for a specific agent"""
        return f"{self.agent_prefix}.{agent_name.lower().replace(' ', '_')}"
    
    def get_request_channel(self, agent_name: str) -> str:
        """Get the request channel for a specific agent"""
        return f"{self.request_prefix}.{agent_name.lower().replace(' ', '_')}"
    
    def get_response_channel(self, agent_name: str, request_id: str) -> str:
        """Get the response channel for a specific request"""
        return f"{self.response_prefix}.{agent_name.lower().replace(' ', '_')}.{request_id}"
    
    def get_handoff_channel(self, from_agent: str, to_agent: str) -> str:
        """Get the handoff channel for agent-to-agent task transfer"""
        from_name = from_agent.lower().replace(' ', '_')
        to_name = to_agent.lower().replace(' ', '_')
        return f"{self.handoff_prefix}.{from_name}.to.{to_name}"


@dataclass
class AgentMetadata:
    """Metadata describing an agent's capabilities and status"""
    
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    status: str = "available"  # available, busy, offline
    model: str = "unknown"
    version: str = "1.0.0"
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "status": self.status,
            "model": self.model,
            "version": self.version,
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMetadata':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class AgentMessage:
    """Standard message format for agent-to-agent communication"""
    
    message_type: str  # request, response, handoff, announcement, heartbeat
    from_agent: str
    to_agent: Optional[str] = None  # None for broadcast
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    priority: int = 3  # 1 (highest) to 5 (lowest)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "message_type": self.message_type,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "in_reply_to": self.in_reply_to,
            "priority": self.priority
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(**data)
    
    def to_bytes(self) -> bytes:
        """Convert to bytes for NATS"""
        return self.to_json().encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'AgentMessage':
        """Create from bytes from NATS"""
        return cls.from_json(data.decode('utf-8'))


# Global config instance
nats_config = NATSConfig()

