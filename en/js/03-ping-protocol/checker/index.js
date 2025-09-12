// connect.js
import { createLibp2p } from 'libp2p'
import { tcp } from '@libp2p/tcp'
import { noise } from '@chainsafe/libp2p-noise'
import { yamux } from '@chainsafe/libp2p-yamux'
import { ping } from '@libp2p/ping'
import { identify } from '@libp2p/identify'
import { multiaddr } from '@multiformats/multiaddr'
import { createEd25519PeerId } from '@libp2p/peer-id-factory'

async function main () {
//   const targets = process.argv.slice(2).map(a => multiaddr(a))
  const targets = [multiaddr('/ip4/127.0.0.1/tcp/54939/p2p/12D3KooWEiHL4zxdQ44fEATH9aAXSYNStVBTamSDchoron1T1a3T')];
  if (targets.length === 0) {
    console.error('❌  You must pass at least one multiaddr to dial')
    console.error('    Example:')
    console.error('      node connect.js /ip4/127.0.0.1/tcp/15001/p2p/12D3KooW...')
    process.exit(1)
  }

  const peerId = await createEd25519PeerId()
  const node = await createLibp2p({
    peerId,
    addresses: { listen: ['/ip4/0.0.0.0/tcp/0'] }, // random free port
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: { ping: ping(), identify: identify() },
    connectionManager: { idleTimeout: 60_000 }
  })

  // Log incoming connections in the required format
  node.addEventListener("connection:open", async (ev) => {
    const c = ev.detail;
    // Log as: connected,<peer_id>,<multiaddr>
    console.log(
      `connected,${c.remotePeer.toString()},${c.remoteAddr.toString()}`
    );
    try {
      const rtt = await node.services.ping.ping(c.remotePeer);
      // Log as: ping,<peer_id>,<rtt> ms
      console.log(`ping,${c.remotePeer.toString()},${rtt} ms`);
      // Close the connection after ping for demonstration
      await c.close();
    } catch (err) {
      console.warn(`x ping to ${c.remotePeer.toString()} failed:`, err.message);
    }
  });

  node.addEventListener("connection:close", (ev) => {
    const c = ev.detail;
    // Log as: closed,<peer_id>
    console.log(`closed,${c.remotePeer.toString()}`);
    // Optionally exit after closing
    process.exit(0);
  });

  // Log incoming dials (simulate 'incoming' event)
  node.addEventListener("connection:incoming", (ev) => {
    const c = ev.detail;
    // Log as: incoming,<target_multiaddr>,<from_multiaddr>
    // Use remoteAddr as the from address, and pick the first listen address as target
    const listenAddrs = node.getMultiaddrs();
    const targetAddr =
      listenAddrs.length > 0 ? listenAddrs[0].toString() : "unknown";
    console.log(`incoming,${targetAddr},${c.remoteAddr.toString()}`);
  });

  await node.start();
  // Dial all targets
  for (const target of targets) {
    try {
      await node.dial(target);
    } catch (err) {
      console.error("x Failed to dial", target.toString(), err);
    }
  }
}

main().catch((err) => {
  console.error("Unhandled error:", err);
  process.exit(1);
});
