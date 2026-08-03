'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const infraDir = __dirname;
const jobDir = path.join(infraDir, 'identity-shadow-job');

function read(name) {
  return fs.readFileSync(path.join(jobDir, name), 'utf8');
}

const dockerfile = read('Dockerfile');
const packageJson = JSON.parse(read('package.json'));
const foundation = read('foundation.bicep');
const job = read('job.bicep');
const runbook = read('README.md');

assert.strictEqual(packageJson.private, true);
assert.match(packageJson.dependencies.pg, /^\d+\.\d+\.\d+$/);
assert.match(dockerfile, /^ARG NODE_BASE_IMAGE_REPOSITORY\r?\nARG NODE_BASE_IMAGE_DIGEST\r?\nFROM \$\{NODE_BASE_IMAGE_REPOSITORY\}@\$\{NODE_BASE_IMAGE_DIGEST\}/m);
assert.doesNotMatch(dockerfile, /^FROM\s+[^$]/m);
assert.match(dockerfile, /USER node/);
assert.match(dockerfile, /--expect-empty/);

assert.match(foundation, /scope: registry/);
assert.match(foundation, /scope: databaseSecret/);
assert.doesNotMatch(foundation, /scope: vault/);
assert.match(foundation, /Microsoft\.KeyVault\/vaults\/secrets@2023-07-01/);
assert.match(foundation, /7f951dda-4ed3-4680-a7ca-43fe172d538d/);
assert.match(foundation, /4633458b-17de-408a-b874-0445c86b69e6/);
assert.doesNotMatch(foundation, /@secure\(\)\s*\r?\nparam\s+\w*(secret|password|connection)/i);

assert.match(job, /Microsoft\.App\/jobs@2025-07-01/);
assert.match(job, /triggerType: 'Manual'/);
assert.match(job, /replicaRetryLimit: 0/);
assert.match(job, /replicaTimeout: 300/);
assert.match(job, /parallelism: 1/);
assert.match(job, /replicaCompletionCount: 1/);
assert.match(job, /@minLength\(71\)[\s\S]*?@maxLength\(71\)[\s\S]*?param imageDigest string/);
assert.match(job, /@secure\(\)[\s\S]*?param databaseSecretVersion string/);
assert.match(job, /keyVaultUrl: databaseSecretUrl/);
assert.match(job, /identity: shadowIdentity\.id/g);
assert.match(job, /@\$\{imageDigest\}/);
assert.match(job, /AUTH_IDENTITY_RESOLVER_MODE'[\s\S]*?value: 'shadow'/);
assert.match(job, /AUTH_IDENTITY_AUTO_PROVISION'[\s\S]*?value: '0'/);
assert.match(job, /AUTH_TRUST_ENTRA_BINDING_CLAIMS'[\s\S]*?value: '0'/);
assert.doesNotMatch(job, /ingress\s*:/);
assert.doesNotMatch(job, /stripe/i);
assert.doesNotMatch(job, /clientSecret|passwordSecretRef|secretValue/i);

assert.match(runbook, /LOCAL PREPARATION ONLY \/ NOT DEPLOYED \/ NOT STARTED/);
assert.match(runbook, /Bicep CLI v0\.45\.15/);
assert.match(runbook, /separate approval/i);
assert.match(runbook, /never deploy by tag/i);
assert.match(runbook, /External ID[\s\S]*not the deployment directory/i);
assert.match(runbook, /individual existing[\s\S]*database-url[\s\S]*not on the entire Key Vault/i);

console.log('identity-shadow-job-contract-tests: 1 passed');
