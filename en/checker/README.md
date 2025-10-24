# Universal Connectivity Workshop Checker Application

This application gets run as the remote peer in any lesson where the solution involves connecting to and communicating with a remote peer. It outputs single lines of comma separated values for easy parsing by the `check.py` scripts in each lession. Below is a list of the messages it produces and the fields that are included in each message.

## Messages

### Error

Whenever an operation results in an error, the checker application will print a line that looks like the followin:

```
error,Some error occurred
```

It begins with the `error` keyword followed by the cause of the message

### Incoming Connection

When the checker receives an incoming connection it outputs a line like the following:

```
incoming,/ip4/172.16.16.17/udp/9091/quic-v1,/ip4/172.16.16.16/udp/41972/quic-v1
```

It starts with the keyword `incoming` and is followed by multiaddr of the checker application and then the multiaddr of the peer connecting to the checker. Remember that the checker application is the remote peer from the perspective of the programmer completing the lesson, so from their perspective the first multiaddr is the remote peer and the second multiaddr is their own.

### Connection Established

When a connection is established, either incoming or outgoing, the checker application outputs a message like the following:

```
connected,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ip4/172.16.16.16/udp/41972/quic-v1
```

It consists of the `connected` keyword followed by the peer ID of the other peer and the multiaddr of the other peer. This will be the peer being written by the user completing the workshop.

### Connection Closed

When a connection to the checker is closed, it outputs a line like the following:

```
closed,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE
```

It is the `closed` keyword followed by the peer ID of that the connection was connected to.

### Identify Response

When the checker receives an identify response, it outputs a line like the following:

```
identify,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,/ipfs/id/1.0.0,universal-connectivity/0.1.0
```

It is the `identify` keyword followed by the sending peer's ID and their agent version string.

### Gossipsub Subscribe

When the checker receives a gossipsub subscribe message it outputs a line that looks like:

```
subscribe,12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE,universal-connectivity
```

It is the `subscribe` keyword followed by the subscribing peer's ID and the topic they are subscribing to.

### Gossipsub Message

When the checker receives a gossipsub message it outputs a line like the following:

```
msg,12D3KooWPWpaEjf8raRBZztEXMcSTXp8WBZwtcbhT7Xy1jyKCoN9,universal-connectivity,Hello from 12D3KooWC56YFhhdVtAuz6hGzhVwKu6SyYQ6qh4PMkTJawXVC8rE!
```

It is the `msg` keyword followed by the sending peer's ID, the topic, and the message.




