#!/usr/bin/env node
/**
 * bus — Peer messaging MCP server for Methodical-CC
 *
 * Channels-based MCP server that lets Claude Code sessions message each other
 * across plugins. See docs/bus-design.md in the methodical-cc repo for the full
 * design rationale.
 *
 * Modes:
 *   - chat:    lightweight, ephemeral, no artifact
 *   - consult: durable, produces an artifact in docs/crossover/{thread_id}/
 *
 * Identity is resolved from .pdt/sessions, .mam{,-*}/sessions, .mama{,-*}/sessions
 * in the repo. Inbox lives at .mcc/bus/inbox/{identity}/. Artifacts live at
 * docs/crossover/{thread_id}/.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import * as fs from 'node:fs'
import * as fsp from 'node:fs/promises'
import * as path from 'node:path'
import * as os from 'node:os'
import * as crypto from 'node:crypto'

// ============================================================================
// Constants
// ============================================================================

const SESSION_FILE_GLOBS = [
  '.pdt/sessions',
  '.pdt-*/sessions',
  '.mam/sessions',
  '.mam-*/sessions',
  '.mama/sessions',
  '.mama-*/sessions',
]
const INBOX_ROOT = '.mcc/bus/inbox'
const CROSSOVER_ROOT = 'docs/crossover'
const CONSUMED_DIR = '.consumed'
const THREAD_STATE_FILE = '.bus-state.json'

const VALID_MODES = ['chat', 'consult']
const VALID_TYPES = [
  'request', 'response', 'clarification', 'followup',
  'commission', 'debrief', 'update',
]
const THREAD_ID_PATTERN = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/

// ============================================================================
// Utility helpers
// ============================================================================

function nowIso() {
  // ISO without milliseconds, suffix Z
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
}

function repoRoot() {
  return process.cwd()
}

async function exists(p) {
  try { await fsp.stat(p); return true } catch { return false }
}

async function globDirPattern(root, pattern) {
  // pattern is "<dir-glob>/<filename>" — only first segment can contain a *
  const slash = pattern.indexOf('/')
  if (slash < 0) return []
  const dirPattern = pattern.slice(0, slash)
  const filename = pattern.slice(slash + 1)
  const dirRegex = new RegExp('^' + dirPattern.replace(/\*/g, '.*') + '$')
  const out = []
  let entries
  try { entries = await fsp.readdir(root, { withFileTypes: true }) } catch { return [] }
  for (const e of entries) {
    if (e.isDirectory() && dirRegex.test(e.name)) {
      const candidate = path.join(root, e.name, filename)
      if (await exists(candidate)) out.push(candidate)
    }
  }
  return out
}

async function findSessionsFiles() {
  const root = repoRoot()
  const all = []
  for (const pat of SESSION_FILE_GLOBS) {
    const found = await globDirPattern(root, pat)
    all.push(...found)
  }
  return all
}

async function parseSessionsFile(p) {
  const out = {}
  let content
  try { content = await fsp.readFile(p, 'utf8') } catch { return out }
  for (const line of content.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue
    const eq = trimmed.indexOf('=')
    const name = trimmed.slice(0, eq).trim()
    const sid = trimmed.slice(eq + 1).trim()
    if (name && sid) out[name] = sid
  }
  return out
}

async function allIdentities() {
  const result = {}
  for (const f of await findSessionsFiles()) {
    const entries = await parseSessionsFile(f)
    for (const [name, sid] of Object.entries(entries)) {
      result[name] = { sessionId: sid, sessionsFile: path.relative(repoRoot(), f) }
    }
  }
  return result
}

async function mySessionId() {
  // Best-effort: most recently modified .jsonl in the project's transcript dir.
  // Brittle with concurrent same-repo sessions; iterate as needed.
  const projectDir = process.env.CLAUDE_PROJECT_DIR
  if (!projectDir) return null
  const mangled = projectDir.replace(/\//g, '-')
  const transcriptDir = path.join(os.homedir(), '.claude', 'projects', mangled)
  let entries
  try { entries = await fsp.readdir(transcriptDir, { withFileTypes: true }) } catch { return null }
  const jsonl = []
  for (const e of entries) {
    if (e.isFile() && e.name.endsWith('.jsonl')) {
      try {
        const stat = await fsp.stat(path.join(transcriptDir, e.name))
        jsonl.push({ name: e.name, mtime: stat.mtimeMs })
      } catch {}
    }
  }
  if (jsonl.length === 0) return null
  jsonl.sort((a, b) => b.mtime - a.mtime)
  return jsonl[0].name.replace(/\.jsonl$/, '')
}

async function myIdentity() {
  const sid = await mySessionId()
  if (!sid) return { name: null, sessionId: null }
  for (const [name, info] of Object.entries(await allIdentities())) {
    if (info.sessionId === sid) return { name, sessionId: sid }
  }
  return { name: null, sessionId: sid }
}

// ============================================================================
// Inbox protocol
// ============================================================================

function inboxDir(identity) {
  return path.join(repoRoot(), INBOX_ROOT, identity)
}

function consumedDirFor(identity) {
  return path.join(inboxDir(identity), CONSUMED_DIR)
}

async function ensureInbox(identity) {
  await fsp.mkdir(inboxDir(identity), { recursive: true })
  await fsp.mkdir(consumedDirFor(identity), { recursive: true })
}

function inboxFilename(sender, threadId) {
  const ts = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)
  const nonce = crypto.randomBytes(2).toString('hex')
  return `${ts}_${sender}_${threadId}_${nonce}.json`
}

async function writeFileAtomic(target, contents) {
  await fsp.mkdir(path.dirname(target), { recursive: true })
  const tmp = target + '.tmp'
  await fsp.writeFile(tmp, contents)
  await fsp.rename(tmp, target)
}

async function listPending(identity) {
  let entries
  try { entries = await fsp.readdir(inboxDir(identity), { withFileTypes: true }) } catch { return [] }
  const files = []
  for (const e of entries) {
    if (e.isFile() && e.name.endsWith('.json')) {
      const full = path.join(inboxDir(identity), e.name)
      try {
        const stat = await fsp.stat(full)
        files.push({ path: full, mtime: stat.mtimeMs })
      } catch {}
    }
  }
  files.sort((a, b) => a.mtime - b.mtime)
  return files.map(f => f.path)
}

async function markConsumed(msgPath) {
  const target = path.join(path.dirname(msgPath), CONSUMED_DIR, path.basename(msgPath))
  await fsp.mkdir(path.dirname(target), { recursive: true })
  await fsp.rename(msgPath, target)
}

// ============================================================================
// Artifact / thread
// ============================================================================

function validateThreadId(threadId) {
  if (!threadId || !THREAD_ID_PATTERN.test(threadId)) {
    throw new Error(
      `thread_id must be kebab-case (lowercase letters, digits, hyphens), got: ${JSON.stringify(threadId)}`,
    )
  }
}

async function autoThreadId(sender, recipient) {
  const today = new Date().toISOString().slice(0, 10)
  const base = `${sender}-to-${recipient}-${today}`
  const crossover = path.join(repoRoot(), CROSSOVER_ROOT)
  let entries
  try { entries = await fsp.readdir(crossover, { withFileTypes: true }) } catch { return `${base}-01` }
  const count = entries.filter(e => e.isDirectory() && e.name.startsWith(base)).length
  return `${base}-${String(count + 1).padStart(2, '0')}`
}

function threadDir(threadId) {
  return path.join(repoRoot(), CROSSOVER_ROOT, threadId)
}

async function nextTurnNumber(threadId) {
  let entries
  try { entries = await fsp.readdir(threadDir(threadId), { withFileTypes: true }) } catch { return 1 }
  const turns = entries
    .filter(e => e.isFile() && e.name.endsWith('.md') && /^\d{3}/.test(e.name))
    .map(e => parseInt(e.name.slice(0, 3), 10))
  return turns.length === 0 ? 1 : Math.max(...turns) + 1
}

async function loadThreadState(threadId) {
  try {
    const txt = await fsp.readFile(path.join(threadDir(threadId), THREAD_STATE_FILE), 'utf8')
    return JSON.parse(txt)
  } catch {
    return {}
  }
}

async function updateThreadState(threadId, sender, recipient, close) {
  const state = await loadThreadState(threadId)
  const participants = new Set(state.participants || [])
  participants.add(sender)
  participants.add(recipient)
  const newState = {
    thread_id: threadId,
    participants: [...participants].sort(),
    started_at: state.started_at || nowIso(),
    last_activity_at: nowIso(),
    status: close ? 'resolved' : (state.status || 'open'),
    turn_count: (state.turn_count || 0) + 1,
    awaiting: close ? null : recipient,
  }
  await writeFileAtomic(
    path.join(threadDir(threadId), THREAD_STATE_FILE),
    JSON.stringify(newState, null, 2),
  )
}

async function writeArtifact(threadId, sender, type_, recipient, body) {
  if (!VALID_TYPES.includes(type_)) {
    throw new Error(`type must be one of ${VALID_TYPES.join(', ')}, got: ${type_}`)
  }
  const turn = await nextTurnNumber(threadId)
  const fname = `${String(turn).padStart(3, '0')}-${sender}-${type_}.md`
  const target = path.join(threadDir(threadId), fname)
  await fsp.mkdir(path.dirname(target), { recursive: true })
  const front =
    `---\n` +
    `thread_id: ${threadId}\n` +
    `turn: ${turn}\n` +
    `type: ${type_}\n` +
    `from: ${sender}\n` +
    `to: ${recipient}\n` +
    `sent_at: ${nowIso()}\n` +
    `status: open\n` +
    `---\n\n`
  await fsp.writeFile(target, front + body)
  return path.relative(repoRoot(), target)
}

// ============================================================================
// MCP server setup
// ============================================================================

const server = new Server(
  { name: 'bus', version: '1.0.0' },
  {
    capabilities: {
      experimental: { 'claude/channel': {} },
      tools: {},
    },
    instructions:
      'Peer messages from the methodical-cc bus arrive as ' +
      '<channel source="bus" from="..." thread_id="..." mode="chat|consult"> tags. ' +
      'When mode=consult, an artifact_path attribute points at a structured document ' +
      'under docs/crossover/{thread_id}/ — read it for the full content. ' +
      'To send, call peer_send with mode=chat for lightweight exchanges or mode=consult ' +
      'for durable design discussions (consult mode produces an artifact). ' +
      'Use peer_list to see registered identities and pending message counts.',
  },
)

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'peer_send',
      description:
        'Send a message to a peer identity over the methodical-cc bus. ' +
        'Use mode=chat for lightweight ephemeral exchanges, mode=consult for ' +
        'durable design discussions that produce a structured artifact in docs/crossover/.',
      inputSchema: {
        type: 'object',
        properties: {
          to: { type: 'string', description: 'Target identity name (e.g. "pdt", "arch").' },
          body: {
            type: 'string',
            description:
              'Message body — always present. Becomes the channel notification content the recipient sees.',
          },
          mode: {
            type: 'string',
            enum: VALID_MODES,
            description: 'chat (ephemeral) or consult (produces artifact).',
          },
          thread_id: {
            type: 'string',
            description:
              'Kebab-case thread id (e.g. "consult-007-depth-visibility"). Auto-generated if omitted.',
          },
          artifact_body: {
            type: 'string',
            description:
              'Required when mode="consult". The structured artifact content (request/response body with options, instinct, etc.).',
          },
          artifact_type: {
            type: 'string',
            enum: VALID_TYPES,
            description:
              'Type of artifact: request, response, clarification, followup, commission, debrief, update. Defaults to "request".',
          },
          close: {
            type: 'boolean',
            description: 'Mark this message as the close of the thread.',
          },
        },
        required: ['to', 'body', 'mode'],
      },
    },
    {
      name: 'peer_list',
      description:
        'List registered peer identities in this repo, with last activity timestamps and pending message counts.',
      inputSchema: { type: 'object', properties: {} },
    },
  ],
}))

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const name = req.params.name
  const args = req.params.arguments || {}
  try {
    let result
    if (name === 'peer_send') {
      result = await handlePeerSend(args)
    } else if (name === 'peer_list') {
      result = await handlePeerList()
    } else {
      throw new Error(`unknown tool: ${name}`)
    }
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
  } catch (e) {
    return {
      content: [{ type: 'text', text: `Error: ${e.message}` }],
      isError: true,
    }
  }
})

// ============================================================================
// Tool handlers
// ============================================================================

async function handlePeerSend(args) {
  const {
    to, body, mode,
    thread_id,
    artifact_body,
    artifact_type = 'request',
    close = false,
  } = args

  if (!VALID_MODES.includes(mode)) {
    throw new Error(`mode must be one of ${VALID_MODES.join(', ')}`)
  }

  const me = await myIdentity()
  const sender = me.name || 'anonymous'

  const identities = await allIdentities()
  if (!identities[to]) {
    const known = Object.keys(identities).sort().join(', ') || '(none)'
    throw new Error(
      `unknown recipient '${to}'. Known identities: ${known}. ` +
      `Run /bus:status or peer_list to see who's registered.`,
    )
  }

  let threadId = thread_id
  if (!threadId) {
    threadId = await autoThreadId(sender, to)
  } else {
    validateThreadId(threadId)
  }

  let artifactPath = null
  if (mode === 'consult') {
    if (!artifact_body) {
      throw new Error('artifact_body is required for mode="consult"')
    }
    artifactPath = await writeArtifact(threadId, sender, artifact_type, to, artifact_body)
  }

  await ensureInbox(to)
  const payload = {
    from: sender,
    to,
    thread_id: threadId,
    mode,
    sent_at: nowIso(),
    body,
    artifact_path: artifactPath,
    close,
  }
  const fname = inboxFilename(sender, threadId)
  const target = path.join(inboxDir(to), fname)
  await writeFileAtomic(target, JSON.stringify(payload, null, 2))

  await updateThreadState(threadId, sender, to, close)

  return {
    ok: true,
    thread_id: threadId,
    delivered_to: to,
    inbox_file: path.relative(repoRoot(), target),
    artifact_path: artifactPath,
    mode,
    close,
  }
}

async function handlePeerList() {
  const identities = await allIdentities()
  const peers = []
  for (const name of Object.keys(identities).sort()) {
    const info = identities[name]
    let lastActivity = null
    try {
      const top = await fsp.readdir(inboxDir(name), { withFileTypes: true })
      let maxMtime = 0
      const stack = top.map(e => ({ entry: e, dir: inboxDir(name) }))
      while (stack.length) {
        const { entry, dir } = stack.pop()
        const full = path.join(dir, entry.name)
        if (entry.isDirectory()) {
          try {
            const sub = await fsp.readdir(full, { withFileTypes: true })
            for (const s of sub) stack.push({ entry: s, dir: full })
          } catch {}
        } else if (entry.isFile()) {
          try {
            const st = await fsp.stat(full)
            if (st.mtimeMs > maxMtime) maxMtime = st.mtimeMs
          } catch {}
        }
      }
      if (maxMtime > 0) lastActivity = new Date(maxMtime).toISOString()
    } catch {}
    const pending = (await listPending(name)).length
    peers.push({
      identity: name,
      sessions_file: info.sessionsFile,
      last_activity: lastActivity,
      pending_messages: pending,
    })
  }
  const me = await myIdentity()
  return {
    self: { identity: me.name, session_id: me.sessionId },
    peers,
  }
}

// ============================================================================
// Channel notification emission
// ============================================================================

async function emitChannelNotification(payload) {
  const meta = {
    from: payload.from || 'unknown',
    thread_id: payload.thread_id || '',
    mode: payload.mode || 'chat',
  }
  if (payload.artifact_path) meta.artifact_path = payload.artifact_path
  if (payload.close) meta.close = 'true'
  // strip empty values
  for (const k of Object.keys(meta)) {
    if (!meta[k]) delete meta[k]
  }
  await server.notification({
    method: 'notifications/claude/channel',
    params: {
      content: payload.body || '',
      meta,
    },
  })
}

// ============================================================================
// Startup unread delivery + watcher
// ============================================================================

async function deliverPendingAtStartup() {
  const me = (await myIdentity()).name
  if (!me) return
  await ensureInbox(me)
  const pending = await listPending(me)
  if (pending.length === 0) return
  for (const p of pending) {
    try {
      const txt = await fsp.readFile(p, 'utf8')
      const payload = JSON.parse(txt)
      await emitChannelNotification(payload)
      await markConsumed(p)
    } catch (e) {
      process.stderr.write(`bus: failed to process ${p}: ${e.message}\n`)
    }
  }
}

function startInboxWatcher(identity) {
  const dir = inboxDir(identity)
  // Debounce: events can fire multiple times for one write. Track recently-seen filenames briefly.
  const recentlySeen = new Set()
  fs.watch(dir, async (eventType, filename) => {
    if (!filename) return
    if (!filename.endsWith('.json')) return
    if (filename.startsWith('.')) return // ignore .consumed/* etc
    if (recentlySeen.has(filename)) return
    recentlySeen.add(filename)
    setTimeout(() => recentlySeen.delete(filename), 1000)

    const full = path.join(dir, filename)
    // Brief delay to let the writer finish their atomic rename
    await new Promise(r => setTimeout(r, 50))
    try {
      const txt = await fsp.readFile(full, 'utf8')
      const payload = JSON.parse(txt)
      await emitChannelNotification(payload)
      await markConsumed(full)
    } catch (e) {
      // File may have been moved already (race) or not yet fully written; ignore.
    }
  })
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  const transport = new StdioServerTransport()
  await server.connect(transport)

  // After connection: deliver any unread, then watch for new arrivals.
  await deliverPendingAtStartup()

  const me = (await myIdentity()).name
  if (me) {
    startInboxWatcher(me)
  }
  // No 'else': anonymous sessions still serve tools but won't receive messages.
}

main().catch((e) => {
  process.stderr.write(`bus: fatal: ${e.stack || e.message}\n`)
  process.exit(1)
})
