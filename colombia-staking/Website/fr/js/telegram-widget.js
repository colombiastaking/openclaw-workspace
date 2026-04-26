/**
 * Social Media Widget - Telegram + X (Twitter)
 */

(function() {
    'use strict';
    
    // Detect current language
    function detectLanguage() {
        const host = window.location.hostname;
        if (host.includes('esp.')) return 'es';
        if (host.includes('fr.')) return 'fr';
        return 'en';
    }
    
    const lang = detectLanguage();
    
    // Configuration per language - correct Telegram links
    const config = {
        en: {
            channels: [
                { name: '📢 Announcements', url: 'https://t.me/ColombiaStakingAnn', desc: 'Official updates & news' },
                { name: '💬 English Chat', url: 'https://t.me/ColombiaStakingChat', desc: 'Community discussions' },
                { name: '🇪🇸 Spanish Chat', url: 'https://t.me/colombiastakingesp', desc: 'Comunidad en español' },
                { name: '🇫🇷 French Chat', url: 'https://t.me/colmbiastakingfr', desc: 'Communauté française' }
            ],
            buttonText: 'Telegram'
        },
        es: {
            channels: [
                { name: '📢 Anuncios', url: 'https://t.me/ColombiaStakingAnn', desc: 'Noticias y actualizaciones' },
                { name: '💬 Chat Inglés', url: 'https://t.me/ColombiaStakingChat', desc: 'English community' },
                { name: '🇪🇸 Chat Español', url: 'https://t.me/colombiastakingesp', desc: 'Comunidad en español' },
                { name: '🇫🇷 Chat Francés', url: 'https://t.me/colmbiastakingfr', desc: 'Communauté française' }
            ],
            buttonText: 'Telegram'
        },
        fr: {
            channels: [
                { name: '📢 Annonces', url: 'https://t.me/ColombiaStakingAnn', desc: 'Nouvelles et mises à jour' },
                { name: '💬 Chat Anglais', url: 'https://t.me/ColombiaStakingChat', desc: 'English community' },
                { name: '🇪🇸 Chat Espagnol', url: 'https://t.me/colombiastakingesp', desc: 'Comunidad en español' },
                { name: '🇫🇷 Chat Français', url: 'https://t.me/colmbiastakingfr', desc: 'Communauté française' }
            ],
            buttonText: 'Telegram'
        }
    };
    
    const c = config[lang];
    
    // Inject styles - social widget at bottom: 20px, node status will be pushed to 80px
    const styles = `
    <style id="cs-telegram-styles">
    .cs-social-widget {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999990;
        font-family: 'Poppins', sans-serif;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 10px;
    }
    
    .cs-social-buttons {
        display: flex;
        gap: 10px;
    }
    
    .cs-x-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        background: #000;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        text-decoration: none;
    }
    
    .cs-x-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.5);
    }
    
    .cs-x-btn img {
        width: 24px;
        height: 24px;
    }
    
    .cs-telegram-btn {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 14px 20px;
        background: linear-gradient(135deg, #0088cc 0%, #00a8e8 100%);
        border: none;
        border-radius: 50px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 136, 204, 0.4);
        transition: all 0.3s ease;
    }
    
    .cs-telegram-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 25px rgba(0, 136, 204, 0.6);
    }
    
    .cs-telegram-btn img {
        width: 24px;
        height: 24px;
    }
    
    .cs-telegram-btn span {
        color: white;
        font-weight: 600;
        font-size: 14px;
        white-space: nowrap;
    }
    
    .cs-telegram-popup {
        position: absolute;
        bottom: 70px;
        right: 0;
        background: #1a1a1a;
        border-radius: 16px;
        padding: 20px;
        min-width: 280px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(0, 136, 204, 0.3);
        opacity: 0;
        visibility: hidden;
        transform: translateY(10px);
        transition: all 0.3s ease;
    }
    
    .cs-telegram-popup.active {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }
    
    .cs-telegram-popup h4 {
        margin: 0 0 15px 0;
        color: #62dbb8;
        font-size: 16px;
        font-weight: 600;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(98, 219, 184, 0.2);
    }
    
    .cs-telegram-channel {
        display: block;
        padding: 12px 15px;
        background: #252525;
        border-radius: 10px;
        margin-bottom: 8px;
        color: white;
        text-decoration: none;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    
    .cs-telegram-channel:last-child {
        margin-bottom: 0;
    }
    
    .cs-telegram-channel:hover {
        background: #333;
        border-color: #0088cc;
        transform: translateX(-5px);
    }
    
    .cs-telegram-channel-name {
        display: block;
        font-weight: 600;
        margin-bottom: 2px;
        font-size: 14px;
    }
    
    .cs-telegram-channel-desc {
        font-size: 12px;
        color: #888;
    }
    
    /* Mobile adjustments */
    @media (max-width: 768px) {
        .cs-telegram-btn span {
            display: none;
        }
        
        .cs-telegram-btn {
            padding: 14px;
            border-radius: 50%;
        }
        
        .cs-telegram-popup {
            right: -10px;
            min-width: 250px;
        }
        
        .cs-x-btn {
            width: 50px;
            height: 50px;
        }
    }
    </style>
    `;
    
    // Build popup HTML
    function buildPopup() {
        const channels = c.channels.map(ch => 
            `<a href="${ch.url}" target="_blank" rel="noopener" class="cs-telegram-channel">
                <span class="cs-telegram-channel-name">${ch.name}</span>
                <span class="cs-telegram-channel-desc">${ch.desc}</span>
            </a>`
        ).join('');
        
        return `
        <div class="cs-social-widget" id="csSocialWidget">
            <div class="cs-telegram-popup" id="csTelegramPopup">
                <h4>📱 Join us on Telegram</h4>
                ${channels}
            </div>
            <div class="cs-social-buttons">
                <a href="https://x.com/ColombiaStaking" target="_blank" rel="noopener" class="cs-x-btn" title="X (Twitter)">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="24" height="24">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <button class="cs-telegram-btn" id="csTelegramBtn" aria-label="Telegram">
                    <img src="images/v/telegram-logo-120.png" alt="Telegram">
                    <span>${c.buttonText}</span>
                </button>
            </div>
        </div>
        `;
    }
    
    // Inject widget and styles
    document.addEventListener('DOMContentLoaded', function() {
        // Remove any existing styles
        const existingStyles = document.getElementById('cs-telegram-styles');
        if (existingStyles) existingStyles.remove();
        
        // Inject styles
        document.head.insertAdjacentHTML('beforeend', styles);
        
        // Inject widget before closing body tag
        document.body.insertAdjacentHTML('beforeend', buildPopup());
        
        // Toggle popup
        const btn = document.getElementById('csTelegramBtn');
        const popup = document.getElementById('csTelegramPopup');
        
        if (btn && popup) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                popup.classList.toggle('active');
            });
            
            // Close when clicking outside
            document.addEventListener('click', function(e) {
                if (!document.getElementById('csSocialWidget').contains(e.target)) {
                    popup.classList.remove('active');
                }
            });
        }
    });
    
})();