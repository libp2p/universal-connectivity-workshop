# Lesson 2: TCP Transport

In this lesson, you'll add TCP transport to your libp2p peer, enabling it to listen for incoming connections and dial (connect to) other peers over the network.

## Learning Objectives

By the end of this lesson, you will:
- Understand multiaddresses (Multiaddr) for network addressing
- Configure your peer to listen on TCP
- Parse remote peer addresses from environment variables
- Dial (connect to) remote peers
- Handle connection events

## Background: Transports in libp2p

A **transport** in libp2p is a way to establish connections between peers. TCP is the most basic and widely-supported transport.

### Multiaddresses

libp2p uses **multiaddresses** (Multiaddr) to represent network addresses in a self-describing format:

```
/ip4/127.0.0.1/tcp/4001/p2p/12D3KooW...
 │    │         │   │    │   └─ PeerId
 │    │         │   │    └─ Protocol
 │    │         │   └─ Port
 │    │         └─ Protocol
 │    └─ IP Address
 └─ Protocol
```

Examples:
- `/ip4/0.0.0.0/tcp/0` - Listen on all IPv4 interfaces, random port
- `/ip4/172.16.16.17/tcp/9092` - Connect to specific IP:port
- `/ip6/::1/tcp/4001` - IPv6 localhost

### Listen vs Dial

- **Listen**: Your peer accepts incoming connections (server role)
- **Dial**: Your peer initiates outbound connections (client role)

In P2P networks, every peer does both!

## Your Task

Extend your Lesson 1 code to:
1. Start listening on TCP (port 0 = random port)
2. Read `REMOTE_PEERS` environment variable
3. Parse comma-separated multiaddresses
4. Dial each remote peer
5. Print connection status messages

Expected output:
```
Starting Universal Connectivity Application...
Local peer id: 12D3KooW...
Listening on: /ip4/127.0.0.1/tcp/54321
Listening on: /ip4/172.16.16.16/tcp/54321
Connecting to: /ip4/172.16.16.17/tcp/9092
Connected to remote peer
```

## Step-by-Step Instructions

### Step 1: Import Multiaddress Package

Add to your using statements:

```csharp
using Multiformats.Address;
```

This package provides the `Multiaddress` type for parsing network addresses.

### Step 2: Start Listening on TCP

After creating your peer, call `StartListenAsync`:

```csharp
await peer.StartListenAsync(["/ip4/0.0.0.0/tcp/0"], cts.Token);
Console.WriteLine($"Listening on: {string.Join(", ", peer.ListenAddresses)}");
```

**Explanation:**
- `"/ip4/0.0.0.0/tcp/0"` means listen on all IPv4 interfaces, random port
- `peer.ListenAddresses` shows the actual addresses after binding
- Multiple addresses may be shown (e.g., loopback + network interface)

### Step 3: Parse Remote Peers from Environment

Read the `REMOTE_PEERS` environment variable and parse comma-separated multiaddresses:

```csharp
List<Multiaddress> remoteAddrs = [];
if (Environment.GetEnvironmentVariable("REMOTE_PEERS") is string remotePeers)
{
    remoteAddrs = remotePeers
        .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
        .Select(addr => Multiaddress.Decode(addr))
        .ToList();
}
```

**What's happening:**
- Split by comma
- Remove empty entries and trim whitespace
- Decode each string into a `Multiaddress` object
- Store in a list for dialing

### Step 4: Handle Incoming Connections

Register a callback for when remote peers connect to you:

```csharp
peer.OnConnected += async session =>
{
    Console.WriteLine($"Peer connected: {session.RemoteAddress}");
};
```

### Step 5: Dial Remote Peers

Loop through the parsed addresses and dial each one:

```csharp
foreach (var addr in remoteAddrs)
{
    try
    {
        Console.WriteLine($"Connecting to: {addr}");
        ISession session = await peer.DialAsync(addr, cts.Token);
        Console.WriteLine($"Connected to remote peer");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Failed to connect: {ex.Message}");
    }
}
```

**Important:**
- `DialAsync` returns an `ISession` representing the connection
- Catch exceptions - connections may fail (peer offline, network issues, etc.)
- The connection stays open until you dispose the session or peer

### Step 6: Keep Running

After dialing, keep the application running so connections stay alive:

```csharp
await Task.Delay(Timeout.Infinite, cts.Token);
```

## Complete Example

```csharp
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Nethermind.Libp2p.Core;
using Multiformats.Address;

Console.WriteLine("Starting Universal Connectivity Application...");

using CancellationTokenSource cts = new();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    cts.Cancel();
};

try
{
    // Parse remote peers
    List<Multiaddress> remoteAddrs = [];
    if (Environment.GetEnvironmentVariable("REMOTE_PEERS") is string remotePeers)
    {
        remoteAddrs = remotePeers
            .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Select(addr => Multiaddress.Decode(addr))
            .ToList();
    }

    // Set up DI
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

    // Create peer
    Identity identity = new();
    IPeerFactory peerFactory = serviceProvider.GetRequiredService<IPeerFactory>();
    await using ILocalPeer peer = peerFactory.Create(identity);

    Console.WriteLine($"Local peer id: {peer.Identity.PeerId}");

    // Handle incoming connections
    peer.OnConnected += async session =>
    {
        Console.WriteLine($"Peer connected: {session.RemoteAddress}");
    };

    // Start listening
    await peer.StartListenAsync(["/ip4/0.0.0.0/tcp/0"], cts.Token);
    Console.WriteLine($"Listening on: {string.Join(", ", peer.ListenAddresses)}");

    // Dial remote peers
    foreach (var addr in remoteAddrs)
    {
        try
        {
            Console.WriteLine($"Connecting to: {addr}");
            ISession session = await peer.DialAsync(addr, cts.Token);
            Console.WriteLine($"Connected to remote peer");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to connect: {ex.Message}");
        }
    }

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

### Local Testing

Run your application:
```bash
dotnet run
```

### Testing with Another Peer

In one terminal:
```bash
dotnet run
```
Note the listening address (e.g., `/ip4/127.0.0.1/tcp/54321`)

In another terminal:
```bash
REMOTE_PEERS="/ip4/127.0.0.1/tcp/54321" dotnet run
```

You should see both peers connect to each other!

## Hints and Troubleshooting

### Why does my peer have multiple listen addresses?
Your peer may bind to multiple network interfaces (loopback 127.0.0.1, local network 192.168.x.x, etc.). All are valid.

### Connection refused errors
Make sure:
- The remote peer is actually running
- The port number matches
- No firewall is blocking the connection

### Port 0 vs specific port
- `/tcp/0` asks the OS to assign a random available port (good for testing)
- `/tcp/4001` binds to a specific port (good for servers)

### Multiaddress parsing errors
Check that your `REMOTE_PEERS` string is properly formatted:
```
/ip4/172.16.16.17/tcp/9092
```
Not:
```
172.16.16.17:9092  ❌ (plain IP:port won't work)
```

## Understanding the Concepts

### Why Multiaddresses?

Traditional addressing:
- `192.168.1.1:8080` - What protocol? TCP? UDP? HTTP?
- Ambiguous, needs out-of-band knowledge

Multiaddresses:
- `/ip4/192.168.1.1/tcp/8080` - Self-describing, composable
- Can include protocol stack: `/ip4/.../tcp/.../ws/p2p/...`

### Peer Discovery

In this lesson, you manually specify `REMOTE_PEERS`. In production systems:
- **Bootstrap nodes**: Well-known peers you connect to first
- **DHT**: Discover peers through a distributed hash table
- **mDNS**: Discover peers on local network
- **Rendezvous**: Meet at a common topic

We'll explore discovery in later lessons!

### Connection Lifecycle

1. **Dial**: Initiate TCP connection
2. **Multistream Negotiation**: Agree on protocols
3. **Session Created**: `ISession` object represents the connection
4. **Data Exchange**: Protocols can now send/receive data
5. **Close**: Either side can close, or network failure

## Success Criteria

Your application must:
- ✅ Print the local PeerId
- ✅ Start listening on TCP
- ✅ Print listen addresses
- ✅ Parse `REMOTE_PEERS` environment variable
- ✅ Successfully dial remote peers (if provided)
- ✅ Print "Connected to remote peer" on success

## Next Steps

Congratulations! Your peer can now:
- Listen for incoming TCP connections
- Dial other peers
- Maintain multiple concurrent connections

In the next lesson, we'll add security (encryption) and multiplexing so you can run multiple protocols over each connection.

## Hints

### Hint 1: Parsing REMOTE_PEERS
```csharp
List<Multiaddress> remoteAddrs = [];
if (Environment.GetEnvironmentVariable("REMOTE_PEERS") is string remotePeers)
{
    remoteAddrs = remotePeers
        .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
        .Select(addr => Multiaddress.Decode(addr))
        .ToList();
}
```

### Hint 2: Starting to Listen
```csharp
await peer.StartListenAsync(["/ip4/0.0.0.0/tcp/0"], cts.Token);
Console.WriteLine($"Listening on: {string.Join(", ", peer.ListenAddresses)}");
```

### Hint 3: Dialing Peers
```csharp
foreach (var addr in remoteAddrs)
{
    try
    {
        Console.WriteLine($"Connecting to: {addr}");
        ISession session = await peer.DialAsync(addr, cts.Token);
        Console.WriteLine($"Connected to remote peer");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Failed to connect: {ex.Message}");
    }
}
```

## Hint - Complete Solution

See lesson.md for the complete working solution in the "Complete Example" section above.
