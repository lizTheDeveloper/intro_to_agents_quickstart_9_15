"""
NATS Agent Mixin

This module provides a mixin class that adds NATS messaging capabilities to any agent.
It enables agents to communicate via NATS like a Slack-style messaging system.
"""

import asyncio
import logging
from typing import Callable, Optional, Dict, Any, List
import uuid
from datetime import datetime

import nats
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg

from nats_config import NATSConfig, AgentMetadata, AgentMessage, nats_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NATSAgentMixin:
    """
    Mixin class that adds NATS messaging capabilities to any agent.
    
    This mixin provides:
    - Connection to NATS server
    - Registration on all-agents channel
    - Direct message handling
    - Request/response patterns
    - Agent handoff capabilities
    """
    
    def __init__(self, *args, **kwargs):
        # Extract NATS-specific kwargs before passing to super
        nats_cfg = kwargs.pop('nats_config', nats_config)
        
        # Only call super().__init__() if there are args/kwargs to pass
        # This handles the case where this mixin is the only parent
        if args or kwargs:
            super().__init__(*args, **kwargs)
        
        # NATS connection
        self.nats_client: Optional[NATSClient] = None
        self.nats_config: NATSConfig = nats_cfg
        
        # Agent metadata
        self.agent_metadata: Optional[AgentMetadata] = None
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # Subscriptions
        self.subscriptions = []
        
        # Background tasks
        self.background_tasks = []
        
        logger.info(f"NATSAgentMixin initialized for agent: {getattr(self, 'name', 'Unknown')}")
    
    async def connect_nats(
        self,
        capabilities: Optional[List[str]] = None,
        description: Optional[str] = None
    ):
        """Connect to NATS and register this agent"""
        try:
            # Connect to NATS
            self.nats_client = await nats.connect(
                servers=[self.nats_config.nats_url],
                connect_timeout=self.nats_config.connection_timeout,
                max_reconnect_attempts=self.nats_config.max_reconnect_attempts,
                reconnect_time_wait=self.nats_config.reconnect_time_wait,
                error_cb=self._on_error,
                disconnected_cb=self._on_disconnected,
                reconnected_cb=self._on_reconnected,
            )
            
            logger.info(f"Connected to NATS at {self.nats_config.nats_url}")
            
            # Set up agent metadata
            self.agent_metadata = AgentMetadata(
                name=getattr(self, 'name', 'Unknown Agent'),
                description=description or getattr(self, 'goal', 'An AI agent'),
                capabilities=capabilities or [],
                tools=[tool.get('function', {}).get('name', '') for tool in getattr(self, 'tools', [])],
                model=getattr(self, 'model', 'unknown'),
            )
            
            # Subscribe to channels
            await self._subscribe_to_channels()
            
            # Announce presence
            await self.announce_presence()
            
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.background_tasks.append(heartbeat_task)
            
            logger.info(f"Agent '{self.agent_metadata.name}' registered on NATS")
            
        except Exception as error:
            logger.error(f"Failed to connect to NATS: {error}")
            raise
    
    async def _subscribe_to_channels(self):
        """Subscribe to relevant NATS channels"""
        # Subscribe to all-agents channel for announcements
        sub_all = await self.nats_client.subscribe(
            self.nats_config.all_agents_channel,
            cb=self._handle_all_agents_message
        )
        self.subscriptions.append(sub_all)
        logger.info(f"Subscribed to {self.nats_config.all_agents_channel}")
        
        # Subscribe to direct message channel
        direct_channel = self.nats_config.get_direct_channel(self.agent_metadata.name)
        sub_direct = await self.nats_client.subscribe(
            direct_channel,
            cb=self._handle_direct_message
        )
        self.subscriptions.append(sub_direct)
        logger.info(f"Subscribed to {direct_channel}")
        
        # Subscribe to request channel
        request_channel = self.nats_config.get_request_channel(self.agent_metadata.name)
        sub_request = await self.nats_client.subscribe(
            request_channel,
            cb=self._handle_request_message
        )
        self.subscriptions.append(sub_request)
        logger.info(f"Subscribed to {request_channel}")
    
    async def announce_presence(self):
        """Announce this agent's presence on the all-agents channel"""
        message = AgentMessage(
            message_type="announcement",
            from_agent=self.agent_metadata.name,
            content=f"Agent '{self.agent_metadata.name}' is now online",
            metadata=self.agent_metadata.to_dict()
        )
        
        await self.nats_client.publish(
            self.nats_config.all_agents_channel,
            message.to_bytes()
        )
        logger.info(f"Announced presence: {self.agent_metadata.name}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while self.nats_client and not self.nats_client.is_closed:
            try:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
                self.agent_metadata.last_heartbeat = datetime.utcnow().isoformat()
                
                message = AgentMessage(
                    message_type="heartbeat",
                    from_agent=self.agent_metadata.name,
                    metadata=self.agent_metadata.to_dict()
                )
                
                await self.nats_client.publish(
                    self.nats_config.all_agents_channel,
                    message.to_bytes()
                )
                
            except Exception as error:
                logger.error(f"Heartbeat error: {error}")
    
    async def _handle_all_agents_message(self, msg: Msg):
        """Handle messages from the all-agents channel"""
        try:
            agent_msg = AgentMessage.from_bytes(msg.data)
            logger.info(f"All-agents message from {agent_msg.from_agent}: {agent_msg.message_type}")
            
            # Handle different message types
            if agent_msg.message_type == "announcement":
                logger.info(f"Agent announcement: {agent_msg.content}")
            elif agent_msg.message_type == "heartbeat":
                # Could maintain a registry of active agents
                pass
            
        except Exception as error:
            logger.error(f"Error handling all-agents message: {error}")
    
    async def _handle_direct_message(self, msg: Msg):
        """Handle direct messages sent to this agent"""
        try:
            agent_msg = AgentMessage.from_bytes(msg.data)
            logger.info(f"Direct message from {agent_msg.from_agent}: {agent_msg.content}")
            
            # Kick off the agent with this message
            if hasattr(self, 'agentic_run'):
                # Run agent with the incoming message in the background
                task = asyncio.create_task(self._handle_agent_kickoff(agent_msg))
                self.background_tasks.append(task)
            else:
                logger.warning(f"Agent {self.agent_metadata.name} doesn't have 'agentic_run' method")
            
        except Exception as error:
            logger.error(f"Error handling direct message: {error}")
    
    async def _handle_request_message(self, msg: Msg):
        """Handle request messages (expecting a response)"""
        try:
            agent_msg = AgentMessage.from_bytes(msg.data)
            logger.info(f"Request from {agent_msg.from_agent}: {agent_msg.content}")
            
            # Process the request using the agent
            if hasattr(self, 'run'):
                # Synchronous run - wrap in async
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.run, agent_msg.content)
                
                # Extract the response content
                response_content = ""
                if result and len(result) > 0:
                    last_message = result[-1]
                    response_content = last_message.get('content', str(result))
                
                # Send response
                response_msg = AgentMessage(
                    message_type="response",
                    from_agent=self.agent_metadata.name,
                    to_agent=agent_msg.from_agent,
                    content=response_content,
                    in_reply_to=agent_msg.message_id,
                    metadata={"original_request": agent_msg.content}
                )
                
                # Reply to the message
                if msg.reply:
                    await self.nats_client.publish(msg.reply, response_msg.to_bytes())
                    logger.info(f"Sent response to {agent_msg.from_agent}")
            
        except Exception as error:
            logger.error(f"Error handling request message: {error}")
    
    async def _handle_agent_kickoff(self, message: AgentMessage):
        """Handle agent kickoff from incoming message"""
        try:
            logger.info(f"Kicking off agent with message: {message.content}")
            
            # Run the agent
            if hasattr(self, 'agentic_run'):
                # Check if agentic_run is async
                result = self.agentic_run(message.content)
                if asyncio.iscoroutine(result):
                    result = await result
                
                logger.info(f"Agent completed task from {message.from_agent}")
                
                # Optionally send completion notification back
                completion_msg = AgentMessage(
                    message_type="response",
                    from_agent=self.agent_metadata.name,
                    to_agent=message.from_agent,
                    content=f"Completed task: {message.content[:100]}...",
                    in_reply_to=message.message_id,
                    metadata={"status": "completed"}
                )
                
                # Send to the requester's direct channel
                response_channel = self.nats_config.get_direct_channel(message.from_agent)
                await self.nats_client.publish(response_channel, completion_msg.to_bytes())
                
        except Exception as error:
            logger.error(f"Error in agent kickoff: {error}")
    
    async def send_direct_message(self, to_agent: str, content: str, metadata: Optional[Dict] = None):
        """Send a direct message to another agent"""
        if not self.nats_client:
            raise RuntimeError("NATS client not connected. Call connect_nats() first.")
        
        message = AgentMessage(
            message_type="request",
            from_agent=self.agent_metadata.name,
            to_agent=to_agent,
            content=content,
            metadata=metadata or {},
            message_id=str(uuid.uuid4())
        )
        
        channel = self.nats_config.get_direct_channel(to_agent)
        await self.nats_client.publish(channel, message.to_bytes())
        logger.info(f"Sent direct message to {to_agent}")
    
    async def request_from_agent(self, to_agent: str, content: str, timeout: int = 30) -> Optional[str]:
        """Send a request to another agent and wait for response"""
        if not self.nats_client:
            raise RuntimeError("NATS client not connected. Call connect_nats() first.")
        
        message_id = str(uuid.uuid4())
        message = AgentMessage(
            message_type="request",
            from_agent=self.agent_metadata.name,
            to_agent=to_agent,
            content=content,
            message_id=message_id
        )
        
        try:
            # Use request/reply pattern
            channel = self.nats_config.get_request_channel(to_agent)
            response = await self.nats_client.request(
                channel,
                message.to_bytes(),
                timeout=timeout
            )
            
            response_msg = AgentMessage.from_bytes(response.data)
            logger.info(f"Received response from {to_agent}")
            return response_msg.content
            
        except asyncio.TimeoutError:
            logger.warning(f"Request to {to_agent} timed out after {timeout}s")
            return None
        except Exception as error:
            logger.error(f"Error requesting from agent: {error}")
            return None
    
    async def handoff_to_agent(self, to_agent: str, content: str, metadata: Optional[Dict] = None):
        """Hand off a task to another agent"""
        if not self.nats_client:
            raise RuntimeError("NATS client not connected. Call connect_nats() first.")
        
        message = AgentMessage(
            message_type="handoff",
            from_agent=self.agent_metadata.name,
            to_agent=to_agent,
            content=content,
            metadata=metadata or {},
            message_id=str(uuid.uuid4()),
            priority=2  # Handoffs are high priority
        )
        
        # Send to both the direct channel and handoff channel
        direct_channel = self.nats_config.get_direct_channel(to_agent)
        handoff_channel = self.nats_config.get_handoff_channel(self.agent_metadata.name, to_agent)
        
        await self.nats_client.publish(direct_channel, message.to_bytes())
        await self.nats_client.publish(handoff_channel, message.to_bytes())
        
        logger.info(f"Handed off task to {to_agent}")
    
    async def broadcast_message(self, content: str, metadata: Optional[Dict] = None):
        """Broadcast a message to all agents"""
        if not self.nats_client:
            raise RuntimeError("NATS client not connected. Call connect_nats() first.")
        
        message = AgentMessage(
            message_type="announcement",
            from_agent=self.agent_metadata.name,
            content=content,
            metadata=metadata or {}
        )
        
        await self.nats_client.publish(
            self.nats_config.all_agents_channel,
            message.to_bytes()
        )
        logger.info(f"Broadcast message: {content}")
    
    async def disconnect_nats(self):
        """Disconnect from NATS and cleanup"""
        if self.nats_client:
            # Send offline announcement
            message = AgentMessage(
                message_type="announcement",
                from_agent=self.agent_metadata.name,
                content=f"Agent '{self.agent_metadata.name}' going offline",
                metadata={"status": "offline"}
            )
            
            try:
                await self.nats_client.publish(
                    self.nats_config.all_agents_channel,
                    message.to_bytes()
                )
            except Exception as error:
                logger.error(f"Error sending offline announcement: {error}")
            
            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
            
            # Drain and close
            await self.nats_client.drain()
            await self.nats_client.close()
            
            logger.info(f"Disconnected from NATS")
    
    async def _on_error(self, error):
        """NATS error callback"""
        logger.error(f"NATS error: {error}")
    
    async def _on_disconnected(self):
        """NATS disconnected callback"""
        logger.warning("Disconnected from NATS")
    
    async def _on_reconnected(self):
        """NATS reconnected callback"""
        logger.info("Reconnected to NATS")
        # Re-announce presence
        await self.announce_presence()

