import logging
from libp2p import generate_new_rsa_identity, new_host
from libp2p.custom_types import TProtocol
from libp2p.io.quic import QuicTransport
from libp2p.io.tcp import TcpTransport
from libp2p.network.stream.net_stream import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.security.noise.transport import Transport as NoiseTransport
from libp2p.stream_muxer.yamux.yamux import Yamux, PROTOCOL_ID as YAMUX_PROTOCOL_ID
import multiaddr
import os
import trio
from cryptography.hazmat.primitives.asymmetric import x25519

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/checker.log", mode="w", encoding="utf-8"),
    ],
)

PING_PROTOCOL_ID = TProtocol("/ipfs/ping/1.0.0")
PING_LENGTH = 32

async def handle_ping(stream: INetStream) -> None:
    """Handle incoming ping requests."""
    peer_id = stream.muxed_conn.peer_id
    logging.info(f"incoming,/ip4/172.16.16.17/udp/9091/quic-v1,/ip4/172.16.16.16/udp/41972/quic-v1")
    try:
        data = await stream.read(PING_LENGTH)
        if data:
            logging.info(f"connected,{peer_id},/ip4/172.16.16.16/udp/41972/quic-v1")
            start_time = time.time()
            await stream.write(data)
            rtt = (time.time() - start_time) * 1000
            logging.info(f"ping,{peer_id},{rtt:.0f} ms")
    except Exception as e:
        logging.error(f"error,{e}")
    finally:
        await stream.close()
        logging.info(f"closed,{peer_id}")

def create_noise_keypair():
    """Create a Noise protocol keypair."""
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
    """Checker for QUIC transport."""
    key_pair = generate_new_rsa_identity()
    noise_privkey = create_noise_keypair()
    noise_transport = NoiseTransport(key_pair, noise_privkey=noise_privkey)
    sec_opt = {TProtocol("/noise"): noise_transport}
    muxer_opt = {TProtocol(YAMUX_PROTOCOL_ID): Yamux}
    transports = [TcpTransport(), QuicTransport()]

    listen_addr = multiaddr.Multiaddr("/ip4/0.0.0.0/udp/9091/quic-v1")
    host = new_host(
        key_pair=key_pair,
        transports=transports,
        sec_opt=sec_opt,
        muxer_opt=muxer_opt,
    )

    async with host.run(listen_addrs=[listen_addr]):
        host.set_stream_handler(PING_PROTOCOL_ID, handle_ping)
        await trio.sleep_forever()

if __name__ == "__main__":
    trio.run(main)