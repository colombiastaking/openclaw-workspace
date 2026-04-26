/**
 * Node Status Widget - Injects floating status link
 */
(function() {
  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    initWidget();
  }
  
  function initWidget() {
    // Don't add on the status page itself
    if (window.location.pathname.includes('node-status')) return;
    
    // Detect language from URL
    var lang = 'en';
    if (window.location.hostname.includes('esp.')) lang = 'es';
    if (window.location.hostname.includes('fr.')) lang = 'fr';
    
    // Get status page URL
    var statusUrl = 'node-status.html';
    if (lang === 'es') statusUrl = 'node-status.html';
    if (lang === 'fr') statusUrl = 'node-status.html';
    
    // Labels
    var labels = {
      en: 'Node Status',
      es: 'Estado Nodos',
      fr: 'État Nœuds'
    };
    
    // Create widget
    var widget = document.createElement('a');
    widget.href = statusUrl;
    widget.className = 'node-status-widget';
    widget.innerHTML = '<span class="status-dot"></span>' + labels[lang];
    widget.title = 'Real-time node monitoring';
    
    // Add to page
    document.body.appendChild(widget);
    
    // Try to fetch status and update dot color
    fetch('status.json')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var allSync = data.nodes.every(function(n) { return n.status === 'SYNC'; });
        if (!allSync) {
          widget.querySelector('.status-dot').style.background = '#ff9800';
        }
      })
      .catch(function() {});
  }
})();
