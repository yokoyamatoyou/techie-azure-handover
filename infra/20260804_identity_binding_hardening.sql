-- TECHIE additive identity-binding invariant hardening.
-- Apply only while all four identity tables are still empty. This migration
-- does not read or modify customer fields and does not update tenants,
-- customer_account, Stripe identifiers, subscriptions, contracts, credits,
-- or ledgers.

ALTER TABLE public.external_identity_binding
    ALTER COLUMN directory_tenant_id DROP DEFAULT,
    ALTER COLUMN identity_provider DROP DEFAULT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.external_identity_binding'::regclass
          AND conname = 'chk_external_identity_binding_directory_tenant_id'
    ) THEN
        ALTER TABLE public.external_identity_binding
            ADD CONSTRAINT chk_external_identity_binding_directory_tenant_id
            CHECK (
                btrim(directory_tenant_id) <> ''
                AND directory_tenant_id = lower(btrim(directory_tenant_id))
            ) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.external_identity_binding'::regclass
          AND conname = 'chk_external_identity_binding_identity_provider'
    ) THEN
        ALTER TABLE public.external_identity_binding
            ADD CONSTRAINT chk_external_identity_binding_identity_provider
            CHECK (identity_provider IN ('email', 'google', 'microsoft'))
            NOT VALID;
    END IF;
END $$;

ALTER TABLE public.external_identity_binding
    VALIDATE CONSTRAINT chk_external_identity_binding_directory_tenant_id;

ALTER TABLE public.external_identity_binding
    VALIDATE CONSTRAINT chk_external_identity_binding_identity_provider;
