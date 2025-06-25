/* eslint-disable import/export */
/* eslint-disable complexity */
/* eslint-disable @typescript-eslint/no-namespace */
/* eslint-disable @typescript-eslint/no-unnecessary-boolean-literal-compare */
/* eslint-disable @typescript-eslint/no-empty-interface */

import { decodeMessage, encodeMessage, enumeration, message } from 'protons-runtime'

const __StatusValues = {
  UNKNOWN: 0,
  OK: 200,
  ERROR: 500,
}

const dm = {}

// DirectMessage
let _DirectMessage_codec

dm.DirectMessage = {}
dm.DirectMessage.codec = () => {
  if (_DirectMessage_codec == null) {
    _DirectMessage_codec = message(
      (obj, w, opts = {}) => {
        if (opts.lengthDelimited !== false) w.fork()
        if (opts.lengthDelimited !== false) w.ldelim()
      },
      (reader, length, opts = {}) => {
        const obj = {}
        const end = length == null ? reader.len : reader.pos + length
        while (reader.pos < end) {
          const tag = reader.uint32()
          switch (tag >>> 3) {
            default: reader.skipType(tag & 7); break
          }
        }
        return obj
      }
    )
  }
  return _DirectMessage_codec
}
dm.DirectMessage.encode = (obj) => encodeMessage(obj, dm.DirectMessage.codec())
dm.DirectMessage.decode = (buf, opts) => decodeMessage(buf, dm.DirectMessage.codec(), opts)

// Metadata
let _Metadata_codec
dm.Metadata = {}
dm.Metadata.codec = () => {
  if (_Metadata_codec == null) {
    _Metadata_codec = message(
      (obj, w, opts = {}) => {
        if (opts.lengthDelimited !== false) w.fork()
        if (obj.clientVersion != null && obj.clientVersion !== '') {
          w.uint32(10)
          w.string(obj.clientVersion)
        }
        if (obj.timestamp != null && obj.timestamp !== 0n) {
          w.uint32(16)
          w.int64(obj.timestamp)
        }
        if (opts.lengthDelimited !== false) w.ldelim()
      },
      (reader, length, opts = {}) => {
        const obj = { clientVersion: '', timestamp: 0n }
        const end = length == null ? reader.len : reader.pos + length
        while (reader.pos < end) {
          const tag = reader.uint32()
          switch (tag >>> 3) {
            case 1: obj.clientVersion = reader.string(); break
            case 2: obj.timestamp = reader.int64(); break
            default: reader.skipType(tag & 7); break
          }
        }
        return obj
      }
    )
  }
  return _Metadata_codec
}
dm.Metadata.encode = (obj) => encodeMessage(obj, dm.Metadata.codec())
dm.Metadata.decode = (buf, opts) => decodeMessage(buf, dm.Metadata.codec(), opts)

// Status
// Use string values for status, but encode/decode as numbers
// UNKNOWN = 0, OK = 200, ERROR = 500

dm.Status = {
  UNKNOWN: 'UNKNOWN',
  OK: 'OK',
  ERROR: 'ERROR',
  values: __StatusValues,
  codec: () => enumeration(__StatusValues)
}

// DirectMessageRequest
let _DirectMessageRequest_codec
dm.DirectMessageRequest = {}
dm.DirectMessageRequest.codec = () => {
  if (_DirectMessageRequest_codec == null) {
    _DirectMessageRequest_codec = message(
      (obj, w, opts = {}) => {
        if (opts.lengthDelimited !== false) w.fork()
        if (obj.metadata != null) {
          w.uint32(10)
          dm.Metadata.codec().encode(obj.metadata, w)
        }
        if (obj.content != null && obj.content !== '') {
          w.uint32(18)
          w.string(obj.content)
        }
        if (obj.type != null && obj.type !== '') {
          w.uint32(26)
          w.string(obj.type)
        }
        if (opts.lengthDelimited !== false) w.ldelim()
      },
      (reader, length, opts = {}) => {
        const obj = { content: '', type: '' }
        const end = length == null ? reader.len : reader.pos + length
        while (reader.pos < end) {
          const tag = reader.uint32()
          switch (tag >>> 3) {
            case 1: obj.metadata = dm.Metadata.codec().decode(reader, reader.uint32(), { limits: opts.limits && opts.limits.metadata }); break
            case 2: obj.content = reader.string(); break
            case 3: obj.type = reader.string(); break
            default: reader.skipType(tag & 7); break
          }
        }
        return obj
      }
    )
  }
  return _DirectMessageRequest_codec
}
dm.DirectMessageRequest.encode = (obj) => encodeMessage(obj, dm.DirectMessageRequest.codec())
dm.DirectMessageRequest.decode = (buf, opts) => decodeMessage(buf, dm.DirectMessageRequest.codec(), opts)

// DirectMessageResponse
let _DirectMessageResponse_codec
dm.DirectMessageResponse = {}
dm.DirectMessageResponse.codec = () => {
  if (_DirectMessageResponse_codec == null) {
    _DirectMessageResponse_codec = message(
      (obj, w, opts = {}) => {
        if (opts.lengthDelimited !== false) w.fork()
        if (obj.metadata != null) {
          w.uint32(10)
          dm.Metadata.codec().encode(obj.metadata, w)
        }
        if (obj.status != null && __StatusValues[obj.status] !== 0) {
          w.uint32(16)
          dm.Status.codec().encode(obj.status, w)
        }
        if (obj.statusText != null) {
          w.uint32(26)
          w.string(obj.statusText)
        }
        if (opts.lengthDelimited !== false) w.ldelim()
      },
      (reader, length, opts = {}) => {
        const obj = { status: 'UNKNOWN' }
        const end = length == null ? reader.len : reader.pos + length
        while (reader.pos < end) {
          const tag = reader.uint32()
          switch (tag >>> 3) {
            case 1: obj.metadata = dm.Metadata.codec().decode(reader, reader.uint32(), { limits: opts.limits && opts.limits.metadata }); break
            case 2: obj.status = dm.Status.codec().decode(reader); break
            case 3: obj.statusText = reader.string(); break
            default: reader.skipType(tag & 7); break
          }
        }
        return obj
      }
    )
  }
  return _DirectMessageResponse_codec
}
dm.DirectMessageResponse.encode = (obj) => encodeMessage(obj, dm.DirectMessageResponse.codec())
dm.DirectMessageResponse.decode = (buf, opts) => decodeMessage(buf, dm.DirectMessageResponse.codec(), opts)

// Root codec (not used, but for completeness)
let _dm_codec
dm.codec = () => {
  if (_dm_codec == null) {
    _dm_codec = message(
      (obj, w, opts = {}) => {
        if (opts.lengthDelimited !== false) w.fork()
        if (opts.lengthDelimited !== false) w.ldelim()
      },
      (reader, length, opts = {}) => {
        const obj = {}
        const end = length == null ? reader.len : reader.pos + length
        while (reader.pos < end) {
          const tag = reader.uint32()
          switch (tag >>> 3) {
            default: reader.skipType(tag & 7); break
          }
        }
        return obj
      }
    )
  }
  return _dm_codec
}
dm.encode = (obj) => encodeMessage(obj, dm.codec())
dm.decode = (buf, opts) => decodeMessage(buf, dm.codec(), opts)

export { dm }