# current mainline tomorrow first prompt

更新日: 2026-03-30  
用途: 2026-03-31 の初回セッションでそのまま貼る prompt

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md

今回の実施範囲:
- current mainline の kept state を再確認し、採用状態を崩さずに次の 1 residual を選ぶ
- 初手では実装に先走らず、current kept state の確認を優先する
- prompt accretion / module accretion を避ける
- simple_note_refactor_2026-03-22 は reopen しない

前提:
- current success path は
  C:\tetie\notecode\note\current_mainline_runner.py
  -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  -> super().generate(...)
  -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- completed 済み simple single-pass refactor は凍結扱い
- UI taxonomy は current kept state として
  - canonical UI journey route = 8分類
  - direct article selector = 7種固定
- comparative の source-grounding 増強仮説は逆効果だったため rollback 済み
- announcement の局所文法崩れは narrow fix を keep 済み
- human_resonance 本体は初手では触らない
- UI を先に増やしたり prompt を長くして直そうとしない

current kept state:
- keep 済み変更
  - UI taxonomy 対応
    - C:\tetie\notecode\note\note_writer_app.py
    - C:\tetie\notecode\note\current_mainline_runner.py
    - C:\tetie\notecode\note\current_mainline_profile_resolver.py
  - announcement 句切れ修正
    - C:\tetie\notecode\note\newalgorithm_pipeline\editor_guard.py
    - C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
- discard / rollback 済み
  - comparative の source-grounding 強化仮説
- 現在の主残差
  - comparative_review の薄さ
  - industry_analysis のタイトル自然さ
  - 全体 rubric は internal 昇格ライン未満

開始時に必ず確認するファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode\docs\current_mainline_quality_status_2026-03-23.md
6. C:\tetie\notecode\docs\simple_note_refactor_status_2026-03-23.md
7. C:\tetie\notecode_current_mainline_handoff_2026-03-30.md
8. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-03-31.md

開始時に必ず確認する最新 artifact:
1. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-ui-taxonomy-check-2026-03-30\summary.json
2. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-ui-taxonomy-check-2026-03-30\ui-short-comparative-axis-lock.txt
3. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-ui-taxonomy-check-2026-03-30\ui-short-industry-analysis.txt
4. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-announcement-final-normalize-fix-2026-03-30\summary.json
5. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-announcement-final-normalize-fix-2026-03-30\ui-short-announcement-action.txt
6. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-announcement-final-normalize-fix-2026-03-30\ui-short-announcement-dense-must-cover.txt

今回の確認ポイント:
- UI taxonomy 変更が current code に正しく残っているか
- announcement 句切れ修正が current code と artifact で整合しているか
- comparative rollback 後の kept state が崩れていないか
- 次に触る residual を 1つだけ選べるか

開始時の既定手順:
1. 上記ファイルと artifact を読む
2. announcement narrow fix について、summary と 2 本の txt を見て
   - sentence_integrity_warning_count = 0
   - announcement_invalid_modal_pattern_count = 0
   - 本文に局所文法崩れがない
   を再確認する
3. full short sweep はまだ回さず、比較系 1 case だけの targeted recheck 方針を既定にする
4. ui-short-comparative-axis-lock を読み、axis drift ではなく「薄さ」が主残差かを確認する
5. single residual を 1つだけ選ぶ
   - 今回の第一候補は comparative_review の薄さ
6. 実装に入る場合も single hypothesis / owner-local で進める

固定ルール:
- 1ターンで扱う residual は 1つだけ
- 1ターンで立てる hypothesis は 1つだけ
- 触る owner file は最大 2 ファイル
- prompt accretion をしない
- module accretion をしない
- failed hypothesis は即 discard し、採用状態を再固定する
- comparative と announcement を同時に触らない
- Web検索は初手では使わない
- local artifact と local code で足りない場合だけ補助的に使う

今回選ぶ single residual:
- comparative_review の薄さ

owner file:
- 第一候補: C:\tetie\notecode\note\natural_blog_core.py
- ここで筋が通らない場合でも、初手で owner を増やさない

success 条件:
- current success path と kept state を崩していないことを確認できる
- announcement kept fix が code / artifact の両方で保持されている
- comparative rollback 済み仮説が再投入されていない
- ui-short-comparative-axis-lock の主残差を axis drift ではなく薄さとして切り分けられる
- 次に触る owner file を 1つに固定できる

rollback 条件:
- prompt を長くしないと説明できない仮説だった場合
- module を増やさないと成立しない仮説だった場合
- announcement kept fix の再確認で regression が見つかった場合
- comparative axis drift の再発が見つかり、薄さより先に kept state 修復が必要になった場合
- owner file が 2 を超える見込みになった場合

やってはいけないこと:
- simple_note_refactor_2026-03-22 を reopen すること
- prompt を長くして帳尻を合わせること
- module を増やして見かけ上の正しさを作ること
- comparative の rollback 済み仮説をそのまま再投入すること
- external review 未確認のまま全面移行を宣言すること

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- current kept state
- discard 済み仮説
- 今回選んだ single residual
- owner file
- success 条件
- rollback 条件
- AGENTS / WORKLOG 更新の有無
```
