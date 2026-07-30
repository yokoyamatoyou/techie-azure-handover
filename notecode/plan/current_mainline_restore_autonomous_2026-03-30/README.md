# current_mainline_restore_autonomous_2026-03-30

current mainline のブログ品質を、kept state を崩さずに段階的に戻すための autonomous execution plan。

## Goal

- current success path を維持したまま、`explanatory_article` / `industry_analysis` 中心の blog quality を回復する
- `gpt-5.4-mini` の追従性を活かせる prompt topology へ寄せる
- prompt accretion / module accretion を避け、責務分離で改善する

## Success Definition

- current success path を維持する
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> super().generate(...)`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- announcement kept fix を維持する
  - `sentence_integrity_warning_count=0`
  - `announcement_invalid_modal_pattern_count=0`
- comparative rollback 済み仮説を再投入しない
- `simple_note_pipeline` の prompt / planning 責務を分離し、single-pass writer の追従先を明確化する
- 最終 phase で live 3 blog generation を通し、品質評価を完了する

## Non-Goals

- `simple_note_refactor_2026-03-22` の reopen
- `human_resonance` 本体の初手改修
- prompt wording の足し算だけで押し切ること
- owner 不明の global tuning

## Fixed Constraints

- local code / local artifact / live output を主判断にする
- prompt / module の accretion を避ける
- 新規 module は責務が 1 つで既存 owner 重複を減らす場合のみ
- phase ごとに pass したら自律的に次へ進む
- phase ごとに error / regression が出たら 3 回まで自己修正を試みる
- 3 回で復旧できなければ停止し、user report に切り替える

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\ALGORITHM.md`
4. `C:\tetie\WORKLOG.md`
5. `C:\tetie\notecode\docs\current_mainline_quality_status_2026-03-23.md`
6. `C:\tetie\notecode\docs\simple_note_refactor_status_2026-03-23.md`
7. `C:\tetie\notecode_current_mainline_handoff_2026-03-30.md`
8. `C:\tetie\notecode\docs\current_mainline_codex_prompt_2026-03-31_burstiness.md`
9. `C:\tetie\notecode\plan\current_mainline_restore_autonomous_2026-03-30\PROGRESS.md`

## Core Hypothesis

- 旧アルゴリズムの強みは「長い prompt」ではなく「役割分離された prompt」と「段階分離」だった
- 現行 current mainline は `simple_note_pipeline` single-pass writer に contract / style / structure / evidence / output を詰め込みすぎている
- `gpt-5.4-mini` は追従性が高いので、1 本の dense prompt よりも、明確に分離された prompt block と compact plan を与えた方が活きる

## Autonomous Rules

- mode は `PLANモード`
- 各 phase は `entry -> implementation -> tests -> exit check -> progress update` の順に進める
- 次 phase へ進む条件:
  - phase の required tests がすべて pass
  - kept state regression がない
  - rollback condition に該当しない
- 停止条件:
  - 同一 phase で 3 回連続して自己修正しても gate を越えられない
  - announcement kept fix regression
  - comparative rollback 済み仮説の再投入
  - owner file 増加が設計境界を超える

## Phase Map

### Phase 00 Baseline Freeze

- 目的:
  - current artifact / code / kept state を再確認して baseline を固定する
- owner:
  - read-only
- 作業:
  - kept state artifact を再確認
  - current success path の owner を再確認
  - final comparison baseline を `PROGRESS.md` に記録
- tests:
  - artifact read check
  - no-edit confirmation
- exit:
  - baseline metrics / blocked hypotheses / kept fixes が明文化されている

### Phase 01 Legacy vs Current Diff Inventory

- 目的:
  - 旧 `outline/article_generator/post_processor` と current `simple_note_pipeline` の責務差を整理する
- owner:
  - read-only
- 作業:
  - `outline responsibility`
  - `section responsibility`
  - `repair responsibility`
  - `postprocess responsibility`
  - `task-model responsibility`
    を diff table 化する
- tests:
  - diff table completeness review
- exit:
  - current で欠落した責務が 3 個以内に絞れている

### Phase 02 Restore Slice Selection

- 目的:
  - 旧責務のうち、最初に戻す 1 slice を選ぶ
- owner:
  - read-only
- 候補:
  - compact structure plan
  - writer prompt block separation
  - repair prompt scope tightening
- tests:
  - slice が `owner <= 2 files` で成立するかレビュー
- exit:
  - first implementation slice が 1 つに固定される

### Phase 03 Prompt Topology Refactor

- 目的:
  - writer prompt を block 単位に再構成し、dense profile 依存を下げる
- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- 作業:
  - `PROFILE` 圧縮をやめ、以下の logical blocks を明示する
  - `HARD_CONTRACT`
  - `STRUCTURE`
  - `STYLE`
  - `EVIDENCE`
  - `OUTPUT_SCHEMA`
  - wording の追加ではなく、既存情報の再配置を優先する
- tests:
  - `test_simple_note_pipeline.py`
  - anti-bloat assertion
- exit:
  - prompt 総量が大きく増えず、block separation が見える

### Phase 04 Compact Plan Prepass Scaffold

- 目的:
  - full outline 復帰ではなく、compact plan JSON prepass の枠だけ追加する
- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- 作業:
  - `heading / purpose / key_message / do_not_cover` の最小 schema を定義
  - writer prompt に plan summary を差し込めるようにする
  - 初期は article type 限定を許可する
- tests:
  - new focused unit tests
  - current pipeline regressions
- exit:
  - prepass schema が parse/fail-open で安定する

### Phase 05 Explanatory Activation

- 目的:
  - explanatory short だけで compact plan を有効化する
- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`
- 作業:
  - `explanatory_article` short/adaptive のみ activation
  - fail-open fallback を維持
- tests:
  - focused pytest
  - announcement/comparative sentinel regression tests
- exit:
  - explanatory で regression なし

### Phase 06 Targeted Explanatory Live

- 目的:
  - first live improvement を 1 case で確認する
- owner:
  - code edit なし想定
- live case:
  - `ui-short-explanatory-default`
- required metrics:
  - `paragraph_length_cv` baseline 比で改善
  - `soft_warning_count` baseline 以上に悪化しない
  - readability 悪化なし
- exit:
  - pass なら次 phase へ進む
  - fail なら 3 回まで修正ループ、それでも不可なら停止

### Phase 07 Industry Activation

- 目的:
  - explanatory で通った slice を `industry_analysis` へ広げる
- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - relevant tests
- tests:
  - focused pytest
  - targeted `industry_analysis` contract regressions
- exit:
  - industry で kept state regression なし

### Phase 08 Targeted Industry Live

- 目的:
  - `industry_analysis` 1 case live で flatness 改善を確認する
- live case:
  - `ui-short-industry-analysis`
- metrics:
  - `paragraph_length_cv`
  - `paragraph_sentence_count_cv`
  - `soft_warning_count`
  - rubric
- exit:
  - pass で次へ
  - fail は 3 回まで自己修正

### Phase 09 Comparative / Announcement Sentinel Protection

- 目的:
  - kept state regression を出さないまま restore slice を固定する
- owner:
  - tests only が基本
- checks:
  - comparative rollback 仮説が再投入されていない
  - announcement kept fix 維持
  - taxonomy keep 維持
- tests:
  - focused pytest
  - artifact/metric checks
- exit:
  - sentinel green

### Phase 10 Comparative Optional Extension

- 目的:
  - explanatory/industry で成立した prompt separation が comparative にも効くか narrow に判断する
- owner:
  - `pipeline.py` / `prompt_builder.py` 以内
- rule:
  - source-grounding rollback 仮説は再投入しない
  - semantic tail suppression は再投入しない
- tests:
  - focused comparative regressions
- exit:
  - pass しない場合は comparative への適用を見送って次 phase へ進む

### Phase 11 Parameter Tuning Loop

- 目的:
  - code phase 完了後、parameter だけで 2〜3 回まで最適化を試す
- allowed knobs:
  - `llm.article_type_params.explanatory_article.verbosity`
  - `llm.article_type_params.industry_analysis.verbosity`
  - `llm.article_type_params.explanatory_article.reasoning_effort`
  - `llm.article_type_params.industry_analysis.reasoning_effort`
  - 必要時のみ `section` task model の reasoning / verbosity
- forbidden:
  - model を無差別に戻すこと
  - prompt を増やして帳尻合わせすること
- loop:
  - 1 loop につき 1 parameter family のみ変更
  - 毎 loop で targeted test + 1 live rerun
- exit:
  - 改善が止まった時点で確定

### Phase 12 Final Live 3-Run Evaluation

- 目的:
  - final acceptance を live 3 blog generation で判断する
- live cases:
  - `ui-short-explanatory-default`
  - `ui-short-industry-analysis`
  - `ui-short-comparative-review`
- quality read:
  - `paragraph_length_cv`
  - `paragraph_count`
  - `paragraph_sentence_count_cv`
  - `soft_warning_count`
  - rubric total
  - human-visible AI signals
- pass:
  - kept state regression なし
  - explanatory / industry は baseline 比で改善または readability 向上
  - comparative は少なくとも悪化しない

### Phase 13 Closeout

- 目的:
  - 最終状態を handoff 可能にする
- 作業:
  - `WORKLOG.md` 更新
  - 必要なら `ALGORITHM.md` 追記
  - tuning を実施した場合は `generation_parameter_tuning_log.md` 更新
  - final report 作成

## Test Matrix

- functional
  - `note/tests/test_simple_note_pipeline.py`
  - `note/tests/test_current_mainline_runner.py`
- prompt injection / policy
  - relevant `current_mainline_regressions`
- anti-bloat
  - prompt block / owner count / no new broad module
- readability / owner boundary
  - targeted live rerun metrics

## Retry / Stop Rule

- phase 内で failure が出たら:
  - 1) root cause localize
  - 2) owner-local 修正
  - 3) same phase tests rerun
- これを最大 3 回まで
- 3 回で復旧できなければ停止し、以下を user に報告する
  - failed phase
  - last attempted hypothesis
  - regression / blocker
  - recommended rollback or next slice
