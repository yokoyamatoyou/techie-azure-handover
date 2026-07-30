# TASK

## Global Rules

- docs-only package として扱う
- product code を変更しない
- tests / rerun / UI server startup は行わない
- `single-pass + optional single repair 1回` を維持する
- prompt accretion / module accretion を避ける
- source外 claim を許容しない
- fingerprint / quality / source grounding threshold を緩和しない
- internal/runtime terms を本文/UIに出さない
- `相談の入口` を単語禁止だけで潰さない
- source-backed な問い合わせ窓口への自然な短い言及は残せる
- 会社紹介記事の主軸を相談導線に戻さない

## Phase 0: Read Artifacts

Objective:

- current baseline、直前診断、current user-trial state を読む。

Required artifacts:

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\`
- `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\`
  - `diagnosis.md`
  - `repair_prompt_trace.json`
  - `repair_candidate_comparison.json`
  - `owner_decision.md`
  - `next_owner_decision.md`
- `C:\tetie\WORKLOG.md`

Exit:

- `B + D mixed` と `repair_acceptance.py` 非対象判断を維持できる。

## Phase 1: Patch-Scope Failure Mechanism

Objective:

- なぜ現行 patch scope では lead / heading の route drift を直せないかを固定する。

Decision:

- bad phrase が `LEAD` / heading name にあると、repair prompt が preservation を要求し、`pipeline.py` acceptance も lead / heading stability を要求するため、candidate は悪い surface を保持しやすい。
- この symptom は body の局所修復不足ではなく、patch-scope surface boundary の問題として扱う。

Exit:

- prompt-only fix でも acceptance-only fix でもないことを説明できる。

## Phase 2: Owner Decision

Objective:

- implementation owner を 1 つに固定する。

Decision:

- next owner:
  - `company_intro patch-scope helper`
- implementation shape:
  - `pipeline.py` へ直接大きな条件を入れない
  - small helper を切り出し、route drift phrase location / allowed lead-heading patch / acceptance precondition を集約する
  - `pipeline.py` は existing patch hook から helper を呼ぶだけにする
  - `prompt_builder.py` は必要な場合だけ既存 preservation wording を conditional replacement する
  - `repair_acceptance.py` は clean candidate が出るまで触らない

Exit:

- one owner / one hypothesis として次 implementation prompt に渡せる。

## Phase 3: Implementation Prompt

Objective:

- 次ウインドウで実装する場合の prompt を作る。ただし今回は実装しない。

Prompt requirements:

- 通常モード
- owner を 1 つに固定
- product code scope を明記
- patch scope handling 条件を明記
- tests を明記
- `company_introduction` 3回 rerun を明記
- `announcement` / `comparative_review` smoke を明記
- WORKLOG 更新を明記
- AGENTS 判断を明記

Exit:

- `EXECUTION_PROMPT.md` が次 window の開始 prompt として使える。

## Phase 4: Validation Gate

Objective:

- 実装後の rerun / smoke gate を固定する。

Implementation validation gate:

- owner-local tests:
  - company_intro patch-scope helper tests
  - lead route phrase removal allowed only under company_introduction + route phrase location
  - affected heading rename allowed only when heading itself has route drift phrase
  - unflagged heading rename rejected
  - source-backed business material drop rejected
  - clean candidate not required to touch `repair_acceptance.py`
- focused regression:
  - `company_intro` / `company_introduction` tests
  - repair prompt patch-scope prompt tests
  - current mainline company_intro tests
  - quality guard regression
- rerun:
  - `company_introduction` 3回
  - route drift phrase in lead / heading should be `0/3`
  - body present `3/3`
  - `SYS_PIPELINE_FAILURE` `0/3`
  - internal leakage `0/3`
  - source grounding not worse
  - current business / product-service / support scope retained
- non-target smoke:
  - `announcement`
  - `comparative_review`

Exit:

- rerun gate passes before user-trial hold is lifted.

