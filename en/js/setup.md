## 0. **Prerequisites**

### Tool
- Node (≥ 18 LTS )            
- npm (≥ 9 )               
- TypeScript (optional) (≥ 5.4 )              


## 1. **Project Setup**
- create a new directory for the project:

```
mkdir uc-workshop
cd uc-workshop
```

## 2. **Install Dependencies**
- Then, initialize your project and install the required dependencies:

```bash
npm init -y
npm install libp2p @libp2p/tcp @libp2p/ping @chainsafe/libp2p-noise @chainsafe/libp2p-yamux @libp2p/ping
```

### For TypeScript support (optional):

```bash
npm install -D typescript @types/node
npx tsc --init
```