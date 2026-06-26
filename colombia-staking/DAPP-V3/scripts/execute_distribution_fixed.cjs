/**
 * COLS Distribution Scripts - FIXED VERSION with On-Chain Verification
 *
 * FIXES over original:
 * 1. Verifies txHash is valid before marking success
 * 2. Awaits transaction confirmation (not just broadcast)
 * 3. Verifies each transaction on-chain before counting as success
 * 4. Handles failures properly with retry logic
 * 5. Batches transactions and verifies in groups to avoid rate limits
 *
 * TWO POOLS:
 * 1. DAO POOL (1/3 of buyback): ONE transaction to PeerMe contract
 * 2. BONUS POOL (2/3 of buyback): Individual ESDT transfers
 */

const fs = require("fs");
const sdk = require("@multiversx/sdk-core");
const { ProxyNetworkProvider } = require("@multiversx/sdk-network-providers");
const { UserSecretKey } = require("@multiversx/sdk-wallet");

const { Address, Transaction, TransactionComputer } = sdk;

// Configuration
const NETWORK_PROVIDER = "https://gateway.multiversx.com";
const CHAIN_ID = "1";
const PEERME_CLAIM_CONTRACT = "erd1qqqqqqqqqqqqqpgqjhn0rrta3hceyguqlmkqgklxc0eh0r5rl3tsv6a9k0";
const COLOMBIA_ENTITY = "erd1qqqqqqqqqqqqqpgq7khr5sqd4cnjh5j5dz0atfz03r3l99y727rsulfjj0";
const COLS_TOKEN_ID = "COLS-9d91b7";

// Gas limits
const GAS_ESDT_TRANSFER = 600000;
const GAS_DAO_DISTRIBUTE = 10000000;

// Verification settings - INCREASED for reliability
const CONFIRMATION_WAIT_MS = 60000;  // Wait 60 seconds for tx confirmation
const DAO_CONFIRMATION_WAIT_MS = 300000;  // PeerMe contract is slow - increased from 180s to 300s
const VERIFICATION_TIMEOUT_MS = 300000;  // Max time to wait for confirmation
const MAX_RETRIES = 3;  // Number of retries for failed transactions
const DAO_MAX_RETRIES = 5;  // More retries for DAO (PeerMe contract is slower)
const BATCH_SIZE = 50;  // Process and verify in batches

// State file
const STATE_FILE = "/tmp/cols_distribution/state.json";

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
    }
  } catch (e) {}
  return { lastDistributionDate: null, lastDaoHash: null, lastBonusCount: 0, nonce: null };
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function colsToHex(amount) {
  let hex = BigInt(Math.floor(amount * 1e18)).toString(16);
  if (hex.length % 2 !== 0) hex = '0' + hex;
  return hex;
}

function stringToHex(str) {
  return Buffer.from(str).toString('hex');
}

function loadWallet() {
  const keyHex = fs.readFileSync('/home/raspberry/.openclaw/wallet/.private_key', 'utf-8').trim();
  return UserSecretKey.fromString(keyHex);
}

function loadDistribution() {
  const files = fs.readdirSync('/tmp/cols_distribution')
    .filter(f => f.startsWith('bonus_distribution_'))
    .sort()
    .reverse();
  if (files.length === 0) {
    throw new Error('No distribution file found');
  }
  return JSON.parse(fs.readFileSync(`/tmp/cols_distribution/${files[0]}`, 'utf-8'));
}

/**
 * Sign and send transaction with proper error handling
 */
async function signTransaction(tx, secretKey, provider) {
  const transactionComputer = new TransactionComputer();
  const serializedTx = transactionComputer.computeBytesForSigning(tx);
  const signature = secretKey.sign(serializedTx);
  tx.signature = signature;

  // Send and get hash
  const txHash = await provider.sendTransaction(tx);

  // BUG FIX #1: Verify txHash is valid
  if (!txHash || txHash === 'undefined' || txHash === 'null') {
    throw new Error(`Invalid txHash returned: ${txHash}`);
  }

  return txHash.toString();
}

/**
 * Wait for transaction to be confirmed on-chain
 */
async function waitForConfirmation(provider, txHash, timeoutMs = VERIFICATION_TIMEOUT_MS) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeoutMs) {
    try {
      const txStatus = await provider.getTransaction(txHash);

      if (txStatus.status.isExecuted()) {
        return { confirmed: true, status: 'executed' };
      }

      if (txStatus.status.isFailed()) {
        return { confirmed: false, status: 'failed' };
      }

      if (txStatus.status.isPending()) {
        // Still pending, wait a bit more
        await new Promise(r => setTimeout(r, 2000));
        continue;
      }

    } catch (e) {
      // Transaction not found yet, wait and retry
      if (e.message.includes('transaction not found') || e.message.includes('404')) {
        await new Promise(r => setTimeout(r, 2000));
        continue;
      }
      // Some other error, throw it
      throw e;
    }
  }

  // Timeout reached
  return { confirmed: false, status: 'timeout' };
}

/**
 * Send and verify a single transaction
 */
async function sendAndVerify(provider, tx, secretKey, recipientInfo, maxRetries = MAX_RETRIES, timeoutMs = CONFIRMATION_WAIT_MS) {
  let lastError = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Sign and send
      const txHash = await signTransaction(tx, secretKey, provider);
      console.log(`     📤 Hash: ${txHash.slice(0, 12)}... (attempt ${attempt})`);

      // Wait for confirmation
      const result = await waitForConfirmation(provider, txHash, timeoutMs);

      if (result.confirmed) {
        return { success: true, txHash, confirmed: true };
      }

      // Transaction not confirmed
      if (result.status === 'timeout') {
        console.log(`     ⏳ Timeout waiting for confirmation`);
        lastError = new Error('Transaction confirmation timeout');
      } else if (result.status === 'failed') {
        console.log(`     ❌ Transaction failed on-chain`);
        lastError = new Error('Transaction failed on-chain');
      }

      // If timeout, do a final on-chain check before giving up
      if (result.status === 'timeout') {
        try {
          const finalStatus = await provider.getTransaction(txHash);
          if (finalStatus.status.isExecuted()) {
            console.log(`     ✅ Transaction actually succeeded on-chain (confirmed after timeout)`);
            return { success: true, txHash, confirmed: true };
          }
        } catch (e) {}
      }

      // If failed, don't retry - it won't help
      break;

    } catch (e) {
      lastError = e;
      console.log(`     ❌ Error: ${e.message}`);

      // If it's a nonce error, don't retry - the nonce is likely stale
      if (e.message.includes('nonce') || e.message.includes('Guardian')) {
        break;
      }
    }

    // Wait before retry
    if (attempt < maxRetries) {
      console.log(`     🔄 Retrying in 3s...`);
      await new Promise(r => setTimeout(r, 3000));
    }
  }

  return { success: false, error: lastError?.message || 'Unknown error', confirmed: false };
}

async function main() {
  const args = process.argv.slice(2);
  const doDao = args.includes('--dao') || args.includes('--all');
  const doBonus = args.includes('--bonus') || args.includes('--all');
  const doGold = args.includes('--gold') || args.includes('--all-gold');
  const force = args.includes('--force');

  const state = loadState();
  const today = new Date().toISOString().slice(0, 10);

  if (!force && state.lastDistributionDate === today) {
    console.log(`⚠️  Distribution already executed today: ${today}`);
    console.log(`   Use --force to re-run`);
    process.exit(0);
  }

  console.log("═".repeat(70));
  console.log("🚀 COLS DISTRIBUTION - FIXED VERSION WITH VERIFICATION");
  console.log("═".repeat(70));
  console.log(`Time: ${new Date().toISOString()}`);
  console.log(`Verification: Waiting ${CONFIRMATION_WAIT_MS/1000}s for on-chain confirmation`);
  console.log("");

  // Setup
  const provider = new ProxyNetworkProvider(NETWORK_PROVIDER, {
    timeout: 30000,
    clientName: "cols-distribution-fixed"
  });
  const secretKey = loadWallet();
  const senderPublicKey = secretKey.generatePublicKey();
  const senderAddress = new Address(senderPublicKey.valueOf());
  const senderAddressForProvider = senderPublicKey.toAddress();

  console.log(`Wallet: ${senderAddress.toBech32()}`);

  // Get fresh nonce
  const account = await provider.getAccount(senderAddressForProvider);
  console.log(`Current Nonce: ${account.nonce}`);
  console.log(`Balance: ${Number(account.balance) / 1e18} EGLD`);
  console.log("");

  // Load distribution
  const dist = loadDistribution();
  const bonusRecipients = dist.bonus.recipients;
  const totalBonus = dist.bonus.totalBonus;
  const totalBuyback = totalBonus / 0.667;
  const daoAmount = totalBuyback * 0.333;

  console.log("📊 Distribution Summary:");
  console.log(`   DAO Pool: ${daoAmount.toFixed(6)} COLS → PeerMe contract`);
  console.log(`   BONUS Pool: ${totalBonus.toFixed(6)} COLS → ${bonusRecipients.length} addresses`);
  console.log("");

  // Initialize results early (used in deduplication below, defined properly later)
  const resultsFile = `/tmp/cols_distribution/results_${today}.json`;
  const existing = (force && fs.existsSync(resultsFile)) ? JSON.parse(fs.readFileSync(resultsFile, 'utf-8')) : null;
  const results = { dao: null, bonus: existing?.bonus || [], gold: existing?.gold || [] };

  // ─── DEDUPLICATION: Check who already received COLS today ───
  const alreadyPaid = new Set(results.bonus.map(r => r.address.toLowerCase()));
  console.log(`   Already paid today (from results): ${alreadyPaid.size}`);

  // Also check on-chain for any addresses that might have been paid by a previous script run
  const toSkip = new Set();
  if (bonusRecipients.length > alreadyPaid.size) {
    console.log(`   Checking on-chain for additional duplicates...`);
    for (const recipient of bonusRecipients) {
      if (alreadyPaid.has(recipient.address.toLowerCase())) continue;
      try {
        const todayStr = new Date().toISOString().split('T')[0];
        const apiUrl = `https://api.multiversx.com/accounts/${recipient.address}/transfers?token=${COLS_TOKEN_ID}&sender=erd1rk378updsudf9vqz98hartfwrkguvpk74jzjpygztlm8nukuqmkqfjk5pt&size=50`;
        // Retry logic for API calls (handle 429 rate limits)
        const MAX_RETRIES = 5;
        let resp = null;
        for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
          resp = await fetch(apiUrl);
          if (resp.ok) break;
          if (resp.status === 429 && attempt < MAX_RETRIES - 1) {
            const waitMs = Math.min(2000 * Math.pow(2, attempt), 10000);
            console.warn(`   ⏳ Rate limited, retrying in ${waitMs}ms... (attempt ${attempt + 1}/${MAX_RETRIES})`);
            await new Promise(r => setTimeout(r, waitMs));
            continue;
          }
          break;
        }
        
        if (resp && resp.ok) {
          const data = await resp.json();
          const receivedToday = (Array.isArray(data) ? data : (data.data || [])).some(t => {
            const ts = t.timestamp || t.date || '';
            const date = typeof ts === 'number' ? new Date(ts > 1e12 ? ts : ts * 1000).toISOString().split('T')[0] : (typeof ts === 'string' && ts.includes('T') ? ts.split('T')[0] : ts);
            return date === todayStr;
          });
          if (receivedToday) {
            toSkip.add(recipient.address);
          }
        } else if (!resp.ok) {
          // API returned non-OK - be conservative, skip to avoid double-pay
          toSkip.add(recipient.address);
          console.warn(`   ⚠ API error for ${recipient.address.slice(0,12)}... (${resp.status}) - SKIPPING`);
        }
        // On-chain check - be conservative: if check fails, skip to avoid double-pay
      } catch (e) {
        // Could not verify - SKIP to avoid double-sending
        toSkip.add(recipient.address);
        console.warn(`   ⚠ Check failed for ${recipient.address.slice(0,12)}... - SKIPPING (cannot verify)`);
      }
    }
    console.log(`   On-chain duplicates found: ${toSkip.size}`);
  }

  // Filter out already-paid recipients
  const recipientsToPay = bonusRecipients.filter(r => !alreadyPaid.has(r.address.toLowerCase()) && !toSkip.has(r.address));
  console.log(`   Recipients to pay: ${recipientsToPay.length} (skipping ${alreadyPaid.size + toSkip.size} already paid)`);
  console.log("");

  let nonce = Number(account.nonce);
  
  // =============================================
  // DAO DISTRIBUTION
  // =============================================
  if (doDao) {
    console.log("═".repeat(70));
    console.log("🔴 DAO POOL");
    console.log("═".repeat(70));

    // Re-fetch nonce AFTER BONUS+GOLD completed (they use sequential nonces starting from account.nonce)
    nonce = Number((await provider.getAccount(senderAddressForProvider)).nonce);
    console.log(`DAO using fresh nonce: ${nonce}`);
    const functionHex = stringToHex("distribute");
    const entityHex = new Address(COLOMBIA_ENTITY).getPublicKey().toString('hex');
    const data = `ESDTTransfer@${stringToHex(COLS_TOKEN_ID)}@${colsToHex(daoAmount)}@${functionHex}@${entityHex}`;

    const daoTx = new Transaction({
      sender: senderAddress,
      receiver: new Address(PEERME_CLAIM_CONTRACT),
      value: 0n,
      gasLimit: BigInt(GAS_DAO_DISTRIBUTE),
      chainID: CHAIN_ID,
      nonce: BigInt(nonce),
      data: Buffer.from(data)
    });

    console.log(`Sending DAO transaction (nonce ${nonce})...`);

    // For retries with fresh nonce, create a helper function
    async function sendDaoWithRetry(provider, secretKey, daoAmount, maxRetries, timeoutMs) {
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        // Get fresh nonce for each attempt (critical for retries!)
        const currentNonce = Number((await provider.getAccount(senderAddressForProvider)).nonce);
        console.log(`   DAO attempt ${attempt}: nonce ${currentNonce}`);

        const data = `ESDTTransfer@${stringToHex(COLS_TOKEN_ID)}@${colsToHex(daoAmount)}@${functionHex}@${entityHex}`;
        const daoTx = new Transaction({
          sender: senderAddress,
          receiver: new Address(PEERME_CLAIM_CONTRACT),
          value: 0n,
          gasLimit: BigInt(GAS_DAO_DISTRIBUTE),
          chainID: CHAIN_ID,
          nonce: BigInt(currentNonce),
          data: Buffer.from(data)
        });

        const result = await sendAndVerify(provider, daoTx, secretKey, { address: PEERME_CLAIM_CONTRACT, amount: daoAmount }, 1, timeoutMs); // 1 retry per attempt (nonce refresh handles actual retries)

        if (result.success) return result;

        console.log(`   ⏳ Timeout, retrying with fresh nonce...`);
        await new Promise(r => setTimeout(r, 5000)); // Wait 5s before retry
      }
      return { success: false, error: 'DAO failed after all retries' };
    }

    const result = await sendDaoWithRetry(provider, secretKey, daoAmount, DAO_MAX_RETRIES, DAO_CONFIRMATION_WAIT_MS);

    if (result.success) {
      console.log(`✅ DAO Transaction CONFIRMED: ${result.txHash}`);
      results.dao = { hash: result.txHash, amount: daoAmount };
      nonce++;
    } else {
      console.error(`❌ DAO Transaction FAILED: ${result.error}`);
      throw new Error(`DAO distribution failed: ${result.error}`);
    }

    await new Promise(r => setTimeout(r, 2000));
  }

  // =============================================
  // BONUS DISTRIBUTION WITH BATCH VERIFICATION
  // =============================================
  if (doBonus) {
    console.log("");
    console.log("═".repeat(70));
    console.log("🟢 BONUS POOL - Sending and verifying in batches");
    console.log("═".repeat(70));
    console.log(`Recipients: ${bonusRecipients.length}`);
    console.log(`Batch size: ${BATCH_SIZE}`);
    console.log(`Confirmation wait: ${CONFIRMATION_WAIT_MS/1000}s per batch`);
    console.log("");

    let successCount = 0;
    let failCount = 0;
    let pendingBatch = [];

    for (let i = 0; i < recipientsToPay.length; i++) {
      const recipient = recipientsToPay[i];

      const data = `ESDTTransfer@${stringToHex(COLS_TOKEN_ID)}@${colsToHex(recipient.amount)}`;
      const tx = new Transaction({
        sender: senderAddress,
        receiver: new Address(recipient.address),
        value: 0n,
        gasLimit: BigInt(GAS_ESDT_TRANSFER),
        chainID: CHAIN_ID,
        nonce: BigInt(nonce),
        data: Buffer.from(data)
      });

      pendingBatch.push({ tx, recipient, nonce });
      nonce++;

      // When batch is full or we're at the end, verify all
      if (pendingBatch.length >= BATCH_SIZE || i === recipientsToPay.length - 1) {
        console.log(`\n📦 Verifying batch of ${pendingBatch.length} transactions...`);

        // Send all in batch first
        const sent = [];
        for (const item of pendingBatch) {
          try {
            const txHash = await signTransaction(item.tx, secretKey, provider);
            sent.push({ ...item, txHash });
            console.log(`  📤 ${item.recipient.address.slice(0,12)}... → ${txHash.slice(0,8)}...`);
          } catch (e) {
            console.error(`  ❌ ${item.recipient.address.slice(0,12)}... → ${e.message}`);
            failCount++;
          }
        }

        // Wait for confirmations
        if (sent.length > 0) {
          console.log(`  ⏳ Waiting ${CONFIRMATION_WAIT_MS/1000}s for first confirmation...`);
          await new Promise(r => setTimeout(r, CONFIRMATION_WAIT_MS));

          // Verify each - collect failed/pending ones
          const needsRetry = [];
          for (const item of sent) {
            try {
              const txStatus = await provider.getTransaction(item.txHash);

              if (txStatus.status.isExecuted()) {
                results.bonus.push({ hash: item.txHash, address: item.recipient.address, amount: item.recipient.amount });
                successCount++;
                console.log(`  ✅ ${item.txHash.slice(0,8)}... → CONFIRMED`);
              } else if (txStatus.status.isFailed()) {
                failCount++;
                console.error(`  ❌ ${item.txHash.slice(0,8)}... → FAILED on-chain`);
              } else {
                // Still pending - need retry with fresh nonce
                needsRetry.push(item);
                console.log(`  ⏳ ${item.txHash.slice(0,8)}... → PENDING (will retry)`);
              }
            } catch (e) {
              failCount++;
              console.error(`  ❌ ${item.txHash.slice(0,8)}... → VERIFICATION ERROR: ${e.message}`);
            }
          }

          // Retry pending TXs with fresh nonces (ON-CHAIN VERIFICATION BEFORE RETRY)
          if (needsRetry.length > 0) {
            console.log(`\n  🔄 Retrying ${needsRetry.length} pending transactions...`);
            const retryResults = [];

            for (const item of needsRetry) {
              try {
                // Get fresh nonce from blockchain
                const freshNonce = Number((await provider.getAccount(senderAddressForProvider)).nonce);

                // Create new TX with fresh nonce
                const retryData = `ESDTTransfer@${stringToHex(COLS_TOKEN_ID)}@${colsToHex(item.recipient.amount)}`;
                const retryTx = new Transaction({
                  sender: senderAddress,
                  receiver: new Address(item.recipient.address),
                  value: 0n,
                  gasLimit: BigInt(GAS_ESDT_TRANSFER),
                  chainID: CHAIN_ID,
                  nonce: BigInt(freshNonce),
                  data: Buffer.from(retryData)
                });

                const retryTxHash = await signTransaction(retryTx, secretKey, provider);
                console.log(`  📤 RETRY ${item.recipient.address.slice(0,12)}... → ${retryTxHash.slice(0,8)}... (nonce ${freshNonce})`);
                retryResults.push({ ...item, retryTxHash, freshNonce, freshNonce });
              } catch (e) {
                failCount++;
                console.error(`  ❌ RETRY FAILED: ${e.message}`);
              }
            }

            // Wait for retry confirmations
            if (retryResults.length > 0) {
              console.log(`  ⏳ Waiting ${CONFIRMATION_WAIT_MS/1000}s for retry confirmations...`);
              await new Promise(r => setTimeout(r, CONFIRMATION_WAIT_MS));

              // Verify each retry on-chain
              for (const item of retryResults) {
                try {
                  const txStatus = await provider.getTransaction(item.retryTxHash);

                  if (txStatus.status.isExecuted()) {
                    results.bonus.push({ hash: item.retryTxHash, address: item.recipient.address, amount: item.recipient.amount, originalHash: item.txHash });
                    successCount++;
                    console.log(`  ✅ RETRY ${item.retryTxHash.slice(0,8)}... → CONFIRMED ✅`);
                  } else if (txStatus.status.isFailed()) {
                    failCount++;
                    console.error(`  ❌ RETRY ${item.retryTxHash.slice(0,8)}... → FAILED on-chain`);
                  } else {
                    // Still pending after retry - give up and count as fail
                    failCount++;
                    console.error(`  ❌ RETRY ${item.retryTxHash.slice(0,8)}... → STILL PENDING after retry`);
                  }
                } catch (e) {
                  failCount++;
                  console.error(`  ❌ RETRY VERIFY ERROR: ${e.message}`);
                }
              }
            }
          }
        }

        // Clear batch
        pendingBatch = [];

        // Progress update
        console.log(`  📊 Progress: ${successCount} confirmed, ${failCount} failed (${i + 1}/${recipientsToPay.length})`);

        // Small delay between batches
        if (i < recipientsToPay.length - 1) {
          await new Promise(r => setTimeout(r, 1000));
        }
      }
    }

    console.log("");
    console.log(`BONUS Complete: ${successCount} confirmed, ${failCount} failed`);
  }

  // =============================================
  // GOLD DISTRIBUTION (similar verification)
  // =============================================
  if (doGold) {
    console.log("");
    console.log("═".repeat(70));
    console.log("🟡 GOLD POOL");
    console.log("═".repeat(70));

    const goldFile = `/tmp/cols_distribution/gold_distribution_latest.json`;

    if (!fs.existsSync(goldFile)) {
      console.log("⚠️ No GOLD distribution file found. Run calculate_gold_distribution.mjs first.");
    } else {
      const goldData = JSON.parse(fs.readFileSync(goldFile, 'utf-8'));
      const allGoldRecipients = goldData.recipients || [];

      // ─── DEDUPLICATION for GOLD ───
      const alreadyPaidGold = new Set(results.gold.map(r => r.address.toLowerCase()));
      const goldToSkip = new Set();
      if (allGoldRecipients.length > alreadyPaidGold.size) {
        console.log(`   Checking on-chain for GOLD duplicates (${alreadyPaidGold.size} already paid from results)...`);
        for (const recipient of allGoldRecipients) {
          if (alreadyPaidGold.has(recipient.address.toLowerCase())) continue;
          try {
            const todayStr = new Date().toISOString().split('T')[0];
            const apiUrl = `https://api.multiversx.com/accounts/${recipient.address}/transfers?token=${COLS_TOKEN_ID}&sender=erd1rk378updsudf9vqz98hartfwrkguvpk74jzjpygztlm8nukuqmkqfjk5pt&size=50`;
            const GOLD_MAX_RETRIES = 5;
            let resp = null;
            for (let attempt = 0; attempt < GOLD_MAX_RETRIES; attempt++) {
              resp = await fetch(apiUrl);
              if (resp.ok) break;
              if (resp.status === 429 && attempt < GOLD_MAX_RETRIES - 1) {
                const waitMs = Math.min(2000 * Math.pow(2, attempt), 10000);
                console.warn(`   ⏳ GOLD Rate limited, retrying in ${waitMs}ms... (${attempt+1}/${GOLD_MAX_RETRIES})`);
                await new Promise(r => setTimeout(r, waitMs));
                continue;
              }
              break;
            }
            if (resp && resp.ok) {
              const data = await resp.json();
              const receivedToday = (Array.isArray(data) ? data : (data.data || [])).some(t => {
                const ts = t.timestamp || t.date || '';
                const date = typeof ts === 'number' ? new Date(ts > 1e12 ? ts : ts * 1000).toISOString().split('T')[0] : (typeof ts === 'string' && ts.includes('T') ? ts.split('T')[0] : ts);
                return date === todayStr;
              });
              if (receivedToday) goldToSkip.add(recipient.address);
            } else if (!resp.ok) {
              // API returned non-OK - be conservative, skip to avoid double-pay
              goldToSkip.add(recipient.address);
              console.warn(`   ⚠ GOLD API error for ${recipient.address.slice(0,12)}... (${resp.status}) - SKIPPING`);
            }
          } catch (e) {
            // Could not verify - SKIP to avoid double-sending
            goldToSkip.add(recipient.address);
            console.warn(`   ⚠ GOLD check failed for ${recipient.address.slice(0,12)}... - SKIPPING`);
          }
        }
      }
      const goldRecipients = allGoldRecipients.filter(r => !alreadyPaidGold.has(r.address.toLowerCase()) && !goldToSkip.has(r.address));
      console.log(`   GOLD: ${goldRecipients.length} to pay (skipping ${alreadyPaidGold.size + goldToSkip.size} already paid)`);
      console.log(`Recipients: ${goldRecipients.length}`);
      console.log(`Batch size: ${BATCH_SIZE}`);

      let successCount = 0, failCount = 0, pendingBatch = [];

      for (let i = 0; i < goldRecipients.length; i++) {
        const recipient = goldRecipients[i];
        const data = `ESDTTransfer@${stringToHex(COLS_TOKEN_ID)}@${colsToHex(recipient.amount)}`;
        const tx = new Transaction({
          sender: senderAddress,
          receiver: new Address(recipient.address),
          value: 0n,
          gasLimit: BigInt(GAS_ESDT_TRANSFER),
          chainID: CHAIN_ID,
          nonce: BigInt(nonce),
          data: Buffer.from(data)
        });

        pendingBatch.push({ tx, recipient, nonce });
        nonce++;

        // When batch is full or we're at the end, verify all
        if (pendingBatch.length >= BATCH_SIZE || i === goldRecipients.length - 1) {
          console.log(`\n📦 Verifying GOLD batch of ${pendingBatch.length} transactions...`);

          // Send all in batch first
          const sent = [];
          for (const item of pendingBatch) {
            try {
              const txHash = await signTransaction(item.tx, secretKey, provider);
              sent.push({ ...item, txHash });
              console.log(`  📤 ${item.recipient.address.slice(0,12)}... → ${txHash.slice(0,8)}...`);
            } catch (e) {
              console.error(`  ❌ ${item.recipient.address.slice(0,12)}... → ${e.message}`);
              failCount++;
            }
          }

          // Wait for confirmations
          if (sent.length > 0) {
            console.log(`  ⏳ Waiting ${CONFIRMATION_WAIT_MS/1000}s for first confirmation...`);
            await new Promise(r => setTimeout(r, CONFIRMATION_WAIT_MS));

            // Verify each - collect pending ones for retry
            const needsRetry = [];
            for (const item of sent) {
              try {
                const txStatus = await provider.getTransaction(item.txHash);

                if (txStatus.status.isExecuted()) {
                  results.gold.push({ hash: item.txHash, address: item.recipient.address, amount: item.recipient.amount });
                  successCount++;
                  console.log(`  ✅ ${item.txHash.slice(0,8)}... → CONFIRMED`);
                } else if (txStatus.status.isFailed()) {
                  failCount++;
                  console.error(`  ❌ ${item.txHash.slice(0,8)}... → FAILED on-chain`);
                } else {
                  needsRetry.push(item);
                  console.log(`  ⏳ ${item.txHash.slice(0,8)}... → PENDING (will retry)`);
                }
              } catch (e) {
                failCount++;
                console.error(`  ❌ ${item.txHash.slice(0,8)}... → VERIFICATION ERROR: ${e.message}`);
              }
            }

            // Retry pending TXs with fresh nonces (ON-CHAIN VERIFICATION BEFORE RETRY)
            if (needsRetry.length > 0) {
              console.log(`\n  🔄 Retrying ${needsRetry.length} pending GOLD transactions...`);

              for (const item of needsRetry) {
                try {
                  const freshNonce = Number((await provider.getAccount(senderAddressForProvider)).nonce);

                  const retryData = `ESDTTransfer@${stringToHex(COLS_TOKEN_ID)}@${colsToHex(item.recipient.amount)}`;
                  const retryTx = new Transaction({
                    sender: senderAddress,
                    receiver: new Address(item.recipient.address),
                    value: 0n,
                    gasLimit: BigInt(GAS_ESDT_TRANSFER),
                    chainID: CHAIN_ID,
                    nonce: BigInt(freshNonce),
                    data: Buffer.from(retryData)
                  });

                  const retryTxHash = await signTransaction(retryTx, secretKey, provider);
                  console.log(`  📤 RETRY ${item.recipient.address.slice(0,12)}... → ${retryTxHash.slice(0,8)}... (nonce ${freshNonce})`);

                  // Wait for retry confirmation
                  await new Promise(r => setTimeout(r, CONFIRMATION_WAIT_MS));

                  const txStatus = await provider.getTransaction(retryTxHash);
                  if (txStatus.status.isExecuted()) {
                    results.gold.push({ hash: retryTxHash, address: item.recipient.address, amount: item.recipient.amount, originalHash: item.txHash });
                    successCount++;
                    console.log(`  ✅ RETRY ${retryTxHash.slice(0,8)}... → CONFIRMED ✅`);
                  } else if (txStatus.status.isFailed()) {
                    failCount++;
                    console.error(`  ❌ RETRY ${retryTxHash.slice(0,8)}... → FAILED on-chain`);
                  } else {
                    failCount++;
                    console.error(`  ❌ RETRY ${retryTxHash.slice(0,8)}... → STILL PENDING after retry`);
                  }
                } catch (e) {
                  failCount++;
                  console.error(`  ❌ RETRY FAILED: ${e.message}`);
                }
              }
            }
          }

          pendingBatch = [];
          console.log(`  📊 GOLD Progress: ${successCount} confirmed, ${failCount} failed (${i + 1}/${goldRecipients.length})`);

          if (i < goldRecipients.length - 1) {
            await new Promise(r => setTimeout(r, 1000));
          }
        }
      }

      console.log(`GOLD Complete: ${successCount} confirmed, ${failCount} failed`);
    }
  }

  // =============================================
  // FINAL SUMMARY
  // =============================================
  console.log("");
  console.log("═".repeat(70));
  console.log("🎉 DISTRIBUTION COMPLETE - VERIFIED");
  console.log("═".repeat(70));

  if (results.dao) {
    console.log(`DAO: ${results.dao.amount.toFixed(6)} COLS → PeerMe`);
    console.log(`   https://explorer.multiversx.com/transactions/${results.dao.hash}`);
  }

  if (results.bonus.length > 0) {
    const totalSent = results.bonus.reduce((s, r) => s + r.amount, 0);
    console.log(`BONUS: ${totalSent.toFixed(6)} COLS → ${results.bonus.length} addresses`);
  }

  if (results.gold?.length > 0) {
    const totalGold = results.gold.reduce((s, r) => s + r.amount, 0);
    console.log(`GOLD: ${totalGold.toFixed(6)} COLS → ${results.gold.length} addresses`);
  }

  // Calculate totals
  const totalDistributed = (results.dao?.amount || 0) +
                          results.bonus.reduce((s, r) => s + r.amount, 0) +
                          (results.gold?.reduce((s, r) => s + r.amount, 0) || 0);

  const expectedTotal = (results.dao?.amount || 0) + totalBonus + (doGold ? dist.gold?.total || 0 : 0);
  const matchPercent = expectedTotal > 0 ? ((totalDistributed / expectedTotal) * 100).toFixed(1) : 0;

  console.log("");
  console.log(`💰 Total Distributed: ${totalDistributed.toFixed(6)} COLS`);
  console.log(`📊 Verification: ${matchPercent}% of expected amount confirmed on-chain`);

  if (Number(matchPercent) < 99) {
    console.log("");
    console.log("⚠️  WARNING: Some transactions were NOT confirmed on-chain!");
    console.log("   Check the failed recipients and re-send if needed.");
  }

  // Save state
  const finalState = {
    lastDistributionDate: today,
    lastDaoHash: results.dao?.hash,
    lastBonusCount: results.bonus.length,
    lastNonce: nonce,
    lastDistribution: {
      dao: results.dao ? { amount: results.dao.amount.toString(), tx: results.dao.hash } : null,
      bonus: results.bonus.length > 0 ? {
        count: results.bonus.length,
        total: results.bonus.reduce((s, r) => s + r.amount, 0).toString()
      } : null,
      gold: results.gold?.length > 0 ? {
        count: results.gold.length,
        total: results.gold.reduce((s, r) => s + r.amount, 0).toString()
      } : null
    }
  };
  saveState(finalState);

  // Save full results
  // Merge with existing results if only re-running DAO
  const saved = (force && fs.existsSync(resultsFile)) ? JSON.parse(fs.readFileSync(resultsFile, 'utf-8')) : {};
  const mergedResults = {
    timestamp: saved.timestamp || new Date().toISOString(),
    verified: true,
    dao: results.dao ?? saved.dao ?? null,
    bonus: results.bonus?.length > 0 ? results.bonus : (saved.bonus || []),
    bonusCount: results.bonus?.length ?? saved.bonusCount ?? 0,
    gold: results.gold?.length > 0 ? results.gold : (saved.gold || []),
    goldCount: results.gold?.length ?? saved.goldCount ?? 0,
    totalColsDistributed: totalDistributed || saved.totalColsDistributed || 0
  };
  fs.writeFileSync(resultsFile, JSON.stringify(mergedResults, null, 2));

  console.log(`\nResults saved: ${resultsFile}`);

  // Exit with error if a requested pool failed (must not fail silently)
  if (doDao && !results.dao) {
    console.error(`\n❌ DAO distribution FAILED - process exiting with error`);
    process.exit(1);
  }
  if (doBonus && results.bonus.length === 0) {
    console.error(`\n❌ BONUS distribution FAILED - process exiting with error`);
    process.exit(1);
  }
  if (doGold && (!results.gold || results.gold.length === 0)) {
    console.error(`\n❌ GOLD distribution FAILED - process exiting with error`);
    process.exit(1);
  }
}

main().catch(e => { console.error(e); process.exit(1); });
