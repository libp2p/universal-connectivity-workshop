import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';

const main = async () => {
  try {
    const node = await createLibp2p({
      addresses: {
        listen: ['/ip4/0.0.0.0/tcp/0']
      },
      transports: [tcp()],
      connectionEncrypters: [noise()],
      streamMuxers: [yamux()]
    });

    node.addEventListener('peer:connect', (evt) => {
      console.log('Connected to:', evt.detail.remotePeer.toString());
    });

    node.addEventListener('peer:disconnect', (evt) => {
      console.log('Disconnected from:', evt.detail.remotePeer.toString());
    });

    node.addEventListener('error', (evt) => {
      console.error('Node error:', evt.detail);
    });

    await node.start();
    console.log('Listening on:');
    node.getMultiaddrs().forEach((addr) => {
      console.log(addr.toString());
    });
  } catch (err) {
    console.error('Failed to start libp2p node:', err);
    process.exit(1);
  }
};

main();
