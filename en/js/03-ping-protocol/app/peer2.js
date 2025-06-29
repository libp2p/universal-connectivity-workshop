import process from 'node:process';
import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { identify } from '@libp2p/identify';
import { ping } from '@libp2p/ping';
import { multiaddr } from '@multiformats/multiaddr';
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

  await node.start();
  console.log('libp2p has started');
  node.getMultiaddrs().forEach((addr) => {
    console.log('listening on:', addr.toString());
  });

  if (process.argv.length >= 3) {
    const remote = process.argv[2];
    try {
      const ma = multiaddr(remote);
      console.log(`pinging remote peer at ${remote}`);
      const latency = await node.services.ping.ping(ma);
      console.log(`pinged ${remote} in ${latency}ms`);
    } catch (err) {
      console.error('Failed to ping remote peer:', err);
    }
  } else {
    console.log('no remote peer address given, skipping ping');
  }
};

main().catch(console.error);
