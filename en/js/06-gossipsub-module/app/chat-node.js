import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { gossipsub } from '@chainsafe/libp2p-gossipsub'
import { identify } from '@libp2p/identify'
import { createEd25519PeerId } from '@libp2p/peer-id-factory'
import { multiaddr } from '@multiformats/multiaddr'
import { fromString as uint8ArrayFromString } from 'uint8arrays/from-string'
import { toString as uint8ArrayToString } from 'uint8arrays/to-string'
import readline from 'readline'

const TOPIC = 'gossipsub-chat'

async function createNode() {
  const peerId = await createEd25519PeerId()
  
  const node = await createLibp2p({
    peerId,
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      pubsub: gossipsub({
        emitSelf: false,
        allowPublishToZeroPeers: true,
        messageProcessingConcurrency: 10
      }),
      identify: identify()
    }
  })
  return node
}

async function main() {
  const node = await createNode()
  await node.start()
  
  console.log('Chat node started with Peer ID:', node.peerId.toString())
  node.getMultiaddrs().forEach(addr => {
    console.log('Listening on:', addr.toString())
  })

  // Check for remote peer address from command line
  const remoteAddr = process.argv[2]
  if (remoteAddr) {
    console.log(`\n💡 Connecting to remote peer: ${remoteAddr}`)
  } else {
    console.log('\n💡 To connect to another chat node, run:')
    console.log(`   node chat-node.js <multiaddr>`)
    node.getMultiaddrs().forEach(addr => {
      console.log(`   Example: node chat-node.js ${addr.toString()}`)
    })
  }

  // Listen for incoming messages
  node.services.pubsub.addEventListener('message', (evt) => {
    const message = uint8ArrayToString(evt.detail.data)
    const fromPeer = evt.detail.from.toString()
    console.log(`MESSAGE RECEIVED from ${fromPeer}: "${message}" on topic ${evt.detail.topic}`)
  })

  // Subscribe to the chat topic
  await node.services.pubsub.subscribe(TOPIC)
  console.log(`Subscribed to topic: ${TOPIC}`)

  // Connect to remote peer if provided
  if (remoteAddr) {
    try {
      await node.dial(multiaddr(remoteAddr))
      console.log(`Connected to remote peer: ${remoteAddr}`)
    } catch (err) {
      console.error('Failed to connect to remote peer:', err.message)
    }
  }

  // Set up interactive chat
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  })

  console.log('\n=== Gossipsub Chat ===')
  console.log('Type your message and press Enter to send:')
  console.log('(Type "quit" to exit)')
  console.log('(Type "peers" to see connected peers)')
  console.log('(Type "help" for instructions)\n')

  rl.on('line', async (input) => {
    if (input.toLowerCase() === 'quit') {
      console.log('Goodbye!')
      await node.stop()
      process.exit(0)
    }

    if (input.toLowerCase() === 'peers') {
      const connections = node.getConnections()
      if (connections.length === 0) {
        console.log('No peers connected. Start another chat node and connect to this one!')
      } else {
        console.log('Connected peers:')
        connections.forEach(conn => {
          console.log(`  - ${conn.remotePeer.toString()}`)
        })
      }
      
      // Show topic subscribers
      const topicPeers = node.services.pubsub.getSubscribers(TOPIC)
      console.log(`Peers subscribed to topic "${TOPIC}": ${topicPeers.length}`)
      topicPeers.forEach(peer => {
        console.log(`  - ${peer.toString()}`)
      })
      return
    }

    if (input.toLowerCase() === 'help') {
      console.log('\n=== Help ===')
      console.log('• Type any message to send it to all connected peers')
      console.log('• Type "peers" to see connected peers and topic subscribers')
      console.log('• Type "quit" to exit')
      console.log('• To connect to another node, run: node chat-node.js <multiaddr>')
      console.log('• Make sure at least 2 nodes are connected to exchange messages\n')
      return
    }

    if (input.trim()) {
      try {
        await node.services.pubsub.publish(TOPIC, uint8ArrayFromString(input))
        console.log(`Message sent: "${input}"`)
      } catch (err) {
        if (err.message.includes('NoPeersSubscribedToTopic')) {
          console.log('⚠️  No other peers subscribed to this topic.')
          console.log('   Start another chat node and connect to this one to exchange messages!')
        } else {
          console.error('Failed to send message:', err)
        }
      }
    }
  })

  // Keep the process alive
  process.stdin.resume()
}

main().catch(console.error) 