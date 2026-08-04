'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const policy = require('../techie-hub/auth-provider-policy.js');
const repositoryRoot = path.resolve(__dirname, '..');

assert.equal(policy.providerEnabled('email', {}), false);
assert.equal(policy.providerHint('email', {}), '');
assert.equal(policy.nativeEmailEnabled({ EMAIL_NATIVE_AUTH_ENABLED: true }), false);
assert.equal(policy.nativeEmailEnabled({
  EMAIL_NATIVE_AUTH_ENABLED: true,
  EMAIL_NATIVE_AUTH_LIVE_VERIFIED: true
}), true);
assert.equal(policy.providerEnabled('email', {
  EMAIL_NATIVE_AUTH_ENABLED: true,
  EMAIL_NATIVE_AUTH_LIVE_VERIFIED: true
}), true);
assert.equal(policy.delegatedEmailFallbackEnabled({ EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED: true }), true);
assert.equal(policy.providerEnabled('email', { EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED: true }), true);
assert.equal(policy.linkProviderEnabled('email', { EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED: true }), false);
assert.equal(policy.linkProviderEnabled('email', {
  EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED: true,
  IDENTITY_LINKING_ENABLED: true
}), true);
assert.equal(policy.linkProviderEnabled('email', {
  EMAIL_NATIVE_AUTH_ENABLED: true,
  EMAIL_NATIVE_AUTH_LIVE_VERIFIED: true,
  IDENTITY_LINKING_ENABLED: true
}), true);
assert.equal(policy.authRequest('email', 'login', {
  EMAIL_NATIVE_AUTH_ENABLED: true,
  EMAIL_NATIVE_AUTH_LIVE_VERIFIED: true
}), null);

assert.equal(policy.providerEnabled('google', {}), false);
assert.equal(policy.providerEnabled('google', { GOOGLE_AUTH_ENABLED: false }), false);
assert.equal(policy.providerHint('google', {}), '');
assert.equal(policy.providerEnabled('google', { GOOGLE_AUTH_ENABLED: true }), false);
assert.equal(policy.providerEnabled('google', {
  GOOGLE_AUTH_ENABLED: true,
  GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED: true
}), true);
assert.equal(policy.linkProviderEnabled('google', {
  GOOGLE_AUTH_ENABLED: true,
  GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED: true,
  IDENTITY_LINKING_ENABLED: true
}), true);
assert.equal(policy.providerHint('google', {
  GOOGLE_AUTH_ENABLED: true,
  GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED: true
}), 'google');

assert.equal(policy.providerEnabled('microsoft', {}), false);
const ignoredMicrosoftConfig = {
  MICROSOFT_AUTH_ENABLED: true,
  MICROSOFT_AUTH_ROUTE_KIND: 'entra_tenant_domain',
  MICROSOFT_AUTH_DOMAIN_HINT: 'Approved.Example'
};
assert.equal(policy.providerEnabled('microsoft', ignoredMicrosoftConfig), false);
assert.equal(policy.providerHint('microsoft', ignoredMicrosoftConfig), '');

assert.equal(policy.providerEnabled('unknown', ignoredMicrosoftConfig), false);
assert.equal(policy.providerHint('unknown', ignoredMicrosoftConfig), '');

assert.equal(policy.authRequest('email', 'login', {}), null);
assert.deepEqual(policy.authRequest('email', 'login', { EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED: true }), {
  prompt: 'select_account',
  extraQueryParameters: { ui_locales: 'ja' }
});
assert.deepEqual(policy.authRequest('email', 'signup', { EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED: true }), {
  prompt: 'create',
  extraQueryParameters: { ui_locales: 'ja' }
});
assert.equal(policy.authRequest('google', 'login', {}), null);
assert.equal(policy.authRequest('google', 'login', { GOOGLE_AUTH_ENABLED: true }), null);
assert.deepEqual(policy.authRequest('google', 'login', {
  GOOGLE_AUTH_ENABLED: true,
  GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED: true
}), {
  prompt: 'login',
  extraQueryParameters: { ui_locales: 'ja', domain_hint: 'google' }
});
assert.deepEqual(policy.authRequest('google', 'signup', {
  GOOGLE_AUTH_ENABLED: true,
  GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED: true
}), {
  prompt: 'create',
  extraQueryParameters: { ui_locales: 'ja', domain_hint: 'google' }
});
assert.equal(policy.authRequest('microsoft', 'link', ignoredMicrosoftConfig), null);
assert.equal(policy.authRequest('email', 'unsupported', { EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED: true }), null);

const hubHtml = fs.readFileSync(path.join(repositoryRoot, 'techie-hub', 'index.html'), 'utf8');
const inlineScripts = Array.from(hubHtml.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi))
  .map(match => match[1].trim())
  .filter(Boolean);
assert.equal(inlineScripts.length, 1);
for (const script of inlineScripts) new Function(script);
assert.match(hubHtml, /data-auth-purpose="link_source"|purpose === 'link_source'/);
assert.match(hubHtml, /purpose === 'link_target'/);
assert.match(hubHtml, /apiFetchWithToken\('\/api\/identity\/link-complete'/);
assert.match(hubHtml, /clearStoredAuthToken\(true\)/);
assert.match(hubHtml, /clearStoredAuthToken\(true\);\s*syncAccount\(\);/);
assert.doesNotMatch(hubHtml, /IDENTITY_LINK_SOURCE_TOKEN/);
const startLoginBody = hubHtml.slice(
  hubHtml.indexOf('async function startLogin('),
  hubHtml.indexOf('async function openCheckout(')
);
assert.ok(
  startLoginBody.indexOf("if (provider === 'email' && nativeEmailEnabled())") < startLoginBody.indexOf("if (!msalClient)"),
  'Native Email must not depend on the MSAL browser library being available'
);

const hubDockerfile = fs.readFileSync(path.join(repositoryRoot, 'techie-hub', 'Dockerfile'), 'utf8');
assert.match(hubDockerfile, /COPY auth-provider-policy\.js \/usr\/share\/nginx\/html\/auth-provider-policy\.js/);

const hubConfigTemplate = fs.readFileSync(path.join(repositoryRoot, 'techie-hub', 'config.template.js'), 'utf8');
for (const enabled of [false, true]) {
  const rendered = hubConfigTemplate
    .replaceAll('%%EMAIL_NATIVE_AUTH_ENABLED%%', String(enabled))
    .replaceAll('%%EMAIL_NATIVE_AUTH_LIVE_VERIFIED%%', String(enabled))
    .replaceAll('%%IDENTITY_LINKING_ENABLED%%', String(enabled));
  assert.doesNotMatch(rendered, /%%(?:EMAIL_NATIVE_AUTH|IDENTITY_LINKING)_/);
  new Function(rendered);
}

const publicHubConfig = fs.readFileSync(path.join(repositoryRoot, 'techie-hub', 'config.js'), 'utf8');
assert.match(publicHubConfig, /EMAIL_NATIVE_AUTH_ENABLED:\s*false/);
assert.match(publicHubConfig, /EMAIL_NATIVE_AUTH_LIVE_VERIFIED:\s*false/);
assert.match(publicHubConfig, /IDENTITY_LINKING_ENABLED:\s*false/);

const deployScript = fs.readFileSync(path.join(repositoryRoot, 'deploy-azure0429-refresh.ps1'), 'utf8');
assert.match(deployScript, /Identity linking requires -IdentityResolverMode enforce/);
assert.match(deployScript, /Identity linking requires -ConfirmIdentityBindingHardeningApplied/);
assert.match(deployScript, /Identity linking requires -ConfirmExistingCustomerBootstrapVerified/);
assert.match(deployScript, /requires a protected lowercase SHA-256 for the approved binding-hardening apply receipt/);
assert.match(deployScript, /requires a protected lowercase SHA-256 for the approved existing-customer bootstrap receipt/);
assert.match(deployScript, /receipt SHA-256 values must be independently derived/);
assert.match(deployScript, /initial rollout requires auto-provision and binding-claim trust to remain disabled/);
assert.match(deployScript, /'%%IDENTITY_LINKING_ENABLED%%' = \$IdentityLinkingEnabled\.ToString\(\)\.ToLowerInvariant\(\)/);
assert.match(deployScript, /IDENTITY_LINKING_ENABLED=\$\(if \(\$EnableIdentityLinking\) \{ '1' \} else \{ '0' \}\)/);

const mainBicep = fs.readFileSync(path.join(repositoryRoot, 'infra', 'main.bicep'), 'utf8');
assert.match(mainBicep, /param identityBindingHardeningVerified bool = false/);
assert.match(mainBicep, /@secure\(\)\s*param identityBindingHardeningReceiptSha256 string = ''/);
assert.match(mainBicep, /param existingCustomerBootstrapVerified bool = false/);
assert.match(mainBicep, /@secure\(\)\s*param existingCustomerBootstrapReceiptSha256 string = ''/);
assert.match(mainBicep, /param identityLinkingEnabled bool = false/);
assert.match(mainBicep, /effectiveIdentityResolverMode == 'enforce'/);
assert.match(mainBicep, /!effectiveIdentityAutoProvision/);
assert.match(mainBicep, /!effectiveTrustEntraBindingClaims/);
assert.match(mainBicep, /length\(identityBindingHardeningReceiptSha256\) == 64/);
assert.match(mainBicep, /length\(existingCustomerBootstrapReceiptSha256\) == 64/);
assert.match(mainBicep, /identityBindingHardeningReceiptSha256 != existingCustomerBootstrapReceiptSha256/);
assert.match(mainBicep, /IDENTITY_LINKING_ENABLED', value: effectiveIdentityLinking \? '1' : '0'/);

console.log('auth provider policy contract: PASS');
