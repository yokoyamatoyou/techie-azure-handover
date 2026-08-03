'use strict';

/**
 * Guarded TECHIE canonical-identity migration runner.
 *
 * Usage in the isolated Kudu audit directory:
 *   node 20260803_identity_binding_runner.js
 *   node 20260803_identity_binding_runner.js --apply \
 *     --confirm-sha256 29D71CBE7F53739858BD499D009CF9527782F3E67D21F745D8FB73DAF074DBCB
 *
 * DATABASE_URL is read from the process environment and is never printed.
 * The default mode always rolls the migration back.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const EXPECTED_SHA256 = '29D71CBE7F53739858BD499D009CF9527782F3E67D21F745D8FB73DAF074DBCB';
const MIGRATION_FILE = path.join(__dirname, '20260803_identity_binding.sql');
const IDENTITY_TABLES = [
  'canonical_principal',
  'external_identity_binding',
  'identity_link_intent',
  'identity_link_audit_log',
];
const BUSINESS_KEYS = [
  'tenants',
  'customer_accounts',
  'stripe_links',
  'duplicate_tenant_accounts',
  'duplicate_stripe_links',
];

function optionValue(name, argv) {
  const index = argv.indexOf(name);
  return index >= 0 && index + 1 < argv.length ? String(argv[index + 1]) : '';
}

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

function businessCountsEqual(before, after) {
  return BUSINESS_KEYS.every(key => Number(before[key]) === Number(after[key]));
}

async function summary(client) {
  const result = await client.query(`
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
      ) AS identity_tables
  `, [IDENTITY_TABLES]);
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

async function runMigration({
  ClientClass,
  argv = process.argv,
  env = process.env,
  output = console,
} = {}) {
  assertCondition(typeof ClientClass === 'function', 'PG_CLIENT_NOT_CONFIGURED');
  const apply = argv.includes('--apply');
  const confirmedHash = optionValue('--confirm-sha256', argv).trim().toUpperCase();
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
    assertCondition(Number(before.identity_tables) === 0, 'IDENTITY_SCHEMA_ALREADY_PRESENT');
    assertCondition(Number(before.duplicate_tenant_accounts) === 0, 'DUPLICATE_TENANT_ACCOUNT_PRECHECK');
    assertCondition(Number(before.duplicate_stripe_links) === 0, 'DUPLICATE_STRIPE_LINK_PRECHECK');

    await client.query('BEGIN');
    inTransaction = true;
    await client.query("SET LOCAL search_path = public, pg_catalog");
    await client.query("SET LOCAL lock_timeout = '5s'");
    await client.query("SET LOCAL statement_timeout = '60s'");
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('techie-identity-migration-20260803', 0))");
    await client.query(sql);

    const inside = await summary(client);
    const insideRows = await identityRowCounts(client);
    assertCondition(Number(inside.identity_tables) === 4, 'IDENTITY_SCHEMA_TABLE_COUNT_MISMATCH');
    assertCondition(allIdentityRowsEmpty(insideRows), 'IDENTITY_SCHEMA_NOT_EMPTY');
    assertCondition(businessCountsEqual(before, inside), 'BUSINESS_COUNTS_CHANGED_IN_TRANSACTION');

    if (!apply) {
      await client.query('ROLLBACK');
      inTransaction = false;
      const afterRollback = await summary(client);
      assertCondition(Number(afterRollback.identity_tables) === 0, 'ROLLBACK_SCHEMA_REMAINS');
      assertCondition(businessCountsEqual(before, afterRollback), 'ROLLBACK_BUSINESS_COUNTS_CHANGED');
      output.log(`DRY_RUN_PASS ${JSON.stringify(afterRollback)}`);
      return { ok: true, mode: 'dry-run', committed: false };
    }

    await client.query('COMMIT');
    inTransaction = false;
    committed = true;
    const afterCommit = await summary(client);
    const committedRows = await identityRowCounts(client);
    assertCondition(Number(afterCommit.identity_tables) === 4, 'COMMIT_SCHEMA_TABLE_COUNT_MISMATCH');
    assertCondition(allIdentityRowsEmpty(committedRows), 'COMMIT_SCHEMA_NOT_EMPTY');
    assertCondition(businessCountsEqual(before, afterCommit), 'COMMIT_BUSINESS_COUNTS_CHANGED');
    output.log(`APPLY_PASS ${JSON.stringify(afterCommit)}`);
    return { ok: true, mode: 'apply', committed: true };
  } catch (error) {
    if (connected && inTransaction) {
      try {
        await client.query('ROLLBACK');
      } catch (_) {
        // Do not replace the original safe error code.
      }
    }
    output.error(`${apply ? 'APPLY' : 'DRY_RUN'}_ERROR ${safeErrorCode(error)} commit_state=${committed ? 'committed' : 'not_committed'}`);
    return { ok: false, mode: apply ? 'apply' : 'dry-run', committed };
  } finally {
    if (connected) {
      await client.end().catch(() => {});
    }
  }
}

async function cliMain() {
  const { Client } = require('pg');
  const result = await runMigration({ ClientClass: Client });
  if (!result.ok) process.exitCode = 1;
}

if (require.main === module) {
  cliMain().catch(error => {
    console.error(`RUNNER_ERROR ${safeErrorCode(error)} commit_state=not_committed`);
    process.exitCode = 1;
  });
}

module.exports = {
  EXPECTED_SHA256,
  IDENTITY_TABLES,
  businessCountsEqual,
  runMigration,
};
