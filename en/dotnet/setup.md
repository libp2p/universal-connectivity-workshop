# .NET libp2p Universal Connectivity Workshop Setup

Welcome to the .NET libp2p Universal Connectivity Workshop! This guide will help you set up your development environment.

## Prerequisites

- **.NET 8 SDK** or higher ([download here](https://dotnet.microsoft.com/download))
- **Docker Desktop** (for containerized lessons)
- **Git** (for version control)
- Basic knowledge of C# and async/await
- Familiarity with networking concepts (optional but helpful)
- IDE of your choice (Visual Studio, VS Code, Rider)

## Environment Setup

### Step 1: Install .NET SDK

**Check if .NET is already installed:**
```bash
dotnet --version
```

You should see version 8.0.0 or higher.

**If not installed:**
- Visit: https://dotnet.microsoft.com/download
- Download .NET 8 SDK (LTS)
- Run the installer
- Verify installation: `dotnet --version`

### Step 2: Create a Workshop Directory

Create a new directory for your workshop projects:

```bash
mkdir dotnet-libp2p-workshop
cd dotnet-libp2p-workshop
```

### Step 3: Verify NuGet Access

Ensure you can access NuGet packages:

```bash
dotnet new console -n test-project
cd test-project
dotnet add package Nethermind.Libp2p --prerelease
dotnet restore
```

If successful, you're ready to go! Clean up:
```bash
cd ..
rm -rf test-project
```

### Step 4: Install Docker Desktop (Optional but Recommended)

Docker is used for running lessons in a consistent environment.

**Check if Docker is installed:**
```bash
docker --version
```

**If not installed:**
- **Windows/Mac**: Download from https://www.docker.com/products/docker-desktop
- **Linux**: Follow instructions at https://docs.docker.com/engine/install/

**Start Docker Desktop** and ensure it's running.

### Step 5: Verify Your Setup

Run the dependency checker:

```bash
cd en/dotnet
python3 deps.py
```

You should see all green checkmarks (✓) for required dependencies.

## Workshop Structure

Each lesson in this workshop follows this structure:

```
01-identity-and-host/
├── app/                    # Your application code goes here
│   ├── Program.cs          # Main C# application file
│   ├── App.csproj          # Project file with dependencies
│   └── Dockerfile          # For containerized testing
├── lesson.md               # Lesson instructions and explanations
├── lesson.yaml             # Lesson metadata
├── check.py                # Automated checker for your solution
├── docker-compose.yaml     # Docker configuration
└── stdout.log              # Output log (created when you run)
```

## Quick Start (Local Development)

For each lesson, you can develop and test locally without Docker:

```bash
cd en/dotnet/01-identity-and-host/app

# Restore NuGet packages
dotnet restore

# Build the project
dotnet build

# Run the application
dotnet run
```

## Quick Start (Docker)

To run lessons in Docker (recommended for workshop environment):

```bash
# Set up environment
export PROJECT_ROOT=/path/to/universal-connectivity-workshop
export LESSON_PATH=en/dotnet/01-identity-and-host

# Create Docker network (one-time setup)
docker network create workshop-net

# Build and run
cd $LESSON_PATH
docker-compose up --build

# Check your solution
python3 check.py
```

## Getting Help

During the workshop:

1. **Read the lesson.md file carefully** - it contains detailed instructions and explanations
2. **Use the hint blocks** - they provide additional context for tricky parts
3. **Check your solution** - run `python3 check.py` to validate your implementation
4. **Review the complete example** - each lesson.md includes a full solution
5. **Ask for help** - don't hesitate to ask the instructor or fellow participants

## Workshop Objectives

By the end of this workshop, you will:

- ✅ Understand peer-to-peer networking fundamentals
- ✅ Master libp2p concepts (identity, transports, protocols)
- ✅ Create libp2p nodes with cryptographic identities using .NET
- ✅ Implement transport layers (TCP) and connection management
- ✅ Work with multiaddresses for self-describing network addresses
- ✅ Use built-in protocols (Ping, Identify)
- ✅ Understand security layers in libp2p
- ✅ Implement pub/sub messaging with GossipSub
- ✅ Build peer discovery mechanisms
- ✅ Write production-quality C# async code
- ✅ Use .NET dependency injection patterns
- ✅ Work with dotnet-libp2p in real applications

## .NET-Specific Features

This workshop teaches idiomatic .NET patterns:

- **Dependency Injection**: Using `ServiceCollection` and `AddLibp2p()`
- **Async/Await**: All network operations are async
- **IAsyncDisposable**: Proper resource cleanup with `await using`
- **CancellationToken**: Graceful shutdown handling
- **Modern C#**: Nullable reference types, pattern matching, collection expressions

## Next Steps

Once your environment is set up:

1. Navigate to the first lesson: `cd en/dotnet/01-identity-and-host/`
2. Read the `lesson.md` file
3. Start coding in the `app/Program.cs` file
4. Test your solution: `dotnet run` (local) or `docker-compose up` (Docker)
5. Validate: `python3 check.py`

Let's begin building the future of peer-to-peer applications with .NET! 🚀

## Troubleshooting

### Common Issues

#### .NET SDK Not Found
```bash
dotnet --version
# If command not found, reinstall .NET SDK
```

Make sure the SDK (not just runtime) is installed. Check:
```bash
dotnet --list-sdks
```

#### NuGet Package Not Found
```bash
# Make sure to use --prerelease flag
dotnet add package Nethermind.Libp2p --prerelease

# Clear NuGet cache if needed
dotnet nuget locals all --clear
```

#### Docker Not Running
```bash
# Start Docker Desktop manually
# On Windows: Start from Start Menu
# On Mac: Start from Applications
# On Linux: sudo systemctl start docker
```

#### Permission Denied (Linux)
```bash
# Add your user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

#### Build Errors in Lessons
```bash
# Clean and rebuild
dotnet clean
dotnet restore
dotnet build
```

#### Connection Refused When Connecting to Peers
- Ensure `REMOTE_PEERS` environment variable is set correctly
- Check that the remote peer is actually running
- Verify Docker network exists: `docker network ls | grep workshop-net`
- Check multiaddress format: `/ip4/172.16.16.17/tcp/9092`

#### Type or Namespace Not Found
- Make sure all packages are restored: `dotnet restore`
- Check that you're using the correct `using` statements
- Verify package versions in `App.csproj`
- Try cleaning: `dotnet clean && dotnet restore`

#### Async/Await Errors
- Always use `await` with async methods
- Use `await using` for `IAsyncDisposable` types like `ILocalPeer`
- Pass `CancellationToken` to async operations
- Don't block on async code with `.Result` or `.Wait()`

### Getting More Help

- **dotnet-libp2p GitHub**: https://github.com/NethermindEth/dotnet-libp2p
- **dotnet-libp2p Docs**: https://github.com/NethermindEth/dotnet-libp2p/tree/main/docs
- **libp2p Specifications**: https://github.com/libp2p/specs
- **libp2p Documentation**: https://docs.libp2p.io
- **.NET Documentation**: https://docs.microsoft.com/dotnet

### Need More Help?

If you're stuck:
1. Check the lesson.md file for the complete solution
2. Review the troubleshooting section above
3. Ask your instructor or workshop facilitator
4. Check GitHub issues for dotnet-libp2p
5. Join the libp2p community: https://discuss.libp2p.io

Happy coding! 👨‍💻
