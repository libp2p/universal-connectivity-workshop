// connect.js
import { createLibp2p } from "libp2p";
import { tcp } from "@libp2p/tcp";
import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { ping } from "@libp2p/ping";
import { identify } from "@libp2p/identify";
import { multiaddr } from "@multiformats/multiaddr";
import { createEd25519PeerId } from "@libp2p/peer-id-factory";

async function main() {
  //   const targets = process.argv.slice(2).map(a => multiaddr(a))
  const targets = [
    multiaddr(
      "/ip4/127.0.0.1/tcp/38527/p2p/12D3KooWMBaGnf5ggeev9Mu1siELsBwrMdTes3hDpNhbbwxCfbjv"
    ),
  ];
  if (targets.length === 0) {
    console.error("❌  You must pass at least one multiaddr to dial");
    console.error("    Example:");
    console.error(
      "      node connect.js /ip4/127.0.0.1/tcp/15001/p2p/12D3KooW..."
    );
    process.exit(1);
  }

  const peerId = await createEd25519PeerId();
  const node = await createLibp2p({
    peerId,
    addresses: { listen: ["/ip4/0.0.0.0/tcp/0"] }, // random free port
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: { ping: ping(), identify: identify() },
    connectionManager: { idleTimeout: 60_000 },
  });

  // ── 3. Add basic connection‑lifecycle logging ───────────────────────────────
  node.addEventListener("connection:open", async (ev) => {
    const c = ev.detail;
    const maddr = c.remoteAddr.toString();
    console.log("connected to:");
    console.log(`PeerId: ${c.remotePeer.toString()}`);
    console.log(`maddr: ${maddr}`);
    const peer = c.remotePeer;
    try {
      const rtt = await node.services.ping.ping(peer);
      console.log(`🏓  ${peer} RTT = ${rtt} ms`);
    } catch (err) {
      console.warn(`⚠️  ping to ${peer} failed:`, err.message);
    }
  });

  node.addEventListener("connection:close", (ev) => {
    console.log(`closed,${ev.detail.remotePeer.toString()}`);
  });

  for (const addr of targets) {
    try {
      await node.dial(addr);
    } catch (err) {
      console.error("⚠️   Dial failed:", addr.toString(), err.message);
    }
  }
}

main().catch((err) => {
  console.error("Unhandled error:", err);
  process.exit(1);
});
