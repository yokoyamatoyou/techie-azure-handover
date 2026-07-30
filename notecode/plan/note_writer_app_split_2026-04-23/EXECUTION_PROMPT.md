# note_writer_app_split_2026-04-23 EXECUTION_PROMPT

`C:\tetie\notecode` の `note_writer_app.py` safe split separate initiative は、直近 window で `Phase 06A: Result Rendering Builder Extraction` まで完了し、その後 `Phase 06B` 候補選定で追加分割を止めて実 UI smoke validation を先に行う判断まで完了済みです。

## Current Startup Rule

- この prompt から次の product code 実装へ自動連鎖しない。
- 次 window は remaining post-generation split ではなく、full-flow user-trial readiness / smoke evidence review を扱う。
- `naturalness_recovery_2026-04-07` current source of truth は維持する。
- `Phase 06A` の completed baseline を巻き戻さない。
- `Phase 06B` として product code 分割は実施しない。

## 最初に読む

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
7. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
8. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
9. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md`
10. `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
11. `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
12. `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
13. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`
    - `## 13. GPT Image 2 Image Generation Algorithm`
14. `C:\tetie\notecode\note\note_writer_app.py`
15. `C:\tetie\notecode\note\note_writer_app_main_page_sections.py`

## Current Verified Baseline

- `Phase 01: Head Assets`: completed
- `Phase 02: Source / Upload / Bootstrap Helpers`: completed
- `Phase 03: Standalone Subviews`: completed
- `Phase 04: Manual Legal Local Helpers`: completed
- `Phase 05: Main Page Pre-Generation Builders`: completed
- `Phase 06A: Result Rendering Builder Extraction`: completed
- `Phase 06B: Candidate Selection / UI Smoke First`: completed without product-code split

`Phase 06A` で `note_writer_app_main_page_sections.py` は result output display builder と quality / review display containers を保持する。`note_writer_app.py` は copy binding、widget mutation、image timing、legal timing、`run_generation()` body、current mainline runner invocation を保持する。

`Phase 06B` では次を確認した。

- `note_writer_app.py`: `8079` lines / `270` definitions / `168` top-level definitions
- `note_writer_app_main_page_sections.py`: `595` lines / `8` definitions
- selected decision: `G. Phase 06B は実装せず、result rendering 変更後の実 UI smoke validation を先に行う`
- smoke URL: `http://127.0.0.1:18080/`
- smoke source: `https://example.com`
- smoke attempt: `gen-ec362ddf`
- smoke outcome: `review_required_draft`
- smoke reason: `SYS_QUALITY_WARNINGS_UNRESOLVED`
- result shell / preview / detail readonly fields / individual section fields / image panel / manual legal panel buttons は表示確認済み
- image generation は output guard stop により未到達。image timing は未変更のまま、次の full-flow readiness で success path として再確認する

## Parked Remaining Candidates

- image auto UI/status helper extraction
- copy/save/export UI helper extraction
- remaining legal panel layout extraction
- journey state transition pure helper extraction
- post-generation metadata / quality summary shaping helper extraction
- `run_generation()` body split: high risk / parked unless explicitly reopened

## Non-Goals Until Replanned

- `run_generation()` body の分割
- generation completion / exception / finally cleanup timing の整理
- image generation trigger timing の変更
- manual legal event timing の変更
- copy-save behavior の変更
- confirm state mutation の helper 移動
- source contract / prompt / threshold / repair count / output guard / image generation logic の変更
- `pipeline.py` / `quality_guard.py` / `output_guard.py` / `blog_image_auto.py` の変更

## Required Next Step

通常モードで次を行う。

- product code を変更しない full-flow user-trial readiness / smoke evidence review を続ける
- `gen-ec362ddf` は review-required draft で image generation phase 未到達だったため、success path の image generation / fail-open UI は別 smoke で確認する
- remaining split candidates は user-trial readiness の後で必要な場合だけ PLAN モードで再選定する
- AGENTS 更新は不要。routing / current source-of-truth が変わる場合だけ更新する
