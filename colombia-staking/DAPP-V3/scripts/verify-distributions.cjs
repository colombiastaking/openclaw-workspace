/**
 * verify-distributions.cjs
 * 
 * Phase 1 of AI-powered distribution:
 * - Reads from distribution JSONs + resent tracking files
 * - For recipients WITHOUT recorded txs: checks blockchain directly
 * - Outputs confirmed / failed / needs-send lists
 *
 * Usage:
 *   node verify-distributions.cjs --pool bonus
 *   node verify-distributions.cjs --pool gold
 *   node verify-distributions.cjs --pool dao
 */

const fs = require("fs");
const path = require("path");
const https = require("https");

const OUTPUT_DIR = "/tmp/cols_distribution";
const API_BASE = "https://api.multiversx.com";
const COLS_TOKEN_ID = "COLS-9d91b7";
const WALLET = "erd1rk378updsudf9vqz98hartfwrkguvpk74jzjpygztlm8nukuqmkqfjk5pt";

function apiGet(path) {
  return new Promise((resolve, reject) => {
    const url = new URL(`${API_BASE}${path}`);
    const opts = { hostname: url.hostname, port: 443, path: url.pathname, method: "GET" };
    https.get(opts, res => {
      let d = ""; res.on("data", c => d += c);
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    }).on("error", reject);
  });
}

async function verifyTx(hash) {
  if (!hash || hash === "unknown") return false;
  try {
    const r = await apiGet(`/transactions/${hash}`);
    return r?.status === "success" || r?.status === "executed";
  } catch { return false; }
}

async function checkReceivedTokens(address) {
  try {
    // Only count transfers received TODAY (distribution date)
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    const r = await apiGet(`/accounts/${address}/transfers?token=${COLS_TOKEN_ID}&sender=${WALLET}&size=50`);
    const transfers = r?.data?.transfers || [];
    const fromUs = transfers.filter(t => {
      // Convert Unix timestamp to YYYY-MM-DD (API returns seconds, timestampMs if present)
      const ts = t.timestamp || t.date || '';
      let txDate;
      if (typeof ts === 'number') {
        txDate = new Date(ts * (ts > 1e12 ? 1 : 1000)).toISOString().split('T')[0];
      } else if (typeof ts === 'string' && ts.includes('T')) {
        txDate = ts.split('T')[0];
      } else {
        txDate = ts;
      }
      if (txDate !== today) return false; // Only today's transfers
      return t.sender === WALLET || t.from === WALLET ||
        (t.transfers && t.transfers.some(t2 =>
          (t2.sender === WALLET || t2.from === WALLET) && t2.tokenIdentifier === COLS_TOKEN_ID));
    });
    return fromUs.length > 0 ? fromUs[0] : null;
  } catch { return null; }
}

async function verifyBonus() {
  // Check resent file first (today's retry batch has the actual tx hashes)
  const resentFile = path.join(OUTPUT_DIR, "bonus_missing_resent.json");
  const resentExists = fs.existsSync(resentFile);
  const resent = resentExists
    ? JSON.parse(fs.readFileSync(resentFile, "utf8"))
    : { recipients: [] };

  const distFiles = fs.readdirSync(OUTPUT_DIR)
    .filter(f => f.startsWith("bonus_distribution_") && f.endsWith(".json"))
    .sort().reverse();
  const dist = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, distFiles[0]), "utf8"));
  const original = dist.bonus?.recipients || [];

  console.log(`\nBONUS: ${original.length} recipients in distribution`);
  if (resentExists) console.log(`BONUS: ${resent.recipients.length} in resent batch`);

  // Build map of address → tx info from resent file
  const resentMap = {};
  for (const r of resent.recipients) {
    if (r._txHash) resentMap[r.address.toLowerCase()] = r._txHash;
  }
  console.log(`BONUS: ${Object.keys(resentMap).length} have tx hashes in resent file`);
  console.log("═".repeat(60));

  const confirmed = [], failed = [], needsSend = [];

  for (const r of original) {
    const addr = r.address.toLowerCase();
    const amount = parseFloat(r.amount);

    if (resentMap[addr]) {
      // Has a recorded tx from resent batch
      const ok = await verifyTx(resentMap[addr]);
      if (ok) {
        confirmed.push({ address: r.address, amount, tx: resentMap[addr], source: "resent-onchain" });
      } else {
        failed.push({ address: r.address, amount, tx: resentMap[addr], source: "resent-failed" });
        needsSend.push({ address: r.address, amount });
      }
    } else {
      // No resent tx — check original dist for tx field, or check blockchain
      if (r.tx) {
        const ok = await verifyTx(r.tx);
        if (ok) {
          confirmed.push({ address: r.address, amount, tx: r.tx, source: "original-onchain" });
        } else {
          failed.push({ address: r.address, amount, tx: r.tx, source: "original-failed" });
          needsSend.push({ address: r.address, amount });
        }
      } else {
        // No recorded tx — check if tokens actually arrived on-chain
        const received = await checkReceivedTokens(r.address);
        if (received) {
          const txHash = received.txHash || received.hash || "unknown";
          confirmed.push({ address: r.address, amount, tx: txHash, source: "blockchain-check" });
        } else {
          needsSend.push({ address: r.address, amount });
        }
      }
    }
  }

  console.log(`✅ Confirmed: ${confirmed.length}`);
  console.log(`❌ Failed on-chain: ${failed.length}`);
  console.log(`📤 Needs sending: ${needsSend.length}`);
  console.log("═".repeat(60));

  const summary = {
    pool: "bonus",
    total: original.length,
    confirmed: confirmed.length,
    failed: failed.length,
    needsSend: needsSend.length,
    confirmedAddresses: confirmed.map(c => c.address),
    failedAddresses: failed.map(f => f.address),
    needsSendAddresses: needsSend
  };
  fs.writeFileSync(path.join(OUTPUT_DIR, "bonus_verification.json"), JSON.stringify(summary, null, 2));
  console.log("Saved: bonus_verification.json\n");
  return summary;
}

async function verifyGold() {
  const resentFile = path.join(OUTPUT_DIR, "gold_missing_resent.json");
  const resentExists = fs.existsSync(resentFile);
  const resent = resentExists ? JSON.parse(fs.readFileSync(resentFile, "utf8")) : { recipients: [] };

  const distFiles = fs.readdirSync(OUTPUT_DIR)
    .filter(f => f.startsWith("gold_distribution_") && f.endsWith(".json"))
    .sort().reverse();
  const dist = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, distFiles[0]), "utf8"));
  const original = dist.recipients || dist.gold?.recipients || [];

  console.log(`\nGOLD: ${original.length} recipients in distribution`);
  if (resentExists) console.log(`GOLD: ${resent.recipients.length} in resent batch`);

  const resentMap = {};
  for (const r of resent.recipients) {
    if (r._txHash) resentMap[r.address.toLowerCase()] = r._txHash;
  }
  console.log(`GOLD: ${Object.keys(resentMap).length} have tx hashes in resent file`);
  console.log("═".repeat(60));

  const confirmed = [], failed = [], needsSend = [];

  for (const r of original) {
    const addr = r.address.toLowerCase();
    const amount = parseFloat(r.totalCols || r.amount);

    if (resentMap[addr]) {
      const ok = await verifyTx(resentMap[addr]);
      if (ok) confirmed.push({ address: r.address, amount, tx: resentMap[addr], source: "resent-onchain" });
      else { failed.push({ address: r.address, amount, tx: resentMap[addr], source: "resent-failed" }); needsSend.push({ address: r.address, amount }); }
    } else {
      if (r.tx) {
        const ok = await verifyTx(r.tx);
        if (ok) confirmed.push({ address: r.address, amount, tx: r.tx, source: "original-onchain" });
        else { failed.push({ address: r.address, amount, tx: r.tx, source: "original-failed" }); needsSend.push({ address: r.address, amount }); }
      } else {
        const received = await checkReceivedTokens(r.address);
        if (received) {
          confirmed.push({ address: r.address, amount, tx: received.txHash || "unknown", source: "blockchain-check" });
        } else {
          needsSend.push({ address: r.address, amount });
        }
      }
    }
  }

  console.log(`✅ Confirmed: ${confirmed.length}`);
  console.log(`❌ Failed on-chain: ${failed.length}`);
  console.log(`📤 Needs sending: ${needsSend.length}`);
  console.log("═".repeat(60));

  const summary = { pool: "gold", total: original.length, confirmed: confirmed.length, failed: failed.length, needsSend: needsSend.length, needsSendAddresses: needsSend };
  fs.writeFileSync(path.join(OUTPUT_DIR, "gold_verification.json"), JSON.stringify(summary, null, 2));
  console.log("Saved: gold_verification.json\n");
  return summary;
}

async function verifyDAO() {
  const files = fs.readdirSync(OUTPUT_DIR)
    .filter(f => f.startsWith("results_") && f.endsWith(".json"))
    .sort().reverse();
  if (!files.length) throw new Error("No results file found");
  const results = JSON.parse(fs.readFileSync(path.join(OUTPUT_DIR, files[0]), "utf8"));
  const daoHash = results.dao?.hash || results.dao?.tx;
  console.log(`\nDAO: hash = ${daoHash || "none"}`);

  if (daoHash) {
    const ok = await verifyTx(daoHash);
    console.log(`DAO: ${ok ? "✅ confirmed on-chain" : "❌ not confirmed"}`);
    const summary = { pool: "dao", hash: daoHash, confirmed: ok };
    fs.writeFileSync(path.join(OUTPUT_DIR, "dao_verification.json"), JSON.stringify(summary, null, 2));
    return summary;
  }
  console.log("DAO: no hash, needs sending");
  return { pool: "dao", hash: null, needsSend: true };
}

async function run() {
  const pool = process.argv.includes("--pool")
    ? process.argv[process.argv.indexOf("--pool") + 1]
    : "bonus";

  console.log("\n" + "═".repeat(60));
  console.log(`Verifying: ${pool}`);
  console.log("═".repeat(60));

  let result;
  if (pool === "bonus") result = await verifyBonus();
  else if (pool === "gold") result = await verifyGold();
  else if (pool === "dao") result = await verifyDAO();
  else { console.error("Unknown pool:", pool); process.exit(1); }

  console.log("\nResult:", JSON.stringify(result));
  process.exit(0);
}

run().catch(e => { console.error(e); process.exit(1); });