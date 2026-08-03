'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  EXPECTED_DRY_RUN_PACKAGE_SHA256,
  EXPECTED_ENGINE_SUCCESS,
  EXPECTED_OPERATION,
  EXPECTED_PG_VERSION,
  EXPECTED_RECOVERY_MANIFEST_SHA256,
  EXPECTED_REMOTE_DIRECTORY,
  EXPECTED_SQL_SHA256,
  parseOptions,
  runApplyOnly,
} = require('./20260804_identity_binding_hardening_apply_only');

const TARGET_HASH = '1'.repeat(64);
const DRY_RUN_RECEIPT_HASH = '2'.repeat(64);
const CHANGE_APPROVAL_HASH = '3'.repeat(64);
const RUNTIME_STATE_RECEIPT_HASH = '4'.repeat(64);
const MAINTENANCE_WINDOW_RECEIPT_HASH = '5'.repeat(64);
const FIXTURE_DATABASE_URL = 'postgresql://fixture-user:fixture-credential@db.example.test:5432/techie';

function validArgv(overrides = {}) {
  return [
    'node',
    'apply-only',
    '--confirm-database-target-sha256',
    overrides.targetHash || TARGET_HASH,
    '--confirm-dry-run-package-sha256',
    overrides.dryRunPackageHash || EXPECTED_DRY_RUN_PACKAGE_SHA256,
    '--confirm-dry-run-receipt-sha256',
    overrides.dryRunReceiptHash || DRY_RUN_RECEIPT_HASH,
    '--confirm-change-approval-sha256',
    overrides.changeApprovalHash || CHANGE_APPROVAL_HASH,
    '--confirm-runtime-state-receipt-sha256',
    overrides.runtimeStateReceiptHash || RUNTIME_STATE_RECEIPT_HASH,
    '--confirm-maintenance-window-receipt-sha256',
    overrides.maintenanceWindowReceiptHash || MAINTENANCE_WINDOW_RECEIPT_HASH,
    '--confirm-recovery-manifest-sha256',
    overrides.recoveryManifestHash || EXPECTED_RECOVERY_MANIFEST_SHA256,
    '--confirm-operation',
    overrides.operation || EXPECTED_OPERATION,
  ];
}

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

function productionReadFile(filePath) {
  const name = path.basename(String(filePath));
  const localFiles = new Set([
    '20260804_identity_binding_hardening_apply_engine.js',
    'emergency_recovery_manifest.json',
  ]);
  const parentFiles = new Set([
    '20260804_identity_binding_hardening.sql',
    '20260804_identity_binding_hardening_emergency_rollback.sql',
    '20260804_identity_binding_hardening_emergency_rollback_runner.js',
  ]);
  if (localFiles.has(name)) return fs.readFileSync(path.join(__dirname, name));
  if (parentFiles.has(name)) return fs.readFileSync(path.join(__dirname, '..', name));
  throw new Error('UNEXPECTED_TEST_FILE');
}

function baseDependencies(overrides = {}) {
  const capture = captureOutput();
  const calls = [];
  return {
    capture,
    calls,
    dependencies: {
      argv: validArgv(),
      env: { DATABASE_URL: FIXTURE_DATABASE_URL },
      cwd: EXPECTED_REMOTE_DIRECTORY,
      platform: 'linux',
      nodeVersion: '22.18.0',
      readFile: productionReadFile,
      runHardeningApply: async options => {
        calls.push(options);
        options.output.log(EXPECTED_ENGINE_SUCCESS);
        return { ok: true, mode: 'apply', committed: true };
      },
      ClientClass: class FixtureClient {},
      pgVersion: EXPECTED_PG_VERSION,
      output: capture.output,
      ...overrides,
    },
  };
}

async function main() {
  const parsed = parseOptions(validArgv());
  assert.strictEqual(parsed.confirmedTargetHash, TARGET_HASH);
  assert.strictEqual(parsed.confirmedDryRunPackageHash, EXPECTED_DRY_RUN_PACKAGE_SHA256);
  assert.strictEqual(parsed.confirmedRecoveryManifestHash, EXPECTED_RECOVERY_MANIFEST_SHA256);
  assert.strictEqual(parsed.confirmedOperation, EXPECTED_OPERATION);

  for (const argv of [
    ['node', 'apply-only'],
    [...validArgv(), '--apply'],
    validArgv().map(value => value === '--confirm-operation' ? '--unknown' : value),
  ]) {
    assert.throws(() => parseOptions(argv), /APPLY_ARGUMENT/);
  }
  assert.throws(
    () => parseOptions(validArgv({ dryRunPackageHash: 'A'.repeat(64) })),
    /DRY_RUN_PACKAGE_HASH_CONFIRMATION_MISMATCH/,
  );
  assert.throws(
    () => parseOptions(validArgv({ recoveryManifestHash: 'B'.repeat(64) })),
    /EMERGENCY_RECOVERY_MANIFEST_HASH_CONFIRMATION_MISMATCH/,
  );
  assert.throws(
    () => parseOptions(validArgv({ operation: 'apply' })),
    /APPLY_OPERATION_CONFIRMATION_MISMATCH/,
  );
  assert.throws(
    () => parseOptions(validArgv({ changeApprovalHash: DRY_RUN_RECEIPT_HASH })),
    /APPLY_CONFIRMATION_HASH_REUSE_REJECTED/,
  );

  const valid = baseDependencies();
  const result = await runApplyOnly(valid.dependencies);
  assert.deepStrictEqual(result, { ok: true, committed: true });
  assert.strictEqual(valid.calls.length, 1);
  assert.strictEqual(valid.calls[0].confirmedTargetHash, TARGET_HASH);
  assert.strictEqual(
    require('crypto').createHash('sha256').update(valid.calls[0].sqlBytes).digest('hex').toUpperCase(),
    EXPECTED_SQL_SHA256,
  );
  assert.strictEqual(Object.prototype.hasOwnProperty.call(valid.calls[0], 'argv'), false);
  const forwarded = JSON.stringify(valid.calls[0]);
  for (const protectedHash of [
    DRY_RUN_RECEIPT_HASH,
    CHANGE_APPROVAL_HASH,
    RUNTIME_STATE_RECEIPT_HASH,
    MAINTENANCE_WINDOW_RECEIPT_HASH,
    EXPECTED_RECOVERY_MANIFEST_SHA256,
  ]) {
    assert(!forwarded.includes(protectedHash));
  }
  const validOutput = valid.capture.messages.join('\n');
  assert.match(validOutput, /KUDU_HARDENING_APPLY_PASS/);
  assert.match(validOutput, /commit_state=committed/);
  assert.doesNotMatch(validOutput, /fixture-user|fixture-credential|db\.example\.test|techie|[0-9A-F]{64}/);

  for (const [override, code] of [
    [{ cwd: '/home/site/wwwroot' }, 'KUDU_APPLY_DIRECTORY_MISMATCH'],
    [{ platform: 'win32' }, 'KUDU_LINUX_RUNTIME_REQUIRED'],
    [{ nodeVersion: '24.0.0' }, 'NODE_RUNTIME_VERSION_NOT_REVIEWED'],
    [{ pgVersion: '8.21.0' }, 'PG_RUNTIME_VERSION_NOT_REVIEWED'],
    [{ env: {} }, 'DATABASE_URL_NOT_CONFIGURED'],
  ]) {
    const fixture = baseDependencies(override);
    await assert.rejects(() => runApplyOnly(fixture.dependencies), new RegExp(code));
    assert.strictEqual(fixture.calls.length, 0);
  }

  for (const [tamperedName, code] of [
    ['20260804_identity_binding_hardening_apply_engine.js', 'REMOTE_HARDENING_ENGINE_HASH_MISMATCH'],
    ['20260804_identity_binding_hardening.sql', 'REMOTE_HARDENING_SQL_HASH_MISMATCH'],
    ['emergency_recovery_manifest.json', 'REMOTE_RECOVERY_MANIFEST_HASH_MISMATCH'],
  ]) {
    const fixture = baseDependencies({
      readFile: filePath => (
        path.basename(String(filePath)) === tamperedName
          ? Buffer.from('tampered')
          : productionReadFile(filePath)
      ),
    });
    await assert.rejects(() => runApplyOnly(fixture.dependencies), new RegExp(code));
    assert.strictEqual(fixture.calls.length, 0);
  }

  const rejected = baseDependencies({
    runHardeningApply: async options => {
      options.output.error('HARDENING_APPLY_ERROR PRECHECK_FAILED commit_state=not_committed');
      return { ok: false, mode: 'apply', committed: false };
    },
  });
  assert.deepStrictEqual(
    await runApplyOnly(rejected.dependencies),
    { ok: false, committed: false },
  );
  assert.deepStrictEqual(
    rejected.capture.messages,
    ['KUDU_HARDENING_APPLY_ERROR UNDERLYING_APPLY_NOT_COMMITTED commit_state=not_committed'],
  );

  const postCommitFailure = baseDependencies({
    runHardeningApply: async options => {
      options.output.error('HARDENING_APPLY_ERROR COMMIT_VERIFY_FAILED commit_state=committed');
      return { ok: false, mode: 'apply', committed: true };
    },
  });
  assert.deepStrictEqual(
    await runApplyOnly(postCommitFailure.dependencies),
    { ok: false, committed: true },
  );
  assert.deepStrictEqual(
    postCommitFailure.capture.messages,
    ['KUDU_HARDENING_APPLY_ERROR POST_COMMIT_VERIFICATION_OR_OUTPUT_INVALID commit_state=committed'],
  );

  const unexpectedCommittedOutput = baseDependencies({
    runHardeningApply: async options => {
      options.output.log('unexpected');
      return { ok: true, mode: 'apply', committed: true };
    },
  });
  assert.deepStrictEqual(
    await runApplyOnly(unexpectedCommittedOutput.dependencies),
    { ok: false, committed: true },
  );

  const thrown = baseDependencies({
    runHardeningApply: async () => {
      throw Object.assign(new Error('fixture'), { code: 'RUNNER_THROWN' });
    },
  });
  assert.deepStrictEqual(await runApplyOnly(thrown.dependencies), { ok: false, committed: null });
  assert.deepStrictEqual(
    thrown.capture.messages,
    ['KUDU_HARDENING_APPLY_ERROR RUNNER_THROWN commit_state=unknown'],
  );

  const recoveryManifestBytes = fs.readFileSync(
    path.join(__dirname, 'emergency_recovery_manifest.json'),
  );
  const recoveryManifestHash = require('crypto')
    .createHash('sha256')
    .update(recoveryManifestBytes)
    .digest('hex')
    .toUpperCase();
  assert.strictEqual(recoveryManifestHash, EXPECTED_RECOVERY_MANIFEST_SHA256);
  const recoveryManifest = JSON.parse(recoveryManifestBytes.toString('utf8'));
  assert.strictEqual(recoveryManifest.source_commit, '692e9ff85092aa4323f5029ca5d91a987c19b3a0');
  assert.strictEqual(recoveryManifest.entries.length, 2);
  for (const entry of recoveryManifest.entries) {
    const bytes = productionReadFile(entry.name);
    assert.strictEqual(bytes.length, entry.bytes);
    assert.strictEqual(
      require('crypto').createHash('sha256').update(bytes).digest('hex').toUpperCase(),
      entry.sha256,
    );
  }

  const applyManifest = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'kudu_hardening_apply_manifest.json'),
    'utf8',
  ));
  assert.strictEqual(applyManifest.mode, 'persistent-apply-with-independent-receipt-gates');
  assert.strictEqual(applyManifest.authorization_embedded, false);
  assert.strictEqual(applyManifest.remote_directory, EXPECTED_REMOTE_DIRECTORY);
  assert.strictEqual(applyManifest.required_pg_version, EXPECTED_PG_VERSION);
  assert.strictEqual(applyManifest.required_operation, EXPECTED_OPERATION);
  assert.strictEqual(applyManifest.entries.length, 4);
  const applySourcePaths = new Map([
    ['20260804_identity_binding_hardening.sql', path.join(__dirname, '..', '20260804_identity_binding_hardening.sql')],
    ['20260804_identity_binding_hardening_apply_engine.js', path.join(__dirname, '20260804_identity_binding_hardening_apply_engine.js')],
    ['emergency_recovery_manifest.json', path.join(__dirname, 'emergency_recovery_manifest.json')],
    ['20260804_identity_binding_hardening_apply_only.js', path.join(__dirname, '20260804_identity_binding_hardening_apply_only.js')],
  ]);
  for (const entry of applyManifest.entries) {
    const sourcePath = applySourcePaths.get(entry.name);
    assert(sourcePath, `UNEXPECTED_APPLY_MANIFEST_ENTRY_${entry.name}`);
    const bytes = fs.readFileSync(sourcePath);
    assert.strictEqual(bytes.length, entry.bytes);
    assert.strictEqual(
      require('crypto').createHash('sha256').update(bytes).digest('hex').toUpperCase(),
      entry.sha256,
    );
  }

  console.log('identity-binding-hardening-kudu-apply-only-tests: 15 passed');
}

main().catch(error => {
  console.error(`identity-binding-hardening-kudu-apply-only-tests: failed ${error.code || error.name}`);
  process.exitCode = 1;
});
