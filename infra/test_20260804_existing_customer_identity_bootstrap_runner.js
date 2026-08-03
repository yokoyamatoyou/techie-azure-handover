'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  parseOptions,
  resolveProtectedManifestPath,
  runBootstrap,
  sha256,
  validateManifest,
} = require('./20260804_existing_customer_identity_bootstrap_runner');

const DIRECTORY_ID = '33333333-3333-4333-8333-333333333333';
const ISSUER = 'https://issuer.example.test/v2.0';
const TENANT_ID = '11111111-1111-4111-8111-111111111111';
const ACCOUNT_ID = '22222222-2222-4222-8222-222222222222';
const OID = '44444444-4444-4444-8444-444444444444';
const STRIPE_ID = 'synthetic-payment-anchor-high-entropy';

function deepCopy(value) {
  return JSON.parse(JSON.stringify(value));
}

function manifestFixture(overrides = {}) {
  const base = {
    schema_version: 'techie-existing-customer-identity-bootstrap-v1',
    batch_id: '55555555-5555-4555-8555-555555555555',
    change_approval_receipt_sha256: 'b'.repeat(64),
    expected_operation_count: 1,
    entries: [
      {
        operation_id: '66666666-6666-4666-8666-666666666666',
        business_tenant_id: TENANT_ID,
        expected_customer_account_id_sha256: sha256(ACCOUNT_ID),
        expected_stripe_customer_id_sha256: sha256(STRIPE_ID),
        directory_tenant_id: DIRECTORY_ID,
        token_issuer: ISSUER,
        subject_type: 'oid',
        subject_value: OID,
        entra_object_id: OID,
        identity_provider: 'email',
        identity_evidence_receipt_sha256: 'a'.repeat(64),
      },
    ],
  };
  return { ...base, ...overrides };
}

function baseState() {
  return {
    business: {
      tenants: 26,
      customer_accounts: 26,
      stripe_links: 26,
      subscription_contracts: 7,
      billing_events: 8,
      payment_receipts: 5,
      reseller_payouts: 2,
      reseller_payout_executions: 2,
      refund_adjustments: 1,
      usage_accounts: 6,
      usage_events: 9,
      duplicate_tenant_accounts: 0,
      duplicate_stripe_links: 0,
    },
    targets: {
      [TENANT_ID]: {
        tenant_id: TENANT_ID,
        customer_account_id: ACCOUNT_ID,
        stripe_customer_id: STRIPE_ID,
      },
    },
    identity_tables: 4,
    hardening_constraints: 2,
    validated_hardening_constraints: 2,
    unsafe_binding_defaults: 0,
    principals: [],
    bindings: [],
    linkIntents: [],
    audits: [],
    driftOnSecondSummary: false,
  };
}

function restoreState(target, snapshot) {
  for (const key of Object.keys(target)) delete target[key];
  Object.assign(target, deepCopy(snapshot));
}

class FakeClient {
  constructor(config, state) {
    this.config = config;
    this.state = state;
    this.snapshot = null;
    this.summaryCalls = 0;
  }

  async connect() {}

  async end() {}

  async query(query, params = []) {
    const statement = String(query).replace(/\s+/g, ' ').trim();
    if (statement.startsWith('BEGIN')) {
      this.snapshot = deepCopy(this.state);
      return { rows: [] };
    }
    if (statement === 'COMMIT') {
      this.snapshot = null;
      return { rows: [] };
    }
    if (statement === 'ROLLBACK') {
      if (this.snapshot) restoreState(this.state, this.snapshot);
      this.snapshot = null;
      return { rows: [] };
    }
    if (statement.startsWith('SET LOCAL') || statement.includes('pg_advisory_xact_lock')) {
      return { rows: [] };
    }
    if (statement.includes('techie-existing-bootstrap:summary')) {
      this.summaryCalls += 1;
      const activeByTenant = new Map();
      for (const principal of this.state.principals.filter((item) => item.status === 'active')) {
        activeByTenant.set(principal.tenant_id, (activeByTenant.get(principal.tenant_id) || 0) + 1);
      }
      const business = { ...this.state.business };
      if (this.state.driftOnSecondSummary && this.summaryCalls === 2) {
        business.stripe_links += 1;
      }
      return {
        rows: [{
          ...business,
          identity_tables: this.state.identity_tables,
          canonical_principals: this.state.principals.length,
          active_principals: this.state.principals.filter((item) => item.status === 'active').length,
          disputed_principals: this.state.principals.filter((item) => item.status === 'disputed').length,
          identity_bindings: this.state.bindings.length,
          active_bindings: this.state.bindings.filter((item) => item.status === 'active').length,
          disputed_bindings: this.state.bindings.filter((item) => item.status === 'disputed').length,
          link_intents: this.state.linkIntents.length,
          identity_audits: this.state.audits.length,
          hardening_constraints: this.state.hardening_constraints,
          validated_hardening_constraints: this.state.validated_hardening_constraints,
          unsafe_binding_defaults: this.state.unsafe_binding_defaults,
          ambiguous_active_principal_tenants: [...activeByTenant.values()].filter((count) => count > 1).length,
          orphan_bindings: 0,
          orphan_principals: 0,
        }],
      };
    }
    if (statement.includes('techie-existing-bootstrap:target')) {
      const target = this.state.targets[String(params[0])];
      return { rows: target ? [deepCopy(target)] : [] };
    }
    if (statement.includes('techie-existing-bootstrap:lock-')) {
      return { rows: [] };
    }
    if (statement.includes('techie-existing-bootstrap:binding')) {
      const binding = this.state.bindings.find((item) => (
        item.token_issuer === params[0]
        && item.subject_type === 'oid'
        && item.subject_value === params[1]
      ));
      if (!binding) return { rows: [] };
      const principal = this.state.principals.find((item) => item.principal_id === binding.principal_id);
      return {
        rows: [{
          identity_binding_id: binding.identity_binding_id,
          principal_id: binding.principal_id,
          directory_tenant_id: binding.directory_tenant_id,
          identity_provider: binding.identity_provider,
          binding_status: binding.status,
          tenant_id: principal.tenant_id,
          principal_status: principal.status,
        }],
      };
    }
    if (statement.includes('techie-existing-bootstrap:principals')) {
      return {
        rows: this.state.principals
          .filter((item) => item.tenant_id === params[0])
          .map((item) => ({ principal_id: item.principal_id, status: item.status })),
      };
    }
    if (statement.includes('techie-existing-bootstrap:insert-principal')) {
      this.state.principals.push({
        principal_id: String(params[0]),
        tenant_id: String(params[1]),
        status: 'active',
      });
      return { rows: [] };
    }
    if (statement.includes('techie-existing-bootstrap:insert-binding')) {
      this.state.bindings.push({
        identity_binding_id: String(params[0]),
        principal_id: String(params[1]),
        directory_tenant_id: String(params[2]),
        token_issuer: String(params[3]),
        subject_type: 'oid',
        subject_value: String(params[4]),
        identity_provider: String(params[5]),
        link_method: String(params[6]),
        status: 'active',
      });
      return { rows: [] };
    }
    if (statement.includes('techie-existing-bootstrap:insert-audit')) {
      this.state.audits.push({
        principal_id: String(params[0]),
        identity_binding_id: String(params[1]),
        action_type: String(params[2]),
        details: JSON.parse(String(params[3])),
      });
      return { rows: [] };
    }
    if (statement.includes('techie-existing-bootstrap:verify')) {
      const binding = this.state.bindings.find((item) => (
        item.token_issuer === params[0]
        && item.subject_type === 'oid'
        && item.subject_value === params[1]
      ));
      if (!binding) return { rows: [] };
      const principal = this.state.principals.find((item) => item.principal_id === binding.principal_id);
      return {
        rows: [{
          tenant_id: principal.tenant_id,
          principal_status: principal.status,
          directory_tenant_id: binding.directory_tenant_id,
          identity_provider: binding.identity_provider,
          binding_status: binding.status,
        }],
      };
    }
    throw new Error(`UNEXPECTED_TEST_SQL_${statement.slice(0, 30)}`);
  }
}

function clientClassFor(state) {
  return class extends FakeClient {
    constructor(config) {
      super(config, state);
    }
  };
}

function runtimeEnv() {
  return {
    DATABASE_URL: 'postgres://not-logged.invalid/test',
    EXPECTED_EXTERNAL_DIRECTORY_ID: DIRECTORY_ID,
    EXPECTED_EXTERNAL_ISSUER: ISSUER,
  };
}

function captureOutput() {
  const values = [];
  return {
    values,
    output: {
      log: (value) => values.push(String(value)),
      error: (value) => values.push(String(value)),
    },
  };
}

function manifestBytes(manifest) {
  return Buffer.from(JSON.stringify(manifest), 'utf8');
}

async function runWithState({ state, manifest, apply = false, hashOverride, countOverride }) {
  const bytes = manifestBytes(manifest);
  const hash = hashOverride === undefined ? sha256(bytes) : hashOverride;
  const count = countOverride === undefined ? manifest.entries.length : countOverride;
  const argv = ['node', 'runner', '--manifest', 'protected-runtime.json'];
  if (apply) {
    argv.push('--apply', '--confirm-manifest-sha256', hash, '--confirm-operation-count', String(count));
  }
  const captured = captureOutput();
  const result = await runBootstrap({
    ClientClass: clientClassFor(state),
    argv,
    env: runtimeEnv(),
    manifestBytes: bytes,
    output: captured.output,
  });
  return { result, output: captured.values.join('\n') };
}

async function main() {
  assert.deepStrictEqual(
    parseOptions(['node', 'runner', '--manifest', 'x.json']),
    { manifestPath: 'x.json', apply: false, confirmedManifestHash: '', confirmedOperationCount: null },
  );
  assert.throws(
    () => parseOptions(['node', 'runner', '--manifest', 'x.json', '--unknown']),
    /UNKNOWN_ARGUMENT/,
  );
  const sourceRoot = path.resolve(__dirname, '..');
  const protectedOutside = path.resolve(sourceRoot, '..', 'operator-protected', 'manifest.json');
  const fakePathDependencies = {
    sourceRoot,
    realpathSync: (value) => path.resolve(value),
    statSync: () => ({ isFile: () => true, mode: 0o100600 }),
    platform: 'linux',
  };
  assert.strictEqual(
    resolveProtectedManifestPath(protectedOutside, fakePathDependencies),
    protectedOutside,
  );
  assert.throws(
    () => resolveProtectedManifestPath(
      path.join(sourceRoot, 'infra', 'protected-runtime.json'),
      fakePathDependencies,
    ),
    /PROTECTED_MANIFEST_INSIDE_SOURCE_TREE/,
  );
  assert.throws(
    () => resolveProtectedManifestPath(protectedOutside, {
      ...fakePathDependencies,
      statSync: () => ({ isFile: () => true, mode: 0o100644 }),
    }),
    /PROTECTED_MANIFEST_PERMISSIONS_NOT_PRIVATE/,
  );

  const valid = manifestFixture();
  assert.strictEqual(validateManifest(valid, runtimeEnv()).entries.length, 1);

  const withEmail = deepCopy(valid);
  withEmail.entries[0].email = 'forbidden@example.test';
  assert.throws(() => validateManifest(withEmail, runtimeEnv()), /MANIFEST_ENTRY_SHAPE_INVALID/);

  const wrongDirectory = deepCopy(valid);
  wrongDirectory.entries[0].directory_tenant_id = '77777777-7777-4777-8777-777777777777';
  assert.throws(() => validateManifest(wrongDirectory, runtimeEnv()), /MANIFEST_DIRECTORY_MISMATCH/);

  const wrongCoordinate = deepCopy(valid);
  wrongCoordinate.entries[0].entra_object_id = '77777777-7777-4777-8777-777777777777';
  assert.throws(() => validateManifest(wrongCoordinate, runtimeEnv()), /MANIFEST_OID_COORDINATE_MISMATCH/);

  const duplicateTenant = deepCopy(valid);
  duplicateTenant.expected_operation_count = 2;
  duplicateTenant.entries.push({
    ...deepCopy(duplicateTenant.entries[0]),
    operation_id: '77777777-7777-4777-8777-777777777777',
    subject_value: '88888888-8888-4888-8888-888888888888',
    entra_object_id: '88888888-8888-4888-8888-888888888888',
  });
  assert.throws(() => validateManifest(duplicateTenant, runtimeEnv()), /MANIFEST_DUPLICATE_BUSINESS_TENANT/);

  const dryState = baseState();
  const dry = await runWithState({ state: dryState, manifest: valid });
  assert.strictEqual(dry.result.ok, true);
  assert.strictEqual(dry.result.committed, false);
  assert.strictEqual(dryState.principals.length, 0);
  assert.strictEqual(dryState.bindings.length, 0);
  assert.match(dry.output, /EXISTING_CUSTOMER_BOOTSTRAP_DRY_RUN_PASS/);
  assert.doesNotMatch(dry.output, new RegExp(TENANT_ID, 'i'));
  assert.doesNotMatch(dry.output, new RegExp(STRIPE_ID, 'i'));

  await assert.rejects(
    runWithState({ state: baseState(), manifest: valid, apply: true, hashOverride: '0'.repeat(64) }),
    /APPLY_MANIFEST_HASH_CONFIRMATION_REQUIRED/,
  );
  await assert.rejects(
    runWithState({ state: baseState(), manifest: valid, apply: true, countOverride: 2 }),
    /APPLY_OPERATION_COUNT_CONFIRMATION_MISMATCH/,
  );

  const applyState = baseState();
  const applied = await runWithState({ state: applyState, manifest: valid, apply: true });
  assert.strictEqual(applied.result.ok, true);
  assert.strictEqual(applied.result.committed, true);
  assert.strictEqual(applyState.principals.length, 1);
  assert.strictEqual(applyState.bindings.length, 1);
  assert.strictEqual(applyState.audits.length, 1);
  assert.strictEqual(applyState.targets[TENANT_ID].stripe_customer_id, STRIPE_ID);
  assert.deepStrictEqual(Object.keys(applyState.audits[0].details).sort(), [
    'batch_id',
    'change_approval_receipt_sha256',
    'identity_evidence_receipt_sha256',
    'identity_provider',
    'operation_id',
    'principal_created',
  ]);

  const idempotent = await runWithState({ state: applyState, manifest: valid, apply: true });
  assert.strictEqual(idempotent.result.ok, true);
  assert.match(idempotent.output, /inserts=0 idempotent=1/);
  assert.strictEqual(applyState.principals.length, 1);
  assert.strictEqual(applyState.bindings.length, 1);
  assert.strictEqual(applyState.audits.length, 1);

  const badAccount = deepCopy(valid);
  badAccount.entries[0].expected_customer_account_id_sha256 = 'b'.repeat(64);
  const badAccountRun = await runWithState({ state: baseState(), manifest: badAccount });
  assert.strictEqual(badAccountRun.result.ok, false);
  assert.match(badAccountRun.output, /TARGET_CUSTOMER_ACCOUNT_HASH_MISMATCH/);
  assert.doesNotMatch(badAccountRun.output, new RegExp(ACCOUNT_ID, 'i'));

  const badStripe = deepCopy(valid);
  badStripe.entries[0].expected_stripe_customer_id_sha256 = 'c'.repeat(64);
  const badStripeRun = await runWithState({ state: baseState(), manifest: badStripe });
  assert.strictEqual(badStripeRun.result.ok, false);
  assert.match(badStripeRun.output, /TARGET_STRIPE_CUSTOMER_HASH_MISMATCH/);
  assert.doesNotMatch(badStripeRun.output, new RegExp(STRIPE_ID, 'i'));

  const mismatchState = baseState();
  mismatchState.principals.push({
    principal_id: '99999999-9999-4999-8999-999999999999',
    tenant_id: TENANT_ID,
    status: 'active',
  });
  mismatchState.bindings.push({
    identity_binding_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    principal_id: '99999999-9999-4999-8999-999999999999',
    directory_tenant_id: DIRECTORY_ID,
    token_issuer: ISSUER,
    subject_type: 'oid',
    subject_value: OID,
    identity_provider: 'google',
    status: 'active',
  });
  const mismatch = await runWithState({ state: mismatchState, manifest: valid });
  assert.strictEqual(mismatch.result.ok, false);
  assert.match(mismatch.output, /EXISTING_BINDING_PROVIDER_MISMATCH/);

  const noHardening = baseState();
  noHardening.hardening_constraints = 0;
  noHardening.validated_hardening_constraints = 0;
  noHardening.unsafe_binding_defaults = 2;
  const noHardeningRun = await runWithState({ state: noHardening, manifest: valid });
  assert.strictEqual(noHardeningRun.result.ok, false);
  assert.match(noHardeningRun.output, /IDENTITY_BINDING_HARDENING_REQUIRED/);

  const ambiguous = baseState();
  ambiguous.principals.push(
    { principal_id: '99999999-9999-4999-8999-999999999991', tenant_id: TENANT_ID, status: 'active' },
    { principal_id: '99999999-9999-4999-8999-999999999992', tenant_id: TENANT_ID, status: 'active' },
  );
  const ambiguousRun = await runWithState({ state: ambiguous, manifest: valid });
  assert.strictEqual(ambiguousRun.result.ok, false);
  assert.match(ambiguousRun.output, /AMBIGUOUS_ACTIVE_PRINCIPAL_PRECHECK/);

  const drift = baseState();
  drift.driftOnSecondSummary = true;
  const driftRun = await runWithState({ state: drift, manifest: valid });
  assert.strictEqual(driftRun.result.ok, false);
  assert.match(driftRun.output, /BUSINESS_OR_STRIPE_INVARIANT_CHANGED/);
  assert.strictEqual(drift.principals.length, 0);
  assert.strictEqual(drift.bindings.length, 0);

  const runnerSource = fs.readFileSync(path.join(__dirname, '20260804_existing_customer_identity_bootstrap_runner.js'), 'utf8');
  const schemaSource = fs.readFileSync(path.join(__dirname, 'existing_customer_identity_bootstrap_manifest.schema.json'), 'utf8');
  assert.doesNotMatch(schemaSource, /billing_email|email_address|email_fingerprint/i);
  assert.doesNotMatch(
    runnerSource,
    /(?:UPDATE|DELETE\s+FROM|INSERT\s+INTO|TRUNCATE)\s+(?:public\.)?(?:tenants|customer_account|subscription_contract|billing_event_ledger|payment_receipt_ledger|reseller_payout_ledger|refund_adjustment_ledger|usage_event_ledger)/i,
  );
  assert.match(runnerSource, /BEGIN ISOLATION LEVEL SERIALIZABLE/);
  assert.match(runnerSource, /FOR SHARE OF t, ca/);
  assert.match(runnerSource, /email_fingerprint, status, link_method/);
  assert.match(runnerSource, /\$6, NULL, 'active'/);

  console.log('existing-customer-identity-bootstrap-tests: 21 passed');
}

main().catch((error) => {
  console.error(`existing-customer-identity-bootstrap-tests: failed ${error.code || error.name}`);
  process.exitCode = 1;
});
