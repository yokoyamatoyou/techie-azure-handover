-- ============================================================
-- TECHIE PostgreSQL initialization script
-- Phase 2 foundation: platform billing, reseller assignment,
-- payout ledgers, coupon approval, RBAC, webhook audit, and RLS.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION set_row_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------
-- Core tenant tables preserved from Phase 1
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    stripe_id TEXT,
    plan_status TEXT NOT NULL DEFAULT 'trial',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_stripe_id ON tenants(stripe_id);

-- ------------------------------------------------------------------
-- Canonical principal and Entra identity binding
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS canonical_principal (
    principal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_canonical_principal_status
        CHECK (status IN ('active', 'disabled', 'disputed'))
);

CREATE INDEX IF NOT EXISTS idx_canonical_principal_tenant
    ON canonical_principal(tenant_id, status);

CREATE TABLE IF NOT EXISTS external_identity_binding (
    identity_binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL REFERENCES canonical_principal(principal_id),
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
    linked_by_principal_id UUID REFERENCES canonical_principal(principal_id),
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
    ON external_identity_binding(token_issuer, subject_type, subject_value);

CREATE INDEX IF NOT EXISTS idx_external_identity_binding_principal
    ON external_identity_binding(principal_id, status);

CREATE INDEX IF NOT EXISTS idx_external_identity_binding_email_guard
    ON external_identity_binding(email_fingerprint)
    WHERE status = 'active' AND email_fingerprint IS NOT NULL;

CREATE TABLE IF NOT EXISTS identity_link_intent (
    identity_link_intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL REFERENCES canonical_principal(principal_id),
    source_identity_binding_id UUID NOT NULL REFERENCES external_identity_binding(identity_binding_id),
    state_digest TEXT NOT NULL UNIQUE,
    requested_provider TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ NOT NULL,
    completed_identity_binding_id UUID REFERENCES external_identity_binding(identity_binding_id),
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_identity_link_intent_status
        CHECK (status IN ('pending', 'completed', 'expired', 'cancelled', 'conflict')),
    CONSTRAINT chk_identity_link_intent_provider
        CHECK (requested_provider IN ('email', 'google', 'microsoft'))
);

CREATE INDEX IF NOT EXISTS idx_identity_link_intent_pending
    ON identity_link_intent(principal_id, status, expires_at);

CREATE TABLE IF NOT EXISTS identity_link_audit_log (
    identity_link_audit_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID REFERENCES canonical_principal(principal_id),
    identity_binding_id UUID REFERENCES external_identity_binding(identity_binding_id),
    identity_link_intent_id UUID REFERENCES identity_link_intent(identity_link_intent_id),
    action_type TEXT NOT NULL,
    result_status TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_identity_link_audit_principal
    ON identity_link_audit_log(principal_id, created_at DESC);

CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID,
    title TEXT,
    content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID,
    report_type TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE IF EXISTS articles ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS tenant_id UUID;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'articles') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_articles_tenant_id') THEN
            ALTER TABLE articles
                ADD CONSTRAINT fk_articles_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
                NOT VALID;
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'reports') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_reports_tenant_id') THEN
            ALTER TABLE reports
                ADD CONSTRAINT fk_reports_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
                NOT VALID;
        END IF;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_articles_tenant_id ON articles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reports_tenant_id ON reports(tenant_id);

ALTER TABLE IF EXISTS articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS reports ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'articles') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public' AND tablename = 'articles' AND policyname = 'tenant_isolation_policy'
        ) THEN
            CREATE POLICY tenant_isolation_policy ON articles
                USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
                WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'reports') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies
            WHERE schemaname = 'public' AND tablename = 'reports' AND policyname = 'tenant_isolation_policy'
        ) THEN
            CREATE POLICY tenant_isolation_policy ON reports
                USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
                WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);
        END IF;
    END IF;
END $$;

-- ------------------------------------------------------------------
-- Phase 2 master data and RBAC
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS role_master (
    role_code TEXT PRIMARY KEY,
    role_name TEXT NOT NULL,
    scope_kind TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO role_master (role_code, role_name, scope_kind, description)
VALUES
    ('platform_admin', 'Platform Admin', 'platform', 'Full access across billing, payout, coupon, reseller, and audit operations.'),
    ('platform_operator', 'Platform Operator', 'platform', 'Operational visibility with controlled coupon processing and no payout formula changes.'),
    ('reseller', 'Reseller', 'reseller', 'Access limited to assigned reseller customers, payout visibility, and coupon requests.'),
    ('customer', 'Customer', 'customer', 'Access limited to own tenant data.')
ON CONFLICT (role_code) DO UPDATE
SET role_name = EXCLUDED.role_name,
    scope_kind = EXCLUDED.scope_kind,
    description = EXCLUDED.description;

CREATE TABLE IF NOT EXISTS principal_role_assignment (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id TEXT NOT NULL,
    role_code TEXT NOT NULL REFERENCES role_master(role_code),
    tenant_id UUID REFERENCES tenants(tenant_id),
    reseller_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_principal_role_assignment_principal ON principal_role_assignment(principal_id);
CREATE INDEX IF NOT EXISTS idx_principal_role_assignment_role ON principal_role_assignment(role_code, is_active);

CREATE TABLE IF NOT EXISTS reseller_master (
    reseller_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID UNIQUE REFERENCES tenants(tenant_id),
    reseller_code TEXT NOT NULL UNIQUE,
    legal_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    stripe_connect_account_id TEXT UNIQUE,
    payout_currency TEXT NOT NULL DEFAULT 'jpy',
    payout_schedule_mode TEXT NOT NULL DEFAULT 'manual_review',
    payout_hold_days INTEGER NOT NULL DEFAULT 7,
    status TEXT NOT NULL DEFAULT 'pending',
    onboarding_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_principal_role_assignment_reseller_id'
    ) THEN
        ALTER TABLE principal_role_assignment
            ADD CONSTRAINT fk_principal_role_assignment_reseller_id
            FOREIGN KEY (reseller_id) REFERENCES reseller_master(reseller_id)
            NOT VALID;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS plan_master (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_code TEXT NOT NULL UNIQUE,
    plan_name TEXT NOT NULL,
    stripe_product_id TEXT UNIQUE,
    stripe_price_id TEXT UNIQUE,
    billing_interval TEXT NOT NULL DEFAULT 'month',
    currency TEXT NOT NULL DEFAULT 'jpy',
    list_price_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS coupon_policy_master (
    coupon_policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_code TEXT NOT NULL UNIQUE,
    policy_name TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    coupon_kind TEXT NOT NULL,
    approval_mode TEXT NOT NULL DEFAULT 'single_step',
    max_percent_off NUMERIC(5, 2),
    max_amount_off NUMERIC(18, 2),
    max_duration_months INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------
-- Customer, contract, reseller assignment
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_account (
    customer_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(tenant_id),
    external_customer_code TEXT,
    legal_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    stripe_customer_id TEXT UNIQUE,
    billing_email TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_reseller_assignment (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_account_id UUID NOT NULL REFERENCES customer_account(customer_account_id),
    reseller_id UUID NOT NULL REFERENCES reseller_master(reseller_id),
    assigned_by_principal TEXT,
    assignment_reason TEXT,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to TIMESTAMPTZ,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_customer_reseller_assignment_primary
    ON customer_reseller_assignment(customer_account_id)
    WHERE is_primary = TRUE AND effective_to IS NULL;

CREATE INDEX IF NOT EXISTS idx_customer_reseller_assignment_reseller
    ON customer_reseller_assignment(reseller_id, effective_to);

CREATE TABLE IF NOT EXISTS subscription_contract (
    subscription_contract_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_account_id UUID NOT NULL REFERENCES customer_account(customer_account_id),
    reseller_id UUID REFERENCES reseller_master(reseller_id),
    plan_id UUID NOT NULL REFERENCES plan_master(plan_id),
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT UNIQUE,
    stripe_checkout_session_id TEXT,
    stripe_portal_configuration_id TEXT,
    contract_status TEXT NOT NULL DEFAULT 'draft',
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    trial_ends_at TIMESTAMPTZ,
    cancel_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_subscription_contract_customer
    ON subscription_contract(customer_account_id, contract_status);

-- ------------------------------------------------------------------
-- Billing, receipts, payouts, refunds
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS billing_event_ledger (
    billing_event_ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_account_id UUID NOT NULL REFERENCES customer_account(customer_account_id),
    subscription_contract_id UUID REFERENCES subscription_contract(subscription_contract_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    event_source TEXT NOT NULL DEFAULT 'stripe',
    external_event_id TEXT,
    event_type TEXT NOT NULL,
    stripe_invoice_id TEXT,
    stripe_payment_intent_id TEXT,
    stripe_checkout_session_id TEXT,
    amount_subtotal NUMERIC(18, 2) NOT NULL DEFAULT 0,
    amount_discount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    amount_tax NUMERIC(18, 2) NOT NULL DEFAULT 0,
    amount_total NUMERIC(18, 2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'jpy',
    billing_status TEXT NOT NULL DEFAULT 'pending',
    event_occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_billing_event_ledger_external_event
    ON billing_event_ledger(event_source, external_event_id)
    WHERE external_event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_billing_event_ledger_invoice
    ON billing_event_ledger(stripe_invoice_id);

CREATE TABLE IF NOT EXISTS payment_receipt_ledger (
    payment_receipt_ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    billing_event_ledger_id UUID NOT NULL UNIQUE REFERENCES billing_event_ledger(billing_event_ledger_id),
    customer_account_id UUID NOT NULL REFERENCES customer_account(customer_account_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    receipt_status TEXT NOT NULL DEFAULT 'pending',
    funds_status TEXT NOT NULL DEFAULT 'not_available',
    received_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    fee_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    net_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    reserved_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'jpy',
    available_for_payout_at TIMESTAMPTZ,
    hold_reason TEXT,
    settled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payment_receipt_ledger_status
    ON payment_receipt_ledger(funds_status, available_for_payout_at);

CREATE TABLE IF NOT EXISTS reseller_payout_rule (
    reseller_payout_rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reseller_id UUID REFERENCES reseller_master(reseller_id),
    plan_id UUID NOT NULL REFERENCES plan_master(plan_id),
    rule_type TEXT NOT NULL DEFAULT 'percentage',
    revenue_share_percent NUMERIC(7, 4),
    fixed_share_amount NUMERIC(18, 2),
    hold_days INTEGER NOT NULL DEFAULT 7,
    allow_negative_adjustment BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active',
    created_by_principal TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_reseller_payout_rule_share
        CHECK (
            (rule_type = 'percentage' AND revenue_share_percent IS NOT NULL AND fixed_share_amount IS NULL) OR
            (rule_type = 'fixed' AND fixed_share_amount IS NOT NULL AND revenue_share_percent IS NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_reseller_payout_rule_lookup
    ON reseller_payout_rule(plan_id, reseller_id, status, effective_from);

CREATE TABLE IF NOT EXISTS reseller_payout_ledger (
    reseller_payout_ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_receipt_ledger_id UUID NOT NULL REFERENCES payment_receipt_ledger(payment_receipt_ledger_id),
    billing_event_ledger_id UUID NOT NULL REFERENCES billing_event_ledger(billing_event_ledger_id),
    subscription_contract_id UUID REFERENCES subscription_contract(subscription_contract_id),
    reseller_id UUID NOT NULL REFERENCES reseller_master(reseller_id),
    reseller_payout_rule_id UUID REFERENCES reseller_payout_rule(reseller_payout_rule_id),
    gross_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    net_bill_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    payout_basis_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    payout_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    payout_currency TEXT NOT NULL DEFAULT 'jpy',
    payout_status TEXT NOT NULL DEFAULT 'pending',
    hold_status TEXT NOT NULL DEFAULT 'awaiting_receipt',
    eligible_at TIMESTAMPTZ,
    reserved_at TIMESTAMPTZ,
    released_at TIMESTAMPTZ,
    transfer_group TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reseller_payout_ledger_ready
    ON reseller_payout_ledger(payout_status, hold_status, eligible_at);

CREATE TABLE IF NOT EXISTS reseller_payout_execution (
    reseller_payout_execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reseller_payout_ledger_id UUID NOT NULL REFERENCES reseller_payout_ledger(reseller_payout_ledger_id),
    reseller_id UUID NOT NULL REFERENCES reseller_master(reseller_id),
    attempt_number INTEGER NOT NULL DEFAULT 1,
    execution_status TEXT NOT NULL DEFAULT 'queued',
    stripe_transfer_id TEXT UNIQUE,
    stripe_payout_id TEXT,
    transfer_group TEXT,
    failure_code TEXT,
    failure_message TEXT,
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reseller_payout_execution_retry
    ON reseller_payout_execution(execution_status, queued_at);

CREATE TABLE IF NOT EXISTS refund_adjustment_ledger (
    refund_adjustment_ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reseller_payout_ledger_id UUID REFERENCES reseller_payout_ledger(reseller_payout_ledger_id),
    billing_event_ledger_id UUID REFERENCES billing_event_ledger(billing_event_ledger_id),
    customer_account_id UUID REFERENCES customer_account(customer_account_id),
    external_adjustment_id TEXT,
    adjustment_type TEXT NOT NULL,
    adjustment_status TEXT NOT NULL DEFAULT 'open',
    gross_adjustment_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    reseller_adjustment_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'jpy',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_refund_adjustment_external
    ON refund_adjustment_ledger(adjustment_type, external_adjustment_id)
    WHERE external_adjustment_id IS NOT NULL;

-- ------------------------------------------------------------------
-- Coupon request, grant, approval, and audit
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coupon_request (
    coupon_request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reseller_id UUID REFERENCES reseller_master(reseller_id),
    customer_account_id UUID REFERENCES customer_account(customer_account_id),
    plan_id UUID REFERENCES plan_master(plan_id),
    coupon_policy_id UUID REFERENCES coupon_policy_master(coupon_policy_id),
    requested_by_principal TEXT NOT NULL,
    request_scope TEXT NOT NULL,
    request_status TEXT NOT NULL DEFAULT 'submitted',
    requested_coupon_kind TEXT NOT NULL,
    requested_percent_off NUMERIC(5, 2),
    requested_amount_off NUMERIC(18, 2),
    requested_duration_kind TEXT,
    requested_duration_months INTEGER,
    request_reason TEXT NOT NULL,
    requested_for_start_at TIMESTAMPTZ,
    requested_for_end_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_coupon_request_status
    ON coupon_request(request_status, created_at);

CREATE TABLE IF NOT EXISTS coupon_request_approval (
    coupon_request_approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coupon_request_id UUID NOT NULL REFERENCES coupon_request(coupon_request_id),
    approval_step INTEGER NOT NULL DEFAULT 1,
    approver_principal TEXT NOT NULL,
    decision TEXT NOT NULL,
    decision_note TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_coupon_request_approval_step
    ON coupon_request_approval(coupon_request_id, approval_step);

CREATE TABLE IF NOT EXISTS discount_grant (
    discount_grant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coupon_request_id UUID REFERENCES coupon_request(coupon_request_id),
    coupon_policy_id UUID REFERENCES coupon_policy_master(coupon_policy_id),
    reseller_id UUID REFERENCES reseller_master(reseller_id),
    customer_account_id UUID REFERENCES customer_account(customer_account_id),
    plan_id UUID REFERENCES plan_master(plan_id),
    granted_by_principal TEXT,
    approved_by_principal TEXT,
    target_scope TEXT NOT NULL,
    discount_kind TEXT NOT NULL,
    stripe_coupon_id TEXT,
    stripe_promotion_code_id TEXT,
    percent_off NUMERIC(5, 2),
    amount_off NUMERIC(18, 2),
    currency TEXT NOT NULL DEFAULT 'jpy',
    duration_kind TEXT,
    duration_months INTEGER,
    grant_status TEXT NOT NULL DEFAULT 'draft',
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_discount_grant_status
    ON discount_grant(grant_status, valid_from, valid_to);

CREATE TABLE IF NOT EXISTS coupon_audit_log (
    coupon_audit_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coupon_request_id UUID REFERENCES coupon_request(coupon_request_id),
    discount_grant_id UUID REFERENCES discount_grant(discount_grant_id),
    actor_principal TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------
-- Webhook, admin, and portal audit
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS webhook_event_log (
    webhook_event_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL DEFAULT 'stripe',
    stripe_event_id TEXT,
    event_type TEXT NOT NULL,
    signature_verified BOOLEAN NOT NULL DEFAULT FALSE,
    receive_status TEXT NOT NULL DEFAULT 'received',
    processing_status TEXT NOT NULL DEFAULT 'pending',
    queue_name TEXT,
    processing_attempts INTEGER NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMPTZ,
    dead_lettered_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_webhook_event_log_stripe_event
    ON webhook_event_log(provider, stripe_event_id)
    WHERE stripe_event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_webhook_event_log_processing
    ON webhook_event_log(processing_status, next_retry_at);

CREATE TABLE IF NOT EXISTS admin_action_audit_log (
    admin_action_audit_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_principal TEXT NOT NULL,
    actor_role_code TEXT REFERENCES role_master(role_code),
    action_type TEXT NOT NULL,
    target_table TEXT,
    target_record_id TEXT,
    tenant_id UUID REFERENCES tenants(tenant_id),
    reseller_id UUID REFERENCES reseller_master(reseller_id),
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_action_audit_log_actor
    ON admin_action_audit_log(actor_principal, created_at);

CREATE TABLE IF NOT EXISTS reseller_portal_access_log (
    reseller_portal_access_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reseller_id UUID NOT NULL REFERENCES reseller_master(reseller_id),
    principal_id TEXT NOT NULL,
    customer_account_id UUID REFERENCES customer_account(customer_account_id),
    action_type TEXT NOT NULL,
    request_path TEXT,
    http_method TEXT,
    response_status INTEGER,
    client_ip INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reseller_portal_access_log_reseller
    ON reseller_portal_access_log(reseller_id, created_at);

-- ------------------------------------------------------------------
-- Usage credits / consumption
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS service_usage_account (
    usage_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    service_key TEXT NOT NULL,
    subscription_contract_id UUID REFERENCES subscription_contract(subscription_contract_id),
    included_credits_total INTEGER NOT NULL DEFAULT 15,
    included_credits_used INTEGER NOT NULL DEFAULT 0,
    bonus_credits_total INTEGER NOT NULL DEFAULT 0,
    bonus_credits_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_service_usage_account UNIQUE (tenant_id, service_key),
    CONSTRAINT chk_service_usage_nonnegative CHECK (
        included_credits_total >= 0 AND included_credits_used >= 0 AND
        bonus_credits_total >= 0 AND bonus_credits_used >= 0 AND
        included_credits_used <= included_credits_total AND
        bonus_credits_used <= bonus_credits_total
    )
);

CREATE INDEX IF NOT EXISTS idx_service_usage_account_service
    ON service_usage_account(service_key, tenant_id);

CREATE TABLE IF NOT EXISTS usage_event_ledger (
    usage_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usage_account_id UUID NOT NULL REFERENCES service_usage_account(usage_account_id),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id),
    service_key TEXT NOT NULL,
    subscription_contract_id UUID REFERENCES subscription_contract(subscription_contract_id),
    actor_user_id TEXT,
    action_key TEXT NOT NULL,
    credit_bucket TEXT NOT NULL,
    units INTEGER NOT NULL DEFAULT 1,
    direction TEXT NOT NULL DEFAULT 'debit',
    idempotency_key TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_usage_event_units CHECK (units > 0),
    CONSTRAINT chk_usage_event_bucket CHECK (credit_bucket IN ('included', 'bonus')),
    CONSTRAINT chk_usage_event_direction CHECK (direction IN ('debit', 'credit'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_usage_event_idempotency
    ON usage_event_ledger(usage_account_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_usage_event_tenant_service
    ON usage_event_ledger(tenant_id, service_key, created_at DESC);

-- ------------------------------------------------------------------
-- Updated-at triggers
-- ------------------------------------------------------------------
DO $$
DECLARE
    target_table TEXT;
BEGIN
    FOREACH target_table IN ARRAY ARRAY[
        'tenants',
        'canonical_principal',
        'external_identity_binding',
        'identity_link_intent',
        'principal_role_assignment',
        'reseller_master',
        'plan_master',
        'coupon_policy_master',
        'customer_account',
        'customer_reseller_assignment',
        'subscription_contract',
        'payment_receipt_ledger',
        'reseller_payout_rule',
        'reseller_payout_ledger',
        'coupon_request',
        'discount_grant'
    ]
    LOOP
        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = target_table
              AND column_name = 'updated_at'
        ) THEN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'trg_' || target_table || '_updated_at'
            ) THEN
                EXECUTE format(
                    'CREATE TRIGGER %I BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION set_row_updated_at()',
                    'trg_' || target_table || '_updated_at',
                    target_table
                );
            END IF;
        END IF;
    END LOOP;
END $$;
