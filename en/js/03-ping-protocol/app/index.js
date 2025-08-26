import { createLibp2p } from "libp2p";
import { tcp } from "@libp2p/tcp";
import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { ping } from "@libp2p/ping";
import { identify } from "@libp2p/identify";
import { multiaddr } from "@multiformats/multiaddr";
import { createEd25519PeerId } from "@libp2p/peer-id-factory";

async function main() {
  console.log("Starting Universal Connectivity application...");

  const relayAddr = process.argv[2];
  const remoteAddrs = relayAddr ? [multiaddr(relayAddr)] : [];

  const peerId = await createEd25519PeerId();
  const node = await createLibp2p({
    peerId,
    addresses: {
      listen: ["/ip4/0.0.0.0/tcp/0"],
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      ping: ping({
        protocolPrefix: "ipfs",
        pingInterval: 1000, 
        timeout: 5000,
      }),
      identify: identify(),
    },
    connectionManager: {
      idleTimeout: 60000,
    },
  });
  // Start the node
  await node.start();
  console.log("Local peer id:", node.peerId.toString());
  console.log("Node started successfully");
  node.getMultiaddrs().forEach((addr) => {
    console.log("  •", addr.toString()); // e.g. /ip4/127.0.0.1/tcp/57139/p2p/12D3KooW...
  });

  // Set up event handlers
  // Peer lifecycle events
  node.addEventListener("peer:connect", (evt) => {
    console.log(`Peer connected: ${evt.detail.toString()}`);
  });

  node.addEventListener("peer:disconnect", (evt) => {
    console.log(`Peer disconnected: ${evt.detail.toString()}`);
  });

  node.addEventListener("connection:open", async (event) => {
    const connection = event.detail;

    const localAddr =
      connection.localAddr?.toString() ??
      node.getMultiaddrs()[0]?.toString() ??
      "unknown";
    const remoteAddr = connection.remoteAddr.toString();

    console.log("\nConnection opened:");
    console.log(`   Remote peer : ${connection.remotePeer.toString()}`);
    console.log(`   Local addr  : ${localAddr}`);
    console.log(`   Remote addr : ${remoteAddr}`);

    try {
      const rtt = await node.services.ping.ping(connection.remotePeer);
      console.log(`   • Ping RTT    : ${rtt} ms`);
    } catch (error) {
      console.warn(`   • Ping failed : ${error.message}`);
    }
  });

  node.addEventListener("connection:close", (event) => {
    const connection = event.detail;
    console.log(`Connection closed: ${connection.remotePeer.toString()}`);
  });

  // Dial all of the remote peer Multiaddrs
  for (const addr of remoteAddrs) {
    try {
      console.log("Dialing:", addr.toString());
      await node.dial(addr);
    } catch (error) {
      console.error("Failed to dial", addr.toString(), ":", error.message);
    }
  }
  console.log("Node is running. Press Ctrl+C to stop.");
  // Graceful shutdown
  const cleanup = async () => {
    console.log("\nShutting down...");
    await node.stop();
    process.exit(0);
  };

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  // Keep the process alive
  process.stdin.resume();
}

main().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
