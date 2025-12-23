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
 * Decode a Universal Connectivity message (handles both JSON and protobuf)
 * @param {Uint8Array} bytes - Encoded message bytes
 * @returns {Object|null} Decoded message object or null if invalid
 */
export function decodeMessage(bytes) {
  // Try JSON first (JS-to-JS messages)
  try {
    const json = uint8ArrayToString(bytes)
    const msg = JSON.parse(json)
    
    if (msg.type !== undefined) {
      return msg
    }
  } catch (error) {
    // Not JSON, try protobuf decoding (from Rust checker)
  }

  // Try protobuf decoding (from Rust checker)
  // Protobuf format for UniversalConnectivityMessage:
  // - field 1 (from): string
  // - field 2 (message): string  
  // - field 3 (timestamp): int64
  // - field 4 (message_type): enum
  try {
    let offset = 0
    let from = null
    let message = null
    
    while (offset < bytes.length) {
      // Read tag (field number * 8 + wire type)
      const tag = bytes[offset++]
      if (tag === 0) break
      
      const fieldNum = tag >> 3
      const wireType = tag & 0x7
      
      if (wireType === 2) { // Length-delimited (strings)
        // Read length (varint)
        let len = 0
        let shift = 0
        while (offset < bytes.length) {
          const byte = bytes[offset++]
          len |= (byte & 0x7f) << shift
          if ((byte & 0x80) === 0) break
          shift += 7
        }
        
        // Read string value
        if (offset + len <= bytes.length) {
          const strBytes = bytes.slice(offset, offset + len)
          const str = uint8ArrayToString(strBytes)
          offset += len
          
          if (fieldNum === 1) {
            from = str
          } else if (fieldNum === 2) {
            message = str
          }
          
          // If we found the message, return early
          if (message) {
            return {
              type: MessageType.CHAT,
              chat: {
                message: message
              }
            }
          }
        }
      } else if (wireType === 0) { // Varint (skip)
        while (offset < bytes.length) {
          const byte = bytes[offset++]
          if ((byte & 0x80) === 0) break
        }
      } else if (wireType === 1) { // 64-bit (skip 8 bytes)
        offset += 8
      }
    }
    
    // If we found the message, return it
    if (message) {
      return {
        type: MessageType.CHAT,
        chat: {
          message: message
        }
      }
    }
  } catch (error) {
    // Protobuf decode failed
  }

  // Final fallback: try as raw text
  try {
    const text = uint8ArrayToString(bytes)
    // Filter out non-printable characters
    const cleanText = text.replace(/[\x00-\x1F\x7F-\x9F]/g, '')
    if (cleanText.length > 0 && cleanText.length < 200) {
      return {
        type: MessageType.CHAT,
        chat: {
          message: cleanText
        }
      }
    }
  } catch {
    // All decode attempts failed
  }
  
  return null
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

