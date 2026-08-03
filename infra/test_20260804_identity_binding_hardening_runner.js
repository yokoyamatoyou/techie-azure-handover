'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  EXPECTED_SHA256,
  IDENTITY_TABLES,
  parseOptions,
  runHardening,
} = require('./20260804_identity_binding_hardening_runner');

function makeState(overrides = {}) {
  return {
    tenants: 26,
    customer_accounts: 26,
    stripe_links: 26,
    duplicate_tenant_accounts: 0,
    duplicate_stripe_links: 0,
    identity_tables: 4,
    hardening_constraints: 0,
    validated_hardening_constraints: 0,
    unsafe_binding_defaults: 2,
    identityRows: Object.fromEntries(IDENTITY_TABLES.map(name => [name, 0])),
    ...overrides,
  };
}

function cloneState(state) {
  return {
    ...state,
    identityRows: { ...state.identityRows },
  };
}

class FakeClient {
  constructor(options) {
    this.options = options;
    this.state = cloneState(FakeClient.nextState);
    this.beforeTransaction = null;
    this.queries = [];
    FakeClient.instances.push(this);
  }

  async connect() {}

  async end() {}

  async query(sql) {
    const statement = String(sql).trim();
    this.queries.push(statement);
    if (statement === 'BEGIN') {
      this.beforeTransaction = cloneState(this.state);
      return { rows: [] };
    }
    if (statement === 'ROLLBACK') {
      if (this.beforeTransaction) this.state = cloneState(this.beforeTransaction);
      return { rows: [] };
    }
    if (statement === 'COMMIT' || statement.startsWith('SET LOCAL ') || statement.includes('pg_advisory_xact_lock')) {
      return { rows: [] };
    }
    if (statement.includes('ADD CONSTRAINT chk_external_identity_binding_directory_tenant_id')) {
      this.state.hardening_constraints = 2;
      this.state.validated_hardening_constraints = 2;
      this.state.unsafe_binding_defaults = 0;
      return { rows: [] };
    }
    if (statement.includes('techie-identity-hardening:summary')) {
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

async function testDryRunRollsBackEveryHardeningChange() {
  FakeClient.nextState = makeState();
  const capture = captureOutput();
  const result = await runHardening({
    ClientClass: FakeClient,
    argv: ['node', 'runner'],
    env: { DATABASE_URL: 'test-database-url-must-not-be-printed' },
    output: capture.output,
  });
  const instance = FakeClient.instances.at(-1);
  assert.deepStrictEqual(result, { ok: true, mode: 'dry-run', committed: false });
  assert.strictEqual(instance.options.ssl.rejectUnauthorized, true);
  assert.strictEqual(instance.state.hardening_constraints, 0);
  assert.strictEqual(instance.state.unsafe_binding_defaults, 2);
  assert.match(capture.messages.join('\n'), /^HARDENING_DRY_RUN_PASS /);
  assert.doesNotMatch(capture.messages.join('\n'), /must-not-be-printed/);
}

async function testApplyRequiresExactHashAndCommits() {
  await assert.rejects(
    () => runHardening({
      ClientClass: FakeClient,
      argv: ['node', 'runner', '--apply'],
      env: { DATABASE_URL: 'test-database-url-must-not-be-printed' },
      output: captureOutput().output,
    }),
    error => error && error.code === 'APPLY_HASH_CONFIRMATION_REQUIRED',
  );

  FakeClient.nextState = makeState();
  const capture = captureOutput();
  const result = await runHardening({
    ClientClass: FakeClient,
    argv: ['node', 'runner', '--apply', '--confirm-sha256', EXPECTED_SHA256],
    env: { DATABASE_URL: 'test-database-url-must-not-be-printed' },
    output: capture.output,
  });
  const instance = FakeClient.instances.at(-1);
  assert.deepStrictEqual(result, { ok: true, mode: 'apply', committed: true });
  assert.strictEqual(instance.state.hardening_constraints, 2);
  assert.strictEqual(instance.state.validated_hardening_constraints, 2);
  assert.strictEqual(instance.state.unsafe_binding_defaults, 0);
  assert.match(capture.messages.join('\n'), /^HARDENING_APPLY_PASS /);
  assert.doesNotMatch(capture.messages.join('\n'), /must-not-be-printed/);
}

async function testNonEmptyIdentityStateFailsBeforeTransaction() {
  const state = makeState();
  state.identityRows.external_identity_binding = 1;
  FakeClient.nextState = state;
  const capture = captureOutput();
  const result = await runHardening({
    ClientClass: FakeClient,
    argv: ['node', 'runner'],
    env: { DATABASE_URL: 'test-database-url-must-not-be-printed' },
    output: capture.output,
  });
  const instance = FakeClient.instances.at(-1);
  assert.deepStrictEqual(result, { ok: false, mode: 'dry-run', committed: false });
  assert.match(capture.messages.join('\n'), /IDENTITY_SCHEMA_NOT_EMPTY/);
  assert(!instance.queries.includes('BEGIN'));
  assert.doesNotMatch(capture.messages.join('\n'), /must-not-be-printed/);
}

function testUnknownArgumentsFailBeforeConnection() {
  assert.throws(
    () => parseOptions(['node', 'runner', '--force']),
    error => error && error.code === 'UNKNOWN_ARGUMENT',
  );
}

function testMigrationTouchesOnlyBindingInvariants() {
  const sql = fs.readFileSync(
    path.join(__dirname, '20260804_identity_binding_hardening.sql'),
    'utf8',
  );
  assert.match(sql, /ALTER TABLE public\.external_identity_binding/);
  assert.match(sql, /chk_external_identity_binding_directory_tenant_id/);
  assert.match(sql, /chk_external_identity_binding_identity_provider/);
  assert.match(sql, /identity_provider IN \('email', 'google', 'microsoft'\)/);
  assert.match(sql, /ALTER COLUMN directory_tenant_id DROP DEFAULT/);
  assert.match(sql, /ALTER COLUMN identity_provider DROP DEFAULT/);
  const executableSql = sql.replace(/--.*$/gm, '');
  assert.doesNotMatch(executableSql, /\b(?:INSERT|UPDATE|DELETE|TRUNCATE|DROP TABLE)\b/i);
  assert.doesNotMatch(executableSql, /ALTER TABLE public\.(?:tenants|customer_account|subscription_contract)/i);
}

(async () => {
  await testDryRunRollsBackEveryHardeningChange();
  await testApplyRequiresExactHashAndCommits();
  await testNonEmptyIdentityStateFailsBeforeTransaction();
  testUnknownArgumentsFailBeforeConnection();
  testMigrationTouchesOnlyBindingInvariants();
  console.log('identity-binding-hardening-runner-tests: 5 passed');
})().catch(error => {
  console.error(`identity-binding-hardening-runner-tests: failed ${String(error && (error.code || error.name) || 'UNKNOWN')}`);
  process.exitCode = 1;
});
