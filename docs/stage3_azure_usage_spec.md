# TECHIE Stage 3 Azure Usage Spec

This document describes the current Stage 3 usage-credit contract that is already implemented in the Azure/backend side of the TECHIE platform.

## Scope

The current Stage 3 backend covers:

- tenant-linked credit balances
- per-service remaining-credit summaries
- idempotent credit consumption
- admin credit grants
- insufficient-credit handling
- manual debit hooks for Kotomake and Kotomigaki
- manual and batch debit hooks prepared in Kotomegane code in the main repo

## Identity And Ownership Model

- Credit balances are managed per `tenant_id`
- Credit events may also carry `subscription_contract_id` metadata when available
- The acting authenticated user is stored as `actor_user_id`
- Service balances are separated by `service_key`

## Service Keys

- `kotomake`
- `kotomigaki`
- `kotomegane`

## Action Keys

- `kotomake.generate`
- `kotomigaki.analyze`
- `kotomegane.manual`
- `kotomegane.batch`
- `kotomegane.scheduled`

## Current Kotomegane Menu Rules

Fixed execution menus:

- `OpenAI単独観測`
  - manual run: `1` credit
  - batch job create: `1` credit
  - scheduled job create: `1` credit
  - default cadence target: `72 hours`

- `3AI横断観測`
  - manual run: `2` credits
  - batch job create: `2` credits
  - scheduled job create: `2` credits
  - default cadence target: `48 hours`

Current implementation note:

- the menu model and credit rules are implemented
- `OpenAI単独観測` is the runtime-ready path today
- `3AI横断観測` is modeled in code but should stay blocked until the client’s final multi-provider runtime/UI package is merged

## Default Usage Units For Existing Live Apps

- Kotomake generation click: `1`
- Kotomigaki analysis click: `1`

## Current API Endpoints

Base URL:

- Production API base: `https://api.techie.jp`

Endpoints:

- `GET /api/usage/summary?service_key=<service-key>`
- `POST /api/usage/consume`
- `POST /api/usage/grant`

## Request / Response Contract

### `GET /api/usage/summary`

Query parameter:

- `service_key`

Authenticated response shape:

```json
{
  "tenant_id": "uuid-or-tenant-key",
  "service_key": "kotomake",
  "included_credits": 15,
  "bonus_credits": 3,
  "used_credits": 4,
  "remaining_credits": 14,
  "updated_at": "2026-04-11T00:00:00Z"
}
```

### `POST /api/usage/consume`

Request body:

```json
{
  "service_key": "kotomake",
  "action_key": "kotomake.generate",
  "units": 1,
  "idempotency_key": "unique-click-or-job-id",
  "metadata": {
    "source": "ui"
  }
}
```

Success response includes the updated balance summary.

If credits are insufficient, the API returns:

- HTTP `402`
- `detail` explaining insufficient credits

Recommended UI behavior:

- show a clear `"insufficient credits"` message
- do not start generation/analysis if `402` is returned

### `POST /api/usage/grant`

Request body:

```json
{
  "service_key": "kotomake",
  "units": 10,
  "reason": "admin.manual_grant",
  "idempotency_key": "grant-2026-04-11-001",
  "metadata": {
    "note": "campaign compensation"
  }
}
```

Authorization rule:

- requires `admin` or `platform_admin`

## Trigger Rules

### Kotomake

- Trigger: article generation click
- Debit timing: before generation starts
- If debit fails with insufficient balance: stop and show shortage message

### Kotomigaki

- Trigger: analysis click
- Debit timing: before analysis starts
- If debit fails with insufficient balance: stop and show shortage message

### Kotomegane Manual

- Trigger: manual run click
- Debit timing: before the manual run starts
- If debit fails with insufficient balance: stop and show shortage message

### Kotomegane Batch

- Trigger: batch job submit / batch job creation
- Debit timing: at batch submit time
- Do **not** charge on import, display, or report open
- Use an idempotency key tied to the batch job
- If batch submit fails after debit, a compensating grant/rollback should be recorded

### Kotomegane Scheduled

- Trigger: scheduled batch job creation by the scheduler
- Debit timing: when the due scheduled job is created
- The scheduler uses the saved owner `tenant_id` / `user_id` from the question set or schedule
- Use an idempotency key tied to `schedule_id + scheduled slot`
- If scheduled batch submit fails after debit, a compensating grant/rollback should be recorded

## Idempotency Rule

Every debit/grant should send an `idempotency_key`.

Recommended patterns:

- manual click: UI attempt ID
- analysis click: analysis attempt ID
- batch: batch job ID
- scheduled: `schedule_id + slot key`
- rollback: `<original-id>-rollback`

This prevents accidental double charging during retries, refreshes, or transient failures.

## Database Tables

Implemented tables:

- `service_usage_account`
- `usage_event_ledger`

Purpose:

- `service_usage_account`: current credit state by tenant and service
- `usage_event_ledger`: immutable ledger of debits and grants

## Current Implementation Status

Implemented in the main production repo:

- shared usage ledger backend
- usage API endpoints
- Kotomake debit hook
- Kotomigaki debit hook
- Kotomegane manual, batch, and scheduled debit logic in the promoted main-repo code

Not yet fully deployed as a production Azure app:

- Kotomegane container/service deployment
- final Kotomegane production runtime topology

## Items Still Requiring Client Finalization

- final Kotomegane UI package/version to promote
- final Kotomegane algorithm/runtime freeze
- final 3AI execution/runtime package from the client side
- any unit/menu changes beyond the currently encoded rules
