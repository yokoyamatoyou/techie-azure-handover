// TECHIE Hub runtime configuration.
// Keep real secrets out of this file. Public client IDs and Stripe price IDs are safe to expose.
window.TECHIE_CONFIG = {
  HUB_URL: 'https://app.techie.jp',
  API_BASE_URL: 'https://api.techie.jp',

  KOTOMAKE_URL: 'https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io',
  KOTOMIGAKI_URL: 'https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io',
  KOTOMEGANE_URL: 'https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io',

  // Microsoft Entra External ID / Azure AD B2C.
  ENTRA_AUTHORITY: 'https://kyotokogyotechie.ciamlogin.com/198ccc88-e870-405e-bb50-5aac609976db',
  ENTRA_CLIENT_ID: 'bbef0e62-048c-49b7-850b-e49c229482d1',
  ENTRA_REDIRECT_URI: 'https://app.techie.jp/auth/callback',
  ENTRA_POST_LOGOUT_REDIRECT_URI: 'https://app.techie.jp/signed-out',
  ENTRA_SCOPES: ['openid', 'profile', 'email'],

  // Stripe Price IDs.
  PLANS: [
    {
      key: 'entry',
      name: 'エントリー',
      priceLabel: '月額 9,000円（税抜）/ 9,900円（税込）',
      creditLabel: '月15クレジット',
      serviceCode: 'techie-entry',
      serviceName: 'TECHIE エントリー',
      stripePriceId: 'price_1TUeFVCW1iD1TojNuRHRB86E',
      description: 'コトメイク・コトミガキ・コトメガネの基本プラン'
    },
    {
      key: 'standard',
      name: 'スタンダード',
      priceLabel: '月額 18,000円（税抜）/ 19,800円（税込）',
      creditLabel: '30クレジット',
      serviceCode: 'techie-standard',
      serviceName: 'TECHIE スタンダード',
      stripePriceId: 'price_1TUeJ7CW1iD1TojNteVdjHLm',
      description: 'コトメイク、コトミガキ、コトメガネを標準的に利用するプランです。'
    },
    {
      key: 'pro',
      name: 'プロ',
      priceLabel: '月額 49,800円（税抜）/ 54,780円（税込）',
      creditLabel: '100クレジット',
      serviceCode: 'techie-pro',
      serviceName: 'TECHIE プロ',
      stripePriceId: 'price_1TUeKwCW1iD1TojNmAdBVyXr',
      description: '利用回数が多い企業向けの上位プランです。'
    },
    {
      key: 'addon_10_credits',
      name: '追加10クレジット',
      priceLabel: '買い切り 10,000円（税抜）/ 11,000円（税込）',
      creditLabel: '10クレジット',
      serviceCode: 'techie-credit-addon',
      serviceName: 'TECHIE 追加クレジット',
      stripePriceId: 'price_1TUeNLCW1iD1TojNYNuY8XUG',
      checkoutMode: 'payment',
      creditGrantAmount: 10,
      description: '追加購入したクレジットは翌月に繰り越されます。'
    },
    {
      key: 'addon_1_credit',
      name: '追加1クレジット',
      priceLabel: '買い切り 1,000円（税抜）/ 1,100円（税込）',
      creditLabel: '1クレジット',
      serviceCode: 'techie-credit-addon-1',
      serviceName: 'TECHIE 追加1クレジット',
      stripePriceId: 'price_1TqO5OCW1iD1TojNQotHGizo',
      checkoutMode: 'payment',
      creditGrantAmount: 1,
      description: '追加購入した1クレジットは翌月に繰り越されます。'
    }
  ],

  IS_LOCAL: false
};

