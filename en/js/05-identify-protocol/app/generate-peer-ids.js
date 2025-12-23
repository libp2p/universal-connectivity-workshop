/**
 * Generate peer IDs for Node1 and Node2
 * Run this script to create peer-id-node1.json and peer-id-node2.json
 */

import { createEd25519PeerId } from '@libp2p/peer-id-factory';
import fs from 'fs';

async function generatePeerIdFile(peerId, filename) {
  // Convert peer ID to JSON format compatible with createFromJSON
  const peerIdJson = {
    id: peerId.toString(),
    privKey: peerId.privateKey && Buffer.from(peerId.privateKey).toString('base64'),
    pubKey: peerId.publicKey && Buffer.from(peerId.publicKey).toString('base64')
  };
  
  fs.writeFileSync(filename, JSON.stringify(peerIdJson, null, 2));
  console.log(`✓ Generated ${filename} (${peerId.toString()})`);
}

async function main() {
  console.log('Generating peer IDs...');
  
  const peerId1 = await createEd25519PeerId();
  const peerId2 = await createEd25519PeerId();
  
  await generatePeerIdFile(peerId1, './peer-id-node1.json');
  await generatePeerIdFile(peerId2, './peer-id-node2.json');
  
  console.log('✓ All peer IDs generated successfully');
}

main().catch((err) => {
  console.error('Error generating peer IDs:', err);
  process.exit(1);
});

