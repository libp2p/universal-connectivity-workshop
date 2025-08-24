// // generate-peer-id.js
// import { createEd25519PeerId } from '@libp2p/peer-id-factory'
// import fs from 'fs'

// const peerId = await createEd25519PeerId()
// fs.writeFileSync('./peer-id.json', JSON.stringify(peerId.toJSON(), null, 2))
// console.log('Peer ID saved to peer-id.json')
// // 

import { createEd25519PeerId } from '@libp2p/peer-id-factory';
import fs from 'fs';

const peerId = await createEd25519PeerId();

// Manually encode keys to Base64 to ensure inclusion
const peerIdJson = {
  id: peerId.toString(),
  privKey: peerId.privateKey && Buffer.from(peerId.privateKey).toString('base64'),
  pubKey: peerId.publicKey && Buffer.from(peerId.publicKey).toString('base64')
};

fs.writeFileSync('peer-id.json', JSON.stringify(peerIdJson, null, 2));

console.log('✅ Full peer-id.json saved with id, privKey, and pubKey');