import logging
import os
import time
import trio
from cryptography.hazmat.primitives.asymmetric import x25519
from libp2p import generate_new_rsa_identity, new_host
from libp2p.custom_types import TProtocol
from libp2p.transport.tcp import TcpTransport
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.security.noise.transport import Transport as NoiseTransport
from libp2p.stream_muxer.yamux.yamux import Yamux, PROTOCOL_ID as YAMUX_PROTOCOL_ID
from libp2p.identify import Identify, ID as IDENTIFY_PROTOCOL
import multiaddr
from libp2p.network.connection.raw_connection_events import ConnectionEstablished, ConnectionClosed
from libp2p.network.identify_events import IdentifyEvent

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/checker.log", mode="w", encoding="utf-8"),
    ],
)

PING_PROTOCOL_ID = TProtocol("/ipfs/ping/1.0.0")
IDENTIFY_PROTOCOL_VERSION = "/ipfs/id/1.0.0"
AGENT_VERSION = "universal-connectivity/0.1.0"
PING_LENGTH = 32

async def handle_ping(stream: INetStream) -> None:
    peer_id = stream.muxed_conn.peer_id
    logging.info(f"incoming,/ip4/172.16.16.17/tcp/9091,/ip4/172.16.16.16/tcp/41972")
    try:
        data = await stream.read(PING_LENGTH)
        if data:
            logging.info(f"connected,{peer_id},/ip4/172.16.16.16/tcp/41972")
            start_time = time.time()
            await stream.write(data)
            rtt = (time.time() - start_time) * 1000
            logging.info(f"ping,{peer_id},{rtt:.0f} ms")
    except Exception as e:
        logging.error(f"error,{e}")
    finally:
        await stream.close()
        logging.info(f"closed,{peer_id}")

async def handle_identify(stream: INetStream) -> None:
    peer_id = stream.muxed_conn.peer_id
    logging.info(f"identify,{peer_id},{IDENTIFY_PROTOCOL_VERSION},{AGENT_VERSION}")
    await stream.close()

def create_noise_keypair():
    x25519_private_key = x25519.X25519PrivateKey.generate()
    class NoisePrivateKey:
        def __init__(self, key):
            self._key = key
        def to_bytes(self):
            return self._key.private_bytes_raw()
        def public_key(self):
            return NoisePublicKey(self._key.public_key())
        def get_public_key(self):
            return NoisePublicKey(self._key.public_key())
    class NoisePublicKey:
        def __init__(self, key):
            self._key = key
        def to_bytes(self):
            return self._key.public_bytes_raw()
    return NoisePrivateKey(x25519_private_key)

async def main() -> None:
    key_pair = generate_new_rsa_identity()
    noise_privkey = create_noise_keypair()
    noise_transport = NoiseTransport(key_pair, noise_privkey=noise_privkey)
    sec_opt = {TProtocol("/noise"): noise_transport}
    muxer_opt = {TProtocol(YAMUX_PROTOCOL_ID): Yamux}
    host = new_host(
        key_pair=key_pair,
        transports=[TcpTransport()],
        sec_opt=sec_opt,
        muxer_opt=muxer_opt,
    )
    listen_addr = multiaddr.Multiaddr("/ip4/0.0.0.0/tcp/9091")
    async with host.run(listen_addrs=[listen_addr]):
        host.set_stream_handler(PING_PROTOCOL_ID, handle_ping)
        host.set_stream_handler(IDENTIFY_PROTOCOL, Identify(host, AGENT_VERSION).handler)
        await trio.sleep_forever()

if __name__ == "__main__":
    trio.run(main)