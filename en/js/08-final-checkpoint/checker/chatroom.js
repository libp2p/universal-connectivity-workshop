import { toString as uint8ArrayToString } from 'uint8arrays/to-string'
import * as readline from 'readline'
import { createChatMessage, decodeMessage, isChatMessage, getChatMessageText } from './proto-messages.js'

const PUBSUB_DISCOVERY_TOPIC = 'universal-connectivity-workshop-js-peer-discovery'
export const CHAT_TOPIC = 'universal-connectivity'


class ChatMessage {
  constructor(nick, message) {
    this.nick = nick
    this.message = message
    this.timestamp = new Date()
  }

  toString() {
    return `[${this.nick}]: ${this.message}`
  }
}

/**
 * ChatRoom class handles all chat functionality including
 * subscribing to topics, publishing messages, and handling incoming messages
 */
export class ChatRoom {
  /**
   * Creates a new ChatRoom instance
   * @param {Libp2p} node - The libp2p node instance
   * @param {string} nickname - User's display name
   */
  constructor(node, nickname) {
    this.node = node
    this.nickname = nickname || this._generateNickname()
    this.messageHandlers = []
    this.running = false
  }

  /**
   * Factory method to join a chat room
   * @param {Libp2p} node - The libp2p node
   * @param {string} nickname - User's nickname
   * @returns {Promise<ChatRoom>} Initialized chat room
   */
  static async join(node, nickname) {
    const chatRoom = new ChatRoom(node, nickname)
    await chatRoom._subscribeToTopics()
    console.log(`[CHAT] Joined chat room as: ${chatRoom.nickname}`)
    return chatRoom
  }

  /**
   * Generate a nickname from the peer ID (last 8 characters)
   * @private
   */
  _generateNickname() {
    const peerId = this.node.peerId.toString()
    return peerId.slice(-8)
  }

  /**
   * Subscribe to chat and discovery topics
   * @private
   */

  async _subscribeToTopics() {
    try {
      await this.node.services.pubsub.subscribe(CHAT_TOPIC)
      console.log(`[CHAT] Subscribed to topic: ${CHAT_TOPIC}`)

      await this.node.services.pubsub.subscribe(PUBSUB_DISCOVERY_TOPIC)
      console.log(`[CHAT] Subscribed to discovery topic: ${PUBSUB_DISCOVERY_TOPIC}`)

      // Message handler
      this.node.services.pubsub.addEventListener('message', (evt) => {
        if (evt.detail.topic === CHAT_TOPIC) {
          this._handleChatMessage(evt.detail)
        } else if (evt.detail.topic === PUBSUB_DISCOVERY_TOPIC) {
          this._handleDiscoveryMessage(evt.detail)
        }
      })

      // Track subscription changes = critical for mesh awareness
      this.node.services.pubsub.addEventListener('subscription-change', (evt) => {
        const peerId = evt.detail.peerId.toString()
        const peerShort = peerId.slice(-8)

        // Log full subscription-change payload for debugging
        console.log(`[GOSSIPSUB] subscription-change from ${peerShort}:`, JSON.stringify(evt.detail.subscriptions))

        evt.detail.subscriptions.forEach(sub => {
          if (sub.topic === CHAT_TOPIC) {
            if (sub.subscribe) {
              console.log(`[GOSSIPSUB] ✓ Peer ${peerShort} subscribed to ${sub.topic}`)
            } else {
              console.log(`[GOSSIPSUB] ⚠️ Peer ${peerShort} unsubscribed from ${sub.topic}`)
            }

            // Always report current subscribers snapshot when subscription-change arrives
            const currentSubs = this.node.services.pubsub.getSubscribers(CHAT_TOPIC)
            console.log(`[GOSSIPSUB] Mesh snapshot: ${currentSubs.length} subscriber(s)`)
            currentSubs.forEach(p => console.log(`[GOSSIPSUB]   - ${p.toString().slice(-8)}`))
          }
        })
      })

      console.log('[CHAT] Message handlers registered successfully')
    } catch (error) {
      console.error('[CHAT] Error subscribing to topics:', error)
      throw error
    }
  }


  /**
   * Handle incoming chat messages
   * @private
   */
  _handleChatMessage(messageEvent) {
    try {
      const senderId = messageEvent.from.toString()
      
      // Skip messages from self
      if (senderId === this.node.peerId.toString()) {
        return
      }

      // Try to decode as Universal Connectivity message format
      const decodedMsg = decodeMessage(messageEvent.data)
      
      if (decodedMsg && isChatMessage(decodedMsg)) {
        const messageText = getChatMessageText(decodedMsg)
        
        // Generate nickname from sender's peer ID (last 8 chars)
        const senderNick = senderId.slice(-8)
        
        // Create ChatMessage object
        const chatMessage = new ChatMessage(senderNick, messageText)
        
        // Call registered handlers
        if (this.messageHandlers.length > 0) {
          this.messageHandlers.forEach(handler => handler(chatMessage))
        } else {
          console.log(chatMessage.toString())
        }
      } else {
        const messageText = uint8ArrayToString(messageEvent.data)
        const senderNick = senderId.slice(-8)
        const chatMessage = new ChatMessage(senderNick, messageText)
        
        if (this.messageHandlers.length > 0) {
          this.messageHandlers.forEach(handler => handler(chatMessage))
        } else {
          console.log(chatMessage.toString())
        }
      }
    } catch (error) {
      console.error('[CHAT] Error handling chat message:', error)
    }
  }

  /**
   * Handle incoming discovery messages
   * @private
   */
  _handleDiscoveryMessage(messageEvent) {
    try {
      const senderId = messageEvent.from.toString()
      
      // Skip messages from self
      if (senderId === this.node.peerId.toString()) {
        return
      }

      console.log(`[DISCOVERY] Peer discovered: ${senderId}`)
    } catch (error) {
      console.error('[CHAT] Error handling discovery message:', error)
    }
  }

  /**
   * Publish a message to the chat topic
   * @param {string} message - The message to send
   * @param {boolean} throwOnError - Whether to throw on error (default: false)
   */
  async publishMessage(message, throwOnError = false) {
    try {
      // Check mesh status BEFORE attempting to publish
      const peers = this.node.services.pubsub.getSubscribers(CHAT_TOPIC)
      
      if (peers.length === 0) {
        // No peers in mesh - don't even try to publish
        console.log('[CHAT] ⚠️  No peers in Gossipsub mesh yet')
        console.log('[CHAT] Message not sent: "' + message + '"')
        console.log('[CHAT] Tip: Wait for another peer to connect and subscribe')
        
        if (!throwOnError) {
          return
        } else {
          throw new Error('No peers subscribed to topic')
        }
      }
  
      console.log(`[CHAT] Publishing message to ${peers.length} peer(s) in mesh`)
      
      // Encode message using Universal Connectivity message format
      const messageBytes = createChatMessage(message)
      
      // Publish the message
      await this.node.services.pubsub.publish(CHAT_TOPIC, messageBytes)
      console.log(`[CHAT] ✅ Message sent: "${message}"`)
      
    } catch (error) {
      // Enhanced error handling
      if (error.message && error.message.includes('NoPeersSubscribedToTopic')) {
        console.log('[CHAT] ⚠️  Gossipsub error: No peers subscribed to topic')
        console.log('[CHAT] This means the mesh hasn\'t formed yet or peers disconnected')
        
        if (!throwOnError) {
          return
        }
      } else {
        console.error('[CHAT] ❌ Error publishing message:', error.message)
      }
      
      if (throwOnError) {
        throw error
      }
    }
  }

  /**
   * Register a message handler callback
   * @param {Function} handler - Callback function to handle messages
   */
  onMessage(handler) {
    this.messageHandlers.push(handler)
  }

  /**
   * Start interactive chat mode (reads from stdin)
   */
  async startInteractive() {
    this.running = true
    
    console.log('\n' + '='.repeat(60))
    console.log('  Welcome to Universal Connectivity Chat!')
    console.log('='.repeat(60))
    console.log(`  Your nickname: ${this.nickname}`)
    console.log(`  Peer ID: ${this.node.peerId.toString()}`)
    console.log(`  Type messages and press Enter to send`)
    console.log(`  Press Ctrl+C to exit`)
    console.log('='.repeat(60) + '\n')

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: `[${this.nickname}]> `
    })

    rl.prompt()

    rl.on('line', async (line) => {
      const message = line.trim()
      if (message) {
        try {
          await this.publishMessage(message)
        } catch (error) {
          console.error('Failed to send message:', error)
        }
      }
      rl.prompt()
    })

    rl.on('close', () => {
      console.log('\n[CHAT] Exiting chat...')
      this.running = false
      process.exit(0)
    })

    try {
      await this.publishMessage(`${this.nickname} has joined the chat!`)
    } catch (error) {
    }
  }

  /**
   * Get connected peer IDs
   * @returns {Set<string>} Set of peer ID strings
   */
  getConnectedPeers() {
    const peers = this.node.services.pubsub.getSubscribers(CHAT_TOPIC)
    return new Set(peers.map(p => p.toString()))
  }

  /**
   * Get count of connected peers
   * @returns {number} Number of connected peers
   */
  getPeerCount() {
    return this.node.services.pubsub.getSubscribers(CHAT_TOPIC).length
  }

  // send an intro message
  async sendIntroduction() {
    const intro = `Hello! I'm ${this.nickname} - ready to chat!`
    await this.publishMessage(intro, false)
  }
}
