# alice-mcp-multiversx Skill

Use the MultiversX MCP server via mcporter to interact with the MultiversX blockchain.

## Setup

The MCP server is already configured at:
- Path: `/home/raspberry/.openclaw/workspace/alice-mcp-multiversx/`
- Wallet: Alice's main wallet (`erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy`)
- mcporter config: `~/.mcporter/mcporter.json`

## Verify Server Status

```bash
mcporter list
```

Should show: `multiversx (14 tools, Xs) — Listed 1 server (1 healthy)`

## Available Tools (14 total)

### Read Tools (no signing required)

| Tool | What it does | Example |
|------|-------------|---------|
| `get-balance` | EGLD balance | `mcporter call multiversx.get-balance address:erd1...` |
| `query-account` | Full account info (balance, nonce, shard) | `mcporter call multiversx.query-account address:erd1...` |
| `track-transaction` | TX status by hash | `mcporter call multiversx.track-transaction txHash:<hash>` |
| `search-products` | Search NFTs/SFTs | `mcporter call multiversx.search-products query:staking limit:5` |

### Write Tools (requires signing)

| Tool | What it does | Example |
|------|-------------|---------|
| `send-egld` | Send EGLD | `mcporter call multiversx.send-egld receiver:erd1... amount:1000000000000000000` |
| `send-tokens` | Send ESDT/NFT/SFT | `mcporter call multiversx.send-tokens receiver:erd1... tokenIdentifier:USDC-c76f1f amount:1000000` |
| `send-egld-to-multiple` | Batch EGLD airdrop | `mcporter call multiversx.send-egld-to-multiple amount:1000000000000000000 receivers:["erd1...","erd1..."]` |
| `send-tokens-to-multiple` | Batch token transfers | (complex — see schema) |
| `issue-fungible-token` | Create new ESDT token | `mcporter call multiversx.issue-fungible-token tokenName:MyToken tokenTicker:MTK initialSupply:1000000 numDecimals:18` |
| `issue-nft-collection` | Create NFT collection | `mcporter call multiversx.issue-nft-collection tokenName:MyNFT tokenTicker:MNFT` |
| `issue-sft-collection` | Create SFT collection | `mcporter call multiversx.issue-sft-collection tokenName:MySFT tokenTicker:MSFT` |
| `issue-meta-esdt-collection` | Create Meta-ESDT collection | `mcporter call multiversx.issue-meta-esdt-collection tokenName:MyMeta tokenTicker:MMETA numDecimals:18` |
| `create-nft` | Mint NFT/SFT under existing collection | `mcporter call multiversx.create-nft collectionIdentifier:COL-123456 name:"My NFT" royalties:500 quantity:1` |
| `create-relayed-v3` | Gasless TX via relayer | (for third-party gas sponsorship) |

## Quick Examples

### Check Alice's balance
```bash
mcporter call multiversx.get-balance address:erd1a7e9dyqcffasu9d4vu45s6cuv25g6qfeqy2r7m6gqyle7vpdkgqqazpyuy
```

### Check any address
```bash
mcporter call multiversx.query-account address:erd1...
```

### Track a transaction
```bash
mcporter call multiversx.track-transaction txHash:d7a...5c
```

### Search NFTs by collection
```bash
mcporter call multiversx.search-products query:staking collection:COL-123456 limit:10
```

## Important Notes

- **Amounts** are in atomic units (1 EGLD = 10^18 wei)
- **Signing**: Write tools use the PEM file at `~/.openclaw/wallet/.private_key`
- **Network**: mainnet (configured in `.env`)
- **Server path**: `/home/raspberry/.openclaw/workspace/alice-mcp-multiversx/`

## ⚠️ mcporter CLI Integer Limitation

**Problem:** mcporter CLI v0.7.3 parses `amount:10000000000000000` as a JavaScript number, which loses precision for large integers > 2^53. The MCP server expects a **string** but receives a **number**, causing validation errors.

**Workaround:** For write transactions (send-egld, send-tokens, etc.), call the MCP server directly via Node.js instead of mcporter CLI:

```bash
cd /home/raspberry/.openclaw/workspace/alice-mcp-multiversx
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"send-egld","arguments":{"receiver":"<erd1>","amount":"10000000000000000"}}}' | \
  MVX_NETWORK=mainnet MVX_SIGNING_MODE=pem MVX_WALLET_PEM=/home/raspberry/.openclaw/wallet/.private_key \
  node dist/index.js mcp
```

This was tested and works. The mcporter issue is a CLI parsing bug, not an MCP server bug.

## Troubleshooting

### Server shows as offline
```bash
cd /home/raspberry/.openclaw/workspace/alice-mcp-multiversx && npm run build
# Then test:
mcporter list
```

### Permission errors
Wallet PEM must be readable:
```bash
chmod 600 ~/.openclaw/wallet/.private_key
```

### Rebuild if src/ changes
```bash
cd /home/raspberry/.openclaw/workspace/alice-mcp-multiversx && npm run build
```

## Repos

- MCP Server: `https://github.com/colombiastaking/alice-mcp-multiversx`
- Skill: `~/.openclaw/workspace/.agents/skills/alice-mcp-multiversx/`
