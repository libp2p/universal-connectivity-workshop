import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { circuitRelayServer } from "@libp2p/circuit-relay-v2";
import { identify } from "@libp2p/identify";
import { webSockets } from "@libp2p/websockets";
import { tcp } from "@libp2p/tcp";
import { createLibp2p } from "libp2p";
import { peerIdFromPrivateKey } from "@libp2p/peer-id";
import { keys } from "@libp2p/crypto";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function createNode() {
  const peerIdPath = path.join(__dirname, "peer-id.json");
  const peerIdJson = JSON.parse(fs.readFileSync(peerIdPath, "utf8"));
  const privateKeyBytes = Buffer.from(peerIdJson.privKey, "base64");
  const privateKey = keys.privateKeyFromProtobuf(privateKeyBytes);
  // Generate peer ID from the private key
  const peerId = peerIdFromPrivateKey(privateKey);
  console.log("PeerId:", peerId.toString());

  const node = await createLibp2p({
    privateKey,
    addresses: {
      listen: ["/ip4/0.0.0.0/tcp/4001", "/ip4/0.0.0.0/tcp/4002/ws"],
    },
    transports: [tcp(), webSockets()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      identify: identify(),
      relay: circuitRelayServer({ reservations: 15 }),
    },
  });
  return node;
}

async function main() {
  const node = await createNode();

  await node.start();
  node.addEventListener("error", (evt) => {
    console.error("Node error:", evt.detail);
  });

  console.log(`PeerId: ${node.peerId.toString()}`);
  console.log(`Node started with id ${node.peerId.toString()}`);
  console.log("Listening on:");
  const multiaddrs = node.getMultiaddrs();
  multiaddrs.forEach((ma) => console.log(ma.toString()));

  // Keep the node running
  process.on("SIGTERM", async () => {
    console.log("Shutting down relay node...");
    await node.stop();
  });
}

main().catch(console.error);
