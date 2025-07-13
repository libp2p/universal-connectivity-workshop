import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { webSockets } from '@libp2p/websockets'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { gossipsub } from '@chainsafe/libp2p-gossipsub'
import { identify } from '@libp2p/identify'
import { fromString as uint8ArrayFromString } from 'uint8arrays/from-string'
import { toString as uint8ArrayToString } from 'uint8arrays/to-string'
import readline from 'readline'

const TOPIC = 'gossipsub-chat'

async function createNode() {
  const node = await createLibp2p({
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
      pubsub: gossipsub(),
      identify: identify()
    }
  })
  return node
}

async function main() {
  const [node1, node2]= await Promise.all([
    createNode(),
    createNode()
  ])
  
  console.log('Chat node started with Peer ID:', node1.peerId.toString())
  node1.getMultiaddrs().forEach(addr => {
    console.log('Listening on:', addr.toString())
  })

  // Listen for incoming messages
  node1.services.pubsub.addEventListener('message', (evt) => {
    const message = uint8ArrayToString(evt.detail.data)
    const fromPeer = evt.detail.from.toString()
    console.log(`MESSAGE RECEIVED from ${fromPeer}: "${message}" on topic ${evt.detail.topic}`)
  })

  // Subscribe to the chat topic
  await node1.services.pubsub.subscribe(TOPIC)
  console.log(`Node 1 Subscribed to topic: ${TOPIC}`)

    try {
      await node1.dial(node2.getMultiaddrs())
      console.log(`Connected to Node_2:`, node2.peerId.toString())
    } catch (err) {
      console.error('Failed to connect to Node_2:', err)
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
      process.exit(0)
    }

    if (input.toLowerCase() === 'peers') {
      const peers = node1.getConnections().map(conn => conn.remotePeer.toString())
      if (peers.length === 0) {
        console.log('No peers connected. Start another chat node and connect to this one!')
      } else {
        console.log('Connected peers:', peers)
      }
      return
    }

    if (input.toLowerCase() === 'help') {
      console.log('\n=== Help ===')
      console.log('• Type any message to send it to all connected peers')
      console.log('• Type "peers" to see connected peers')
      console.log('• Type "quit" to exit')
      console.log('• To connect to another node, run: npm start in another terminal')
      console.log('• Make sure at least 2 nodes are connected to exchange messages\n')
      return
    }

    node2.services.pubsub.addEventListener("message", (evt) => {
      console.log(`node2 received: ${uint8ArrayToString(evt.detail.data)} on topic ${evt.detail.topic}`)
    })
    await node2.services.pubsub.subscribe(`${TOPIC}`)
    

    if (input.trim()) {
      try {

        await node2.services.pubsub.publish(TOPIC, uint8ArrayFromString(input))
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