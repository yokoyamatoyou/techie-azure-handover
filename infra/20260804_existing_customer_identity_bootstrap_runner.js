'use strict';

/**
 * Guarded existing-customer identity bootstrap runner.
 *
 * The runtime manifest is protected operator input and must never be added to
 * Git or chat. It contains immutable Entra coordinates but no email address,
 * customer-account ID, Stripe ID, token, or secret. Existing account and
 * Stripe anchors are confirmed only through SHA-256 digests.
 *
 * Default: SERIALIZABLE transaction followed by rollback.
 * Apply:   --apply --confirm-manifest-sha256 <sha256>
 *          --confirm-operation-count <count>
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const SCHEMA_VERSION = 'techie-existing-customer-identity-bootstrap-v1';
const LINK_METHOD = 'verified_existing_customer_bootstrap';
const ALLOWED_PROVIDERS = new Set(['email', 'google', 'microsoft']);
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;
const TOP_LEVEL_KEYS = [
  'schema_version',
  'batch_id',
  'change_approval_receipt_sha256',
  'expected_operation_count',
  'entries',
];
const ENTRY_KEYS = [
  'operation_id',
  'business_tenant_id',
  'expected_customer_account_id_sha256',
  'expected_stripe_customer_id_sha256',
  'directory_tenant_id',
  'token_issuer',
  'subject_type',
  'subject_value',
  'entra_object_id',
  'identity_provider',
  'identity_evidence_receipt_sha256',
];
const BUSINESS_KEYS = [
  'tenants',
  'customer_accounts',
  'stripe_links',
  'subscription_contracts',
  'billing_events',
  'payment_receipts',
  'reseller_payouts',
  'reseller_payout_executions',
  'refund_adjustments',
  'usage_accounts',
  'usage_events',
  'duplicate_tenant_accounts',
  'duplicate_stripe_links',
];
const SUMMARY_KEYS = [
  ...BUSINESS_KEYS,
  'identity_tables',
  'canonical_principals',
  'active_principals',
  'disputed_principals',
  'identity_bindings',
  'active_bindings',
  'disputed_bindings',
  'link_intents',
  'identity_audits',
  'hardening_constraints',
  'validated_hardening_constraints',
  'unsafe_binding_defaults',
  'ambiguous_active_principal_tenants',
  'orphan_bindings',
  'orphan_principals',
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

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function resolveProtectedManifestPath(manifestPath, {
  sourceRoot = path.resolve(__dirname, '..'),
  realpathSync = fs.realpathSync,
  statSync = fs.statSync,
  platform = process.platform,
} = {}) {
  const resolvedSourceRoot = realpathSync(path.resolve(sourceRoot));
  const resolvedManifest = realpathSync(path.resolve(manifestPath));
  const relative = path.relative(resolvedSourceRoot, resolvedManifest);
  const insideSource = relative === ''
    || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
  assertCondition(!insideSource, 'PROTECTED_MANIFEST_INSIDE_SOURCE_TREE');
  const stats = statSync(resolvedManifest);
  assertCondition(stats.isFile(), 'PROTECTED_MANIFEST_NOT_REGULAR_FILE');
  if (platform !== 'win32') {
    assertCondition((Number(stats.mode) & 0o077) === 0, 'PROTECTED_MANIFEST_PERMISSIONS_NOT_PRIVATE');
  }
  return resolvedManifest;
}

function readProtectedManifest(manifestPath, dependencies) {
  return fs.readFileSync(resolveProtectedManifestPath(manifestPath, dependencies));
}

function normalizeUuid(value, code) {
  const normalized = String(value || '').trim().toLowerCase();
  assertCondition(UUID_PATTERN.test(normalized), code);
  return normalized;
}

function normalizeIssuer(value, code) {
  const normalized = String(value || '').trim().replace(/\/+$/, '').toLowerCase();
  let parsed;
  try {
    parsed = new URL(normalized);
  } catch (_) {
    assertCondition(false, code);
  }
  assertCondition(parsed.protocol === 'https:' && !parsed.username && !parsed.password, code);
  assertCondition(!parsed.search && !parsed.hash, code);
  return normalized;
}

function assertExactKeys(value, expectedKeys, code) {
  assertCondition(value && typeof value === 'object' && !Array.isArray(value), code);
  const actual = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  assertCondition(actual.length === expected.length, code);
  assertCondition(actual.every((key, index) => key === expected[index]), code);
}

function parseOptions(argv) {
  const options = argv.slice(2);
  let manifestPath = '';
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
  assertCondition(apply || (!confirmedManifestHash && confirmedOperationCount === null), 'APPLY_CONFIRMATION_WITHOUT_APPLY');
  if (apply) {
    assertCondition(SHA256_PATTERN.test(confirmedManifestHash), 'MANIFEST_HASH_CONFIRMATION_INVALID');
    assertCondition(confirmedOperationCount !== null, 'OPERATION_COUNT_CONFIRMATION_REQUIRED');
  }
  return { manifestPath, apply, confirmedManifestHash, confirmedOperationCount };
}

function validateManifest(rawManifest, env) {
  assertExactKeys(rawManifest, TOP_LEVEL_KEYS, 'MANIFEST_TOP_LEVEL_SHAPE_INVALID');
  assertCondition(rawManifest.schema_version === SCHEMA_VERSION, 'MANIFEST_SCHEMA_VERSION_INVALID');
  const batchId = normalizeUuid(rawManifest.batch_id, 'MANIFEST_BATCH_ID_INVALID');
  const approvalReceiptHash = String(rawManifest.change_approval_receipt_sha256 || '').trim();
  assertCondition(SHA256_PATTERN.test(approvalReceiptHash), 'MANIFEST_CHANGE_APPROVAL_HASH_INVALID');
  assertCondition(Number.isInteger(rawManifest.expected_operation_count), 'MANIFEST_EXPECTED_COUNT_INVALID');
  assertCondition(
    rawManifest.expected_operation_count >= 1 && rawManifest.expected_operation_count <= 100,
    'MANIFEST_EXPECTED_COUNT_INVALID',
  );
  assertCondition(Array.isArray(rawManifest.entries), 'MANIFEST_ENTRIES_INVALID');
  assertCondition(rawManifest.entries.length === rawManifest.expected_operation_count, 'MANIFEST_ENTRY_COUNT_MISMATCH');

  const expectedDirectory = normalizeUuid(env.EXPECTED_EXTERNAL_DIRECTORY_ID, 'EXPECTED_EXTERNAL_DIRECTORY_ID_INVALID');
  const expectedIssuer = normalizeIssuer(env.EXPECTED_EXTERNAL_ISSUER, 'EXPECTED_EXTERNAL_ISSUER_INVALID');
  const operationIds = new Set();
  const tenantIds = new Set();
  const coordinates = new Set();
  const entries = rawManifest.entries.map((entry) => {
    assertExactKeys(entry, ENTRY_KEYS, 'MANIFEST_ENTRY_SHAPE_INVALID');
    const normalized = {
      operation_id: normalizeUuid(entry.operation_id, 'MANIFEST_OPERATION_ID_INVALID'),
      business_tenant_id: normalizeUuid(entry.business_tenant_id, 'MANIFEST_BUSINESS_TENANT_ID_INVALID'),
      expected_customer_account_id_sha256: String(entry.expected_customer_account_id_sha256 || '').trim(),
      expected_stripe_customer_id_sha256: String(entry.expected_stripe_customer_id_sha256 || '').trim(),
      directory_tenant_id: normalizeUuid(entry.directory_tenant_id, 'MANIFEST_DIRECTORY_TENANT_ID_INVALID'),
      token_issuer: normalizeIssuer(entry.token_issuer, 'MANIFEST_TOKEN_ISSUER_INVALID'),
      subject_type: String(entry.subject_type || '').trim(),
      subject_value: normalizeUuid(entry.subject_value, 'MANIFEST_SUBJECT_VALUE_INVALID'),
      entra_object_id: normalizeUuid(entry.entra_object_id, 'MANIFEST_ENTRA_OBJECT_ID_INVALID'),
      identity_provider: String(entry.identity_provider || '').trim(),
      identity_evidence_receipt_sha256: String(entry.identity_evidence_receipt_sha256 || '').trim(),
    };
    assertCondition(SHA256_PATTERN.test(normalized.expected_customer_account_id_sha256), 'MANIFEST_CUSTOMER_ACCOUNT_HASH_INVALID');
    assertCondition(SHA256_PATTERN.test(normalized.expected_stripe_customer_id_sha256), 'MANIFEST_STRIPE_CUSTOMER_HASH_INVALID');
    assertCondition(SHA256_PATTERN.test(normalized.identity_evidence_receipt_sha256), 'MANIFEST_IDENTITY_EVIDENCE_HASH_INVALID');
    assertCondition(normalized.directory_tenant_id === expectedDirectory, 'MANIFEST_DIRECTORY_MISMATCH');
    assertCondition(normalized.token_issuer === expectedIssuer, 'MANIFEST_ISSUER_MISMATCH');
    assertCondition(normalized.subject_type === 'oid', 'MANIFEST_SUBJECT_TYPE_NOT_ALLOWED');
    assertCondition(normalized.subject_value === normalized.entra_object_id, 'MANIFEST_OID_COORDINATE_MISMATCH');
    assertCondition(ALLOWED_PROVIDERS.has(normalized.identity_provider), 'MANIFEST_IDENTITY_PROVIDER_INVALID');
    const coordinate = `${normalized.token_issuer}|oid|${normalized.subject_value}`;
    assertCondition(!operationIds.has(normalized.operation_id), 'MANIFEST_DUPLICATE_OPERATION_ID');
    assertCondition(!tenantIds.has(normalized.business_tenant_id), 'MANIFEST_DUPLICATE_BUSINESS_TENANT');
    assertCondition(!coordinates.has(coordinate), 'MANIFEST_DUPLICATE_IDENTITY_COORDINATE');
    operationIds.add(normalized.operation_id);
    tenantIds.add(normalized.business_tenant_id);
    coordinates.add(coordinate);
    return normalized;
  });
  return {
    schema_version: SCHEMA_VERSION,
    batch_id: batchId,
    change_approval_receipt_sha256: approvalReceiptHash,
    entries,
  };
}

async function summary(client) {
  const result = await client.query(`
    /* techie-existing-bootstrap:summary */
    SELECT
      (SELECT count(*)::int FROM tenants) AS tenants,
      (SELECT count(*)::int FROM customer_account) AS customer_accounts,
      (SELECT count(*)::int FROM customer_account WHERE stripe_customer_id IS NOT NULL AND btrim(stripe_customer_id) <> '') AS stripe_links,
      (SELECT count(*)::int FROM subscription_contract) AS subscription_contracts,
      (SELECT count(*)::int FROM billing_event_ledger) AS billing_events,
      (SELECT count(*)::int FROM payment_receipt_ledger) AS payment_receipts,
      (SELECT count(*)::int FROM reseller_payout_ledger) AS reseller_payouts,
      (SELECT count(*)::int FROM reseller_payout_execution) AS reseller_payout_executions,
      (SELECT count(*)::int FROM refund_adjustment_ledger) AS refund_adjustments,
      (SELECT count(*)::int FROM service_usage_account) AS usage_accounts,
      (SELECT count(*)::int FROM usage_event_ledger) AS usage_events,
      (SELECT count(*)::int FROM (SELECT tenant_id FROM customer_account GROUP BY tenant_id HAVING count(*) > 1) d) AS duplicate_tenant_accounts,
      (SELECT count(*)::int FROM (SELECT stripe_customer_id FROM customer_account WHERE stripe_customer_id IS NOT NULL AND btrim(stripe_customer_id) <> '' GROUP BY stripe_customer_id HAVING count(*) > 1) d) AS duplicate_stripe_links,
      (SELECT count(*)::int FROM information_schema.tables WHERE table_schema = 'public' AND table_name = ANY(ARRAY['canonical_principal','external_identity_binding','identity_link_intent','identity_link_audit_log'])) AS identity_tables,
      (SELECT count(*)::int FROM canonical_principal) AS canonical_principals,
      (SELECT count(*)::int FROM canonical_principal WHERE status = 'active') AS active_principals,
      (SELECT count(*)::int FROM canonical_principal WHERE status = 'disputed') AS disputed_principals,
      (SELECT count(*)::int FROM external_identity_binding) AS identity_bindings,
      (SELECT count(*)::int FROM external_identity_binding WHERE status = 'active') AS active_bindings,
      (SELECT count(*)::int FROM external_identity_binding WHERE status = 'disputed') AS disputed_bindings,
      (SELECT count(*)::int FROM identity_link_intent) AS link_intents,
      (SELECT count(*)::int FROM identity_link_audit_log) AS identity_audits,
      (SELECT count(*)::int FROM pg_constraint WHERE conrelid = to_regclass('public.external_identity_binding') AND conname = ANY(ARRAY['chk_external_identity_binding_directory_tenant_id','chk_external_identity_binding_identity_provider'])) AS hardening_constraints,
      (SELECT count(*)::int FROM pg_constraint WHERE conrelid = to_regclass('public.external_identity_binding') AND conname = ANY(ARRAY['chk_external_identity_binding_directory_tenant_id','chk_external_identity_binding_identity_provider']) AND convalidated) AS validated_hardening_constraints,
      (SELECT count(*)::int FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'external_identity_binding' AND column_name = ANY(ARRAY['directory_tenant_id','identity_provider']) AND column_default IS NOT NULL) AS unsafe_binding_defaults,
      (SELECT count(*)::int FROM (SELECT tenant_id FROM canonical_principal WHERE status = 'active' GROUP BY tenant_id HAVING count(*) > 1) d) AS ambiguous_active_principal_tenants,
      (SELECT count(*)::int FROM external_identity_binding eib LEFT JOIN canonical_principal cp ON cp.principal_id = eib.principal_id WHERE cp.principal_id IS NULL) AS orphan_bindings,
      (SELECT count(*)::int FROM canonical_principal cp LEFT JOIN tenants t ON t.tenant_id = cp.tenant_id WHERE t.tenant_id IS NULL) AS orphan_principals
  `);
  return result.rows[0];
}

function summariesEqual(left, right, keys = SUMMARY_KEYS) {
  return keys.every((key) => Number(left[key]) === Number(right[key]));
}

function assertBaseState(state) {
  assertCondition(Number(state.identity_tables) === 4, 'IDENTITY_SCHEMA_TABLE_COUNT_MISMATCH');
  assertCondition(Number(state.hardening_constraints) === 2, 'IDENTITY_BINDING_HARDENING_REQUIRED');
  assertCondition(Number(state.validated_hardening_constraints) === 2, 'IDENTITY_BINDING_HARDENING_NOT_VALIDATED');
  assertCondition(Number(state.unsafe_binding_defaults) === 0, 'IDENTITY_BINDING_UNSAFE_DEFAULT_REMAINS');
  assertCondition(Number(state.duplicate_tenant_accounts) === 0, 'DUPLICATE_TENANT_ACCOUNT_PRECHECK');
  assertCondition(Number(state.duplicate_stripe_links) === 0, 'DUPLICATE_STRIPE_LINK_PRECHECK');
  assertCondition(Number(state.ambiguous_active_principal_tenants) === 0, 'AMBIGUOUS_ACTIVE_PRINCIPAL_PRECHECK');
  assertCondition(Number(state.orphan_bindings) === 0, 'ORPHAN_BINDING_PRECHECK');
  assertCondition(Number(state.orphan_principals) === 0, 'ORPHAN_PRINCIPAL_PRECHECK');
}

function assertExpectedIdentityDelta(before, after, inserts) {
  assertCondition(BUSINESS_KEYS.every((key) => Number(before[key]) === Number(after[key])), 'BUSINESS_OR_STRIPE_INVARIANT_CHANGED');
  assertCondition(Number(after.canonical_principals) === Number(before.canonical_principals) + inserts.principals, 'CANONICAL_PRINCIPAL_DELTA_MISMATCH');
  assertCondition(Number(after.active_principals) === Number(before.active_principals) + inserts.principals, 'ACTIVE_PRINCIPAL_DELTA_MISMATCH');
  assertCondition(Number(after.disputed_principals) === Number(before.disputed_principals), 'DISPUTED_PRINCIPAL_CHANGED');
  assertCondition(Number(after.identity_bindings) === Number(before.identity_bindings) + inserts.bindings, 'IDENTITY_BINDING_DELTA_MISMATCH');
  assertCondition(Number(after.active_bindings) === Number(before.active_bindings) + inserts.bindings, 'ACTIVE_BINDING_DELTA_MISMATCH');
  assertCondition(Number(after.disputed_bindings) === Number(before.disputed_bindings), 'DISPUTED_BINDING_CHANGED');
  assertCondition(Number(after.identity_audits) === Number(before.identity_audits) + inserts.audits, 'IDENTITY_AUDIT_DELTA_MISMATCH');
  assertCondition(Number(after.link_intents) === Number(before.link_intents), 'IDENTITY_LINK_INTENT_CHANGED');
  assertBaseState(after);
}

async function lockAndVerifyTarget(client, entry) {
  const result = await client.query(`
    /* techie-existing-bootstrap:target */
    SELECT
      t.tenant_id::text AS tenant_id,
      ca.customer_account_id::text AS customer_account_id,
      ca.stripe_customer_id
    FROM tenants t
    JOIN customer_account ca ON ca.tenant_id = t.tenant_id
    WHERE t.tenant_id = $1::uuid
    FOR SHARE OF t, ca
  `, [entry.business_tenant_id]);
  assertCondition(result.rows.length === 1, 'TARGET_BUSINESS_ACCOUNT_NOT_UNIQUE');
  const target = result.rows[0];
  assertCondition(sha256(String(target.customer_account_id || '').trim().toLowerCase()) === entry.expected_customer_account_id_sha256, 'TARGET_CUSTOMER_ACCOUNT_HASH_MISMATCH');
  const stripeCustomerId = String(target.stripe_customer_id || '').trim();
  assertCondition(Boolean(stripeCustomerId), 'TARGET_STRIPE_CUSTOMER_MISSING');
  assertCondition(sha256(stripeCustomerId) === entry.expected_stripe_customer_id_sha256, 'TARGET_STRIPE_CUSTOMER_HASH_MISMATCH');
  return String(target.customer_account_id);
}

async function lockTargetBusinessRows(client, customerAccountId, tenantId) {
  const lockQueries = [
    [`/* techie-existing-bootstrap:lock-contracts */ SELECT subscription_contract_id FROM subscription_contract WHERE customer_account_id = $1::uuid FOR SHARE`, [customerAccountId]],
    [`/* techie-existing-bootstrap:lock-billing-events */ SELECT billing_event_ledger_id FROM billing_event_ledger WHERE customer_account_id = $1::uuid FOR SHARE`, [customerAccountId]],
    [`/* techie-existing-bootstrap:lock-payment-receipts */ SELECT payment_receipt_ledger_id FROM payment_receipt_ledger WHERE customer_account_id = $1::uuid FOR SHARE`, [customerAccountId]],
    [`/* techie-existing-bootstrap:lock-reseller-payouts */ SELECT rpl.reseller_payout_ledger_id FROM reseller_payout_ledger rpl JOIN billing_event_ledger bel ON bel.billing_event_ledger_id = rpl.billing_event_ledger_id WHERE bel.customer_account_id = $1::uuid FOR SHARE OF rpl`, [customerAccountId]],
    [`/* techie-existing-bootstrap:lock-reseller-payout-executions */ SELECT rpe.reseller_payout_execution_id FROM reseller_payout_execution rpe JOIN reseller_payout_ledger rpl ON rpl.reseller_payout_ledger_id = rpe.reseller_payout_ledger_id JOIN billing_event_ledger bel ON bel.billing_event_ledger_id = rpl.billing_event_ledger_id WHERE bel.customer_account_id = $1::uuid FOR SHARE OF rpe`, [customerAccountId]],
    [`/* techie-existing-bootstrap:lock-refunds */ SELECT ral.refund_adjustment_ledger_id FROM refund_adjustment_ledger ral LEFT JOIN billing_event_ledger bel ON bel.billing_event_ledger_id = ral.billing_event_ledger_id WHERE ral.customer_account_id = $1::uuid OR bel.customer_account_id = $1::uuid FOR SHARE OF ral`, [customerAccountId]],
    [`/* techie-existing-bootstrap:lock-usage-accounts */ SELECT usage_account_id FROM service_usage_account WHERE tenant_id = $1::uuid FOR SHARE`, [tenantId]],
    [`/* techie-existing-bootstrap:lock-usage-events */ SELECT usage_event_id FROM usage_event_ledger WHERE tenant_id = $1::uuid FOR SHARE`, [tenantId]],
  ];
  for (const [query, params] of lockQueries) {
    await client.query(query, params);
  }
}

async function findBindingForUpdate(client, entry) {
  const result = await client.query(`
    /* techie-existing-bootstrap:binding */
    SELECT
      eib.identity_binding_id::text AS identity_binding_id,
      eib.principal_id::text AS principal_id,
      eib.directory_tenant_id,
      eib.identity_provider,
      eib.status AS binding_status,
      cp.tenant_id::text AS tenant_id,
      cp.status AS principal_status
    FROM external_identity_binding eib
    JOIN canonical_principal cp ON cp.principal_id = eib.principal_id
    WHERE eib.token_issuer = $1
      AND eib.subject_type = 'oid'
      AND eib.subject_value = $2
    FOR UPDATE OF eib, cp
  `, [entry.token_issuer, entry.subject_value]);
  assertCondition(result.rows.length <= 1, 'IDENTITY_COORDINATE_NOT_UNIQUE');
  return result.rows[0] || null;
}

async function getOrCreatePrincipal(client, entry) {
  const result = await client.query(`
    /* techie-existing-bootstrap:principals */
    SELECT principal_id::text AS principal_id, status
    FROM canonical_principal
    WHERE tenant_id = $1::uuid
    ORDER BY created_at, principal_id
    FOR UPDATE
  `, [entry.business_tenant_id]);
  assertCondition(result.rows.length <= 1, 'TARGET_CANONICAL_PRINCIPAL_AMBIGUOUS');
  if (result.rows.length === 1) {
    assertCondition(result.rows[0].status === 'active', 'TARGET_CANONICAL_PRINCIPAL_NOT_ACTIVE');
    return { principalId: String(result.rows[0].principal_id), inserted: false };
  }
  const principalId = crypto.randomUUID();
  await client.query(`
    /* techie-existing-bootstrap:insert-principal */
    INSERT INTO canonical_principal (
      principal_id, tenant_id, status, created_at, updated_at
    ) VALUES ($1::uuid, $2::uuid, 'active', now(), now())
  `, [principalId, entry.business_tenant_id]);
  return { principalId, inserted: true };
}

function assertExistingBindingMatches(binding, entry) {
  assertCondition(binding.binding_status === 'active', 'EXISTING_BINDING_NOT_ACTIVE');
  assertCondition(binding.principal_status === 'active', 'EXISTING_BINDING_PRINCIPAL_NOT_ACTIVE');
  assertCondition(String(binding.tenant_id).toLowerCase() === entry.business_tenant_id, 'EXISTING_BINDING_TENANT_MISMATCH');
  assertCondition(String(binding.directory_tenant_id || '').trim().toLowerCase() === entry.directory_tenant_id, 'EXISTING_BINDING_DIRECTORY_MISMATCH');
  assertCondition(String(binding.identity_provider || '').trim() === entry.identity_provider, 'EXISTING_BINDING_PROVIDER_MISMATCH');
}

async function insertBindingAndAudit(client, manifest, entry, principalId, principalCreated) {
  const bindingId = crypto.randomUUID();
  await client.query(`
    /* techie-existing-bootstrap:insert-binding */
    INSERT INTO external_identity_binding (
      identity_binding_id, principal_id, directory_tenant_id, token_issuer,
      subject_type, subject_value, entra_object_id, token_subject,
      identity_provider, email_fingerprint, status, link_method,
      linked_by_principal_id, linked_at, created_at, updated_at
    ) VALUES (
      $1::uuid, $2::uuid, $3, $4, 'oid', $5, $5, NULL,
      $6, NULL, 'active', $7, NULL, now(), now(), now()
    )
  `, [
    bindingId,
    principalId,
    entry.directory_tenant_id,
    entry.token_issuer,
    entry.subject_value,
    entry.identity_provider,
    LINK_METHOD,
  ]);
  const safeDetails = JSON.stringify({
    batch_id: manifest.batch_id,
    operation_id: entry.operation_id,
    change_approval_receipt_sha256: manifest.change_approval_receipt_sha256,
    identity_evidence_receipt_sha256: entry.identity_evidence_receipt_sha256,
    identity_provider: entry.identity_provider,
    principal_created: Boolean(principalCreated),
  });
  await client.query(`
    /* techie-existing-bootstrap:insert-audit */
    INSERT INTO identity_link_audit_log (
      principal_id, identity_binding_id, action_type, result_status,
      details, created_at
    ) VALUES ($1::uuid, $2::uuid, $3, 'success', $4::jsonb, now())
  `, [principalId, bindingId, LINK_METHOD, safeDetails]);
}

async function verifyBinding(client, entry) {
  const result = await client.query(`
    /* techie-existing-bootstrap:verify */
    SELECT
      cp.tenant_id::text AS tenant_id,
      cp.status AS principal_status,
      eib.directory_tenant_id,
      eib.identity_provider,
      eib.status AS binding_status
    FROM external_identity_binding eib
    JOIN canonical_principal cp ON cp.principal_id = eib.principal_id
    WHERE eib.token_issuer = $1
      AND eib.subject_type = 'oid'
      AND eib.subject_value = $2
  `, [entry.token_issuer, entry.subject_value]);
  assertCondition(result.rows.length === 1, 'POST_BINDING_NOT_UNIQUE');
  assertExistingBindingMatches(result.rows[0], entry);
}

async function executeEntries(client, manifest) {
  const inserts = { principals: 0, bindings: 0, audits: 0, idempotent: 0 };
  for (const entry of manifest.entries) {
    const coordinateLock = `${entry.token_issuer}|oid|${entry.subject_value}`;
    await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [coordinateLock]);
    await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1, 0))', [`business-tenant|${entry.business_tenant_id}`]);
    const customerAccountId = await lockAndVerifyTarget(client, entry);
    await lockTargetBusinessRows(client, customerAccountId, entry.business_tenant_id);
    const existing = await findBindingForUpdate(client, entry);
    if (existing) {
      assertExistingBindingMatches(existing, entry);
      inserts.idempotent += 1;
      continue;
    }
    const principal = await getOrCreatePrincipal(client, entry);
    if (principal.inserted) inserts.principals += 1;
    await insertBindingAndAudit(client, manifest, entry, principal.principalId, principal.inserted);
    inserts.bindings += 1;
    inserts.audits += 1;
    await verifyBinding(client, entry);
  }
  return inserts;
}

async function runBootstrap({
  ClientClass,
  argv = process.argv,
  env = process.env,
  manifestBytes,
  output = console,
} = {}) {
  assertCondition(typeof ClientClass === 'function', 'PG_CLIENT_NOT_CONFIGURED');
  const options = parseOptions(argv);
  const bytes = manifestBytes === undefined
    ? readProtectedManifest(options.manifestPath)
    : Buffer.from(manifestBytes);
  assertCondition(bytes.length > 0 && bytes.length <= 1024 * 1024, 'MANIFEST_SIZE_INVALID');
  const manifestHash = sha256(bytes);
  let rawManifest;
  try {
    rawManifest = JSON.parse(bytes.toString('utf8'));
  } catch (_) {
    assertCondition(false, 'MANIFEST_JSON_INVALID');
  }
  const manifest = validateManifest(rawManifest, env);
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
    await client.query("SELECT pg_advisory_xact_lock(hashtextextended('techie-existing-customer-bootstrap-v1', 0))");

    const before = await summary(client);
    assertBaseState(before);

    const inserts = await executeEntries(client, manifest);
    const inside = await summary(client);
    assertExpectedIdentityDelta(before, inside, inserts);

    if (!options.apply) {
      await client.query('ROLLBACK');
      inTransaction = false;
      const afterRollback = await summary(client);
      assertCondition(summariesEqual(before, afterRollback), 'ROLLBACK_STATE_CHANGED');
      output.log(`EXISTING_CUSTOMER_BOOTSTRAP_DRY_RUN_PASS operations=${manifest.entries.length} inserts=${inserts.bindings} idempotent=${inserts.idempotent} business_invariants_unchanged=true manifest_sha256=${manifestHash}`);
      return { ok: true, mode: 'dry-run', committed: false, manifestHash };
    }

    await client.query('COMMIT');
    inTransaction = false;
    committed = true;
    const afterCommit = await summary(client);
    assertExpectedIdentityDelta(before, afterCommit, inserts);
    output.log(`EXISTING_CUSTOMER_BOOTSTRAP_APPLY_PASS operations=${manifest.entries.length} inserts=${inserts.bindings} idempotent=${inserts.idempotent} business_invariants_unchanged=true manifest_sha256=${manifestHash}`);
    return { ok: true, mode: 'apply', committed: true, manifestHash };
  } catch (error) {
    if (connected && inTransaction) {
      try {
        await client.query('ROLLBACK');
      } catch (_) {
        // Preserve the original safe error code.
      }
    }
    output.error(`EXISTING_CUSTOMER_BOOTSTRAP_${options.apply ? 'APPLY' : 'DRY_RUN'}_ERROR ${safeErrorCode(error)} commit_state=${committed ? 'committed' : 'not_committed'}`);
    return { ok: false, mode: options.apply ? 'apply' : 'dry-run', committed, manifestHash };
  } finally {
    if (connected) await client.end().catch(() => {});
  }
}

async function cliMain() {
  const { Client } = require('pg');
  const result = await runBootstrap({ ClientClass: Client });
  if (!result.ok) process.exitCode = 1;
}

if (require.main === module) {
  cliMain().catch((error) => {
    console.error(`EXISTING_CUSTOMER_BOOTSTRAP_RUNNER_ERROR ${safeErrorCode(error)} commit_state=not_committed`);
    process.exitCode = 1;
  });
}

module.exports = {
  BUSINESS_KEYS,
  ENTRY_KEYS,
  LINK_METHOD,
  SCHEMA_VERSION,
  assertBaseState,
  lockAndVerifyTarget,
  lockTargetBusinessRows,
  parseOptions,
  readProtectedManifest,
  resolveProtectedManifestPath,
  runBootstrap,
  safeErrorCode,
  sha256,
  summariesEqual,
  summary,
  validateManifest,
};
