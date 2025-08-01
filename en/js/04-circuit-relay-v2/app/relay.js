import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { circuitRelayServer } from '@libp2p/circuit-relay-v2'
import { identify } from '@libp2p/identify'
import { webSockets } from '@libp2p/websockets'
import { tcp } from '@libp2p/tcp'
import { createLibp2p } from 'libp2p'
import { createFromJSON } from '@libp2p/peer-id-factory'
import fs from 'fs'


async function createNode() {
  const peerIdJson = await JSON.parse(fs.readFileSync('./peer-id.json'))
  const peerId = await createFromJSON(peerIdJson)

  const node = await createLibp2p({
    peerId,
    addresses: {
      listen: [
        '/ip4/0.0.0.0/tcp/0',
        '/ip4/0.0.0.0/tcp/0/ws'
      ]
    },
    transports: [tcp(), webSockets()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      identify: identify(),
      relay: circuitRelayServer({reservations: 15})
    }
  })
  return node
}

async function main(){
  
const node = await createNode();

await node.start()
node.addEventListener('error', (evt) => {
  console.error('Node error:', evt.detail);
});

console.log(`Node started with id ${node.peerId.toString()}`)
console.log('Listening on:')
node.getMultiaddrs().forEach((ma) => console.log(ma.toString()))

}

main().catch(console.error) 
