# cpp-libp2p Universal Connectivity Workshop Setup

Welcome to the cpp-libp2p Universal Connectivity Workshop! This guide will help you set up your development environment for building peer-to-peer applications with C++.

## Prerequisites

- C++20 compatible compiler (GCC 10+, Clang 12+, or AppleClang 13+)
- CMake 3.16 or higher
- vcpkg package manager (recommended) or Hunter
- Basic knowledge of C++ and CMake
- Familiarity with networking concepts (optional but helpful)
- Text editor or IDE of your choice (VSCode with C++ extensions recommended)

## Environment Setup

### Step 1: Install Build Tools

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    libssl-dev \
    curl \
    zip \
    unzip \
    tar
```

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install cmake openssl pkg-config
```

**Windows:**
```powershell
# Install Visual Studio 2022 with C++ workload
# Or use winget:
winget install Microsoft.VisualStudio.2022.Community
winget install Kitware.CMake
winget install Git.Git
```

### Step 2: Build and Install cpp-libp2p

cpp-libp2p uses **Hunter** as its package manager, which automatically downloads and builds all dependencies during the cmake configuration step.

```bash
# Clone cpp-libp2p
git clone https://github.com/libp2p/cpp-libp2p.git
cd cpp-libp2p

# Create build directory
mkdir build && cd build

# Configure and build (Hunter will download dependencies - this takes 15-20 min first time)
cmake .. -DCMAKE_BUILD_TYPE=Release \
    -DTESTING=OFF \
    -DEXAMPLES=OFF \
    -DCMAKE_INSTALL_PREFIX=$HOME/libp2p

# Build (use -j to parallelize)
cmake --build . -j$(nproc)

# Install to $HOME/libp2p
cmake --install .
```

**Note**: The first build takes 15-20 minutes as Hunter downloads and compiles all dependencies (Boost, OpenSSL, protobuf, etc.). Subsequent builds are much faster.

### Step 3: Set Environment Variables

Add these to your `.bashrc` or `.zshrc`:

```bash
# Find the Hunter install directory
export HUNTER_INSTALL_DIR=$(find ~/.hunter -type d -name "Install" | head -1)
export LIBP2P_INSTALL_DIR=$HOME/libp2p

# For cmake to find the libraries
export CMAKE_PREFIX_PATH="$LIBP2P_INSTALL_DIR:$HUNTER_INSTALL_DIR:$CMAKE_PREFIX_PATH"
```

### Step 5: Verify Your Setup

Run the dependency checker:

```bash
python deps.py
```

You should see all green checkmarks (v) for required dependencies.

## Workshop Structure

Each lesson in this workshop follows this structure:

```
01-identity-and-swarm/
├── app/                    # Your application code goes here
│   ├── main.cpp           # Main application file
│   ├── CMakeLists.txt     # CMake build configuration
│   └── Dockerfile         # For containerized testing
├── lesson.md              # Lesson instructions and explanations
├── lesson.yaml            # Lesson metadata
├── check.py               # Automated checker for your solution
├── docker-compose.yaml    # Docker configuration
└── stdout.log             # Output log (created when you run your code)
```

## Building Lessons

### Option 1: Using Docker (Recommended)

Docker provides a consistent build environment with all dependencies:

```bash
cd en/cpp/01-identity-and-swarm
docker compose up --build
```

**Note**: First build takes 15-20 minutes. Subsequent builds are faster.

### Option 2: Building Locally

After installing cpp-libp2p (Step 2 above):

```bash
# Set paths (or add to your shell profile)
export LIBP2P_INSTALL_DIR=$HOME/libp2p
export HUNTER_INSTALL_DIR=$(find ~/.hunter -type d -name "Install" | head -1)

# Build the lesson
cd en/cpp/01-identity-and-swarm/app
mkdir -p build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$LIBP2P_INSTALL_DIR;$HUNTER_INSTALL_DIR"
cmake --build build

# Run and capture output
timeout 5 ./build/lesson > ../stdout.log 2>&1
cat ../stdout.log

# Validate
python3 ../check.py
```

## Getting Help

During the workshop:

1. **Read the lesson.md file carefully** - it contains detailed instructions and explanations
2. **Use the hint blocks** - they provide additional context for tricky parts
3. **Check your solution** - run `python check.py` to validate your implementation
4. **Ask for help** - don't hesitate to ask the instructor or fellow participants

## Workshop Objectives

By the end of this workshop, you will:

- Understand peer-to-peer networking fundamentals
- Know how to create libp2p nodes with cryptographic identities using C++
- Implement transport layers and connection management
- Build custom protocols for peer communication
- Work with the Kademlia DHT for peer discovery
- Use Gossipsub for pub-sub messaging
- Connect to the Universal Connectivity network

## C++ Specific Concepts

This workshop will also cover:

- **Boost.Asio**: Async I/O operations for networking
- **Boost.DI**: Dependency injection for flexible component configuration
- **Modern C++20**: Using concepts, ranges, and coroutines where applicable
- **Smart Pointers**: Memory management with `std::shared_ptr` and `std::unique_ptr`
- **Error Handling**: Using `outcome::result` for robust error handling

## Next Steps

Once your environment is set up:

1. Navigate to the first lesson: `01-identity-and-swarm/`
2. Read the `lesson.md` file
3. Start coding in the `app/` directory
4. Test your solution with `python check.py`

Let's begin building the future of peer-to-peer applications with C++!

## Troubleshooting

### Common Issues

**CMake can't find libp2p:**
```bash
# Make sure CMAKE_PREFIX_PATH includes both install directories
export CMAKE_PREFIX_PATH="$HOME/libp2p:$(find ~/.hunter -type d -name Install | head -1)"
cmake .. -DCMAKE_PREFIX_PATH="$CMAKE_PREFIX_PATH"
```

**Compiler version too old:**
```bash
# Check your compiler version
g++ --version   # Should be 10+ for GCC
clang++ --version  # Should be 12+ for Clang

# On Ubuntu, install newer GCC
sudo apt-get install g++-12
export CXX=g++-12
```

**Hunter download fails (network issues):**
```bash
# Hunter caches downloads in ~/.hunter
# Clear cache and retry
rm -rf ~/.hunter
cd cpp-libp2p/build
cmake ..  # Re-run cmake to re-download
```

**OpenSSL issues on macOS:**
```bash
# Link OpenSSL from Homebrew
export OPENSSL_ROOT_DIR=$(brew --prefix openssl)
```

**Docker build fails:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache
```

**ARM64 Mac issues:**
```bash
# cpp-libp2p's boringssl has ARM64 issues
# Use Docker with linux/amd64 platform (handled automatically in our Dockerfile)
docker compose up --build
```

Need more help? Ask your instructor!
