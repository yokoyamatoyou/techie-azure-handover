// TECHIE HUB - Service configuration
// For Azure deployment: real FQDNs baked at build time.
// For local dev with docker-compose: override this file or use localhost fallback.
window.TECHIE_CONFIG = {
  KOTOMAKE_URL:  'https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io',
  KOTOMIGAKI_URL: 'https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io',
  KOTOMEGANE_URL: 'https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io',

  // Microsoft Entra External ID / Azure AD B2C compatibility
  B2C_AUTHORITY: '%%B2C_AUTHORITY%%',
  B2C_CLIENT_ID: '%%B2C_CLIENT_ID%%',
  B2C_REDIRECT_URI: '%%B2C_REDIRECT_URI%%',
  B2C_SCOPES: ['openid', 'profile', 'email'],

  IS_LOCAL: false,
};
