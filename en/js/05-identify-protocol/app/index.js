import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { webSockets } from '@libp2p/websockets'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { identify } from '@libp2p/identify'
import { multiaddr } from '@multiformats/multiaddr'
import { createFromJSON } from '@libp2p/peer-id-factory'
import { privateKeyFromRaw } from '@libp2p/crypto/keys'
import fs from 'fs'

async function createNode(peerId) {
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
      identify: identify()
    }
  })
  return node
}

async function main() {
  // Load PeerId from file
  const peerIdJson = JSON.parse(fs.readFileSync('./peer-id.json'))
  const peerId = await createFromJSON(peerIdJson)

  // Extract and concatenate privateKey and publicKey for Ed25519
  if (peerId.privateKey && peerId.publicKey) {
    const privKeyRaw = Buffer.from(peerId.privateKey, 'base64')
    const pubKeyRaw = Buffer.from(peerId.publicKey, 'base64')
    const ed25519Raw = Buffer.concat([privKeyRaw, pubKeyRaw])
    const privKeyObj = privateKeyFromRaw(ed25519Raw)
    console.log('Reconstructed PrivateKey from raw (priv+pub):', privKeyObj)
  } else {
    console.log('No private or public key found in PeerId!')
  }
  console.log('Has private key:', !!peerId.privateKey)

  const node = await createNode(peerId)
  await node.start()
  console.log('Node started with Peer ID:', node.peerId.toString())
  node.getMultiaddrs().forEach(addr => {
    console.log('Listening on:', addr.toString())
  })

  // If a remote multiaddr is provided, dial and query identify
  const remoteAddr = process.argv[2]
  if (remoteAddr) {
    try {
      const conn = await node.dial(multiaddr(remoteAddr))
      const remotePeer = conn.remotePeer
      // Query identify info
      const protocols = await node.services.identify.getProtocols(remotePeer)
      console.log(`Remote PeerId: ${remotePeer.toString()}`)
      console.log('Protocols:', protocols)
    } catch (err) {
      console.error('Failed to connect or identify remote peer:', err)
    }
  }
  process.stdin.resume()
}

main().catch(console.error) 