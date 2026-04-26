/**
 * Test script for distribution fix verification
 * Sends a tiny amount to verify the signing/verification works
 */

const fs = require("fs");
const sdk = require("@multiversx/sdk-core");
const { ProxyNetworkProvider } = require("@multiversx/sdk-network-providers");
const { UserSecretKey } = require("@multiversx/sdk-wallet");

const { Address, Transaction, TransactionComputer } = sdk;

const NETWORK_PROVIDER = "https://gateway.multiversx.com";
const COLS_TOKEN_ID = "COLS-9d91b7";
const GAS_LIMIT = 600000;
const CHAIN_ID = "1";

// Test recipient - Sebas's address
const TEST_RECIPIENT = "erd1kr7m0ge40v6zj6yr8e2eupkeudfsnv827e7ta6w550e9rnhmdv6sfr8qdm";
const TEST_AMOUNT = 0.000001; // Tiny amount to test

async function main() {
  console.log("═".repeat(70));
  console.log("🧪 DISTRIBUTION FIX TEST");
  console.log("═".repeat(70));
  console.log("");
  
  // Load wallet
  const keyHex = fs.readFileSync('/home/raspberry/.openclaw/wallet/.private_key', 'utf-8').trim();
  const secretKey = UserSecretKey.fromString(keyHex);
  const senderPublicKey = secretKey.generatePublicKey();
  const senderAddress = new Address(senderPublicKey.valueOf());
  const senderAddressForProvider = senderPublicKey.toAddress();
  
  console.log(`Sender: ${senderAddress.toBech32()}`);
  console.log(`Test recipient: ${TEST_RECIPIENT}`);
  console.log(`Test amount: ${TEST_AMOUNT} COLS`);
  console.log("");
  
  // Setup provider
  const provider = new ProxyNetworkProvider(NETWORK_PROVIDER, { 
    timeout: 30000,
    clientName: "cols-test"
  });
  
  // Get nonce
  const account = await provider.getAccount(senderAddressForProvider);
  console.log(`Current nonce: ${account.nonce}`);
  console.log("");
  
  // Convert amount to hex
  const amountBigInt = BigInt(Math.floor(TEST_AMOUNT * 1e18));
  let amountHex = amountBigInt.toString(16);
  if (amountHex.length % 2 !== 0) amountHex = '0' + amountHex;
  console.log(`Amount hex: ${amountHex}`);
  
  // Build transaction
  const tokenHex = Buffer.from(COLS_TOKEN_ID).toString('hex');
  const dataStr = `ESDTTransfer@${tokenHex}@${amountHex}`;
  console.log(`Data: ${dataStr}`);
  console.log("");
  
  // Create transaction
  const tx = new Transaction({
    sender: senderAddress,
    receiver: new Address(TEST_RECIPIENT),
    value: 0n,
    gasLimit: BigInt(GAS_LIMIT),
    chainID: CHAIN_ID,
    nonce: BigInt(account.nonce),
    data: Buffer.from(dataStr)
  });
  
  console.log("📝 Signing transaction...");
  const transactionComputer = new TransactionComputer();
  const serializedTx = transactionComputer.computeBytesForSigning(tx);
  console.log(`  Serialized bytes length: ${serializedTx.length}`);
  
  const signature = secretKey.sign(serializedTx);
  tx.signature = signature;
  console.log(`  Signature: ${Buffer.from(signature).toString('hex').slice(0, 20)}...`);
  console.log("");
  
  // Send transaction
  console.log("📤 Sending transaction...");
  let txHash;
  try {
    txHash = await provider.sendTransaction(tx);
    console.log(`  TxHash: ${txHash}`);
    console.log(`  Explorer: https://explorer.multiversx.com/transactions/${txHash}`);
  } catch (e) {
    console.error(`  ❌ Send failed: ${e.message}`);
    process.exit(1);
  }
  console.log("");
  
  // Wait for confirmation
  console.log("⏳ Waiting 6 seconds for confirmation...");
  await new Promise(r => setTimeout(r, 6000));
  console.log("");
  
  // Verify on-chain
  console.log("🔍 Verifying on-chain...");
  try {
    const txStatus = await provider.getTransaction(txHash);
    console.log(`  Status: ${txStatus.status}`);
    
    if (txStatus.status.isExecuted()) {
      console.log("");
      console.log("✅ TEST PASSED - Transaction confirmed on-chain!");
      console.log(`   https://explorer.multiversx.com/transactions/${txHash}`);
    } else if (txStatus.status.isFailed()) {
      console.log("");
      console.log("❌ TEST FAILED - Transaction failed on-chain!");
    } else if (txStatus.status.isPending()) {
      console.log("");
      console.log("⏳ TEST INCONCLUSIVE - Transaction still pending");
    } else {
      console.log("");
      console.log(`❓ TEST INCONCLUSIVE - Unknown status: ${txStatus.status}`);
    }
  } catch (e) {
    console.error(`  ❌ Verification failed: ${e.message}`);
    console.log("");
    console.log("❌ TEST FAILED - Could not verify transaction on-chain");
  }
}

main().catch(console.error);
