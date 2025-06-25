import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { identify } from '@libp2p/identify';
import { ping } from '@libp2p/ping';
import {directMessage} from './direct-message.js'

const main = async () => {
  const node = await createLibp2p({
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      identify: identify(),
      ping: ping(),
      directMessage: directMessage(),
    }
  });

  node.addEventListener('error', (evt) => {
    console.error('Node error:', evt.detail);
  });

  await node.start();
  console.log('libp2p has started');
  node.getMultiaddrs().forEach((addr) => {
    console.log('listening on:', addr.toString());
  });
};

main().catch(console.error);
