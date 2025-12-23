import { createEd25519PeerId } from '@libp2p/peer-id-factory';
import fs from 'fs';

const peerId = await createEd25519PeerId();

const peerIdJson = {
  id: peerId.toString(),
  privKey: peerId.privateKey && Buffer.from(peerId.privateKey).toString('base64'),
  pubKey: peerId.publicKey && Buffer.from(peerId.publicKey).toString('base64')
};

fs.writeFileSync('peer-id.json', JSON.stringify(peerIdJson, null, 2));

console.log('✅ Full peer-id.json saved with id, privKey, and pubKey');