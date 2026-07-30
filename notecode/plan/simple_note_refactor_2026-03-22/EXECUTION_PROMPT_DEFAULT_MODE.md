# Execution Prompt (Default Mode)

以下を別ウインドウの最初のプロンプトとして使う。

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md

今回の実施範囲:
- C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md に従い、current phase から simple single-pass note refactor を実装する
- phase ごとの計画正本は C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PHASE_00_PLAN_LOCK_AND_RULES.md から PHASE_08_HANDOFF_FREEZE.md を参照する
- old algorithm と current refactor を混在させない

実行モード:
- Default mode で進める
- Plan mode へは切り替えない

開始時の read order:
1. C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\README.md
2. C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md
3. current phase の phase 文書
4. C:\tetie\notecode\ALGORITHM.md
5. C:\tetie\WORKLOG.md

固定ルール:
- 本文 mainline は single-pass + optional single repair 1回を維持する
- markdown ## 目次 を使い、native TOC へ広げない
- note rule check は必須
- human corpus / learner は first track で導入する
- learner 初期モデルは RandomForest
- prompt accretion を禁止する
- module accretion を禁止する
- runtime package の新規 file 追加は replacement とセットにする
- old ArticleGenerator / human_resonance* / vnext を本文 mainline へ戻さない
- free text は残す
- current interview / question flow は unresolved slot 補完に限定する
- brand_architecture_clarity は visible UI に出さず、source + user prompt + unresolved slot question で補う

phase 運用ルール:
- PROGRESS.md の current phase だけを進める
- phase をまたいだ実装を同じ slice で行わない
- phase 開始時に PROGRESS.md の phase status を in_progress に更新する
- phase 完了時に PROGRESS.md を completed に更新し、next phase を current next slice に設定する
- runtime contract を変えたときだけ C:\tetie\notecode\ALGORITHM.md を更新する
- phase 完了または plan package 更新時だけ C:\tetie\WORKLOG.md を更新する

各 phase の完了条件:
- phase 文書の Self-Test を全て実施する
- 次の 4 系統が通るまで completed にしない
  1. functional
  2. prompt injection / policy
  3. anti-bloat
  4. readability / owner boundary

自律実行ルール:
- phase 完了テストに合格したら、自律的に次の phase へ移動する
- 全 phase 完了後に内部で動作テストを実施する
- phase 中にエラーが出たら、その場で最大 2 回まで修正を試みる
- 2 回で解消しない場合は停止し、何が失敗したか、どこまで終わったか、次に必要な判断は何かを user に報告する

混線防止ルール:
- pre-refactor 情報は archive 側へ分離し、current refactor の docs / logs / artifacts と混在させない
- plan package の current source of truth は次に固定する
  - C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\README.md
  - C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md
- 旧 path は compat redirect として扱い、正本にしない

最初の行動:
- C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md を読み、Phase 01 Archive Boundary And Baseline Freeze から開始する
- 実装前に current filesystem を確認し、plan と現物の差があれば PROGRESS.md にメモしてから進める
```
