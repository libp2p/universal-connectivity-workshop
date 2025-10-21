import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { gossipsub } from '@chainsafe/libp2p-gossipsub'
import { kadDHT } from '@libp2p/kad-dht'
import { identify } from '@libp2p/identify'
import { ping } from '@libp2p/ping'
import { createEd25519PeerId } from '@libp2p/peer-id-factory'
import { multiaddr } from '@multiformats/multiaddr'
import { ChatRoom } from './chatroom.js'
import { mdns } from '@libp2p/mdns'

/**
 * Create a fully configured libp2p node with all protocols
 */
async function createUniversalConnectivityNode() {
  console.log('Starting Universal Connectivity Application...')

  const peerId = await createEd25519PeerId()
  console.log(`[SYSTEM] Generated Peer ID: ${peerId.toString()}`)

  const node = await createLibp2p({
    peerId,
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']
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
  // Peer connection events
  node.addEventListener('peer:connect', (evt) => {
    const peerId = evt.detail.toString()
    console.log(`[CONNECTION] Connected to peer: ${peerId}`)
  })

  node.addEventListener('peer:disconnect', (evt) => {
    const peerId = evt.detail.toString()
    console.log(`[CONNECTION] Disconnected from peer: ${peerId}`)
  })

  // Identify protocol events
  node.addEventListener('peer:identify', (evt) => {
    const peerId = evt.detail.peerId.toString()
    const protocols = evt.detail.protocols
    const addresses = evt.detail.listenAddrs
    const protocolVersion = evt.detail.protocolVersion || 'unknown'
    const agentVersion = evt.detail.agentVersion || 'unknown'

    console.log(`[IDENTIFY] Received identify from: ${peerId}`)
    console.log(`[IDENTIFY]   Protocol Version: ${protocolVersion}`)
    console.log(`[IDENTIFY]   Agent Version: ${agentVersion}`)
    console.log(`[IDENTIFY]   Protocols: ${protocols.length} protocol(s)`)
    if (protocols.length > 0) {
      protocols.slice(0, 5).forEach(p => {
        console.log(`[IDENTIFY]     - ${p}`)
      })
      if (protocols.length > 5) {
        console.log(`[IDENTIFY]     ... and ${protocols.length - 5} more`)
      }
    }
    console.log(`[IDENTIFY]   Addresses: ${addresses.length} address(es)`)
  })

  // Connection closure events
  node.addEventListener('connection:close', (evt) => {
    console.log(`[CONNECTION] Connection closed`)
  })

  // DHT events
  console.log('[DHT] Kademlia DHT initialized in server mode')
}

// helper: wait for identify that advertises goosipsub (or timeout)
function waitForPeerWithPubsub(node, timeoutMs = 5000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      node.removeEventListener('peer:identify', onIdentify)
      resolve(false) // timed out
    }, timeoutMs)

    function onIdentify(evt) {
      const peerId = evt.detail.peerId.toString()
      const protocols = evt.detail.protocols || []
      const hasGossipsub = protocols.some(p => p.includes('gossipsub'))
      console.log(`[IDENTIFY] Peer ${peerId.slice(-8)} supports:`, protocols)
      if (hasGossipsub) {
        clearTimeout(timer)
        node.removeEventListener('peer:identify', onIdentify)
        resolve(true)
      }
      // otherwise keep waiting until timeout
    }

    node.addEventListener('peer:identify', onIdentify)
  })
}

/**
 * Connect to remote peers if specified
 */
async function connectToRemotePeers(node, remotePeerAddrs) {
  if (!remotePeerAddrs || remotePeerAddrs.length === 0) {
    console.log('[SYSTEM] No remote peers specified - running in standalone mode')
    return
  }

  for (const addrString of remotePeerAddrs) {
    try {
      console.log(`[CONNECTION] Attempting to connect to: ${addrString}`)
      const addr = multiaddr(addrString)
      await node.dial(addr)
      console.log(`[CONNECTION] Successfully connected to: ${addrString}`)

      // Ping the remote peer to test connectivity
      try {
        const startTime = Date.now()
        await node.services.ping.ping(addr)
        const rtt = Date.now() - startTime
        console.log(`[PING] Received a ping response, round trip time: ${rtt} ms`)
      } catch (pingError) {
        console.log(`[PING] Ping failed: ${pingError.message}`)
      }
    } catch (error) {
      console.error(`[CONNECTION] Failed to connect to ${addrString}:`, error.message)
    }
  }
}

/**
 * Main application function
 */
async function main() {
  try {
    // Create libp2p node
    const node = await createUniversalConnectivityNode()

    // Start the node
    await node.start()
    console.log('[SYSTEM] Node started successfully')

    // Display listening addresses
    const addrs = node.getMultiaddrs()
    console.log(`[SYSTEM] Listening on ${addrs.length} address(es):`)
    addrs.forEach(addr => {
      console.log(`[SYSTEM]   ${addr.toString()}`)
    })

    // Set up event handlers
    setupEventHandlers(node)

    // Get remote peer addresses from environment variable or command line
    const remotePeerEnv = process.env.REMOTE_PEER || process.env.REMOTE_PEERS || ''
    const remotePeerArgs = process.argv.slice(2).filter(arg =>
      arg.startsWith('/ip4/') || arg.startsWith('/ip6/') || arg.startsWith('--connect=')
    ).map(arg => arg.replace('--connect=', ''))

    const remotePeerAddrs = [
      ...remotePeerEnv.split(',').filter(s => s.trim()),
      ...remotePeerArgs
    ]

    // STEP 1: Subscribe to chat topics FIRST (even before connecting)
    // This is critical! Subscribe early so when peers connect, they already know your subscriptions
    console.log('\n[CHAT] Initializing chat room...')
    const chatRoom = await ChatRoom.join(node, null) // null = use default nickname

    // STEP 2: Connect to remote peers AFTER subscribing
    await connectToRemotePeers(node, remotePeerAddrs)

    // CRITICAL: Wait for Identify protocol to complete!
    // Gossipsub needs to know remote peer supports Gossipsub protocol (via Identify)
    // before it can add them to the mesh
    console.log('[CHAT] Waiting for Identify protocol to exchange supported protocols...')
    //await new Promise(resolve => setTimeout(resolve, 10000)) // Give Identify time to complete
    

    // usage in main after connectToRemotePeers(...)
    console.log('[CHAT] Waiting for Identify protocol(s) that advertise pubsub...')
    const identified = await waitForPeerWithPubsub(node, 8000)
    if (!identified) {
      console.log('[CHAT] Warning: no peer advertised gossipsub within timeout. Continuing checks...')
    } else {
      console.log('[CHAT] At least one peer advertises gossipsub')
    }


    // STEP 3: Check Gossipsub status
    console.log('[CHAT] Checking Gossipsub status...')

    // Get connected peers
    const connections = node.getConnections()
    console.log(`[DEBUG] Connected to ${connections.length} peer(s):`)
    connections.forEach(conn => {
      console.log(`[DEBUG]   - ${conn.remotePeer.toString().slice(-8)}`)
    })

    // Check who's subscribed locally
    const localTopics = node.services.pubsub.getTopics()
    console.log(`[DEBUG] Local subscriptions: ${localTopics.join(', ')}`)

    // Try to get peers for each topic
    localTopics.forEach(topic => {
      const topicPeers = node.services.pubsub.getSubscribers(topic)
      console.log(`[DEBUG] Topic "${topic}": ${topicPeers.length} peer(s)`)
    })

    // Manual check every second for 10 seconds
    console.log('[CHAT] Waiting up to 10 seconds for mesh to form...')

    let meshFormed = false
    for (let i = 0; i < 10; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000))

      const subscribers = node.services.pubsub.getSubscribers('universal-connectivity')
      console.log(`[CHAT] Check ${i + 1}/10: ${subscribers.length} peer(s) in mesh`)

      if (subscribers.length > 0) {
        console.log(`[CHAT] ✅ Mesh formed with ${subscribers.length} peer(s)!`)
        meshFormed = true
        break
      }
    }

    // STEP 4: Verify mesh formation and provide clear feedback
    const subscribers = node.services.pubsub.getSubscribers('universal-connectivity')

    if (subscribers.length > 0) {
      console.log(`\n${'='.repeat(60)}`)
      console.log('✅ GOSSIPSUB MESH SUCCESSFULLY FORMED!')
      console.log('='.repeat(60))
      console.log(`[CHAT] Connected to ${subscribers.length} peer(s) in mesh:`)
      subscribers.forEach(peer => {
        console.log(`[CHAT]   ✓ ${peer.toString()}`)
      })
      console.log('='.repeat(60))
      console.log('✅ READY TO CHAT!\n')
    } else {
      console.log(`\n${'='.repeat(60)}`)
      console.log('⚠️  NO MESH PEERS FOUND')
      console.log('='.repeat(60))
      console.log('[CHAT] Running in standalone mode')
      console.log('[CHAT] Start another peer and connect it to this node')
      console.log('[CHAT] Messages will be queued until peers connect')
      console.log('='.repeat(60) + '\n')
    }

    // Send introduction message
    try {
      await chatRoom.sendIntroduction()
    } catch (error) {
      // Silent fail - normal for standalone mode
    }

    // Check if interactive mode is enabled
    const isInteractive = process.env.INTERACTIVE !== 'false' && process.stdin.isTTY

    if (isInteractive) {
      // Start interactive chat
      await chatRoom.startInteractive()
    } else {
      console.log('[SYSTEM] Running in non-interactive mode')
      console.log('[SYSTEM] Listening for messages...')

      // Set up message handler
      chatRoom.onMessage((msg) => {
        console.log(msg.toString())
      })

      // Send periodic heartbeat messages
      const heartbeatInterval = setInterval(async () => {
        try {
          const peerCount = chatRoom.getPeerCount()
          await chatRoom.publishMessage(`Heartbeat - ${peerCount} peer(s) connected`)
        } catch (error) {
          console.error('[HEARTBEAT] Error:', error.message)
        }
      }, 30000) // Every 30 seconds

      // Keep the process running
      process.on('SIGTERM', async () => {
        console.log('\n[SYSTEM] Received SIGTERM - shutting down gracefully...')
        clearInterval(heartbeatInterval)
        await node.stop()
        process.exit(0)
      })

      // For Docker environments, wait for a timeout
      const timeoutDuration = process.env.TIMEOUT_DURATION || '60s'
      const timeoutMs = parseInt(timeoutDuration) * 1000 || 60000

      console.log(`[SYSTEM] Will run for ${timeoutDuration} then exit`)
      setTimeout(async () => {
        console.log('[SYSTEM] Timeout reached - shutting down')
        clearInterval(heartbeatInterval)
        await node.stop()
        console.log('[SYSTEM] Node stopped successfully')
        process.exit(0)
      }, timeoutMs)
    }

  } catch (error) {
    console.error('[ERROR] Fatal error:', error)
    process.exit(1)
  }
}

// Run the application
main().catch((error) => {
  console.error('[ERROR] Unhandled error:', error)
  process.exit(1)
})

