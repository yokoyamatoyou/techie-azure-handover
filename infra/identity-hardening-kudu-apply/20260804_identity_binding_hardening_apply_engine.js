'use strict';

/**
 * Persistent identity-binding hardening engine with no CLI or argument parser.
 * The guarded apply-only wrapper supplies hash-verified SQL bytes and the
 * independently confirmed database target after all receipt gates pass.
 */
const crypto = require('crypto');

const EXPECTED_SQL_SHA256 = '4E4D677AF23BF6781262F185FCC5C99338C112455294984CCAF2B1E59C310E53';
const EXPECTED_BUSINESS_STATE_SHA256 = '28FA3613F4DB035EE728837861ED0A5C1403C8B45BE8858972E36F007011DEB3';
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
const SUCCESS_LINE = 'HARDENING_APPLY_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 commit_state=committed';

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
  const target = `postgresql://${parsed.hostname.toLowerCase()}:${parsed.port || '5432'}/${databaseName}`;
  return crypto.createHash('sha256').update(target).digest('hex').toUpperCase();
}

function businessStateSha256(state) {
  const canonical = BUSINESS_KEYS.map(key => `${key}=${Number(state[key])}`).join('|');
  return crypto.createHash('sha256').update(canonical).digest('hex').toUpperCase();
}

async function summary(client) {
  const result = await client.query(`
    /* techie-identity-hardening-apply-engine:summary */
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

function assertBusinessState(state, prefix) {
  assertCondition(
    businessStateSha256(state) === EXPECTED_BUSINESS_STATE_SHA256,
    `${prefix}_BUSINESS_STATE_DIGEST_MISMATCH`,
  );
}

function assertIdentityRowsEmpty(rows, prefix) {
  assertCondition(
    IDENTITY_TABLES.every(tableName => Number(rows[tableName]) === 0),
    `${prefix}_IDENTITY_SCHEMA_NOT_EMPTY`,
  );
}

function assertUnhardenedState(state, rows, prefix) {
  assertCondition(Number(state.identity_tables) === 4, `${prefix}_IDENTITY_TABLE_COUNT_MISMATCH`);
  assertIdentityRowsEmpty(rows, prefix);
  assertCondition(Number(state.hardening_constraints) === 0, `${prefix}_HARDENING_ALREADY_PRESENT`);
  assertCondition(Number(state.validated_hardening_constraints) === 0, `${prefix}_HARDENING_STATE_INVALID`);
  assertCondition(Number(state.unsafe_binding_defaults) === 2, `${prefix}_UNSAFE_DEFAULT_PRECHECK_FAILED`);
  assertBusinessState(state, prefix);
}

function assertHardenedState(state, rows, prefix) {
  assertCondition(Number(state.identity_tables) === 4, `${prefix}_IDENTITY_TABLE_COUNT_MISMATCH`);
  assertIdentityRowsEmpty(rows, prefix);
  assertCondition(Number(state.hardening_constraints) === 2, `${prefix}_HARDENING_CONSTRAINT_COUNT_MISMATCH`);
  assertCondition(Number(state.validated_hardening_constraints) === 2, `${prefix}_HARDENING_CONSTRAINT_NOT_VALIDATED`);
  assertCondition(Number(state.unsafe_binding_defaults) === 0, `${prefix}_UNSAFE_DEFAULT_REMAINS`);
  assertBusinessState(state, prefix);
}

async function runHardeningApply({
  ClientClass,
  confirmedTargetHash,
  sqlBytes,
  env = process.env,
  output = console,
} = {}) {
  assertCondition(typeof ClientClass === 'function', 'PG_CLIENT_NOT_CONFIGURED');
  const normalizedTargetHash = String(confirmedTargetHash || '').trim().toUpperCase();
  assertCondition(SHA256_PATTERN.test(normalizedTargetHash), 'DATABASE_TARGET_HASH_CONFIRMATION_REQUIRED');
  const sql = Buffer.from(sqlBytes || '').toString('utf8');
  assertCondition(
    crypto.createHash('sha256').update(sql).digest('hex').toUpperCase() === EXPECTED_SQL_SHA256,
    'HARDENING_SQL_HASH_MISMATCH',
  );
  assertCondition(Boolean(env.DATABASE_URL), 'DATABASE_URL_NOT_CONFIGURED');
  assertCondition(
    databaseTargetSha256(env.DATABASE_URL) === normalizedTargetHash,
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
    assertUnhardenedState(before, beforeRows, 'PRECHECK');

    await client.query('BEGIN ISOLATION LEVEL SERIALIZABLE');
    inTransaction = true;
    await client.query("SET LOCAL search_path = public, pg_catalog");
    await client.query("SET LOCAL lock_timeout = '5s'");
    await client.query("SET LOCAL statement_timeout = '60s'");
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('techie-identity-hardening-20260804', 0))");
    await client.query(sql);

    const inside = await summary(client);
    const insideRows = await identityRowCounts(client);
    assertHardenedState(inside, insideRows, 'IN_TRANSACTION');

    await client.query('COMMIT');
    inTransaction = false;
    committed = true;
    const afterCommit = await summary(client);
    const afterCommitRows = await identityRowCounts(client);
    assertHardenedState(afterCommit, afterCommitRows, 'COMMIT');
    output.log(SUCCESS_LINE);
    return { ok: true, mode: 'apply', committed: true };
  } catch (error) {
    if (connected && inTransaction) {
      try { await client.query('ROLLBACK'); } catch (_) { /* preserve original */ }
    }
    output.error(`HARDENING_APPLY_ERROR ${safeErrorCode(error)} commit_state=${committed ? 'committed' : 'not_committed'}`);
    return { ok: false, mode: 'apply', committed };
  } finally {
    if (connected) await client.end().catch(() => {});
  }
}

module.exports = {
  EXPECTED_BUSINESS_STATE_SHA256,
  EXPECTED_SQL_SHA256,
  IDENTITY_TABLES,
  SUCCESS_LINE,
  businessStateSha256,
  databaseTargetSha256,
  runHardeningApply,
};
