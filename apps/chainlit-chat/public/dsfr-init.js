/**
 * DSFR Initialization for Chainlit
 *
 * Loads the DSFR JavaScript module which provides:
 * - data-fr-scheme management (light/dark/system theme switching)
 * - Disclosure patterns (accordions, tabs, modals)
 * - Accessibility focus management
 * - Collapse/expand animations
 *
 * For a chat application, the most useful behaviors are:
 * - Theme scheme management (respects system preference)
 * - Accessibility focus ring patterns
 * - Future-proofing for DSFR HTML components (header, footer, navigation)
 */

// Set the DSFR scheme attribute on the HTML element.
// "system" follows the user's OS light/dark preference.
document.documentElement.setAttribute('data-fr-scheme', 'system');

// Dynamically load the DSFR module script.
// We use dynamic import to avoid issues with Chainlit's custom_js loading mechanism,
// which may not support ES module attributes directly.
(function () {
  var script = document.createElement('script');
  script.type = 'module';
  script.src = '/public/dsfr/dsfr.module.min.js';
  document.body.appendChild(script);

  // Also load the nomodule fallback for older browsers
  var nomodule = document.createElement('script');
  nomodule.setAttribute('nomodule', '');
  nomodule.src = '/public/dsfr/dsfr.nomodule.min.js';
  document.body.appendChild(nomodule);
})();
