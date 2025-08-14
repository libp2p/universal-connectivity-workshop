"""
Universal Connectivity Message Protocol
Simple message implementation for the workshop
"""

import time
from enum import IntEnum
from typing import Optional


class MessageType(IntEnum):
    """Message types for the universal connectivity protocol."""
    CHAT = 0
    FILE_SHARE = 1
    PEER_DISCOVERY = 2
    STATUS = 3


class UniversalConnectivityMessage:
    """
    Simple message class that mimics protobuf behavior.
    This is a simplified implementation for the workshop.
    """
    
    def __init__(self):
        self.from_peer: str = ""
        self.message: str = ""
        self.timestamp: int = 0
        self.message_type: MessageType = MessageType.CHAT
        self.data: bytes = b""
    
    def SerializeToString(self) -> bytes:
        """Serialize the message to bytes (simplified implementation)."""
        # Simple serialization format: from_peer|message|timestamp|message_type|data
        parts = [
            self.from_peer.encode('utf-8'),
            self.message.encode('utf-8'),
            str(self.timestamp).encode('utf-8'),
            str(int(self.message_type)).encode('utf-8'),
            self.data
        ]
        
        # Join with separator and include lengths for proper parsing
        serialized = b''
        for part in parts:
            serialized += len(part).to_bytes(4, 'big') + part
        
        return serialized
    
    def ParseFromString(self, data: bytes) -> None:
        """Parse message from bytes (simplified implementation)."""
        try:
            offset = 0
            parts = []
            
            # Parse 5 parts: from_peer, message, timestamp, message_type, data
            for i in range(5):
                if offset + 4 > len(data):
                    raise ValueError("Invalid message format: incomplete length field")
                
                length = int.from_bytes(data[offset:offset+4], 'big')
                offset += 4
                
                if offset + length > len(data):
                    raise ValueError("Invalid message format: incomplete data field")
                
                part = data[offset:offset+length]
                offset += length
                parts.append(part)
            
            # Assign parsed values
            self.from_peer = parts[0].decode('utf-8')
            self.message = parts[1].decode('utf-8')
            self.timestamp = int(parts[2].decode('utf-8'))
            self.message_type = MessageType(int(parts[3].decode('utf-8')))
            self.data = parts[4]
            
        except Exception as e:
            # If parsing fails, create a default message
            self.from_peer = "unknown"
            self.message = "Failed to parse message"
            self.timestamp = int(time.time())
            self.message_type = MessageType.CHAT
            self.data = b""
            raise ValueError(f"Failed to parse message: {e}")
    
    def __str__(self) -> str:
        """String representation of the message."""
        return f"UniversalConnectivityMessage(from_peer='{self.from_peer}', message='{self.message}', timestamp={self.timestamp}, message_type={self.message_type.name})"
    
    def __repr__(self) -> str:
        """Detailed representation of the message."""
        return self.__str__()