"""
Airweave Client - Python bridge to Airweave MCP Search Server
Part of hndl-it Antigravity ecosystem

Provides semantic memory retrieval for the orchestrator.
Calls the local Airweave MCP server via subprocess or HTTP.
"""

import subprocess
import json
import logging
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("hndl-it.airweave")

@dataclass
class AirweaveResult:
    """A single search result from Airweave."""
    score: float
    title: str
    content: str
    source_name: str
    entity_id: str
    metadata: Dict[str, Any]

    def to_a2ui_card(self) -> Dict[str, Any]:
        """Convert to A2UI Card component format."""
        return {
            "type": "Card",
            "id": f"airweave_{self.entity_id}",
            "props": {
                "title": self.title,
                "subtitle": f"Score: {self.score:.2f} | Source: {self.source_name}",
                "elevation": 2
            },
            "children": [
                {
                    "type": "Text",
                    "id": f"airweave_{self.entity_id}_content",
                    "props": {
                        "text": self.content[:300] + "..." if len(self.content) > 300 else self.content
                    }
                },
                {
                    "type": "Button",
                    "id": f"airweave_{self.entity_id}_expand",
                    "props": {
                        "label": "View Full",
                        "action": "expand_result",
                        "payload": {"entity_id": self.entity_id}
                    }
                }
            ]
        }


class AirweaveClient:
    """
    Client for Airweave semantic memory retrieval.
    
    Supports two modes:
    1. MCP Mode: Calls the Node.js MCP server via subprocess
    2. HTTP Mode: Calls the hosted API directly
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        collection: Optional[str] = None,
        base_url: str = "http://localhost:8001",
        mode: str = "http"  # "http" or "mcp"
    ):
        self.api_key = api_key or os.environ.get("AIRWEAVE_API_KEY", "")
        self.collection = collection or os.environ.get("AIRWEAVE_COLLECTION", "default")
        self.base_url = base_url
        self.mode = mode
        
        # Path to MCP server (for mcp mode)
        self.mcp_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "AG_HANDS", "airweave", "mcp"
        )
        
        logger.info(f"AirweaveClient initialized: mode={mode}, collection={collection}")

    def search(
        self,
        query: str,
        limit: int = 10,
        recency_bias: float = 0.3,
        score_threshold: float = 0.5
    ) -> List[AirweaveResult]:
        """
        Search Airweave for semantically similar content.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            recency_bias: Weight for recency (0-1)
            score_threshold: Minimum similarity score
            
        Returns:
            List of AirweaveResult objects
        """
        try:
            if self.mode == "http":
                return self._search_http(query, limit, recency_bias, score_threshold)
            else:
                return self._search_mcp(query, limit, recency_bias, score_threshold)
        except Exception as e:
            logger.error(f"Airweave search failed: {e}")
            return []

    def store(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store content in Airweave.

        Args:
            content: The text content to store
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mode == "http":
                return self._store_http(content, metadata)
            else:
                return self._store_mcp(content, metadata)
        except Exception as e:
            logger.error(f"Airweave store failed: {e}")
            return False

    def _search_http(
        self,
        query: str,
        limit: int,
        recency_bias: float,
        score_threshold: float
    ) -> List[AirweaveResult]:
        """Search via HTTP API."""
        import requests
        
        url = f"{self.base_url}/collections/{self.collection}/search"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        
        params = {
            "query": query,
            "limit": limit,
            "recency_bias": recency_bias,
            "score_threshold": score_threshold,
            "response_type": "raw"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_results(data.get("results", []))

    def _store_http(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store via HTTP API."""
        import requests

        url = f"{self.base_url}/collections/{self.collection}/documents"
        headers = {"x-api-key": self.api_key} if self.api_key else {}

        payload = {
            "documents": [
                {
                    "content": content,
                    "metadata": metadata or {}
                }
            ]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return True

    def _search_mcp(
        self,
        query: str,
        limit: int,
        recency_bias: float,
        score_threshold: float
    ) -> List[AirweaveResult]:
        """Search via MCP subprocess call."""
        # Build MCP tool call request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": f"search-{self.collection}",
                "arguments": {
                    "query": query,
                    "limit": limit,
                    "recency_bias": recency_bias,
                    "score_threshold": score_threshold
                }
            }
        }
        
        # Set up environment for MCP server
        env = os.environ.copy()
        env["AIRWEAVE_API_KEY"] = self.api_key
        env["AIRWEAVE_COLLECTION"] = self.collection
        env["AIRWEAVE_BASE_URL"] = self.base_url
        
        # Call MCP server
        result = subprocess.run(
            ["npx", "airweave-mcp-search"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            env=env,
            cwd=self.mcp_path,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"MCP search failed: {result.stderr}")
            return []
        
        # Parse MCP response
        response = json.loads(result.stdout)
        if "error" in response:
            logger.error(f"MCP error: {response['error']}")
            return []
        
        content = response.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            data = json.loads(content[0]["text"])
            return self._parse_results(data.get("results", []))
        
        return []

    def _store_mcp(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store via MCP subprocess call."""
        # TODO: Implement MCP store tool when available
        logger.warning("MCP store mode not yet implemented. Please use HTTP mode.")
        return False

    def _parse_results(self, raw_results: List[Dict]) -> List[AirweaveResult]:
        """Parse raw API results into AirweaveResult objects."""
        results = []
        for item in raw_results:
            payload = item.get("payload", {})
            results.append(AirweaveResult(
                score=item.get("score", 0.0),
                title=payload.get("title", "Untitled"),
                content=payload.get("md_content", payload.get("content", "")),
                source_name=payload.get("source_name", "Unknown"),
                entity_id=payload.get("entity_id", ""),
                metadata=payload.get("metadata", {})
            ))
        return results

    def to_a2ui(self, results: List[AirweaveResult]) -> Dict[str, Any]:
        """
        Convert search results to full A2UI component tree.
        
        Returns a List component containing Cards for each result.
        """
        if not results:
            return {
                "type": "Card",
                "id": "airweave_no_results",
                "props": {"title": "No Results", "elevation": 1},
                "children": [
                    {"type": "Text", "id": "no_results_text", "props": {"text": "No matching documents found."}}
                ]
            }
        
        return {
            "type": "List",
            "id": "airweave_results",
            "props": {"title": f"Found {len(results)} results"},
            "children": [r.to_a2ui_card() for r in results]
        }


# Singleton instance
_client: Optional[AirweaveClient] = None

def get_airweave_client() -> AirweaveClient:
    """Get or create the global AirweaveClient instance."""
    global _client
    if _client is None:
        _client = AirweaveClient()
    return _client
