'use strict';

/**
 * Guarded emergency reversal for the identity-binding DB hardening.
 *
 * Default: execute the reversal in a transaction, verify it, then roll back
 * and prove the hardened state was restored. Persistent emergency reversal
 * requires a separate approval receipt and the exact hardening-apply receipt.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const EXPECTED_ROLLBACK_SQL_SHA256 = '40C6774F8DD9251999F09A571C46297E8AFB8DD7118D6008266099CB1B58F19E';
const EXPECTED_BUSINESS_STATE_SHA256 = '28FA3613F4DB035EE728837861ED0A5C1403C8B45BE8858972E36F007011DEB3';
const ROLLBACK_SQL_FILE = path.join(__dirname, '20260804_identity_binding_hardening_emergency_rollback.sql');
const SHA256_PATTERN = /^[0-9A-F]{64}$/;
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

function assertCondition(condition, code) {
  if (!condition) {
    const error = new Error(code);
    error.code = code;
    throw error;
  }
}

function safeErrorCode(error) {
  const raw = String(error && (error.code || error.name) || 'UNKNOWN');
  return /^[A-Za-z0-9_-]{1,96}$/.test(raw) ? raw : 'UNKNOWN';
}

function parseOptions(argv) {
  const options = argv.slice(2);
  let apply = false;
  let confirmedTargetHash = '';
  let confirmedSqlHash = '';
  let emergencyApprovalHash = '';
  let hardeningApplyReceiptHash = '';
  for (let index = 0; index < options.length; index += 1) {
    const option = options[index];
    if (option === '--apply') {
      assertCondition(!apply, 'DUPLICATE_APPLY_OPTION');
      apply = true;
      continue;
    }
    const valueOptions = {
      '--confirm-database-target-sha256': ['confirmedTargetHash', 'DUPLICATE_DATABASE_TARGET_HASH_CONFIRMATION'],
      '--confirm-sha256': ['confirmedSqlHash', 'DUPLICATE_SQL_HASH_CONFIRMATION'],
      '--confirm-emergency-approval-sha256': ['emergencyApprovalHash', 'DUPLICATE_EMERGENCY_APPROVAL_CONFIRMATION'],
      '--confirm-hardening-apply-receipt-sha256': ['hardeningApplyReceiptHash', 'DUPLICATE_HARDENING_APPLY_RECEIPT_CONFIRMATION'],
    };
    assertCondition(Object.prototype.hasOwnProperty.call(valueOptions, option), 'UNKNOWN_ARGUMENT');
    assertCondition(index + 1 < options.length, 'OPTION_VALUE_REQUIRED');
    const [field, duplicateCode] = valueOptions[option];
    const current = {
      confirmedTargetHash,
      confirmedSqlHash,
      emergencyApprovalHash,
      hardeningApplyReceiptHash,
    }[field];
    assertCondition(!current, duplicateCode);
    const value = String(options[index + 1] || '').trim().toUpperCase();
    if (field === 'confirmedTargetHash') confirmedTargetHash = value;
    if (field === 'confirmedSqlHash') confirmedSqlHash = value;
    if (field === 'emergencyApprovalHash') emergencyApprovalHash = value;
    if (field === 'hardeningApplyReceiptHash') hardeningApplyReceiptHash = value;
    index += 1;
  }
  assertCondition(SHA256_PATTERN.test(confirmedTargetHash), 'DATABASE_TARGET_HASH_CONFIRMATION_REQUIRED');
  if (!apply) {
    assertCondition(
      !confirmedSqlHash && !emergencyApprovalHash && !hardeningApplyReceiptHash,
      'APPLY_CONFIRMATION_WITHOUT_APPLY',
    );
  } else {
    assertCondition(confirmedSqlHash === EXPECTED_ROLLBACK_SQL_SHA256, 'EMERGENCY_ROLLBACK_SQL_HASH_CONFIRMATION_REQUIRED');
    assertCondition(SHA256_PATTERN.test(emergencyApprovalHash), 'EMERGENCY_APPROVAL_CONFIRMATION_REQUIRED');
    assertCondition(SHA256_PATTERN.test(hardeningApplyReceiptHash), 'HARDENING_APPLY_RECEIPT_CONFIRMATION_REQUIRED');
    const distinct = new Set([
      confirmedTargetHash,
      confirmedSqlHash,
      emergencyApprovalHash,
      hardeningApplyReceiptHash,
      EXPECTED_BUSINESS_STATE_SHA256,
    ]);
    assertCondition(distinct.size === 5, 'EMERGENCY_CONFIRMATION_HASH_REUSE_REJECTED');
  }
  return {
    apply,
    confirmedTargetHash,
    confirmedSqlHash,
    emergencyApprovalHash,
    hardeningApplyReceiptHash,
  };
}

function databaseTargetSha256(connectionString) {
  let parsed;
  try { parsed = new URL(String(connectionString || '')); }
  catch (_) { assertCondition(false, 'DATABASE_URL_INVALID'); }
  assertCondition(
    parsed.protocol === 'postgres:' || parsed.protocol === 'postgresql:',
    'DATABASE_URL_PROTOCOL_INVALID',
  );
  assertCondition(/^[a-z0-9.-]+$/i.test(parsed.hostname), 'DATABASE_URL_HOST_INVALID');
  const encodedName = parsed.pathname.replace(/^\/+/, '');
  let databaseName;
  try { databaseName = decodeURIComponent(encodedName); }
  catch (_) { assertCondition(false, 'DATABASE_URL_NAME_INVALID'); }
  assertCondition(/^[A-Za-z0-9_.-]{1,63}$/.test(databaseName), 'DATABASE_URL_NAME_INVALID');
  const canonical = `postgresql://${parsed.hostname.toLowerCase()}:${parsed.port || '5432'}/${databaseName}`;
  return crypto.createHash('sha256').update(canonical).digest('hex').toUpperCase();
}

function businessStateSha256(state) {
  const canonical = BUSINESS_KEYS.map(key => `${key}=${Number(state[key])}`).join('|');
  return crypto.createHash('sha256').update(canonical).digest('hex').toUpperCase();
}

async function summary(client) {
  const result = await client.query(`
    /* techie-identity-hardening-emergency:summary */
    SELECT
      (SELECT count(*)::int FROM tenants) AS tenants,
      (SELECT count(*)::int FROM customer_account) AS customer_accounts,
      (SELECT count(*)::int FROM customer_account WHERE stripe_customer_id IS NOT NULL AND btrim(stripe_customer_id) <> '') AS stripe_links,
      (SELECT count(*)::int FROM (SELECT tenant_id FROM customer_account GROUP BY tenant_id HAVING count(*) > 1) d) AS duplicate_tenant_accounts,
      (SELECT count(*)::int FROM (SELECT stripe_customer_id FROM customer_account WHERE stripe_customer_id IS NOT NULL AND btrim(stripe_customer_id) <> '' GROUP BY stripe_customer_id HAVING count(*) > 1) d) AS duplicate_stripe_links,
      (SELECT count(*)::int FROM information_schema.tables WHERE table_schema = 'public' AND table_name = ANY($1::text[])) AS identity_tables,
      (SELECT count(*)::int FROM pg_constraint WHERE conrelid = to_regclass('public.external_identity_binding') AND conname = ANY($2::text[])) AS hardening_constraints,
      (SELECT count(*)::int FROM pg_constraint WHERE conrelid = to_regclass('public.external_identity_binding') AND conname = ANY($2::text[]) AND convalidated) AS validated_hardening_constraints,
      (SELECT count(*)::int FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'external_identity_binding' AND column_name = ANY($3::text[]) AND column_default IS NOT NULL) AS unsafe_binding_defaults
  `, [
    IDENTITY_TABLES,
    [
      'chk_external_identity_binding_directory_tenant_id',
      'chk_external_identity_binding_identity_provider',
    ],
    ['directory_tenant_id', 'identity_provider'],
  ]);
  return result.rows[0];
}

async function identityRowCounts(client) {
  const counts = {};
  for (const tableName of IDENTITY_TABLES) {
    const result = await client.query(`SELECT count(*)::int AS count FROM ${tableName}`);
    counts[tableName] = Number(result.rows[0].count);
  }
  return counts;
}

function assertIdentityEmpty(counts, prefix) {
  assertCondition(
    IDENTITY_TABLES.every(tableName => Number(counts[tableName]) === 0),
    `${prefix}_IDENTITY_SCHEMA_NOT_EMPTY`,
  );
}

function assertBusinessState(state, prefix) {
  assertCondition(
    businessStateSha256(state) === EXPECTED_BUSINESS_STATE_SHA256,
    `${prefix}_BUSINESS_STATE_DIGEST_MISMATCH`,
  );
}

function assertHardenedState(state, rows, prefix) {
  assertCondition(Number(state.identity_tables) === 4, `${prefix}_IDENTITY_TABLE_COUNT_MISMATCH`);
  assertIdentityEmpty(rows, prefix);
  assertCondition(Number(state.hardening_constraints) === 2, `${prefix}_HARDENING_CONSTRAINT_COUNT_MISMATCH`);
  assertCondition(Number(state.validated_hardening_constraints) === 2, `${prefix}_HARDENING_CONSTRAINT_NOT_VALIDATED`);
  assertCondition(Number(state.unsafe_binding_defaults) === 0, `${prefix}_UNSAFE_DEFAULT_PRESENT`);
  assertBusinessState(state, prefix);
}

function assertPreHardeningState(state, rows, prefix) {
  assertCondition(Number(state.identity_tables) === 4, `${prefix}_IDENTITY_TABLE_COUNT_MISMATCH`);
  assertIdentityEmpty(rows, prefix);
  assertCondition(Number(state.hardening_constraints) === 0, `${prefix}_HARDENING_CONSTRAINT_REMAINS`);
  assertCondition(Number(state.validated_hardening_constraints) === 0, `${prefix}_VALIDATED_CONSTRAINT_REMAINS`);
  assertCondition(Number(state.unsafe_binding_defaults) === 2, `${prefix}_PRE_HARDENING_DEFAULT_COUNT_MISMATCH`);
  assertBusinessState(state, prefix);
}

async function runEmergencyRollback({
  ClientClass,
  argv = process.argv,
  env = process.env,
  output = console,
} = {}) {
  assertCondition(typeof ClientClass === 'function', 'PG_CLIENT_NOT_CONFIGURED');
  const options = parseOptions(argv);
  const sql = fs.readFileSync(ROLLBACK_SQL_FILE, 'utf8');
  const actualSqlHash = crypto.createHash('sha256').update(sql).digest('hex').toUpperCase();
  assertCondition(actualSqlHash === EXPECTED_ROLLBACK_SQL_SHA256, 'EMERGENCY_ROLLBACK_SQL_HASH_MISMATCH');
  assertCondition(Boolean(env.DATABASE_URL), 'DATABASE_URL_NOT_CONFIGURED');
  assertCondition(
    databaseTargetSha256(env.DATABASE_URL) === options.confirmedTargetHash,
    'DATABASE_TARGET_HASH_CONFIRMATION_MISMATCH',
  );
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
    const beforeRows = Number(before.identity_tables) === 4 ? await identityRowCounts(client) : {};
    assertHardenedState(before, beforeRows, 'PRECHECK');

    await client.query('BEGIN ISOLATION LEVEL SERIALIZABLE');
    inTransaction = true;
    await client.query("SET LOCAL search_path = public, pg_catalog");
    await client.query("SET LOCAL lock_timeout = '5s'");
    await client.query("SET LOCAL statement_timeout = '60s'");
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('techie-identity-hardening-emergency-rollback-20260804', 0))");
    await client.query(sql);

    const inside = await summary(client);
    const insideRows = await identityRowCounts(client);
    assertPreHardeningState(inside, insideRows, 'IN_TRANSACTION');

    if (!options.apply) {
      await client.query('ROLLBACK');
      inTransaction = false;
      const restored = await summary(client);
      const restoredRows = await identityRowCounts(client);
      assertHardenedState(restored, restoredRows, 'ROLLBACK');
      output.log('HARDENING_EMERGENCY_ROLLBACK_DRY_RUN_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 hardened_state_restored=true commit_state=not_committed');
      return { ok: true, mode: 'dry-run', committed: false };
    }

    await client.query('COMMIT');
    inTransaction = false;
    committed = true;
    const afterCommit = await summary(client);
    const afterCommitRows = await identityRowCounts(client);
    assertPreHardeningState(afterCommit, afterCommitRows, 'COMMIT');
    output.log('HARDENING_EMERGENCY_ROLLBACK_APPLY_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 pre_hardening_state_restored=true commit_state=committed');
    return { ok: true, mode: 'apply', committed: true };
  } catch (error) {
    if (connected && inTransaction) {
      try { await client.query('ROLLBACK'); } catch (_) { /* preserve original */ }
    }
    output.error(`HARDENING_EMERGENCY_ROLLBACK_${options.apply ? 'APPLY' : 'DRY_RUN'}_ERROR ${safeErrorCode(error)} commit_state=${committed ? 'committed' : 'not_committed'}`);
    return { ok: false, mode: options.apply ? 'apply' : 'dry-run', committed };
  } finally {
    if (connected) await client.end().catch(() => {});
  }
}

async function cliMain() {
  const { Client } = require('pg');
  const result = await runEmergencyRollback({ ClientClass: Client });
  if (!result.ok) process.exitCode = 1;
}

if (require.main === module) {
  cliMain().catch(error => {
    console.error(`HARDENING_EMERGENCY_ROLLBACK_RUNNER_ERROR ${safeErrorCode(error)} commit_state=not_committed`);
    process.exitCode = 1;
  });
}

module.exports = {
  EXPECTED_BUSINESS_STATE_SHA256,
  EXPECTED_ROLLBACK_SQL_SHA256,
  IDENTITY_TABLES,
  businessStateSha256,
  databaseTargetSha256,
  parseOptions,
  runEmergencyRollback,
};
