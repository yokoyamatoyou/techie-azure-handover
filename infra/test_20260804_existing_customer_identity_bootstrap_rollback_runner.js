'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  ROLLBACK_METHOD,
  ROLLBACK_REASON,
  parseRollbackOptions,
  runRollback,
} = require('./20260804_existing_customer_identity_bootstrap_rollback_runner');
const {
  LINK_METHOD,
  sha256,
} = require('./20260804_existing_customer_identity_bootstrap_runner');

const DIRECTORY_ID = '33333333-3333-4333-8333-333333333333';
const ISSUER = 'https://issuer.example.test/v2.0';
const TENANT_ID = '11111111-1111-4111-8111-111111111111';
const ACCOUNT_ID = '22222222-2222-4222-8222-222222222222';
const OID = '44444444-4444-4444-8444-444444444444';
const STRIPE_ID = 'synthetic-payment-anchor-high-entropy';
const BATCH_ID = '55555555-5555-4555-8555-555555555555';
const OPERATION_ID = '66666666-6666-4666-8666-666666666666';
const PRINCIPAL_ID = '77777777-7777-4777-8777-777777777777';
const BINDING_ID = '88888888-8888-4888-8888-888888888888';
const OTHER_BINDING_ID = '99999999-9999-4999-8999-999999999999';
const CHANGE_APPROVAL_HASH = 'b'.repeat(64);
const EVIDENCE_HASH = 'a'.repeat(64);
const ROLLBACK_APPROVAL_HASH = 'c'.repeat(64);

function deepCopy(value) {
  return JSON.parse(JSON.stringify(value));
}

function manifestFixture() {
  return {
    schema_version: 'techie-existing-customer-identity-bootstrap-v1',
    batch_id: BATCH_ID,
    change_approval_receipt_sha256: CHANGE_APPROVAL_HASH,
    expected_operation_count: 1,
    entries: [
      {
        operation_id: OPERATION_ID,
        business_tenant_id: TENANT_ID,
        expected_customer_account_id_sha256: sha256(ACCOUNT_ID),
        expected_stripe_customer_id_sha256: sha256(STRIPE_ID),
        directory_tenant_id: DIRECTORY_ID,
        token_issuer: ISSUER,
        subject_type: 'oid',
        subject_value: OID,
        entra_object_id: OID,
        identity_provider: 'email',
        identity_evidence_receipt_sha256: EVIDENCE_HASH,
      },
    ],
  };
}

function bootstrapState({ principalCreated = true, otherActiveBinding = false } = {}) {
  const state = {
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
    principals: [{ principal_id: PRINCIPAL_ID, tenant_id: TENANT_ID, status: 'active' }],
    bindings: [{
      identity_binding_id: BINDING_ID,
      principal_id: PRINCIPAL_ID,
      directory_tenant_id: DIRECTORY_ID,
      token_issuer: ISSUER,
      subject_type: 'oid',
      subject_value: OID,
      identity_provider: 'email',
      status: 'active',
      link_method: LINK_METHOD,
      end_reason: null,
    }],
    linkIntents: [],
    audits: [{
      principal_id: PRINCIPAL_ID,
      identity_binding_id: BINDING_ID,
      action_type: LINK_METHOD,
      result_status: 'success',
      details: {
        batch_id: BATCH_ID,
        operation_id: OPERATION_ID,
        change_approval_receipt_sha256: CHANGE_APPROVAL_HASH,
        identity_evidence_receipt_sha256: EVIDENCE_HASH,
        identity_provider: 'email',
        principal_created: principalCreated,
      },
    }],
    driftOnSecondSummary: false,
  };
  if (otherActiveBinding) {
    state.bindings.push({
      identity_binding_id: OTHER_BINDING_ID,
      principal_id: PRINCIPAL_ID,
      directory_tenant_id: DIRECTORY_ID,
      token_issuer: ISSUER,
      subject_type: 'oid',
      subject_value: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      identity_provider: 'google',
      status: 'active',
      link_method: 'verified_dual_auth',
      end_reason: null,
    });
  }
  return state;
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
      if (this.state.driftOnSecondSummary && this.summaryCalls === 2) business.stripe_links += 1;
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
    if (statement.includes('techie-existing-bootstrap:lock-')) return { rows: [] };
    if (statement.includes('techie-existing-rollback:target')) {
      const binding = this.state.bindings.find((item) => (
        item.token_issuer === params[0]
        && item.subject_type === 'oid'
        && item.subject_value === params[1]
      ));
      if (!binding) return { rows: [] };
      const principal = this.state.principals.find((item) => item.principal_id === binding.principal_id);
      return {
        rows: this.state.audits
          .filter((item) => (
            item.identity_binding_id === binding.identity_binding_id
            && item.action_type === params[2]
            && item.result_status === 'success'
          ))
          .map((audit) => ({
            identity_binding_id: binding.identity_binding_id,
            principal_id: binding.principal_id,
            directory_tenant_id: binding.directory_tenant_id,
            identity_provider: binding.identity_provider,
            binding_status: binding.status,
            link_method: binding.link_method,
            end_reason: binding.end_reason,
            tenant_id: principal.tenant_id,
            principal_status: principal.status,
            bootstrap_audit_details: deepCopy(audit.details),
          })),
      };
    }
    if (statement.includes('techie-existing-rollback:audit')) {
      return {
        rows: this.state.audits
          .filter((item) => (
            item.identity_binding_id === params[0]
            && item.action_type === params[1]
            && item.result_status === 'success'
          ))
          .map((item) => ({ details: deepCopy(item.details) })),
      };
    }
    if (statement.includes('techie-existing-rollback:other-bindings')) {
      const count = this.state.bindings.filter((item) => (
        item.principal_id === params[0]
        && item.identity_binding_id !== params[1]
        && item.status === 'active'
      )).length;
      return { rows: [{ count }] };
    }
    if (statement.includes('techie-existing-rollback:link-intents')) {
      return {
        rows: this.state.linkIntents
          .filter((item) => (
            item.principal_id === params[0]
            || item.source_identity_binding_id === params[1]
            || item.completed_identity_binding_id === params[1]
          ))
          .map((item) => ({
            identity_link_intent_id: item.identity_link_intent_id,
            status: item.status,
          })),
      };
    }
    if (statement.includes('techie-existing-rollback:dispute-binding')) {
      const binding = this.state.bindings.find((item) => item.identity_binding_id === params[0]);
      if (!binding || binding.status !== 'active') return { rows: [], rowCount: 0 };
      binding.status = 'disputed';
      binding.end_reason = String(params[1]);
      return { rows: [], rowCount: 1 };
    }
    if (statement.includes('techie-existing-rollback:dispute-principal')) {
      const principal = this.state.principals.find((item) => item.principal_id === params[0]);
      if (!principal || principal.status !== 'active') return { rows: [], rowCount: 0 };
      principal.status = 'disputed';
      return { rows: [], rowCount: 1 };
    }
    if (statement.includes('techie-existing-rollback:insert-audit')) {
      this.state.audits.push({
        principal_id: String(params[0]),
        identity_binding_id: String(params[1]),
        action_type: String(params[2]),
        result_status: 'success',
        details: JSON.parse(String(params[3])),
      });
      return { rows: [], rowCount: 1 };
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

async function runWithState({
  state,
  manifest,
  apply = false,
  rollbackApprovalHash = ROLLBACK_APPROVAL_HASH,
  hashOverride,
  countOverride,
}) {
  const bytes = Buffer.from(JSON.stringify(manifest), 'utf8');
  const hash = hashOverride === undefined ? sha256(bytes) : hashOverride;
  const count = countOverride === undefined ? manifest.entries.length : countOverride;
  const argv = [
    'node',
    'rollback-runner',
    '--manifest',
    'protected-runtime.json',
    '--rollback-approval-sha256',
    rollbackApprovalHash,
  ];
  if (apply) {
    argv.push('--apply', '--confirm-manifest-sha256', hash, '--confirm-operation-count', String(count));
  }
  const captured = captureOutput();
  const result = await runRollback({
    ClientClass: clientClassFor(state),
    argv,
    env: runtimeEnv(),
    manifestBytes: bytes,
    output: captured.output,
  });
  return { result, output: captured.values.join('\n') };
}

async function main() {
  const valid = manifestFixture();
  assert.deepStrictEqual(
    parseRollbackOptions([
      'node', 'runner', '--manifest', 'x.json',
      '--rollback-approval-sha256', ROLLBACK_APPROVAL_HASH,
    ]),
    {
      manifestPath: 'x.json',
      rollbackApprovalHash: ROLLBACK_APPROVAL_HASH,
      apply: false,
      confirmedManifestHash: '',
      confirmedOperationCount: null,
    },
  );
  assert.throws(
    () => parseRollbackOptions(['node', 'runner', '--manifest', 'x.json']),
    /ROLLBACK_APPROVAL_REQUIRED/,
  );
  assert.throws(
    () => parseRollbackOptions([
      'node', 'runner', '--manifest', 'x.json',
      '--rollback-approval-sha256', ROLLBACK_APPROVAL_HASH, '--unknown',
    ]),
    /UNKNOWN_ARGUMENT/,
  );
  await assert.rejects(
    runWithState({
      state: bootstrapState(),
      manifest: valid,
      rollbackApprovalHash: CHANGE_APPROVAL_HASH,
    }),
    /ROLLBACK_APPROVAL_NOT_SEPARATE/,
  );

  const dryState = bootstrapState();
  const exactDryState = deepCopy(dryState);
  const dry = await runWithState({ state: dryState, manifest: valid });
  assert.strictEqual(dry.result.ok, true);
  assert.strictEqual(dry.result.committed, false);
  assert.deepStrictEqual(dryState, exactDryState);
  assert.match(dry.output, /EXISTING_CUSTOMER_BOOTSTRAP_ROLLBACK_DRY_RUN_PASS/);

  await assert.rejects(
    runWithState({ state: bootstrapState(), manifest: valid, apply: true, hashOverride: '0'.repeat(64) }),
    /APPLY_MANIFEST_HASH_CONFIRMATION_REQUIRED/,
  );
  await assert.rejects(
    runWithState({ state: bootstrapState(), manifest: valid, apply: true, countOverride: 2 }),
    /APPLY_OPERATION_COUNT_CONFIRMATION_MISMATCH/,
  );

  const applyState = bootstrapState();
  const applied = await runWithState({ state: applyState, manifest: valid, apply: true });
  assert.strictEqual(applied.result.ok, true);
  assert.strictEqual(applied.result.committed, true);
  assert.strictEqual(applyState.bindings[0].status, 'disputed');
  assert.strictEqual(applyState.bindings[0].end_reason, ROLLBACK_REASON);
  assert.strictEqual(applyState.principals[0].status, 'disputed');
  assert.strictEqual(applyState.audits.length, 2);
  assert.strictEqual(applyState.targets[TENANT_ID].stripe_customer_id, STRIPE_ID);
  const rollbackAudit = applyState.audits[1];
  assert.strictEqual(rollbackAudit.action_type, ROLLBACK_METHOD);
  assert.deepStrictEqual(Object.keys(rollbackAudit.details).sort(), [
    'batch_id',
    'operation_id',
    'original_change_approval_receipt_sha256',
    'original_identity_evidence_receipt_sha256',
    'principal_disputed',
    'rollback_approval_receipt_sha256',
  ]);

  const idempotent = await runWithState({ state: applyState, manifest: valid, apply: true });
  assert.strictEqual(idempotent.result.ok, true);
  assert.match(idempotent.output, /disputed=0 idempotent=1/);
  assert.strictEqual(applyState.audits.length, 2);

  const otherBindingState = bootstrapState({ otherActiveBinding: true });
  const otherBinding = await runWithState({ state: otherBindingState, manifest: valid, apply: true });
  assert.strictEqual(otherBinding.result.ok, true);
  assert.strictEqual(otherBindingState.bindings[0].status, 'disputed');
  assert.strictEqual(otherBindingState.bindings[1].status, 'active');
  assert.strictEqual(otherBindingState.principals[0].status, 'active');
  assert.strictEqual(otherBindingState.audits[1].details.principal_disputed, false);

  const preexistingPrincipalState = bootstrapState({ principalCreated: false });
  const preexistingPrincipal = await runWithState({ state: preexistingPrincipalState, manifest: valid, apply: true });
  assert.strictEqual(preexistingPrincipal.result.ok, true);
  assert.strictEqual(preexistingPrincipalState.bindings[0].status, 'disputed');
  assert.strictEqual(preexistingPrincipalState.principals[0].status, 'active');

  const approvalMismatchState = bootstrapState();
  approvalMismatchState.audits[0].details.change_approval_receipt_sha256 = 'd'.repeat(64);
  const approvalMismatch = await runWithState({ state: approvalMismatchState, manifest: valid });
  assert.strictEqual(approvalMismatch.result.ok, false);
  assert.match(approvalMismatch.output, /BOOTSTRAP_AUDIT_APPROVAL_MISMATCH/);
  assert.strictEqual(approvalMismatchState.bindings[0].status, 'active');

  const evidenceMismatchState = bootstrapState();
  evidenceMismatchState.audits[0].details.identity_evidence_receipt_sha256 = 'd'.repeat(64);
  const evidenceMismatch = await runWithState({ state: evidenceMismatchState, manifest: valid });
  assert.strictEqual(evidenceMismatch.result.ok, false);
  assert.match(evidenceMismatch.output, /BOOTSTRAP_AUDIT_EVIDENCE_MISMATCH/);
  assert.strictEqual(evidenceMismatchState.bindings[0].status, 'active');

  const malformedAuditState = bootstrapState();
  malformedAuditState.audits[0].details.unapproved_extra = true;
  const malformedAudit = await runWithState({ state: malformedAuditState, manifest: valid });
  assert.strictEqual(malformedAudit.result.ok, false);
  assert.match(malformedAudit.output, /BOOTSTRAP_AUDIT_DETAILS_SHAPE_INVALID/);
  assert.strictEqual(malformedAuditState.bindings[0].status, 'active');

  const pendingIntentState = bootstrapState();
  pendingIntentState.linkIntents.push({
    identity_link_intent_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    principal_id: PRINCIPAL_ID,
    source_identity_binding_id: BINDING_ID,
    completed_identity_binding_id: null,
    status: 'pending',
  });
  const pendingIntent = await runWithState({ state: pendingIntentState, manifest: valid });
  assert.strictEqual(pendingIntent.result.ok, false);
  assert.match(pendingIntent.output, /BOOTSTRAP_ROLLBACK_PENDING_LINK_INTENT/);
  assert.strictEqual(pendingIntentState.bindings[0].status, 'active');

  const badAccount = deepCopy(valid);
  badAccount.entries[0].expected_customer_account_id_sha256 = 'd'.repeat(64);
  const badAccountState = bootstrapState();
  const badAccountResult = await runWithState({ state: badAccountState, manifest: badAccount });
  assert.strictEqual(badAccountResult.result.ok, false);
  assert.match(badAccountResult.output, /TARGET_CUSTOMER_ACCOUNT_HASH_MISMATCH/);
  assert.strictEqual(badAccountState.bindings[0].status, 'active');

  const badStripe = deepCopy(valid);
  badStripe.entries[0].expected_stripe_customer_id_sha256 = 'd'.repeat(64);
  const badStripeState = bootstrapState();
  const badStripeResult = await runWithState({ state: badStripeState, manifest: badStripe });
  assert.strictEqual(badStripeResult.result.ok, false);
  assert.match(badStripeResult.output, /TARGET_STRIPE_CUSTOMER_HASH_MISMATCH/);
  assert.strictEqual(badStripeState.bindings[0].status, 'active');

  const driftState = bootstrapState();
  driftState.driftOnSecondSummary = true;
  const drift = await runWithState({ state: driftState, manifest: valid });
  assert.strictEqual(drift.result.ok, false);
  assert.match(drift.output, /ROLLBACK_BUSINESS_OR_STRIPE_INVARIANT_CHANGED/);
  assert.strictEqual(driftState.bindings[0].status, 'active');
  assert.strictEqual(driftState.principals[0].status, 'active');

  for (const value of [dry.output, applied.output, approvalMismatch.output, badStripeResult.output]) {
    assert.doesNotMatch(value, new RegExp(TENANT_ID, 'i'));
    assert.doesNotMatch(value, new RegExp(ACCOUNT_ID, 'i'));
    assert.doesNotMatch(value, new RegExp(STRIPE_ID, 'i'));
    assert.doesNotMatch(value, new RegExp(OID, 'i'));
  }

  const rollbackSource = fs.readFileSync(
    path.join(__dirname, '20260804_existing_customer_identity_bootstrap_rollback_runner.js'),
    'utf8',
  );
  assert.doesNotMatch(rollbackSource, /\bDELETE\b|\bTRUNCATE\b/i);
  assert.doesNotMatch(
    rollbackSource,
    /(?:UPDATE|INSERT\s+INTO)\s+(?:public\.)?(?:tenants|customer_account|subscription_contract|billing_event_ledger|payment_receipt_ledger|reseller_payout_ledger|reseller_payout_execution|refund_adjustment_ledger|service_usage_account|usage_event_ledger)\b/i,
  );
  assert.match(rollbackSource, /BEGIN ISOLATION LEVEL SERIALIZABLE/);
  assert.match(rollbackSource, /UPDATE external_identity_binding/);
  assert.match(rollbackSource, /UPDATE canonical_principal/);
  assert.match(rollbackSource, /INSERT INTO identity_link_audit_log/);

  console.log('existing-customer-identity-bootstrap-rollback-tests: 21 passed');
}

main().catch((error) => {
  console.error(`existing-customer-identity-bootstrap-rollback-tests: failed ${error.code || error.name}`);
  process.exitCode = 1;
});
