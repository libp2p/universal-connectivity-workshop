#!/usr/bin/env python3
"""
Universal Connectivity Application using py-libp2p with Gossipsub, Kademlia, Identify, and Ping
"""

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
import trio
from multiaddr import Multiaddr
import traceback

from libp2p import new_host
from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.pubsub.gossipsub import GossipSub
from libp2p.pubsub.pubsub import Pubsub
from libp2p.kad_dht.kad_dht import KadDHT, DHTMode
from libp2p.identity.identify import identify_handler_for, ID as IDENTIFY_PROTOCOL
from libp2p.transport.tcp.tcp import TCP
from libp2p.host.ping import PingService, handle_ping, ID as PING_PROTOCOL
from libp2p.security.noise.transport import Transport as NoiseTransport
from libp2p.stream_muxer.muxer_multistream import MuxerMultistream
from libp2p.stream_muxer.yamux.yamux import PROTOCOL_ID as YAMUX_PROTOCOL, Yamux
from libp2p.tools.async_service import background_trio_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("universal-connectivity")

UNIVERSAL_CONNECTIVITY_TOPIC = "universal-connectivity"
PROTOCOL_ID = "/chat/1.0.0"
MAX_READ_LEN = 2**32 - 1

@dataclass
class UniversalConnectivityMessage:
    message_type: str
    data: Dict[str, Any]
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        return json.dumps({
            "message_type": self.message_type,
            "data": self.data,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(
            message_type=data["message_type"],
            data=data["data"],
            timestamp=data.get("timestamp")
        )
    
    @classmethod
    def create_chat_message(cls, message: str, sender_id: str = ""):
        return cls(
            message_type="chat",
            data={"message": message, "sender_id": sender_id}
        )

async def read_stream_data(stream: INetStream, peer_id: str) -> None:
    """Read data from direct stream (for compatibility with direct connections)"""
    while True:
        try:
            read_bytes = await stream.read(MAX_READ_LEN)
            if read_bytes:
                read_string = read_bytes.decode().strip()
                if read_string and read_string != "\n":
                    try:
                        uc_message = UniversalConnectivityMessage.from_json(read_string)
                        if uc_message.message_type == "chat":
                            sender = uc_message.data.get("sender_id", peer_id[:12])
                            content = uc_message.data.get("message", "")
                            print(f"\n💬 {sender}: {content}")
                    except json.JSONDecodeError:
                        print(f"\n💬 {peer_id[:12]}: {read_string}")
        except Exception as e:
            print(f"\n❌ Stream connection lost: {e}")
            break

async def write_stream_data(stream: INetStream, own_peer_id: str) -> None:
    """Handle user input and send messages via stream"""
    async_f = trio.wrap_file(sys.stdin)
    
    while True:
        try:
            line = await async_f.readline()
            if line:
                message_text = line.strip()
                if message_text:
                    msg = UniversalConnectivityMessage.create_chat_message(message_text, own_peer_id[:12])
                    msg_json = msg.to_json() + "\n"
                    await stream.write(msg_json.encode())
                    print(f"✅ You: {message_text}")
        except Exception as e:
            print(f"❌ Send error: {e}")
            break

async def handle_gossipsub_messages(subscription, peer_id: str) -> None:
    """Handle incoming Gossipsub messages"""
    async for message in subscription:
        if str(message.from_id) == peer_id:
            continue  # Skip our own messages
        
        try:
            uc_message = UniversalConnectivityMessage.from_json(message.data.decode())
            if uc_message.message_type == "chat":
                sender = uc_message.data.get("sender_id", str(message.from_id)[:12])
                chat_text = uc_message.data.get("message", "")
                print(f"\n💬 {sender}: {chat_text}")
        except Exception as e:
            logger.debug(f"Error processing Gossipsub message: {e}")
            try:
                raw_text = message.data.decode()
                sender = str(message.from_id)[:12]
                print(f"\n💬 {sender}: {raw_text}")
            except:
                pass

async def handle_connections(host, peer_id: str) -> None:
    """Monitor connection events"""
    connected_peers = set()
    
    while True:
        current_peers = set(str(p) for p in host.get_connected_peers())
        new_peers = current_peers - connected_peers
        for peer in new_peers:
            print(f"✅ Connected to: {peer[:12]}...")
        
        disconnected = connected_peers - current_peers
        for peer in disconnected:
            print(f"❌ Disconnected from: {peer[:12]}")
        
        connected_peers = current_peers
        await trio.sleep(2)

async def connect_to_peers(host, remote_addrs):
    for addr_str in remote_addrs:
        try:
            maddr = Multiaddr(addr_str)
            info = info_from_p2p_addr(maddr)
            host.get_peerstore().add_addrs(info.peer_id, info.addrs, 3600)
            await host.connect(info)
            print(f"✅ Connected to: {addr_str}")

            # Trigger identify exchange
            try:
                stream = await host.new_stream(info.peer_id, [IDENTIFY_PROTOCOL])
                await trio.sleep(0.1)
                try:
                    await stream.read(65536)
                except Exception:
                    pass
                await stream.close()
                await trio.sleep(0.1)  # let peer_protocol populate
            except Exception as e:
                logger.debug(f"Identify exchange with {info.peer_id} failed: {e}")
        except Exception as e:
            logger.error(f"Failed to connect to {addr_str}: {e}")

async def send_intro_message(pubsub, peer_id: str) -> None:
    """Send introductory chat message via Gossipsub (with better error logging)."""
    try:
        # small delay to give the mesh a moment to form
        await trio.sleep(0.5)
        intro_msg = UniversalConnectivityMessage.create_chat_message(
            "Hello from the Universal Connectivity Workshop!",
            peer_id[:12]
        )
        # ensure bytes
        data = intro_msg.to_json().encode() if isinstance(intro_msg.to_json(), str) else intro_msg.to_json()
        await pubsub.publish(UNIVERSAL_CONNECTIVITY_TOPIC, data)
        logger.info("Sent introductory message")
    except Exception as e:
        # log full traceback and the type of exception
        logger.error("Failed to send intro message. Exception type: %s, value: %s", type(e), e, exc_info=True)
       
async def publish_user_input(pubsub, peer_id: str) -> None:
    async_f = trio.wrap_file(sys.stdin)
    print("\nType messages and press Enter to send to the 'universal-connectivity' topic.")
    while True:
        try:
            line = await async_f.readline()
            if not line:
                await trio.sleep(0.1)
                continue
            text = line.strip()
            if not text:
                continue
            msg = UniversalConnectivityMessage.create_chat_message(text, sender_id=peer_id[:12])
            # ensure bytes payload
            payload = msg.to_json().encode() if isinstance(msg.to_json(), str) else msg.to_json()
            await pubsub.publish(UNIVERSAL_CONNECTIVITY_TOPIC, payload)
            print(f"✅ Sent: {text}")
        except Exception as e:
            # show precise info so we can debug the rare exception that prints as PeerID
            logger.error("Publish error. Exception type: %s, value: %s", type(e), e, exc_info=True)
            traceback.print_exc()
            break

async def run(port: int, remote_addrs: list) -> None:
    """Main application"""
    print("Starting Universal Connectivity Application...")
    
    key_pair = create_new_key_pair()
    
    # Setup security and multiplexing
    noise_transport = NoiseTransport(
        libp2p_keypair=key_pair,
        noise_privkey=key_pair.private_key,
    )
    yamux_muxer = MuxerMultistream({YAMUX_PROTOCOL: Yamux})
    tcp_transport = TCP()
    
    # Create host with security and multiplexing
    host = new_host(
        key_pair=key_pair,
        listen_addrs=[f"/ip4/0.0.0.0/tcp/{port}"],
        enable_mDNS=True,
    )
    peer_id = str(host.get_id())
    print(f"🆔 Local peer ID: {peer_id}")
    
    # Configure protocols
    gossipsub = GossipSub(
        protocols=["/gossipsub/1.1.0"],
        degree=3,
        degree_low=2,
        degree_high=4,
        heartbeat_interval=10.0
    )

    pubsub = Pubsub(host, gossipsub)
    dht = KadDHT(host, DHTMode.CLIENT)
    
    # Setup stream handler for direct connections (backward compatibility)
    async def stream_handler(stream: INetStream) -> None:
        remote_peer_id = str(stream.muxed_conn.peer_id)
        print(f"\n🎯 Incoming connection from: {remote_peer_id[:12]}...")
        async with trio.open_nursery() as nursery:
            nursery.start_soon(read_stream_data, stream, remote_peer_id)
            nursery.start_soon(write_stream_data, stream, peer_id)
    
    host.set_stream_handler(PROTOCOL_ID, stream_handler)
    
    # Start host-run and protocol services
    listen_addr = Multiaddr(f"/ip4/0.0.0.0/tcp/{port}")

    async with host.run(listen_addrs=[listen_addr]):
        # print listen addrs
        for addr in host.get_addrs():
            print(f"📡 Listening on: {addr}")

        # Use background_trio_service as an async context manager (no .astart())
        # Start pubsub and dht services together
        async with background_trio_service(pubsub), background_trio_service(dht):

            # Subscribe to the Gossipsub topic AFTER pubsub service is up
            subscription = await pubsub.subscribe(UNIVERSAL_CONNECTIVITY_TOPIC)

            # Open a nursery for concurrent handlers (consumers, monitors, etc.)
            async with trio.open_nursery() as nursery:
                # Monitor connection events
                nursery.start_soon(handle_connections, host, peer_id)
                nursery.start_soon(publish_user_input, pubsub, peer_id)

                # Start pubsub consumer
                nursery.start_soon(handle_gossipsub_messages, subscription, peer_id)

                # Connect to remote peers (if provided)
                if remote_addrs:
                    # connecting is awaited so the connection attempt happens before we publish an intro
                    await connect_to_peers(host, remote_addrs)
                    await trio.sleep(2)  # give it a moment
                    await send_intro_message(pubsub, peer_id)

                print("\n" + "="*60)
                if remote_addrs:
                    print("🔗 CLIENT MODE - Type messages to send via Gossipsub")
                else:
                    print("🎯 SERVER MODE - Waiting for connections")
                    print(f"Run this command in another terminal to connect:")
                    print(f"python3 main.py -p 8001 -c {host.get_addrs()[0]}/p2p/{peer_id}")
                print("="*60)

                # keep the nursery running until cancelled
                try:
                    await trio.sleep_forever()
                except KeyboardInterrupt:
                    # nursery will exit and the async context managers will clean up
                    pass

def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Connectivity Application using py-libp2p")
    parser.add_argument("-p", "--port", default=8000, type=int, help="Port to listen on")
    parser.add_argument("-c", "--connect", action="append", default=[], help="Peer multiaddress to connect to")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get remote peer from environment variable
    remote_addrs = args.connect
    if os.getenv("REMOTE_PEER"):
        remote_addrs.append(os.getenv("REMOTE_PEER"))
    
    try:
        trio.run(run, args.port, remote_addrs)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error("Fatal error:", exc_info=True)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()