using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Nethermind.Libp2p;
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
    // TODO: Set up dependency injection with AddLibp2p
    // ServiceProvider serviceProvider = new ServiceCollection()
    //     .AddLibp2p()
    //     .AddLogging(...)
    //     .BuildServiceProvider();

    // TODO: Create an Identity with Ed25519 keys
    // Identity identity = new();

    // TODO: Get IPeerFactory and create ILocalPeer
    // IPeerFactory peerFactory = serviceProvider.GetRequiredService<IPeerFactory>();
    // await using ILocalPeer peer = peerFactory.Create(identity);

    // TODO: Print the PeerId
    // Console.WriteLine($"Local peer id: {peer.Identity.PeerId}");

    // TODO: Keep running until Ctrl+C
    // await Task.Delay(Timeout.Infinite, cts.Token);

    Console.WriteLine("Implementation incomplete - see lesson.md for instructions");
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
