-- TECHIE additive canonical identity migration.
-- Apply only after a schema-only backup and preflight. This migration does
-- not update existing tenants, customer accounts, Stripe IDs, or contracts.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION public.techie_identity_set_row_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------
-- Canonical principal and Entra identity binding
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.canonical_principal (
    principal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(tenant_id),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_canonical_principal_status
        CHECK (status IN ('active', 'disabled', 'disputed'))
);

CREATE INDEX IF NOT EXISTS idx_canonical_principal_tenant
    ON public.canonical_principal(tenant_id, status);

CREATE TABLE IF NOT EXISTS public.external_identity_binding (
    identity_binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL REFERENCES public.canonical_principal(principal_id),
    directory_tenant_id TEXT NOT NULL DEFAULT '',
    token_issuer TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_value TEXT NOT NULL,
    entra_object_id TEXT,
    token_subject TEXT,
    identity_provider TEXT NOT NULL DEFAULT 'unknown',
    email_fingerprint TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    link_method TEXT NOT NULL,
    linked_by_principal_id UUID REFERENCES public.canonical_principal(principal_id),
    linked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    end_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_external_identity_binding_subject_type
        CHECK (subject_type IN ('oid', 'sub')),
    CONSTRAINT chk_external_identity_binding_status
        CHECK (status IN ('active', 'disabled', 'disputed')),
    CONSTRAINT chk_external_identity_binding_email_fingerprint
        CHECK (email_fingerprint IS NULL OR email_fingerprint ~ '^[0-9a-f]{64}$')
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_external_identity_binding_coordinate
    ON public.external_identity_binding(token_issuer, subject_type, subject_value);

CREATE INDEX IF NOT EXISTS idx_external_identity_binding_principal
    ON public.external_identity_binding(principal_id, status);

CREATE INDEX IF NOT EXISTS idx_external_identity_binding_email_guard
    ON public.external_identity_binding(email_fingerprint)
    WHERE status = 'active' AND email_fingerprint IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.identity_link_intent (
    identity_link_intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL REFERENCES public.canonical_principal(principal_id),
    source_identity_binding_id UUID NOT NULL REFERENCES public.external_identity_binding(identity_binding_id),
    state_digest TEXT NOT NULL UNIQUE,
    requested_provider TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    completed_identity_binding_id UUID REFERENCES public.external_identity_binding(identity_binding_id),
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_identity_link_intent_status
        CHECK (status IN ('pending', 'completed', 'expired', 'cancelled', 'conflict')),
    CONSTRAINT chk_identity_link_intent_provider
        CHECK (requested_provider IN ('email', 'google', 'microsoft'))
);

CREATE INDEX IF NOT EXISTS idx_identity_link_intent_pending
    ON public.identity_link_intent(principal_id, status, expires_at);

CREATE TABLE IF NOT EXISTS public.identity_link_audit_log (
    identity_link_audit_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID REFERENCES public.canonical_principal(principal_id),
    identity_binding_id UUID REFERENCES public.external_identity_binding(identity_binding_id),
    identity_link_intent_id UUID REFERENCES public.identity_link_intent(identity_link_intent_id),
    action_type TEXT NOT NULL,
    result_status TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_identity_link_audit_principal
    ON public.identity_link_audit_log(principal_id, created_at DESC);

DO $$
DECLARE
    target_table TEXT;
BEGIN
    FOREACH target_table IN ARRAY ARRAY[
        'canonical_principal',
        'external_identity_binding',
        'identity_link_intent'
    ]
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger
            WHERE tgname = 'trg_' || target_table || '_updated_at'
              AND tgrelid = to_regclass(format('public.%I', target_table))
        ) THEN
            EXECUTE format(
                'CREATE TRIGGER %I BEFORE UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.techie_identity_set_row_updated_at()',
                'trg_' || target_table || '_updated_at',
                target_table
            );
        END IF;
    END LOOP;
END $$;
