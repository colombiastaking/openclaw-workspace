// stats-updater.js - Fetch live Colombia Staking stats and update the page
// Supports: English, Spanish, French
(function() {
    const API_URL = '/stats-api.php';
    
    const LABEL_MAP = {
        // English
        'Validator Nodes': { field: 'validators', format: v => v.replace(' nodes', '') },
        'Active Delegators': { field: 'delegators', format: v => v.replace('+', '') },
        'eGLD Staked': { field: 'staked', format: v => v },
        'eGLD Rewards Paid': { field: 'distributed', format: v => v },
        // English About page (shorter labels)
        'Nodes': { field: 'validators', format: v => v.replace(' nodes', '') },
        // Spanish
        'Nodos Validadores': { field: 'validators', format: v => v.replace(' nodes', '') },
        'Delegadores Activos': { field: 'delegators', format: v => v.replace('+', '') },
        'eGLD Delegados': { field: 'staked', format: v => v },
        'eGLD en Recompensas': { field: 'distributed', format: v => v },
        // Spanish About page (shorter labels)
        'Nodos': { field: 'validators', format: v => v.replace(' nodes', '') },
        // French
        'Nœuds Validateurs': { field: 'validators', format: v => v.replace(' nodes', '') },
        'Délégataires Actifs': { field: 'delegators', format: v => v.replace('+', '') },
        'eGLD Délégués': { field: 'staked', format: v => v },
        'eGLD en Récompenses': { field: 'distributed', format: v => v },
        // French About page (shorter labels)
        'Nœuds': { field: 'validators', format: v => v.replace(' nodes', '') }
    };
    
    async function updateStats() {
        try {
            const resp = await fetch(API_URL);
            if (!resp.ok) throw new Error('API error');
            const data = await resp.json();
            
            if (!data.success) return;
            
            const statItems = document.querySelectorAll('.stat-item');
            
            statItems.forEach(item => {
                const label = item.querySelector('.stat-label');
                if (!label) return;
                const labelText = label.textContent;
                
                // Find matching label using startsWith (label may include USD in parentheses)
                const entry = Object.entries(LABEL_MAP).find(([key]) => labelText.startsWith(key));
                if (!entry) return;
                const [key, config] = entry;
                
                const valueEl = item.querySelector('.stat-value');
                if (!valueEl) return;
                
                const rawValue = data.formatted[config.field];
                valueEl.textContent = config.format(rawValue);
                
                // Update USD values in labels
                // Match patterns like: (~$0.8M), (~$91K), (~0,8M$), (~90K$), (~$1.2M €)
                const usdField = config.field + 'Usd';
                if (data.formatted[usdField]) {
                    const newUsd = data.formatted[usdField];
                    // Replace USD pattern regardless of format: ($ at start or end, comma decimals, € symbol)
                    label.textContent = labelText.replace(/\(~?[\$€]?[\d.,]+[MK]?[\$€]?\)/, '(' + newUsd + ')');
                }
            });
            
        } catch (err) {
            console.log('Stats API unavailable:', err.message);
        }
    }
    
    // Run on load
    updateStats();
    
    // Refresh every 24 hours
    setInterval(updateStats, 24 * 60 * 60 * 1000);
})();
