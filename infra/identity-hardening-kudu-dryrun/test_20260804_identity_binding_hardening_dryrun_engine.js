'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  EXPECTED_BUSINESS_STATE_SHA256,
  IDENTITY_TABLES,
  businessStateSha256,
  databaseTargetSha256,
  runHardeningDryRun,
} = require('./20260804_identity_binding_hardening_dryrun_engine');

const TEST_DATABASE_URL = 'postgresql://fixture-user:fixture-credential@db.example.test:5432/techie?sslmode=require';
const TARGET_HASH = databaseTargetSha256(TEST_DATABASE_URL);
const SQL_BYTES = fs.readFileSync(
  path.join(__dirname, '..', '20260804_identity_binding_hardening.sql'),
);

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
  return { ...state, identityRows: { ...state.identityRows } };
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
    if (statement.startsWith('BEGIN')) {
      this.beforeTransaction = cloneState(this.state);
      return { rows: [] };
    }
    if (statement === 'ROLLBACK') {
      if (this.beforeTransaction) this.state = cloneState(this.beforeTransaction);
      return { rows: [] };
    }
    if (statement === 'COMMIT') {
      throw Object.assign(new Error('COMMIT_MUST_NOT_BE_REACHABLE'), { code: 'COMMIT_MUST_NOT_BE_REACHABLE' });
    }
    if (statement.startsWith('SET LOCAL ') || statement.includes('pg_advisory_xact_lock')) {
      return { rows: [] };
    }
    if (statement.includes('ADD CONSTRAINT chk_external_identity_binding_directory_tenant_id')) {
      this.state.hardening_constraints = FakeClient.invalidInsideState ? 1 : 2;
      this.state.validated_hardening_constraints = FakeClient.invalidInsideState ? 1 : 2;
      this.state.unsafe_binding_defaults = 0;
      return { rows: [] };
    }
    if (statement.includes('techie-identity-hardening-dryrun-only:summary')) {
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
FakeClient.invalidInsideState = false;

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

async function run({ state = makeState(), sqlBytes = SQL_BYTES, targetHash = TARGET_HASH } = {}) {
  FakeClient.nextState = state;
  const capture = captureOutput();
  const result = await runHardeningDryRun({
    ClientClass: FakeClient,
    confirmedTargetHash: targetHash,
    sqlBytes,
    env: { DATABASE_URL: TEST_DATABASE_URL },
    output: capture.output,
  });
  return { result, capture, instance: FakeClient.instances.at(-1) };
}

async function main() {
  FakeClient.invalidInsideState = false;
  const success = await run();
  assert.deepStrictEqual(success.result, { ok: true, mode: 'dry-run', committed: false });
  assert.strictEqual(success.instance.options.ssl.rejectUnauthorized, true);
  assert.strictEqual(success.instance.state.hardening_constraints, 0);
  assert.strictEqual(success.instance.state.unsafe_binding_defaults, 2);
  assert(success.instance.queries.includes('ROLLBACK'));
  assert(!success.instance.queries.includes('COMMIT'));
  assert.match(success.capture.messages.join('\n'), /^HARDENING_DRY_RUN_PASS /);
  assert.doesNotMatch(success.capture.messages.join('\n'), /fixture-user|fixture-credential|db\.example\.test|techie/);

  const nonEmptyState = makeState();
  nonEmptyState.identityRows.external_identity_binding = 1;
  const nonEmpty = await run({ state: nonEmptyState });
  assert.strictEqual(nonEmpty.result.ok, false);
  assert.match(nonEmpty.capture.messages.join('\n'), /PRECHECK_IDENTITY_SCHEMA_NOT_EMPTY/);
  assert(!nonEmpty.instance.queries.some(query => query.startsWith('BEGIN')));

  const drift = await run({ state: makeState({ tenants: 27 }) });
  assert.strictEqual(drift.result.ok, false);
  assert.match(drift.capture.messages.join('\n'), /PRECHECK_BUSINESS_STATE_DIGEST_MISMATCH/);
  assert(!drift.instance.queries.some(query => query.startsWith('BEGIN')));

  const beforeTargetMismatch = FakeClient.instances.length;
  await assert.rejects(
    () => run({ targetHash: '0'.repeat(64) }),
    /DATABASE_TARGET_HASH_CONFIRMATION_MISMATCH/,
  );
  assert.strictEqual(FakeClient.instances.length, beforeTargetMismatch);

  const beforeSqlMismatch = FakeClient.instances.length;
  await assert.rejects(
    () => run({ sqlBytes: Buffer.from('not-the-reviewed-migration') }),
    /HARDENING_SQL_HASH_MISMATCH/,
  );
  assert.strictEqual(FakeClient.instances.length, beforeSqlMismatch);

  FakeClient.invalidInsideState = true;
  const invalidInside = await run();
  FakeClient.invalidInsideState = false;
  assert.strictEqual(invalidInside.result.ok, false);
  assert.strictEqual(invalidInside.result.committed, false);
  assert(invalidInside.instance.queries.includes('ROLLBACK'));
  assert(!invalidInside.instance.queries.includes('COMMIT'));
  assert.strictEqual(invalidInside.instance.state.hardening_constraints, 0);
  assert.strictEqual(invalidInside.instance.state.unsafe_binding_defaults, 2);
  assert.match(invalidInside.capture.messages.join('\n'), /IN_TRANSACTION_HARDENING_CONSTRAINT_COUNT_MISMATCH/);

  assert.strictEqual(businessStateSha256(makeState()), EXPECTED_BUSINESS_STATE_SHA256);
  const source = fs.readFileSync(
    path.join(__dirname, '20260804_identity_binding_hardening_dryrun_engine.js'),
    'utf8',
  );
  assert.doesNotMatch(source, /client\.query\(['"]COMMIT|--apply|HARDENING_APPLY/);
  assert.match(source, /client\.query\(['"]ROLLBACK/);

  console.log('identity-binding-hardening-kudu-dryrun-engine-tests: 7 passed');
}

main().catch(error => {
  console.error(`identity-binding-hardening-kudu-dryrun-engine-tests: failed ${error.code || error.name}`);
  process.exitCode = 1;
});
