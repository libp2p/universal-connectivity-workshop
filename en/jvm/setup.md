# jvm-libp2p Universal Connectivity Workshop Setup

Welcome to the jvm-libp2p Universal Connectivity Workshop! This guide will help you set up your development environment.

## Prerequisites

- JDK 11 or higher (recommended: JDK 21+)
- Gradle 8.0 or higher (can use wrapper)
- Basic knowledge of Kotlin or Java programming
- Familiarity with Gradle and async/coroutines (helpful)
- Understanding of networking concepts (optional but helpful)
- Text editor or IDE of your choice (IntelliJ IDEA, VS Code with Kotlin, Eclipse, etc.)

## Environment Setup

### Step 1: Install JDK

If you haven't installed a JDK yet, download and install it from:
- [Eclipse Temurin](https://adoptium.net/) (recommended)
- [Oracle JDK](https://www.oracle.com/java/technologies/downloads/)
- [Amazon Corretto](https://aws.amazon.com/corretto/)

Verify your Java installation:

```bash
java -version  # Should be 11 or higher
```

### Step 2: Install Gradle (Optional)

While we'll use the Gradle wrapper in this workshop, you can optionally install Gradle globally:

Download from [https://gradle.org/install/](https://gradle.org/install/)

Verify Gradle installation:

```bash
gradle --version  # Should be 8.0 or higher
```

### Step 3: Create a Workshop Directory

Create a new directory for your workshop projects:

```bash
mkdir jvm-libp2p-workshop
cd jvm-libp2p-workshop
```

### Step 4: Initialize Gradle Project

Each lesson will have its own Gradle project, but let's verify Gradle works:

```bash
# Create a test directory
mkdir test-project
cd test-project

# Initialize a Kotlin Gradle project
gradle init --type kotlin-application --dsl kotlin
```

Follow the prompts (select defaults or your preferences).

### Step 5: Test jvm-libp2p Import

Let's verify we can import jvm-libp2p. Create a simple test project:

```bash
cd ..
mkdir libp2p-test
cd libp2p-test
```

Create `build.gradle.kts`:

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
}

application {
    mainClass.set("MainKt")
}
```

Create `src/main/kotlin/Main.kt`:

```kotlin
import io.libp2p.core.Host
import io.libp2p.core.dsl.host

fun main() {
    println("jvm-libp2p version check...")
    println("✓ Setup verified successfully!")
}
```

Build and run:

```bash
gradle build
gradle run
```

You should see:
```
jvm-libp2p version check...
✓ Setup verified successfully!
```

Clean up the test:

```bash
cd ..
rm -rf libp2p-test test-project
```

### Step 6: Run Dependency Checker

Run the dependency checker to ensure all required tools are available:

```bash
python deps.py
```

You should see all green checkmarks (✓) for required dependencies.

## Workshop Structure

Each lesson in this workshop follows this structure:

```
01-identity-and-host/
├── app/                           # Your application code goes here
│   ├── src/
│   │   └── main/
│   │       └── kotlin/
│   │           └── Main.kt       # Main application file
│   ├── build.gradle.kts          # Gradle build configuration
│   └── Dockerfile                # For containerized testing
├── lesson.md                      # Lesson instructions and explanations
├── lesson.yaml                    # Lesson metadata
├── check.py                       # Automated checker for your solution
├── docker-compose.yaml            # Docker configuration
└── stdout.log                     # Output log (created when you run your code)
```

## jvm-libp2p Architecture Overview

jvm-libp2p is structured around several core components:

### Host
The **Host** is the main entry point for libp2p functionality. It manages:
- Peer identity (PeerId derived from cryptographic keys)
- Network connections
- Protocol handlers
- Stream multiplexing

### Builder Pattern
jvm-libp2p uses a fluent Kotlin DSL for configuration:

```kotlin
val host = host {
    identity {
        random()
    }
    transports {
        +::TcpTransport
    }
    secureChannels {
        +::NoiseXXSecureChannel
    }
    muxers {
        +StreamMuxerProtocol.Mplex
    }
    protocols {
        +Ping()
    }
    network {
        listen("/ip4/0.0.0.0/tcp/0")
    }
}
```

### Transports
Transport layers handle low-level network communication:
- **TCP**: Traditional reliable transport
- **QUIC**: Modern UDP-based transport with built-in encryption (beta)
- **WebSocket**: Browser-compatible transport (beta)

### Security
Security protocols encrypt connections:
- **Noise**: Modern cryptographic handshake protocol (production)
- **TLS**: Traditional TLS 1.3 support (beta)

### Multiplexing
Stream multiplexers allow multiple logical streams over a single connection:
- **Mplex**: Primary multiplexer (production)
- **Yamux**: Alternative multiplexer (beta)

### Protocols
Application-level protocols built on top of streams:
- **Ping**: Connectivity testing and latency measurement
- **Identify**: Peer information exchange
- **Kad-DHT**: Distributed hash table for peer discovery (planned)
- **GossipSub**: Pub/sub messaging system (production)

## Getting Help

During the workshop:

1. **Read the lesson.md file carefully** - it contains detailed instructions and explanations
2. **Use the hint blocks** - they provide additional context for tricky parts
3. **Check your solution** - run `python check.py` to validate your implementation
4. **Consult the documentation** - [jvm-libp2p GitHub](https://github.com/libp2p/jvm-libp2p)
5. **Ask for help** - don't hesitate to ask the instructor or fellow participants

## Workshop Objectives

By the end of this workshop, you will:

- Understand peer-to-peer networking fundamentals
- Know how to create libp2p hosts with cryptographic identities
- Implement transport layers and connection management
- Build custom protocols for peer communication
- Use built-in protocols (ping, identify, GossipSub, Kademlia)
- Connect to the Universal Connectivity network
- Handle NAT traversal and connectivity challenges

## Kotlin/Java-Specific Best Practices

Throughout this workshop, we'll follow JVM best practices:

### Error Handling with CompletableFuture
jvm-libp2p is async-first using CompletableFuture:
```kotlin
val host = host { ... }
host.start().get()  // Blocking wait

// Or with proper error handling:
host.start().whenComplete { _, error ->
    if (error != null) {
        println("Error starting host: ${error.message}")
    }
}
```

### Resource Cleanup
Always close resources properly:
```kotlin
val host = host { ... }
try {
    host.start().get()
    // ... do work ...
} finally {
    host.stop().get()
}
```

### Structured Logging
Use SLF4J for logging:
```kotlin
import org.slf4j.LoggerFactory

val logger = LoggerFactory.getLogger("UniversalConnectivity")
logger.info("Connected to peer {}", peerId)
```

### Kotlin DSL vs Java Builder
Both styles are supported:

**Kotlin DSL:**
```kotlin
val host = host {
    identity { random() }
}
```

**Java Builder:**
```java
Host host = new HostBuilder()
    .protocol(new Ping())
    .listen("/ip4/127.0.0.1/tcp/0")
    .build();
```

## Next Steps

Once your environment is set up:

1. Navigate to the first lesson: `01-identity-and-host/`
2. Read the `lesson.md` file
3. Start coding in the `app/src/main/kotlin/` directory
4. Test your solution with `python check.py`

Let's begin building the future of peer-to-peer applications with JVM! 🚀

## Troubleshooting

### Common Issues

**JDK version too old:**
```bash
java -version  # Should be 11+
```
If your version is too old, download the latest from [Adoptium](https://adoptium.net/).

**Gradle build issues:**
```bash
# Use the Gradle wrapper instead of global Gradle
./gradlew build  # Linux/Mac
gradlew.bat build  # Windows
```

**Dependency download failures:**
```bash
# Clear Gradle cache and retry
rm -rf ~/.gradle/caches
./gradlew build --refresh-dependencies
```

**jitpack.io timeout:**
If you see timeouts when downloading from jitpack.io:
```bash
# Try again - jitpack builds on first request
./gradlew build --refresh-dependencies
```

**Build errors:**
```bash
# Ensure dependencies are downloaded
./gradlew build --refresh-dependencies

# Clean build
./gradlew clean build
```

**Port already in use:**
If you see "bind: address already in use" errors, another process is using the port. Either:
- Stop the other process
- Change the listen port in your code
- Use `lsof -i :PORT` (Mac/Linux) or `netstat -ano | findstr :PORT` (Windows) to find the process

**OutOfMemoryError:**
Increase Gradle JVM memory in `gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m
```

Need more help? Ask your instructor! 👨‍🏫

## Additional Resources

- **jvm-libp2p GitHub repository**: [https://github.com/libp2p/jvm-libp2p](https://github.com/libp2p/jvm-libp2p)
- **Official libp2p documentation**: [https://docs.libp2p.io/](https://docs.libp2p.io/)
- **jvm-libp2p examples**: [https://github.com/libp2p/jvm-libp2p/tree/develop/examples](https://github.com/libp2p/jvm-libp2p/tree/develop/examples)
- **libp2p specifications**: [https://github.com/libp2p/specs](https://github.com/libp2p/specs)
- **Kotlin documentation**: [https://kotlinlang.org/docs/](https://kotlinlang.org/docs/)
