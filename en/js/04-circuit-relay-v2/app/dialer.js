/**
 * Circuit Relay v2 - Dialer Node
 * 
 * The dialer node connects to the listener node through the relay.
 * It uses the circuit relay address advertised by the listener to establish
 * a connection, even though the listener is behind a NAT/firewall.
 * 
 * Key concepts:
 * - Dialer connects to listener via relay address: /ip4/.../tcp/.../p2p/<relay-id>/p2p-circuit/p2p/<listener-id>
 * - Traffic flows: Dialer -> Relay -> Listener
 * - The relay forwards all traffic between dialer and listener
 * - This enables NAT traversal without port forwarding
 */

import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { circuitRelayTransport } from '@libp2p/circuit-relay-v2';
import { ping } from '@libp2p/ping';
import { identify } from '@libp2p/identify';
import { multiaddr } from '@multiformats/multiaddr';

async function main() {
  console.log('Starting Circuit Relay v2 - Dialer Node');
  console.log('========================================');
  
  // Get listener relay address from environment or command line argument
  const listenerRelayAddrStr = process.env.LISTENER_RELAY_ADDR || process.argv[2];
  if (!listenerRelayAddrStr) {
    throw new Error('Listener relay address must be provided via LISTENER_RELAY_ADDR env var or command line argument');
  }

  // Validate and parse the multiaddr
  let listenerRelayAddr;
  try {
    listenerRelayAddr = multiaddr(listenerRelayAddrStr);
  } catch (err) {
    throw new Error(`Invalid multiaddr format: ${listenerRelayAddrStr}. Error: ${err.message}`);
  }

  // Validate the multiaddr contains required components
  const addrStr = listenerRelayAddrStr;
  if (!addrStr.includes('/p2p-circuit')) {
    throw new Error(`Invalid relay address: must contain /p2p-circuit. Got: ${addrStr}`);
  }
  if (!addrStr.includes('/p2p/')) {
    throw new Error(`Invalid relay address: must contain /p2p/<peer-id>. Got: ${addrStr}`);
  }

  // Create dialer node
  const node = await createLibp2p({
    addresses: {
      listen: []  // No need to listen - we're dialing
    },
    transports: [
      tcp(),
      circuitRelayTransport()  // Enable circuit relay transport to connect through relay
    ],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      ping: ping({
        protocolPrefix: "ipfs",
        pingInterval: 1000,
        timeout: 5000,
      }),
      identify: identify()
    }
  });

  await node.start();

  // Print node information (check.py expects this format)
  console.log(`Node started with id ${node.peerId.toString()}`);

  // Dial the listener through the relay
  console.log(`Dialing listener via relay at ${listenerRelayAddrStr}...`);
  
  try {
    const conn = await node.dial(listenerRelayAddr, {
      signal: AbortSignal.timeout(30_000)  // 30 second timeout
    });
    
    const remoteAddr = conn.remoteAddr.toString();
    console.log(`Connected to the listener node via ${remoteAddr}`);
  } catch (err) {
    if (err.message?.includes('timeout') || err.name === 'AbortError') {
      throw new Error(`Failed to connect to listener via relay: Connection timeout. Relay address: ${listenerRelayAddrStr}`);
    }
    throw new Error(`Failed to connect to listener via relay: ${err.message}. Relay address: ${listenerRelayAddrStr}`);
  }

  await new Promise(resolve => setTimeout(resolve, 2000));

  await node.stop();
  process.exit(0);
}

main().catch((err) => {
  console.error('Dialer node error:', err);
  process.exit(1);
});