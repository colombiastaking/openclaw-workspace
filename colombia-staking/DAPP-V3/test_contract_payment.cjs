const sdk = require("@multiversx/sdk-core");
const { ProxyNetworkProvider } = require("@multiversx/sdk-network-providers");
const { UserSecretKey } = require("@multiversx/sdk-wallet");
const fs = require("fs");

const { Address, Transaction, TransactionComputer } = sdk;

const NETWORK_PROVIDER = "https://gateway.multiversx.com";
const CHAIN_ID = "1";

async function main() {
  // Load wallet
  const keyHex = fs.readFileSync('/home/raspberry/.openclaw/wallet/.private_key', 'utf-8').trim();
  const privateKey = UserSecretKey.fromString(keyHex);
  const senderPublicKey = privateKey.generatePublicKey();
  const senderAddress = new Address(senderPublicKey.valueOf());
  
  // Contract
  const contractAddress = new Address("erd1qqqqqqqqqqqqqpgqw09yjq5a303px3kgdk9sfhwqyh5p0qvskgqqmza2t9");
  
  // Get nonce
  const { ApiNetworkProvider } = require("@multiversx/sdk-network-providers");
  const provider = new ApiNetworkProvider("https://api.multiversx.com", { clientName: "test" });
  const account = await provider.getAccount(senderAddress);
  const nonce = Number(account.nonce);
  
  console.log(`Sender: ${senderAddress.toString()}`);
  console.log(`Nonce: ${nonce}`);
  console.log(`Contract: ${contractAddress.toString()}`);
  
  // Token and data
  const COLS_TOKEN = "COLS-ticker-4ab53f";
  const PRICE_WEI = "4563918244f40000"; // 5 COLS
  const functionHex = Buffer.from("payForYear").toString('hex');
  const targetHex = senderAddress.getPublicKey().toString('hex');
  const yearHex = (2025).toString(16).padStart(8, '0');
  
  const data = `ESDTTransfer@${Buffer.from(COLS_TOKEN).toString('hex')}@${PRICE_WEI}@${functionHex}@${targetHex}@${yearHex}`;
  
  console.log(`Data: ${data}`);
  
  // Create transaction
  const tx = new Transaction({
    sender: senderAddress,
    receiver: contractAddress,
    value: 0n,
    gasLimit: 10000000n,
    chainID: CHAIN_ID,
    data: Buffer.from(data)
  });
  
  // Sign and send
  const transactionComputer = new TransactionComputer();
  const serializedTx = transactionComputer.computeBytesForSigning(tx);
  const signature = privateKey.sign(serializedTx);
  tx.signature = signature;
  
  console.log('Sending...');
  const result = await provider.sendTransaction(tx);
  console.log(`✅ Transaction sent! Hash: ${result}`);
  console.log(`Explorer: https://explorer.multiversx.com/transactions/${result}`);
}

main().catch(e => console.error('Error:', e.message));
