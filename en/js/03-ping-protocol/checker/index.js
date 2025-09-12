import { createLibp2p } from "libp2p";
import { tcp } from "@libp2p/tcp";
import { noise } from "@chainsafe/libp2p-noise";
import { yamux } from "@chainsafe/libp2p-yamux";
import { ping } from "@libp2p/ping";
import { identify } from "@libp2p/identify";
import { multiaddr } from "@multiformats/multiaddr";
import fs from "fs";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getLessonMultiaddr() {
  let attempts = 0;
  const maxAttempts = 30;

  while (attempts < maxAttempts) {
    try {
      if (fs.existsSync("/app/stdout.log")) {
        const stdoutLog = fs.readFileSync("/app/stdout.log", "utf8");

        // Extract peer ID
        const peerIdMatch = stdoutLog.match(/Local peer id: ([A-Za-z0-9]+)/);
        if (peerIdMatch) {
          const peerId = peerIdMatch[1];

          // Look for Docker network IP address first, then fallback to localhost
          const dockerIpMatch = stdoutLog.match(
            /\/ip4\/172\.16\.16\.16\/tcp\/(\d+)\/p2p\/[A-Za-z0-9]+/
          );
          if (dockerIpMatch) {
            const port = dockerIpMatch[1];
            return `/ip4/172.16.16.16/tcp/${port}/p2p/${peerId}`;
          }
        }
      }
    } catch (err) {
      // Ignore errors, keep trying
    }
    await sleep(2000);
    attempts++;
  }
  throw new Error("Could not get lesson multiaddr from stdout.log");
}

async function main() {
  try {
    console.log("ping_protocol,starting,checker");

    // Get lesson multiaddr from stdout.log
    const lessonMultiaddr = await getLessonMultiaddr();
    console.log("ping_protocol,found,lesson_address");

    const targets = [multiaddr(lessonMultiaddr)];

    const node = await createLibp2p({
      addresses: { listen: ["/ip4/0.0.0.0/tcp/0"] }, // random free port
      transports: [tcp()],
      connectionEncrypters: [noise()],
      streamMuxers: [yamux()],
      services: { ping: ping(), identify: identify() },
      connectionManager: { idleTimeout: 60_000 },
    });

    let connectionSuccess = false;
    let pingSuccess = false;

    // Log connections and ping results
    node.addEventListener("connection:open", async (ev) => {
      const c = ev.detail;
      connectionSuccess = true;
      console.log(`connected to:`);
      console.log(`PeerId: ${c.remotePeer.toString()}`);
      console.log(`maddr: ${c.remoteAddr.toString()}`);

      try {
        const rtt = await node.services.ping.ping(c.remotePeer);
        pingSuccess = true;
        console.log(`🏓  ${c.remotePeer} RTT = ${rtt} ms`);
        await c.close();
      } catch (err) {
        console.warn(`⚠️  ping to ${c.remotePeer} failed:`, err.message);
      }
    });

    node.addEventListener("connection:close", (ev) => {
      console.log(`closed,${ev.detail.remotePeer.toString()}`);
    });

    await node.start();

    // Dial the lesson node
    for (const target of targets) {
      try {
        await node.dial(target);
      } catch (err) {
        console.error("⚠️   Dial failed:", target.toString(), err.message);
      }
    }

    // Wait a moment for ping to complete
    await sleep(3000);

    // Write final validation result
    if (connectionSuccess && pingSuccess) {
      console.log("ping_protocol,success,complete_flow");
      fs.writeFileSync(
        "/app/checker.log",
        "✅ Ping Protocol validation passed\n" +
          "✅ Lesson node: PASS\n" +
          "✅ Checker connection: PASS\n" +
          "✅ Ping protocol: PASS\n" +
          `Completed at: ${new Date().toISOString()}`
      );
      process.exit(0);
    } else {
      console.log("ping_protocol,failed,validation");
      fs.writeFileSync(
        "/app/checker.log",
        "❌ Ping Protocol validation failed"
      );
      process.exit(1);
    }
  } catch (error) {
    console.log(`ping_protocol,error,${error.message}`);
    fs.writeFileSync("/app/checker.log", `❌ Error: ${error.message}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Unhandled error:", err);
  process.exit(1);
});
