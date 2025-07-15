import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { ping } from '@libp2p/ping'
import { identify } from '@libp2p/identify'
import { multiaddr } from '@multiformats/multiaddr'
import { createEd25519PeerId } from '@libp2p/peer-id-factory';

async function main() {
    console.log('Starting Universal Connectivity application...')

    // Parse the remote peer addresses from the environment variable
    let remoteAddrs = []
    if (process.env.REMOTE_PEERS) {
        remoteAddrs = process.env.REMOTE_PEERS
            .split(',')                     // Split the string at ','
            .map(addr => addr.trim())       // Trim whitespace of each string
            .filter(addr => addr !== '')    // Filter out empty strings
            .map(addr => multiaddr(addr))   // Parse each string into Multiaddr
    }

    
    // Create the libp2p node
    
  const peerId = await createEd25519PeerId()
    
    const node = await createLibp2p({
      peerId,
        addresses: {
            listen: ['/ip4/0.0.0.0/tcp/0']
        },
        transports: [
            tcp()
        ],
        connectionEncrypters: [noise()],
        streamMuxers: [
            yamux()
        ],
        services: {
            ping: ping(),
            identify: identify()
        },
        connectionManager: {
            idleTimeout: 60000
        }
    })

    console.log('Local peer id:', node.peerId.toString())

    // Set up event handlers
    node.addEventListener('peer:connect', (event) => {
        const peerId = event.detail
        console.log('Connected to:', peerId.toString())
    })

    node.addEventListener('peer:disconnect', (event) => {
        const peerId = event.detail
        console.log('Disconnected from:', peerId.toString())
    })

    node.addEventListener('connection:open', (event) => {
        const connection = event.detail
        console.log('Connection opened to:', connection.remotePeer.toString(), 'via', connection.remoteAddr.toString())
    })

    node.addEventListener('connection:close', (event) => {
        const connection = event.detail
        console.log('Connection closed to:', connection.remotePeer.toString())
    })

    // Start the node
    await node.start()
    console.log('Node started successfully')
    node.getMultiaddrs().forEach(addr => {
        console.log('  •', addr.toString())   // e.g. /ip4/127.0.0.1/tcp/57139/p2p/12D3KooW...
        })


    // Dial all of the remote peer Multiaddrs
    for (const addr of remoteAddrs) {
        try {
            console.log('Dialing:', addr.toString())
            await node.dial(addr)
        } catch (error) {
            console.error('Failed to dial', addr.toString(), ':', error.message)
        }
    }

    // Keep the process running
    process.on('SIGINT', async () => {
        console.log('Shutting down...')
        await node.stop()
        process.exit(0)
    })

    console.log('Node is running. Press Ctrl+C to stop.')
}

main().catch(console.error)