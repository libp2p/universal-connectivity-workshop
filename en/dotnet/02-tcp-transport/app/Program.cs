using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Nethermind.Libp2p;
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
    // TODO: Parse REMOTE_PEERS environment variable
    // List<Multiaddress> remoteAddrs = [];
    // if (Environment.GetEnvironmentVariable("REMOTE_PEERS") is string remotePeers)
    // {
    //     remoteAddrs = remotePeers
    //         .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
    //         .Select(addr => Multiaddress.Decode(addr))
    //         .ToList();
    // }

    // TODO: Set up DI (same as Lesson 1)
    // ServiceProvider serviceProvider = ...

    // TODO: Create peer (same as Lesson 1)
    // Identity identity = new();
    // IPeerFactory peerFactory = serviceProvider.GetRequiredService<IPeerFactory>();
    // await using ILocalPeer peer = peerFactory.Create(identity);

    // Console.WriteLine($"Local peer id: {peer.Identity.PeerId}");

    // TODO: Handle incoming connections
    // peer.OnConnected += async session =>
    // {
    //     Console.WriteLine($"Peer connected: {session.RemoteAddress}");
    // };

    // TODO: Start listening on TCP
    // await peer.StartListenAsync(["/ip4/0.0.0.0/tcp/0"], cts.Token);
    // Console.WriteLine($"Listening on: {string.Join(", ", peer.ListenAddresses)}");

    // TODO: Dial remote peers
    // foreach (var addr in remoteAddrs)
    // {
    //     try
    //     {
    //         Console.WriteLine($"Connecting to: {addr}");
    //         ISession session = await peer.DialAsync(addr, cts.Token);
    //         Console.WriteLine($"Connected to remote peer");
    //     }
    //     catch (Exception ex)
    //     {
    //         Console.WriteLine($"Failed to connect: {ex.Message}");
    //     }
    // }

    // TODO: Keep running
    // await Task.Delay(Timeout.Infinite, cts.Token);

    Console.WriteLine("Implementation incomplete - see lesson.md");
    return 1;
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
