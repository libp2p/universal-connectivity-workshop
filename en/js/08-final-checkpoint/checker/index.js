/**
 * Universal Connectivity Checker Application
 * 
 * This is the validation peer that student implementations connect to.
 * It acts as a full-featured libp2p node with all protocols enabled.
 */

import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { gossipsub } from '@chainsafe/libp2p-gossipsub'
import { kadDHT } from '@libp2p/kad-dht'
import { identify } from '@libp2p/identify'
import { ping } from '@libp2p/ping'
import { createEd25519PeerId } from '@libp2p/peer-id-factory'
import { toString as uint8ArrayToString } from 'uint8arrays/to-string'
import { createChatMessage, decodeMessage, isChatMessage, getChatMessageText, isFileMessage, getFileMessageDetails } from './proto-messages.js'
import { mdns } from '@libp2p/mdns'

// Universal Connectivity Protocol Topics
const CHAT_TOPIC = 'universal-connectivity'
const FILE_TOPIC = 'universal-connectivity-file'
const BROWSER_DISCOVERY_TOPIC = 'universal-connectivity-browser-peer-discovery'


async function createCheckerNode() {
  console.log('Starting Universal Connectivity Checker...')
  
  const peerId = await createEd25519PeerId()
  console.log(`Local peer id: ${peerId.toString()}`)

  const node = await createLibp2p({
    peerId,
    addresses: {
      listen: [
        '/ip4/0.0.0.0/tcp/0'
      ]
    },
    transports: [
      tcp()
    ],
    connectionEncrypters: [
      noise()
    ],
    streamMuxers: [
      yamux()
    ],
    peerDiscovery: [
      mdns()
    ],
    services: {
      identify: identify({
        protocolPrefix: 'ipfs',
        agentVersion: 'universal-connectivity-checker/1.0.0'
      }),
      ping: ping({
        protocolPrefix: 'ipfs'
      }),
      pubsub: gossipsub({
        emitSelf: false,
        allowPublishToZeroPeers: true,
        messageProcessingConcurrency: 10,
        canRelayMessage: true,
      }),
      dht: kadDHT({
        clientMode: false,
        protocol: '/ipfs/kad/1.0.0',
        peerInfoMapper: (peer) => peer
      })
    },
    connectionManager: {
      minConnections: 0,
      maxConnections: 100,
      pollInterval: 2000,
      autoDialInterval: 10000
    }
  })

  return node
}

/**
 * Set up event handlers for all protocols
 */
function setupEventHandlers(node) {
  // peer connection events
  node.addEventListener('peer:connect', (evt) => {
    const peerId = evt.detail.toString()
    console.log(`Connected to: ${peerId}`)
  })

  node.addEventListener('peer:disconnect', (evt) => {
    const peerId = evt.detail.toString()
    console.log(`Disconnected from: ${peerId}`)
  })

  // Identify protocol events
  node.addEventListener('peer:identify', (evt) => {
    const peerId = evt.detail.peerId.toString()
    const protocols = evt.detail.protocols
    const agentVersion = evt.detail.agentVersion || 'unknown'
    const protocolVersion = evt.detail.protocolVersion || 'unknown'
    
    console.log(`Received identify from ${peerId}: protocol_version: ${protocolVersion}`)
    console.log(`Peer agent: ${agentVersion}`)
    console.log(`Peer supports ${protocols.length} protocols`)
  })

  // Track when peer updates happen
  node.addEventListener('peer:update', (evt) => {
    const peerId = evt.detail.peer.id.toString()
    console.log(`Peer updated: ${peerId}`)
  })
}

/**
 * Set up Gossipsub subscriptions and message handling
 */
function setupGossipsub(node) {
  node.services.pubsub.subscribe(CHAT_TOPIC)
  console.log(`Subscribed to topic: ${CHAT_TOPIC}`)
  
  node.services.pubsub.subscribe(FILE_TOPIC)
  console.log(`Subscribed to topic: ${FILE_TOPIC}`)
  
  node.services.pubsub.subscribe(BROWSER_DISCOVERY_TOPIC)
  console.log(`Subscribed to topic: ${BROWSER_DISCOVERY_TOPIC}`)

  // handle incoming messages
  node.services.pubsub.addEventListener('message', (evt) => {
    const topic = evt.detail.topic
    const from = evt.detail.from.toString()
    
    try {
      // Try to decode as Universal Connectivity message
      const decodedMsg = decodeMessage(evt.detail.data)
      
      if (decodedMsg && isChatMessage(decodedMsg)) {
        const messageText = getChatMessageText(decodedMsg)
        console.log(`Received chat message from ${from}: ${messageText}`)
      } else if (decodedMsg && isFileMessage(decodedMsg)) {
        const fileDetails = getFileMessageDetails(decodedMsg)
        console.log(`Received file message from ${from}: ${fileDetails.name} (${fileDetails.size} bytes)`)
      } else if (topic === BROWSER_DISCOVERY_TOPIC) {
        console.log(`Received browser discovery message from ${from}`)
      } else {
        // Fallback to raw text
        const messageText = uint8ArrayToString(evt.detail.data)
        console.log(`Received message on topic ${topic} from ${from}: ${messageText}`)
      }
    } catch (error) {
      console.log(`Received binary message from ${from} on topic ${topic}`)
    }
  })

  // Track subscription changes
  node.services.pubsub.addEventListener('subscription-change', (evt) => {
    const peerId = evt.detail.peerId.toString()
    const peerShort = peerId.slice(-8)
    console.log(`[GOSSIPSUB] subscription-change event from ${peerShort}`)
    
    evt.detail.subscriptions.forEach(sub => {
      console.log(`[GOSSIPSUB]   Topic: ${sub.topic}, Subscribe: ${sub.subscribe}`)
      
      if (sub.subscribe) {
        console.log(`Peer ${peerShort} subscribed to topic: ${sub.topic}`)
        
        // If it's the chat topic, show mesh status
        if (sub.topic === CHAT_TOPIC) {
          const currentSubs = node.services.pubsub.getSubscribers(CHAT_TOPIC)
          console.log(`✓ Chat mesh now has ${currentSubs.length} subscriber(s)`)
          if (currentSubs.length > 0) {
            currentSubs.forEach(peer => {
              console.log(`  - Mesh peer: ${peer.toString().slice(-8)}`)
            })
          }
        }
      } else {
        console.log(`Peer ${peerShort} unsubscribed from topic: ${sub.topic}`)
      }
    })
  })
}


async function sendWelcomeMessage(node) {
  try {
    const welcomeMsg = 'Hello from the Universal Connectivity checker!'
    const messageBytes = createChatMessage(welcomeMsg)
    
    const peers = node.services.pubsub.getSubscribers(CHAT_TOPIC)
    if (peers.length > 0) {
      console.log(`Sent welcome chat message to connected peers`)
      await node.services.pubsub.publish(CHAT_TOPIC, messageBytes)
    }
  } catch (error) {
    // silently handle if no peers subscribed yet
  }
}

/**
 * Perform ping test on connected peers
 */
async function pingPeers(node) {
  const connections = node.getConnections()
  
  for (const connection of connections) {
    try {
      const peerId = connection.remotePeer
      const startTime = Date.now()
      
      // Create a stream for ping
      await node.services.ping.ping(peerId)
      
      const rtt = Date.now() - startTime
      console.log(`Received a ping from ${peerId.toString()}, round trip time: ${rtt} ms`)
    } catch (error) {
      console.log(`Ping failed for ${connection.remotePeer.toString()}: ${error.message}`)
    }
  }
}

/**
 * Main application function
 */
async function main() {
  try {
    // Create and start the checker node
    const node = await createCheckerNode()
    
    await node.start()
    console.log('Checker node started successfully')

    // Display listening addresses
    const addrs = node.getMultiaddrs()
    console.log(`Listening on ${addrs.length} address(es)`)
    addrs.forEach(addr => {
      console.log(`  ${addr.toString()}`)
    })

    setupEventHandlers(node)
    setupGossipsub(node)

    await new Promise(resolve => setTimeout(resolve, 10000))

    let welcomeSent = false
    node.addEventListener('peer:connect', async () => {
      if (!welcomeSent) {
        await new Promise(resolve => setTimeout(resolve, 12000))
        await sendWelcomeMessage(node)
        welcomeSent = true
      }
    })

    setInterval(async () => {
      const connections = node.getConnections()
      if (connections.length > 0) {
        await pingPeers(node)
      }
    }, 5000)

    process.on('SIGTERM', async () => {
      console.log('Received SIGTERM - shutting down gracefully...')
      await node.stop()
      console.log('Checker stopped successfully')
      process.exit(0)
    })

    const timeout = process.env.TIMEOUT_DURATION || '60'
    const timeoutMs = parseInt(timeout) * 1000
    
    console.log(`Checker will run for ${timeout}s`)
    
    await new Promise(resolve => setTimeout(resolve, timeoutMs))
    
    console.log('Timeout reached - shutting down')
    await node.stop()
    console.log('Checker stopped successfully')
    process.exit(0)

  } catch (error) {
    console.error('Fatal error:', error)
    process.exit(1)
  }
}


main().catch((error) => {
  console.error('Unhandled error:', error)
  process.exit(1)
})
