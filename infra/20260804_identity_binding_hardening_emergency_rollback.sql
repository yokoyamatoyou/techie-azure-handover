-- TECHIE emergency reversal of the identity-binding invariant hardening.
-- Use only while all four identity tables are still empty and production is
-- still on the legacy resolver. This restores the pre-hardening schema state;
-- it does not modify any identity, tenant, customer, payment, contract, or
-- ledger row.

ALTER TABLE public.external_identity_binding
    DROP CONSTRAINT chk_external_identity_binding_directory_tenant_id,
    DROP CONSTRAINT chk_external_identity_binding_identity_provider;

ALTER TABLE public.external_identity_binding
    ALTER COLUMN directory_tenant_id SET DEFAULT '',
    ALTER COLUMN identity_provider SET DEFAULT 'unknown';
