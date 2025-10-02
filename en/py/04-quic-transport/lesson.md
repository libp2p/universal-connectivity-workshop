# Lesson 4: QUIC Transport

Now that you understand TCP transport, let's explore QUIC - a modern UDP-based transport protocol that provides built-in encryption and multiplexing. You'll learn about py-libp2p's multi-transport capabilities by connecting to a remote peer with both TCP and QUIC simultaneously.

## Learning Objectives

By the end of this lesson, you will:
- Understand the advantages of QUIC over TCP
- Configure multi-transport py-libp2p hosts
- Handle connections over different transport protocols
- Connect to remote peers using QUIC multiaddresses

## Background: QUIC Transport

QUIC (Quick UDP Internet Connections) is a modern transport protocol that offers several advantages over TCP:

- **Built-in Security**: Encryption is integrated into the protocol (no separate TLS layer needed)
- **Reduced Latency**: Fewer round-trips for connection establishment
- **Better Multiplexing**: Streams don't block each other (no head-of-line blocking)
- **Connection Migration**: Connections can survive network changes
- **UDP-based**: Can traverse NATs more easily than TCP

## Transport Comparison

Remember back in Lesson 2, you learned that the libp2p stack looks like the following when using TCP, Noise, and Yamux:

```
Application protocols (ping, gossipsub, etc.)
    ↕
Multiplexer (Yamux)
    ↕
Security (Noise)
    ↕
Transport (TCP)
    ↕
Network (IP)
```

In this lesson you will add the ability to connect to remote peers using the QUIC transport. Because it has integrated encryption and multiplexing, the libp2p stack looks like the following when using QUIC:

```
Application protocols (ping, gossipsub, etc.)
    ↕
──────────────┐
Multiplexer   │
Security    (QUIC)
Transport     │
──────────────┘
    ↕
Network (IP)
```

## Your Task

Extend your ping application to support both TCP and QUIC transports:

1. **Add QUIC Transport**: Configure QUIC alongside your existing TCP transport
2. **Multi-Transport Configuration**: Create a host that can handle both protocols
3. **Connect via QUIC**: Use a QUIC multiaddress to connect to the remote peer
4. **Handle Transport Events**: Display connection information for both transports

## Step-by-Step Instructions

### Step 1: Update Dependencies

Add QUIC support to your requirements.txt:

```txt
libp2p>=0.2.9
trio>=0.22.0
multiaddr>=0.0.9
```

The py-libp2p package includes QUIC transport support by default in recent versions.

### Step 2: Import Required Modules

Update your imports to include QUIC transport:

```python
import os
import time

import trio
from multiaddr import Multiaddr

from libp2p import new_host, generate_new_rsa_identity
from libp2p.custom_types import TProtocol
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr

# Try to import QUIC transport - if this fails, QUIC isn't supported in this version
try:
    from libp2p.transport.quic.transport import QUICTransport
    QUIC_AVAILABLE = True
except ImportError as e:
    print(f"QUIC transport not available: {e}")
    QUIC_AVAILABLE = False
    QUICTransport = None

PING_PROTOCOL_ID = TProtocol("/ipfs/ping/1.0.0")
PING_LENGTH = 32
```

### Step 3: Class Definition and Initialization

```python
class QUICPingApp:
    """
    A libp2p application that uses QUIC transport for ping functionality.
    """
    
    def __init__(self):
        self.quic_host = None
        self.peer_id = None
        self.running = True
```

This block defines the `QUICPingApp` class, which encapsulates the logic for a libp2p application that uses QUIC transport to implement a ping functionality. The class includes a docstring describing its purpose. In the `__init__` method, three instance variables are initialized: `self.quic_host` is set to `None` and will later store the libp2p host object using QUIC transport, `self.peer_id` is set to None and will store the peer ID of the host, and `self.running` is set to `True` to control the application's main loop, allowing it to be stopped gracefully.

### Step 4: Creating a QUIC Host

```python
    async def create_quic_host(self):
        """Create a QUIC host."""
        if not QUIC_AVAILABLE:
            print("❌ QUIC transport not available, cannot proceed")
            return None
            
        try:
            # Generate keypair for QUIC host
            key_pair = generate_new_rsa_identity()
            
            # Create QUIC transport
            quic_transport = QUICTransport(key_pair.private_key)
            
            # Create a basic host first
            host = new_host(key_pair=key_pair)
            swarm = host.get_network()
            swarm.transport = quic_transport
            
            if hasattr(quic_transport, 'set_swarm'):
                quic_transport.set_swarm(swarm)
            
            print("✅ QUIC host created successfully")
            return host
            
        except Exception as e:
            print(f"❌ Failed to create QUIC host: {e}")
            import traceback
            traceback.print_exc()
            return None
```

This block defines the `create_quic_host method`, an asynchronous function responsible for setting up a libp2p host with QUIC transport. The method first checks if `QUIC_AVAILABLE` is `False`, printing an error message and returning `None` if QUIC is not supported. If QUIC is available, the method proceeds within a try-except block to handle potential errors. It generates a new RSA key pair using `generate_new_rsa_identity` for secure communication. A `QUICTransport` object is created with the private key from the key pair. A basic libp2p host is then created using `new_host` with the generated key pair. The method retrieves the host's network swarm and replaces its default transport with the `QUICTransport` object. If the `QUICTransport` object has a `set_swarm` method, it is called to associate the transport with the swarm, ensuring proper configuration. If the host creation is successful, a success message is printed, and the host object is returned. If an exception occurs, an error message is printed along with a stack trace, and `None` is returned.

### Step 5: Handling Incoming Ping Requests

```python
    async def handle_ping(self, stream: INetStream) -> None:
        """Handle incoming ping requests over QUIC."""
        try:
            while True:
                start_time = time.time()
                data = await stream.read(PING_LENGTH)
                
                if not data:
                    break
                
                await stream.write(data)
                rtt_ms = (time.time() - start_time) * 1000
                peer_id = stream.muxed_conn.peer_id
                print(f"📨 Received QUIC ping from {peer_id}, RTT: {int(rtt_ms)} ms")
                
        except Exception as e:
            print(f"❌ Ping handler error: {e}")
        finally:
            try:
                await stream.close()
            except:
                pass
```

This block defines the `handle_ping` method, an asynchronous function that processes incoming ping requests over a QUIC stream. The method runs in a loop to continuously handle incoming data. It records the start time using `time.time()` and reads `PING_LENGTH` bytes (32 bytes) from the provided `INetStream` stream. If no data is received (indicating the stream has closed), the loop breaks. Otherwise, the received data is written back to the stream as a response, effectively echoing the ping. The round-trip time (RTT) is calculated by subtracting the start time from the current time and converting to milliseconds. The peer ID is extracted from the stream's multiplexed connection, and a message is printed showing the peer ID and the RTT. If an exception occurs, an error message is printed. In the `finally` block, the method attempts to close the stream to clean up resources, ignoring any errors during closure.

### Step 6: Sending Pings to Remote Peers

```python
    async def send_ping(self, stream: INetStream):
        """Send ping to remote peer and measure RTT over QUIC."""
        try:
            payload = b"\x01" * PING_LENGTH
            peer_id = stream.muxed_conn.peer_id
            
            while self.running:
                start_time = time.time()
                await stream.write(payload)
                
                with trio.fail_after(5):
                    response = await stream.read(PING_LENGTH)
                
                if response == payload:
                    rtt_ms = (time.time() - start_time) * 1000
                    print(f"🏓 QUIC ping to {peer_id}, RTT: {int(rtt_ms)} ms")
                else:
                    print(f"❌ QUIC ping response mismatch from {peer_id}")
                
                # Wait 1 second between pings
                await trio.sleep(1)
                
        except trio.TooSlowError:
            print(f"⏱️ QUIC ping timeout to {peer_id}")
        except Exception as e:
            print(f"❌ QUIC ping failed to {peer_id}: {e}")
        finally:
            try:
                await stream.close()
            except:
                pass
```

This block defines the `send_ping` method, an asynchronous function that sends ping messages to a remote peer over a QUIC stream and measures the RTT. A payload of 32 bytes (all 0x01) is created. The peer ID is obtained from the stream's multiplexed connection. The method runs in a loop as long as `self.running` is `True`. In each iteration, it records the start time, writes the payload to the stream, and waits for a response with a 5-second timeout enforced by `trio.fail_after`. If a response is received, it checks if it matches the sent payload. If it matches, the RTT is calculated and printed; otherwise, a mismatch error is printed. The method waits for 1 second before sending the next ping. If a timeout occurs (`trio.TooSlowError`), a timeout message is printed. Other exceptions result in an error message with the peer ID. The `finally` block ensures the stream is closed, ignoring any closure errors.

### Step 7: Dialing a Remote Peer

```python
    async def dial_peer(self, addr_str: str):
        """Dial a peer using QUIC."""
        try:
            addr = Multiaddr(addr_str)
            print(f"🔄 Dialing peer at: {addr} via QUIC")
            
            # Parse peer info from multiaddr
            info = info_from_p2p_addr(addr)
            await self.quic_host.connect(info)
            
            print(f"✅ Connected to: {info.peer_id} via QUIC")
            
            # Open ping stream
            stream = await self.quic_host.new_stream(info.peer_id, [PING_PROTOCOL_ID])
            
            # Start ping loop
            await self.send_ping(stream)
            
        except Exception as e:
            print(f"❌ Failed to connect via QUIC to {addr_str}: {e}")
```

This block defines the `dial_peer` method, an asynchronous function that establishes a connection to a remote peer using QUIC. It takes a multi-address string (`addr_str`) and converts it to a `Multiaddr` object. The method prints a message indicating it is dialing the peer. It parses the peer information from the address using `info_from_p2p_addr` and connects to the peer using the `quic_host.connect` method. Upon successful connection, it prints a confirmation message with the peer ID. A new stream is opened to the peer using the ``PING_PROTOCOL_ID`, and the `send_ping` method is called to start sending pings. If any exception occurs during this process, an error message is printed with the address and the error details.

### Step 8: Running the QUIC Host

```python
    async def run_host(self, host, listen_addr: Multiaddr):
        """Run the QUIC host with error handling."""
        try:
            # Set ping handler
            host.set_stream_handler(PING_PROTOCOL_ID, self.handle_ping)
            
            async with host.run(listen_addrs=[listen_addr]):
                # Print listening addresses
                addrs = host.get_addrs()
                if addrs:
                    print(f"🎧 QUIC listening on:")
                    for addr in addrs:
                        print(f"  {addr}")
                
                await trio.sleep_forever()
                
        except Exception as e:
            print(f"❌ QUIC host failed: {e}")
            raise
```
This block defines the `run_host` method, an asynchronous function that starts the QUIC host and sets it up to listen for incoming connections. The method configures the host to use the `handle_ping` method for streams with the `PING_PROTOCOL_ID`. It then starts the host using the provided `listen_addr` (a Multiaddr object) within an async with block, which ensures proper resource cleanup. The method retrieves and prints the addresses the host is listening on. The `trio.sleep_forever()` call keeps the host running indefinitely to handle incoming connections. If an exception occurs, an error message is printed, and the exception is re-raised to be handled by the caller.

### Step 9: Printing Connection Command

```python
    def print_connection_command(self):
        """Print ready-to-use command for connecting from another terminal."""
        if not self.quic_host:
            print("❌ No QUIC host available to generate connection command")
            return
        
        print("ℹ️ No remote peers specified. To connect from another terminal, copy-paste this:")
        quic_addrs = [str(addr) for addr in self.quic_host.get_addrs() if "/quic" in str(addr)]
        for addr in quic_addrs:
            dial_addr = addr.replace("/ip4/0.0.0.0/", "/ip4/127.0.0.1/")
            print(f"$env:REMOTE_PEERS='{dial_addr}'; python app/main.py")
        
        print("⏳ Waiting for incoming connections...")
```

This block defines the `print_connection_command` method, which generates and prints a command that another instance of the application can use to connect to this host. If no `quic_host` exists, an error message is printed, and the method returns. Otherwise, it retrieves the host's listening addresses, filters for those using QUIC (containing "/quic"), and converts them to strings. Each address is modified to replace `0.0.0.0` with `127.0.0.1` for local testing. The method prints a command that sets the `REMOTE_PEERS` environment variable with the modified address and runs the `app/main.py` script. Finally, it prints a message indicating the host is waiting for connections.

### Step 10: Main Application Loop

```python
    async def run(self):
        """Main application loop for QUIC ping."""
        print("🚀 Starting QUIC Ping Application...")
        
        # Create QUIC host
        if not QUIC_AVAILABLE:
            print("❌ QUIC transport not available, exiting...")
            return
        
        print("🔧 Attempting to create QUIC host...")
        self.quic_host = await self.create_quic_host()
        if not self.quic_host:
            print("❌ Failed to create QUIC host, exiting...")
            return
        
        self.peer_id = self.quic_host.get_id()
        print(f"🆔 Local QUIC peer ID: {self.peer_id}")
        
        # Parse remote peers from environment variable
        remote_peers = []
        if "REMOTE_PEERS" in os.environ:
            remote_peers = [
                addr.strip() 
                for addr in os.environ["REMOTE_PEERS"].split(",")
                if addr.strip() and "/quic" in addr
            ]
        
        try:
            async with trio.open_nursery() as nursery:
                # Start QUIC host
                quic_addr = Multiaddr("/ip4/0.0.0.0/udp/0/quic-v1")
                nursery.start_soon(self.run_host, self.quic_host, quic_addr)
                
                # Give host time to start
                await trio.sleep(1)
                
                # Connect to remote peers if specified
                if remote_peers:
                    print(f"🔗 Connecting to {len(remote_peers)} remote peer(s)...")
                    for addr_str in remote_peers:
                        nursery.start_soon(self.dial_peer, addr_str)
                
                else:
                    self.print_connection_command()
                
        except Exception as e:
            print(f"❌ Application error: {e}")
            raise
```

This block defines the `run` method, the main asynchronous entry point for the `QUICPingApp`. It starts by printing a message indicating the application is starting. If QUIC is not available, it prints an error and exits. It then attempts to create a QUIC host by calling `create_quic_host`. If the host creation fails, it prints an error and exits. The peer ID of the host is retrieved and printed. The method checks the `REMOTE_PEERS` environment variable for a comma-separated list of peer addresses, filtering for valid QUIC addresses. Using a trio nursery (a context for managing concurrent tasks), it starts the QUIC host with a listen address of `/ip4/0.0.0.0/udp/0/quic-v1`, which binds to all interfaces on a random UDP port using QUIC. After a 1-second delay to ensure the host starts, it checks if remote peers are specified. If so, it starts tasks to dial each peer; otherwise, it calls ``print_connection_command` to display connection instructions. Any exceptions are caught, printed, and re-raised.

### Step 11: Main Entry Point

```python
async def main():
    """Application entry point."""
    app = QUICPingApp()
    
    try:
        await app.run()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        app.running = False
    except Exception as e:
        print(f"💥 Application error: {e}")
        print("\n🔍 Analysis:")
        print("Your py-libp2p version uses a single-transport architecture.")
        print("The QUIC transport exists but may not be fully stable.")
        print("\n🔧 Solutions:")
        print("1. Build py-libp2p with QUIC support enabled")
        print("2. Use a newer version of py-libp2p with better QUIC support")
        print("3. Check QUIC configuration and network permissions")
    finally:
        print("🏁 Application stopped")

if __name__ == "__main__":
    trio.run(main)
```

This block defines the `main` asynchronous function, which serves as the application's entry point. It creates an instance of `QUICPingApp` and calls its `run` method. The method is wrapped in a try-except block to handle interruptions and errors. If a `KeyboardInterrupt` (Ctrl+C) occurs, it prints a shutdown message and sets `app.running` to `False` to stop any loops. For other exceptions, it prints an error message, provides an analysis suggesting that the `py-libp2p` library may have a single-transport architecture and unstable QUIC support, and offers solutions like enabling QUIC support, updating the library, or checking network permissions. The `finally` block prints a message indicating the application has stopped. The `if __name__ == "__main__":` clause ensures the `main` function is run using `trio.run` when the script is executed directly.


## Testing Your Implementation

1. Set the environment variables:
   ```bash
   export PROJECT_ROOT=/path/to/workshop
   export LESSON_PATH=en/py/04-quic-transport
   ```

2. Change into the lesson directory:
    ```bash
    cd $PROJECT_ROOT/$LESSON_PATH
    ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run with Docker Compose:
   ```bash
   docker rm -f workshop-lesson ucw-checker-04-quic-transport
   docker network rm -f workshop-net
   docker network create --driver bridge --subnet 172.16.16.0/24 workshop-net
   docker compose --project-name workshop up --build --remove-orphans
   ```

5. Run the Python script to check your output:
   ```bash
   python check.py
   ```

## Success Criteria

Your implementation should:
- ✅ Display the startup message and local peer ID
- ✅ Successfully dial the remote peer using QUIC
- ✅ Establish a QUIC connection
- ✅ Send and receive ping messages over QUIC
- ✅ Display round-trip times in milliseconds
- ✅ Identify transport type (TCP vs QUIC) in connection messages

## Hints

### Hint - QUIC Multiaddress Format

QUIC multiaddresses use UDP instead of TCP and include the QUIC protocol after the port number.
- TCP: `/ip4/127.0.0.1/tcp/9092`
- QUIC: `/ip4/127.0.0.1/udp/9092/quic-v1`

### Hint - Error Handling

py-libp2p uses async/await patterns, so make sure to properly handle exceptions in async contexts:

```python
try:
    await host.connect(addr)
except Exception as e:
    print(f"Connection failed: {e}")
```

### Hint - Here is the complete code 

py-libp2p hosts should be used with async context managers to ensure proper resource cleanup:

```python
import os
import time

import trio
from multiaddr import Multiaddr

from libp2p import new_host, generate_new_rsa_identity
from libp2p.custom_types import TProtocol
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr

# Try to import QUIC transport - if this fails, QUIC isn't supported in this version
try:
    from libp2p.transport.quic.transport import QUICTransport
    QUIC_AVAILABLE = True
except ImportError as e:
    print(f"QUIC transport not available: {e}")
    QUIC_AVAILABLE = False
    QUICTransport = None

PING_PROTOCOL_ID = TProtocol("/ipfs/ping/1.0.0")
PING_LENGTH = 32

class QUICPingApp:
    """
    A libp2p application that uses QUIC transport for ping functionality.
    """
    
    def __init__(self):
        self.quic_host = None
        self.peer_id = None
        self.running = True
        
    async def create_quic_host(self):
        """Create a QUIC host."""
        if not QUIC_AVAILABLE:
            print("❌ QUIC transport not available, cannot proceed")
            return None
            
        try:
            # Generate keypair for QUIC host
            key_pair = generate_new_rsa_identity()
            
            # Create QUIC transport
            quic_transport = QUICTransport(key_pair.private_key)
            
            host = new_host(key_pair=key_pair)
            
            swarm = host.get_network()
            swarm.transport = quic_transport
            
            # Set up QUIC transport with the swarm if method exists
            if hasattr(quic_transport, 'set_swarm'):
                quic_transport.set_swarm(swarm)
            
            print("✅ QUIC host created successfully")
            return host
            
        except Exception as e:
            print(f"❌ Failed to create QUIC host: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def handle_ping(self, stream: INetStream) -> None:
        """Handle incoming ping requests over QUIC."""
        try:
            while True:
                start_time = time.time()
                data = await stream.read(PING_LENGTH)
                
                if not data:
                    break
                
                await stream.write(data)
                rtt_ms = (time.time() - start_time) * 1000
                peer_id = stream.muxed_conn.peer_id
                print(f"📨 Received QUIC ping from {peer_id}, RTT: {int(rtt_ms)} ms")
                
        except Exception as e:
            print(f"❌ Ping handler error: {e}")
        finally:
            try:
                await stream.close()
            except:
                pass
    
    async def send_ping(self, stream: INetStream):
        """Send ping to remote peer and measure RTT over QUIC."""
        try:
            payload = b"\x01" * PING_LENGTH
            peer_id = stream.muxed_conn.peer_id
            
            while self.running:
                start_time = time.time()
                await stream.write(payload)
                
                with trio.fail_after(5):
                    response = await stream.read(PING_LENGTH)
                
                if response == payload:
                    rtt_ms = (time.time() - start_time) * 1000
                    print(f"🏓 QUIC ping to {peer_id}, RTT: {int(rtt_ms)} ms")
                else:
                    print(f"❌ QUIC ping response mismatch from {peer_id}")
                
                # Wait 1 second between pings
                await trio.sleep(1)
                
        except trio.TooSlowError:
            print(f"⏱️ QUIC ping timeout to {peer_id}")
        except Exception as e:
            print(f"❌ QUIC ping failed to {peer_id}: {e}")
        finally:
            try:
                await stream.close()
            except:
                pass
    
    async def dial_peer(self, addr_str: str):
        """Dial a peer using QUIC."""
        try:
            addr = Multiaddr(addr_str)
            print(f"🔄 Dialing peer at: {addr} via QUIC")
            
            # Parse peer info from multiaddr
            info = info_from_p2p_addr(addr)
            await self.quic_host.connect(info)
            
            print(f"✅ Connected to: {info.peer_id} via QUIC")
            
            # Open ping stream
            stream = await self.quic_host.new_stream(info.peer_id, [PING_PROTOCOL_ID])
            
            # Start ping loop
            await self.send_ping(stream)
            
        except Exception as e:
            print(f"❌ Failed to connect via QUIC to {addr_str}: {e}")
    
    async def run_host(self, host, listen_addr: Multiaddr):
        """Run the QUIC host with error handling."""
        try:
            # Set ping handler
            host.set_stream_handler(PING_PROTOCOL_ID, self.handle_ping)
            
            async with host.run(listen_addrs=[listen_addr]):
                # Print listening addresses
                addrs = host.get_addrs()
                if addrs:
                    print(f"🎧 QUIC listening on:")
                    for addr in addrs:
                        print(f"  {addr}")
                
                await trio.sleep_forever()
                
        except Exception as e:
            print(f"❌ QUIC host failed: {e}")
            raise
    
    def print_connection_command(self):
        """Print ready-to-use command for connecting from another terminal."""
        if not self.quic_host:
            print("❌ No QUIC host available to generate connection command")
            return
        
        print("ℹ️ No remote peers specified. To connect from another terminal, copy-paste this:")
        quic_addrs = [str(addr) for addr in self.quic_host.get_addrs() if "/quic" in str(addr)]
        for addr in quic_addrs:
            dial_addr = addr.replace("/ip4/0.0.0.0/", "/ip4/127.0.0.1/")
            print(f"$env:REMOTE_PEERS='{dial_addr}'; python app/main.py")
        
        print("⏳ Waiting for incoming connections...")
    
    async def run(self):
        """Main application loop for QUIC ping."""
        print("🚀 Starting QUIC Ping Application...")
        
        # Create QUIC host
        if not QUIC_AVAILABLE:
            print("❌ QUIC transport not available, exiting...")
            return
        
        print("🔧 Attempting to create QUIC host...")
        self.quic_host = await self.create_quic_host()
        if not self.quic_host:
            print("❌ Failed to create QUIC host, exiting...")
            return
        
        self.peer_id = self.quic_host.get_id()
        print(f"🆔 Local QUIC peer ID: {self.peer_id}")
        
        # Parse remote peers from environment variable
        remote_peers = []
        if "REMOTE_PEERS" in os.environ:
            remote_peers = [
                addr.strip() 
                for addr in os.environ["REMOTE_PEERS"].split(",")
                if addr.strip() and "/quic" in addr
            ]
        
        try:
            async with trio.open_nursery() as nursery:
                # Start QUIC host
                quic_addr = Multiaddr("/ip4/0.0.0.0/udp/0/quic-v1")
                nursery.start_soon(self.run_host, self.quic_host, quic_addr)
                
                # Give host time to start
                await trio.sleep(1)
                
                # Connect to remote peers if specified
                if remote_peers:
                    print(f"🔗 Connecting to {len(remote_peers)} remote peer(s)...")
                    for addr_str in remote_peers:
                        nursery.start_soon(self.dial_peer, addr_str)
                
                else:
                    self.print_connection_command()
                
        except Exception as e:
            print(f"❌ Application error: {e}")
            raise

async def main():
    """Application entry point."""
    app = QUICPingApp()
    
    try:
        await app.run()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        app.running = False
    except Exception as e:
        print(f"💥 Application error: {e}")
        print("\n🔍 Analysis:")
        print("Your py-libp2p version uses a single-transport architecture.")
        print("The QUIC transport exists but may not be fully stable.")
        print("\n🔧 Solutions:")
        print("1. Build py-libp2p with QUIC support enabled")
        print("2. Use a newer version of py-libp2p with better QUIC support")
        print("3. Check QUIC configuration and network permissions")
    finally:
        print("🏁 Application stopped")

if __name__ == "__main__":
    trio.run(main)
```

## Key Differences from Rust Implementation

The Python implementation differs from Rust in several ways:

1. **Host vs Swarm**: py-libp2p uses a `Host` abstraction instead of directly managing a `Swarm`
2. **Async/Await**: Uses Python's async/await syntax instead of futures and streams
3. **Context Managers**: Uses async context managers for resource management
4. **Transport Registration**: Transports are passed to the host constructor
5. **Connection Events**: Connection events are handled through the host's network interface

## What's Next?

Great work! You've successfully implemented multi-transport support with QUIC in Python. You now understand:

- **QUIC Advantages**: Built-in security, reduced latency, better multiplexing
- **Multi-Transport Configuration**: Running multiple transports simultaneously
- **Transport Flexibility**: py-libp2p's ability to adapt to different network conditions
- **Modern Protocols**: How py-libp2p embraces cutting-edge networking technology

Key concepts you've learned:
- **QUIC Protocol**: Modern UDP-based transport with integrated security
- **Multi-Transport**: Supporting multiple protocols simultaneously
- **Transport Abstraction**: How py-libp2p handles different transports uniformly
- **Connection Flexibility**: Choosing the best transport for each connection

In the next lesson, you'll reach your second checkpoint by implementing the Identify protocol, which allows peers to exchange information about their capabilities and supported protocols!