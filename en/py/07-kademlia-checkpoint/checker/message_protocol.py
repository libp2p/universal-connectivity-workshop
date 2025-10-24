"""
Universal Connectivity Message Protocol
Simple message implementation for the workshop checker
"""

from enum import IntEnum


class MessageType(IntEnum):
    """Message types for the Universal Connectivity protocol."""
    CHAT = 0
    FILE = 1
    BROWSER_PEER_DISCOVERY = 2


class UniversalConnectivityMessage:
    """
    Simple message class that mimics protobuf structure for the workshop.
    In production, you would use actual protobuf-generated classes.
    """
    
    def __init__(self):
        self.from_peer = ""
        self.message = ""
        self.timestamp = 0
        self.message_type = MessageType.CHAT
    
    def SerializeToString(self) -> bytes:
        """
        Serialize message to bytes using a simple pipe-separated format.
        This is a simplified implementation for the workshop.
        In production, you would use protobuf serialization.
        """
        data = f"{self.from_peer}|{self.message}|{self.timestamp}|{self.message_type}"
        return data.encode('utf-8')
    
    def ParseFromString(self, data: bytes) -> None:
        """
        Parse message from bytes using a simple pipe-separated format.
        This is a simplified implementation for the workshop.
        In production, you would use protobuf deserialization.
        """
        try:
            parts = data.decode('utf-8').split('|')
            if len(parts) >= 4:
                self.from_peer = parts[0]
                self.message = parts[1]
                self.timestamp = int(parts[2])
                self.message_type = MessageType(int(parts[3]))
            else:
                raise ValueError("Invalid message format")
        except (UnicodeDecodeError, ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse message: {e}")