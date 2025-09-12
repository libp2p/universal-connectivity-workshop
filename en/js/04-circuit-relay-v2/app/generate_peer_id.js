import { createEd25519PeerId } from "@libp2p/peer-id-factory";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const peerId = await createEd25519PeerId();
const peerIdData = {
  id: peerId.toString(),
  privKey: Buffer.from(peerId.privateKey).toString("base64"),
  pubKey: Buffer.from(peerId.publicKey).toString("base64"),
};
const outputPath = path.join(__dirname, "peer-id.json");
fs.writeFileSync(outputPath, JSON.stringify(peerIdData, null, 2));
console.log(`Peer ID saved to ${outputPath}`);
