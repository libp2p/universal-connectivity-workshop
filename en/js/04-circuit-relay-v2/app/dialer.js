import { createLibp2p } from 'libp2p'
import { webSockets } from '@libp2p/websockets'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { multiaddr } from '@multiformats/multiaddr'

const listenNodeAddr = process.argv[2]
if (!listenNodeAddr) {
  throw new Error('The listening node address needs to be specified')
}

const node = await createLibp2p({
  transports: [webSockets()],
  connectionEncrypters: [noise()],
  streamMuxers: [yamux()]
})

console.log(`Node started with id ${node.peerId.toString()}`)

const ma = multiaddr(listenNodeAddr)
const conn = await node.dial(ma, {
  signal: AbortSignal.timeout(10_000)
})
console.log(`Connected to the listen node via ${conn.remoteAddr.toString()}`)