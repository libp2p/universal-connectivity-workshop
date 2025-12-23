/**
 * Circuit Relay v2 - Listener Node
 * 
 * The listener node is behind a NAT/firewall and cannot receive direct connections.
 * It reserves a "slot" on the relay node by listening on a circuit relay address,
 * allowing other peers to connect to it through the relay.
 * 
 * Key concepts:
 * - Listener connects to relay first
 * - Listener listens on /p2p-circuit or a specific relay address to reserve a slot
 * - Listener advertises a relay address: /ip4/.../tcp/.../p2p/<relay-id>/p2p-circuit/p2p/<listener-id>
 * - Other peers can connect to listener via this relay address
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
  console.log('Starting Circuit Relay v2 - Listener Node');
  console.log('==========================================');
  
  // Get relay address from environment or command line argument
  const relayAddrStr = process.env.RELAY_ADDR || process.argv[2];
  if (!relayAddrStr) {
    throw new Error('Relay address must be provided via RELAY_ADDR env var or command line argument');
  }

  const relayAddr = multiaddr(relayAddrStr);

  // Create listener node (behind NAT - no direct listen addresses)
  const node = await createLibp2p({
    addresses: {
      listen: []  // No direct listening - behind NAT
    },
    transports: [
      tcp(),
      circuitRelayTransport()  // Enable circuit relay transport
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

  // Connect to relay first to establish connection
  console.log(`Connecting to relay at ${relayAddr.toString()}...`);
  const relayConn = await node.dial(relayAddr);
  const relayPeerId = relayConn.remotePeer.toString();
  console.log(`Connected to the relay ${relayPeerId}`);

  // Construct circuit listen address by appending /p2p-circuit to the relay address
  // Format: /ip4/<relay-ip>/tcp/<relay-port>/p2p/<relay-peer-id>/p2p-circuit
  // This tells the listener to reserve a slot on this specific relay
  const circuitListenAddrStr = `${relayAddr.toString()}/p2p-circuit`;
  const circuitListenAddr = multiaddr(circuitListenAddrStr);
  
  // In js-libp2p v3, we use the transport manager's listen method
  // The circuit relay transport will automatically create a reservation when we listen
  console.log(`Listening on circuit relay address: ${circuitListenAddrStr}...`);
  await node.components.transportManager.listen([circuitListenAddr]);

  // Wait for the reservation to be confirmed and address to be advertised
  // The node will automatically add relay addresses to getMultiaddrs() once reservation is confirmed
  let relayMultiaddr = null;
  let attempts = 0;
  const maxAttempts = 30;
  
  while (attempts < maxAttempts) {
    const addrs = node.getMultiaddrs();
    // Find the relay address (contains /p2p-circuit)
    relayMultiaddr = addrs.find(addr => {
      const addrStr = addr.toString();
      return addrStr.includes('/p2p-circuit') && 
             addrStr.includes(relayPeerId) &&
             addrStr.includes(node.peerId.toString());
    });
    
    if (relayMultiaddr) {
      const relayAddrStr = relayMultiaddr.toString();
      console.log(`Advertising with a relay address of ${relayAddrStr}`);
      break;
    }
    
    // Wait a bit and try again
    await new Promise(resolve => setTimeout(resolve, 500));
    attempts++;
  }
  
  if (!relayMultiaddr) {
    // Fallback: construct the relay address manually
    const relayAddrStr = `${relayAddr.toString()}/p2p-circuit/p2p/${node.peerId.toString()}`;
    console.log(`Advertising with a relay address of ${relayAddrStr}`);
  }

  // Keep the listener running
  process.on('SIGINT', async () => {
    console.log('\nShutting down listener node...');
    await node.stop();
    process.exit(0);
  });

  // Keep process alive
  await new Promise(() => {});
}

main().catch((err) => {
  console.error('Listener node error:', err);
  process.exit(1);
});