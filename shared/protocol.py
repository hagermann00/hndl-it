"""
hndl-it Protocol Definitions
Shared message format for all agents
"""

from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum
import json


class MessageType(str, Enum):
    # From Floater to Agent
    COMMAND = "command"
    PING = "ping"
    
    # From Agent to Floater
    RESPONSE = "response"
    ACTION = "action"
    ERROR = "error"
    CONFIRM = "confirm"
    PROGRESS = "progress"
    PONG = "pong"


@dataclass
class Message:
    type: MessageType
    content: str = ""
    data: Optional[dict] = None
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "content": self.content,
            "data": self.data
        })
    
    @classmethod
    def from_json(cls, raw: str) -> "Message":
        obj = json.loads(raw)
        return cls(
            type=MessageType(obj.get("type", "command")),
            content=obj.get("content", ""),
            data=obj.get("data")
        )


@dataclass  
class Action:
    """Browser/Desktop action to execute"""
    type: str  # navigate, click, type, scroll, etc.
    target: Optional[str] = None  # URL, selector, coordinates
    value: Optional[str] = None   # Text to type, scroll amount
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "target": self.target,
            "value": self.value,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Action":
        return cls(
            type=d.get("type", ""),
            target=d.get("target") or d.get("url") or d.get("selector"),
            value=d.get("value") or d.get("text"),
            description=d.get("description", "")
        )
