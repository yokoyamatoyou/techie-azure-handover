'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  EXPECTED_BUSINESS_STATE_SHA256,
  EXPECTED_ROLLBACK_SQL_SHA256,
  IDENTITY_TABLES,
  businessStateSha256,
  databaseTargetSha256,
  parseOptions,
  runEmergencyRollback,
} = require('./20260804_identity_binding_hardening_emergency_rollback_runner');

const TEST_DATABASE_URL = 'postgresql://fixture-user:fixture-credential@db.example.test:5432/techie?sslmode=require';
const TARGET_HASH = databaseTargetSha256(TEST_DATABASE_URL);
const EMERGENCY_APPROVAL_HASH = 'C'.repeat(64);
const HARDENING_APPLY_RECEIPT_HASH = 'D'.repeat(64);

function makeState(overrides = {}) {
  return {
    tenants: 26,
    customer_accounts: 26,
    stripe_links: 26,
    duplicate_tenant_accounts: 0,
    duplicate_stripe_links: 0,
    identity_tables: 4,
    hardening_constraints: 2,
    validated_hardening_constraints: 2,
    unsafe_binding_defaults: 0,
    identityRows: Object.fromEntries(IDENTITY_TABLES.map(name => [name, 0])),
    ...overrides,
  };
}

function copyState(state) {
  return { ...state, identityRows: { ...state.identityRows } };
}

class FakeClient {
  constructor(options) {
    this.options = options;
    this.state = copyState(FakeClient.nextState);
    this.beforeTransaction = null;
    this.queries = [];
    FakeClient.instances.push(this);
  }

  async connect() {}

  async end() {}

  async query(sql) {
    const statement = String(sql).trim();
    this.queries.push(statement);
    if (statement.startsWith('BEGIN')) {
      this.beforeTransaction = copyState(this.state);
      return { rows: [] };
    }
    if (statement === 'ROLLBACK') {
      if (this.beforeTransaction) this.state = copyState(this.beforeTransaction);
      return { rows: [] };
    }
    if (statement === 'COMMIT') {
      this.beforeTransaction = null;
      if (FakeClient.postCommitBusinessDrift) this.state.tenants += 1;
      return { rows: [] };
    }
    if (statement.startsWith('SET LOCAL') || statement.includes('pg_advisory_xact_lock')) {
      return { rows: [] };
    }
    if (statement.includes('DROP CONSTRAINT chk_external_identity_binding_directory_tenant_id')) {
      this.state.hardening_constraints = 0;
      this.state.validated_hardening_constraints = 0;
      this.state.unsafe_binding_defaults = 2;
      return { rows: [] };
    }
    if (statement.includes('techie-identity-hardening-emergency:summary')) {
      const { identityRows: _, ...summary } = this.state;
      return { rows: [{ ...summary }] };
    }
    const countMatch = statement.match(/^SELECT count\(\*\)::int AS count FROM ([a-z_]+)$/);
    if (countMatch && IDENTITY_TABLES.includes(countMatch[1])) {
      return { rows: [{ count: this.state.identityRows[countMatch[1]] }] };
    }
    throw Object.assign(new Error('UNEXPECTED_QUERY'), { code: 'UNEXPECTED_QUERY' });
  }
}
FakeClient.instances = [];
FakeClient.nextState = makeState();
FakeClient.postCommitBusinessDrift = false;

function captureOutput() {
  const messages = [];
  return {
    messages,
    output: {
      log: value => messages.push(String(value)),
      error: value => messages.push(String(value)),
    },
  };
}

function dryRunArgv() {
  return ['node', 'runner', '--confirm-database-target-sha256', TARGET_HASH];
}

function applyArgv(overrides = {}) {
  return [
    ...dryRunArgv(),
    '--apply',
    '--confirm-sha256',
    overrides.sqlHash || EXPECTED_ROLLBACK_SQL_SHA256,
    '--confirm-emergency-approval-sha256',
    overrides.approvalHash || EMERGENCY_APPROVAL_HASH,
    '--confirm-hardening-apply-receipt-sha256',
    overrides.applyReceiptHash || HARDENING_APPLY_RECEIPT_HASH,
  ];
}

async function run({ state = makeState(), argv = dryRunArgv(), databaseUrl = TEST_DATABASE_URL } = {}) {
  FakeClient.nextState = state;
  const capture = captureOutput();
  const result = await runEmergencyRollback({
    ClientClass: FakeClient,
    argv,
    env: { DATABASE_URL: databaseUrl },
    output: capture.output,
  });
  return { result, capture, instance: FakeClient.instances.at(-1) };
}

async function main() {
  assert.deepStrictEqual(parseOptions(dryRunArgv()), {
    apply: false,
    confirmedTargetHash: TARGET_HASH,
    confirmedSqlHash: '',
    emergencyApprovalHash: '',
    hardeningApplyReceiptHash: '',
  });
  assert.throws(
    () => parseOptions([...dryRunArgv(), '--unknown']),
    /UNKNOWN_ARGUMENT/,
  );

  const dry = await run();
  assert.deepStrictEqual(dry.result, { ok: true, mode: 'dry-run', committed: false });
  assert.strictEqual(dry.instance.state.hardening_constraints, 2);
  assert.strictEqual(dry.instance.state.unsafe_binding_defaults, 0);
  assert.strictEqual(dry.instance.options.ssl.rejectUnauthorized, true);
  assert.match(dry.capture.messages.join('\n'), /HARDENING_EMERGENCY_ROLLBACK_DRY_RUN_PASS/);
  assert.doesNotMatch(dry.capture.messages.join('\n'), /fixture-user|fixture-credential|db\.example\.test|techie/);

  assert.throws(
    () => parseOptions([...dryRunArgv(), '--apply']),
    /EMERGENCY_ROLLBACK_SQL_HASH_CONFIRMATION_REQUIRED/,
  );
  assert.throws(
    () => parseOptions(applyArgv({ approvalHash: HARDENING_APPLY_RECEIPT_HASH })),
    /EMERGENCY_CONFIRMATION_HASH_REUSE_REJECTED/,
  );

  const applied = await run({ argv: applyArgv() });
  assert.deepStrictEqual(applied.result, { ok: true, mode: 'apply', committed: true });
  assert.strictEqual(applied.instance.state.hardening_constraints, 0);
  assert.strictEqual(applied.instance.state.validated_hardening_constraints, 0);
  assert.strictEqual(applied.instance.state.unsafe_binding_defaults, 2);
  assert.match(applied.capture.messages.join('\n'), /HARDENING_EMERGENCY_ROLLBACK_APPLY_PASS/);

  FakeClient.postCommitBusinessDrift = true;
  const postCommitFailure = await run({ argv: applyArgv() });
  FakeClient.postCommitBusinessDrift = false;
  assert.deepStrictEqual(postCommitFailure.result, { ok: false, mode: 'apply', committed: true });
  assert.match(postCommitFailure.capture.messages.join('\n'), /COMMIT_BUSINESS_STATE_DIGEST_MISMATCH/);
  assert.match(postCommitFailure.capture.messages.join('\n'), /commit_state=committed/);
  assert(!postCommitFailure.capture.messages.join('\n').includes('commit_state=not_committed'));

  const nonEmpty = makeState();
  nonEmpty.identityRows.external_identity_binding = 1;
  const nonEmptyRun = await run({ state: nonEmpty });
  assert.strictEqual(nonEmptyRun.result.ok, false);
  assert.match(nonEmptyRun.capture.messages.join('\n'), /PRECHECK_IDENTITY_SCHEMA_NOT_EMPTY/);
  assert(!nonEmptyRun.instance.queries.some(query => query.startsWith('BEGIN')));

  const driftRun = await run({ state: makeState({ tenants: 27 }) });
  assert.strictEqual(driftRun.result.ok, false);
  assert.match(driftRun.capture.messages.join('\n'), /PRECHECK_BUSINESS_STATE_DIGEST_MISMATCH/);
  assert(!driftRun.instance.queries.some(query => query.startsWith('BEGIN')));

  const instanceCount = FakeClient.instances.length;
  await assert.rejects(
    () => runEmergencyRollback({
      ClientClass: FakeClient,
      argv: ['node', 'runner', '--confirm-database-target-sha256', '0'.repeat(64)],
      env: { DATABASE_URL: TEST_DATABASE_URL },
      output: captureOutput().output,
    }),
    /DATABASE_TARGET_HASH_CONFIRMATION_MISMATCH/,
  );
  assert.strictEqual(FakeClient.instances.length, instanceCount);

  assert.strictEqual(businessStateSha256(makeState()), EXPECTED_BUSINESS_STATE_SHA256);
  const sql = fs.readFileSync(
    path.join(__dirname, '20260804_identity_binding_hardening_emergency_rollback.sql'),
    'utf8',
  );
  const executableSql = sql.replace(/--.*$/gm, '');
  assert.match(executableSql, /ALTER TABLE public\.external_identity_binding/);
  assert.doesNotMatch(executableSql, /\b(?:INSERT|UPDATE|DELETE|TRUNCATE|DROP TABLE)\b/i);
  assert.doesNotMatch(executableSql, /ALTER TABLE public\.(?:tenants|customer_account|subscription_contract)/i);

  console.log('identity-binding-hardening-emergency-rollback-tests: 11 passed');
}

main().catch(error => {
  console.error(`identity-binding-hardening-emergency-rollback-tests: failed ${error.code || error.name}`);
  process.exitCode = 1;
});
