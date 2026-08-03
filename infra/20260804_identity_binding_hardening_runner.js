'use strict';

/**
 * Guarded TECHIE identity-binding invariant hardening runner.
 *
 * Usage in an isolated, access-controlled operator directory:
 *   node 20260804_identity_binding_hardening_runner.js
 *   node 20260804_identity_binding_hardening_runner.js --apply \
 *     --confirm-sha256 4E4D677AF23BF6781262F185FCC5C99338C112455294984CCAF2B1E59C310E53
 *
 * DATABASE_URL is read from the process environment and is never printed.
 * The default mode always rolls the migration back. Apply mode is permitted
 * only while all identity tables remain empty and business/Stripe aggregates
 * remain unchanged.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const EXPECTED_SHA256 = '4E4D677AF23BF6781262F185FCC5C99338C112455294984CCAF2B1E59C310E53';
const MIGRATION_FILE = path.join(__dirname, '20260804_identity_binding_hardening.sql');
const IDENTITY_TABLES = [
  'canonical_principal',
  'external_identity_binding',
  'identity_link_intent',
  'identity_link_audit_log',
];
const HARDENING_CONSTRAINTS = [
  'chk_external_identity_binding_directory_tenant_id',
  'chk_external_identity_binding_identity_provider',
];
const HARDENED_COLUMNS = ['directory_tenant_id', 'identity_provider'];
const BUSINESS_KEYS = [
  'tenants',
  'customer_accounts',
  'stripe_links',
  'duplicate_tenant_accounts',
  'duplicate_stripe_links',
];

function assertCondition(condition, code) {
  if (!condition) {
    const error = new Error(code);
    error.code = code;
    throw error;
  }
}

function parseOptions(argv) {
  const options = argv.slice(2);
  let apply = false;
  let confirmedHash = '';
  for (let index = 0; index < options.length; index += 1) {
    const option = options[index];
    if (option === '--apply') {
      assertCondition(!apply, 'DUPLICATE_APPLY_OPTION');
      apply = true;
      continue;
    }
    if (option === '--confirm-sha256') {
      assertCondition(!confirmedHash, 'DUPLICATE_HASH_CONFIRMATION');
      assertCondition(index + 1 < options.length, 'HASH_CONFIRMATION_VALUE_REQUIRED');
      confirmedHash = String(options[index + 1]).trim().toUpperCase();
      index += 1;
      continue;
    }
    assertCondition(false, 'UNKNOWN_ARGUMENT');
  }
  assertCondition(apply || !confirmedHash, 'HASH_CONFIRMATION_WITHOUT_APPLY');
  return { apply, confirmedHash };
}

function safeErrorCode(error) {
  const raw = String(error && (error.code || error.name) || 'UNKNOWN');
  return /^[A-Za-z0-9_-]{1,80}$/.test(raw) ? raw : 'UNKNOWN';
}

function businessCountsEqual(before, after) {
  return BUSINESS_KEYS.every(key => Number(before[key]) === Number(after[key]));
}

async function summary(client) {
  const result = await client.query(`
    /* techie-identity-hardening:summary */
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
      (
        SELECT count(*)::int
        FROM pg_constraint
        WHERE conrelid = to_regclass('public.external_identity_binding')
          AND conname = ANY($2::text[])
      ) AS hardening_constraints,
      (
        SELECT count(*)::int
        FROM pg_constraint
        WHERE conrelid = to_regclass('public.external_identity_binding')
          AND conname = ANY($2::text[])
          AND convalidated
      ) AS validated_hardening_constraints,
      (
        SELECT count(*)::int
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'external_identity_binding'
          AND column_name = ANY($3::text[])
          AND column_default IS NOT NULL
      ) AS unsafe_binding_defaults
  `, [IDENTITY_TABLES, HARDENING_CONSTRAINTS, HARDENED_COLUMNS]);
  return result.rows[0];
}

async function identityRowCounts(client) {
  const result = {};
  for (const tableName of IDENTITY_TABLES) {
    // Table names come only from the constant allowlist above.
    const row = await client.query(`SELECT count(*)::int AS count FROM ${tableName}`);
    result[tableName] = Number(row.rows[0].count);
  }
  return result;
}

function allIdentityRowsEmpty(counts) {
  return IDENTITY_TABLES.every(tableName => Number(counts[tableName]) === 0);
}

function assertUnhardenedEmptyState(state, rows) {
  assertCondition(Number(state.identity_tables) === 4, 'IDENTITY_SCHEMA_TABLE_COUNT_MISMATCH');
  assertCondition(allIdentityRowsEmpty(rows), 'IDENTITY_SCHEMA_NOT_EMPTY');
  assertCondition(Number(state.hardening_constraints) === 0, 'IDENTITY_BINDING_HARDENING_ALREADY_PRESENT');
  assertCondition(Number(state.validated_hardening_constraints) === 0, 'IDENTITY_BINDING_HARDENING_STATE_INVALID');
  assertCondition(Number(state.unsafe_binding_defaults) === 2, 'IDENTITY_BINDING_DEFAULT_PRECHECK_FAILED');
}

function assertHardenedEmptyState(state, rows, prefix) {
  assertCondition(Number(state.identity_tables) === 4, `${prefix}_IDENTITY_SCHEMA_TABLE_COUNT_MISMATCH`);
  assertCondition(allIdentityRowsEmpty(rows), `${prefix}_IDENTITY_SCHEMA_NOT_EMPTY`);
  assertCondition(Number(state.hardening_constraints) === 2, `${prefix}_CONSTRAINT_COUNT_MISMATCH`);
  assertCondition(Number(state.validated_hardening_constraints) === 2, `${prefix}_CONSTRAINT_NOT_VALIDATED`);
  assertCondition(Number(state.unsafe_binding_defaults) === 0, `${prefix}_UNSAFE_DEFAULT_REMAINS`);
}

async function runHardening({
  ClientClass,
  argv = process.argv,
  env = process.env,
  output = console,
} = {}) {
  assertCondition(typeof ClientClass === 'function', 'PG_CLIENT_NOT_CONFIGURED');
  const { apply, confirmedHash } = parseOptions(argv);
  if (apply) {
    assertCondition(confirmedHash === EXPECTED_SHA256, 'APPLY_HASH_CONFIRMATION_REQUIRED');
  }

  const sql = fs.readFileSync(MIGRATION_FILE, 'utf8');
  const actualHash = crypto.createHash('sha256').update(sql).digest('hex').toUpperCase();
  assertCondition(actualHash === EXPECTED_SHA256, 'MIGRATION_HASH_MISMATCH');
  assertCondition(Boolean(env.DATABASE_URL), 'DATABASE_URL_NOT_CONFIGURED');

  const client = new ClientClass({
    connectionString: env.DATABASE_URL,
    ssl: { rejectUnauthorized: true },
  });
  let connected = false;
  let inTransaction = false;
  let committed = false;
  try {
    await client.connect();
    connected = true;
    const before = await summary(client);
    const beforeRows = Number(before.identity_tables) === 4
      ? await identityRowCounts(client)
      : {};
    assertUnhardenedEmptyState(before, beforeRows);
    assertCondition(Number(before.duplicate_tenant_accounts) === 0, 'DUPLICATE_TENANT_ACCOUNT_PRECHECK');
    assertCondition(Number(before.duplicate_stripe_links) === 0, 'DUPLICATE_STRIPE_LINK_PRECHECK');

    await client.query('BEGIN');
    inTransaction = true;
    await client.query("SET LOCAL search_path = public, pg_catalog");
    await client.query("SET LOCAL lock_timeout = '5s'");
    await client.query("SET LOCAL statement_timeout = '60s'");
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('techie-identity-hardening-20260804', 0))");
    await client.query(sql);

    const inside = await summary(client);
    const insideRows = await identityRowCounts(client);
    assertHardenedEmptyState(inside, insideRows, 'IN_TRANSACTION');
    assertCondition(businessCountsEqual(before, inside), 'BUSINESS_COUNTS_CHANGED_IN_TRANSACTION');

    if (!apply) {
      await client.query('ROLLBACK');
      inTransaction = false;
      const afterRollback = await summary(client);
      const rollbackRows = await identityRowCounts(client);
      assertUnhardenedEmptyState(afterRollback, rollbackRows);
      assertCondition(businessCountsEqual(before, afterRollback), 'ROLLBACK_BUSINESS_COUNTS_CHANGED');
      output.log(`HARDENING_DRY_RUN_PASS ${JSON.stringify(afterRollback)}`);
      return { ok: true, mode: 'dry-run', committed: false };
    }

    await client.query('COMMIT');
    inTransaction = false;
    committed = true;
    const afterCommit = await summary(client);
    const committedRows = await identityRowCounts(client);
    assertHardenedEmptyState(afterCommit, committedRows, 'COMMIT');
    assertCondition(businessCountsEqual(before, afterCommit), 'COMMIT_BUSINESS_COUNTS_CHANGED');
    output.log(`HARDENING_APPLY_PASS ${JSON.stringify(afterCommit)}`);
    return { ok: true, mode: 'apply', committed: true };
  } catch (error) {
    if (connected && inTransaction) {
      try {
        await client.query('ROLLBACK');
      } catch (_) {
        // Preserve the original safe error code.
      }
    }
    output.error(`HARDENING_${apply ? 'APPLY' : 'DRY_RUN'}_ERROR ${safeErrorCode(error)} commit_state=${committed ? 'committed' : 'not_committed'}`);
    return { ok: false, mode: apply ? 'apply' : 'dry-run', committed };
  } finally {
    if (connected) {
      await client.end().catch(() => {});
    }
  }
}

async function cliMain() {
  const { Client } = require('pg');
  const result = await runHardening({ ClientClass: Client });
  if (!result.ok) process.exitCode = 1;
}

if (require.main === module) {
  cliMain().catch(error => {
    console.error(`HARDENING_RUNNER_ERROR ${safeErrorCode(error)} commit_state=not_committed`);
    process.exitCode = 1;
  });
}

module.exports = {
  EXPECTED_SHA256,
  HARDENING_CONSTRAINTS,
  IDENTITY_TABLES,
  parseOptions,
  runHardening,
};
