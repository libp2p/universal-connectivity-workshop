#!/usr/bin/env node

import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";

const execAsync = promisify(exec);

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForFile(filepath, timeout = 30000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    try {
      if (fs.existsSync(filepath) && fs.statSync(filepath).size > 0) {
        return true;
      }
    } catch (err) {
      // File might not exist yet
    }
    await sleep(1000);
  }
  return false;
}

async function getRelayMultiaddr() {
  let attempts = 0;
  const maxAttempts = 30;

  while (attempts < maxAttempts) {
    try {
      if (fs.existsSync("/app/relay.log")) {
        const relayLog = fs.readFileSync("/app/relay.log", "utf8");
        const peerIdMatch = relayLog.match(/PeerId: ([A-Za-z0-9]+)/);
        if (peerIdMatch) {
          const relayPeerId = peerIdMatch[1];
          return `/ip4/172.16.16.16/tcp/4001/p2p/${relayPeerId}`;
        }
      }
    } catch (err) {
    }
    await sleep(2000);
    attempts++;
  }

  throw new Error("Could not get relay multiaddr");
}

async function getListenerRelayAddr() {
  let attempts = 0;
  const maxAttempts = 30;

  while (attempts < maxAttempts) {
    try {
      if (fs.existsSync("/app/listener.log")) {
        const listenerLog = fs.readFileSync("/app/listener.log", "utf8");
        const relayAddrMatch = listenerLog.match(
          /Advertising with a relay address of ([^\r\n]+)/
        );
        if (relayAddrMatch) {
          return relayAddrMatch[1].trim();
        }
      }
    } catch (err) {
    }
    await sleep(2000);
    attempts++;
  }

  throw new Error("Could not get listener relay address");
}

function validateRelayLog(logContent) {
  const checks = [
    /PeerId: ([A-Za-z0-9]+)/,
    /Node started with id ([A-Za-z0-9]+)/,
    /tcp\/4001/,
  ];
  return checks.every((pattern) => pattern.test(logContent));
}

function validateListenerLog(logContent) {
  const checks = [
    /Node started with id ([A-Za-z0-9]+)/,
    /Connected to the relay ([A-Za-z0-9]+)/,
    /Advertising with a relay address of (\/ip4\/.*\/p2p-circuit\/p2p\/[A-Za-z0-9]+)/,
  ];
  return checks.every((pattern) => pattern.test(logContent));
}

function validateDialerLog(logContent) {
  const checks = [
    /Node started with id ([A-Za-z0-9]+)/,
    /Connected to the listener node via (\/ip4\/.*\/p2p-circuit\/p2p\/[A-Za-z0-9]+)/,
    /DIAL SUCCESS/,
  ];
  return checks.every((pattern) => pattern.test(logContent));
}

async function main() {
  try {
    // Get relay multiaddr
    const relayMultiaddr = await getRelayMultiaddr();
    // Give the relay a moment to finish binding before the listener dials
    await sleep(2000);
    // Start listener and capture its output
    const listenerProcess = execAsync(
      `node listener.js "${relayMultiaddr}" > /app/listener.log 2>&1`
    );
    listenerProcess.catch(() => {});
    await sleep(8000);
    // Get listener relay address and start dialer
    const listenerRelayAddr = await getListenerRelayAddr();
    // Log the essential circuit relay address
    console.log(`Advertising with a relay address of ${listenerRelayAddr}`);
    // Start dialer and capture its output
    await execAsync(
      `node dialer.js "${listenerRelayAddr}" > /app/dialer.log 2>&1`
    );
    // Validate all logs
    const logFiles = ["/app/relay.log", "/app/listener.log", "/app/dialer.log"];
    for (const file of logFiles) {
      if (!(await waitForFile(file))) {
        throw new Error(`Missing ${file}`);
      }
    }

    const relayLog = fs.readFileSync("/app/relay.log", "utf8");
    const listenerLog = fs.readFileSync("/app/listener.log", "utf8");
    const dialerLog = fs.readFileSync("/app/dialer.log", "utf8");

    const relayValid = validateRelayLog(relayLog);
    const listenerValid = validateListenerLog(listenerLog);
    const dialerValid = validateDialerLog(dialerLog);

    if (relayValid && listenerValid && dialerValid) {
      console.log("circuit_relay,success,complete_flow");
      fs.writeFileSync(
        "/app/checker.log",
        "✅ Circuit Relay v2 validation passed"
      );
      process.exit(0);
    } else {
      console.log("circuit_relay,failed,validation");
      fs.writeFileSync(
        "/app/checker.log",
        "❌ Circuit Relay v2 validation failed"
      );
      process.exit(1);
    }
  } catch (error) {
    console.log(`circuit_relay,error,${error.message}`);
    fs.writeFileSync("/app/checker.log", `❌ Error: ${error.message}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("❌ Unhandled error:", err);
  process.exit(1);
});
