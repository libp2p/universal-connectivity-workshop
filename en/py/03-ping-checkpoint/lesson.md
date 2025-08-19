# Lesson 3: Ping Checkpoint 🏆

Welcome to your first checkpoint! In this lesson, you'll implement the ping protocol using `py-libp2p` with the Trio library to establish bidirectional connectivity with a remote peer and measure round-trip times. This lesson builds on basic libp2p concepts and introduces protocol handling and event-driven networking.

## Learning Objectives

By the end of this lesson, you will:
- Understand the purpose and mechanics of the ping protocol in libp2p.
- Implement a working ping protocol using `py-libp2p` and Trio.
- Handle ping requests and responses to measure network performance.
- Successfully connect to remote peers and validate your solution.

## Background: The Ping Protocol

The ping protocol in libp2p serves several purposes:
- **Connectivity Testing**: Verifies bidirectional communication between peers.
- **Latency Measurement**: Measures round-trip time (RTT) to assess network performance.
- **Keep-Alive**: Sends periodic messages to maintain active connections.
- **Network Quality**: Provides insights into connection stability and reliability.

The libp2p ping protocol (`/ipfs/ping/1.0.0`) exchanges 32-byte payloads between peers, with the receiver echoing the data back to measure round-trip time.

## Your Task

You will create two versions:
1. **Basic Version**: Simple ping without encryption/multiplexing
2. **Advanced Version**: With Noise encryption and Yamux multiplexing

## Step-by-Step Instructions

### Step 1: Basic Ping Implementation

Create a file `ping_basic.py`:

```python
import argparse
import os
import multiaddr
import trio
from libp2p import new_host
from libp2p.custom_types import TProtocol
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr

PING_PROTOCOL_ID = TProtocol("/ipfs/ping/1.0.0")
PING_LENGTH = 32
RESP_TIMEOUT = 10

async def handle_ping(stream: INetStream) -> None:
    """Handle incoming ping requests"""
    peer_id = stream.muxed_conn.peer_id
    print(f"incoming,{peer_id}")
    
    while True:
        try:
            payload = await stream.read(PING_LENGTH)
            if payload is None or len(payload) == 0:
                break
            
            print(f"ping,{peer_id},received")
            await stream.write(payload)
            print(f"ping,{peer_id},responded")
            
        except Exception as e:
            print(f"error,Ping handler error: {e}")
            await stream.reset()
            break
    
    print(f"closed,{peer_id}")

async def send_ping(stream: INetStream) -> None:
    """Send ping to remote peer"""
    try:
        payload = b"\x01" * PING_LENGTH
        peer_id = stream.muxed_conn.peer_id
        
        print(f"ping,{peer_id},sending")
        await stream.write(payload)
        
        with trio.fail_after(RESP_TIMEOUT):
            response = await stream.read(PING_LENGTH)
        
        if response == payload:
            print(f"ping,{peer_id},success")
        else:
            print(f"error,Ping response mismatch from {peer_id}")
            
    except trio.TooSlowError:
        print(f"error,Ping timeout to {peer_id}")
    except Exception as e:
        print(f"error,Ping failed to {peer_id}: {e}")

async def run_server(port: int) -> None:
    """Run as ping server"""
    listen_addr = multiaddr.Multiaddr(f"/ip4/0.0.0.0/tcp/{port}")
    host = new_host()
    
    print("Starting Universal Connectivity Application...")
    
    async with host.run(listen_addrs=[listen_addr]):
        host.set_stream_handler(PING_PROTOCOL_ID, handle_ping)
        
        peer_id = host.get_id()
        addrs = host.get_addrs()
        
        print(f"Local peer id: {peer_id}")
        if addrs:
            print(f"Listening on: {addrs[0]}")
            print(f"Full address: {addrs[0]}/p2p/{peer_id}")
        
        print("Waiting for connections...")
        await trio.sleep_forever()

async def run_client(destination: str) -> None:
    """Run as ping client"""
    listen_addr = multiaddr.Multiaddr("/ip4/0.0.0.0/tcp/0")
    host = new_host()
    
    print("Starting Universal Connectivity Application...")
    
    async with host.run(listen_addrs=[listen_addr]), trio.open_nursery() as nursery:
        peer_id = host.get_id()
        print(f"Local peer id: {peer_id}")
        
        # Parse destination
        maddr = multiaddr.Multiaddr(destination)
        info = info_from_p2p_addr(maddr)
        
        print(f"Connecting to: {destination}")
        await host.connect(info)
        print(f"connected,{info.peer_id}")
        
        # Open ping stream
        stream = await host.new_stream(info.peer_id, [PING_PROTOCOL_ID])
        nursery.start_soon(send_ping, stream)

def main():
    parser = argparse.ArgumentParser(description="libp2p ping demo")
    parser.add_argument("-p", "--port", default=8000, type=int, help="Port to listen on")
    parser.add_argument("-d", "--destination", type=str, help="Destination multiaddr")
    
    args = parser.parse_args()
    
    try:
        if args.destination:
            trio.run(run_client, args.destination)
        else:
            trio.run(run_server, args.port)
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
```

### Step 2: Advanced Ping with Noise and Yamux

Create a file `ping_advanced.py`:

```python
import argparse
import os
import multiaddr
import trio
from libp2p import new_host, generate_new_rsa_identity
from libp2p.custom_types import TProtocol
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.security.noise.transport import Transport as NoiseTransport
from libp2p.stream_muxer.yamux.yamux import Yamux, PROTOCOL_ID as YAMUX_PROTOCOL_ID
from cryptography.hazmat.primitives.asymmetric import x25519

PING_PROTOCOL_ID = TProtocol("/ipfs/ping/1.0.0")
PING_LENGTH = 32
RESP_TIMEOUT = 10

class NoisePrivateKey:
    def __init__(self, key):
        self._key = key
    
    def to_bytes(self):
        return self._key.private_bytes_raw()
    
    def public_key(self):
        return NoisePublicKey(self._key.public_key())
    
    def get_public_key(self):
        return self.public_key()

class NoisePublicKey:
    def __init__(self, key):
        self._key = key
    
    def to_bytes(self):
        return self._key.public_bytes_raw()

async def handle_ping(stream: INetStream) -> None:
    """Handle incoming ping requests"""
    peer_id = stream.muxed_conn.peer_id
    print(f"incoming,{peer_id}")
    
    while True:
        try:
            payload = await stream.read(PING_LENGTH)
            if payload is None or len(payload) == 0:
                break
            
            print(f"ping,{peer_id},received")
            await stream.write(payload)
            print(f"ping,{peer_id},responded")
            
        except Exception as e:
            print(f"error,Ping handler error: {e}")
            await stream.reset()
            break
    
    print(f"closed,{peer_id}")

async def send_ping(stream: INetStream) -> None:
    """Send ping to remote peer"""
    try:
        payload = b"\x01" * PING_LENGTH
        peer_id = stream.muxed_conn.peer_id
        
        print(f"ping,{peer_id},sending")
        await stream.write(payload)
        
        with trio.fail_after(RESP_TIMEOUT):
            response = await stream.read(PING_LENGTH)
        
        if response == payload:
            print(f"ping,{peer_id},success")
        else:
            print(f"error,Ping response mismatch from {peer_id}")
            
    except trio.TooSlowError:
        print(f"error,Ping timeout to {peer_id}")
    except Exception as e:
        print(f"error,Ping failed to {peer_id}: {e}")

def create_secure_host():
    """Create a libp2p host with Noise encryption and Yamux multiplexing"""
    # Generate RSA keypair for libp2p identity
    key_pair = generate_new_rsa_identity()
    
    # Generate X25519 keypair for Noise protocol
    x25519_private_key = x25519.X25519PrivateKey.generate()
    noise_privkey = NoisePrivateKey(x25519_private_key)
    
    # Create Noise transport
    noise_transport = NoiseTransport(key_pair, noise_privkey=noise_privkey)
    
    # Configure security and multiplexing
    sec_opt = {TProtocol("/noise"): noise_transport}
    muxer_opt = {TProtocol(YAMUX_PROTOCOL_ID): Yamux}
    
    return new_host(
        key_pair=key_pair,
        sec_opt=sec_opt,
        muxer_opt=muxer_opt
    )

async def run_server(port: int) -> None:
    """Run as secure ping server"""
    listen_addr = multiaddr.Multiaddr(f"/ip4/0.0.0.0/tcp/{port}")
    host = create_secure_host()
    
    print("Starting Universal Connectivity Application...")
    
    async with host.run(listen_addrs=[listen_addr]):
        host.set_stream_handler(PING_PROTOCOL_ID, handle_ping)
        
        peer_id = host.get_id()
        addrs = host.get_addrs()
        
        print(f"Local peer id: {peer_id}")
        if addrs:
            print(f"Listening on: {addrs[0]}")
            print(f"Full address: {addrs[0]}/p2p/{peer_id}")
        
        print("Security: Noise encryption enabled")
        print("Multiplexing: Yamux enabled")
        print("Waiting for connections...")
        await trio.sleep_forever()

async def run_client(destination: str) -> None:
    """Run as secure ping client"""
    listen_addr = multiaddr.Multiaddr("/ip4/0.0.0.0/tcp/0")
    host = create_secure_host()
    
    print("Starting Universal Connectivity Application...")
    
    async with host.run(listen_addrs=[listen_addr]), trio.open_nursery() as nursery:
        peer_id = host.get_id()
        print(f"Local peer id: {peer_id}")
        print("Security: Noise encryption enabled")
        print("Multiplexing: Yamux enabled")
        
        # Parse destination
        maddr = multiaddr.Multiaddr(destination)
        info = info_from_p2p_addr(maddr)
        
        print(f"Connecting to: {destination}")
        await host.connect(info)
        print(f"connected,{info.peer_id}")
        
        # Open ping stream
        stream = await host.new_stream(info.peer_id, [PING_PROTOCOL_ID])
        nursery.start_soon(send_ping, stream)

def main():
    parser = argparse.ArgumentParser(description="Secure libp2p ping demo with Noise and Yamux")
    parser.add_argument("-p", "--port", default=8000, type=int, help="Port to listen on")
    parser.add_argument("-d", "--destination", type=str, help="Destination multiaddr")
    
    args = parser.parse_args()
    
    try:
        if args.destination:
            trio.run(run_client, args.destination)
        else:
            trio.run(run_server, args.port)
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
```

### Step 3: Workshop Integration

For the checkpoint validation, create `main.py` that matches the expected output format:

```python
import os
import trio
from libp2p import new_host, generate_new_rsa_identity
from libp2p.custom_types import TProtocol
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.security.noise.transport import Transport as NoiseTransport
from libp2p.stream_muxer.yamux.yamux import Yamux, PROTOCOL_ID as YAMUX_PROTOCOL_ID
import multiaddr as Multiaddr
from cryptography.hazmat.primitives.asymmetric import x25519
import time
import re


PING_PROTOCOL_ID = TProtocol("/ipfs/ping/1.0.0")
PING_LENGTH = 32

class NoisePrivateKey:
    def __init__(self, key):
        self._key = key
    
    def to_bytes(self):
        return self._key.private_bytes_raw()
    
    def public_key(self):
        return NoisePublicKey(self._key.public_key())
    
    def get_public_key(self):
        return self.public_key()

class NoisePublicKey:
    def __init__(self, key):
        self._key = key
    
    def to_bytes(self):
        return self._key.public_bytes_raw()

def parse_duration(duration_str):
    """Parse duration string like '20s', '5m', '1h' to seconds"""
    if not duration_str:
        return 20.0  # default
    
    # Remove whitespace
    duration_str = duration_str.strip()
    
    # Try to parse as plain number first
    try:
        return float(duration_str)
    except ValueError:
        pass
    
    # Parse with unit suffix
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([smh]?)$', duration_str.lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")
    
    value, unit = match.groups()
    value = float(value)
    
    if unit == 's' or unit == '':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    else:
        raise ValueError(f"Unknown time unit: {unit}")

async def handle_ping(stream: INetStream) -> None:
    """Handle incoming ping requests"""
    try:
        while True:
            start_time = time.time()
            data = await stream.read(PING_LENGTH)
            
            if not data:
                break
            
            await stream.write(data)
            rtt_ms = (time.time() - start_time) * 1000
            print(f"ping,{stream.muxed_conn.peer_id},{int(rtt_ms)} ms")
            
    except Exception as e:
        print(f"error,Ping error: {e}")
    finally:
        try:
            await stream.close()
        except:
            pass

async def send_ping(stream: INetStream):
    """Send ping to remote peer"""
    try:
        payload = b"\x01" * PING_LENGTH
        start_time = time.time()
        
        await stream.write(payload)
        
        with trio.fail_after(5):
            response = await stream.read(PING_LENGTH)
        
        if response == payload:
            rtt_ms = (time.time() - start_time) * 1000
            print(f"ping,{stream.muxed_conn.peer_id},{int(rtt_ms)} ms")
        else:
            print(f"error,Ping response mismatch")
            
    except Exception as e:
        print(f"error,Ping failed: {e}")
    finally:
        try:
            await stream.close()
        except:
            pass

def create_secure_host():
    """Create a libp2p host with Noise encryption and Yamux multiplexing"""
    # Generate RSA keypair for libp2p identity
    key_pair = generate_new_rsa_identity()
    
    # Generate X25519 keypair for Noise protocol
    x25519_private_key = x25519.X25519PrivateKey.generate()
    noise_privkey = NoisePrivateKey(x25519_private_key)
    
    # Create Noise transport
    noise_transport = NoiseTransport(key_pair, noise_privkey=noise_privkey)
    
    # Configure security and multiplexing
    sec_opt = {TProtocol("/noise"): noise_transport}
    muxer_opt = {TProtocol(YAMUX_PROTOCOL_ID): Yamux}
    
    return new_host(
        key_pair=key_pair,
        sec_opt=sec_opt,
        muxer_opt=muxer_opt
    )


async def main():
    print("Starting Universal Connectivity Application...")
    
    # Use the create_secure_host function instead of duplicating code
    host = create_secure_host()
    peer_id = host.get_id()
    print(f"Local peer id: {peer_id}")
    
    # Set ping handler
    host.set_stream_handler(PING_PROTOCOL_ID, handle_ping)
    
    # Start host
    listen_addr = Multiaddr.Multiaddr("/ip4/0.0.0.0/tcp/0")
    
    async with host.run(listen_addrs=[listen_addr]):
        # Print listening addresses
        addrs = host.get_addrs()
        print(f"Listening on:")
        for addr in addrs:
            print(f"  {addr}")
        
        # Connect to remote peers
        remote_peers = os.getenv("REMOTE_PEERS", "")
        
        if remote_peers:
            print(f"Connecting to remote peers: {remote_peers}")
            remote_addrs = [
                Multiaddr.Multiaddr(addr.strip()) for addr in remote_peers.split(",")
                if addr.strip()
            ]
            
            async with trio.open_nursery() as nursery:
                for addr in remote_addrs:
                    try:
                        info = info_from_p2p_addr(addr)
                        await host.connect(info)
                        print(f"connected,{info.peer_id},{addr}")
                        
                        # Open ping stream
                        stream = await host.new_stream(info.peer_id, [PING_PROTOCOL_ID])
                        nursery.start_soon(send_ping, stream)
                        
                    except Exception as e:
                        print(f"error,Failed to connect to {addr}: {e}")
                
                # Wait for timeout - now properly parsing duration
                timeout = parse_duration(os.getenv("TIMEOUT_DURATION", "20"))
                print(f"Running for {timeout} seconds...")
                with trio.move_on_after(timeout):
                    await trio.sleep_forever()
        else:
            # Just wait for incoming connections
            timeout = parse_duration(os.getenv("TIMEOUT_DURATION", "20"))
            print(f"No remote peers configured. Waiting for incoming connections for {timeout} seconds...")
            with trio.move_on_after(timeout):
                await trio.sleep_forever()
        
        print("Application finished.")

if __name__ == "__main__":
    trio.run(main)
```

## Testing Your Implementation

### Linux/Mac Commands:

#### Test Basic Ping:
```bash
# Terminal 1 - Start server
python ping_basic.py -p 8000

# Terminal 2 - Connect as client (replace PEER_ID with actual ID from server)
python ping_basic.py -d /ip4/127.0.0.1/tcp/8000/p2p/PEER_ID
```

#### Test Advanced Ping:
```bash
# Terminal 1 - Start secure server
python ping_advanced.py -p 8001

# Terminal 2 - Connect as secure client
python ping_advanced.py -d /ip4/127.0.0.1/tcp/8001/p2p/PEER_ID
```

### Windows Commands:

#### Test Basic Ping:
```cmd
REM Terminal 1 - Start server
python ping_basic.py -p 8000

REM Terminal 2 - Connect as client (replace PEER_ID with actual ID from server)
python ping_basic.py -d /ip4/127.0.0.1/tcp/8000/p2p/PEER_ID
```

#### Test Advanced Ping:
```cmd
REM Terminal 1 - Start secure server
python ping_advanced.py -p 8001

REM Terminal 2 - Connect as secure client
python ping_advanced.py -d /ip4/127.0.0.1/tcp/8001/p2p/PEER_ID
```

### Docker Workshop Commands:

#### Linux/Mac:
```bash
export PROJECT_ROOT=/path/to/workshop
export LESSON_PATH=uc-workshop/en/py/03-ping-checkpoint
cd $PROJECT_ROOT/$LESSON_PATH

# Clean up
docker rm -f workshop-lesson ucw-checker-03-ping-checkpoint
docker network rm -f workshop-net

# Run workshop
docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
docker compose --project-name workshop up --build --remove-orphans

# Check results
python check.py
```

#### Windows:
```cmd
set PROJECT_ROOT=C:\path\to\workshop
set LESSON_PATH=uc-workshop\en\py\03-ping-checkpoint
cd %PROJECT_ROOT%\%LESSON_PATH%

REM Clean up
docker rm -f workshop-lesson ucw-checker-03-ping-checkpoint
docker network rm -f workshop-net

REM Run workshop
docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
docker compose --project-name workshop up --build --remove-orphans

REM Check results
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Successfully establish connections with remote peers
- ✅ Handle incoming ping requests and send appropriate responses
- ✅ Send ping requests and measure round-trip times
- ✅ Output logs in the expected format for validation
- ✅ Work with both basic and secure (Noise + Yamux) configurations

## Troubleshooting

**Common Issues:**

1. **Import Errors**: Ensure py-libp2p is installed: `pip install libp2p`
2. **Connection Refused**: Check if the server is running and ports are available
3. **Peer ID Mismatch**: Copy the exact peer ID from server output
4. **Timeout Issues**: Increase RESP_TIMEOUT if network is slow
5. **Windows Path Issues**: Use forward slashes in multiaddrs: `/ip4/127.0.0.1/tcp/8000`

**Debug Tips:**
- Add `import logging; logging.basicConfig(level=logging.DEBUG)` for detailed logs
- Use `netstat -an | grep :8000` (Linux/Mac) or `netstat -an | findstr :8000` (Windows) to check if port is listening
- Test with basic version first, then advance to secure version

## What's Next?

Congratulations! You've successfully implemented the libp2p ping protocol 🎉

You've learned:
- **Protocol Implementation**: How to handle libp2p protocols with stream handlers
- **Async Programming**: Using Trio for concurrent networking operations
- **Security**: Adding Noise encryption and Yamux multiplexing
- **Connection Management**: Establishing and maintaining peer connections

In the next lesson, you'll explore more advanced libp2p features like DHT (Distributed Hash Table) and content routing!