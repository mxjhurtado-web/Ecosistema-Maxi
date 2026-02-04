"""
Multi-MCP configuration models and routing logic.
Prepared for future multi-MCP support.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server"""
    name: str = Field(..., description="Unique name for this MCP server")
    url: str = Field(..., description="URL to the MCP query endpoint")
    timeout: int = Field(5, description="Timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay: int = Field(1, description="Delay between retries in seconds")
    enabled: bool = Field(True, description="Whether this MCP is enabled")
    priority: int = Field(0, description="Priority for routing (higher = preferred)")
    tags: List[str] = Field(default_factory=list, description="Tags for routing")
    description: Optional[str] = Field(None, description="Description of this MCP")


class MCPRoutingRule(BaseModel):
    """Routing rule for multi-MCP support"""
    name: str = Field(..., description="Rule name")
    condition_type: str = Field(..., description="Type: 'keyword', 'channel', 'tag'")
    condition_value: str = Field(..., description="Value to match")
    target_mcp: str = Field(..., description="Target MCP name")
    enabled: bool = Field(True, description="Whether this rule is enabled")


class MultiMCPConfig(BaseModel):
    """Configuration for multiple MCP servers"""
    servers: List[MCPServerConfig] = Field(default_factory=list)
    routing_rules: List[MCPRoutingRule] = Field(default_factory=list)
    default_mcp: str = Field("default", description="Default MCP to use")
    fallback_enabled: bool = Field(True, description="Enable fallback to other MCPs")


# Default configuration (single MCP for now)
DEFAULT_MULTI_MCP_CONFIG = MultiMCPConfig(
    servers=[
        MCPServerConfig(
            name="default",
            url="http://localhost:8080/query",
            timeout=5,
            max_retries=3,
            retry_delay=1,
            enabled=True,
            priority=100,
            tags=["general", "news"],
            description="Default MCP server"
        )
    ],
    routing_rules=[],
    default_mcp="default"
)


class MCPRouter:
    """
    Router for multi-MCP support.
    Currently supports single MCP, prepared for future expansion.
    """
    
    def __init__(self, config: MultiMCPConfig = None):
        self.config = config or DEFAULT_MULTI_MCP_CONFIG
    
    def get_mcp_for_request(
        self,
        user_text: str,
        channel: str,
        tags: Optional[List[str]] = None
    ) -> Optional[MCPServerConfig]:
        """
        Determine which MCP server to use for a request.
        
        Args:
            user_text: User's query text
            channel: Channel (whatsapp, telegram, etc.)
            tags: Optional tags for routing
        
        Returns:
            MCPServerConfig or None
        """
        # Check routing rules
        for rule in self.config.routing_rules:
            if not rule.enabled:
                continue
            
            matched = False
            
            if rule.condition_type == "keyword":
                if rule.condition_value.lower() in user_text.lower():
                    matched = True
            
            elif rule.condition_type == "channel":
                if rule.condition_value == channel:
                    matched = True
            
            elif rule.condition_type == "tag" and tags:
                if rule.condition_value in tags:
                    matched = True
            
            if matched:
                # Find target MCP
                for server in self.config.servers:
                    if server.name == rule.target_mcp and server.enabled:
                        return server
        
        # Use default MCP
        for server in self.config.servers:
            if server.name == self.config.default_mcp and server.enabled:
                return server
        
        # Fallback to first enabled MCP
        for server in self.config.servers:
            if server.enabled:
                return server
        
        return None
    
    def get_all_mcps(self) -> List[MCPServerConfig]:
        """Get all configured MCP servers"""
        return self.config.servers
    
    def get_enabled_mcps(self) -> List[MCPServerConfig]:
        """Get all enabled MCP servers"""
        return [s for s in self.config.servers if s.enabled]
    
    def add_mcp(self, server: MCPServerConfig) -> bool:
        """Add a new MCP server"""
        # Check if name already exists
        if any(s.name == server.name for s in self.config.servers):
            return False
        
        self.config.servers.append(server)
        return True
    
    def update_mcp(self, name: str, server: MCPServerConfig) -> bool:
        """Update an existing MCP server"""
        for i, s in enumerate(self.config.servers):
            if s.name == name:
                self.config.servers[i] = server
                return True
        return False
    
    def remove_mcp(self, name: str) -> bool:
        """Remove an MCP server"""
        for i, s in enumerate(self.config.servers):
            if s.name == name:
                self.config.servers.pop(i)
                return True
        return False
    
    def add_routing_rule(self, rule: MCPRoutingRule) -> bool:
        """Add a routing rule"""
        self.config.routing_rules.append(rule)
        return True
    
    def remove_routing_rule(self, name: str) -> bool:
        """Remove a routing rule"""
        for i, r in enumerate(self.config.routing_rules):
            if r.name == name:
                self.config.routing_rules.pop(i)
                return True
        return False


# Global router instance
mcp_router = MCPRouter()
