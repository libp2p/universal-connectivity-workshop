import { createLibp2p } from "libp2p";
import { tcp } from "@libp2p/tcp";
import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { multiaddr } from "@multiformats/multiaddr";
import { webSockets } from "@libp2p/websockets";
import { circuitRelayTransport } from "@libp2p/circuit-relay-v2";
import { identify } from "@libp2p/identify";
import { createEd25519PeerId } from "@libp2p/peer-id-factory";

const LISTENER_RELAY_ADDR = process.argv[2];
// const LISTENER_RELAY_ADDR = multiaddr(
//   "/ip4/127.0.0.1/tcp/4001/p2p/12D3KooWJdPLnHZjYGr32LPoUyQDEt34DL2yZ9B6wyZ3tgdnRr2U/p2p-circuit/p2p/12D3KooWPDK9yfeoKGxTq55Hf15jqw6hNG5TUuqCDDMJkBo5PG4D"
// );
if (!LISTENER_RELAY_ADDR) {
  throw new Error(
    "Listener relay address must be provided as command line argument"
  );
}

const main = async () => {
  try {
    const peerId = await createEd25519PeerId();
    const node = await createLibp2p({
      peerId,
      addresses: { listen: [] },
      transports: [tcp(), webSockets(), circuitRelayTransport()],
      connectionEncrypters: [noise()],
      streamMuxers: [yamux()],
      services: {
        identify: identify(),
      },
    });

    await node.start();
    console.log(`Node started with id ${node.peerId.toString()}`);

    try {
      await node.dial(multiaddr(LISTENER_RELAY_ADDR));
      console.log(`Connected to the listener node via ${LISTENER_RELAY_ADDR}`);
      console.log("DIAL SUCCESS");
    } catch (err) {
      console.error("Dial failed:", err);
      process.exit(1);
    }

    // Keep node running briefly to maintain connection
    setTimeout(async () => {
      console.log("Shutting down dialer node...");
      await node.stop();
    }, 5000);
  } catch (err) {
    console.error("Dialer setup failed:", err);
    process.exit(1);
  }
};

main().catch(console.error);
