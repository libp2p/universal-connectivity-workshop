0. **Prerequisites**

| Tool       | Recommended version |
| ---------- | ------------------- | 
| Node       | ≥ 18 LTS            | 
| npm        | ≥ 9                 |
| TypeScript | ≥ 5.4               |


1. **Install Dependencies**
First, initialize your project and add the required dependencies:

```bash
npm init -y
npm install libp2p @libp2p/tcp @libp2p/ping @chainsafe/libp2p-noise @chainsafe/libp2p-yamux @libp2p/ping
```

For TypeScript support (optional):

```bash
npm install -D typescript @types/node
npx tsc --init
```