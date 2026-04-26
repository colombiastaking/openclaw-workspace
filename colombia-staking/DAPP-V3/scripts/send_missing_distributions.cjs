/**
 * MCP Direct Batch Sender - send_missing_distributions.cjs
 * 
 * Calls the MCP send-tokens tool directly via raw JSON-RPC over stdio.
 * This avoids mcporter CLI's string→number coercion that breaks BigInt amounts.
 * 
 * Usage:
 *   node send_missing_distributions.cjs --pool bonus
 *   node send_missing_distributions.cjs --pool gold
 *   node send_missing_distributions.cjs --pool dao
 * 
 * Environment (picked up automatically from mcporter.json via MCP_PATH):
 *   MVX_NETWORK=mainnet
 *   MVX_SIGNING_MODE=pem
 *   MVX_WALLET_PEM=/home/raspberry/.openclaw/wallet/.private_key
 */

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const OUTPUT_DIR = "/tmp/cols_distribution";
const MCP_PATH = "/home/raspberry/.openclaw/workspace/alice-mcp-multiversx/dist/index.js";
const COLS_TOKEN_ID = "COLS-9d91b7";
const DAO_TOKEN_ID = "COLS-9d91b7"; // same token
const PEERME_CLAIM = "erd1qqqqqqqqqqqqqpgqjhn0rrta3hceyguqlmkqgklxc0eh0r5rl3tsv6a9k0";

// ─── MCP over stdio ─────────────────────────────────────────────────────────────
function callMcpTool(toolName, args) {
  return new Promise((resolve, reject) => {
    const request = {
      jsonrpc: "2.0",
      id: Date.now(),
      method: "tools/call",
      params: { name: toolName, arguments: args }
    };
    const child = spawn("node", [MCP_PATH, "mcp"], {
      stdio: ["pipe", "pipe", "pipe"],
      env: {
        ...process.env,
        MVX_NETWORK: "mainnet",
        MVX_SIGNING_MODE: "pem",
        MVX_WALLET_PEM: "/home/raspberry/.openclaw/wallet/.private_key"
      }
    });
    let stdout = "", stderr = "";
    child.stdout.on("data", d => stdout += d);
    child.stderr.on("data", d => stderr += d);
    child.on("error", reject);
    child.on("close", () => {
      const lines = stdout.trim().split("\n").filter(Boolean);
      try {
        // Last JSON line is the result
        const response = JSON.parse(lines[lines.length - 1] || "{}");
        if (response.error) {
          reject(new Error(response.error.message || JSON.stringify(response.error)));
          return;
        }
        resolve(response.result || response);
      } catch {
        reject(new Error(`MCP parse error: ${stdout.slice(0, 200)}`));
      }
    });
    child.stdin.write(JSON.stringify(request) + "\n");
    child.stdin.end();
  });
}

// ─── Helpers ─────────────────────────────────────────────────────────────────────
const sleep = ms => new Promise(s => setTimeout(s, ms));

function colsToAtomic(amountStr) {
  // amount as string like "3.0161508367822694" → atomic units string
  const num = parseFloat(amountStr);
  return BigInt(Math.floor(num * 1e18)).toString();
}

// ─── Pool senders ─────────────────────────────────────────────────────────────
async function sendMissingBonus() {
  const files = fs.readdirSync(OUTPUT_DIR)
    .filter(f => f.startsWith("bonus_distribution_") && f.endsWith(".json"))
    .sort().reverse();
  if (!files.length) throw new Error("No bonus distribution file found");
  const dist = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, files[0]), "utf8"));
  const recipients = dist.bonus?.recipients || [];
  console.log(`\nBONUS: ${recipients.length} recipients in file`);

  const sent = new Set();
  for (const r of recipients) { if (r.tx) sent.add(r.address.toLowerCase()); }
  console.log(`BONUS: ${sent.size} have a tx hash`);

  const missing = recipients.filter(r => !sent.has(r.address.toLowerCase()));
  console.log(`BONUS: ${missing.length} MISSING distributions\n`);
  if (!missing.length) return { pool: "bonus", missing: 0, success: 0, failed: 0 };

  let success = 0, fail = 0;

  for (const m of missing) {
    const amount = colsToAtomic(m.amount.toString());
    try {
      const result = await callMcpTool("send-tokens", {
        receiver: m.address,
        tokenIdentifier: COLS_TOKEN_ID,
        amount  // string - preserved through JSON-RPC
      });
      const text = result?.content?.[0]?.text || "";
      const txHash = text.match(/transactions\/([a-f0-9]+)/)?.[1] || "";
      m._txHash = txHash; m._verified = true;
      success++;
      console.log(`  ✅ ${m.address.slice(0, 14)}... → ${parseFloat(m.amount).toFixed(4)} COLS`);
      await sleep(800);
    } catch (e) {
      fail++; m._error = e.message;
      console.log(`  ❌ ${m.address.slice(0, 14)}... → ${e.message}`);
    }
  }

  fs.writeFileSync(path.join(OUTPUT_DIR, files[0]), JSON.stringify(dist, null, 2));
  fs.writeFileSync(path.join(OUTPUT_DIR, "bonus_missing_resent.json"),
    JSON.stringify({ pool: "bonus", sent: success, failed: fail, recipients: missing }, null, 2));
  return { pool: "bonus", missing: missing.length, success, fail };
}

async function sendMissingGold() {
  const files = fs.readdirSync(OUTPUT_DIR)
    .filter(f => f.startsWith("gold_distribution_") && f.endsWith(".json"))
    .sort().reverse();
  if (!files.length) throw new Error("No gold distribution file found");
  const dist = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, files[0]), "utf8"));
  const recipients = dist.recipients || dist.gold?.recipients || [];
  console.log(`\nGOLD: ${recipients.length} recipients in file`);

  const sent = new Set();
  for (const r of recipients) { if (r.tx) sent.add(r.address.toLowerCase()); }
  console.log(`GOLD: ${sent.size} have a tx hash`);

  const missing = recipients.filter(r => !sent.has(r.address.toLowerCase()));
  console.log(`GOLD: ${missing.length} MISSING distributions\n`);
  if (!missing.length) return { pool: "gold", missing: 0, success: 0, failed: 0 };

  let success = 0, fail = 0;

  for (const m of missing) {
    const amount = colsToAtomic((m.totalCols || m.amount).toString());
    try {
      const result = await callMcpTool("send-tokens", {
        receiver: m.address,
        tokenIdentifier: COLS_TOKEN_ID,
        amount
      });
      const text = result?.content?.[0]?.text || "";
      const txHash = text.match(/transactions\/([a-f0-9]+)/)?.[1] || "";
      m._txHash = txHash; m._verified = true;
      success++;
      console.log(`  ✅ ${m.address.slice(0, 14)}... → ${parseFloat(m.totalCols || m.amount).toFixed(4)} COLS`);
      await sleep(800);
    } catch (e) {
      fail++; m._error = e.message;
      console.log(`  ❌ ${m.address.slice(0, 14)}... → ${e.message}`);
    }
  }

  fs.writeFileSync(path.join(OUTPUT_DIR, files[0]), JSON.stringify(dist, null, 2));
  fs.writeFileSync(path.join(OUTPUT_DIR, "gold_missing_resent.json"),
    JSON.stringify({ pool: "gold", sent: success, failed: fail, recipients: missing }, null, 2));
  return { pool: "gold", missing: missing.length, success, fail };
}

async function retryDAO() {
  const files = fs.readdirSync(OUTPUT_DIR)
    .filter(f => f.startsWith("results_") && f.endsWith(".json"))
    .sort().reverse();
  if (!files.length) throw new Error("No results file found");
  const results = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, files[0]), "utf8"));
  const daoHash = results.dao?.hash || results.dao?.tx;
  console.log(`\nDAO: current hash = ${daoHash || "none"}`);

  if (daoHash) {
    console.log("DAO: already has hash, skipping (verify on-chain separately)");
    return { pool: "dao", status: "skipped" };
  }

  const amount = colsToAtomic((results.dao?.amount || results.dao?.totalCols || 0).toString());
  if (!amount || amount === "0") return { pool: "dao", status: "no_amount" };

  try {
    // DAO uses the same ESDT transfer (claim is just a data field)
    const result = await callMcpTool("send-tokens", {
      receiver: PEERME_CLAIM,
      tokenIdentifier: COLS_TOKEN_ID,
      amount
    });
    const text = result?.content?.[0]?.text || "";
    const txHash = text.match(/transactions\/([a-f0-9]+)/)?.[1] || "";
    fs.writeFileSync(path.join(OUTPUT_DIR, "dao_retry_result.json"),
      JSON.stringify({ hash: txHash, confirmed: false, amount }, null, 2));
    console.log(`DAO: ✅ sent ${results.dao?.amount || results.dao?.totalCols} COLS → ${txHash}`);
    return { pool: "dao", status: "sent", hash: txHash };
  } catch (e) {
    return { pool: "dao", status: "error", error: e.message };
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function run() {
  const pool = process.argv.includes("--pool")
    ? process.argv[process.argv.indexOf("--pool") + 1]
    : "bonus";

  console.log("\n" + "═".repeat(60));
  console.log(`Missing distributions: ${pool}`);
  console.log("═".repeat(60));

  let result;
  if (pool === "bonus") result = await sendMissingBonus();
  else if (pool === "gold") result = await sendMissingGold();
  else if (pool === "dao") result = await retryDAO();
  else { console.error("Unknown pool:", pool); process.exit(1); }

  console.log("═".repeat(60));
  console.log("Result:", JSON.stringify(result));
  process.exit(0);
}

run().catch(e => { console.error(e); process.exit(1); });