import { useGetAccount } from '@multiversx/sdk-dapp/out/react/account/useGetAccount';
import { Link } from 'react-router-dom';
import { useGlobalContext } from 'context';
import { useColsAprContext } from '../../context/ColsAprContext';
import { useGoldMember, calculateEffectiveApr, getRawApr } from '../../hooks/useGoldMember';
import { AnimatedDots } from 'components/AnimatedDots';
import { HelpIcon } from 'components/HelpIcon';
import { ColsAprTable } from 'components/ColsAprTable';
import { RankingTable } from 'components/Stake/RankingTable';

import styles from './styles.module.scss';

function formatNumber(amount: number | string, decimals = 6) {
  const num = typeof amount === 'string' ? Number(amount) : amount;
  if (isNaN(num)) return '0';
  return num.toLocaleString(undefined, { maximumFractionDigits: decimals });
}

function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${Math.floor(value).toLocaleString()}`;
}

// League info helper - matches RankingTable
const ANIMAL_LEAGUES = [
  { name: 'Leviathan', icon: '🐉', color: '#9c27b0', range: [0, 1], gradient: 'linear-gradient(135deg, #9c27b0, #7b1fa2)', image: '/leagues/leviathan.jpg', tier: 'Diamond' },
  { name: 'Whale', icon: '🐋', color: '#2196f3', range: [1, 5], gradient: 'linear-gradient(135deg, #2196f3, #1565c0)', image: '/leagues/whale.jpg', tier: 'Platinum' },
  { name: 'Shark', icon: '🦈', color: '#03a9f4', range: [5, 15], gradient: 'linear-gradient(135deg, #03a9f4, #0097a7)', image: '/leagues/Shark.jpg', tier: 'Gold' },
  { name: 'Dolphin', icon: '🐬', color: '#00bcd4', range: [15, 30], gradient: 'linear-gradient(135deg, #00bcd4, #009688)', image: '/leagues/Dolphin.jpg', tier: 'Silver' },
  { name: 'Pufferfish', icon: '🐡', color: '#4caf50', range: [30, 50], gradient: 'linear-gradient(135deg, #4caf50, #388e3c)', image: '/leagues/Pufferfish.jpg', tier: 'Bronze' },
  { name: 'Fish', icon: '🐟', color: '#8bc34a', range: [50, 70], gradient: 'linear-gradient(135deg, #8bc34a, #689f38)', image: '/leagues/Fish.jpg', tier: 'Iron' },
  { name: 'Crab', icon: '🦀', color: '#ff9800', range: [70, 90], gradient: 'linear-gradient(135deg, #ff9800, #f57c00)', image: '/leagues/Crab.jpg', tier: 'Stone' },
  { name: 'Shrimp', icon: '🦐', color: '#f44336', range: [90, 100], gradient: 'linear-gradient(135deg, #f44336, #d32f2f)', image: '/leagues/Shrimp.jpg', tier: 'Wood' },
];

function getLeagueInfo(rank: number, total: number) {
  const percentile = (rank / total) * 100;
  return ANIMAL_LEAGUES.find(l => percentile > l.range[0] && percentile <= l.range[1]) || ANIMAL_LEAGUES[ANIMAL_LEAGUES.length - 1];
}

function getLeagueClass(rank: number, total: number): string {
  const league = getLeagueInfo(rank, total);
  return league.name.toLowerCase();
}

export const Home = () => {
  const account = useGetAccount();
  const address = account.address;
  const { stakers, loading, egldPrice, colsPrice, baseApr, aprMax, numNodes } = useColsAprContext();
  const { userActiveStake } = useGlobalContext();
  
  // Combined loading state: data is ready when BOTH ColsAprContext AND userActiveStake are loaded
  const isDataReady = !loading && userActiveStake.status === 'loaded';
  
  // Gold Member detection
  const { isGoldMember, goldNftCount, goldCapacityEgld } = useGoldMember(address);
  
  // Find user row in stakers (case-insensitive comparison)
  const userRow = stakers.find((s: any) => s.address.toLowerCase() === address.toLowerCase()) ?? null;
  
  // Get delegated eGLD from context (converted from raw to eGLD)
  const delegatedEgld = userActiveStake.status === 'loaded' 
    ? Number(userActiveStake.data || '0') / 1e18 
    : 0;

  // Get eGLD from stakers data
  const egldDelegatedFromStakers = userRow?.egldStaked ?? 0;
  const colsStaked = userRow?.colsStaked ?? 0;

  // Priority for eGLD:
  // 1. If user in stakers and has valid eGLD → use stakers
  // 2. If user in stakers but eGLD = 0 (failed query) → use context
  // 3. If user not in stakers → use context
  const actualEgldDelegated = (userRow && egldDelegatedFromStakers > 0) 
    ? egldDelegatedFromStakers 
    : delegatedEgld;
  
  // Calculate Gold member effective APR (without service fee = bruto)
  const rawBaseApr = getRawApr(baseApr);
  const { goldBonusApr } = calculateEffectiveApr(baseApr, actualEgldDelegated, goldCapacityEgld);
  
  // Get user's APR from stakers data
  const userBaseApr = userRow?.aprTotal !== null && userRow?.aprTotal !== undefined 
    ? Number(userRow.aprTotal) 
    : null;
  
  const userAprBonusOnly = userRow?.aprBonus ?? null;
  
  // Gold member total: base APR + Gold Bonus (shown as raw/bruto APR)
  const goldBrutoApr = userBaseApr !== null ? userBaseApr + goldBonusApr : (userAprBonusOnly !== null ? baseApr + userAprBonusOnly + goldBonusApr : null);

  const totalUsd =
    (actualEgldDelegated * Number(egldPrice || 0)) +
    (Number(colsStaked) * Number(colsPrice || 0));

  const totalStakers = stakers.length;

  // Total APR shown in main panel:
  const userApr = userBaseApr !== null 
    ? userBaseApr + goldBonusApr  // User in stakers + Gold bonus
    : (userAprBonusOnly !== null 
        ? baseApr + userAprBonusOnly + goldBonusApr  // Has COLS bonus only + Gold
        : (isGoldMember && goldBonusApr > 0 ? rawBaseApr + goldBonusApr : null));
  const userRank = userRow?.rank;
  const leagueInfo = userRank && totalStakers > 0 
    ? getLeagueInfo(userRank, totalStakers) 
    : null;

  const totalAprHelpText = `Total APR represents your annual percentage rate based on your staking position.

• If you have eGLD delegated, the Total APR applies to your eGLD delegation.
• If you stake COLS tokens, you earn additional APR bonus.
${isGoldMember ? `\n🌟 GOLD MEMBER: You have ${goldNftCount} Gold NFT(s) giving ${goldCapacityEgld} eGLD at 0% service fee!\n• Gold Bonus APR: +${goldBonusApr.toFixed(2)}%\n• Your Bruto APR: ${goldBrutoApr !== null ? goldBrutoApr.toFixed(2) + '%' : '—'}` : ''}

This ensures the APR reflects your actual staking position.`;

  // Check if user has no holdings
  const hasNoHoldings = actualEgldDelegated === 0 && Number(colsStaked) === 0;
  // const hasEgldButNoCols = actualEgldDelegated > 0 && Number(colsStaked) === 0;
  // const hasColsButLittle = Number(colsStaked) > 0 && Number(colsStaked) < 100;
  // const hasColsOnly = Number(colsStaked) > 0 && actualEgldDelegated === 0;

  // Potential rewards calculator for new users
  const potentialExamples = [
    { egld: 100, cols: 0, desc: 'eGLD Only', apr: baseApr },
    { egld: 100, cols: 50, desc: 'With COLS', apr: baseApr + 2 },
    { egld: 100, cols: 200, desc: 'COLS Boost', apr: baseApr + 5 },
  ];

  const aprBonusMax = aprMax;

  // Determine hero class based on league
  const heroClass = (userRank && totalStakers > 0) 
    ? getLeagueClass(userRank, totalStakers) 
    : 'default';

  return (
    <div className={styles.landing}>
      {/* Gold Member Hero Banner - Show for Gold members with holdings */}
      {isGoldMember && actualEgldDelegated > 0 && !hasNoHoldings && (
        <section className={styles.goldHeroBanner}>
          <div className={styles.goldHeroContent}>
            <div className={styles.goldHeroBadge}>
              <span className={styles.goldHeroIcon}>👑</span>
              <span>GOLD MEMBER</span>
            </div>
            <h2 className={styles.goldHeroTitle}>Welcome back, Gold Member!</h2>
            <p className={styles.goldHeroText}>
              You have <strong>{goldNftCount} Gold NFT{goldNftCount > 1 ? 's' : ''}</strong> giving you 
              <strong> {goldCapacityEgld} eGLD</strong> at 0% service fee
            </p>
            <div className={styles.goldHeroStats}>
              <div className={styles.goldHeroStat}>
                <span className={styles.goldHeroStatValue}>+{goldBonusApr.toFixed(2)}%</span>
                <span className={styles.goldHeroStatLabel}>APR Bonus</span>
              </div>
              <div className={styles.goldHeroStatDivider}></div>
              <div className={styles.goldHeroStat}>
                <span className={styles.goldHeroStatValue}>{goldBrutoApr !== null ? goldBrutoApr.toFixed(2) + '%' : '—'}</span>
                <span className={styles.goldHeroStatLabel}>Your Effective APR</span>
              </div>
              <div className={styles.goldHeroStatDivider}></div>
              <div className={styles.goldHeroStat}>
                <span className={styles.goldHeroStatValue}>0%</span>
                <span className={styles.goldHeroStatLabel}>Service Fee</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Empty State Welcome - for new users */}
      {hasNoHoldings && address && (
        <>
          <section className={styles.welcomeBanner}>
            <div className={styles.welcomeIcon}>🚀</div>
            <div className={styles.welcomeContent}>
              <h2 className={styles.welcomeTitle}>Welcome to Colombia Staking!</h2>
              <p className={styles.welcomeText}>
                {!isDataReady ? (
                  <AnimatedDots />
                ) : (
                  <>
                    You're not staking yet. Start earning <strong>{baseApr.toFixed(1)}% APY</strong> on your eGLD today — and up to <strong>{baseApr + aprBonusMax}%</strong> with COLS!
                  </>
                )}
              </p>
              <div className={styles.welcomeBenefits}>
                <div className={styles.welcomeBenefit}>
                  <span>🛡️</span> {numNodes} Nodes - Most secure agency
                </div>
                <div className={styles.welcomeBenefit}>
                  <span>🇨🇴</span> Colombian operations
                </div>
                <div className={styles.welcomeBenefit}>
                  {!isDataReady ? <AnimatedDots /> : <><span>💎</span> Up to +{aprBonusMax}% COLS bonus</>}
                </div>
              </div>
            </div>
          </section>

          {/* Potential Earnings Calculator */}
          <section className={styles.potentialSection}>
            <h3 className={styles.potentialTitle}>💰 What Could You Earn?</h3>
            <p className={styles.potentialSubtitle}>
              {!isDataReady ? <AnimatedDots /> : <>Base APR: {baseApr.toFixed(1)}% • COLS bonus: up to +{aprBonusMax}%</>}
            </p>
            <div className={styles.potentialGrid}>
              {potentialExamples.map((example, i) => {
                const yearlyEgld = example.egld * (example.apr / 100);
                const egldPriceNum = Number(egldPrice) || 0;
                return (
                  <div key={i} className={styles.potentialCard}>
                    <div className={styles.potentialLabel}>{example.desc}</div>
                    <div className={styles.potentialStake}>
                      {example.egld} eGLD + {example.cols} COLS
                    </div>
                    <div className={styles.potentialReward}>
                      +{yearlyEgld.toFixed(1)} eGLD/year
                    </div>
                    <div className={styles.potentialUsd}>
                      ≈ ${(yearlyEgld * egldPriceNum).toFixed(0)}/year
                    </div>
                    <div className={styles.potentialApr}>
                      {example.apr.toFixed(1)}% APR
                    </div>
                    {example.cols > 0 && (
                      <div className={styles.potentialBonus}>+COLS bonus!</div>
                    )}
                  </div>
                );
              })}
            </div>
            <Link to="/delegate" className={styles.potentialCta}>
              Start Earning Now →</Link>
          </section>
        </>
      )}

      {/* Upsell Banner - has eGLD but no COLS */}
      {/* {hasEgldButNoCols && address && (
        <section className={styles.upsellBanner}>
          <div className={styles.upsellIcon}>🔥</div>
          <div className={styles.upsellContent}>
            <h3 className={styles.upsellTitle}>Boost Your APR!</h3>
            <p className={styles.upsellText}>
              {!isDataReady ? (
                <AnimatedDots />
              ) : (
                <>Stake COLS tokens to earn up to <strong>+{aprBonusMax}% bonus APR</strong> on your eGLD delegation. The more COLS you stake relative to eGLD, the higher your bonus!</>
              )}
            </p>
          </div>
          <Link to="/stake" className={styles.upsellButton}>Stake COLS →</Link>
        </section>
      )} */}

      {/* Upsell Banner - has some COLS but not enough */}
      {/* {hasColsButLittle && address && (
        <section className={styles.upsellBannerCols}>
          <div className={styles.upsellIcon}>💎</div>
          <div className={styles.upsellContent}>
            <h3 className={styles.upsellTitle}>Level Up Your Staking!</h3>
            <p className={styles.upsellText}>
              Stake more COLS to unlock the <strong>Diamond League</strong> and earn even higher rewards!
            </p>
          </div>
          <Link to="/stake" className={styles.upsellButtonCols}>Stake More →</Link>
        </section>
      )} */}

      {/* COLS-Only Banner - has COLS but no eGLD */}
      {/* {hasColsOnly && address && (
        <section className={styles.colsOnlyBanner}>
          <div className={styles.colsOnlyIcon}>🎯</div>
          <div className={styles.colsOnlyContent}>
            <h3 className={styles.colsOnlyTitle}>Maximize Your Rewards!</h3>
            <p className={styles.colsOnlyText}>
              You have COLS staked earning <strong>DAO rewards</strong>. Delegate eGLD to also earn base APR + bonus on your eGLD!
            </p>
          </div>
          <Link to="/delegate" className={styles.colsOnlyButton}>Delegate eGLD →</Link>
        </section>
      )} */}

      {/* League Hero Section - Main showcase when user has holdings */}
      {address && !hasNoHoldings && (
        <section className={`${styles.heroSection} ${heroClass}`}>
          <div className={styles.heroContent}>
            {/* Animal Image */}
            <div className={styles.heroAnimal}>
              {leagueInfo ? (
                <>
                  <img src={leagueInfo.image} alt={leagueInfo.name} />
                  <div className={styles.leagueBadge}>
                    <div className={styles.tier}>{leagueInfo.tier}</div>
                    <div className={styles.name}>{leagueInfo.name}</div>
                  </div>
                </>
              ) : (
                <div style={{ width: 180, height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 80, background: 'rgba(255,255,255,0.1)', borderRadius: 30 }}>
                  🏆
                </div>
              )}
            </div>

            {/* Info */}
            <div className={styles.heroInfo}>
              <h1 className={styles.heroGreeting}>
                Welcome, <span>Staker</span> 👋
              </h1>
              
              {/* Rank Badge */}
              {userRank && (
                <div className={styles.heroRank}>
                  <span className={styles.rankNumber}>#{userRank}</span>
                  <span>of {totalStakers.toLocaleString()} stakers</span>
                </div>
              )}

              {/* Stats */}
              <div className={styles.heroStats}>
                <div className={styles.heroStat}>
                  <span className={styles.value}>
                    {userApr !== null ? `${userApr.toFixed(1)}%` : '—'}
                  </span>
                  <span className={styles.label}>Your APR</span>
                </div>
                <div className={styles.heroStat}>
                  <span className={styles.value}>
                    {!isDataReady ? '—' : formatNumber(actualEgldDelegated, 2)}
                  </span>
                  <span className={styles.label}>eGLD</span>
                </div>
                <div className={styles.heroStat}>
                  <span className={styles.value}>
                    {!isDataReady ? '—' : formatNumber(colsStaked, 0)}
                  </span>
                  <span className={styles.label}>COLS</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Asset Cards Grid */}
      {address && (
        <div className={styles.assetGrid}>
          {/* eGLD Card */}
          <div className={styles.assetCard}>
            <div className={styles.assetIcon}>💎</div>
            <div className={styles.assetLabel}>eGLD Delegated</div>
            <div className={`${styles.assetValue} ${styles.assetValuePrimary}`}>
              {!isDataReady ? (
                <><AnimatedDots /></>
              ) : (
                formatNumber(actualEgldDelegated, 4)
              )}
            </div>
            <div className={styles.assetUsd}>
              ≈ ${Math.floor(actualEgldDelegated * Number(egldPrice || 0)).toLocaleString()}
            </div>
          </div>

          {/* COLS Card */}
          <div className={styles.assetCardAccent}>
            <div className={styles.assetIconAccent}>🪙</div>
            <div className={styles.assetLabel}>COLS Staked</div>
            <div className={`${styles.assetValue} ${styles.assetValueAccent}`}>
              {!isDataReady ? <><AnimatedDots /></> : formatNumber(colsStaked, 2)}
            </div>
            <div className={styles.assetUsd}>
              ≈ ${(Number(colsStaked) * Number(colsPrice || 0)).toFixed(2)}
            </div>
          </div>

          {/* Total Value Card */}
          <div className={styles.assetCardTotal}>
            <div className={styles.assetIcon}>💰</div>
            <div className={styles.assetLabel}>Total Portfolio Value</div>
            <div className={styles.totalValue}>
              {Number.isFinite(totalUsd) ? formatCurrency(totalUsd) : '$0'}
            </div>
            <div className={styles.hint}>
              COLS ${Number(colsPrice || 0).toLocaleString(undefined, { maximumFractionDigits: 4 })} 
              {' '}• eGLD ${Number(egldPrice || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>
      )}

      {/* APR Panel */}
      <section className={`${styles.aprPanel} ${heroClass}`}>
        <div className={styles.aprHeader}>
          Your Total APR
          <HelpIcon text={totalAprHelpText} />
        </div>

        <div className={styles.aprCard}>
          <div className={styles.aprLabel}>Annual Percentage Rate</div>
          <div className={`${styles.aprValue} ${styles.aprValueLarge}`}>
            {!isDataReady ? <><AnimatedDots /></> : userApr !== null ? `${userApr.toFixed(2)}%` : '—'}
            {isDataReady && isGoldMember && goldBonusApr > 0 && <span className={styles.goldBonusBadge}> +{goldBonusApr.toFixed(2)}% Gold</span>}
          </div>
        </div>

        <div className={styles.baseAprRow}>
          Base APR: <span className={styles.baseAprValue}>
            {!isDataReady ? <AnimatedDots /> : `${baseApr.toFixed(2)}%`}
          </span>
          <HelpIcon text="Base APR is the standard annual percentage rate for all delegators, before any COLS bonus." />
        </div>

        {/* Ranking Badge */}
        {userRank !== null && userRank !== undefined && (
          <div className={styles.rankingBadge}>
            {leagueInfo?.image ? (
              <img src={leagueInfo.image} alt={leagueInfo.name} className={styles.rankingBadgeImage} />
            ) : (
              <span className={styles.rankingBadgeIcon}>{leagueInfo?.icon}</span>
            )}
            <span>
              <span className={styles.rankingBadgeRank}>#{userRank}</span> · {leagueInfo?.tier} Tier
            </span>
          </div>
        )}

        {/* Stats Row */}
        <div className={styles.statsRow}>
          <div className={styles.statItem}>
            <div className={`${styles.statValue} ${styles.statValuePrimary}`}>
              {!isDataReady ? '—' : userApr !== null ? `${(userApr - baseApr).toFixed(2)}%` : '—'}
            </div>
            <div className={styles.statLabel}>Bonus APR</div>
          </div>
          <div className={styles.statItem}>
            {leagueInfo?.image ? (
              <img src={leagueInfo.image} alt={leagueInfo.name} style={{width: 44, height: 44, borderRadius: 14, marginBottom: 6, border: `2px solid ${leagueInfo.color}`}} />
            ) : (
              <div className={`${styles.statValue} ${styles.assetValueAccent}`}>
                {!isDataReady ? '—' : (leagueInfo?.name || '—')}
              </div>
            )}
            <div className={styles.statLabel}>{leagueInfo?.tier} Tier</div>
          </div>
          <div className={styles.statItem}>
            <div className={styles.statValue}>
              {!isDataReady ? '—' : (((actualEgldDelegated * Number(egldPrice || 0) + Number(colsStaked) * Number(colsPrice || 0)) > 0 && baseApr)
                ? `$${Math.floor((actualEgldDelegated * Number(egldPrice || 0) + Number(colsStaked) * Number(colsPrice || 0)) * (Number(baseApr) / 100)).toLocaleString()}`
                : '$0')}
            </div>
            <div className={styles.statLabel}>Est. Yearly Reward</div>
          </div>
        </div>
      </section>

      {/* Ranking Table */}
      <RankingTable />
      
      {/* Admin Table (only visible for target user) */}
      <ColsAprTable />
    </div>
  );
};

export default Home;
