/**
 * Circuit Relay v2 - Relay Node
 * 
 * The relay node acts as an intermediary, forwarding traffic between peers
 * that cannot connect directly (e.g., when behind NATs or firewalls).
 * 
 * Key concepts:
 * - Circuit relay allows NAT traversal
 * - The relay listens on public addresses
 * - Peers reserve "slots" on the relay to receive connections
 * - The relay forwards traffic between peers
 */

import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { circuitRelayServer } from '@libp2p/circuit-relay-v2';
import { ping } from '@libp2p/ping';
import { identify } from '@libp2p/identify';
import { createFromJSON } from '@libp2p/peer-id-factory';
import fs from 'fs';

async function main() {
  console.log('Starting Circuit Relay v2 - Relay Node');
  console.log('=======================================');
  
  // Load persistent peer ID (ensures same identity across restarts)
  const peerIdJson = JSON.parse(fs.readFileSync('./peer-id.json', 'utf-8'));
  const peerId = await createFromJSON(peerIdJson);

  // Create the relay node
  const node = await createLibp2p({
    peerId,
    addresses: {
      listen: [
        '/ip4/0.0.0.0/tcp/0',  // Listen on any available TCP port
      ]
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      ping: ping({
        protocolPrefix: "ipfs",
        pingInterval: 1000,
        timeout: 5000,
      }),
      identify: identify(),
      relay: circuitRelayServer({
        reservations: {
          maxReservations: 15  // Allow up to 15 peers to reserve relay slots
        }
      })
    }
  });

  await node.start();

  // Print node information (check.py expects this format)
  console.log(`Node started with id ${node.peerId.toString()}`);
  console.log('Listening on:');
  node.getMultiaddrs().forEach((addr) => {
    console.log(`  ${addr.toString()}`);
  });


  process.on('SIGINT', async () => {
    console.log('\nShutting down relay node...');
    await node.stop();
    process.exit(0);
  });


  await new Promise(() => {});
}

main().catch((err) => {
  console.error('Relay node error:', err);
  process.exit(1);
});
