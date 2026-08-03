'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { runTargetPreflight } = require('./20260804_identity_binding_hardening_target_preflight');

const RUNTIME_URL = 'postgresql://protected-user:fixture-credential@db.example.test:5432/techie?sslmode=require';

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

function run(env) {
  const capture = captureOutput();
  const result = runTargetPreflight({ env, output: capture.output });
  return { result, messages: capture.messages.join('\n') };
}

const valid = run({
  DATABASE_URL: RUNTIME_URL,
  EXPECTED_DATABASE_HOST: 'DB.EXAMPLE.TEST',
  EXPECTED_DATABASE_PORT: '5432',
  EXPECTED_DATABASE_NAME: 'techie',
});
assert.strictEqual(valid.result.ok, true);
assert.match(valid.messages, /^DATABASE_TARGET_PREFLIGHT_PASS confirm_database_target_sha256=[0-9A-F]{64}$/);
assert.doesNotMatch(valid.messages, /protected-user|fixture-credential|db\.example\.test|techie/i);

const wrongHost = run({
  DATABASE_URL: RUNTIME_URL,
  EXPECTED_DATABASE_HOST: 'other.example.test',
  EXPECTED_DATABASE_NAME: 'techie',
});
assert.strictEqual(wrongHost.result.ok, false);
assert.match(wrongHost.messages, /DATABASE_TARGET_INDEPENDENT_SOURCE_MISMATCH/);

const wrongDatabase = run({
  DATABASE_URL: RUNTIME_URL,
  EXPECTED_DATABASE_HOST: 'db.example.test',
  EXPECTED_DATABASE_NAME: 'other',
});
assert.strictEqual(wrongDatabase.result.ok, false);
assert.match(wrongDatabase.messages, /DATABASE_TARGET_INDEPENDENT_SOURCE_MISMATCH/);

const missingIndependentSource = run({ DATABASE_URL: RUNTIME_URL });
assert.strictEqual(missingIndependentSource.result.ok, false);
assert.match(missingIndependentSource.messages, /EXPECTED_DATABASE_HOST_NOT_CONFIGURED/);

const invalidProtocol = run({
  DATABASE_URL: 'https://db.example.test/techie',
  EXPECTED_DATABASE_HOST: 'db.example.test',
  EXPECTED_DATABASE_NAME: 'techie',
});
assert.strictEqual(invalidProtocol.result.ok, false);
assert.match(invalidProtocol.messages, /DATABASE_URL_PROTOCOL_INVALID/);

const source = fs.readFileSync(
  path.join(__dirname, '20260804_identity_binding_hardening_target_preflight.js'),
  'utf8',
);
assert.doesNotMatch(source, /require\(['"](?:pg|https?|axios|node:https?|node:net|net)['"]\)/);
assert.doesNotMatch(source, /output\.(?:log|error)\([^\n]*(?:DATABASE_URL|EXPECTED_DATABASE_HOST|EXPECTED_DATABASE_NAME)/);

console.log('identity-binding-hardening-target-preflight-tests: 6 passed');
