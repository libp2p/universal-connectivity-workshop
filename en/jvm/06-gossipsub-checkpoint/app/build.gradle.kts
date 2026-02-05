plugins {
    kotlin("jvm") version "1.9.24"
    application
}

repositories {
    mavenCentral()
    maven("https://dl.cloudsmith.io/public/libp2p/jvm-libp2p/maven/")
    maven("https://jitpack.io")
    maven("https://hyperledger.jfrog.io/artifactory/besu-maven/")
    maven("https://artifacts.consensys.net/public/maven/maven/")
}

dependencies {
    // jvm-libp2p core library (includes gossip protocol)
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
    // Exclude signature files from signed JARs to avoid SecurityException
    exclude("META-INF/*.SF", "META-INF/*.DSA", "META-INF/*.RSA")
}
