'use strict';

const assert = require('assert');
const { runProbe } = require('./20260804_identity_shadow_probe');

function makeState(overrides = {}) {
  return {
    tenants: 26,
    customer_accounts: 26,
    stripe_links: 26,
    duplicate_tenant_accounts: 0,
    duplicate_stripe_links: 0,
    identity_tables: 4,
    canonical_principals: 0,
    active_identity_bindings: 0,
    pending_link_intents: 0,
    identity_audit_rows: 0,
    duplicate_active_bindings: 0,
    orphan_identity_bindings: 0,
    orphan_canonical_principals: 0,
    ...overrides,
  };
}

class FakeClient {
  constructor(options) {
    this.options = options;
    this.state = { ...FakeClient.nextState };
    this.queries = [];
    FakeClient.instances.push(this);
  }

  async connect() {}

  async end() {}

  async query(sql) {
    const statement = String(sql).trim();
    this.queries.push(statement);
    if (statement.startsWith('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')) {
      return { rows: [] };
    }
    if (statement === 'ROLLBACK' || statement.startsWith('SET LOCAL ')) {
      return { rows: [] };
    }
    if (statement.includes("current_setting('transaction_read_only')")) {
      return { rows: [{ value: 'on' }] };
    }
    if (statement.includes('techie-shadow:summary')) {
      return { rows: [{ ...this.state }] };
    }
    if (statement.includes('techie-shadow:synthetic-binding')) {
      return { rows: [{ count: 0 }] };
    }
    if (statement.includes('techie-shadow:tenant-sample')) {
      return { rows: [{ tenant_id: '00000000-0000-0000-0000-000000000001' }] };
    }
    if (statement.includes('techie-shadow:legacy-candidate')) {
      return { rows: [{ count: 1 }] };
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

async function testReadOnlyEmptyProbePasses() {
  FakeClient.nextState = makeState();
  const capture = captureOutput();
  const result = await runProbe({
    ClientClass: FakeClient,
    argv: ['node', 'probe', '--expect-empty'],
    env: { DATABASE_URL: 'postgres://must-not-be-printed' },
    output: capture.output,
    randomUUID: () => '00000000-0000-0000-0000-000000000099',
  });
  const instance = FakeClient.instances.at(-1);
  assert.strictEqual(result.ok, true);
  assert.strictEqual(result.rolledBack, true);
  assert.strictEqual(instance.options.ssl.rejectUnauthorized, true);
  assert(instance.queries.some(query => query.includes('READ ONLY')));
  assert.match(capture.messages.join('\n'), /^SHADOW_PROBE_PASS /);
  assert.doesNotMatch(capture.messages.join('\n'), /must-not-be-printed/);
}

async function testNonEmptyHealthySchemaPassesWithoutEmptyGate() {
  FakeClient.nextState = makeState({
    canonical_principals: 1,
    active_identity_bindings: 3,
    identity_audit_rows: 3,
  });
  const result = await runProbe({
    ClientClass: FakeClient,
    argv: ['node', 'probe'],
    env: { DATABASE_URL: 'postgres://must-not-be-printed' },
    output: captureOutput().output,
    randomUUID: () => '00000000-0000-0000-0000-000000000098',
  });
  assert.strictEqual(result.ok, true);
}

async function testDuplicateBindingFailsAndRollsBack() {
  FakeClient.nextState = makeState({ duplicate_active_bindings: 1 });
  const capture = captureOutput();
  const result = await runProbe({
    ClientClass: FakeClient,
    argv: ['node', 'probe'],
    env: { DATABASE_URL: 'postgres://must-not-be-printed' },
    output: capture.output,
  });
  assert.deepStrictEqual(
    { ok: result.ok, rolledBack: result.rolledBack, errorCode: result.errorCode },
    { ok: false, rolledBack: true, errorCode: 'DUPLICATE_ACTIVE_BINDING' },
  );
  assert.match(capture.messages.join('\n'), /transaction_state=rolled_back/);
  assert.doesNotMatch(capture.messages.join('\n'), /must-not-be-printed/);
}

async function testUnknownArgumentFailsBeforeConnection() {
  const previousCount = FakeClient.instances.length;
  await assert.rejects(
    () => runProbe({
      ClientClass: FakeClient,
      argv: ['node', 'probe', '--apply'],
      env: { DATABASE_URL: 'postgres://must-not-be-printed' },
      output: captureOutput().output,
    }),
    error => error && error.code === 'UNKNOWN_ARGUMENT',
  );
  assert.strictEqual(FakeClient.instances.length, previousCount);
}

(async () => {
  await testReadOnlyEmptyProbePasses();
  await testNonEmptyHealthySchemaPassesWithoutEmptyGate();
  await testDuplicateBindingFailsAndRollsBack();
  await testUnknownArgumentFailsBeforeConnection();
  console.log('identity-shadow-probe-tests: 4 passed');
})().catch(error => {
  console.error(`identity-shadow-probe-tests: failed ${String(error && error.code || error && error.name || 'UNKNOWN')}`);
  process.exitCode = 1;
});
