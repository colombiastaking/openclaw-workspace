<?php
// stats-api.php - Dynamic Colombia Staking stats from MultiversX API
// Fetches: nodes, total staked, total distributed (eGLD rewards from protocol)

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Cache-Control: max-age=300'); // Cache for 5 minutes

// MultiversX API endpoints
$IDENTITY_API = "https://api.multiversx.com/identities/colombiastaking";
$PROVIDER_API = "https://api.multiversx.com/providers/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqallllls5rqmaf";
$COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=elrond-erd-2&vs_currencies=usd";

function apiCall($url, $timeout = 10) {
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Accept: application/json']);
    $resp = curl_exec($ch);
    $http = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return $http === 200 ? json_decode($resp, true) : null;
}

$results = [
    'success' => true,
    'timestamp' => date('c')
];

// 1. Get identity info (validators count)
$identityData = apiCall($IDENTITY_API);
if ($identityData) {
    $results['validators'] = $identityData['validators'] ?? 0;
    $results['stake'] = isset($identityData['stake']) ? floatval($identityData['stake']) / 1e18 : 0;
    $results['topUp'] = isset($identityData['topUp']) ? floatval($identityData['topUp']) / 1e18 : 0;
    $results['totalStaked'] = round($results['stake'] + $results['topUp'], 2);
}

// 2. Get provider data for cumulatedRewards
$providerData = apiCall($PROVIDER_API);
if ($providerData) {
    $results['delegators'] = $providerData['numUsers'] ?? 0;
    $results['apr'] = $providerData['apr'] ?? 0;
    $results['serviceFee'] = ($providerData['serviceFee'] ?? 0.1) * 100;
    
    // Cumulated rewards from protocol - this is the eGLD distributed to delegators
    if (isset($providerData['cumulatedRewards'])) {
        $results['totalDistributed'] = round(floatval($providerData['cumulatedRewards']) / 1e18, 2);
    }
}

// 3. Get EGLD price
$egldData = apiCall($COINGECKO_API);
$egldPrice = $egldData['elrond-erd-2']['usd'] ?? 4.0;
$results['egldPrice'] = $egldPrice;

// 4. Calculate USD values
$results['totalStakedUsd'] = round($results['totalStaked'] * $egldPrice, 0);
$results['totalDistributedUsd'] = round($results['totalDistributed'] * $egldPrice, 0);

// 5. Format for website display
$results['formatted'] = [
    'validators' => number_format($results['validators']) . ' nodes',
    'staked' => formatK($results['totalStaked']) . ' eGLD',
    'stakedUsd' => '$' . number_format($results['totalStakedUsd'] / 1e6, 1) . 'M',
    'delegators' => number_format($results['delegators']) . '+',
    'distributed' => formatK($results['totalDistributed']) . ' eGLD',
    'distributedUsd' => '$' . number_format($results['totalDistributedUsd'] / 1e3, 0) . 'K'
];

function formatK($num) {
    if ($num >= 1000) {
        return round($num / 1000, 1) . 'K';
    }
    return round($num, 1);
}

echo json_encode($results, JSON_PRETTY_PRINT);
