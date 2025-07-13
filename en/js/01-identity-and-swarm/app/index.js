import { createLibp2p } from 'libp2p';
import { tcp } from '@libp2p/tcp';
import { noise } from '@chainsafe/libp2p-noise';
import { yamux } from '@chainsafe/libp2p-yamux';
import { ping } from '@libp2p/ping';

const main = async () => {
  console.log('Starting Universal Connectivity Application...');
  
  // Create the libp2p node
  const node = await createLibp2p({
    addresses: {
      listen: ['/ip4/0.0.0.0/tcp/0']
    },
    transports: [tcp()],
    connectionEncrypters: [noise()],
    streamMuxers: [yamux()],
    services: {
      ping: ping({
        protocolPrefix: 'ipfs',
      })
    }
  });

  // Start the node
  await node.start();

  // Print identity and network information
  console.log('Local peer id:', node.peerId.toString());
  console.log('Listening on:');
  node.getMultiaddrs().forEach((addr) => {
    console.log(' ', addr.toString());
  });

  // Handle network events
  node.addEventListener('peer:connect', (evt) => {
    console.log('Connected to:', evt.detail.toString());
  });

  node.addEventListener('peer:disconnect', (evt) => {
    console.log('Disconnected from:', evt.detail.toString());
  });

  console.log('Node is running. Press Ctrl+C to stop.');

  // Graceful shutdown
  const cleanup = async () => {
    console.log('\nShutting down...');
    await node.stop();
    process.exit(0);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);

  // Keep the process alive
  process.stdin.resume();
};

main().catch((error) => {
  console.error('Error:', error);
  process.exit(1);
});