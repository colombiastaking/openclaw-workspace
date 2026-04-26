/**
 * Manual补救 - Send missing March 27 & March 28 bonuses to Sebas
 */
const fs = require("fs");

async function main() {
  const { ProxyNetworkProvider } = await import("@multiversx/sdk-network-providers");
  const { Address, Transaction, TransactionPayload } = await import("@multiversx/sdk-core");
  const { UserSecretKey } = await import("@multiversx/sdk-wallet");

  const provider = new ProxyNetworkProvider('https://gateway.multiversx.com');

  const keyHex = fs.readFileSync('/home/raspberry/.openclaw/wallet/.private_key', 'utf-8').trim();
  const secretKey = UserSecretKey.fromString(keyHex);
  const publicKey = secretKey.generatePublicKey();
  const senderAddress = publicKey.toAddress();

  const sebasAddress = 'erd1kr7m0ge40v6zj6yr8e2eupkeudfsnv827e7ta6w550e9rnhmdv6sfr8qdm';

  const missing = [
    { date: 'March 27', amount: 0.0006843746295037028 },
    { date: 'March 28', amount: 0.0006861176746461974 },
  ];

  const tokenIdHex = '434f4c532d396439316237';

  function amountToHex(amountCols) {
    const amountBigInt = BigInt(Math.floor(amountCols * 1e18));
    let hexStr = amountBigInt.toString(16);
    if (hexStr.length % 2 !== 0) hexStr = '0' + hexStr;
    return hexStr;
  }

  console.log('Sender:', senderAddress.bech32());
  console.log('Recipient:', sebasAddress);
  console.log('');

  let currentNonce = (await provider.getAccount(senderAddress)).nonce;
  console.log('Current nonce:', currentNonce);
  console.log('');

  for (const m of missing) {
    const amountHex = amountToHex(m.amount);
    const dataStr = `ESDTTransfer@${tokenIdHex}@${amountHex}`;
    const payload = new TransactionPayload(dataStr);

    const tx = new Transaction({
      sender: senderAddress,
      receiver: new Address(sebasAddress),
      nonce: currentNonce,
      data: payload,
      gasLimit: 500000,
      chainID: '1',
    });

    const serializedTx = tx.serializeForSigning();
    const signature = secretKey.sign(serializedTx);
    tx.applySignature(signature);

    try {
      const txHash = await provider.sendTransaction(tx);
      console.log(`✅ ${m.date}: ${m.amount.toFixed(6)} COLS → ${txHash}`);
    } catch (e) {
      console.error(`❌ ${m.date}: ${e.message}`);
    }

    currentNonce++;
    await new Promise(r => setTimeout(r, 1000));
  }

  console.log('\nDone!');
}

main().catch(console.error);
