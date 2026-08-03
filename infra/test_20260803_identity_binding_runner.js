'use strict';

const assert = require('assert');
const {
  EXPECTED_SHA256,
  IDENTITY_TABLES,
  runMigration,
} = require('./20260803_identity_binding_runner');

function makeState() {
  return {
    tenants: 26,
    customer_accounts: 26,
    stripe_links: 26,
    duplicate_tenant_accounts: 0,
    duplicate_stripe_links: 0,
    identity_tables: 0,
    identityRows: Object.fromEntries(IDENTITY_TABLES.map(name => [name, 0])),
  };
}

class FakeClient {
  constructor(options) {
    this.options = options;
    this.state = FakeClient.nextState;
    this.beforeTransactionIdentityTables = 0;
    FakeClient.instances.push(this);
  }

  async connect() {}

  async end() {}

  async query(sql) {
    const statement = String(sql).trim();
    if (statement === 'BEGIN') {
      this.beforeTransactionIdentityTables = this.state.identity_tables;
      return { rows: [] };
    }
    if (statement === 'ROLLBACK') {
      this.state.identity_tables = this.beforeTransactionIdentityTables;
      return { rows: [] };
    }
    if (statement === 'COMMIT' || statement.startsWith('SET LOCAL ') || statement.includes('pg_advisory_xact_lock')) {
      return { rows: [] };
    }
    if (statement.includes('CREATE TABLE IF NOT EXISTS public.canonical_principal')) {
      this.state.identity_tables = 4;
      return { rows: [] };
    }
    if (statement.includes('FROM information_schema.tables') && statement.includes('FROM tenants')) {
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

async function testDryRunRollsBack() {
  FakeClient.nextState = makeState();
  const capture = captureOutput();
  const result = await runMigration({
    ClientClass: FakeClient,
    argv: ['node', 'runner'],
    env: { DATABASE_URL: 'postgres://must-not-be-printed' },
    output: capture.output,
  });
  assert.deepStrictEqual(result, { ok: true, mode: 'dry-run', committed: false });
  assert.strictEqual(FakeClient.instances.at(-1).options.ssl.rejectUnauthorized, true);
  assert.strictEqual(FakeClient.nextState.identity_tables, 0);
  assert.match(capture.messages.join('\n'), /^DRY_RUN_PASS /);
  assert.doesNotMatch(capture.messages.join('\n'), /must-not-be-printed/);
}

async function testApplyRequiresHashAndCommits() {
  await assert.rejects(
    () => runMigration({
      ClientClass: FakeClient,
      argv: ['node', 'runner', '--apply'],
      env: { DATABASE_URL: 'postgres://must-not-be-printed' },
      output: captureOutput().output,
    }),
    error => error && error.code === 'APPLY_HASH_CONFIRMATION_REQUIRED',
  );

  FakeClient.nextState = makeState();
  const capture = captureOutput();
  const result = await runMigration({
    ClientClass: FakeClient,
    argv: ['node', 'runner', '--apply', '--confirm-sha256', EXPECTED_SHA256],
    env: { DATABASE_URL: 'postgres://must-not-be-printed' },
    output: capture.output,
  });
  assert.deepStrictEqual(result, { ok: true, mode: 'apply', committed: true });
  assert.strictEqual(FakeClient.nextState.identity_tables, 4);
  assert.match(capture.messages.join('\n'), /^APPLY_PASS /);
  assert.doesNotMatch(capture.messages.join('\n'), /must-not-be-printed/);
}

(async () => {
  await testDryRunRollsBack();
  await testApplyRequiresHashAndCommits();
  console.log('identity-migration-runner-tests: 3 passed');
})().catch(error => {
  console.error(`identity-migration-runner-tests: failed ${String(error && error.code || error && error.name || 'UNKNOWN')}`);
  process.exitCode = 1;
});
