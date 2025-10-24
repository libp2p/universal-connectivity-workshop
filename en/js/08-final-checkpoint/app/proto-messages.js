/**
 * Universal Connectivity Protocol Messages
 * 
 * This module defines the message format for Universal Connectivity,
 * matching the protobuf definitions used in other implementations (like Rust).
 * 
 * Message hierarchy:
 * - UniversalConnectivityMessage (wrapper)
 *   - ChatMessage (text chat)
 *   - FileMessage (file transfer)
 *   - BrowserPeerDiscoveryMessage (browser peer discovery)
 */

import { fromString as uint8ArrayFromString } from 'uint8arrays/from-string'
import { toString as uint8ArrayToString } from 'uint8arrays/to-string'

/**
 * Message type enum matching protobuf tags
 */
export const MessageType = {
  CHAT: 1,
  FILE: 2,
  BROWSER_PEER_DISCOVERY: 3
}

/**
 * Create a chat message
 * @param {string} message - The chat message text
 * @returns {Uint8Array} Encoded message bytes
 */
export function createChatMessage(message) {
  // using JSON encoding which is interoperable
  const chatMsg = {
    type: MessageType.CHAT,
    chat: {
      message: message
    }
  }
  
  const json = JSON.stringify(chatMsg)
  return uint8ArrayFromString(json)
}

/**
 * Create a file message
 * @param {string} name - File name
 * @param {number} size - File size in bytes
 * @param {Uint8Array} data - File data
 * @returns {Uint8Array} Encoded message bytes
 */
export function createFileMessage(name, size, data) {
  const fileMsg = {
    type: MessageType.FILE,
    file: {
      name: name,
      size: size,
      data: uint8ArrayToString(data, 'base64')
    }
  }
  
  const json = JSON.stringify(fileMsg)
  return uint8ArrayFromString(json)
}


/**
 * Create a browser peer discovery message
 * @param {string} peerId - Peer ID
 * @param {string[]} multiaddrs - List of multiaddresses
 * @returns {Uint8Array} Encoded message bytes
 */
export function createBrowserPeerDiscoveryMessage(peerId, multiaddrs) {
  const discoveryMsg = {
    type: MessageType.BROWSER_PEER_DISCOVERY,
    browserPeerDiscovery: {
      peerId: peerId,
      multiaddrs: multiaddrs
    }
  }
  
  const json = JSON.stringify(discoveryMsg)
  return uint8ArrayFromString(json)
}

/**
 * Decode a Universal Connectivity message
 * @param {Uint8Array} bytes - Encoded message bytes
 * @returns {Object|null} Decoded message object or null if invalid
 */
export function decodeMessage(bytes) {
  try {
    const json = uint8ArrayToString(bytes)
    const msg = JSON.parse(json)
    
    if (msg.type !== undefined) {
      return msg
    }
    
    // Fall back to raw string for compatibility with non-JSON messages
    return {
      type: MessageType.CHAT,
      chat: {
        message: json
      }
    }
  } catch (error) {
    // If JSON parsing fails, treat as raw text message
    try {
      const text = uint8ArrayToString(bytes)
      return {
        type: MessageType.CHAT,
        chat: {
          message: text
        }
      }
    } catch {
      return null
    }
  }
}

/**
 * Check if a message is a chat message
 * @param {Object} msg - Decoded message
 * @returns {boolean} True if chat message
 */
export function isChatMessage(msg) {
  return msg && msg.type === MessageType.CHAT && msg.chat !== undefined
}

/**
 * Check if a message is a file message
 * @param {Object} msg - Decoded message
 * @returns {boolean} True if file message
 */
export function isFileMessage(msg) {
  return msg && msg.type === MessageType.FILE && msg.file !== undefined
}

/**
 * Check if a message is a browser peer discovery message
 * @param {Object} msg - Decoded message
 * @returns {boolean} True if browser peer discovery message
 */
export function isBrowserPeerDiscoveryMessage(msg) {
  return msg && msg.type === MessageType.BROWSER_PEER_DISCOVERY && msg.browserPeerDiscovery !== undefined
}

/**
 * Get the chat message text
 * @param {Object} msg - Decoded message
 * @returns {string|null} Chat message text or null
 */
export function getChatMessageText(msg) {
  if (isChatMessage(msg)) {
    return msg.chat.message
  }
  return null
}

/**
 * Get the file message details
 * @param {Object} msg - Decoded message
 * @returns {Object|null} File details or null
 */
export function getFileMessageDetails(msg) {
  if (isFileMessage(msg)) {
    return {
      name: msg.file.name,
      size: msg.file.size,
      data: uint8ArrayFromString(msg.file.data, 'base64')
    }
  }
  return null
}

