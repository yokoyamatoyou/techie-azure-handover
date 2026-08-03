'use strict';

/**
 * Kudu-only guarded entrypoint for persistent identity-binding hardening.
 *
 * This file is local preparation only. It must not be uploaded or executed
 * without a new explicit live approval. It accepts independent non-secret
 * receipt hashes and never prints them or DATABASE_URL.
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const EXPECTED_REMOTE_DIRECTORY = '/home/LogFiles/techie-identity-hardening-apply';
const EXPECTED_OPERATION = 'APPLY_TECHIE_EMPTY_IDENTITY_BINDING_HARDENING_20260804';
const EXPECTED_PG_VERSION = '8.22.0';
const EXPECTED_SQL_SHA256 = '4E4D677AF23BF6781262F185FCC5C99338C112455294984CCAF2B1E59C310E53';
const EXPECTED_ENGINE_SHA256 = 'CF798F8C970247CAE813247B3ED42A9A5E72C64F47980599EDC72D695F4D913F';
const EXPECTED_RECOVERY_MANIFEST_SHA256 = '00DB2C4E21C0D0F1A3C8DC4A967A7DAE112E97A1B27A3CE94D308448EEBCE768';
const EXPECTED_ROLLBACK_SQL_SHA256 = '40C6774F8DD9251999F09A571C46297E8AFB8DD7118D6008266099CB1B58F19E';
const EXPECTED_ROLLBACK_RUNNER_SHA256 = 'C049F7661DEC1AD2D5CB5E57E873DFA70A3E0906F6928DF57B300A726AB7CBCC';
const EXPECTED_DRY_RUN_PACKAGE_SHA256 = '6A2658589D35D079CE2E826A7CEF958913CAA8C095B1CD07636238FF76E93727';
const EXPECTED_BUSINESS_STATE_SHA256 = '28FA3613F4DB035EE728837861ED0A5C1403C8B45BE8858972E36F007011DEB3';
const EXPECTED_ENGINE_SUCCESS = 'HARDENING_APPLY_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 commit_state=committed';
const SUPPORTED_NODE_MAJORS = new Set([20, 22]);
const SHA256_PATTERN = /^[0-9A-F]{64}$/;

const VALUE_OPTIONS = Object.freeze({
  '--confirm-database-target-sha256': 'confirmedTargetHash',
  '--confirm-dry-run-package-sha256': 'confirmedDryRunPackageHash',
  '--confirm-dry-run-receipt-sha256': 'dryRunReceiptHash',
  '--confirm-change-approval-sha256': 'changeApprovalHash',
  '--confirm-runtime-state-receipt-sha256': 'runtimeStateReceiptHash',
  '--confirm-maintenance-window-receipt-sha256': 'maintenanceWindowReceiptHash',
  '--confirm-recovery-manifest-sha256': 'confirmedRecoveryManifestHash',
  '--confirm-operation': 'confirmedOperation',
});

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

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex').toUpperCase();
}

function normalizePosixDirectory(value) {
  return String(value || '').replace(/\\/g, '/').replace(/\/+$/, '');
}

function assertRecoveryManifest(bytes) {
  let manifest;
  try {
    manifest = JSON.parse(Buffer.from(bytes).toString('utf8'));
  } catch (_) {
    assertCondition(false, 'EMERGENCY_RECOVERY_MANIFEST_JSON_INVALID');
  }
  assertCondition(
    manifest.schema_version === 'techie-identity-binding-hardening-emergency-recovery-v1',
    'EMERGENCY_RECOVERY_MANIFEST_SCHEMA_INVALID',
  );
  assertCondition(
    manifest.source_commit === '692e9ff85092aa4323f5029ca5d91a987c19b3a0',
    'EMERGENCY_RECOVERY_SOURCE_COMMIT_MISMATCH',
  );
  assertCondition(
    manifest.persistent_use_requires_separate_emergency_approval === true,
    'EMERGENCY_RECOVERY_APPROVAL_BOUNDARY_MISSING',
  );
  const expectedEntries = new Map([
    ['20260804_identity_binding_hardening_emergency_rollback.sql', {
      bytes: 664,
      sha256: EXPECTED_ROLLBACK_SQL_SHA256,
    }],
    ['20260804_identity_binding_hardening_emergency_rollback_runner.js', {
      bytes: 12701,
      sha256: EXPECTED_ROLLBACK_RUNNER_SHA256,
    }],
  ]);
  assertCondition(Array.isArray(manifest.entries) && manifest.entries.length === 2, 'EMERGENCY_RECOVERY_ENTRY_COUNT_MISMATCH');
  const seen = new Set();
  for (const entry of manifest.entries) {
    const expected = expectedEntries.get(entry && entry.name);
    assertCondition(Boolean(expected) && !seen.has(entry.name), 'EMERGENCY_RECOVERY_ENTRY_INVALID');
    assertCondition(Number(entry.bytes) === expected.bytes, 'EMERGENCY_RECOVERY_ENTRY_BYTES_MISMATCH');
    assertCondition(entry.sha256 === expected.sha256, 'EMERGENCY_RECOVERY_ENTRY_HASH_MISMATCH');
    seen.add(entry.name);
  }
}

function parseOptions(argv) {
  const options = argv.slice(2);
  assertCondition(options.length === Object.keys(VALUE_OPTIONS).length * 2, 'APPLY_ARGUMENT_SHAPE_INVALID');
  const parsed = Object.fromEntries(Object.values(VALUE_OPTIONS).map(field => [field, '']));
  for (let index = 0; index < options.length; index += 2) {
    const option = options[index];
    assertCondition(Object.prototype.hasOwnProperty.call(VALUE_OPTIONS, option), 'APPLY_ARGUMENT_NOT_ALLOWED');
    const field = VALUE_OPTIONS[option];
    assertCondition(!parsed[field], 'DUPLICATE_APPLY_CONFIRMATION');
    assertCondition(index + 1 < options.length, 'APPLY_CONFIRMATION_VALUE_REQUIRED');
    parsed[field] = String(options[index + 1] || '').trim();
  }

  for (const field of [
    'confirmedTargetHash',
    'confirmedDryRunPackageHash',
    'dryRunReceiptHash',
    'changeApprovalHash',
    'runtimeStateReceiptHash',
    'maintenanceWindowReceiptHash',
    'confirmedRecoveryManifestHash',
  ]) {
    parsed[field] = parsed[field].toUpperCase();
    assertCondition(SHA256_PATTERN.test(parsed[field]), 'APPLY_CONFIRMATION_SHA256_REQUIRED');
  }
  assertCondition(
    parsed.confirmedDryRunPackageHash === EXPECTED_DRY_RUN_PACKAGE_SHA256,
    'DRY_RUN_PACKAGE_HASH_CONFIRMATION_MISMATCH',
  );
  assertCondition(
    parsed.confirmedRecoveryManifestHash === EXPECTED_RECOVERY_MANIFEST_SHA256,
    'EMERGENCY_RECOVERY_MANIFEST_HASH_CONFIRMATION_MISMATCH',
  );
  assertCondition(parsed.confirmedOperation === EXPECTED_OPERATION, 'APPLY_OPERATION_CONFIRMATION_MISMATCH');

  const independentHashes = [
    parsed.confirmedTargetHash,
    parsed.confirmedDryRunPackageHash,
    parsed.dryRunReceiptHash,
    parsed.changeApprovalHash,
    parsed.runtimeStateReceiptHash,
    parsed.maintenanceWindowReceiptHash,
    parsed.confirmedRecoveryManifestHash,
    EXPECTED_SQL_SHA256,
    EXPECTED_ENGINE_SHA256,
    EXPECTED_ROLLBACK_SQL_SHA256,
    EXPECTED_ROLLBACK_RUNNER_SHA256,
    EXPECTED_BUSINESS_STATE_SHA256,
  ];
  assertCondition(new Set(independentHashes).size === independentHashes.length, 'APPLY_CONFIRMATION_HASH_REUSE_REJECTED');
  return parsed;
}

async function runApplyOnly({
  argv = process.argv,
  env = process.env,
  cwd = process.cwd(),
  platform = process.platform,
  nodeVersion = process.versions.node,
  readFile = fs.readFileSync,
  runHardeningApply,
  ClientClass,
  pgVersion,
  output = console,
} = {}) {
  const confirmations = parseOptions(argv);
  assertCondition(platform === 'linux', 'KUDU_LINUX_RUNTIME_REQUIRED');
  assertCondition(
    normalizePosixDirectory(cwd) === EXPECTED_REMOTE_DIRECTORY,
    'KUDU_APPLY_DIRECTORY_MISMATCH',
  );
  const nodeMajor = Number(String(nodeVersion || '').split('.')[0]);
  assertCondition(SUPPORTED_NODE_MAJORS.has(nodeMajor), 'NODE_RUNTIME_VERSION_NOT_REVIEWED');

  const sourceFiles = {
    engine: path.join(__dirname, '20260804_identity_binding_hardening_apply_engine.js'),
    sql: path.join(__dirname, '20260804_identity_binding_hardening.sql'),
    recoveryManifest: path.join(__dirname, 'emergency_recovery_manifest.json'),
  };
  const sourceBytes = Object.fromEntries(
    Object.entries(sourceFiles).map(([key, filePath]) => [key, readFile(filePath)]),
  );
  assertCondition(sha256(sourceBytes.engine) === EXPECTED_ENGINE_SHA256, 'REMOTE_HARDENING_ENGINE_HASH_MISMATCH');
  assertCondition(sha256(sourceBytes.sql) === EXPECTED_SQL_SHA256, 'REMOTE_HARDENING_SQL_HASH_MISMATCH');
  assertCondition(
    sha256(sourceBytes.recoveryManifest) === EXPECTED_RECOVERY_MANIFEST_SHA256,
    'REMOTE_RECOVERY_MANIFEST_HASH_MISMATCH',
  );
  assertRecoveryManifest(sourceBytes.recoveryManifest);
  assertCondition(Boolean(env.DATABASE_URL), 'DATABASE_URL_NOT_CONFIGURED');

  let resolvedRunHardeningApply = runHardeningApply;
  let resolvedClientClass = ClientClass;
  let resolvedPgVersion = pgVersion;
  if (!resolvedRunHardeningApply || !resolvedClientClass || !resolvedPgVersion) {
    const engineModule = require(sourceFiles.engine);
    const pgPackage = require('pg/package.json');
    const pgModule = require('pg');
    resolvedRunHardeningApply = engineModule.runHardeningApply;
    resolvedClientClass = pgModule.Client;
    resolvedPgVersion = pgPackage.version;
  }
  assertCondition(typeof resolvedRunHardeningApply === 'function', 'HARDENING_ENGINE_EXPORT_INVALID');
  assertCondition(typeof resolvedClientClass === 'function', 'PG_CLIENT_EXPORT_INVALID');
  assertCondition(resolvedPgVersion === EXPECTED_PG_VERSION, 'PG_RUNTIME_VERSION_NOT_REVIEWED');

  const engineMessages = [];
  let result;
  try {
    result = await resolvedRunHardeningApply({
      ClientClass: resolvedClientClass,
      confirmedTargetHash: confirmations.confirmedTargetHash,
      sqlBytes: sourceBytes.sql,
      env,
      output: {
        log: value => engineMessages.push(String(value)),
        error: value => engineMessages.push(String(value)),
      },
    });
  } catch (error) {
    output.error(`KUDU_HARDENING_APPLY_ERROR ${safeErrorCode(error)} commit_state=unknown`);
    return { ok: false, committed: null };
  }

  const exactSuccess = engineMessages.length === 1 && engineMessages[0] === EXPECTED_ENGINE_SUCCESS;
  if (result && result.committed === true) {
    if (result.ok === true && result.mode === 'apply' && exactSuccess) {
      output.log('KUDU_HARDENING_APPLY_PASS target_confirmed=true dry_run_receipt_confirmed=true change_approval_confirmed=true runtime_legacy_confirmed=true maintenance_window_confirmed=true recovery_confirmed=true identity_rows=0 commit_state=committed');
      return { ok: true, committed: true };
    }
    output.error('KUDU_HARDENING_APPLY_ERROR POST_COMMIT_VERIFICATION_OR_OUTPUT_INVALID commit_state=committed');
    return { ok: false, committed: true };
  }

  output.error('KUDU_HARDENING_APPLY_ERROR UNDERLYING_APPLY_NOT_COMMITTED commit_state=not_committed');
  return { ok: false, committed: false };
}

async function cliMain() {
  try {
    const result = await runApplyOnly();
    if (!result.ok) process.exitCode = 1;
  } catch (error) {
    console.error(`KUDU_HARDENING_APPLY_ERROR ${safeErrorCode(error)} commit_state=not_committed`);
    process.exitCode = 1;
  }
}

if (require.main === module) cliMain();

module.exports = {
  EXPECTED_DRY_RUN_PACKAGE_SHA256,
  EXPECTED_ENGINE_SHA256,
  EXPECTED_ENGINE_SUCCESS,
  EXPECTED_OPERATION,
  EXPECTED_PG_VERSION,
  EXPECTED_RECOVERY_MANIFEST_SHA256,
  EXPECTED_REMOTE_DIRECTORY,
  EXPECTED_SQL_SHA256,
  parseOptions,
  runApplyOnly,
  safeErrorCode,
};
