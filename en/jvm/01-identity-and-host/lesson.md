# Lesson 1: Identity and Basic Host

Welcome to your first step into peer-to-peer networking with jvm-libp2p! In this lesson, you'll create your very first libp2p peer and understand the fundamental concept of peer identity.

## Learning Objectives

By the end of this lesson, you will:
- Understand what a PeerId is and why it's important
- Create a cryptographic keypair for peer identification
- Initialize a basic libp2p Host using Kotlin DSL
- Run your first jvm-libp2p application

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

## Your Task

Create a Kotlin application that:
1. Generates an Ed25519 keypair for peer identity
2. Creates a basic libp2p Host using the Kotlin DSL
3. Prints the peer's ID when the application starts
4. Keeps the host running until the application exits

## Step-by-Step Instructions

### Step 1: Set Up Your Build Configuration

Create `app/build.gradle.kts` with the project dependencies:

```kotlin
plugins {
    kotlin("jvm") version "1.9.24"
    application
}

repositories {
    mavenCentral()
    maven("https://jitpack.io")
}

dependencies {
    // jvm-libp2p core library
    implementation("io.libp2p:jvm-libp2p:1.1.1-RELEASE")

    // Logging
    implementation("org.slf4j:slf4j-api:2.0.9")
    implementation("org.apache.logging.log4j:log4j-slf4j2-impl:2.20.0")
    implementation("org.apache.logging.log4j:log4j-core:2.20.0")
}

application {
    mainClass.set("MainKt")
}

tasks.withType<Jar> {
    manifest {
        attributes["Main-Class"] = "MainKt"
    }
    // Create fat JAR with all dependencies
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
    from(configurations.runtimeClasspath.get().map { if (it.isDirectory) it else zipTree(it) })
}
```

**What's happening here?**

- `kotlin("jvm")`: Applies the Kotlin plugin for JVM targets
- `maven("https://jitpack.io")`: jvm-libp2p is published on JitPack
- `io.libp2p:jvm-libp2p`: The main libp2p library for JVM
- `slf4j` and `log4j`: Logging framework (jvm-libp2p uses SLF4J)
- `application.mainClass`: Specifies the entry point
- `Jar` task configuration: Creates a fat JAR with all dependencies included

**Why JitPack?** jvm-libp2p is published to JitPack, which builds JVM libraries directly from GitHub. The first build might take longer as JitPack compiles the library.

### Step 2: Set Up Your Main Package

Create `app/src/main/kotlin/Main.kt` with the basic structure and imports:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import java.util.concurrent.TimeUnit

fun main() {
    println("Starting Universal Connectivity Application...")

    // Your code will go here
}
```

**What's happening here?**

- `io.libp2p.core.Host`: The main Host interface
- `io.libp2p.core.crypto.KeyType`: Enum for key types (Ed25519, RSA, etc.)
- `io.libp2p.core.dsl.host`: Kotlin DSL function for host creation
- `java.util.concurrent.TimeUnit`: For controlling execution time

**Why Kotlin DSL?** jvm-libp2p provides a fluent Kotlin DSL that makes configuration intuitive and type-safe. It's more concise than the Java builder pattern.

### Step 3: Create the libp2p Host

Now create the host using the Kotlin DSL:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import java.util.concurrent.TimeUnit

fun main() {
    println("Starting Universal Connectivity Application...")

    // Create a libp2p host with Ed25519 identity
    val node: Host = host {
        identity {
            random(KeyType.ED25519)
        }
    }

    // Print the peer ID
    println("Local peer id: ${node.peerId}")

    // Your next code will go here
}
```

**What's happening here?**

- `host { ... }`: Kotlin DSL function that builds and returns a `Host`
- `identity { random(KeyType.ED25519) }`: Generates a random Ed25519 keypair
  - `KeyType.ED25519`: Specifies Ed25519 elliptic curve cryptography
  - `random()`: Generates a new keypair each time the app runs
- `node.peerId`: Gets the PeerId derived from the public key

**Why Ed25519?** It's a modern elliptic curve algorithm that provides:
- Fast key generation and signing
- Small key sizes (32 bytes)
- Strong security guarantees
- Deterministic signatures

### Step 4: Start the Host and Keep it Running

Add code to start the host and keep it running:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import java.util.concurrent.TimeUnit

fun main() {
    println("Starting Universal Connectivity Application...")

    // Create a libp2p host
    val node: Host = host {
        identity {
            random(KeyType.ED25519)
        }
    }

    // Start the host (async operation)
    node.start().get()

    // Print the peer ID
    println("Local peer id: ${node.peerId}")

    // Keep the application running
    Thread.sleep(TimeUnit.SECONDS.toMillis(10))

    // Shut down gracefully
    node.stop().get()
    println("Shutting down...")
}
```

**What's happening here?**

- `node.start()`: Starts the host asynchronously
  - Returns a `CompletableFuture<Void>`
  - `.get()` blocks until the start operation completes
- `Thread.sleep(...)`: Keeps the application running for 10 seconds
  - In a real application, you'd use signal handling or wait for user input
- `node.stop()`: Stops the host asynchronously
  - `.get()` blocks until shutdown completes
  - Ensures clean resource cleanup

**Why CompletableFuture?** jvm-libp2p is async-first using Java's `CompletableFuture` API:
- Non-blocking by default
- Composable with other async operations
- Allows proper error handling
- `.get()` is used here for simplicity, but you can use callbacks for non-blocking code

**Why Thread.sleep?** In this lesson, we use a simple sleep to keep the application alive. In production:
- Use signal handlers (like `Runtime.getRuntime().addShutdownHook()`)
- Wait for user input
- Use a proper event loop or framework

### Step 5: Add Logging Configuration

Create `app/src/main/resources/log4j2.xml` to configure logging:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Configuration status="INFO">
    <Appenders>
        <Console name="Console" target="SYSTEM_OUT">
            <PatternLayout pattern="%d{HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n"/>
        </Console>
    </Appenders>
    <Loggers>
        <Root level="info">
            <AppenderRef ref="Console"/>
        </Root>
        <!-- Reduce verbosity of libp2p internals -->
        <Logger name="io.libp2p" level="warn"/>
        <Logger name="io.netty" level="warn"/>
    </Loggers>
</Configuration>
```

**What's happening here?**

- `Console` appender: Outputs logs to standard output
- `PatternLayout`: Formats log messages with timestamp, thread, level, and message
- `Root level="info"`: Sets default log level to INFO
- `Logger name="io.libp2p" level="warn"`: Reduces libp2p internal logging to warnings only

**Why configure logging?** jvm-libp2p uses SLF4J for logging. Without configuration, you'll see warnings about missing logging implementation. This gives you clean output focused on your application.

### Step 6: Understanding the Complete Flow

Here's how your program executes:

1. **Startup**: Prints startup message
2. **Host Creation**: Creates host with Ed25519 identity using Kotlin DSL
3. **Host Start**: Starts the host asynchronously (initializes network stack)
4. **PeerId Display**: Shows the peer's unique identifier
5. **Wait**: Sleeps for 10 seconds (keeping host alive)
6. **Shutdown**:
   - Stops the host cleanly
   - Prints shutdown message

This pattern ensures proper resource initialization and cleanup.

## Testing Your Implementation

### Running Your Code

1. Navigate to the lesson directory:
   ```bash
   cd en/jvm/01-identity-and-host
   ```

2. Build your application:
   ```bash
   cd app
   ./gradlew build  # Use gradlew.bat on Windows
   ```

3. Run your application:
   ```bash
   ./gradlew run
   ```

4. You should see output similar to:
   ```
   Starting Universal Connectivity Application...
   Local peer id: 12D3KooWJ7GFEPLWbpxPyWkfPvFCbR7BwNb6Nwvn8Nrw9J8JZLQP
   Shutting down...
   ```

### Automated Checking

If you're using the workshop tool, press the `c` key to check your solution.

For manual testing:
```bash
cd ..  # Back to lesson directory
python check.py
```

## Success Criteria

Your implementation should:
- ✅ Display the startup message
- ✅ Generate a valid Ed25519 keypair
- ✅ Create a libp2p host successfully
- ✅ Display a valid peer ID (starts with "12D3KooW")
- ✅ Run for the specified duration
- ✅ Shut down gracefully

## Hints

<details>
<summary>Hint: Gradle Build Issues</summary>

If Gradle fails to download dependencies:

```bash
# Clear Gradle cache
rm -rf ~/.gradle/caches

# Rebuild with dependency refresh
./gradlew build --refresh-dependencies
```

If JitPack times out, try again - it builds on-demand:
```bash
./gradlew build --refresh-dependencies
```
</details>

<details>
<summary>Hint: PeerId Format</summary>

Valid libp2p PeerIds (using Ed25519):
- Start with "12D3KooW" (base58btc multibase prefix + Ed25519 indicator)
- Are 52-55 characters long
- Only contain base58 characters (no 0, O, I, l)

Example: `12D3KooWJ7GFEPLWbpxPyWkfPvFCbR7BwNb6Nwvn8Nrw9J8JZLQP`
</details>

<details>
<summary>Hint: Understanding CompletableFuture</summary>

jvm-libp2p uses `CompletableFuture` for async operations:

```kotlin
// Blocking wait for completion
val future = node.start()
future.get()  // Blocks until complete

// Non-blocking callback
node.start().whenComplete { _, error ->
    if (error != null) {
        println("Error starting host: ${error.message}")
    } else {
        println("Host started successfully")
    }
}

// Chaining operations
node.start()
    .thenRun { println("Host started") }
    .thenCompose { node.stop() }
    .thenRun { println("Host stopped") }
```

For this lesson, we use `.get()` for simplicity, but async callbacks are more idiomatic.
</details>

<details>
<summary>Hint: Kotlin DSL vs Java Builder</summary>

jvm-libp2p supports both Kotlin DSL and Java builder patterns:

**Kotlin DSL (recommended for Kotlin):**
```kotlin
val host = host {
    identity {
        random(KeyType.ED25519)
    }
}
```

**Java Builder:**
```java
Host host = new HostBuilder()
    .identity(IdentityFactory.random(KeyType.ED25519))
    .build();
```

Both produce the same result, use whichever matches your language.
</details>

## Hint - Complete Solution

Here's the complete working solution:

**Main.kt:**
```kotlin
import io.libp2p.core.Host
import io.libp2p.core.crypto.KeyType
import io.libp2p.core.dsl.host
import java.util.concurrent.TimeUnit

fun main() {
    println("Starting Universal Connectivity Application...")

    // Create a libp2p host with Ed25519 identity
    val node: Host = host {
        identity {
            random(KeyType.ED25519)
        }
    }

    // Start the host
    node.start().get()

    // Print the peer ID
    println("Local peer id: ${node.peerId}")

    // Keep the application running
    Thread.sleep(TimeUnit.SECONDS.toMillis(10))

    // Shut down gracefully
    node.stop().get()
    println("Shutting down...")
}
```

**build.gradle.kts:**
```kotlin
plugins {
    kotlin("jvm") version "1.9.24"
    application
}

repositories {
    mavenCentral()
    maven("https://jitpack.io")
}

dependencies {
    implementation("io.libp2p:jvm-libp2p:1.1.1-RELEASE")
    implementation("org.slf4j:slf4j-api:2.0.9")
    implementation("org.apache.logging.log4j:log4j-slf4j2-impl:2.20.0")
    implementation("org.apache.logging.log4j:log4j-core:2.20.0")
}

application {
    mainClass.set("MainKt")
}

tasks.withType<Jar> {
    manifest {
        attributes["Main-Class"] = "MainKt"
    }
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
    from(configurations.runtimeClasspath.get().map { if (it.isDirectory) it else zipTree(it) })
}
```

**log4j2.xml:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Configuration status="INFO">
    <Appenders>
        <Console name="Console" target="SYSTEM_OUT">
            <PatternLayout pattern="%d{HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n"/>
        </Console>
    </Appenders>
    <Loggers>
        <Root level="info">
            <AppenderRef ref="Console"/>
        </Root>
        <Logger name="io.libp2p" level="warn"/>
        <Logger name="io.netty" level="warn"/>
    </Loggers>
</Configuration>
```

## What You've Learned

Congratulations! You've created your first jvm-libp2p node with:

- **Cryptographic Identity**: Your node has a unique, verifiable identity using Ed25519
- **PeerId**: A compact identifier that other peers can use to reference your node
- **Basic Host**: The foundation that will handle all network operations
- **Kotlin DSL**: Fluent, type-safe configuration using Kotlin's domain-specific language
- **Async Operations**: Using CompletableFuture for non-blocking operations
- **Resource Management**: Proper startup and shutdown procedures

## Key Concepts

### Peer Identity
Every libp2p node has a cryptographic identity based on public-key cryptography. The PeerId is derived from the public key and serves as the node's unique identifier in the network.

### Host Interface
The `io.libp2p.core.Host` interface is the core of jvm-libp2p. It provides:
- Identity management
- Network connection handling
- Protocol stream management
- Address listening and dialing

### Kotlin DSL
The Kotlin DSL provides:
- Type-safe builders
- Concise syntax
- IDE autocomplete support
- Compile-time validation
- Clear, readable configuration

### CompletableFuture Pattern
Java's `CompletableFuture` is used throughout jvm-libp2p for:
- Asynchronous operations
- Non-blocking I/O
- Error handling
- Operation composition
- Callback registration

## What's Next?

In the next lesson, you'll learn about:
- **Multiaddresses**: How peers specify where they can be reached
- **Transport Layers**: Adding TCP networking to your host
- **Listening**: Making your peer discoverable on the network
- **Dialing**: Connecting to other peers

Your identity is just the beginning - now let's make your peer reachable on the network!

## Additional Resources

- [jvm-libp2p GitHub repository](https://github.com/libp2p/jvm-libp2p)
- [PeerId specification](https://github.com/libp2p/specs/blob/master/peer-ids/peer-ids.md)
- [libp2p connectivity](https://docs.libp2p.io/concepts/fundamentals/peers/)
- [Kotlin coroutines and async](https://kotlinlang.org/docs/coroutines-overview.html)
- [CompletableFuture guide](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CompletableFuture.html)
