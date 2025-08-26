import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { circuitRelayTransport } from "@libp2p/circuit-relay-v2";
import { identify } from "@libp2p/identify";
import { createLibp2p } from "libp2p";
import { multiaddr } from "@multiformats/multiaddr";
import { tcp } from "@libp2p/tcp";
import { createEd25519PeerId } from "@libp2p/peer-id-factory";

const relayAddr = process.argv[2];
// const relayAddr = multiaddr(
//   "/ip4/127.0.0.1/tcp/4001/p2p/12D3KooWJdPLnHZjYGr32LPoUyQDEt34DL2yZ9B6wyZ3tgdnRr2U"
// );
if (!relayAddr) {
  throw new Error("Relay address must be provided as command line argument");
}

const peerId = await createEd25519PeerId();
const node = await createLibp2p({
  peerId,
  addresses: {
    listen: ["/p2p-circuit"],
  },
  transports: [circuitRelayTransport(), tcp()],
  connectionEncrypters: [noise()],
  streamMuxers: [yamux()],
  services: {
    identify: identify(),
  },
});

console.log(`Node started with id ${node.peerId.toString()}`);
const conn = await node.dial(multiaddr(relayAddr));
console.log(`Connected to the relay ${conn.remotePeer.toString()}`);

node.addEventListener("self:peer:update", (evt) => {
  const relayAddresses = node
    .getMultiaddrs()
    .filter((ma) => ma.toString().includes("/p2p-circuit/"));
  if (relayAddresses.length > 0) {
    console.log(
      `Advertising with a relay address of ${relayAddresses[0].toString()}`
    );
  }
});

// Keep the node running
process.on("SIGTERM", async () => {
  console.log("Shutting down listener node...");
  await node.stop();
});
