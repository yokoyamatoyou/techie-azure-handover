'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  EXPECTED_PG_VERSION,
  EXPECTED_REMOTE_DIRECTORY,
  EXPECTED_RUNNER_SHA256,
  EXPECTED_RUNNER_SUCCESS,
  EXPECTED_SQL_SHA256,
  parseOptions,
  runDryRunOnly,
} = require('./20260804_identity_binding_hardening_dryrun_only');

const TARGET_HASH = 'A'.repeat(64);
const FIXTURE_DATABASE_URL = 'postgresql://fixture-user:fixture-credential@db.example.test:5432/techie';
const RUNNER_BYTES = Buffer.from('fixture-runner');
const SQL_BYTES = Buffer.from('fixture-sql');

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

function baseDependencies(overrides = {}) {
  const capture = captureOutput();
  const calls = [];
  return {
    capture,
    calls,
    dependencies: {
      argv: ['node', 'dryrun', '--confirm-database-target-sha256', TARGET_HASH],
      env: { DATABASE_URL: FIXTURE_DATABASE_URL },
      cwd: EXPECTED_REMOTE_DIRECTORY,
      platform: 'linux',
      nodeVersion: '22.18.0',
      readFile: filePath => (
        String(filePath).endsWith('20260804_identity_binding_hardening_runner.js')
          ? RUNNER_BYTES
          : SQL_BYTES
      ),
      runHardening: async options => {
        calls.push(options);
        options.output.log(EXPECTED_RUNNER_SUCCESS);
        return { ok: true, mode: 'dry-run', committed: false };
      },
      ClientClass: class FixtureClient {},
      pgVersion: EXPECTED_PG_VERSION,
      output: capture.output,
      ...overrides,
    },
  };
}

function productionReadFile(filePath) {
  const name = path.basename(String(filePath));
  if (name === '20260804_identity_binding_hardening_runner.js') {
    return fs.readFileSync(path.join(__dirname, '..', name));
  }
  if (name === '20260804_identity_binding_hardening.sql') {
    return fs.readFileSync(path.join(__dirname, '..', name));
  }
  throw new Error('UNEXPECTED_TEST_FILE');
}

async function main() {
  assert.deepStrictEqual(
    parseOptions(['node', 'dryrun', '--confirm-database-target-sha256', TARGET_HASH]),
    { confirmedTargetHash: TARGET_HASH },
  );
  for (const argv of [
    ['node', 'dryrun'],
    ['node', 'dryrun', '--apply', '--confirm-database-target-sha256', TARGET_HASH],
    ['node', 'dryrun', '--confirm-database-target-sha256', TARGET_HASH, '--unknown'],
  ]) {
    assert.throws(() => parseOptions(argv), /DRY_RUN_ARGUMENT/);
  }

  const valid = baseDependencies({ readFile: productionReadFile });
  const result = await runDryRunOnly(valid.dependencies);
  assert.deepStrictEqual(result, { ok: true, committed: false });
  assert.strictEqual(valid.calls.length, 1);
  assert.deepStrictEqual(valid.calls[0].argv, [
    'node',
    '20260804_identity_binding_hardening_runner.js',
    '--confirm-database-target-sha256',
    TARGET_HASH,
  ]);
  assert.doesNotMatch(valid.calls[0].argv.join(' '), /--apply/);
  assert.match(valid.capture.messages.join('\n'), /apply_capability=false/);
  assert.doesNotMatch(valid.capture.messages.join('\n'), /fixture-user|fixture-credential|db\.example\.test|techie/);

  for (const [override, code] of [
    [{ cwd: '/home/site/wwwroot' }, 'KUDU_ISOLATED_DIRECTORY_MISMATCH'],
    [{ platform: 'win32' }, 'KUDU_LINUX_RUNTIME_REQUIRED'],
    [{ nodeVersion: '24.0.0' }, 'NODE_RUNTIME_VERSION_NOT_REVIEWED'],
    [{ pgVersion: '8.21.0' }, 'PG_RUNTIME_VERSION_NOT_REVIEWED'],
  ]) {
    const fixture = baseDependencies({ readFile: productionReadFile, ...override });
    await assert.rejects(() => runDryRunOnly(fixture.dependencies), new RegExp(code));
    assert.strictEqual(fixture.calls.length, 0);
  }

  const badRunner = baseDependencies({
    readFile: filePath => (
      String(filePath).endsWith('20260804_identity_binding_hardening_runner.js')
        ? RUNNER_BYTES
        : productionReadFile(filePath)
    ),
  });
  await assert.rejects(() => runDryRunOnly(badRunner.dependencies), /REMOTE_HARDENING_RUNNER_HASH_MISMATCH/);
  assert.strictEqual(badRunner.calls.length, 0);

  const badSql = baseDependencies({
    readFile: filePath => (
      String(filePath).endsWith('20260804_identity_binding_hardening.sql')
        ? SQL_BYTES
        : productionReadFile(filePath)
    ),
  });
  await assert.rejects(() => runDryRunOnly(badSql.dependencies), /REMOTE_HARDENING_SQL_HASH_MISMATCH/);
  assert.strictEqual(badSql.calls.length, 0);

  const unexpectedCommit = baseDependencies({
    readFile: productionReadFile,
    runHardening: async options => {
      options.output.log(EXPECTED_RUNNER_SUCCESS);
      return { ok: true, mode: 'apply', committed: true };
    },
  });
  await assert.rejects(
    () => runDryRunOnly(unexpectedCommit.dependencies),
    /HARDENING_DRY_RUN_MODE_INVALID/,
  );

  const unexpectedOutput = baseDependencies({
    readFile: productionReadFile,
    runHardening: async options => {
      options.output.log('unexpected');
      return { ok: true, mode: 'dry-run', committed: false };
    },
  });
  await assert.rejects(
    () => runDryRunOnly(unexpectedOutput.dependencies),
    /HARDENING_DRY_RUN_OUTPUT_CONTRACT_MISMATCH/,
  );

  const wrapperSource = fs.readFileSync(
    path.join(__dirname, '20260804_identity_binding_hardening_dryrun_only.js'),
    'utf8',
  );
  assert.doesNotMatch(wrapperSource, /argv[^\n]*--apply|options\.push\([^\n]*--apply/);
  assert.match(wrapperSource, /apply_capability=false/);
  assert.match(wrapperSource, /ssl|runHardening/);

  const manifest = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'kudu_hardening_dryrun_manifest.json'),
    'utf8',
  ));
  assert.strictEqual(manifest.mode, 'transaction-rollback-dry-run-only');
  assert.strictEqual(manifest.apply_capability, false);
  assert.strictEqual(manifest.remote_directory, EXPECTED_REMOTE_DIRECTORY);
  assert.strictEqual(manifest.required_pg_version, EXPECTED_PG_VERSION);
  assert.strictEqual(manifest.entries.length, 3);
  const expectedEntries = new Map([
    ['20260804_identity_binding_hardening.sql', EXPECTED_SQL_SHA256],
    ['20260804_identity_binding_hardening_runner.js', EXPECTED_RUNNER_SHA256],
    [
      '20260804_identity_binding_hardening_dryrun_only.js',
      '4250B233E3988A1D9614FBCBF0B9DE0FC4BAE5CD1AE842F8DDDC63B92653F4D2',
    ],
  ]);
  for (const entry of manifest.entries) {
    assert.strictEqual(entry.sha256, expectedEntries.get(entry.name));
    const sourcePath = entry.name === '20260804_identity_binding_hardening_dryrun_only.js'
      ? path.join(__dirname, entry.name)
      : path.join(__dirname, '..', entry.name);
    const bytes = fs.readFileSync(sourcePath);
    assert.strictEqual(entry.bytes, bytes.length);
    assert.strictEqual(
      require('crypto').createHash('sha256').update(bytes).digest('hex').toUpperCase(),
      entry.sha256,
    );
  }

  console.log('identity-binding-hardening-kudu-dryrun-only-tests: 13 passed');
}

main().catch(error => {
  console.error(`identity-binding-hardening-kudu-dryrun-only-tests: failed ${error.code || error.name}`);
  process.exitCode = 1;
});
