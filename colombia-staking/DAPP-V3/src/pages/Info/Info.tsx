import { useEffect, useState } from 'react';
import { useGetAccount } from '@multiversx/sdk-dapp/out/react/account/useGetAccount';
import { useNavigate } from 'react-router-dom';
import { useColsAprContext } from '../../context/ColsAprContext';
import { useGlobalContext } from 'context';
import { AnimatedDots } from 'components/AnimatedDots';
import styles from './Info.module.scss';

const NUMBER_OF_NODES = 50;
const SOLAR_POWER_KW = 5.75;
const CPU_CORES = 60;
const MACHINES = 9;
const ISP_COUNT = 4;

// Node status interface (matches status.json format from node_monitor_full.sh)
interface NodeStatus {
  name: string;
  status: string;
  nonce: string;
  epoch?: number;
  peers: string;
  blocksBehind: number;
  version?: string;
  ip?: string;
  // Optional detailed metrics (from node-dashboard API if available)
  cpu?: { percent: number; model: string; cores: string };
  memory?: { percent: number; usedGB: number; totalGB: number; ram: string };
  txPool?: number;
}

interface ValidatorStatus {
  name: string;
  shard: string;
  rating: number;
  tempRating: number;
  leaderFailure: number;
  leaderSuccess: number;
  online: boolean;
}

interface StatusData {
  timestamp: number;
  epoch: string;
  eligibleCount: number;
  observers: NodeStatus[];
  validators: ValidatorStatus[];
}

// Animal leagues (same as RankingTable)
const ANIMAL_LEAGUES = [
  { name: 'Leviathan', icon: '🐉', color: '#9c27b0', range: [0, 1], image: '/leagues/leviathan.jpg', tier: 'Diamond' },
  { name: 'Whale', icon: '🐋', color: '#2196f3', range: [1, 5], image: '/leagues/whale.jpg', tier: 'Platinum' },
  { name: 'Shark', icon: '🦈', color: '#03a9f4', range: [5, 15], image: '/leagues/Shark.jpg', tier: 'Gold' },
  { name: 'Dolphin', icon: '🐬', color: '#00bcd4', range: [15, 30], image: '/leagues/Dolphin.jpg', tier: 'Silver' },
  { name: 'Pufferfish', icon: '🐡', color: '#4caf50', range: [30, 50], image: '/leagues/Pufferfish.jpg', tier: 'Bronze' },
  { name: 'Fish', icon: '🐟', color: '#8bc34a', range: [50, 70], image: '/leagues/Fish.jpg', tier: 'Iron' },
  { name: 'Crab', icon: '🦀', color: '#ff9800', range: [70, 90], image: '/leagues/Crab.jpg', tier: 'Stone' },
  { name: 'Shrimp', icon: '🦐', color: '#f44336', range: [90, 100], image: '/leagues/Shrimp.jpg', tier: 'Wood' }
];

function getLeague(rank: number, total: number) {
  const percentile = (rank / total) * 100;
  return (
    ANIMAL_LEAGUES.find((l) => percentile > l.range[0] && percentile <= l.range[1]) ||
    ANIMAL_LEAGUES[ANIMAL_LEAGUES.length - 1]
  );
}

function formatNumber(num: number, decimals = 2): string {
  if (num >= 1_000_000) {
    return (num / 1_000_000).toFixed(decimals) + 'M';
  }
  if (num >= 1_000) {
    return (num / 1_000).toFixed(decimals) + 'K';
  }
  return num.toFixed(decimals);
}

export const Info = () => {
  const account = useGetAccount();
  const address = account.address;
  const navigate = useNavigate();
  const { loading, stakers, egldPrice, colsPrice, baseApr, agencyLockedEgld } = useColsAprContext();
  const globalDelegatorCount = useGlobalContext().delegatorCount;
  const [isMobile, setIsMobile] = useState(false);
  const [nodeStatus, setNodeStatus] = useState<StatusData | null>(null);
  const [nodeStatusLoading, setNodeStatusLoading] = useState(true);
  const [providerStats, setProviderStats] = useState<{numNodes: number; numUsers: number} | null>(null);

  useEffect(() => {
    if (!address) {
      navigate('/unlock');
    }
  }, [address, navigate]);

  useEffect(() => {
    function handleResize() {
      setIsMobile(window.innerWidth <= 700);
    }
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch node status
  useEffect(() => {
    const fetchNodeStatus = async () => {
      try {
        // Use local DApp status.json to avoid CORS issues
        const response = await fetch('/status.json');
        if (response.ok) {
          const data = await response.json();
          setNodeStatus(data);
        }
      } catch (error) {
        console.error('Failed to fetch node status:', error);
      } finally {
        setNodeStatusLoading(false);
      }
    };
    
    fetchNodeStatus();
    // Refresh every 2 minutes
    const interval = setInterval(fetchNodeStatus, 120000);
    return () => clearInterval(interval);
  }, []);

  // Fetch provider stats (nodes, delegators) from public API
  useEffect(() => {
    const fetchProviderStats = async () => {
      try {
        let nodes = 50;
        let users = 0;
        
        // Use identity API for validators count (same as main website)
        const identityRes = await fetch(
          'https://api.multiversx.com/identities/colombiastaking'
        );
        if (identityRes.ok) {
          const identityData = await identityRes.json();
          nodes = identityData.validators || 50;
        }
        
        // Use provider API for delegator count
        const providerRes = await fetch(
          'https://api.multiversx.com/providers/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf'
        );
        if (providerRes.ok) {
          const providerData = await providerRes.json();
          users = providerData.numUsers || 0;
        }
        
        setProviderStats({ numNodes: nodes, numUsers: users });
      } catch (error) {
        console.error('Failed to fetch provider stats:', error);
      }
    };
    fetchProviderStats();
  }, []);

  // Get delegator count from cached context
  const delegatorCountValue = globalDelegatorCount.status === 'loaded' ? globalDelegatorCount.data : null;

  // Calculate total COLS staked
  const totalColsStaked = stakers.reduce((sum: number, s: any) => sum + (s.colsStaked || 0), 0);

  // Total eGLD in USD
  const totalEgldUsd = agencyLockedEgld && egldPrice ? agencyLockedEgld * egldPrice : 0;

  // Top 10 COLS stakers
  const topStakers = [...stakers]
    .filter((s: any) => s.colsStaked > 0)
    .sort((a: any, b: any) => (b.colsStaked || 0) - (a.colsStaked || 0))
    .slice(0, 10);

  // Get total stakers for league calculation
  const totalStakers = stakers.length;

  return (
    <div className={styles.infoPage}>
      {/* Header Banner */}
      <div className={styles.headerBanner}>
        <h1 className={styles.title}>📊 Colombia Staking Info</h1>
        <p className={styles.subtitle}>"Your trusted staking provider since 2020"</p>
      </div>

      {loading ? (
        <div className={styles.loadingContainer}>
          <AnimatedDots />
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className={styles.statsGrid}>
            {/* Nodes */}
            <div className={styles.statCard}>
              <div className={styles.statIcon}>🖥️</div>
              <div className={styles.statContent}>
                <div className={styles.statLabel}>Active Nodes</div>
                <div className={styles.statValue}>{providerStats?.numNodes || NUMBER_OF_NODES}</div>
                <div className={styles.statSubtext}>Validating on MultiversX</div>
              </div>
            </div>

            {/* Total eGLD Staked */}
            <div className={styles.statCard}>
              <div className={styles.statIcon}>💎</div>
              <div className={styles.statContent}>
                <div className={styles.statLabel}>Total eGLD Staked</div>
                <div className={styles.statValue}>
                  {agencyLockedEgld ? formatNumber(agencyLockedEgld, 0) : '—'}
                </div>
                <div className={styles.statSubtext}>
                  ≈ ${totalEgldUsd ? formatNumber(totalEgldUsd, 0) : '—'}
                </div>
              </div>
            </div>

            {/* Delegators */}
            <div className={styles.statCard}>
              <div className={styles.statIcon}>👥</div>
              <div className={styles.statContent}>
                <div className={styles.statLabel}>Delegators</div>
                <div className={styles.statValue}>
                  {providerStats?.numUsers ? providerStats.numUsers.toLocaleString() :
                   delegatorCountValue !== null ? delegatorCountValue.toLocaleString() : 
                   globalDelegatorCount.status === 'loading' ? '...' : '—'}
                </div>
                <div className={styles.statSubtext}>Trusting our nodes</div>
              </div>
            </div>

            {/* Base APR */}
            <div className={styles.statCard}>
              <div className={styles.statIcon}>📈</div>
              <div className={styles.statContent}>
                <div className={styles.statLabel}>Base APR</div>
                <div className={styles.statValue}>
                  {baseApr ? baseApr.toFixed(2) + '%' : '—'}
                </div>
                <div className={styles.statSubtext}>From blockchain rewards</div>
              </div>
            </div>
          </div>

          {/* Infrastructure Section */}
          <div className={styles.infraSection}>
            <h2 className={styles.sectionTitle}>🖥️ Infrastructure</h2>
            <div className={styles.infraGrid}>
              {/* Solar Power */}
              <div className={styles.infraCard}>
                <div className={styles.infraIcon}>☀️</div>
                <div className={styles.infraContent}>
                  <div className={styles.infraLabel}>Solar Power</div>
                  <div className={styles.infraValue}>{SOLAR_POWER_KW} kW</div>
                  <div className={styles.infraSubtext}>Clean energy</div>
                </div>
              </div>

              {/* CPU Cores */}
              <div className={styles.infraCard}>
                <div className={styles.infraIcon}>⚙️</div>
                <div className={styles.infraContent}>
                  <div className={styles.infraLabel}>CPU Cores</div>
                  <div className={styles.infraValue}>{CPU_CORES}</div>
                  <div className={styles.infraSubtext}>Total processing power</div>
                </div>
              </div>

              {/* Machines */}
              <div className={styles.infraCard}>
                <div className={styles.infraIcon}>🖥️</div>
                <div className={styles.infraContent}>
                  <div className={styles.infraLabel}>Machines</div>
                  <div className={styles.infraValue}>{MACHINES}</div>
                  <div className={styles.infraSubtext}>Validator servers</div>
                </div>
              </div>

              {/* ISP */}
              <div className={styles.infraCard}>
                <div className={styles.infraIcon}>🌐</div>
                <div className={styles.infraContent}>
                  <div className={styles.infraLabel}>ISP Connections</div>
                  <div className={styles.infraValue}>{ISP_COUNT}</div>
                  <div className={styles.infraSubtext}>Redundant connectivity</div>
                </div>
              </div>
            </div>
          </div>

          {/* Network Map Section */}
          <div className={styles.networkMapSection}>
            <h2 className={styles.sectionTitle}>🗺️ Live Network Map</h2>
            <p className={styles.sectionSubtitle}>
              Explore the real-time state of the MultiversX blockchain — see validators, observers, and node distribution worldwide
            </p>
            <div className={styles.networkMapWrapper}>
              <div className={styles.networkMapPreview}>
                <iframe
                  src="https://colombia-staking.co/network/?embed=1"
                  title="MultiversX Network Explorer"
                  loading="eager"
                  allow="fullscreen"
                />
                <a
                  href="https://colombia-staking.co/network/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.networkMapCta}
                >
                  🌐 Open Full Network Explorer
                </a>
              </div>
              <div className={styles.networkMapSidebar}>
                <div className={styles.networkStat}>
                  <span className={styles.networkStatValue}>5,300+</span>
                  <span className={styles.networkStatLabel}>Network Nodes</span>
                </div>
                <div className={styles.networkStat}>
                  <span className={styles.networkStatValue}>50</span>
                  <span className={styles.networkStatLabel}>Colombia Staking Nodes</span>
                </div>
                <div className={styles.networkStat}>
                  <span className={styles.networkStatValue}>60+</span>
                  <span className={styles.networkStatLabel}>Countries</span>
                </div>
                <div className={styles.networkStat}>
                  <span className={styles.networkStatValue}>4</span>
                  <span className={styles.networkStatLabel}>Shards + Metachain</span>
                </div>
                <div className={styles.networkStat}>
                  <span className={styles.networkStatValue}>24/7</span>
                  <span className={styles.networkStatLabel}>Monitoring</span>
                </div>
                <div className={styles.networkInfoCard}>
                  <h4>🗺️ Network Explorer</h4>
                  <p>Our real-time MultiversX network explorer maps validator nodes across the globe using IP geolocation. Hover nodes to see identity, shard, and provider details.</p>
                  <ul>
                    <li>🔴 P2P connections directly observed</li>
                    <li>🔵 Identity-based peer matching</li>
                    <li>🟢 Name/location-based grouping</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Node Status Section */}
          <div className={styles.nodeStatusSection}>
            <h2 className={styles.sectionTitle}>🟢 Node Status</h2>
            <p className={styles.sectionSubtitle}>
              Real-time status of our displayed validator nodes
            </p>
            
            {nodeStatusLoading ? (
              <div className={styles.loadingContainer}>
                <AnimatedDots />
              </div>
            ) : nodeStatus && nodeStatus.observers ? (
              <>
                <div className={styles.nodeStatusGrid}>
                  {nodeStatus.observers.map((node) => (
                    <div key={node.name} className={`${styles.nodeCard} ${styles[node.status.toLowerCase()] || styles.unknown}`}>
                      <div className={styles.nodeHeader}>
                        <span className={styles.nodeName}>{node.name}</span>
                        <span className={`${styles.statusBadge} ${styles[node.status.toLowerCase()] || styles.unknown}`}>
                          {node.status === 'SYNC' && '✓'}
                          {node.status === 'SLOW' && '⚠'}
                          {node.status === 'LAG' && '🔄'}
                          {node.status === 'DESYNC' && '✗'}
                          {node.status === 'ERROR' && '💀'}
                          {node.status === 'DOWN' && '🔴'}
                          {node.status === 'UNKNOWN' && '❓'}
                          {' '}{node.status}
                        </span>
                      </div>
                      
                      {/* Show detailed metrics if available (from node-dashboard) */}
                      {node.cpu && node.memory && (
                        <div className={styles.nodeMetrics}>
                          <div className={styles.metricPair}>
                            <span className={styles.metricLabel}>CPU</span>
                            <div className={styles.metricBar}>
                              <div 
                                className={`${styles.metricFill} ${node.cpu.percent > 80 ? styles.danger : node.cpu.percent > 50 ? styles.warning : ''}`}
                                style={{ width: `${node.cpu.percent}%` }}
                              />
                            </div>
                            <span className={styles.metricValue}>{node.cpu.percent}%</span>
                          </div>
                          
                          <div className={styles.metricPair}>
                            <span className={styles.metricLabel}>RAM</span>
                            <div className={styles.metricBar}>
                              <div 
                                className={`${styles.metricFill} ${node.memory.percent > 90 ? styles.danger : node.memory.percent > 70 ? styles.warning : ''}`}
                                style={{ width: `${node.memory.percent}%` }}
                              />
                            </div>
                            <span className={styles.metricValue}>{node.memory.percent}%</span>
                          </div>
                        </div>
                      )}
                      
                      <div className={styles.nodeDetails}>
                        <span>🌐 {node.peers || '?'} peers</span>
                        {node.txPool !== undefined && <span>📦 {node.txPool} tx</span>}
                        {!isMobile && <span>⏱️ {node.blocksBehind !== undefined ? node.blocksBehind : '?'} behind</span>}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Validators summary */}
                {nodeStatus.validators && nodeStatus.validators.length > 0 && (
                  <div className={styles.validatorsSection} style={{ marginTop: '2rem' }}>
                    <h3 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>
                      🏆 {nodeStatus.eligibleCount} Eligible Validators
                    </h3>
                    <div className={styles.nodeStatusGrid}>
                      {nodeStatus.validators.map((v) => (
                        <div key={v.name} className={`${styles.nodeCard} ${v.online ? styles.sync : styles.error}`}>
                          <div className={styles.nodeHeader}>
                            <span className={styles.nodeName}>{v.name}</span>
                            <span className={`${styles.statusBadge} ${v.online ? styles.sync : styles.error}`}>
                              {v.online ? '✓ ONLINE' : '🔴 OFFLINE'}
                            </span>
                          </div>
                          <div className={styles.nodeDetails}>
                            <span>📍 Shard {v.shard}</span>
                            <span>⭐ Rating: {v.rating}</span>
                            {v.leaderFailure > 0 && (
                              <span style={{ color: '#ff6b6b' }}>⚠️ {v.leaderFailure} failures</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className={styles.statusFooter}>
                  <span>Epoch: {nodeStatus.epoch}</span>
                  <span>•</span>
                  <span>Updated: {new Date(Number(nodeStatus.timestamp) * 1000).toLocaleTimeString()}</span>
                </div>
              </>
            ) : (
              <div className={styles.statusUnavailable}>
                <p>⚠️ Node status temporarily unavailable</p>
                <a 
                  href="https://colombia-staking.com/node-status.html" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={styles.statusLink}
                >
                  View on website →
                </a>
              </div>
            )}
          </div>

          {/* Prices Section */}
          <div className={styles.pricesSection}>
            <h2 className={styles.sectionTitle}>💲 Token Prices</h2>
            <div className={styles.pricesGrid}>
              <div className={styles.priceCard}>
                <div className={styles.tokenLogo}>🔵</div>
                <div className={styles.priceInfo}>
                  <div className={styles.tokenName}>eGLD</div>
                  <div className={styles.priceValue}>
                    ${egldPrice ? egldPrice.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                  </div>
                </div>
              </div>
              <div className={styles.priceCard}>
                <div className={styles.tokenLogo}>🟣</div>
                <div className={styles.priceInfo}>
                  <div className={styles.tokenName}>COLS</div>
                  <div className={styles.priceValue}>
                    ${colsPrice ? Number(colsPrice).toLocaleString(undefined, { maximumFractionDigits: 6 }) : '—'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* COLS Staking Stats */}
          <div className={styles.colsSection}>
            <h2 className={styles.sectionTitle}>🎯 COLS Staking</h2>
            <div className={styles.colsStats}>
              <div className={styles.colsStat}>
                <span className={styles.colsLabel}>Total COLS Staked</span>
                <span className={styles.colsValue}>
                  {totalColsStaked ? formatNumber(totalColsStaked, 0) : '—'}
                </span>
              </div>
              <div className={styles.colsStat}>
                <span className={styles.colsLabel}>COLS Stakers</span>
                <span className={styles.colsValue}>
                  {stakers.filter((s: any) => s.colsStaked > 0).length.toLocaleString()}
                </span>
              </div>
            </div>
            
            {/* COLS Token Properties */}
            <div className={styles.colsProperties}>
              <h3 className={styles.colsPropsTitle}>📜 COLS Token Properties</h3>
              <ul className={styles.colsPropsList}>
                <li><strong>Max Supply:</strong> 150,000 COLS (fixed, never more)</li>
                <li><strong>Already Circulating:</strong> All 150,000 COLS in circulation</li>
                <li><strong>Token Utility:</strong> Staking + DAO rewards + Bonus APR</li>
              </ul>
            </div>
          </div>

          {/* Top 10 COLS Stakers - Card Layout */}
          <div className={styles.topStakersSection}>
            <h2 className={styles.sectionTitle}>🏆 Top 10 COLS Stakers</h2>
            <p className={styles.sectionSubtitle}>
              Ranked by COLS tokens staked
            </p>
            
            <div className={styles.leagueCardsGrid}>
              {topStakers.map((staker: any, index: number) => {
                const league = staker.rank && totalStakers 
                  ? getLeague(staker.rank, totalStakers) 
                  : ANIMAL_LEAGUES[7];
                const shortAddress = `${staker.address.slice(0, 6)}...${staker.address.slice(-4)}`;
                const isTop3 = index < 3;
                
                return (
                  <div 
                    key={staker.address} 
                    className={`${styles.leagueCard} ${isTop3 ? styles.leagueCardTop : ''}`}
                    style={{ 
                      '--league-color': league.color,
                      '--league-gradient': `linear-gradient(135deg, ${league.color}33, ${league.color}11)`
                    } as React.CSSProperties}
                  >
                    <div className={styles.leagueCardRank}>
                      {index === 0 && <span className={styles.rankMedal} style={{background: 'linear-gradient(135deg, #ffd700, #ffaa00)'}}>🥇</span>}
                      {index === 1 && <span className={styles.rankMedal} style={{background: 'linear-gradient(135deg, #c0c0c0, #a0a0a0)'}}>🥈</span>}
                      {index === 2 && <span className={styles.rankMedal} style={{background: 'linear-gradient(135deg, #cd7f32, #a05020)'}}>🥉</span>}
                      {index > 2 && <span className={styles.rankNumber}>#{index + 1}</span>}
                    </div>
                    
                    <div className={styles.leagueCardMain}>
                      <div className={styles.leagueCardHeader}>
                        <img src={league.image} alt={league.name} className={styles.leagueCardImage} />
                        <div className={styles.leagueCardInfo}>
                          <span className={styles.leagueCardName}>{league.name}</span>
                          <span className={styles.leagueCardTier}>{league.tier} Tier</span>
                        </div>
                      </div>
                      
                      <div className={styles.leagueCardStats}>
                        <div className={styles.leagueCardStat}>
                          <span className={styles.leagueCardStatLabel}>COLS</span>
                          <span className={styles.leagueCardStatValue}>{staker.colsStaked ? formatNumber(staker.colsStaked, 0) : '—'}</span>
                        </div>
                        <div className={styles.leagueCardStat}>
                          <span className={styles.leagueCardStatLabel}>eGLD</span>
                          <span className={styles.leagueCardStatValue}>{staker.egldStaked ? formatNumber(staker.egldStaked, 2) : '—'}</span>
                        </div>
                        <div className={styles.leagueCardStat}>
                          <span className={styles.leagueCardStatLabel}>APR</span>
                          <span className={styles.leagueCardStatValue} style={{color: '#6ee7c7'}}>{staker.aprTotal ? staker.aprTotal.toFixed(2) + '%' : '—'}</span>
                        </div>
                      </div>
                      
                      <a 
                        href={`https://explorer.multiversx.com/accounts/${staker.address}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.leagueCardAddress}
                      >
                        {shortAddress} ↗
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Info Footer */}
          <div className={styles.infoFooter}>
            <div className={styles.linksRow}>
              <a 
                href="https://colombia-staking.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className={styles.footerLink}
              >
                🌐 Website
              </a>
              <a 
                href="https://x.com/ColombiaStaking" 
                target="_blank" 
                rel="noopener noreferrer"
                className={styles.footerLink}
              >
                𝕏 Twitter
              </a>
              <a 
                href="https://github.com/colombiastaking" 
                target="_blank" 
                rel="noopener noreferrer"
                className={styles.footerLink}
              >
                📂 GitHub
              </a>
            </div>
            <p className={styles.footerText}>
              Colombia Staking — 50 nodes securing the MultiversX network from Colombia 🇨🇴
            </p>
          </div>
        </>
      )}
    </div>
  );
};