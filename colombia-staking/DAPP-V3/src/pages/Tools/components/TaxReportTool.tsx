import { useState, useEffect } from 'react';
import { useGetAccount } from '@multiversx/sdk-dapp/out/react/account/useGetAccount';
import { useGetActiveTransactionsStatus } from 'hooks/useTransactionStatus';
import { sendTransactions } from 'helpers/sendTransactions';
import axios from 'axios';
import { jsPDF } from 'jspdf';
import styles from './TaxReportTool.module.scss';

interface Props {
  onBack: () => void;
}

// ========== SMART CONTRACT CONSTANTS ==========
const TAX_REPORT_CONTRACT = 'erd1qqqqqqqqqqqqqpgqw09yjq5a303px3kgdk9sfhwqyh5p0qvskgqqmza2t9';
const COLS_TOKEN_ID = 'COLS-9d91b7';
const REPORT_PRICE_WEI = '5000000000000000000'; // 5 COLS with 18 decimals

interface Transaction {
  date: string;
  hash: string;
  type: string;
  value: number;
  price: number;
  monthKey: string;
  provider?: string;
}

interface MonthlyData {
  month: string;
  monthNum: number;
  egld: number;
  usd: number;
  eur: number;
  avgPrice: number;
  txCount: number;
}

interface TaxReport {
  year: number;
  totalEgld: number;
  totalUsd: number;
  totalEur: number;
  monthlyData: MonthlyData[];
  transactions: Transaction[];
  providers: Array<{ address: string; name: string }>;
}

interface PaymentStatus {
  hasPaid: boolean;
  paymentCount: number;
}

const PROVIDER_NAMES: Record<string, string> = {
  'erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf': 'Colombia Staking',
};

let cachedPrices: { usd: Record<string, number>; eur: Record<string, number> } | null = null;

const PUBLIC_API = 'https://api.multiversx.com';
const TAX_QUERY_ENDPOINT = 'https://colombia-staking.co/tax-query';

async function loadHistoricalPrices(): Promise<{ usd: Record<string, number>; eur: Record<string, number> }> {
  if (cachedPrices) return cachedPrices;
  
  try {
    const response = await fetch('/egld-prices.json');
    if (response.ok) {
      const data = await response.json();
      cachedPrices = { usd: data.usd || {}, eur: data.eur || {} };
      return cachedPrices;
    }
  } catch (error) {
    console.error('Failed to load egld-prices.json:', error);
  }
  
  return { usd: {}, eur: {} };
}

function getProviderName(contract: string): string {
  return PROVIDER_NAMES[contract.toLowerCase()] || contract.slice(0, 20) + '...';
}

// ========== PAYMENT VERIFICATION ==========

// Convert bech32 address to 32-byte hex (without 0x prefix)
function bech32ToHex(bech32: string): string {
  // MultiversX bech32 addresses: erd1... -> 32 bytes
  // We need the raw public key bytes as hex
  // Using simple conversion: remove erd1 prefix and decode base32
  const CHARS = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l';
  const bech32Data = bech32.replace('erd1', '').toLowerCase();
  
  // Decode bech32 to get 32 bytes
  let bits = 0;
  let value = 0;
  const output: number[] = [];
  
  for (let i = 0; i < bech32Data.length; i++) {
    const c = bech32Data[i];
    const pos = CHARS.indexOf(c);
    if (pos === -1) continue;
    value = (value << 5) + pos;
    bits += 5;
    if (bits >= 8) {
      output.push((value >> (bits - 8)) & 0xff);
      bits -= 8;
    }
  }
  
  // Take only 32 bytes (ignore last partial byte if any)
  const pubkeyBytes = output.slice(0, 32);
  return pubkeyBytes.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function checkPaymentStatus(address: string, year: number): Promise<PaymentStatus> {
  try {
    const addressHex = bech32ToHex(address);
    const yearHex = year.toString(16).padStart(8, '0');
    
    const response = await axios.post(
      'https://gateway.multiversx.com/v1.0/vm-values/query',
      {
        scAddress: TAX_REPORT_CONTRACT,
        funcName: 'hasPaymentForYear',
        args: [addressHex, addressHex, yearHex]
      },
      { timeout: 10000 }
    );
    
    const returnData = response.data?.data?.data?.returnData;
    if (returnData && returnData[0]) {
      const decoded = atob(returnData[0]);
      const hasPaid = decoded === '\u0001';
      return {
        hasPaid,
        paymentCount: hasPaid ? 1 : 0
      };
    }
    
    return { hasPaid: false, paymentCount: 0 };
  } catch (error) {
    console.error('[PaymentCheck] Failed:', error);
    return { hasPaid: false, paymentCount: 0 };
  }
}

// ========== TAX QUERY (PRIMARY) - Uses server-side proxy to bypass CORS ==========

interface TaxQueryResponse {
  providers: Array<{ address: string; name: string }>;
  transactions: Array<{
    hash: string;
    date: string;
    type: string;
    value: number;
    provider: string;
    providerName?: string;
    timestamp: number;
  }>;
  error?: string;
}

async function fetchTaxDataViaProxy(
  address: string,
  year: number,
  onProgress: (status: string, count: number) => void
): Promise<{ transactions: Transaction[]; providers: Array<{ address: string; name: string }> }> {
  onProgress('Querying tax data via proxy...', 0);
  
  try {
    const response = await axios.get<TaxQueryResponse>(
      `${TAX_QUERY_ENDPOINT}?address=${address}&year=${year}`,
      { timeout: 120000 }
    );
    
    if (response.data.error) {
      throw new Error(response.data.error);
    }
    
    const providers = response.data.providers || [];
    const txs = response.data.transactions || [];
    
    onProgress(`Found ${txs.length} transactions`, txs.length);
    
    // Convert to Transaction format
    const transactions: Transaction[] = txs.map(tx => {
      const txDate = new Date(tx.timestamp * 1000);
      const monthKey = `${year}-${(txDate.getMonth() + 1).toString().padStart(2, '0')}`;
      
      return {
        date: tx.date,
        hash: tx.hash,
        type: tx.type,
        value: tx.value,
        price: 0,
        monthKey,
        provider: tx.providerName || getProviderName(tx.provider)
      };
    });
    
    return { transactions, providers };
  } catch (error) {
    console.error('[TaxQuery] Failed:', error);
    throw error;
  }
}

// ========== PUBLIC API FUNCTIONS (Fallback) ==========

async function fetchDelegationContractsPublic(
  address: string,
  onProgress: (status: string, count?: number) => void
): Promise<string[]> {
  onProgress('Finding your staking providers...');
  
  try {
    const { data } = await axios.get(
      `${PUBLIC_API}/accounts/${address}/delegation`,
      { timeout: 15000 }
    );
    
    if (Array.isArray(data)) {
      const contracts = data.map((d: any) => d.contract).filter(Boolean);
      console.log(`[Public API] Found ${contracts.length} delegation contracts`);
      return contracts;
    }
  } catch (error) {
    console.error('[Public API] Failed to fetch delegation contracts:', error);
  }
  
  return [];
}

async function fetchAllStakingRewards(
  address: string, 
  year: number,
  onProgress: (status: string, count: number) => void
): Promise<{ transactions: Transaction[]; providers: Array<{ address: string; name: string }> }> {
  
  // Try Tax Query Proxy first (bypasses CORS)
  try {
    const result = await fetchTaxDataViaProxy(address, year, (status, count) => onProgress(status, count));
    if (result.transactions.length > 0) {
      onProgress('Processing complete', result.transactions.length);
      return result;
    }
  } catch (error) {
    console.error('[TaxQuery] Failed, falling back to public API:', error);
    onProgress('Proxy unavailable, using public API...', 0);
  }
  
  // Fallback: Use public API with pagination
  onProgress('Finding your staking providers...', 0);
  
  // Get delegation contracts
  const providers = await fetchDelegationContractsPublic(address, (status, _count) => onProgress(status, _count || 0));
  
  if (providers.length === 0) {
    onProgress('No staking providers found for this address', 0);
    return { transactions: [], providers: [] };
  }
  
  onProgress(`Found ${providers.length} provider(s)`, 0);
  const providerSet = new Set(providers.map(p => p.toLowerCase()));
  
  const transactions: Transaction[] = [];
  const startTs = Math.floor(new Date(`${year}-01-01`).getTime() / 1000);
  const endTs = Math.floor(new Date(`${year}-12-31 23:59:59`).getTime() / 1000);
  
  let page = 0;
  let totalFetched = 0;
  const foundProviders = new Set<string>();

  while (true) {
    onProgress(`Scanning page ${page + 1}...`, totalFetched);
    
    try {
      const { data } = await axios.get(
        `${PUBLIC_API}/accounts/${address}/transactions?size=1000&from=${page * 1000}&status=success`,
        { timeout: 30000 }
      );

      if (!data || data.length === 0) break;

      let hasOlder = false;
      
      for (const tx of data) {
        const txTs = tx.timestamp;
        
        if (txTs < startTs) {
          hasOlder = true;
          if (page === 0) continue;
          break;
        }
        if (txTs > endTs) continue;
        
        totalFetched++;

        const receiver = tx.receiver || '';
        const isClaimCall = 
          (tx.function === 'claimRewards' || tx.function === 'claim') &&
          tx.sender === address &&
          providerSet.has(receiver.toLowerCase());

        if (isClaimCall) {
          foundProviders.add(receiver.toLowerCase());
          const txDate = new Date(txTs * 1000);
          const monthKey = `${year}-${(txDate.getMonth() + 1).toString().padStart(2, '0')}`;
          
          const txHash = tx.hash || tx.txHash;
          let egldValue = parseInt(tx.value || 0) / 1e18;
          
          if (egldValue === 0) {
            if (txHash) {
              try {
                // Try public API for transaction with results
                const fullTx = await axios.get(
                  `${PUBLIC_API}/transactions/${txHash}?withResults=true`,
                  { timeout: 15000 }
                );
                
                if (fullTx.data?.results) {
                  let maxValue = 0;
                  for (const result of fullTx.data.results) {
                    const isFromProvider = providerSet.has(result.sender?.toLowerCase() || '');
                    const isToUser = result.receiver?.toLowerCase() === address.toLowerCase();
                    
                    if (isFromProvider && isToUser && result.function === 'transfer') {
                      const transferValue = parseInt(result.value || 0) / 1e18;
                      if (transferValue > maxValue) {
                        maxValue = transferValue;
                      }
                    }
                  }
                  egldValue = maxValue;
                }
              } catch (err) {
                console.error('Failed to fetch claim amount:', err);
              }
            }
          }
          
          if (egldValue > 0) {
            transactions.push({
              date: txDate.toISOString().split('T')[0],
              hash: txHash || '',
              type: tx.function || 'claimRewards',
              value: egldValue,
              price: 0,
              monthKey,
              provider: getProviderName(receiver)
            });
          }
        }
      }
      
      if (hasOlder) break;
      page++;
      
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
      break;
    }
  }

  onProgress('Processing complete', transactions.length);
  return { transactions, providers: Array.from(foundProviders).map(p => ({ address: p, name: getProviderName(p) })) };
}

async function fetchHistoricalPrices(_year: number): Promise<{ usd: Record<string, number>; eur: Record<string, number> }> {
  return loadHistoricalPrices();
}

function calculateTaxReport(
  transactions: Transaction[],
  year: number,
  prices: { usd: Record<string, number>; eur: Record<string, number> }
): TaxReport {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthlyMap: Record<string, MonthlyData> = {};
  
  for (let i = 0; i < 12; i++) {
    const monthKey = `${year}-${(i + 1).toString().padStart(2, '0')}`;
    monthlyMap[monthKey] = {
      month: months[i],
      monthNum: i + 1,
      egld: 0,
      usd: 0,
      eur: 0,
      avgPrice: 0,
      txCount: 0
    };
  }

  let totalEgld = 0;
  let totalUsd = 0;
  let totalEur = 0;

  for (const tx of transactions) {
    const monthData = monthlyMap[tx.monthKey];
    if (!monthData) continue;
    
    const usdPrice = prices.usd[tx.monthKey] || 0;
    const eurPrice = prices.eur[tx.monthKey] || 0;
    
    tx.price = usdPrice;
    
    monthData.egld += tx.value;
    monthData.usd += tx.value * usdPrice;
    monthData.eur += tx.value * eurPrice;
    monthData.txCount++;
    
    if (usdPrice > 0 && monthData.avgPrice === 0) {
      monthData.avgPrice = usdPrice;
    }
    
    totalEgld += tx.value;
    totalUsd += tx.value * usdPrice;
    totalEur += tx.value * eurPrice;
  }

  const monthlyData = Object.values(monthlyMap);

  return {
    year,
    totalEgld,
    totalUsd,
    totalEur,
    monthlyData,
    transactions,
    providers: [...new Set(transactions.map(t => t.provider || '').filter(Boolean))].map(p => ({ address: p, name: p }))
  };
}

// Load logo as base64 for jsPDF
async function loadLogoBase64(): Promise<string> {
  try {
    const response = await fetch('/assets/colombia-staking-logo.png');
    const blob = await response.blob();
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error('Failed to load logo:', error);
    return '';
  }
}

// Generate professional PDF report
async function generatePDF(report: TaxReport, address: string): Promise<void> {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  let y = 20;

  // Colombia Staking brand colors
  const primaryColor: [number, number, number] = [0, 128, 100];
  const accentColor: [number, number, number] = [0, 77, 64];
  const textColor: [number, number, number] = [33, 33, 33];
  const mutedColor: [number, number, number] = [100, 100, 100];
  const lightBg: [number, number, number] = [245, 248, 247];

  // Load logo
  const logoBase64 = await loadLogoBase64();

  // ========== HEADER ==========
  if (logoBase64) {
    doc.addImage(logoBase64, 'PNG', margin, 10, 22, 22);
  }
  
  doc.setFontSize(20);
  doc.setTextColor(...primaryColor);
  doc.text('MultiversX Staking Tax Report', logoBase64 ? margin + 27 : margin, 22);
  
  doc.setFontSize(10);
  doc.setTextColor(...mutedColor);
  doc.text('Staking Rewards Summary', logoBase64 ? margin + 27 : margin, 29);
  
  // Decorative line
  doc.setDrawColor(...primaryColor);
  doc.setLineWidth(0.5);
  doc.line(margin, 38, pageWidth - margin, 38);
  
  y = 45;

  // ========== REPORT INFO ==========
  doc.setFontSize(12);
  doc.setTextColor(...textColor);
  doc.text(`Tax Year: ${report.year}`, margin, y);
  y += 6;
  
  doc.setFontSize(9);
  doc.setTextColor(...mutedColor);
  doc.text(`Wallet: ${address.slice(0, 12)}...${address.slice(-8)}`, margin, y);
  y += 3;
  doc.text(`Generated: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`, margin, y);
  y += 3;
  
  if (report.providers.length > 0) {
    doc.text(`Providers: ${report.providers.map(p => p.name).join(', ')}`, margin, y);
    y += 3;
  }
  y += 12;

  // ========== SUMMARY CARD ==========
  doc.setFillColor(...lightBg);
  doc.roundedRect(margin, y, pageWidth - (margin * 2), 40, 3, 3, 'F');
  
  doc.setFillColor(...primaryColor);
  doc.rect(margin, y, 3, 40, 'F');
  
  y += 10;
  doc.setFontSize(11);
  doc.setTextColor(...primaryColor);
  doc.text('TOTAL STAKING REWARDS', margin + 10, y);
  
  y += 10;
  doc.setFontSize(18);
  doc.setTextColor(...textColor);
  doc.text(`${report.totalEgld.toFixed(4)} eGLD`, margin + 10, y);
  
  doc.setFontSize(11);
  doc.setTextColor(...mutedColor);
  doc.text(`$${report.totalUsd.toFixed(2)} USD`, margin + 70, y);
  doc.text(`€${report.totalEur.toFixed(2)} EUR`, margin + 115, y);
  
  y += 15;

  // ========== MONTHLY BREAKDOWN ==========
  doc.setFontSize(14);
  doc.setTextColor(...accentColor);
  doc.text('Monthly Breakdown', margin, y);
  y += 8;

  // Table header
  doc.setFillColor(...primaryColor);
  doc.rect(margin, y - 4, pageWidth - (margin * 2), 8, 'F');
  
  doc.setFontSize(9);
  doc.setTextColor(255, 255, 255);
  doc.text('Month', margin + 3, y);
  doc.text('eGLD', margin + 30, y);
  doc.text('Avg Price (USD)', margin + 60, y);
  doc.text('USD Value', margin + 95, y);
  doc.text('EUR Value', margin + 125, y);
  doc.text('Txns', margin + 155, y);
  y += 8;

  // Table rows
  doc.setTextColor(...textColor);
  doc.setFontSize(9);
  
  let row = 0;
  for (const m of report.monthlyData) {
    if (m.egld > 0) {
      if (row % 2 === 0) {
        doc.setFillColor(250, 250, 250);
        doc.rect(margin, y - 4, pageWidth - (margin * 2), 7, 'F');
      }
      
      doc.setTextColor(...textColor);
      doc.text(m.month, margin + 3, y);
      doc.text(m.egld.toFixed(4), margin + 30, y);
      doc.text(`$${m.avgPrice.toFixed(2)}`, margin + 60, y);
      doc.text(`$${m.usd.toFixed(2)}`, margin + 95, y);
      doc.text(`€${m.eur.toFixed(2)}`, margin + 125, y);
      doc.text(m.txCount.toString(), margin + 155, y);
      y += 7;
      row++;
    }
  }
  y += 10;

  // ========== TRANSACTION DETAILS ==========
  doc.setFontSize(14);
  doc.setTextColor(...accentColor);
  doc.text('Transaction Details', margin, y);
  y += 8;

  // Transaction table header
  doc.setFillColor(...primaryColor);
  doc.rect(margin, y - 4, pageWidth - (margin * 2), 8, 'F');
  
  doc.setFontSize(8);
  doc.setTextColor(255, 255, 255);
  doc.text('Date', margin + 3, y);
  doc.text('Transaction Hash', margin + 25, y);
  doc.text('Provider', margin + 75, y);
  doc.text('eGLD', margin + 115, y);
  doc.text('USD', margin + 140, y);
  y += 8;

  // Transaction rows - ALL TRANSACTIONS
  doc.setFontSize(8);
  row = 0;
  for (const tx of report.transactions) {
    if (y > pageHeight - 40) {
      doc.addPage();
      y = 20;
      doc.setFillColor(...primaryColor);
      doc.rect(margin, y - 4, pageWidth - (margin * 2), 8, 'F');
      doc.setFontSize(8);
      doc.setTextColor(255, 255, 255);
      doc.text('Date', margin + 3, y);
      doc.text('Transaction Hash', margin + 25, y);
      doc.text('Provider', margin + 75, y);
      doc.text('eGLD', margin + 115, y);
      doc.text('USD', margin + 140, y);
      y += 8;
    }
    
    if (row % 2 === 0) {
      doc.setFillColor(250, 250, 250);
      doc.rect(margin, y - 4, pageWidth - (margin * 2), 6, 'F');
    }
    
    doc.setTextColor(...textColor);
    const dateStr = tx.date.length > 10 ? tx.date.substring(0, 10) : tx.date;
    const hashStr = tx.hash.substring(0, 20) + '...';
    const providerStr = (tx.provider || 'Unknown').substring(0, 15);
    
    doc.text(dateStr, margin + 3, y);
    doc.text(hashStr, margin + 25, y);
    doc.text(providerStr, margin + 75, y);
    doc.text(tx.value.toFixed(4), margin + 115, y);
    doc.text(`$${(tx.value * tx.price).toFixed(2)}`, margin + 140, y);
    y += 6;
    row++;
  }
  y += 10;

  // ========== DISCLAIMER ==========
  doc.setFontSize(7);
  doc.setTextColor(...mutedColor);
  const disclaimer = 'This report is for informational purposes only and does not constitute financial or tax advice. Please consult a qualified tax professional for your specific situation. Staking rewards may be subject to taxation in your jurisdiction.';
  const disclaimerLines = doc.splitTextToSize(disclaimer, pageWidth - (margin * 2));
  doc.text(disclaimerLines, margin, y);
  y += disclaimerLines.length * 4 + 5;

  // ========== FOOTER ==========
  doc.setFontSize(8);
  doc.setTextColor(...primaryColor);
  doc.text('MultiversX Staking Tax Report', pageWidth / 2, pageHeight - 10, { align: 'center' });

  // ========== DOWNLOAD ==========
  const pdfBlob = doc.output('blob');
  const pdfUrl = URL.createObjectURL(pdfBlob);
  
  const link = document.createElement('a');
  link.href = pdfUrl;
  link.download = `multiversx-staking-tax-report-${report.year}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  setTimeout(() => URL.revokeObjectURL(pdfUrl), 100);
}

export default function TaxReportTool({ onBack }: Props) {
  const { address: userAddress } = useGetAccount();
  const [address, setAddress] = useState(userAddress || '');
  const [year, setYear] = useState(new Date().getFullYear() - 1);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState({ status: '', count: 0 });
  const [report, setReport] = useState<TaxReport | null>(null);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const { success: txSuccess, pending: txPending } = useGetActiveTransactionsStatus();

  // Refresh payment status and regenerate report when transaction succeeds
  useEffect(() => {
    if (!txSuccess || !address) return;

    const refreshReport = async () => {
      setIsProcessingPayment(false); // Reset loading state
      try {
        // Check updated payment status
        const payment = await checkPaymentStatus(address, year);
        setPaymentStatus(payment);

        // If now paid, regenerate report data to reflect paid status
        if (payment.hasPaid) {
          const prices = await fetchHistoricalPrices(year);
          const { transactions, providers } = await fetchAllStakingRewards(address, year, () => {});
          const calculatedReport = calculateTaxReport(transactions, year, prices);
          calculatedReport.providers = providers;
          setReport(calculatedReport);
        }
      } catch (err) {
        console.error('Failed to refresh report after payment:', err);
      }
    };

    refreshReport();
  }, [txSuccess, address, year]);

  const handleGenerateReport = async () => {
    if (!address) {
      setError('Please enter an address');
      return;
    }
    
    setIsLoading(true);
    setError('');
    setReport(null);
    setPaymentStatus(null);
    
    try {
      // First check payment status
      const payment = await checkPaymentStatus(address, year);
      setPaymentStatus(payment);
      
      // If already paid, generate report directly
      if (payment.hasPaid) {
        console.log('[TaxReport] Report already paid for, generating...');
      }
      
      const { transactions, providers } = await fetchAllStakingRewards(address, year, (status, count) => {
        setProgress({ status, count });
      });
      
      if (transactions.length === 0) {
        setError(`No staking rewards found for ${address} in ${year}`);
        setIsLoading(false);
        return;
      }
      
      const prices = await fetchHistoricalPrices(year);
      const calculatedReport = calculateTaxReport(transactions, year, prices);
      calculatedReport.providers = providers;
      
      setReport(calculatedReport);
    } catch (err) {
      console.error('Failed to generate report:', err);
      setError('Failed to generate report. Please try again.');
    }
    
    setIsLoading(false);
  };

  const handlePayForReport = async () => {
    if (!address || !report) return;
    
    setIsProcessingPayment(true);
    try {
      // Convert bech32 address to hex for contract call
      const addressHex = bech32ToHex(address);
      const yearHex = year.toString(16).padStart(8, '0');
      
      // Build ESDT transfer transaction
      // ESDTTransfer@<token_id_hex>@<value_hex>@<function_hex>@<target_hex>@<year_hex>
      // Value must be in HEX format, not decimal string
      const priceHex = BigInt(REPORT_PRICE_WEI).toString(16);
      const data = `ESDTTransfer@${Buffer.from(COLS_TOKEN_ID).toString('hex')}@${priceHex}@${Buffer.from('payForYear').toString('hex')}@${addressHex}@${yearHex}`;
      
      await sendTransactions({
        transactions: [{
          receiver: TAX_REPORT_CONTRACT,
          data: data,
          value: '0',
          gasLimit: 10000000
        }]
      });
      
      // Transaction sent - payment status will refresh via useEffect when tx succeeds
      // Don't set isProcessingPayment to false here - let the useEffect handle the state update
      
    } catch (err) {
      console.error('Payment failed:', err);
      setError('Payment failed. Please try again.');
      setIsProcessingPayment(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!report) return;
    
    setDownloading(true);
    try {
      await generatePDF(report, address);
    } catch (err) {
      console.error('PDF generation failed:', err);
    }
    setDownloading(false);
  };

  const formatNumber = (num: number, decimals = 2) => {
    if (num >= 1e9) return (num / 1e9).toFixed(decimals) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(decimals) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(decimals) + 'K';
    return num.toFixed(decimals);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button onClick={onBack} className={styles.backButton}>← Back</button>
        <h2>Tax Report Generator</h2>
      </div>

      <div className={styles.inputSection}>
        <div className={styles.inputGroup}>
          <label>Address</label>
          <input
            type='text'
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder='erd1...'
            className={styles.addressInput}
          />
        </div>
        
        <div className={styles.inputGroup}>
          <label>Year</label>
          <select 
            value={year} 
            onChange={(e) => setYear(parseInt(e.target.value))}
            className={styles.yearSelect}
          >
            {[2021, 2022, 2023, 2024, 2025, 2026].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        
        <button 
          onClick={handleGenerateReport}
          disabled={isLoading || !address}
          className={styles.generateButton}
        >
          {isLoading ? 'Generating...' : 'Generate Report'}
        </button>
      </div>

      {isLoading && (
        <div className={styles.progressSection}>
          <div className={styles.spinner}></div>
          <p>{progress.status}</p>
          {progress.count > 0 && <p>Found {progress.count} transactions</p>}
        </div>
      )}

      {error && (
        <div className={styles.errorSection}>
          <p>{error}</p>
        </div>
      )}

      {report && !isLoading && (
        <div className={styles.reportSection}>
          {!paymentStatus?.hasPaid ? (
            <div className={styles.summaryCard}>
              <h3>{report.year} Tax Summary (Preview)</h3>
              <div className={styles.summaryGrid}>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryLabel}>Total EGLD</span>
                  <span className={styles.summaryValue}>{report.totalEgld.toFixed(4)}</span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryLabel}>Total USD</span>
                  <span className={styles.summaryValue}>${formatNumber(report.totalUsd)}</span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryLabel}>Total EUR</span>
                  <span className={styles.summaryValue}>€{formatNumber(report.totalEur)}</span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryLabel}>Transactions</span>
                  <span className={styles.summaryValue}>{report.transactions.length}</span>
                </div>
                <div className={styles.summaryItem}>
                  <span className={styles.summaryLabel}>Providers</span>
                  <span className={styles.summaryValue}>{report.providers.length}</span>
                </div>
              </div>
              
              {report.providers.length > 0 && (
                <div className={styles.providersList}>
                  <strong>Staking Providers Found:</strong>
                  <ul>
                    {report.providers.map((p, i) => (
                      <li key={i}>{p.name}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className={styles.paymentSection}>
                <p className={styles.paymentInfo}>
                  🔒 <strong>Full report locked</strong> - Pay to unlock monthly breakdown, all transactions, and PDF download
                </p>
                <button
                  onClick={handlePayForReport}
                  disabled={isProcessingPayment || txPending}
                  className={styles.payButton}
                >
                  {isProcessingPayment ? 'Processing Payment...' : txPending ? 'Confirming...' : '💰 Pay 5 COLS to Unlock'}
                </button>
                <p className={styles.paymentNote}>
                  Payment is recorded on-chain for {year} tax report
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className={styles.summaryCard}>
                <h3>{report.year} Tax Summary</h3>
                <div className={styles.summaryGrid}>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Total EGLD</span>
                    <span className={styles.summaryValue}>{report.totalEgld.toFixed(4)}</span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Total USD</span>
                    <span className={styles.summaryValue}>${formatNumber(report.totalUsd)}</span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Total EUR</span>
                    <span className={styles.summaryValue}>€{formatNumber(report.totalEur)}</span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Transactions</span>
                    <span className={styles.summaryValue}>{report.transactions.length}</span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Providers</span>
                    <span className={styles.summaryValue}>{report.providers.length}</span>
                  </div>
                </div>
                
                {report.providers.length > 0 && (
                  <div className={styles.providersList}>
                    <strong>Staking Providers Found:</strong>
                    <ul>
                      {report.providers.map((p, i) => (
                        <li key={i}>{p.name}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className={styles.monthlyTable}>
                <h3>Monthly Breakdown</h3>
                <table>
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th>EGLD</th>
                      <th>USD</th>
                      <th>EUR</th>
                      <th>Tx Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.monthlyData.filter(m => m.txCount > 0).map(month => (
                      <tr key={month.month}>
                        <td>{month.month}</td>
                        <td>{month.egld.toFixed(4)}</td>
                        <td>${formatNumber(month.usd)}</td>
                        <td>€{formatNumber(month.eur)}</td>
                        <td>{month.txCount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className={styles.transactionsTable}>
                <h3>All Transactions ({report.transactions.length})</h3>
                <div className={styles.tableWrapper}>
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Provider</th>
                        <th>Amount</th>
                        <th>USD</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.transactions.map((tx, i) => (
                        <tr key={i}>
                          <td>{tx.date}</td>
                          <td>{tx.type}</td>
                          <td>{tx.provider || '-'}</td>
                          <td>{tx.value.toFixed(4)}</td>
                          <td>${(tx.value * tx.price).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className={styles.paymentSuccess}>
                <span>✅ Payment verified - Full report unlocked!</span>
              </div>
              
              <button
                onClick={handleDownloadPDF}
                disabled={downloading}
                className={styles.downloadButton}
              >
                {downloading ? 'Generating PDF...' : '📥 Download PDF Report'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};
