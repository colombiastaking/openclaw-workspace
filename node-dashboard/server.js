'use strict';

const http = require('http');
const https = require('https');
const express = require('express');
const path = require('path');
const fs = require('fs');

const NODES = [
  { name: 'Shard 0', ip: '192.168.0.120', shard: 0, color: '#58a6ff' },
  { name: 'Shard 1', ip: '192.168.0.121', shard: 1, color: '#a371f7' },
  { name: 'Shard 2', ip: '192.168.0.122', shard: 2, color: '#3fb950' },
  { name: 'Metachain', ip: '192.168.0.124', shard: -1, color: '#f0883e' },
];

const HISTORY_SIZE = 120;
const POLL_INTERVAL = 3000;
const REFERENCE_CACHE_TTL = 60000;

const app = express();

// ── State ─────────────────────────────────────────────────────────────────
let nodesState = NODES.map(n => ({
  name: n.name, ip: n.ip, shard: n.shard, color: n.color,
  cpu: null, memLoad: null, peers: null, round: null, epoch: null,
  blocks: null, consensus: null, version: null,
  txPool: null, lastSeen: null, online: false,
  roundDiff: null, syncStatus: 'unknown',
}));

const history = NODES.map(() => []);
let lastUpdate = null;
let referenceRound = null;
let referenceEpoch = null;
let referenceCacheTime = 0;

// SSE clients
const clients = new Set();

// ── HTTP Helper ────────────────────────────────────────────────────────────
function httpGet(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const isHttps = url.startsWith('https://');
    const mod = isHttps ? https : http;
    const timer = setTimeout(() => reject(new Error('timeout')), timeout);
    const req = mod.get(url, { headers: { 'Accept': 'application/json' } }, res => {
      clearTimeout(timer);
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => { try { resolve(JSON.parse(data)); } catch (e) { reject(e); } });
    });
    req.on('error', err => { clearTimeout(timer); reject(err); });
    req.setTimeout(timeout, () => { clearTimeout(timer); req.destroy(); reject(new Error('timeout')); });
  });
}

// ── Broadcast ─────────────────────────────────────────────────────────────
function broadcast(payload) {
  const msg = `data: ${JSON.stringify(payload)}\n\n`;
  for (const res of clients) {
    try { res.write(msg); } catch (e) { clients.delete(res); }
  }
}

function addToHistory(i, point) {
  history[i].push(point);
  if (history[i].length > HISTORY_SIZE) history[i].shift();
}

function getPayload() {
  return {
    nodes: nodesState.map(n => ({ ...n })),
    history: NODES.map((n, i) => ({ name: n.name, ip: n.ip, shard: n.shard, color: n.color, data: history[i] })),
    lastUpdate, referenceRound, referenceEpoch,
  };
}

// ── Reference Data ─────────────────────────────────────────────────────────
async function updateReference() {
  const now = Date.now();
  if (now - referenceCacheTime < REFERENCE_CACHE_TTL && referenceRound) return;
  try {
    const [s0, s1, s2, meta] = await Promise.all([
      httpGet('https://api.multiversx.com/blocks?size=1&shard=0', 5000),
      httpGet('https://api.multiversx.com/blocks?size=1&shard=1', 5000),
      httpGet('https://api.multiversx.com/blocks?size=1&shard=2', 5000),
      httpGet('https://api.multiversx.com/blocks?size=1&shard=4294967295', 5000),
    ]);
    referenceRound = Math.max(s0[0]?.nonce ?? 0, s1[0]?.nonce ?? 0, s2[0]?.nonce ?? 0, meta[0]?.nonce ?? 0);
    referenceEpoch = s0[0]?.epoch ?? null;
    referenceCacheTime = now;
  } catch (e) { /* keep last known */ }
}

// ── Node Polling ───────────────────────────────────────────────────────────
async function pollNodes() {
  await updateReference();
  await Promise.allSettled(NODES.map(async (node, i) => {
    try {
      const d = await httpGet(`http://${node.ip}:80/node/status`, 5000);
      const m = d?.data?.metrics || {};
      const round = m.erd_current_round;
      const roundDiff = referenceRound && round ? referenceRound - round : null;
      let syncStatus = 'synced';
      if (roundDiff === null) syncStatus = 'unknown';
      else if (roundDiff > 10) syncStatus = 'behind';
      else if (roundDiff > 2) syncStatus = 'lagging';

      const state = {
        cpu: m.erd_cpu_load_percent ?? null,
        memLoad: m.erd_mem_load_percent ?? null,
        peers: m.erd_num_connected_peers ?? null,
        round, epoch: m.erd_epoch_number ?? null,
        blocks: m.erd_count_accepted_blocks ?? null,
        consensus: m.erd_consensus_state ?? null,
        version: (m.erd_app_version || '').split('/')[0],
        txPool: m.erd_tx_pool_load ?? null,
        lastSeen: Date.now(), online: true, roundDiff, syncStatus,
      };
      nodesState[i] = { ...nodesState[i], ...state };
      addToHistory(i, { cpu: state.cpu, memLoad: state.memLoad, peers: state.peers, round: state.round, epoch: state.epoch, ts: Date.now() });
    } catch (e) {
      nodesState[i] = { ...nodesState[i], online: false, lastSeen: Date.now() };
    }
  }));
  lastUpdate = Date.now();
  broadcast(getPayload());
}

// ── Routes (EXPLICIT BEFORE static) ────────────────────────────────────────
const INDEX_HTML = path.join(__dirname, 'public', 'index.html');

app.get('/api/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.flushHeaders();
  res.write(`data: ${JSON.stringify(getPayload())}\n\n`);
  clients.add(res);
  req.on('close', () => clients.delete(res));
});

app.get('/api/nodes', (req, res) => res.json(getPayload()));

// Explicit routes served BEFORE static (express matches in order)
app.get('/nodes', (req, res) => res.type('html').end(fs.readFileSync(INDEX_HTML)));
app.get('/', (req, res) => res.type('html').end(fs.readFileSync(INDEX_HTML)));

// Static AFTER explicit routes (serves assets, network/, etc.)
app.use(express.static(__dirname + '/public'));

// ── Start ─────────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Node dashboard listening on ${PORT}`));
setInterval(pollNodes, POLL_INTERVAL);
pollNodes();