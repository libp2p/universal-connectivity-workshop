# Lesson 1: Identity and Host

Welcome to the first lesson in the .NET libp2p workshop! In this lesson, you'll create your first peer-to-peer node using Nethermind's dotnet-libp2p implementation.

## Learning Objectives

By the end of this lesson, you will:
- Understand what a PeerId is and why it's important
- Use .NET dependency injection with libp2p
- Create an `ILocalPeer` with cryptographic identity
- Print your peer's unique identifier
- Handle graceful shutdown with cancellation tokens

## Background: Peer Identity in libp2p

In traditional client-server applications, servers have known addresses (like domain names), but clients are anonymous. In peer-to-peer networks, every participant is both a client and a server, so each peer needs a stable, verifiable identity.

libp2p uses **cryptographic keypairs** for peer identity:
- **Private Key**: Kept secret, used to sign messages and prove identity
- **Public Key**: Shared with others, used to verify signatures
- **PeerId**: A hash of the public key, used as a short identifier

This design ensures that:
1. Peers can prove they control their identity (via signatures)
2. Others can verify that proof (via public key cryptography)
3. Identities are compact and easy to share (via PeerId hash)

### PeerId Format

PeerIds come in two formats:
- **CIDv0**: Starts with "Qm", 46 characters, base58-encoded (e.g., `QmYyQSo1c1Ym7orWxLYvCrM2EmxFTANf8wXmmE7DWjhx5N`)
- **CIDv1**: Starts with "12D3KooW" for Ed25519 keys, variable length (e.g., `12D3KooWD3eckifWpRn9wQpMG9R9hX3sD158z7EqHWmweQAJU5SA`)

## Your Task

Create a C# application that:
1. Sets up dependency injection with `AddLibp2p`
2. Generates an Ed25519 cryptographic identity
3. Creates an `ILocalPeer` instance
4. Prints the PeerId to the console
5. Runs until interrupted (Ctrl+C)
6. Shuts down gracefully

The output should look like:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooWD3eckifWpRn9wQpMG9R9hX3sD158z7EqHWmweQAJU5SA
```

## Step-by-Step Instructions

### Step 0: Understanding the .NET Project Structure

Your workspace contains:
- `Program.cs` - Your main application code (you'll edit this)
- `App.csproj` - Project file with dependencies (already configured)
- `Dockerfile` - Container build instructions (for workshop infrastructure)

### Step 1: Review Dependencies

The `App.csproj` file already includes the necessary packages:

```xml
<PackageReference Include="Nethermind.Libp2p" Version="1.0.0-preview.*" />
<PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="8.0.0" />
<PackageReference Include="Microsoft.Extensions.Logging.Console" Version="8.0.0" />
```

- **Nethermind.Libp2p**: The core libp2p library for .NET
- **Microsoft.Extensions.DependencyInjection**: .NET's IoC container
- **Microsoft.Extensions.Logging.Console**: Console logging support

### Step 2: Set Up Dependency Injection

dotnet-libp2p uses .NET's idiomatic dependency injection pattern. Start by creating a `ServiceCollection` and adding libp2p services:

```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Nethermind.Libp2p.Core;

ServiceProvider serviceProvider = new ServiceCollection()
    .AddLibp2p()  // Registers all libp2p services
    .AddLogging(builder => builder
        .SetMinimumLevel(LogLevel.Information)
        .AddSimpleConsole(options =>
        {
            options.SingleLine = true;
            options.TimestampFormat = "[HH:mm:ss] ";
        }))
    .BuildServiceProvider();
```

**What's happening:**
- `AddLibp2p()` registers the peer factory and all protocol implementations
- `AddLogging()` configures console output for debugging
- `BuildServiceProvider()` finalizes the dependency container

### Step 3: Create a Cryptographic Identity

Create an `Identity` object with a random Ed25519 keypair:

```csharp
using Nethermind.Libp2p.Core;

Identity identity = new();  // Generates a random Ed25519 keypair
```

**Key Types Supported:**
- Ed25519 (default, recommended)
- Secp256k1 (Ethereum-style keys)
- ECDSA
- RSA

For this workshop, we use Ed25519 because it's fast, secure, and widely supported.

### Step 4: Create the Local Peer

Get the `IPeerFactory` from the service provider and create your peer:

```csharp
IPeerFactory peerFactory = serviceProvider.GetRequiredService<IPeerFactory>();
await using ILocalPeer peer = peerFactory.Create(identity);
```

**Important Notes:**
- `ILocalPeer` implements `IAsyncDisposable`, so use `await using` for proper cleanup
- The peer is not listening yet - it just has an identity

### Step 5: Print the PeerId

Extract and print the PeerId:

```csharp
Console.WriteLine($"Local peer id: {peer.Identity.PeerId}");
```

The `peer.Address` is a `Multiaddress` that includes the PeerId. We use `GetPeerId()` to extract just the peer identifier.

### Step 6: Keep Running Until Interrupted

The application should run until the user presses Ctrl+C:

```csharp
using CancellationTokenSource cts = new();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;  // Prevent immediate termination
    cts.Cancel();     // Signal graceful shutdown
};

await Task.Delay(Timeout.Infinite, cts.Token);
```

This pattern:
- Creates a `CancellationTokenSource` for shutdown signaling
- Hooks the Ctrl+C event
- Waits indefinitely until cancellation is requested
- Allows the `await using` to properly dispose the peer

### Step 7: Handle Errors Gracefully

Wrap everything in proper error handling:

```csharp
try
{
    // Your code here
    return 0;
}
catch (OperationCanceledException)
{
    Console.WriteLine("Shutting down...");
    return 0;
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
    return 1;
}
```

## Complete Example

Here's what your `Program.cs` should look like:

```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Nethermind.Libp2p.Core;

Console.WriteLine("Starting Universal Connectivity Application...");

// Set up graceful shutdown
using CancellationTokenSource cts = new();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    cts.Cancel();
};

try
{
    // Set up dependency injection
    ServiceProvider serviceProvider = new ServiceCollection()
        .AddLibp2p()
        .AddLogging(builder => builder
            .SetMinimumLevel(LogLevel.Information)
            .AddSimpleConsole(options =>
            {
                options.SingleLine = true;
                options.TimestampFormat = "[HH:mm:ss] ";
            }))
        .BuildServiceProvider();

    // Create identity
    Identity identity = new();

    // Create peer
    IPeerFactory peerFactory = serviceProvider.GetRequiredService<IPeerFactory>();
    await using ILocalPeer peer = peerFactory.Create(identity);

    // Print PeerId
    Console.WriteLine($"Local peer id: {peer.Identity.PeerId}");

    // Keep running
    await Task.Delay(Timeout.Infinite, cts.Token);
}
catch (OperationCanceledException)
{
    Console.WriteLine("Shutting down...");
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
    return 1;
}

return 0;
```

## Testing Your Implementation

Run your application:

```bash
dotnet run
```

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
```

Press Ctrl+C to stop:
```
Shutting down...
```

## Hints and Troubleshooting

### My PeerId looks different each time
✅ **This is correct!** A new identity is generated each time you run the program. In later lessons, we'll show how to persist identities.

### I get a NuGet restore error
Try:
```bash
dotnet restore
dotnet build
```

### I get "package Nethermind.Libp2p not found"
Make sure you're using `--prerelease`:
```bash
dotnet add package Nethermind.Libp2p --prerelease
```

### What's the difference between CIDv0 and CIDv1 PeerIds?
- **CIDv0** (legacy): Always starts with "Qm", uses SHA-256, 46 characters
- **CIDv1** (modern): Starts with "12D3KooW" for Ed25519, supports multiple hash algorithms

Both formats are valid. dotnet-libp2p may use either depending on the key type.

## Understanding the Concepts

### Why Dependency Injection?

dotnet-libp2p uses .NET's IoC pattern because:
1. **Testability**: Easy to mock dependencies in unit tests
2. **Extensibility**: Plugins can register additional protocols
3. **Configuration**: Centralized service configuration
4. **Lifetime Management**: Framework handles object lifecycles

This is idiomatic .NET - if you're building production applications, this pattern integrates seamlessly with ASP.NET Core, Worker Services, etc.

### Why Async/Await?

All libp2p operations are asynchronous because:
1. Network I/O is naturally async (waiting for connections, data)
2. Multiple peers can be handled concurrently
3. Non-blocking operations improve throughput
4. Cancellation tokens enable graceful shutdown

`IAsyncDisposable` ensures network resources are properly released even in error scenarios.

### Why Ed25519 Keys?

Ed25519 is the default because:
- **Fast**: Sign/verify operations are very quick
- **Small**: 32-byte keys, 64-byte signatures
- **Secure**: Twist-secure elliptic curve
- **Deterministic**: No randomness needed for signing
- **Widely Supported**: All libp2p implementations support it

## Next Steps

Congratulations! You've created your first libp2p peer. You now have:
- A unique cryptographic identity (PeerId)
- An `ILocalPeer` that can be extended with transports and protocols
- A solid foundation for peer-to-peer networking

In the next lesson, we'll add TCP transport so your peer can actually connect to other peers over the network.

## Success Criteria

To complete this lesson, your application must:
- ✅ Print "Starting Universal Connectivity Application..."
- ✅ Print a valid PeerId (CIDv0 or CIDv1 format)
- ✅ Run without crashing
- ✅ Respond to Ctrl+C gracefully

The checker script will validate your output automatically.

## Hints

### Hint 1: ServiceCollection Setup
If you're stuck on the dependency injection setup:
```csharp
ServiceProvider serviceProvider = new ServiceCollection()
    .AddLibp2p()
    .AddLogging(builder => builder
        .SetMinimumLevel(LogLevel.Information)
        .AddSimpleConsole(options =>
        {
            options.SingleLine = true;
            options.TimestampFormat = "[HH:mm:ss] ";
        }))
    .BuildServiceProvider();
```

### Hint 2: Creating the Peer
Remember to use `await using` for proper cleanup:
```csharp
Identity identity = new();
IPeerFactory peerFactory = serviceProvider.GetRequiredService<IPeerFactory>();
await using ILocalPeer peer = peerFactory.Create(identity);
```

### Hint 3: Extracting PeerId
```csharp
Console.WriteLine($"Local peer id: {peer.Identity.PeerId}");
```

## Hint - Complete Solution

Here's the complete working solution:

```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Nethermind.Libp2p.Core;

Console.WriteLine("Starting Universal Connectivity Application...");

using CancellationTokenSource cts = new();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    cts.Cancel();
};

try
{
    ServiceProvider serviceProvider = new ServiceCollection()
        .AddLibp2p()
        .AddLogging(builder => builder
            .SetMinimumLevel(LogLevel.Information)
            .AddSimpleConsole(options =>
            {
                options.SingleLine = true;
                options.TimestampFormat = "[HH:mm:ss] ";
            }))
        .BuildServiceProvider();

    Identity identity = new();
    IPeerFactory peerFactory = serviceProvider.GetRequiredService<IPeerFactory>();
    await using ILocalPeer peer = peerFactory.Create(identity);

    Console.WriteLine($"Local peer id: {peer.Identity.PeerId}");

    await Task.Delay(Timeout.Infinite, cts.Token);
}
catch (OperationCanceledException)
{
    Console.WriteLine("Shutting down...");
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
    return 1;
}

return 0;
```

## What's Next?

Great job! You've created your first libp2p node with .NET! In the next lesson, you'll learn how to add TCP transport so your node can actually connect to other peers over the network.

Key concepts you've learned:
- **Peer Identity**: Every libp2p node has a cryptographic identity  
- **Keypairs**: Ed25519 keypairs provide both identity and security
- **PeerId**: A compact identifier derived from the public key
- **.NET DI**: Using `AddLibp2p()` with ServiceCollection
- **Async/Await**: Proper async patterns with CancellationToken
- **ILocalPeer**: The main entry point for libp2p in .NET

Next up: Adding TCP transport so peers can actually communicate!
