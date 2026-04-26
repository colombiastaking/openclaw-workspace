/**
 * Unified Header Injector for Colombia Staking Website
 * Responsive design with mobile hamburger menu - FIXED VERSION
 */

(function() {
    'use strict';
    
    // Detect current language based on domain or path
    function detectLanguage() {
        const host = window.location.hostname;
        if (host.includes('esp.')) return 'es';
        if (host.includes('fr.')) return 'fr';
        return 'en';
    }
    
    const lang = detectLanguage();
    
    // Configuration per language
    const config = {
        en: {
            logoAlt: 'Colombia Staking Logo',
            siteName: 'Colombia Staking',
            nav: [
                { text: 'Home', href: 'index.html' },
                { text: 'COLS Token', href: 'cols-token.html' },
                { text: 'MultiversX', href: 'multiversx.html' },
                { text: 'DApp', href: 'dapp.html' },
                { text: 'Nodes', href: 'node-status.html' },
                { text: 'About', href: 'quienes-somos.html' },
                { text: 'FAQ', href: 'preguntas-frecuentes.html' }
            ],
            currentNav: ['About', 'Nodes', 'COLS Token', 'DApp'],
            langLinks: [
                { href: 'https://esp.colombia-staking.com' + window.location.pathname, img: 'images/v/bandera_de_espana.svg', alt: 'ES', title: 'Español' },
                { href: 'https://fr.colombia-staking.com' + window.location.pathname, img: 'images/n/flag_of_france.svg-63.png', alt: 'FR', title: 'Français' }
            ],
            menuLabel: 'Menu'
        },
        es: {
            logoAlt: 'Logo Colombia Staking',
            siteName: 'Colombia Staking',
            nav: [
                { text: 'Inicio', href: 'index.html' },
                { text: 'Token COLS', href: 'cols-token.html' },
                { text: 'MultiversX', href: 'elrond.html' },
                { text: 'DApp', href: 'dapp.html' },
                { text: 'Nodos', href: 'node-status.html' },
                { text: 'Nosotros', href: 'quienes-somos.html' },
                { text: 'FAQ', href: 'preguntas-frecuentes.html' }
            ],
            currentNav: ['Nosotros', 'Nodos', 'Token COLS', 'DApp'],
            langLinks: [
                { href: 'https://colombia-staking.com' + window.location.pathname, img: 'images/v/1200px-flag_of_the_united_kingdom.svg-56.webp', alt: 'EN', title: 'English' },
                { href: 'https://fr.colombia-staking.com' + window.location.pathname, img: 'images/n/flag_of_france.svg-63.png', alt: 'FR', title: 'Français' }
            ],
            menuLabel: 'Menú'
        },
        fr: {
            logoAlt: 'Logo Colombia Staking',
            siteName: 'Colombia Staking',
            nav: [
                { text: 'Accueil', href: 'index.html' },
                { text: 'Jeton COLS', href: 'cols-token.html' },
                { text: 'MultiversX', href: 'elrond.html' },
                { text: 'DApp', href: 'dapp.html' },
                { text: 'Nœuds', href: 'node-status.html' },
                { text: 'À Propos', href: 'quienes-somos.html' },
                { text: 'FAQ', href: 'preguntas-frecuentes.html' }
            ],
            currentNav: ['À Propos', 'Nœuds', 'Jeton COLS', 'DApp'],
            langLinks: [
                { href: 'https://colombia-staking.com' + window.location.pathname, img: 'images/v/1200px-flag_of_the_united_kingdom.svg-56.webp', alt: 'EN', title: 'English' },
                { href: 'https://esp.colombia-staking.com' + window.location.pathname, img: 'images/v/bandera_de_espana.svg', alt: 'ES', title: 'Español' }
            ],
            menuLabel: 'Menu'
        }
    };
    
    const c = config[lang];
    
    // Build navigation HTML
    function buildNav() {
        return c.nav.map(item => {
            const isActive = c.currentNav.includes(item.text);
            const activeClass = isActive ? 'active' : '';
            return `<a href="${item.href}" class="cs-nav-link ${activeClass}">${item.text}</a>`;
        }).join('\n            ');
    }
    
    // Build language switcher HTML
    function buildLangSwitch() {
        return c.langLinks.map(l => 
            `<a href="${l.href}" title="${l.title}" class="cs-lang-btn"><img src="${l.img}" alt="${l.alt}" onerror="this.style.display='none'"></a>`
        ).join('\n            ');
    }
    
    // Inject styles - using !important to override existing site CSS
    const styles = `
    <style id="cs-header-styles">
    /* Colombia Staking Unified Header - Mobile First with !important overrides */
    
    .cs-header-wrapper {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999999 !important;
        background: rgba(0,0,0,0.98) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
    }
    
    .cs-header-top {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 10px 15px !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    .cs-logo-container {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        flex-shrink: 0 !important;
        z-index: 1000001 !important;
    }
    
    .cs-logo-img {
        width: 40px !important;
        height: 40px !important;
        border-radius: 50% !important;
        object-fit: cover !important;
        background: #1d1f23 !important;
        flex-shrink: 0 !important;
    }
    
    .cs-logo-text {
        font-family: 'Lustria', Georgia, serif !important;
        font-size: 16px !important;
        color: #62dbb8 !important;
        text-decoration: none !important;
        white-space: nowrap !important;
    }
    
    /* Hamburger button */
    .cs-hamburger {
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-around !important;
        width: 30px !important;
        height: 24px !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
        padding: 0 !important;
        z-index: 1000002 !important;
        flex-shrink: 0 !important;
    }
    
    .cs-hamburger span {
        width: 100% !important;
        height: 3px !important;
        background: #62dbb8 !important;
        border-radius: 2px !important;
        transition: all 0.3s ease !important;
        transform-origin: center !important;
        display: block !important;
    }
    
    .cs-hamburger.active span:nth-child(1) {
        transform: rotate(45deg) translate(5px, 6px) !important;
    }
    
    .cs-hamburger.active span:nth-child(2) {
        opacity: 0 !important;
        transform: scaleX(0) !important;
    }
    
    .cs-hamburger.active span:nth-child(3) {
        transform: rotate(-45deg) translate(6px, -6px) !important;
    }
    
    /* Mobile menu overlay */
    .cs-mobile-menu {
        position: fixed !important;
        top: 70px !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        width: 100vw !important;
        height: calc(100vh - 70px) !important;
        background: rgba(0,0,0,0.98) !important;
        z-index: 999998 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding: 15px 20px !important;
        padding-top: 20px !important;
        padding-bottom: 100px !important;
        overflow-y: auto !important;
        box-sizing: border-box !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        transition: all 0.3s ease !important;
    }
    
    .cs-mobile-menu.active {
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }
    
    .cs-nav-link {
        display: block !important;
        width: 100% !important;
        max-width: 280px !important;
        padding: 12px 20px !important;
        margin: 4px 0 !important;
        background: #1d1f23 !important;
        border: 1px solid rgba(98,219,184,0.3) !important;
        border-radius: 10px !important;
        color: #62dbb8 !important;
        text-decoration: none !important;
        font-family: 'Lustria', Georgia, serif !important;
        font-size: 16px !important;
        text-align: center !important;
        transition: all 0.2s ease !important;
        box-sizing: border-box !important;
    }
    
    .cs-nav-link:hover,
    .cs-nav-link.active {
        background: rgba(98,219,184,0.2) !important;
        border-color: #62dbb8 !important;
        transform: scale(1.02) !important;
    }
    
    .cs-lang-switch {
        display: flex !important;
        gap: 15px !important;
        margin-top: 15px !important;
        padding-top: 15px !important;
        border-top: 1px solid rgba(98,219,184,0.2) !important;
        flex-shrink: 0 !important;
    }
    
    .cs-lang-btn {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 10px 16px !important;
        background: #1d1f23 !important;
        border-radius: 8px !important;
        border: 1px solid rgba(98,219,184,0.2) !important;
        transition: all 0.2s ease !important;
    }
    
    .cs-lang-btn:hover {
        background: rgba(98,219,184,0.2) !important;
        border-color: #62dbb8 !important;
    }
    
    .cs-lang-switch img {
        width: 40px !important;
        height: 26px !important;
        object-fit: cover !important;
        border-radius: 4px !important;
        display: block !important;
    }
    
    /* Desktop styles */
    @media (min-width: 901px) {
        .cs-header-wrapper {
            position: sticky !important;
        }
        
        .cs-header-top {
            padding: 12px 25px !important;
        }
        
        .cs-logo-img {
            width: 50px !important;
            height: 50px !important;
        }
        
        .cs-logo-text {
            font-size: 22px !important;
        }
        
        .cs-hamburger {
            display: none !important;
        }
        
        .cs-mobile-menu {
            position: static !important;
            width: auto !important;
            height: auto !important;
            flex-direction: row !important;
            flex: 1 !important;
            justify-content: center !important;
            padding: 0 !important;
            background: transparent !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            gap: 5px !important;
            overflow: visible !important;
        }
        
        .cs-nav-link {
            width: auto !important;
            max-width: none !important;
            padding: 8px 16px !important;
            margin: 0 !important;
            font-size: 14px !important;
            border-radius: 20px !important;
            white-space: nowrap !important;
        }
        
        .cs-nav-link:hover {
            transform: translateY(-2px) scale(1) !important;
            box-shadow: 0 4px 12px rgba(98,219,184,0.2) !important;
        }
        
        .cs-lang-switch {
            margin-top: 0 !important;
            margin-left: 15px !important;
            padding-top: 0 !important;
            border-top: none !important;
        }
        
        .cs-lang-btn {
            padding: 5px !important;
            background: transparent !important;
            border: none !important;
        }
        
        .cs-lang-btn:hover {
            background: transparent !important;
            transform: scale(1.1) !important;
        }
        
        .cs-lang-switch img {
            width: 28px !important;
            height: 18px !important;
        }
    }
    
    /* Add body padding to prevent content from hiding behind fixed header */
    body.cs-menu-open {
        overflow: hidden !important;
    }
    
    /* Push page content down on mobile */
    body {
        padding-top: 70px !important;
    }
    
    @media (min-width: 901px) {
        body {
            padding-top: 74px !important;
        }
    }
    </style>
    `;
    
    // Build header HTML
    const logoPath = 'images/colombia-staking-logo.svg';
    
    const headerHTML = `
    <div class="cs-header-wrapper">
        <div class="cs-header-top">
            <div class="cs-logo-container">
                <a href="index.html">
                    <img src="${logoPath}" alt="${c.logoAlt}" class="cs-logo-img">
                </a>
                <a href="index.html" class="cs-logo-text">${c.siteName}</a>
            </div>
            
            <button class="cs-hamburger" aria-label="${c.menuLabel}" id="csMenuToggle">
                <span></span>
                <span></span>
                <span></span>
            </button>
            
            <nav class="cs-mobile-menu" id="csMobileMenu">
                ${buildNav()}
                <div class="cs-lang-switch">
                    ${buildLangSwitch()}
                </div>
            </nav>
        </div>
    </div>
    `;
    
    // Inject header and styles
    document.addEventListener('DOMContentLoaded', function() {
        // Remove any existing header styles
        const existingStyles = document.getElementById('cs-header-styles');
        if (existingStyles) existingStyles.remove();
        
        // Inject styles
        document.head.insertAdjacentHTML('beforeend', styles);
        
        // Inject header immediately after opening body tag
        document.body.insertAdjacentHTML('afterbegin', headerHTML);
        
        // Mobile menu toggle
        const menuToggle = document.getElementById('csMenuToggle');
        const mobileMenu = document.getElementById('csMobileMenu');
        
        if (menuToggle && mobileMenu) {
            menuToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                menuToggle.classList.toggle('active');
                mobileMenu.classList.toggle('active');
                document.body.classList.toggle('cs-menu-open');
            });
            
            // Close menu when clicking a link
            mobileMenu.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', function() {
                    menuToggle.classList.remove('active');
                    mobileMenu.classList.remove('active');
                    document.body.classList.remove('cs-menu-open');
                });
            });
            
            // Close menu on escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
                    menuToggle.classList.remove('active');
                    mobileMenu.classList.remove('active');
                    document.body.classList.remove('cs-menu-open');
                }
            });
        }
    });
    
})();