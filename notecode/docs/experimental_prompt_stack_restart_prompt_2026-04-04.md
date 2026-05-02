# experimental prompt stack restart prompt 2026-04-04

以下をそのまま次回開始時の prompt として使う。

---

参照ルールファイル: C:\tetie\AGENTS.md、C:\tetie\notecode\AGENTS.md
今回の実施範囲: 別ウインドウ再開用の初回プロンプト作成

以下をそのまま使ってください。

参照ルールファイル: C:\tetie\AGENTS.md、C:\tetie\notecode\AGENTS.md
今回の実施範囲: notecode の prompt-first 移行を、脚本 / 執筆 / 編集の3役で current mainline を壊さず narrow diff で前進させる

着手前に以下を読むこと。
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md
4. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md
5. C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md
6. C:\tetie\notecode\ALGORITHM.md

前提:
- 旧アルゴリズムはパラメータ制御を100回以上試して失敗したため、今後は prompt-first で進める
- モデルは GPT-5.4 mini の指示追従性を前提にする
- prompt accretion は避ける
- リーガルは今回は記事本体フローから外してよい
- 本線は current mainline:
  current_mainline_runner -> newalgorithm_pipeline -> simple_note_pipeline

現在の重要判断:
- source は本文 prompt に直積みしない
- source は別で要約し、writer には薄い handoff を渡す
- 役割は 3 つ:
  - support = 脚本担当
  - writer = 執筆担当
  - editor = 編集担当
- editor は改行、段落呼吸、AIっぽさ、一人称密度、主語省略の過不足を局所補修する
- writer に legal 判断や source digest 全文を背負わせない

直近の live 比較結果:
- artifact: C:\tetie\notecode\logs\prompt_only_compare\20260404-113244-live\summary.json
- 3変種:
  - po-source-docs-only: rubric 7, pass
  - po-source-docs-plus-inline-summary: rubric 7, pass, warning増
  - po-inline-summary-only: rubric 8, pass, ただし grounding不要扱い
- 判断:
  - source_documents + inline summary の直積みは悪化
  - 本線は source_documents only を基準にしつつ、support/script が別要約を作る構成に寄せる

すでに入っている実装:
1. support / planner / writer / editor の experimental prompt stack を脚本-執筆-編集の分担へ寄せた
   - file: C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
   - support は source を writer 向け handoff JSON に整える prompt
   - planner / writer / editor は <SCRIPT_JSON> を受ける前提に変更済み

2. embedded UI slot の復元改善
   - file: C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
   - prompt に埋め込まれた UI選択 から speaker / audience / tone / core_message を復元
   - auto/default 値に負けず上書きできるよう修正済み
   - field_sources も prompt_ui_embedded に更新される

追加済みテスト:
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py

直近の通過テスト:
- PYTHONPATH=C:\tetie\notecode python -m pytest C:\tetie\notecode\note\tests\test_simple_note_pipeline.py -k "experimental_prompt_stack" -q
  -> 3 passed
- PYTHONPATH=C:\tetie\notecode python -m pytest C:\tetie\notecode\note\tests\test_current_mainline_runner.py -k "embedded_ui_slots" -q
  -> 2 passed

このセッションの最優先タスク:
- support/script -> planner -> writer -> editor の実接続を進める
- source は support が別要約にして writer へ渡す構成にする
- current mainline を壊さない narrow diff を守る
- prompt を肥大させず、観測や閾値はできるだけ code/guard 側で持つ

このセッションでまずやること:
1. simple_note_pipeline の実行経路で experimental prompt stack がどこまで実際に使われているか確認
2. support の出力 JSON を最小 schema で確定
   - reader
   - core_message
   - source_digest
   - section_briefs[{heading, section_focus, fact_anchor, why_it_matters, do_not_mix}]
   - writing_cautions
3. writer が source raw ではなく SCRIPT_JSON を主に使うよう接続
4. editor は SCRIPT_JSON と draft を見て局所補修だけするよう接続
5. その後 live rerun を 3本切る

注意:
- completed 済み package や archive を正本にしない
- user の明示指示がない作業を勝手に拡張しない
- AGENTS の書式に従い、返信冒頭で参照ルールファイルと今回の実施範囲を明示する
- 完了時に AGENTS/WORKLOG更新の要否を1行で報告する

---
