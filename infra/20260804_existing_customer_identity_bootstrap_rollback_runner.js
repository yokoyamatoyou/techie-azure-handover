'use strict';

/**
 * Dispute-only rollback for verified existing-customer bootstrap bindings.
 *
 * It never deletes identity history. The exact batch manifest, original audit
 * details, target customer/Stripe hashes, and a separate rollback approval
 * receipt hash must all match. Default mode rolls the transaction back.
 */
const {
  BUSINESS_KEYS,
  LINK_METHOD,
  assertBaseState,
  lockAndVerifyTarget,
  lockTargetBusinessRows,
  readProtectedManifest,
  safeErrorCode,
  sha256,
  summariesEqual,
  summary,
  validateManifest,
} = require('./20260804_existing_customer_identity_bootstrap_runner');

const ROLLBACK_METHOD = 'verified_existing_customer_bootstrap_rollback';
const ROLLBACK_REASON = 'approved_existing_customer_bootstrap_rollback';
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const BOOTSTRAP_AUDIT_KEYS = [
  'batch_id',
  'operation_id',
  'change_approval_receipt_sha256',
  'identity_evidence_receipt_sha256',
  'identity_provider',
  'principal_created',
];
const ROLLBACK_AUDIT_KEYS = [
  'batch_id',
  'operation_id',
  'rollback_approval_receipt_sha256',
  'original_change_approval_receipt_sha256',
  'original_identity_evidence_receipt_sha256',
  'principal_disputed',
];

function assertCondition(condition, code) {
  if (!condition) {
    const error = new Error(code);
    error.code = code;
    throw error;
  }
}

function parseRollbackOptions(argv) {
  const options = argv.slice(2);
  let manifestPath = '';
  let rollbackApprovalHash = '';
  let apply = false;
  let confirmedManifestHash = '';
  let confirmedOperationCount = null;
  for (let index = 0; index < options.length; index += 1) {
    const option = options[index];
    if (option === '--manifest') {
      assertCondition(!manifestPath, 'DUPLICATE_MANIFEST_OPTION');
      assertCondition(index + 1 < options.length, 'MANIFEST_PATH_REQUIRED');
      manifestPath = String(options[index + 1] || '').trim();
      index += 1;
      continue;
    }
    if (option === '--rollback-approval-sha256') {
      assertCondition(!rollbackApprovalHash, 'DUPLICATE_ROLLBACK_APPROVAL');
      assertCondition(index + 1 < options.length, 'ROLLBACK_APPROVAL_REQUIRED');
      rollbackApprovalHash = String(options[index + 1] || '').trim().toLowerCase();
      index += 1;
      continue;
    }
    if (option === '--apply') {
      assertCondition(!apply, 'DUPLICATE_APPLY_OPTION');
      apply = true;
      continue;
    }
    if (option === '--confirm-manifest-sha256') {
      assertCondition(!confirmedManifestHash, 'DUPLICATE_MANIFEST_HASH_CONFIRMATION');
      assertCondition(index + 1 < options.length, 'MANIFEST_HASH_CONFIRMATION_REQUIRED');
      confirmedManifestHash = String(options[index + 1] || '').trim().toLowerCase();
      index += 1;
      continue;
    }
    if (option === '--confirm-operation-count') {
      assertCondition(confirmedOperationCount === null, 'DUPLICATE_OPERATION_COUNT_CONFIRMATION');
      assertCondition(index + 1 < options.length, 'OPERATION_COUNT_CONFIRMATION_REQUIRED');
      const rawCount = String(options[index + 1] || '').trim();
      assertCondition(/^[1-9][0-9]{0,2}$/.test(rawCount), 'OPERATION_COUNT_CONFIRMATION_INVALID');
      confirmedOperationCount = Number(rawCount);
      index += 1;
      continue;
    }
    assertCondition(false, 'UNKNOWN_ARGUMENT');
  }
  assertCondition(Boolean(manifestPath), 'MANIFEST_PATH_REQUIRED');
  assertCondition(SHA256_PATTERN.test(rollbackApprovalHash), 'ROLLBACK_APPROVAL_REQUIRED');
  assertCondition(apply || (!confirmedManifestHash && confirmedOperationCount === null), 'APPLY_CONFIRMATION_WITHOUT_APPLY');
  if (apply) {
    assertCondition(SHA256_PATTERN.test(confirmedManifestHash), 'MANIFEST_HASH_CONFIRMATION_INVALID');
    assertCondition(confirmedOperationCount !== null, 'OPERATION_COUNT_CONFIRMATION_REQUIRED');
  }
  return {
    manifestPath,
    rollbackApprovalHash,
    apply,
    confirmedManifestHash,
    confirmedOperationCount,
  };
}

function normalizeDetails(value) {
  if (value && typeof value === 'object' && !Array.isArray(value)) return value;
  try {
    return JSON.parse(String(value || ''));
  } catch (_) {
    assertCondition(false, 'BOOTSTRAP_AUDIT_DETAILS_INVALID');
  }
}

function assertExactDetailKeys(details, expectedKeys, code) {
  assertCondition(details && typeof details === 'object' && !Array.isArray(details), code);
  const actual = Object.keys(details).sort();
  const expected = [...expectedKeys].sort();
  assertCondition(actual.length === expected.length, code);
  assertCondition(actual.every((key, index) => key === expected[index]), code);
}

async function lockRollbackTarget(client, manifest, entry) {
  const result = await client.query(`
    /* techie-existing-rollback:target */
    SELECT
      eib.identity_binding_id::text AS identity_binding_id,
      eib.principal_id::text AS principal_id,
      eib.directory_tenant_id,
      eib.identity_provider,
      eib.status AS binding_status,
      eib.link_method,
      eib.end_reason,
      cp.tenant_id::text AS tenant_id,
      cp.status AS principal_status,
      ila.details AS bootstrap_audit_details
    FROM external_identity_binding eib
    JOIN canonical_principal cp ON cp.principal_id = eib.principal_id
    JOIN identity_link_audit_log ila
      ON ila.identity_binding_id = eib.identity_binding_id
     AND ila.action_type = $3
     AND ila.result_status = 'success'
    WHERE eib.token_issuer = $1
      AND eib.subject_type = 'oid'
      AND eib.subject_value = $2
    FOR UPDATE OF eib, cp, ila
  `, [entry.token_issuer, entry.subject_value, LINK_METHOD]);
  assertCondition(result.rows.length === 1, 'BOOTSTRAP_ROLLBACK_TARGET_NOT_UNIQUE');
  const target = result.rows[0];
  assertCondition(String(target.tenant_id).toLowerCase() === entry.business_tenant_id, 'BOOTSTRAP_ROLLBACK_TENANT_MISMATCH');
  assertCondition(String(target.directory_tenant_id || '').trim().toLowerCase() === entry.directory_tenant_id, 'BOOTSTRAP_ROLLBACK_DIRECTORY_MISMATCH');
  assertCondition(String(target.identity_provider || '').trim() === entry.identity_provider, 'BOOTSTRAP_ROLLBACK_PROVIDER_MISMATCH');
  assertCondition(String(target.link_method || '') === LINK_METHOD, 'BOOTSTRAP_ROLLBACK_LINK_METHOD_MISMATCH');
  const details = normalizeDetails(target.bootstrap_audit_details);
  assertExactDetailKeys(details, BOOTSTRAP_AUDIT_KEYS, 'BOOTSTRAP_AUDIT_DETAILS_SHAPE_INVALID');
  assertCondition(details.batch_id === manifest.batch_id, 'BOOTSTRAP_AUDIT_BATCH_MISMATCH');
  assertCondition(details.operation_id === entry.operation_id, 'BOOTSTRAP_AUDIT_OPERATION_MISMATCH');
  assertCondition(details.change_approval_receipt_sha256 === manifest.change_approval_receipt_sha256, 'BOOTSTRAP_AUDIT_APPROVAL_MISMATCH');
  assertCondition(details.identity_evidence_receipt_sha256 === entry.identity_evidence_receipt_sha256, 'BOOTSTRAP_AUDIT_EVIDENCE_MISMATCH');
  assertCondition(details.identity_provider === entry.identity_provider, 'BOOTSTRAP_AUDIT_PROVIDER_MISMATCH');
  assertCondition(typeof details.principal_created === 'boolean', 'BOOTSTRAP_AUDIT_PRINCIPAL_CREATED_MISSING');
  return { ...target, principal_created: details.principal_created };
}

async function findRollbackAudit(client, target, manifest, entry, rollbackApprovalHash) {
  const result = await client.query(`
    /* techie-existing-rollback:audit */
    SELECT details
    FROM identity_link_audit_log
    WHERE identity_binding_id = $1::uuid
      AND action_type = $2
      AND result_status = 'success'
  `, [target.identity_binding_id, ROLLBACK_METHOD]);
  const matches = result.rows.map((row) => {
    const details = normalizeDetails(row.details);
    assertExactDetailKeys(details, ROLLBACK_AUDIT_KEYS, 'ROLLBACK_AUDIT_DETAILS_SHAPE_INVALID');
    return details;
  }).filter((details) => (
    details.batch_id === manifest.batch_id
      && details.operation_id === entry.operation_id
      && details.rollback_approval_receipt_sha256 === rollbackApprovalHash
      && details.original_change_approval_receipt_sha256 === manifest.change_approval_receipt_sha256
      && details.original_identity_evidence_receipt_sha256 === entry.identity_evidence_receipt_sha256
      && typeof details.principal_disputed === 'boolean'
  ));
  assertCondition(matches.length <= 1, 'ROLLBACK_AUDIT_NOT_UNIQUE');
  return matches.length === 1 ? matches[0] : null;
}

async function countOtherActiveBindings(client, target) {
  const result = await client.query(`
    /* techie-existing-rollback:other-bindings */
    SELECT count(*)::int AS count
    FROM external_identity_binding
    WHERE principal_id = $1::uuid
      AND identity_binding_id <> $2::uuid
      AND status = 'active'
  `, [target.principal_id, target.identity_binding_id]);
  return Number(result.rows[0].count);
}

async function lockAndRejectPendingLinkIntents(client, target) {
  const result = await client.query(`
    /* techie-existing-rollback:link-intents */
    SELECT identity_link_intent_id::text AS identity_link_intent_id, status
    FROM identity_link_intent
    WHERE principal_id = $1::uuid
       OR source_identity_binding_id = $2::uuid
       OR completed_identity_binding_id = $2::uuid
    FOR UPDATE
  `, [target.principal_id, target.identity_binding_id]);
  assertCondition(
    result.rows.every((row) => String(row.status || '') !== 'pending'),
    'BOOTSTRAP_ROLLBACK_PENDING_LINK_INTENT',
  );
}

async function applyDispute(client, manifest, entry, target, rollbackApprovalHash) {
  if (target.binding_status === 'disputed' && target.end_reason === ROLLBACK_REASON) {
    const rollbackAudit = await findRollbackAudit(client, target, manifest, entry, rollbackApprovalHash);
    assertCondition(Boolean(rollbackAudit), 'ROLLBACK_IDEMPOTENCY_AUDIT_MISSING');
    assertCondition(
      target.principal_status === 'active' || target.principal_status === 'disputed',
      'ROLLBACK_IDEMPOTENCY_PRINCIPAL_STATE_INVALID',
    );
    if (rollbackAudit.principal_disputed) {
      assertCondition(target.principal_status === 'disputed', 'ROLLBACK_IDEMPOTENCY_PRINCIPAL_NOT_DISPUTED');
    }
    return { bindingDisputed: 0, principalDisputed: 0, auditInserted: 0, idempotent: 1 };
  }
  assertCondition(target.binding_status === 'active', 'BOOTSTRAP_ROLLBACK_BINDING_NOT_ACTIVE');
  assertCondition(target.principal_status === 'active', 'BOOTSTRAP_ROLLBACK_PRINCIPAL_NOT_ACTIVE');

  const update = await client.query(`
    /* techie-existing-rollback:dispute-binding */
    UPDATE external_identity_binding
    SET status = 'disputed',
        ended_at = now(),
        end_reason = $2,
        updated_at = now()
    WHERE identity_binding_id = $1::uuid
      AND status = 'active'
  `, [target.identity_binding_id, ROLLBACK_REASON]);
  assertCondition(Number(update.rowCount) === 1, 'ROLLBACK_BINDING_UPDATE_COUNT_MISMATCH');

  const otherActiveBindings = await countOtherActiveBindings(client, target);
  let principalDisputed = 0;
  if (target.principal_created && otherActiveBindings === 0) {
    const principalUpdate = await client.query(`
      /* techie-existing-rollback:dispute-principal */
      UPDATE canonical_principal
      SET status = 'disputed', updated_at = now()
      WHERE principal_id = $1::uuid
        AND status = 'active'
    `, [target.principal_id]);
    assertCondition(Number(principalUpdate.rowCount) === 1, 'ROLLBACK_PRINCIPAL_UPDATE_COUNT_MISMATCH');
    principalDisputed = 1;
  }

  const details = JSON.stringify({
    batch_id: manifest.batch_id,
    operation_id: entry.operation_id,
    rollback_approval_receipt_sha256: rollbackApprovalHash,
    original_change_approval_receipt_sha256: manifest.change_approval_receipt_sha256,
    original_identity_evidence_receipt_sha256: entry.identity_evidence_receipt_sha256,
    principal_disputed: principalDisputed === 1,
  });
  const auditInsert = await client.query(`
    /* techie-existing-rollback:insert-audit */
    INSERT INTO identity_link_audit_log (
      principal_id, identity_binding_id, action_type, result_status,
      details, created_at
    ) VALUES ($1::uuid, $2::uuid, $3, 'success', $4::jsonb, now())
  `, [target.principal_id, target.identity_binding_id, ROLLBACK_METHOD, details]);
  assertCondition(Number(auditInsert.rowCount) === 1, 'ROLLBACK_AUDIT_INSERT_COUNT_MISMATCH');
  return { bindingDisputed: 1, principalDisputed, auditInserted: 1, idempotent: 0 };
}

function assertRollbackDelta(before, after, changes) {
  assertCondition(BUSINESS_KEYS.every((key) => Number(before[key]) === Number(after[key])), 'ROLLBACK_BUSINESS_OR_STRIPE_INVARIANT_CHANGED');
  assertCondition(Number(after.canonical_principals) === Number(before.canonical_principals), 'ROLLBACK_CANONICAL_PRINCIPAL_COUNT_CHANGED');
  assertCondition(Number(after.identity_bindings) === Number(before.identity_bindings), 'ROLLBACK_IDENTITY_BINDING_COUNT_CHANGED');
  assertCondition(Number(after.link_intents) === Number(before.link_intents), 'ROLLBACK_LINK_INTENT_CHANGED');
  assertCondition(Number(after.identity_audits) === Number(before.identity_audits) + changes.auditInserted, 'ROLLBACK_AUDIT_DELTA_MISMATCH');
  assertCondition(Number(after.active_bindings) === Number(before.active_bindings) - changes.bindingDisputed, 'ROLLBACK_ACTIVE_BINDING_DELTA_MISMATCH');
  assertCondition(Number(after.disputed_bindings) === Number(before.disputed_bindings) + changes.bindingDisputed, 'ROLLBACK_DISPUTED_BINDING_DELTA_MISMATCH');
  assertCondition(Number(after.active_principals) === Number(before.active_principals) - changes.principalDisputed, 'ROLLBACK_ACTIVE_PRINCIPAL_DELTA_MISMATCH');
  assertCondition(Number(after.disputed_principals) === Number(before.disputed_principals) + changes.principalDisputed, 'ROLLBACK_DISPUTED_PRINCIPAL_DELTA_MISMATCH');
  assertBaseState(after);
}

async function executeRollback(client, manifest, rollbackApprovalHash) {
  const changes = {
    bindingDisputed: 0,
    principalDisputed: 0,
    auditInserted: 0,
    idempotent: 0,
  };
  for (const entry of manifest.entries) {
    await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [`${entry.token_issuer}|oid|${entry.subject_value}`]);
    await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [`business-tenant|${entry.business_tenant_id}`]);
    const customerAccountId = await lockAndVerifyTarget(client, entry);
    await lockTargetBusinessRows(client, customerAccountId, entry.business_tenant_id);
    const target = await lockRollbackTarget(client, manifest, entry);
    await lockAndRejectPendingLinkIntents(client, target);
    const result = await applyDispute(client, manifest, entry, target, rollbackApprovalHash);
    for (const key of Object.keys(changes)) changes[key] += result[key];
  }
  return changes;
}

async function runRollback({
  ClientClass,
  argv = process.argv,
  env = process.env,
  manifestBytes,
  output = console,
} = {}) {
  assertCondition(typeof ClientClass === 'function', 'PG_CLIENT_NOT_CONFIGURED');
  const options = parseRollbackOptions(argv);
  const bytes = manifestBytes === undefined ? readProtectedManifest(options.manifestPath) : Buffer.from(manifestBytes);
  assertCondition(bytes.length > 0 && bytes.length <= 1024 * 1024, 'MANIFEST_SIZE_INVALID');
  const manifestHash = sha256(bytes);
  let rawManifest;
  try {
    rawManifest = JSON.parse(bytes.toString('utf8'));
  } catch (_) {
    assertCondition(false, 'MANIFEST_JSON_INVALID');
  }
  const manifest = validateManifest(rawManifest, env);
  assertCondition(
    options.rollbackApprovalHash !== manifestHash
      && options.rollbackApprovalHash !== manifest.change_approval_receipt_sha256
      && manifest.entries.every(
        (entry) => options.rollbackApprovalHash !== entry.identity_evidence_receipt_sha256,
      ),
    'ROLLBACK_APPROVAL_NOT_SEPARATE',
  );
  if (options.apply) {
    assertCondition(options.confirmedManifestHash === manifestHash, 'APPLY_MANIFEST_HASH_CONFIRMATION_REQUIRED');
    assertCondition(options.confirmedOperationCount === manifest.entries.length, 'APPLY_OPERATION_COUNT_CONFIRMATION_MISMATCH');
  }
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
    await client.query('BEGIN ISOLATION LEVEL SERIALIZABLE');
    inTransaction = true;
    await client.query("SET LOCAL search_path = public, pg_catalog");
    await client.query("SET LOCAL lock_timeout = '5s'");
    await client.query("SET LOCAL statement_timeout = '120s'");
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('techie-existing-customer-bootstrap-rollback-v1', 0))");
    const before = await summary(client);
    assertBaseState(before);
    const changes = await executeRollback(client, manifest, options.rollbackApprovalHash);
    const inside = await summary(client);
    assertRollbackDelta(before, inside, changes);

    if (!options.apply) {
      await client.query('ROLLBACK');
      inTransaction = false;
      const afterRollback = await summary(client);
      assertCondition(summariesEqual(before, afterRollback), 'ROLLBACK_DRY_RUN_STATE_CHANGED');
      output.log(`EXISTING_CUSTOMER_BOOTSTRAP_ROLLBACK_DRY_RUN_PASS operations=${manifest.entries.length} disputed=${changes.bindingDisputed} idempotent=${changes.idempotent} business_invariants_unchanged=true manifest_sha256=${manifestHash}`);
      return { ok: true, mode: 'dry-run', committed: false, manifestHash };
    }

    await client.query('COMMIT');
    inTransaction = false;
    committed = true;
    const afterCommit = await summary(client);
    assertRollbackDelta(before, afterCommit, changes);
    output.log(`EXISTING_CUSTOMER_BOOTSTRAP_ROLLBACK_APPLY_PASS operations=${manifest.entries.length} disputed=${changes.bindingDisputed} idempotent=${changes.idempotent} business_invariants_unchanged=true manifest_sha256=${manifestHash}`);
    return { ok: true, mode: 'apply', committed: true, manifestHash };
  } catch (error) {
    if (connected && inTransaction) {
      try {
        await client.query('ROLLBACK');
      } catch (_) {
        // Preserve the original safe error code.
      }
    }
    output.error(`EXISTING_CUSTOMER_BOOTSTRAP_ROLLBACK_${options.apply ? 'APPLY' : 'DRY_RUN'}_ERROR ${safeErrorCode(error)} commit_state=${committed ? 'committed' : 'not_committed'}`);
    return { ok: false, mode: options.apply ? 'apply' : 'dry-run', committed, manifestHash };
  } finally {
    if (connected) await client.end().catch(() => {});
  }
}

async function cliMain() {
  const { Client } = require('pg');
  const result = await runRollback({ ClientClass: Client });
  if (!result.ok) process.exitCode = 1;
}

if (require.main === module) {
  cliMain().catch((error) => {
    console.error(`EXISTING_CUSTOMER_BOOTSTRAP_ROLLBACK_RUNNER_ERROR ${safeErrorCode(error)} commit_state=not_committed`);
    process.exitCode = 1;
  });
}

module.exports = {
  ROLLBACK_METHOD,
  ROLLBACK_REASON,
  parseRollbackOptions,
  runRollback,
};
