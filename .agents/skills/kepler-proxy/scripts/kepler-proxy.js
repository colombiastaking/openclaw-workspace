#!/usr/bin/env node
/**
 * Kepler Proxy with Tax Query Support
 * 
 * Handles:
 * - /api/* -> kepler API
 * - /gateway/* -> kepler gateway  
 * - /es/* -> elasticsearch
 * - /tax-query?address=erd1...&year=2025 -> Returns tax data (bypasses CORS)
 */

const http = require('http');
const https = require('https');
const { parse } = require('url');

const API_KEY = 'acea534bc927840076692374ffab66fb';
const TARGET_HOST = 'kepler-api.projectx.mx';
const TARGET_PORT = 443;
const LISTEN_PORT = 3000;

// Helper: Make HTTPS request
function httpsRequest(options, body = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, headers: res.headers, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, headers: res.headers, data });
        }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

// Helper: Add CORS headers
function addCorsHeaders(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Origin, Content-Type, Accept, X-Api-Key');
}

// Fetch delegation contracts
async function fetchDelegationContracts(address) {
  const options = {
    hostname: TARGET_HOST,
    port: TARGET_PORT,
    path: `/mainnet/api/accounts/${address}/delegation`,
    method: 'GET',
    headers: { 'Api-Key': API_KEY, 'Content-Type': 'application/json' }
  };
  const result = await httpsRequest(options);
  if (result.status === 200 && Array.isArray(result.data)) {
    return result.data.map(d => d.contract).filter(Boolean);
  }
  return [];
}

// Known provider display names (for nice formatting)
const PROVIDER_DISPLAY_NAMES = {
  'colombiastaking': 'Colombia Staking',
  'figment-networks': 'Figment Networks',
  'stakefish': 'Stakefish',
  'bitcat': 'Bitcat',
  'coincast': 'Coincast',
  'stakingrewards': 'Staking Rewards',
  'elk': 'Elk Finance',
  'p2p': 'P2P',
  'binance': 'Binance',
  'kraken': 'Kraken',
  'fireblocks': 'Fireblocks',
  'celsius': 'Celsius',
  'moonlet': 'Moonlet',
  'ledger': 'Ledger',
  'trust-wallet': 'Trust Wallet',
  'math-wallet': 'Math Wallet',
};

// Format provider identity to nice display name
function formatProviderIdentity(identity) {
  if (!identity) return null;
  const lower = identity.toLowerCase();
  if (PROVIDER_DISPLAY_NAMES[lower]) {
    return PROVIDER_DISPLAY_NAMES[lower];
  }
  // Convert kebab-case or snake_case to Title Case
  return identity
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

// Fetch all providers info (identity, name, etc.)
let cachedProviders = null;
async function fetchAllProviders() {
  if (cachedProviders) return cachedProviders;
  
  const options = {
    hostname: TARGET_HOST,
    port: TARGET_PORT,
    path: '/mainnet/api/providers',
    method: 'GET',
    headers: { 'Api-Key': API_KEY, 'Content-Type': 'application/json' }
  };
  const result = await httpsRequest(options);
  if (result.status === 200 && Array.isArray(result.data)) {
    // Build a map of contract -> provider info
    cachedProviders = new Map();
    for (const p of result.data) {
      if (p.serviceFee !== undefined) {
        // This is a staking provider
        const identity = p.identity || '';
        const displayName = formatProviderIdentity(identity) || identity || 'Unknown Provider';
        const providerKey = p.provider || p.contract || '';
        if (providerKey) {
          cachedProviders.set(providerKey.toLowerCase(), {
            name: displayName,
            identity: identity,
            provider: providerKey
          });
        }
      }
    }
    console.log(`[TaxQuery] Cached ${cachedProviders.size} provider names`);
  }
  return cachedProviders || new Map();
}

// Get provider name from address
function getProviderNameFromAddress(address, providersMap) {
  const lower = address.toLowerCase();
  if (providersMap && providersMap.has(lower)) {
    const info = providersMap.get(lower);
    if (info.name) return info.name;
  }
  return null;
}

// Query Elasticsearch for transactions
async function esSearchTransactions(address, providers, year) {
  const startTs = Math.floor(new Date(`${year}-01-01`).getTime());
  const endTs = Math.floor(new Date(`${year}-12-31 23:59:59`).getTime());
  
  const mustClauses = [
    { term: { sender: address.toLowerCase() } },
    {
      bool: {
        should: providers.map(p => ({ term: { receiver: p.toLowerCase() } })),
        minimum_should_match: 1
      }
    },
    { terms: { function: ['claimRewards', 'claim'] } },
    { range: { timestamp: { gte: startTs, lte: endTs } } }
  ];
  
  const searchQuery = {
    size: 10000,
    query: { bool: { must: mustClauses } },
    sort: [{ timestamp: { order: 'desc' } }]
  };
  
  const options = {
    hostname: TARGET_HOST,
    port: TARGET_PORT,
    path: '/mainnet/es/transactions/_search',
    method: 'POST',
    headers: { 'Api-Key': API_KEY, 'Content-Type': 'application/json' }
  };
  
  const result = await httpsRequest(options, searchQuery);
  if (result.status === 200 && result.data?.hits?.hits) {
    return result.data.hits.hits.map(h => ({
      _id: h._id,
      timestamp: h._source.timestamp,
      sender: h._source.sender,
      receiver: h._source.receiver,
      function: h._source.function
    }));
  }
  return [];
}

// Query scresults for amounts
async function esSearchScResults(txHashes) {
  if (txHashes.length === 0) return [];
  
  const scResultsQuery = {
    size: txHashes.length * 5,
    query: { terms: { originalTxHash: txHashes } },
    sort: [{ timestamp: { order: 'desc' } }]
  };
  
  const options = {
    hostname: TARGET_HOST,
    port: TARGET_PORT,
    path: '/mainnet/es/scresults/_search',
    method: 'POST',
    headers: { 'Api-Key': API_KEY, 'Content-Type': 'application/json' }
  };
  
  const result = await httpsRequest(options, scResultsQuery);
  if (result.status === 200 && result.data?.hits?.hits) {
    return result.data.hits.hits.map(h => ({
      originalTxHash: h._source.originalTxHash,
      receiver: h._source.receiver,
      value: h._source.value
    }));
  }
  return [];
}

// Main tax query handler
async function handleTaxQuery(address, year) {
  console.log(`[TaxQuery] Processing ${address} for year ${year}`);
  
  // Step 1: Fetch delegation contracts
  const providers = await fetchDelegationContracts(address);
  console.log(`[TaxQuery] Found ${providers.length} delegation contracts`);
  
  if (providers.length === 0) {
    return { providers: [], transactions: [], error: null };
  }
  
  // Step 1b: Fetch all providers info for names
  const providersMap = await fetchAllProviders();
  
  // Step 2: Search ES for transactions
  const esTransactions = await esSearchTransactions(address, providers, year);
  console.log(`[TaxQuery] Found ${esTransactions.length} ES transactions`);
  
  if (esTransactions.length === 0) {
    // Still return providers with their names
    const providersWithNames = providers.map(p => ({
      address: p,
      name: getProviderNameFromAddress(p, providersMap) || p.slice(0, 20) + '...'
    }));
    return { providers: providersWithNames, transactions: [] };
  }
  
  // Step 3: Get amounts from scresults
  const txHashes = esTransactions.map(t => t._id);
  const scResults = await esSearchScResults(txHashes);
  console.log(`[TaxQuery] Found ${scResults.length} scresults`);
  
  // Step 4: Match amounts to transactions
  const claimAmounts = new Map();
  for (const sr of scResults) {
    if (sr.receiver?.toLowerCase() === address.toLowerCase()) {
      const current = claimAmounts.get(sr.originalTxHash) || 0;
      const value = parseInt(String(sr.value || '0')) / 1e18;
      claimAmounts.set(sr.originalTxHash, current + value);
    }
  }
  
  // Step 5: Build final transaction list with provider names
  const transactions = [];
  for (const tx of esTransactions) {
    const egldValue = claimAmounts.get(tx._id) || 0;
    if (egldValue > 0) {
      const txDate = new Date(tx.timestamp * 1000);
      const providerName = getProviderNameFromAddress(tx.receiver, providersMap) || tx.receiver.slice(0, 20) + '...';
      transactions.push({
        hash: tx._id,
        date: txDate.toISOString().split('T')[0],
        type: tx.function || 'claimRewards',
        value: egldValue,
        provider: tx.receiver,
        providerName: providerName,
        timestamp: tx.timestamp
      });
    }
  }
  
  // Step 6: Build providers list with names
  const providersWithNames = providers.map(p => ({
    address: p,
    name: getProviderNameFromAddress(p, providersMap) || p.slice(0, 20) + '...'
  }));
  
  console.log(`[TaxQuery] Returning ${transactions.length} transactions with amounts`);
  return { providers: providersWithNames, transactions };
}

// HTTP Server
const server = http.createServer(async (req, res) => {
  const parsedUrl = parse(req.url, true);
  const pathname = parsedUrl.pathname;
  
  // Add CORS headers to all responses
  addCorsHeaders(res);
  
  // Handle preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }
  
  console.log(`[Proxy] ${req.method} ${pathname}`);
  
  try {
    // TAX QUERY ENDPOINT - handles ES query server-side to bypass CORS
    if (pathname === '/tax-query' || pathname === '/api/tax-query') {
      const address = parsedUrl.query.address;
      const year = parseInt(parsedUrl.query.year) || new Date().getFullYear() - 1;
      
      if (!address) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Missing address parameter' }));
        return;
      }
      
      const result = await handleTaxQuery(address, year);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
      return;
    }
    
    // DELEGATION ENDPOINT
    if (pathname === '/delegation' || pathname === '/api/delegation') {
      const address = parsedUrl.query.address;
      
      if (!address) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Missing address parameter' }));
        return;
      }
      
      const providers = await fetchDelegationContracts(address);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ providers }));
      return;
    }
    
    // HEALTH CHECK
    if (pathname === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok' }));
      return;
    }
    
    // PROXY: Forward to Kepler API/Gateway/ES
    let targetPath, targetBase;
    
    if (pathname.startsWith('/api/')) {
      targetBase = `https://${TARGET_HOST}/mainnet/api/`;
      targetPath = req.url.replace(/^\/api\//, '');
    } else if (pathname.startsWith('/gateway/')) {
      targetBase = `https://${TARGET_HOST}/mainnet/gateway/`;
      targetPath = req.url.replace(/^\/gateway\//, '');
    } else if (pathname.startsWith('/es/')) {
      targetBase = `https://${TARGET_HOST}/mainnet/es/`;
      targetPath = req.url.replace(/^\/es\//, '');
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
      return;
    }
    
    const fullPath = targetBase + targetPath;
    
    const options = {
      hostname: TARGET_HOST,
      port: TARGET_PORT,
      path: fullPath.replace(`https://${TARGET_HOST}`, ''),
      method: req.method,
      headers: {
        ...req.headers,
        host: TARGET_HOST,
        'Api-Key': API_KEY,
        'Content-Type': 'application/json'
      }
    };

    const proxyReq = https.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });

    proxyReq.on('error', (err) => {
      console.error('[Proxy] Error:', err.message);
      res.writeHead(502);
      res.end('Bad Gateway');
    });

    req.pipe(proxyReq);
    
  } catch (error) {
    console.error('[Proxy] Exception:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: error.message }));
  }
});

server.listen(LISTEN_PORT, '0.0.0.0', () => {
  console.log(`Kepler proxy listening on port ${LISTEN_PORT}`);
  console.log(`Endpoints:`);
  console.log(`  GET /tax-query?address=erd1...&year=2025  - Tax query (bypasses CORS)`);
  console.log(`  GET /delegation?address=erd1...           - Delegation contracts`);
  console.log(`  GET /api/*  -> kepler API`);
  console.log(`  GET /gateway/* -> kepler gateway`);
  console.log(`  GET /es/*  -> elasticsearch`);
});
