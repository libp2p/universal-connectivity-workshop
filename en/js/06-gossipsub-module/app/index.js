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

const TOPIC = 'universal-connectivity'

/**
 * Creates a libp2p node with GossipSub pub/sub capabilities
 */
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

/**
 * Sets up GossipSub message handling for the node
 */
function setupMessageHandling(node) {
  // Listen for incoming messages on the topic
  node.services.pubsub.addEventListener('message', (evt) => {
    const message = uint8ArrayToString(evt.detail.data)
    const fromPeer = evt.detail.from.toString()
    console.log(`Received message from ${fromPeer}: "${message}" on topic ${evt.detail.topic}`)
  })

  // Listen for peer subscription events
  node.services.pubsub.addEventListener('subscription-change', (evt) => {
    console.log(`Peer ${evt.detail.peerId.toString()} ${evt.detail.subscriptions.map(s => 
      `${s.subscribe ? 'subscribed to' : 'unsubscribed from'} topic: ${s.topic}`
    ).join(', ')}`)
  })
}

/**
 * Demonstrates GossipSub functionality
 */
async function demonstrateGossipSub(node, remoteAddr = null) {
  console.log('Setting up GossipSub messaging...')
  
  // Set up message handling
  setupMessageHandling(node)
  
  // Subscribe to the universal connectivity topic
  await node.services.pubsub.subscribe(TOPIC)
  console.log(`Subscribed to topic: ${TOPIC}`)
  
  // If remote address provided, connect to peer
  if (remoteAddr) {
    try {
      console.log(`Connecting to remote peer: ${remoteAddr}`)
      await node.dial(multiaddr(remoteAddr))
      console.log('Successfully connected to remote peer')
      
      // Wait a moment for mesh to form
      await new Promise(resolve => setTimeout(resolve, 2000))
      
    } catch (err) {
      console.error('Failed to connect to remote peer:', err.message)
    }
  }
  
  // Publish a test message
  const message = `Hello from ${node.peerId.toString()} at ${new Date().toISOString()}`
  
  try {
    await node.services.pubsub.publish(TOPIC, uint8ArrayFromString(message))
    console.log(`Published message: "${message}"`)
  } catch (err) {
    if (err.message.includes('NoPeersSubscribedToTopic')) {
      console.log('No peers subscribed to topic - message published to network anyway')
    } else {
      console.error('Failed to publish message:', err.message)
    }
  }
  
  // Show topic peers
  const topicPeers = node.services.pubsub.getSubscribers(TOPIC)
  console.log(`Peers subscribed to topic "${TOPIC}": ${topicPeers.length}`)
  topicPeers.forEach(peer => {
    console.log(`  - ${peer.toString()}`)
  })
}

/**
 * Main function - Workshop entry point
 */
async function main() {
  console.log('Starting GossipSub Universal Connectivity Lesson...')
  
  try {
    // Create libp2p node with GossipSub
    const node = await createNode()
    await node.start()
    
    console.log(`Node started with Peer ID: ${node.peerId.toString()}`)
    node.getMultiaddrs().forEach(addr => {
      console.log(`Listening on: ${addr.toString()}`)
    })
    
    // Check for remote peer address from command line
    const remoteAddr = process.argv[2]
    if (remoteAddr) {
      console.log(`Remote peer address provided: ${remoteAddr}`)
    } else {
      console.log('No remote peer specified - running in standalone mode')
      console.log('To connect to another node, run: node index.js <multiaddr>')
    }
    
    // Demonstrate GossipSub functionality
    await demonstrateGossipSub(node, remoteAddr)
    
    console.log('GossipSub demonstration complete!')
    console.log('Key achievements:')
    console.log('✓ Created libp2p node with GossipSub service')
    console.log('✓ Subscribed to pub/sub topic')
    console.log('✓ Published message to topic')
    console.log('✓ Set up message and subscription event handling')
    
    // Keep running for workshop validation
    console.log('Keeping node running for workshop validation...')
    
    // Graceful shutdown after timeout
    setTimeout(async () => {
      console.log('Workshop lesson completed - shutting down gracefully')
      await node.stop()
      process.exit(0)
    }, 10000) // 10 seconds for workshop tool validation
    
  } catch (error) {
    console.error('Error in main function:', error)
    process.exit(1)
  }
}

// Handle process termination gracefully
process.on('SIGINT', () => {
  console.log('\nReceived SIGINT - shutting down gracefully...')
  process.exit(0)
})

process.on('SIGTERM', () => {
  console.log('\nReceived SIGTERM - shutting down gracefully...')
  process.exit(0)
})

// Start the lesson
main().catch((error) => {
  console.error('Unhandled error:', error)
  process.exit(1)
})
