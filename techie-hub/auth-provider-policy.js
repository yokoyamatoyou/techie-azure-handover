(function (factory) {
  const policy = factory();
  if (typeof window !== 'undefined') window.TECHIE_AUTH_PROVIDER_POLICY = policy;
  if (typeof module === 'object' && module.exports) module.exports = policy;
}(function () {
  function providerHint(provider, config = {}) {
    if (provider === 'google') {
      return config.GOOGLE_AUTH_ENABLED === true && config.GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED === true
        ? 'google'
        : '';
    }
    return '';
  }

  function providerEnabled(provider, config = {}) {
    if (provider === 'email') {
      return nativeEmailEnabled(config) || delegatedEmailFallbackEnabled(config);
    }
    if (provider === 'google') {
      return config.GOOGLE_AUTH_ENABLED === true && config.GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED === true;
    }
    // Microsoft-hosted email addresses use the ordinary Email OTP route.
    // Microsoft SSO is not a public TECHIE sign-in method.
    if (provider === 'microsoft') return false;
    return false;
  }

  function nativeEmailEnabled(config = {}) {
    return config.EMAIL_NATIVE_AUTH_ENABLED === true
      && config.EMAIL_NATIVE_AUTH_LIVE_VERIFIED === true;
  }

  function delegatedEmailFallbackEnabled(config = {}) {
    return config.EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED === true;
  }

  function authRequest(provider, intent = 'login', config = {}) {
    if (!providerEnabled(provider, config)) return null;
    if (!['login', 'signup', 'link'].includes(intent)) return null;
    if (provider === 'email' && nativeEmailEnabled(config)) return null;
    const hint = providerHint(provider, config);
    const extraQueryParameters = { ui_locales: 'ja' };
    if (hint) extraQueryParameters.domain_hint = hint;
    return {
      prompt: intent === 'signup' ? 'create' : hint ? 'login' : 'select_account',
      extraQueryParameters
    };
  }

  function linkProviderEnabled(provider, config = {}) {
    if (config.IDENTITY_LINKING_ENABLED !== true) return false;
    if (provider === 'email') return providerEnabled('email', config);
    return provider === 'google' && providerEnabled('google', config);
  }

  return Object.freeze({
    authRequest,
    delegatedEmailFallbackEnabled,
    linkProviderEnabled,
    nativeEmailEnabled,
    providerEnabled,
    providerHint
  });
}));
