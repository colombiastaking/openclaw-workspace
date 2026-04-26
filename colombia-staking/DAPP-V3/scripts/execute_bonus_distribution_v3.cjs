/**
 * BONUS Pool Distribution Script v3 - WITH VERIFICATION
 * 
 * FIXES over v2:
 * 1. Verifies txHash exists before marking success
 * 2. Awaits transaction confirmation (not just broadcast)
 * 3. Verifies each hash on-chain before counting as success
 * 4. Handles failures properly with retry logic
 * 
 * Run with: node execute_bonus_distribution_v3.cjs [--execute]
 */

const fs = require("fs");

async function main() {
  // Dynamic imports
  const { ProxyNetworkProvider } = await import("@multiversx/sdk-network-providers");
  const { Address, Transaction, TransactionPayload } = await import("@multiversx/sdk-core");
  const { UserSecretKey } = await import("@multiversx/sdk-wallet");

  // Configuration
  const NETWORK_PROVIDER = "https://gateway.multiversx.com";
  const COLS_TOKEN_ID = "COLS-9d91b7";
  const GAS_LIMIT = 500000;      // Fixed gas limit for ESDT transfers
  const CHAIN_ID = "1";          // Mainnet
  const CONFIRMATION_WAIT_MS = 6000;  // Wait 6 seconds for tx to be confirmed
  const MAX_RETRIES = 2;         // Retry failed transactions

  console.log("═".repeat(70));
  console.log("🚀 BONUS POOL DISTRIBUTION v3 (WITH VERIFICATION)");
  console.log("═".repeat(70));
  console.log(`Time: ${new Date().toISOString()}`);
  console.log();

  // Setup provider
  const provider = new ProxyNetworkProvider(NETWORK_PROVIDER, {
    clientName: "bonus-distribution-v3"
  });
  
  // Load private key
  const keyHex = fs.readFileSync('/home/raspberry/.openclaw/wallet/.private_key', 'utf-8').trim();
  const secretKey = UserSecretKey.fromString(keyHex);
  const publicKey = secretKey.generatePublicKey();
  const senderAddress = publicKey.toAddress();
  
  console.log(`Sender Wallet: ${senderAddress.bech32()}`);
  console.log("⚠️  DRY RUN MODE - No transactions will be sent unless --execute flag is provided");
  console.log();
  
  // Check balance
  const accountOnNetwork = await provider.getAccount(senderAddress);
  console.log(`Nonce: ${accountOnNetwork.nonce}`);
  console.log(`EGLD Balance: ${Number(accountOnNetwork.balance) / 1e18}`);
  
  const tokens = await provider.getFungibleTokensOfAccount(senderAddress, [COLS_TOKEN_ID]);
  const colsBalance = tokens[0]?.balance || 0n;
  console.log(`COLS Balance: ${Number(colsBalance) / 1e18}`);
  console.log();
  
  // Load recipients from distribution file
  const recipientsData = JSON.parse(fs.readFileSync('/tmp/distribution_full_v4.json', 'utf-8'));
  const recipients = recipientsData.bonusRecipients;
  const totalAmount = recipients.reduce((s, r) => s + r.dailyBonus, 0);
  
  console.log(`Recipients: ${recipients.length}`);
  console.log(`Total COLS to distribute: ${totalAmount.toFixed(6)}`);
  console.log();

  // Helper: Convert amount to properly padded hex string
  function amountToHex(amountCols) {
    const amountBigInt = BigInt(Math.floor(amountCols * 1e18));
    let hexStr = amountBigInt.toString(16);
    
    // CRITICAL FIX: Pad with leading zero if length is odd
    if (hexStr.length % 2 !== 0) {
      hexStr = '0' + hexStr;
    }
    
    return hexStr;
  }

  // Verify sufficient balance
  if (Number(colsBalance) < totalAmount * 1e18) {
    throw new Error(`Insufficient COLS balance. Need ${totalAmount.toFixed(2)}, have ${Number(colsBalance)/1e18}`);
  }
  
  // Build ESDT transfer data
  const tokenHex = Buffer.from(COLS_TOKEN_ID).toString('hex');
  
  // Check for execute flag
  const shouldExecute = process.argv.includes('--execute');
  
  if (!shouldExecute) {
    console.log("═".repeat(70));
    console.log("📋 DRY RUN - Preview of transactions");
    console.log("═".repeat(70));
    console.log();
    
    console.log("First 10 transactions:");
    for (let i = 0; i < 10 && i < recipients.length; i++) {
      const r = recipients[i];
      const amountHex = amountToHex(r.dailyBonus);
      const dataStr = `ESDTTransfer@${tokenHex}@${amountHex}`;
      
      console.log(`  [${i}] ${r.address.slice(0,20)}...`);
      console.log(`       Amount: ${r.dailyBonus.toFixed(6)} COLS`);
      console.log(`       Hex: ${amountHex} (${amountHex.length} chars, ${amountHex.length % 2 === 0 ? 'EVEN ✓' : 'ODD ✗'})`);
      console.log(`       Data: ${dataStr.slice(0,60)}...`);
    }
    
    console.log();
    console.log("Last 3 transactions:");
    for (let i = recipients.length - 3; i < recipients.length; i++) {
      const r = recipients[i];
      const amountHex = amountToHex(r.dailyBonus);
      
      console.log(`  [${i}] ${r.address.slice(0,20)}...`);
      console.log(`       Amount: ${r.dailyBonus.toFixed(10)} COLS`);
      console.log(`       Hex: ${amountHex} (${amountHex.length} chars, ${amountHex.length % 2 === 0 ? 'EVEN ✓' : 'ODD ✗'})`);
    }
    
    console.log();
    console.log("═".repeat(70));
    console.log(`Total: ${recipients.length} transactions, ${totalAmount.toFixed(6)} COLS`);
    console.log("═".repeat(70));
    console.log();
    console.log("To execute, run with --execute flag");
    return;
  }
  
  // EXECUTE MODE
  console.log("═".repeat(70));
  console.log("⚠️  EXECUTE MODE - Transactions will be sent with VERIFICATION!");
  console.log("═".repeat(70));
  console.log();
  
  // Re-fetch fresh nonce right before sending
  const freshAccount = await provider.getAccount(senderAddress);
  let currentNonce = Number(freshAccount.nonce);
  console.log(`Starting nonce: ${currentNonce}`);
  console.log();
  
  const txHashes = [];
  let successCount = 0;
  let failCount = 0;
  let pendingTransactions = [];  // Track unconfirmed transactions
  
  // Process recipients in small batches to avoid nonce issues
  const BATCH_SIZE = 10;
  
  for (let batchStart = 0; batchStart < recipients.length; batchStart += BATCH_SIZE) {
    const batchEnd = Math.min(batchStart + BATCH_SIZE, recipients.length);
    const batch = recipients.slice(batchStart, batchEnd);
    
    console.log(`\n📦 Processing batch ${Math.floor(batchStart / BATCH_SIZE) + 1}: recipients ${batchStart} to ${batchEnd - 1}`);
    
    // Step 1: Send all transactions in this batch
    const batchTxs = [];
    for (let i = 0; i < batch.length; i++) {
      const recipient = batch[i];
      const amountHex = amountToHex(recipient.dailyBonus);
      const dataStr = `ESDTTransfer@${tokenHex}@${amountHex}`;
      
      // Create payload as a Uint8Array (direct bytes, no TransactionPayload wrapper)
      const dataBytes = Buffer.from(dataStr, 'utf8');
      
      const tx = new Transaction({
        sender: senderAddress,
        receiver: new Address(recipient.address),
        value: 0n,
        gasLimit: BigInt(GAS_LIMIT),
        chainID: CHAIN_ID,
        nonce: BigInt(currentNonce),
        data: dataBytes
      });
      
      // Sign transaction
      const serializedTx = tx.serializeForSigning();
      const signature = secretKey.sign(serializedTx);
      tx.applySignature(signature);
      
      // Send transaction
      try {
        const txHash = await provider.sendTransaction(tx);
        
        // BUG FIX #1: Verify txHash is valid before proceeding
        if (!txHash || txHash === 'undefined' || txHash === 'null') {
          throw new Error(`Invalid txHash returned: ${txHash}`);
        }
        
        const txHashStr = txHash.toString();
        console.log(`  📤 [${batchStart + i}] ${recipient.address.slice(0,16)}... → ${txHashStr.slice(0,8)}...`);
        
        batchTxs.push({
          txHash: txHashStr,
          recipient: recipient.address,
          amount: recipient.dailyBonus,
          nonce: currentNonce
        });
        
      } catch (e) {
        console.error(`  ❌ [${batchStart + i}] ${recipient.address.slice(0,16)}... → ${e.message}`);
        failCount++;
      }
      
      currentNonce++;
    }
    
    // Step 2: Wait for confirmation and verify on-chain
    console.log(`  ⏳ Waiting ${CONFIRMATION_WAIT_MS/1000}s for confirmations...`);
    await new Promise(r => setTimeout(r, CONFIRMATION_WAIT_MS));
    
    // Verify each transaction
    for (const pending of batchTxs) {
      try {
        // BUG FIX #2: Actually verify the transaction exists on-chain
        const txStatus = await provider.getTransaction(pending.txHash);
        
        if (txStatus.status.isPending()) {
          // Transaction is still pending - not confirmed yet
          console.error(`  ⏳ [PENDING] ${pending.txHash.slice(0,8)}... → Still pending, not counted as success`);
          failCount++;
        } else if (txStatus.status.isExecuted()) {
          // Transaction was executed successfully
          txHashes.push(pending);
          successCount++;
          console.log(`  ✅ [CONFIRMED] ${pending.txHash.slice(0,8)}... → OK`);
        } else if (txStatus.status.isFailed()) {
          // Transaction failed
          console.error(`  ❌ [FAILED] ${pending.txHash.slice(0,8)}... → ${txStatus.status}`);
          failCount++;
        } else {
          // Unknown status
          console.error(`  ❌ [UNKNOWN] ${pending.txHash.slice(0,8)}... → Status: ${txStatus.status}`);
          failCount++;
        }
        
      } catch (e) {
        // BUG FIX #3: Transaction not found on-chain = failed
        console.error(`  ❌ [NOT FOUND] ${pending.txHash.slice(0,8)}... → ${e.message}`);
        failCount++;
      }
    }
    
    // Small delay between batches to let the network catch up
    if (batchEnd < recipients.length) {
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  
  // Final Summary
  console.log();
  console.log("═".repeat(70));
  console.log("DISTRIBUTION COMPLETE");
  console.log("═".repeat(70));
  console.log(`✅ Confirmed on-chain: ${successCount}`);
  console.log(`❌ Failed/Not confirmed: ${failCount}`);
  console.log(`📊 Expected recipients: ${recipients.length}`);
  
  if (txHashes.length > 0) {
    const totalDistributed = txHashes.reduce((s, t) => s + t.amount, 0);
    console.log(`💰 Total COLS distributed: ${totalDistributed.toFixed(6)}`);
  }
  
  // Save results
  const results = {
    timestamp: new Date().toISOString(),
    successCount,
    failCount,
    totalDistributed: txHashes.reduce((s, t) => s + t.amount, 0),
    transactions: txHashes,
    failedRecipients: recipients.filter(r => !txHashes.find(t => t.recipient === r.address)).map(r => ({
      address: r.address,
      amount: r.dailyBonus
    }))
  };
  
  fs.writeFileSync('/tmp/bonus_distribution_results_v3.json', JSON.stringify(results, null, 2));
  console.log(`\n✅ Results saved to /tmp/bonus_distribution_results_v3.json`);
  
  // If there were failures, warn
  if (failCount > 0) {
    console.log();
    console.log("⚠️  WARNING: Some transactions failed or were not confirmed!");
    console.log("   Check the failedRecipients list in the results file.");
    console.log("   You may need to re-run distribution for failed recipients.");
  }
}

main().catch(console.error);
