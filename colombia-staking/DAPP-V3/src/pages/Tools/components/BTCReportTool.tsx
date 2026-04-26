import { useState, useEffect } from 'react';
import { useGetAccount } from '@multiversx/sdk-dapp/out/react/account/useGetAccount';
import axios from 'axios';
import styles from './BTCReportTool.module.scss';
import { useColsAprContext } from 'context/ColsAprContext';

interface Props {
  onBack: () => void;
}

// ========== CONSTANTS ==========
const MIN_COLS_FOR_ACCESS = 100; // Minimum COLS staked to access the report

// API endpoint for BTC Report
const BTC_REPORT_SUMMARY_ENDPOINT = 'https://colombia-staking.co/btc-report/summary';

// ========== TYPES ==========
interface BTCReport {
  score: number;
  score_interpretation: string;
  score_detail: string;
  dca_recommendation: string;
  regime: string;
  regime_title: string;
  regime_description: string;
  action: string;
  action_detail: string;
  recommendation: string;
}

// ========== API FETCH ==========
async function fetchBTCReport(): Promise<BTCReport> {
  const response = await axios.get<BTCReport>(BTC_REPORT_SUMMARY_ENDPOINT, {
    timeout: 30000
  });
  return response.data;
}

// ========== COMPONENT ==========
export const BTCReportTool = ({ onBack }: Props) => {
  const { address } = useGetAccount();
  const { stakers, loading: colsLoading } = useColsAprContext();
  const [report, setReport] = useState<BTCReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasAccess, setHasAccess] = useState(false);
  const [showDocs, setShowDocs] = useState(false);
  const [monthlyAmount, setMonthlyAmount] = useState<number>(800);

  // ========== DCA CALCULATOR ==========
  const getDcaMultiplier = (score: number): number => {
    if (score <= 5) return 2.00;
    if (score <= 10) return 1.85;
    if (score <= 15) return 1.70;
    if (score <= 20) return 1.55;
    if (score <= 25) return 1.40;
    if (score <= 30) return 1.25;
    if (score <= 35) return 1.10;
    if (score <= 40) return 0.95;
    if (score <= 45) return 0.80;
    if (score <= 50) return 0.70;
    if (score <= 55) return 0.50;
    if (score <= 60) return 0.25;
    if (score <= 65) return 0.50;
    if (score <= 70) return 0.25;
    if (score <= 75) return 0.0;
    return 0.0;
  };

  const calculateWeeklyDCA = (score: number, monthlyEur: number): { weekly: number; multiplier: number; status: string } => {
    const weeklyBase = monthlyEur / 4.33;
    const multiplier = getDcaMultiplier(score);
    const weekly = weeklyBase * multiplier;
    return { weekly, multiplier, status: multiplier === 0 ? 'STOP' : 'DCA' };
  };

  // Find user's COLS staked from the already-fetched stakers list
  const userColsStaked = address && stakers
    ? (stakers.find((s: { address: string; colsStaked: number }) => s.address.toLowerCase() === address.toLowerCase())?.colsStaked || 0)
    : 0;

  useEffect(() => {
    if (address && !colsLoading) {
      // Use COLS from context (already fetched at login)
      setHasAccess(userColsStaked >= MIN_COLS_FOR_ACCESS);
    }
  }, [address, colsLoading, userColsStaked]);

  useEffect(() => {
    if (address) {
      // Fetch BTC Report
      fetchBTCReport()
        .then(data => {
          // Check if API returned an error response
          if ('error' in data) {
            setError(data.error as string);
            setIsLoading(false);
            return;
          }
          setReport(data as BTCReport);
          setIsLoading(false);
        })
        .catch(err => {
          console.error('[BTC Report] Error:', err);
          setError('Failed to load BTC report. Please try again later.');
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, [address]);

  // ========== RENDER HELPERS ==========
  const getScoreColor = (score: number) => {
    if (score <= 30) return '#22c55e'; // Strong Buy - Green
    if (score <= 50) return '#84cc16'; // Buy - Lime
    if (score <= 65) return '#eab308'; // Neutral - Yellow
    if (score <= 80) return '#f97316'; // Sell - Orange
    return '#ef4444'; // Strong Sell - Red
  };

  const getActionIcon = (action: string) => {
    if (action.includes('ACCUMULATE')) return '📈';
    if (action.includes('HOLD')) return '⏸️';
    if (action.includes('SELL')) return '📉';
    return '➡️';
  };

  const getRegimeIcon = (regime: string) => {
    if (regime.includes('BEAR')) return '🐻';
    if (regime.includes('BULL')) return '🐂';
    if (regime.includes('ACCUMULATION')) return '📦';
    return '📊';
  };

  // ========== INDICATOR DOCUMENTATION ==========
  const INDICATOR_DOCS: Record<string, { name: string; description: string; howToRead: string }> = {
    'MVRV': {
      name: 'Market Value to Realized Value Ratio',
      description: 'Compares the current market cap to the realized cap (average price paid by all holders). When MVRV is below 1, it historically indicates undervaluation.',
      howToRead: 'Below 1.0 = Undervalued (accumulation zone). Above 3.5 = Overvalued (distribution zone).'
    },
    'RSI': {
      name: 'Relative Strength Index',
      description: 'Measures the speed and magnitude of price changes. Ranges from 0 to 100. Traditional overbought/oversold levels are 70/30.',
      howToRead: 'Below 30 = Oversold (potential buy). Above 70 = Overbought (potential sell).'
    },
    'FearGreed': {
      name: 'Fear & Greed Index',
      description: 'Measures overall market sentiment. Extreme fear can be a buying opportunity; extreme greed can signal a top.',
      howToRead: '0-25 = Extreme Fear (buy opportunity). 75-100 = Extreme Greed (sell opportunity).'
    },
    'ETF': {
      name: 'ETF Net Flows (7-Day)',
      description: 'Tracks net inflows/outflows from Bitcoin ETFs. Positive flows suggest institutional demand; negative flows suggest selling pressure.',
      howToRead: 'Positive = Institutional accumulation. Negative = Institutional distribution.'
    },
    'PiCycle': {
      name: 'Pi Cycle Indicator',
      description: 'Uses moving averages to identify market cycle tops and bottoms. When the 111-day MA crosses below the 350-day MA * 2, it historically signals cycle bottoms.',
      howToRead: 'Crossover down = Potential bottom (accumulation). Crossover up = Potential top (distribution).'
    },
    'S2F': {
      name: 'Stock-to-Flow Ratio',
      description: 'Measures the scarcity of Bitcoin by comparing existing supply to annual production. Higher ratio = more scarcity.',
      howToRead: 'Higher S2F = More scarcity = Higher price expectation. Current cycle S2F is unprecedented.'
    },
    'MA50Discount': {
      name: '50-Week Moving Average Discount',
      description: 'Shows how far current price is below the 50-week moving average. Large discounts historically indicate accumulation zones.',
      howToRead: '-30% to -50% discount = Deep accumulation zone. Above MA = Bull market.'
    },
    'Bollinger': {
      name: 'Bollinger Band Position',
      description: 'Shows where current price sits relative to Bollinger Bands (20-week MA ± 2 standard deviations).',
      howToRead: 'Near lower band = Oversold. Near upper band = Overbought. Middle = Neutral.'
    },
    'MACD': {
      name: 'MACD Histogram',
      description: 'Moving Average Convergence Divergence. Shows momentum by comparing 12-week and 26-week EMAs.',
      howToRead: 'Positive histogram = Bullish momentum. Negative = Bearish momentum. Zero line crossover = trend change.'
    },
    'CyclePosition': {
      name: 'Cycle Position (Days Since Halving)',
      description: 'Tracks position within the 4-year halving cycle. Bitcoin returns tend to be highest in the 12-18 months post-halving.',
      howToRead: '365-550 days post-halving = Historically the most profitable period.'
    },
    'MVRVZScore': {
      name: 'MVRV Z-Score',
      description: 'Statistical Z-score of MVRV. Identifies when Bitcoin is extremely over/undervalued relative to its historical norm.',
      howToRead: 'Below 0 = Undervalued. Above 7 = Extremely overvalued (cycle top zone).'
    }
  };

  // ========== LOADING STATE ==========
  if (isLoading) {
    return (
      <div className={styles.container}>
        <button className={styles.backButton} onClick={onBack}>← Back</button>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Loading BTC Report...</p>
        </div>
      </div>
    );
  }

  // ========== NO WALLET ==========
  if (!address) {
    return (
      <div className={styles.container}>
        <button className={styles.backButton} onClick={onBack}>← Back</button>
        <div className={styles.noAccess}>
          <h3>🔐 Wallet Required</h3>
          <p>Please connect your wallet to access the BTC Report.</p>
        </div>
      </div>
    );
  }

  // ========== INSUFFICIENT COLS ==========
  if (!colsLoading && !hasAccess) {
    return (
      <div className={styles.container}>
        <button className={styles.backButton} onClick={onBack}>← Back</button>
        <div className={styles.noAccess}>
          <h3>🔐 Access Required</h3>
          <p>You need at least <strong>{MIN_COLS_FOR_ACCESS} COLS</strong> staked to access this tool.</p>
          <p className={styles.currentBalance}>
            Your COLS staked: <strong>{userColsStaked.toFixed(2)} COLS</strong>
          </p>
          <p className={styles.hint}>
            💡 Stake more COLS to unlock this and other premium tools!
          </p>
        </div>
      </div>
    );
  }

  // ========== ERROR STATE ==========
  if (error || !report) {
    return (
      <div className={styles.container}>
        <button className={styles.backButton} onClick={onBack}>← Back</button>
        <div className={styles.error}>
          <h3>❌ Error</h3>
          <p>{error || 'Failed to load report'}</p>
          <button onClick={() => window.location.reload()}>Try Again</button>
        </div>
      </div>
    );
  }

  // ========== MAIN REPORT VIEW ==========
  return (
    <div className={styles.container}>
      <button className={styles.backButton} onClick={onBack}>← Back</button>
      
      <div className={styles.header}>
        <h2>📊 BTC Strategy Report</h2>
        <p>AI-powered market analysis for Colombia Staking community</p>
      </div>

      {/* Score Card */}
      <div className={styles.scoreCard} style={{ borderColor: getScoreColor(report.score) }}>
        <div className={styles.scoreMain}>
          <div className={styles.scoreValue} style={{ color: getScoreColor(report.score) }}>
            {report.score.toFixed(1)}
          </div>
          <div className={styles.scoreLabel}>/100</div>
        </div>
        <div className={styles.scoreMeta}>
          <div className={styles.scoreInterpretation}>
            {report.score_interpretation}
          </div>
          <div className={styles.dcaRecommendation}>
            DCA: {report.dca_recommendation}
          </div>
        </div>
      </div>

      {/* DCA Calculator */}
      {(() => {
        const { weekly, multiplier, status } = calculateWeeklyDCA(report.score, monthlyAmount);
        return (
          <div className={styles.calculatorCard}>
            <h3>💰 DCA Calculator</h3>
            <p className={styles.calculatorHint}>Enter your monthly BTC investment budget</p>
            
            <div className={styles.inputGroup}>
              <label>Monthly Amount (EUR)</label>
              <input 
                type="number" 
                value={monthlyAmount}
                onChange={(e) => setMonthlyAmount(Number(e.target.value))}
                min={0}
                max={10000}
                step={50}
              />
            </div>
            
            <div className={styles.resultBox}>
              <div className={styles.resultMain}>
                <span className={styles.resultLabel}>Recommended Weekly DCA</span>
                <span className={styles.resultValue}>€{weekly.toFixed(0)}/week</span>
              </div>
              <div className={styles.resultMeta}>
                <span>Multiplier: {(multiplier * 100).toFixed(0)}%</span>
                <span>Score: {report.score.toFixed(1)}/100</span>
              </div>
              {status === 'STOP' && (
                <div className={styles.stopWarning}>
                  ⚠️ Score indicates NOT optimal for DCA - Consider pausing
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {/* Action Card */}
      <div className={styles.actionCard}>
        <div className={styles.actionIcon}>{getActionIcon(report.action)}</div>
        <div className={styles.actionContent}>
          <div className={styles.actionMain}>{report.action}</div>
          <div className={styles.actionDetail}>{report.action_detail}</div>
        </div>
      </div>

      {/* Regime Card */}
      <div className={styles.regimeCard}>
        <div className={styles.regimeHeader}>
          {getRegimeIcon(report.regime)} {report.regime_title}
        </div>
        <p className={styles.regimeDescription}>{report.regime_description}</p>
      </div>

      {/* Documentation Toggle */}
      <button 
        className={styles.docsToggle}
        onClick={() => setShowDocs(!showDocs)}
      >
        📚 {showDocs ? 'Hide' : 'Show'} Indicator Documentation
      </button>

      {/* Indicator Documentation */}
      {showDocs && (
        <div className={styles.docsSection}>
          <h3>📖 Understanding the 11 Indicators</h3>
          
          <div className={styles.docGrid}>
            {Object.entries(INDICATOR_DOCS).map(([key, doc]) => (
              <div key={key} className={styles.docCard}>
                <h4>{doc.name}</h4>
                <p className={styles.docDescription}>{doc.description}</p>
                <div className={styles.docHowToRead}>
                  <strong>How to read:</strong> {doc.howToRead}
                </div>
              </div>
            ))}
          </div>

          <div className={styles.docsFooter}>
            <h3>🎯 How to Use This Report</h3>
            <ul>
              <li><strong>Score 0-50:</strong> Generally favorable for accumulation. Consider increasing DCA.</li>
              <li><strong>Score 50-75:</strong> Neutral to cautious. Maintain current DCA level.</li>
              <li><strong>Score 75+:</strong> Consider reducing DCA and taking some profits.</li>
            </ul>
            <p className={styles.disclaimer}>
              ⚠️ This report is for informational purposes only and does not constitute financial advice. 
              Always do your own research before making investment decisions.
            </p>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className={styles.footer}>
        <p>
          Report generated daily at 8:30 AM (GMT-5). Based on 11 technical and on-chain indicators.
        </p>
      </div>
    </div>
  );
};
// DAPP version: 2026-03-31 - BTC report fix - NEW BUILD
