C:\tetie 全体を俯瞰しつつ、主対象は notecode current mainline の comparative_review long 本文品質残課題です。
PLANモードで進めてください。

【最初に読む】
- C:\tetie\AGENTS.md
- C:\tetie\WORKLOG.md
  - 特に 2026-03-12 の以下
    - current mainline semantic dedupe tail blank true owner fix
    - current mainline live revalidation after semantic dedupe fix
- C:\tetie\ALGORITHM.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\notecode\docs\current_mainline_tomorrow_plan_2026-03-13.md

【既知の状態】
- strict live short は 7/7 pass
- strict live promoted long も 7/7 pass
- runtime blocker はなし
- semantic_dedupe tail blanking は true owner fix 済み
- case_study long の末尾節欠落は解消済み
- comparative_review long の closing 節欠落も解消済み
- ただし comparative_review long の本文品質 watch が残る
  - latest long: comparative_axis_shift_count=22
  - comparative_absolute_winner_claim_count=0
- 今回は owner-only で進め、observe-only 側へは広げない

【最優先目的】
- comparative_review long の軸ぶれを本文品質ベースで下げる
- criteria -> comparison -> fit -> caution -> closing の continuity を改善する
- full rewrite ではなく、natural_blog_core / discourse_planner / section_generator の最小修正で進める
- strict live short -> promoted long の pass を維持する

【主な確認対象】
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py
- C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py
- C:\tetie\notecode\logs\current_mainline_ui_long_matrix_latest.json
- C:\tetie\notecode\logs\current_mainline_ui_runs\20260312-222043-long\ui-short-comparative-review-promoted-long.txt
- 必要なら:
  - C:\tetie\notecode\logs\current_mainline_ui_short_matrix_latest.json
  - C:\tetie\notecode\logs\current_mainline_ui_runs\20260312-202908-short\

【進め方】
- まず update_plan で 4〜6 steps の作業計画を出す
- WORKLOG の主張と現 artifact / コードが一致しているか確認する
- 次の順で見る
  - 本文のどこで軸が飛ぶか
  - discourse contract がどこで薄くなるか
  - section generation がどこで一般論へ寄るか
- 本当に必要な最小修正だけを入れる
- fixed test の後に strict live short -> promoted long を再実行する
- 重大な不明点以外は自走する

【やらないこと】
- semantic_dedupe の再修正
- runtime/config/model availability の再調整
- observe-only metric owner への拡張
- full rewrite
- threshold 微調整だけでごまかすこと

【出力してほしい内容】
1. 現状認識
2. findings
- 重大度順
- 事実と推測を分ける
- owner を明記する
3. 最小修正方針
4. Phase A/B/C の実行計画
5. 検証計画
- fixed test
- strict live short
- strict live promoted long
- artifact 人手確認
- ログ
6. open questions

【判断原則】
- 指標より本文品質
- 1責務1owner
- current mainline 正本
- runtime と本文品質を混同しない
- body owner 修正後も comparative_axis_shift_count だけが残るなら owner-only で停止する
