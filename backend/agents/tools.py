"""
Enhanced Tool Management System for Agents
Provides tool discovery, execution tracking, and caching capabilities
"""
import logging
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class ToolExecutionTracker:
    """
    Tracks tool executions for monitoring and learning
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.execution_history: List[Dict[str, Any]] = []
        self.tool_statistics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "avg_duration": 0.0,
            "last_used": None
        })
    
    def record_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        success: bool,
        duration: float,
        error: Optional[str] = None
    ):
        """
        Record a tool execution
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments passed to the tool
            result: Result returned by the tool
            success: Whether execution was successful
            duration: Execution duration in seconds
            error: Error message if execution failed
        """
        execution_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_name,
            "arguments": arguments,
            "result": str(result)[:500] if result else None,  # Limit result size
            "success": success,
            "duration": duration,
            "error": error
        }
        
        self.execution_history.append(execution_record)
        
        # Update statistics
        stats = self.tool_statistics[tool_name]
        stats["total_calls"] += 1
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        # Update average duration
        prev_avg = stats["avg_duration"]
        total = stats["total_calls"]
        stats["avg_duration"] = (prev_avg * (total - 1) + duration) / total
        stats["last_used"] = datetime.now(timezone.utc).isoformat()

    def get_tool_statistics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a specific tool or all tools
        
        Args:
            tool_name: Optional tool name to filter by
        
        Returns:
            Dictionary of tool statistics
        """
        if tool_name:
            return dict(self.tool_statistics.get(tool_name, {}))
        else:
            return {name: dict(stats) for name, stats in self.tool_statistics.items()}
    
    def get_execution_history(
        self,
        tool_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get execution history
        
        Args:
            tool_name: Optional tool name to filter by
            limit: Maximum number of records to return
        
        Returns:
            List of execution records
        """
        if tool_name:
            history = [
                record for record in self.execution_history
                if record["tool_name"] == tool_name
            ]
        else:
            history = self.execution_history
        
        return history[-limit:]
    
    def get_most_used_tools(self, limit: int = 5) -> List[Tuple[str, int]]:
        """
        Get most frequently used tools
        
        Args:
            limit: Number of tools to return
        
        Returns:
            List of (tool_name, call_count) tuples
        """
        sorted_tools = sorted(
            self.tool_statistics.items(),
            key=lambda x: x[1]["total_calls"],
            reverse=True
        )
        
        return [(name, stats["total_calls"]) for name, stats in sorted_tools[:limit]]

class ToolResultCache:
    """
    Caches tool execution results to avoid redundant calls
    """
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
            max_size: Maximum number of entries to cache
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_cache_key(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Generate a cache key from tool name and arguments"""
        # Create a deterministic string representation
        args_str = json.dumps(arguments, sort_keys=True)
        combined = f"{tool_name}:{args_str}"
        
        # Hash it for a fixed-length key
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        """
        Get a cached result if available and not expired
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments used for the tool call
        
        Returns:
            Cached result or None if not found or expired
        """
        key = self._generate_cache_key(tool_name, arguments)
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        cached_time = datetime.fromisoformat(entry["timestamp"])
        
        # Check if expired
        if datetime.now(timezone.utc) - cached_time > timedelta(seconds=self.ttl_seconds):
            del self.cache[key]
            return None

        return entry["result"]
    
    def set(self, tool_name: str, arguments: Dict[str, Any], result: Any):
        """
        Cache a tool execution result
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments used for the tool call
            result: Result to cache
        """
        # Enforce max size (simple FIFO eviction)
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k]["timestamp"]
            )
            del self.cache[oldest_key]
        
        key = self._generate_cache_key(tool_name, arguments)
        self.cache[key] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result
        }

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }

class ToolCapability:
    """
    Represents a tool capability with metadata
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        parameters: Dict[str, Any],
        server_name: Optional[str] = None,
        is_builtin: bool = False
    ):
        self.name = name
        self.description = description
        self.category = category
        self.parameters = parameters
        self.server_name = server_name
        self.is_builtin = is_builtin
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "server_name": self.server_name,
            "is_builtin": self.is_builtin
        }
    
    def matches_query(self, query: str) -> bool:
        """Check if tool matches a search query"""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower() or
            query_lower in self.description.lower() or
            query_lower in self.category.lower()
        )

class EnhancedToolManager:
    """
    Enhanced tool management with discovery, tracking, and caching
    """
    
    def __init__(self, agent_id: str, mcp_client: Optional[Any] = None):
        self.agent_id = agent_id
        self.mcp_client = mcp_client
        
        # Tool tracking and caching
        self.tracker = ToolExecutionTracker(agent_id)
        self.cache = ToolResultCache(ttl_seconds=300, max_size=100)
        
        # Tool registry
        self.tools: Dict[str, ToolCapability] = {}
        
        # Built-in tools
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in tool capabilities"""
        # Example built-in tools that don't require MCP
        
        # Text processing tools
        self.tools["text_summarize"] = ToolCapability(
            name="text_summarize",
            description="Summarize a long text into key points",
            category="text_processing",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                    "max_length": {"type": "integer", "description": "Maximum summary length"}
                },
                "required": ["text"]
            },
            is_builtin=True
        )
        
        self.tools["text_extract_keywords"] = ToolCapability(
            name="text_extract_keywords",
            description="Extract keywords from text",
            category="text_processing",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "count": {"type": "integer", "description": "Number of keywords to extract"}
                },
                "required": ["text"]
            },
            is_builtin=True
        )
        
    
    async def discover_tools(self) -> List[ToolCapability]:
        """
        Discover all available tools from MCP servers
        
        Returns:
            List of available tools
        """
        if not self.mcp_client:
            return list(self.tools.values())
        
        try:
            mcp_tools = await self.mcp_client.list_tools()
            
            for server_name, server_tools in mcp_tools.items():
                for tool in server_tools:
                    tool_name = f"{server_name}_{tool['name']}"
                    
                    # Categorize based on server name
                    category = server_name
                    
                    self.tools[tool_name] = ToolCapability(
                        name=tool_name,
                        description=tool.get('description', ''),
                        category=category,
                        parameters=tool.get('input_schema', {}),
                        server_name=server_name,
                        is_builtin=False
                    )
            
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id}: Error discovering MCP tools: {e}")
        
        return list(self.tools.values())
    
    def search_tools(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[ToolCapability]:
        """
        Search for tools by query or category
        
        Args:
            query: Search query (matches name, description, category)
            category: Filter by category
        
        Returns:
            List of matching tools
        """
        results = list(self.tools.values())
        
        if category:
            results = [t for t in results if t.category == category]
        
        if query:
            results = [t for t in results if t.matches_query(query)]
        
        return results
    
    def get_tool_by_name(self, name: str) -> Optional[ToolCapability]:
        """Get a tool by its name"""
        return self.tools.get(name)
    
    def get_tool_categories(self) -> List[str]:
        """Get all tool categories"""
        return list(set(tool.category for tool in self.tools.values()))
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        use_cache: bool = True
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute a tool with tracking and caching
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            use_cache: Whether to use cached results
        
        Returns:
            Tuple of (success, result, error_message)
        """
        start_time = datetime.now(timezone.utc)
        
        # Check cache first
        if use_cache:
            cached_result = self.cache.get(tool_name, arguments)
            if cached_result is not None:
                # Record cached execution
                self.tracker.record_execution(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=cached_result,
                    success=True,
                    duration=0.0
                )
                return True, cached_result, None
        
        # Execute tool
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                error = f"Tool '{tool_name}' not found"
                return False, None, error
            
            if tool.is_builtin:
                # Execute built-in tool
                result = await self._execute_builtin_tool(tool_name, arguments)
            else:
                # Execute MCP tool
                if not self.mcp_client:
                    error = "MCP client not available"
                    return False, None, error
                
                # Parse server name and tool name
                parts = tool_name.split('_', 1)
                if len(parts) != 2:
                    error = f"Invalid tool name format: {tool_name}"
                    return False, None, error
                
                server_name, actual_tool_name = parts
                
                result = await self.mcp_client.call_tool(
                    server_name=server_name,
                    tool_name=actual_tool_name,
                    arguments=arguments
                )
            
            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Cache result
            if use_cache:
                self.cache.set(tool_name, arguments, result)
            
            # Record execution
            self.tracker.record_execution(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=True,
                duration=duration
            )
            
            return True, result, None
            
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            error_msg = str(e)
            
            # Record failed execution
            self.tracker.record_execution(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                duration=duration,
                error=error_msg
            )
            
            logger.error(f"Agent {self.agent_id}: Tool execution failed: {error_msg}")
            return False, None, error_msg
    
    async def _execute_builtin_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute a built-in tool"""
        if tool_name == "text_summarize":
            text = arguments.get("text", "")
            max_length = arguments.get("max_length", 200)
            # Simple summarization (truncate to max length)
            return text[:max_length] + ("..." if len(text) > max_length else "")
        
        elif tool_name == "text_extract_keywords":
            text = arguments.get("text", "")
            count = arguments.get("count", 5)
            # Simple keyword extraction (most common words)
            words = text.lower().split()
            # Filter out common stop words
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
            keywords = [w for w in words if w not in stop_words and len(w) > 3]
            # Count frequency
            counter = Counter(keywords)
            return [word for word, _ in counter.most_common(count)]
        
        else:
            raise ValueError(f"Unknown built-in tool: {tool_name}")
    
    def get_execution_report(self) -> Dict[str, Any]:
        """Get a comprehensive execution report"""
        return {
            "total_tools": len(self.tools),
            "builtin_tools": len([t for t in self.tools.values() if t.is_builtin]),
            "mcp_tools": len([t for t in self.tools.values() if not t.is_builtin]),
            "tool_statistics": self.tracker.get_tool_statistics(),
            "most_used_tools": self.tracker.get_most_used_tools(limit=5),
            "cache_stats": self.cache.get_cache_stats()
        }
