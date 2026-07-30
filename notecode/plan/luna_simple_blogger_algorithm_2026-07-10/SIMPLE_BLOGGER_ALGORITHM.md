# Simple Blogger Algorithm

## Status

This is an isolated candidate specification, not a Route V change.

Current decision: `conditionally_possible`.

## Input contract

The algorithm receives a compact, already-saved source-use packet containing:

- source-backed facts and excerpts
- source limits / do-not-infer items
- company/service speaker identity
- article type and target body floor

It does not receive raw full sources and does not refetch.

## Minimal blogger persona

Role ID: `company_side_blogger_v1`.

Contract:

> この会社の仕事に日々触れているブロガーとして、検索やサムネイルから偶然来た、まだ関心の薄い読者へ書く。会社を外から評さず、sourceにある具体的な場面・名詞・動作から興味を立ち上げ、事実を足さない。

The role text is writer-facing only. The role name and contract must never appear in the article.

## Arm A: one-stage baseline

Fixed model calls after the compact source packet exists: `1`.

The blogger writes the full article once.

Required behavior:

1. Open from one source-present scene, action, object, or friction point.
2. Maintain the company/provider's own voice without repeating `私たち` or `当社` mechanically.
3. Use source-specific nouns and verbs before abstract explanation.
4. Keep exactly one H1, useful H2 sections, and the configured body floor.
5. Do not add facts, outcomes, emotions, rankings, numbers, or responsibility not present in the packet.

## Arm B: same-blogger two-stage candidate

Fixed model calls after the compact source packet exists: `2`.

### Stage 1

Identical role and generation contract to Arm A.

### Stage 2

The same blogger rereads the complete Stage 1 article with the same compact source ledger. The identity does not change.

The second task is restricted to four questions:

1. Does the opening and each late section preserve a reason to continue reading for a low-interest visitor?
2. Does the prose still sound like the company-side person's own voice rather than an outside summary?
3. Can every omitted subject be recovered uniquely after speaker, paragraph, heading, and quote changes?
4. Have generic meta sentences displaced source-specific scenes, nouns, or actions?

If a paragraph fails, rewrite only that paragraph and at most one adjacent sentence. Return the complete article, preserving unaffected paragraphs, facts, H1/H2 order, and floor. If no material failure exists, return the article unchanged.

## Phrase policy

Initial watch set:

- `判断軸`
- `判断材料`
- `はじめの一歩`
- `第一歩`
- `効く`
- high-frequency meta use of `確認`, `整理`, `説明`, `判断`

This is not the main rewrite algorithm and not a synonym-replacement list. A flagged sentence must be returned to a source-specific actor, object, action, scene, or observed constraint. Source quotations are reviewed separately.

## Speaker and zero-anaphora rule

A repeated company-side subject may be omitted only when all are true:

- the actor was explicit within the previous two sentences
- no customer, partner, public body, product, or quoted speaker has become a competing discourse center
- no heading, paragraph, or quotation boundary was crossed
- the sentence does not assign a date, price, promise, request, responsibility, or customer action

Otherwise the responsible subject is explicit. `私たち` / `当社` frequency is a balance signal, not a quota.

## Stage and acceptance boundaries

- no source refetch
- no raw full source handoff
- no whole-article free regeneration in Stage 2
- no third role
- no repair loop beyond Stage 2
- no automatic fallback
- no threshold relaxation
- unsupported-claim and source-grounding gates remain hard

## Cost / latency shape

This specification only claims call shape:

- Arm A: one fixed blog-generation call
- Arm B: two fixed blog-generation calls

Prompt lengths are measured by the no-API renderer. Actual Luna tokens, latency, and cost are unknown until an explicitly approved live owner runs the sealed A/B.
