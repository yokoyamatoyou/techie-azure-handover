# current mainline tomorrow first prompt

更新日: 2026-03-23  
用途: 次回セッション開始時にそのまま貼る初回プロンプト

## 目次
- prompt
- 補足メモ

## prompt

```text
参照ルールファイル:
  - C:\tetie\AGENTS.md
  - C:\tetie\notecode\AGENTS.md

今回の実施範囲:
  - 2026-03-24 の初回起動として、current mainline short quality の続きから再開する
  - completed 済みの simple_note_refactor_2026-03-22 plan package は completed のまま扱い、勝手に reopen しない
  - runtime owner を広げず、simple_note_pipeline owner 内の narrow fix に限定する
  - prompt accretion / module accretion を避ける

実行モード:
  - Default mode
  - Plan mode へ切り替えない

開始直後に必ず確認するファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\README.md
4. C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md
5. C:\tetie\notecode\ALGORITHM.md
6. C:\tetie\notecode\docs\current_mainline_quality_status_2026-03-23.md
7. C:\tetie\notecode\docs\simple_note_refactor_status_2026-03-23.md
8. C:\tetie\notecode_current_mainline_handoff_2026-03-23.md
9. C:\tetie\WORKLOG.md
10. latest live artifacts
   - C:\tetie\notecode\logs\current_mainline_ui_runs\20260323-104904-short
   - C:\tetie\notecode\logs\current_mainline_ui_runs\20260323-120255-short

開始時の最初の行動:
  - filesystem を確認し、上記 path と現物が一致するか確認する
  - current runtime mainline が C:\tetie\notecode\note\simple_note_pipeline\pipeline.py であることを再確認する
  - compatibility import path が C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py であることを再確認する
  - completed initiative と pending quality work を混在させず整理する
  - 先に live artifact diff を見てから narrow fix に入る
  - 先に module 追加や route 追加へ入らない

今回の本命 owner:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py

今回の目的:
  - short body の section density / sentence rhythm を replacement-only で改善する
  - guard ではなく prompt_builder 側を first slice とする
  - 文字数を増やすこと自体を目的にしない
  - source-grounded を壊さない

固定ルール:
  - 本文 mainline は single-pass + optional single repair 1回
  - markdown `## 目次` を使い、native TOC へ広げない
  - note rule check は必須
  - free text は残す
  - question flow は unresolved slot 補完に限定する
  - old ArticleGenerator / human_resonance* / vnext を本文 mainline に戻さない
  - prompt と module を肥大化させない

やってはいけないこと:
  - prompt accretion
  - module accretion
  - 文字数を増やすこと自体を目的にすること
  - source にない断定的な補足を足すこと
  - simple_note_refactor_2026-03-22 を reopen すること

最初に見るべき case:
  - ui-short-explanatory-default
  - ui-short-case-study-explain
  - ui-short-branding-company-grounded

想定する進め方:
  - まず 20260323-104904-short と 20260323-120255-short の case diff を整理する
  - その後、prompt_builder.py に replacement-only の narrow fix を入れる
  - focused test を回す
  - current mainline regression を回す
  - short live rerun を 1 回だけ実行する

最終報告で必ず示すこと:
  - 読んだ正本ファイル
  - 変更した file path
  - AGENTS / WORKLOG 更新の有無
  - latest live artifact path
  - current quality blocker の要約
  - 次に残る narrow fix 候補
```

## 補足メモ

- 2026-03-23 の latest live は `C:\tetie\notecode\logs\current_mainline_ui_runs\20260323-120255-short`
  - `rubric_mean_total=7.3`
- 直前の better run は `C:\tetie\notecode\logs\current_mainline_ui_runs\20260323-104904-short`
  - `rubric_mean_total=7.5`
- 次回は `quality_guard.py` を先に広げるより、`prompt_builder.py` で section density / rhythm を狭く寄せる方が本命
