'use strict';

/**
 * Kudu-only, apply-incapable entrypoint for the identity-binding hardening
 * transaction dry-run. Upload the commit-fixed flat bundle to the exact
 * isolated directory. This wrapper never forwards caller arguments except the
 * independently reviewed database-target confirmation SHA-256.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const EXPECTED_REMOTE_DIRECTORY = '/home/LogFiles/techie-identity-hardening-audit';
const EXPECTED_RUNNER_SHA256 = '4296FE2A7C3399302B68021D77F01420D685E02FBF3BCE4F6FD209736FF3155B';
const EXPECTED_SQL_SHA256 = '4E4D677AF23BF6781262F185FCC5C99338C112455294984CCAF2B1E59C310E53';
const EXPECTED_PG_VERSION = '8.22.0';
const SUPPORTED_NODE_MAJORS = new Set([20, 22]);
const SHA256_PATTERN = /^[0-9A-F]{64}$/;
const EXPECTED_RUNNER_SUCCESS = 'HARDENING_DRY_RUN_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 commit_state=not_committed';

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
  assertCondition(options.length === 2, 'DRY_RUN_ARGUMENT_SHAPE_INVALID');
  assertCondition(options[0] === '--confirm-database-target-sha256', 'DRY_RUN_ARGUMENT_NOT_ALLOWED');
  const confirmedTargetHash = String(options[1] || '').trim().toUpperCase();
  assertCondition(SHA256_PATTERN.test(confirmedTargetHash), 'DATABASE_TARGET_HASH_CONFIRMATION_REQUIRED');
  return { confirmedTargetHash };
}

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex').toUpperCase();
}

function normalizePosixDirectory(value) {
  return String(value || '').replace(/\\/g, '/').replace(/\/+$/, '');
}

async function runDryRunOnly({
  argv = process.argv,
  env = process.env,
  cwd = process.cwd(),
  platform = process.platform,
  nodeVersion = process.versions.node,
  readFile = fs.readFileSync,
  runHardening,
  ClientClass,
  pgVersion,
  output = console,
} = {}) {
  const { confirmedTargetHash } = parseOptions(argv);
  assertCondition(platform === 'linux', 'KUDU_LINUX_RUNTIME_REQUIRED');
  assertCondition(
    normalizePosixDirectory(cwd) === EXPECTED_REMOTE_DIRECTORY,
    'KUDU_ISOLATED_DIRECTORY_MISMATCH',
  );
  const nodeMajor = Number(String(nodeVersion || '').split('.')[0]);
  assertCondition(SUPPORTED_NODE_MAJORS.has(nodeMajor), 'NODE_RUNTIME_VERSION_NOT_REVIEWED');

  const runnerPath = path.join(__dirname, '20260804_identity_binding_hardening_runner.js');
  const sqlPath = path.join(__dirname, '20260804_identity_binding_hardening.sql');
  const runnerBytes = readFile(runnerPath);
  const sqlBytes = readFile(sqlPath);
  assertCondition(sha256(runnerBytes) === EXPECTED_RUNNER_SHA256, 'REMOTE_HARDENING_RUNNER_HASH_MISMATCH');
  assertCondition(sha256(sqlBytes) === EXPECTED_SQL_SHA256, 'REMOTE_HARDENING_SQL_HASH_MISMATCH');
  assertCondition(Boolean(env.DATABASE_URL), 'DATABASE_URL_NOT_CONFIGURED');

  let resolvedRunHardening = runHardening;
  let resolvedClientClass = ClientClass;
  let resolvedPgVersion = pgVersion;
  if (!resolvedRunHardening || !resolvedClientClass || !resolvedPgVersion) {
    const runnerModule = require(runnerPath);
    const pgPackage = require('pg/package.json');
    const pgModule = require('pg');
    resolvedRunHardening = runnerModule.runHardening;
    resolvedClientClass = pgModule.Client;
    resolvedPgVersion = pgPackage.version;
  }
  assertCondition(typeof resolvedRunHardening === 'function', 'HARDENING_RUNNER_EXPORT_INVALID');
  assertCondition(typeof resolvedClientClass === 'function', 'PG_CLIENT_EXPORT_INVALID');
  assertCondition(resolvedPgVersion === EXPECTED_PG_VERSION, 'PG_RUNTIME_VERSION_NOT_REVIEWED');

  const runnerMessages = [];
  const result = await resolvedRunHardening({
    ClientClass: resolvedClientClass,
    argv: [
      'node',
      '20260804_identity_binding_hardening_runner.js',
      '--confirm-database-target-sha256',
      confirmedTargetHash,
    ],
    env,
    output: {
      log: value => runnerMessages.push(String(value)),
      error: value => runnerMessages.push(String(value)),
    },
  });
  assertCondition(result && result.ok === true, 'HARDENING_DRY_RUN_FAILED');
  assertCondition(result.mode === 'dry-run', 'HARDENING_DRY_RUN_MODE_INVALID');
  assertCondition(result.committed === false, 'HARDENING_DRY_RUN_UNEXPECTED_COMMIT');
  assertCondition(
    runnerMessages.length === 1 && runnerMessages[0] === EXPECTED_RUNNER_SUCCESS,
    'HARDENING_DRY_RUN_OUTPUT_CONTRACT_MISMATCH',
  );
  output.log('KUDU_HARDENING_DRY_RUN_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 commit_state=not_committed apply_capability=false');
  return { ok: true, committed: false };
}

async function cliMain() {
  try {
    const result = await runDryRunOnly();
    if (!result.ok) process.exitCode = 1;
  } catch (error) {
    console.error(`KUDU_HARDENING_DRY_RUN_ERROR ${safeErrorCode(error)} commit_state=not_committed apply_capability=false`);
    process.exitCode = 1;
  }
}

if (require.main === module) cliMain();

module.exports = {
  EXPECTED_PG_VERSION,
  EXPECTED_REMOTE_DIRECTORY,
  EXPECTED_RUNNER_SHA256,
  EXPECTED_RUNNER_SUCCESS,
  EXPECTED_SQL_SHA256,
  parseOptions,
  runDryRunOnly,
  safeErrorCode,
};
