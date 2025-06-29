import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';

const main = async () => {
  const node = await createLibp2p({
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()]
  });

  await node.start();
  console.log('PeerId:', node.peerId.toString());
  console.log('Listening on:');
  node.getMultiaddrs().forEach((addr) => {
    console.log(addr.toString());
  });
};

main().catch(console.error);
