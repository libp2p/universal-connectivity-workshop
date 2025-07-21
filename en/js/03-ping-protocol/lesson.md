Lesson 3: Ping Checkpoint 🏆
Welcome to your first checkpoint! In this lesson, you'll implement the ping protocol, one of the fundamental protocols in libp2p that allows peers to measure connectivity and round-trip times.
Learning Objectives
By the end of this lesson, you will:

Understand the purpose and mechanics of the ping protocol
Configure ping behavior with custom intervals and timeouts
Handle ping events and display connection quality metrics
Successfully establish bidirectional connectivity with a remote peer

Background: The Ping Protocol
The ping protocol in libp2p serves several important purposes:

Connectivity Testing: Verifies that connections are working bidirectionally
Latency Measurement: Measures round-trip time between peers
Keep-Alive: Helps maintain connections by sending periodic traffic
Network Quality: Provides insights into connection stability

Unlike ICMP ping, libp2p's ping protocol works over any transport and respects the encryption and multiplexing layers.
Your Task
Building on your TCP transport implementation from Lesson 2, you need to:

Configure Ping Settings: Set up ping with a 1-second interval and 5-second timeout
Handle Ping Events: Process ping events and display round-trip times

Step-by-Step Instructions
Step 1: Update Your Ping Service Configuration
Your existing code already includes the ping service from Lesson 1, but now you need to configure it properly with custom timing settings.
The default settings for interval and timeout are 15 seconds and 20 seconds respectively. We are making those values shorter so that when we test this solution we'll send and receive pings immediately after establishing a connection to the remote peer. This is just for convenience. In normal networking situations, the defaults are more appropriate. When programming for mobile or other battery powered devices, you should make the interval and timeout much longer, such as 30 and 45 seconds so that the radio in the device can spend less time in the high power active state.
Step 2: Configure Ping in the Node Creation
Modify your libp2p node configuration to include the ping service with a 1-second interval and 5-second timeout:


```
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { ping } from '@libp2p/ping';

const main = async () => {
  console.log('Starting Universal Connectivity Application...');
  
  // Create the libp2p node with configured ping service
  const node = await createLibp2p({
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      ping: ping({
        protocolPrefix: 'ipfs',
        pingInterval: 1000,    // 1 second interval
        timeout: 5000          // 5 second timeout
      })
    },
    connectionManager: {
      idleConnectionTimeout: 60000  // 60 seconds idle timeout
    }
  });

  // Start the node
  await node.start();

  // Print identity and network information
  console.log('Local peer id:', node.peerId.toString());
  console.log('Listening on:');
  node.getMultiaddrs().forEach((addr) => {
    console.log(' ', addr.toString());
  });
  ```

  Step 3: Handle Ping Events
In your event handling section, add listeners for ping events alongside your existing connection events:

```
// Handle connection events
  node.addEventListener('peer:connect', (evt) => {
    console.log('Connected to:', evt.detail.toString());
  });

  node.addEventListener('peer:disconnect', (evt) => {
    console.log('Disconnected from:', evt.detail.toString());
  });

  // Handle ping events
  node.services.ping.addEventListener('ping', (evt) => {
    const { peer, rtt } = evt.detail;
    console.log(`Received a ping from ${peer.toString()}, round trip time: ${rtt} ms`);
  });

  node.services.ping.addEventListener('error', (evt) => {
    const { peer, error } = evt.detail;
    console.log(`Ping failed to ${peer.toString()}: ${error.message}`);
  });

  console.log('Node is running. Press Ctrl+C to stop.');

  // Graceful shutdown
  const cleanup = async () => {
    console.log('\nShutting down...');
    await node.stop();
    process.exit(0);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);

  // Keep the process alive
  process.stdin.resume();
};

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});
```
