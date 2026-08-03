'use strict';

/**
 * Read-only live probe for the TECHIE canonical identity schema.
 *
 * Usage in an isolated Kudu audit directory:
 *   node 20260804_identity_shadow_probe.js --expect-empty
 *
 * The probe never accepts an apply/write mode. DATABASE_URL is read from the
 * process environment and is never printed. All reported values are aggregate
 * counts or booleans; no identity, customer, Stripe, token, or secret value is
 * emitted.
 */
const crypto = require('crypto');

const IDENTITY_TABLES = [
  'canonical_principal',
  'external_identity_binding',
  'identity_link_intent',
  'identity_link_audit_log',
];

function assertCondition(condition, code) {
  if (!condition) {
    const error = new Error(code);
    error.code = code;
    throw error;
  }
}

function safeErrorCode(error) {
  const raw = String(error && (error.code || error.name) || 'UNKNOWN');
  return /^[A-Za-z0-9_-]{1,80}$/.test(raw) ? raw : 'UNKNOWN';
}

function summariesEqual(before, after) {
  const beforeKeys = Object.keys(before).sort();
  const afterKeys = Object.keys(after).sort();
  return beforeKeys.length === afterKeys.length
    && beforeKeys.every((key, index) => (
      key === afterKeys[index] && Number(before[key]) === Number(after[key])
    ));
}

async function summary(client) {
  const result = await client.query(`
    /* techie-shadow:summary */
    SELECT
      (SELECT count(*)::int FROM tenants) AS tenants,
      (SELECT count(*)::int FROM customer_account) AS customer_accounts,
      (
        SELECT count(*)::int
        FROM customer_account
        WHERE stripe_customer_id IS NOT NULL
          AND btrim(stripe_customer_id) <> ''
      ) AS stripe_links,
      (
        SELECT count(*)::int
        FROM (
          SELECT tenant_id
          FROM customer_account
          GROUP BY tenant_id
          HAVING count(*) > 1
        ) duplicate_tenant
      ) AS duplicate_tenant_accounts,
      (
        SELECT count(*)::int
        FROM (
          SELECT stripe_customer_id
          FROM customer_account
          WHERE stripe_customer_id IS NOT NULL
            AND btrim(stripe_customer_id) <> ''
          GROUP BY stripe_customer_id
          HAVING count(*) > 1
        ) duplicate_stripe
      ) AS duplicate_stripe_links,
      (
        SELECT count(*)::int
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = ANY($1::text[])
      ) AS identity_tables,
      (SELECT count(*)::int FROM canonical_principal) AS canonical_principals,
      (
        SELECT count(*)::int
        FROM external_identity_binding
        WHERE status = 'active'
      ) AS active_identity_bindings,
      (
        SELECT count(*)::int
        FROM identity_link_intent
        WHERE status = 'pending'
      ) AS pending_link_intents,
      (SELECT count(*)::int FROM identity_link_audit_log) AS identity_audit_rows,
      (
        SELECT count(*)::int
        FROM (
          SELECT token_issuer, subject_type, subject_value
          FROM external_identity_binding
          WHERE status = 'active'
          GROUP BY token_issuer, subject_type, subject_value
          HAVING count(*) > 1
        ) duplicate_binding
      ) AS duplicate_active_bindings,
      (
        SELECT count(*)::int
        FROM external_identity_binding eib
        LEFT JOIN canonical_principal cp ON cp.principal_id = eib.principal_id
        WHERE cp.principal_id IS NULL
      ) AS orphan_identity_bindings,
      (
        SELECT count(*)::int
        FROM canonical_principal cp
        LEFT JOIN tenants t ON t.tenant_id = cp.tenant_id
        WHERE t.tenant_id IS NULL
      ) AS orphan_canonical_principals
  `, [IDENTITY_TABLES]);
  return result.rows[0];
}

async function probeLookups(client, randomUUID = crypto.randomUUID) {
  const probeId = randomUUID();
  const synthetic = await client.query(`
    /* techie-shadow:synthetic-binding */
    SELECT count(*)::int AS count
    FROM external_identity_binding eib
    JOIN canonical_principal cp ON cp.principal_id = eib.principal_id
    WHERE eib.token_issuer = $1
      AND eib.subject_type = 'sub'
      AND eib.subject_value = $2
      AND eib.status = 'active'
      AND cp.status = 'active'
  `, [`https://probe.invalid/${probeId}`, probeId]);

  const tenant = await client.query(`
    /* techie-shadow:tenant-sample */
    SELECT tenant_id
    FROM tenants
    ORDER BY tenant_id
    LIMIT 1
  `);
  assertCondition(tenant.rows.length === 1, 'TENANT_SAMPLE_UNAVAILABLE');

  const legacyCandidate = await client.query(`
    /* techie-shadow:legacy-candidate */
    SELECT count(*)::int AS count
    FROM tenants
    WHERE tenant_id = $1::uuid
  `, [tenant.rows[0].tenant_id]);

  return {
    synthetic_binding_matches: Number(synthetic.rows[0].count),
    legacy_candidate_matches: Number(legacyCandidate.rows[0].count),
  };
}

async function runProbe({
  ClientClass,
  argv = process.argv,
  env = process.env,
  output = console,
  randomUUID = crypto.randomUUID,
} = {}) {
  assertCondition(typeof ClientClass === 'function', 'PG_CLIENT_NOT_CONFIGURED');
  const options = argv.slice(2);
  assertCondition(options.every(value => value === '--expect-empty'), 'UNKNOWN_ARGUMENT');
  const expectEmpty = options.includes('--expect-empty');
  assertCondition(Boolean(env.DATABASE_URL), 'DATABASE_URL_NOT_CONFIGURED');

  const client = new ClientClass({
    connectionString: env.DATABASE_URL,
    ssl: { rejectUnauthorized: true },
  });
  let connected = false;
  let inTransaction = false;
  let rolledBack = false;
  try {
    await client.connect();
    connected = true;
    const before = await summary(client);

    await client.query('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');
    inTransaction = true;
    await client.query("SET LOCAL search_path = public, pg_catalog");
    await client.query("SET LOCAL lock_timeout = '5s'");
    await client.query("SET LOCAL statement_timeout = '30s'");

    const readOnly = await client.query("SELECT current_setting('transaction_read_only') AS value");
    assertCondition(String(readOnly.rows[0].value).toLowerCase() === 'on', 'TRANSACTION_NOT_READ_ONLY');

    const inside = await summary(client);
    assertCondition(Number(inside.identity_tables) === 4, 'IDENTITY_SCHEMA_TABLE_COUNT_MISMATCH');
    assertCondition(Number(inside.duplicate_tenant_accounts) === 0, 'DUPLICATE_TENANT_ACCOUNT');
    assertCondition(Number(inside.duplicate_stripe_links) === 0, 'DUPLICATE_STRIPE_LINK');
    assertCondition(Number(inside.duplicate_active_bindings) === 0, 'DUPLICATE_ACTIVE_BINDING');
    assertCondition(Number(inside.orphan_identity_bindings) === 0, 'ORPHAN_IDENTITY_BINDING');
    assertCondition(Number(inside.orphan_canonical_principals) === 0, 'ORPHAN_CANONICAL_PRINCIPAL');

    if (expectEmpty) {
      assertCondition(Number(inside.canonical_principals) === 0, 'CANONICAL_PRINCIPAL_NOT_EMPTY');
      assertCondition(Number(inside.active_identity_bindings) === 0, 'IDENTITY_BINDING_NOT_EMPTY');
      assertCondition(Number(inside.pending_link_intents) === 0, 'PENDING_LINK_INTENT_NOT_EMPTY');
      assertCondition(Number(inside.identity_audit_rows) === 0, 'IDENTITY_AUDIT_NOT_EMPTY');
    }

    const lookups = await probeLookups(client, randomUUID);
    assertCondition(lookups.synthetic_binding_matches === 0, 'SYNTHETIC_BINDING_COLLISION');
    assertCondition(lookups.legacy_candidate_matches === 1, 'LEGACY_CANDIDATE_LOOKUP_FAILED');

    await client.query('ROLLBACK');
    inTransaction = false;
    rolledBack = true;

    const after = await summary(client);
    assertCondition(summariesEqual(before, after), 'POST_PROBE_STATE_CHANGED');

    const report = {
      transaction_read_only: true,
      ...inside,
      ...lookups,
    };
    output.log(`SHADOW_PROBE_PASS ${JSON.stringify(report)}`);
    return { ok: true, rolledBack: true, report };
  } catch (error) {
    if (connected && inTransaction) {
      try {
        await client.query('ROLLBACK');
        rolledBack = true;
      } catch (_) {
        // Do not replace the original safe error code.
      }
    }
    output.error(`SHADOW_PROBE_ERROR ${safeErrorCode(error)} transaction_state=${rolledBack ? 'rolled_back' : 'not_rolled_back'}`);
    return { ok: false, rolledBack, errorCode: safeErrorCode(error) };
  } finally {
    if (connected) {
      await client.end().catch(() => {});
    }
  }
}

async function cliMain() {
  const { Client } = require('pg');
  const result = await runProbe({ ClientClass: Client });
  if (!result.ok) process.exitCode = 1;
}

if (require.main === module) {
  cliMain().catch(error => {
    console.error(`SHADOW_PROBE_ERROR ${safeErrorCode(error)} transaction_state=not_started`);
    process.exitCode = 1;
  });
}

module.exports = {
  IDENTITY_TABLES,
  probeLookups,
  runProbe,
  safeErrorCode,
  summariesEqual,
};
