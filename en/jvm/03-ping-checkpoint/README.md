# Lesson 03: Ping Protocol Checkpoint 🏆

This is a checkpoint lesson where you'll implement the ping protocol to verify connectivity and measure round-trip times to remote peers.

## Quick Start

### Prerequisites

- Java JDK 21 or later
- Gradle 8.5 or later (or use the Gradle wrapper)
- Internet connection (to connect to checkpoint server)

### Build and Run

```bash
# Navigate to the app directory
cd app

# Build the application
./gradlew build

# Run the application
./gradlew run
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on:
  /ip4/127.0.0.1/tcp/54321/p2p/12D3KooW...
Ping protocol initialized
No REMOTE_PEERS specified, using checkpoint server
Dialing peer QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Connected to: QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN

Pinging connected peers...
Pinging QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN...
Ping to QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN successful: RTT = 45ms

Application running. Press Ctrl+C to exit.
```

### Run with Custom Peers

```bash
# Set REMOTE_PEERS environment variable
export REMOTE_PEERS="/ip4/192.168.1.100/tcp/4001/p2p/12D3KooW..."

# Run the application
./gradlew run
```

### Check Your Solution

```bash
# Navigate back to lesson directory
cd ..

# Run the check script
python check.py
```

## What You'll Learn

- Adding libp2p protocols to your host
- Using the Ping protocol to measure latency
- Working with CompletableFuture chains
- Handling async operations with timeouts
- Connecting to public libp2p nodes

## Success Criteria

✅ Ping protocol is added to the host
✅ Connection to checkpoint server succeeds
✅ Ping completes successfully
✅ RTT is measured and displayed in milliseconds
✅ Errors are handled gracefully

## Troubleshooting

**Connection Timeout**
- Check internet connectivity
- Verify firewall allows outbound TCP connections
- Try increasing connection timeout

**Ping Failure**
- Ensure peer is still connected
- Check protocol negotiation logs
- Verify ping protocol was initialized

**Build Errors**
- Clear Gradle cache: `./gradlew clean`
- Refresh dependencies: `./gradlew build --refresh-dependencies`

For detailed instructions, see [lesson.md](lesson.md).
