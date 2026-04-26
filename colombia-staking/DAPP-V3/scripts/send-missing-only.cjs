/**
 * send-missing-only.cjs
 * 
 * Phase 2 of AI-powered distribution:
 * - Reads needsSend list from verify-distributions output
 * - Sends ONLY addresses that genuinely failed/didn't receive
 * - Uses MCP send-tokens via raw JSON-RPC (no CLI coercion)
 * - 800ms delay between sends to avoid rate limiting
 *
 * Usage:
 *   node send-missing-only.cjs --pool bonus
 *   node send-missing-only.cjs --pool gold
 *   node send-missing-only.cjs --pool dao
 */

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const OUTPUT_DIR = "/tmp/cols_distribution";
const MCP_PATH = "/home/raspberry/.openclaw/workspace/alice-mcp-multiversx/dist/index.js";
const COLS_TOKEN_ID = "COLS-9d91b7";
const PEERME_CLAIM = "erd1qqqqqqqqqqqqqpgqjhn0rrta3hceyguqlmkqgklxc0eh0r5rl3tsv6a9k0";

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
      env: { ...process.env, MVX_NETWORK: "mainnet", MVX_SIGNING_MODE: "pem", MVX_WALLET_PEM: "/home/raspberry/.openclaw/wallet/.private_key" }
    });
    let stdout = "", stderr = "";
    child.stdout.on("data", d => stdout += d);
    child.stderr.on("data", d => stderr += d);
    child.on("error", reject);
    child.on("close", () => {
      const lines = stdout.trim().split("\n").filter(Boolean);
      try {
        const response = JSON.parse(lines[lines.length - 1] || "{}");
        if (response.error) { reject(new Error(response.error.message || JSON.stringify(response.error))); return; }
        resolve(response.result || response);
      } catch { reject(new Error(`MCP parse: ${stdout.slice(0, 200)}`)); }
    });
    child.stdin.write(JSON.stringify(request) + "\n");
    child.stdin.end();
  });
}

const sleep = ms => new Promise(s => setTimeout(s, ms));

function colsToAtomic(amount) {
  return BigInt(Math.floor(parseFloat(amount) * 1e18)).toString();
}

async function sendBonus() {
  const vFile = path.join(OUTPUT_DIR, "bonus_verification.json");
  if (!fs.existsSync(vFile)) { console.error("Run verify-distributions.cjs first"); process.exit(1); }
  const v = JSON.parse(fs.readFileSync(vFile, "utf8"));
  const needs = v.needsSendAddresses || [];
  console.log(`\nBONUS: ${needs.length} addresses need sending`);
  if (!needs.length) return { pool: "bonus", sent: 0 };

  const log = [];
  for (const item of needs) {
    const addr = typeof item === "string" ? item : item.address;
    const amount = typeof item === "string" ? null : item.amount;
    if (!amount) continue;
    const atomic = colsToAtomic(amount);
    try {
      const result = await callMcpTool("send-tokens", { receiver: addr, tokenIdentifier: COLS_TOKEN_ID, amount: atomic });
      const text = result?.content?.[0]?.text || "";
      const txHash = text.match(/transactions\/([a-f0-9]+)/)?.[1] || "unknown";
      log.push({ address: addr, amount, tx: txHash, status: "sent" });
      console.log(`  ✅ ${addr.slice(0, 14)}... → ${amount.toFixed(4)} COLS`);
      await sleep(800);
    } catch (e) {
      log.push({ address: addr, amount, error: e.message, status: "failed" });
      console.log(`  ❌ ${addr.slice(0, 14)}... → ${e.message}`);
    }
  }
  fs.writeFileSync(path.join(OUTPUT_DIR, "bonus_resent.json"), JSON.stringify({ pool: "bonus", log }, null, 2));
  return { pool: "bonus", total: needs.length, sent: log.filter(l => l.status === "sent").length, failed: log.filter(l => l.status === "failed").length };
}

async function sendGold() {
  const vFile = path.join(OUTPUT_DIR, "gold_verification.json");
  if (!fs.existsSync(vFile)) { console.error("Run verify-distributions.cjs first"); process.exit(1); }
  const v = JSON.parse(fs.readFileSync(vFile, "utf8"));
  const needs = v.needsSendAddresses || [];
  console.log(`\nGOLD: ${needs.length} addresses need sending`);
  if (!needs.length) return { pool: "gold", sent: 0 };

  const log = [];
  for (const item of needs) {
    const addr = typeof item === "string" ? item : item.address;
    const amount = typeof item === "string" ? null : item.amount;
    if (!amount) continue;
    const atomic = colsToAtomic(amount);
    try {
      const result = await callMcpTool("send-tokens", { receiver: addr, tokenIdentifier: COLS_TOKEN_ID, amount: atomic });
      const text = result?.content?.[0]?.text || "";
      const txHash = text.match(/transactions\/([a-f0-9]+)/)?.[1] || "unknown";
      log.push({ address: addr, amount, tx: txHash, status: "sent" });
      console.log(`  ✅ ${addr.slice(0, 14)}... → ${amount.toFixed(4)} COLS`);
      await sleep(800);
    } catch (e) {
      log.push({ address: addr, amount, error: e.message, status: "failed" });
      console.log(`  ❌ ${addr.slice(0, 14)}... → ${e.message}`);
    }
  }
  fs.writeFileSync(path.join(OUTPUT_DIR, "gold_resent.json"), JSON.stringify({ pool: "gold", log }, null, 2));
  return { pool: "gold", total: needs.length, sent: log.filter(l => l.status === "sent").length, failed: log.filter(l => l.status === "failed").length };
}

async function sendDAO() {
  const vFile = path.join(OUTPUT_DIR, "dao_verification.json");
  if (!fs.existsSync(vFile)) { console.error("Run verify-distributions.cjs first"); process.exit(1); }
  const v = JSON.parse(fs.readFileSync(vFile, "utf8"));
  if (!v.needsSend) { console.log("\nDAO: already confirmed"); return { pool: "dao", status: "confirmed" }; }

  const rFile = path.join(OUTPUT_DIR, "results_dao.json") || fs.readdirSync(OUTPUT_DIR).filter(f => f.startsWith("results_") && f.endsWith(".json")).sort().reverse()[0];
  const results = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, fs.readdirSync(OUTPUT_DIR).filter(f => f.startsWith("results_") && f.endsWith(".json")).sort().reverse()[0]), "utf8"));
  const amount = colsToAtomic(results.dao?.amount || results.dao?.totalCols || 0);
  console.log(`\nDAO: sending ${amount} atomic units`);

  try {
    const result = await callMcpTool("send-tokens", { receiver: PEERME_CLAIM, tokenIdentifier: COLS_TOKEN_ID, amount });
    const text = result?.content?.[0]?.text || "";
    const txHash = text.match(/transactions\/([a-f0-9]+)/)?.[1] || "unknown";
    console.log(`DAO: ✅ sent → ${txHash}`);
    fs.writeFileSync(path.join(OUTPUT_DIR, "dao_resent.json"), JSON.stringify({ pool: "dao", txHash }, null, 2));
    return { pool: "dao", status: "sent", txHash };
  } catch (e) {
    console.log(`DAO: ❌ ${e.message}`);
    return { pool: "dao", status: "error", error: e.message };
  }
}

async function run() {
  const pool = process.argv.includes("--pool") ? process.argv[process.argv.indexOf("--pool") + 1] : "bonus";
  console.log("\n" + "═".repeat(60));
  console.log(`Sending missing: ${pool}`);
  console.log("═".repeat(60));

  let result;
  if (pool === "bonus") result = await sendBonus();
  else if (pool === "gold") result = await sendGold();
  else if (pool === "dao") result = await sendDAO();
  else { console.error("Unknown pool:", pool); process.exit(1); }

  console.log("═".repeat(60));
  console.log("Result:", JSON.stringify(result));
  process.exit(0);
}

run().catch(e => { console.error(e); process.exit(1); });