'use strict';

/**
 * Offline target-identity preflight for the DB hardening runner.
 *
 * DATABASE_URL must come from the protected application runtime. The expected
 * host/name/port must be obtained independently from the reviewed Azure DB
 * resource and must not be copied from DATABASE_URL. No network or DB call is
 * made and no raw target or credential is printed.
 */
const {
  databaseTargetSha256,
  databaseTargetSha256FromParts,
} = require('./20260804_identity_binding_hardening_runner');

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

function runTargetPreflight({ env = process.env, output = console } = {}) {
  try {
    assertCondition(Boolean(env.DATABASE_URL), 'DATABASE_URL_NOT_CONFIGURED');
    assertCondition(Boolean(env.EXPECTED_DATABASE_HOST), 'EXPECTED_DATABASE_HOST_NOT_CONFIGURED');
    assertCondition(Boolean(env.EXPECTED_DATABASE_NAME), 'EXPECTED_DATABASE_NAME_NOT_CONFIGURED');
    const actual = databaseTargetSha256(env.DATABASE_URL);
    const expected = databaseTargetSha256FromParts(
      env.EXPECTED_DATABASE_HOST,
      env.EXPECTED_DATABASE_PORT || '5432',
      env.EXPECTED_DATABASE_NAME,
    );
    assertCondition(actual === expected, 'DATABASE_TARGET_INDEPENDENT_SOURCE_MISMATCH');
    output.log(`DATABASE_TARGET_PREFLIGHT_PASS confirm_database_target_sha256=${actual}`);
    return { ok: true, databaseTargetSha256: actual };
  } catch (error) {
    output.error(`DATABASE_TARGET_PREFLIGHT_ERROR ${safeErrorCode(error)}`);
    return { ok: false };
  }
}

if (require.main === module) {
  const result = runTargetPreflight();
  if (!result.ok) process.exitCode = 1;
}

module.exports = { runTargetPreflight };
