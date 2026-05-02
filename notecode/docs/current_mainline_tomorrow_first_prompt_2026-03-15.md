# current mainline tomorrow first prompt (2026-03-15)

`C:\tetie\notecode` の current mainline を主対象に進めてください。
PLANモードで作業してください。

【最初に読む】
- `C:\tetie\AGENTS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode\docs\current_mainline_tomorrow_plan_2026-03-13.md`
- `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-03-14.md`
- `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`
- `C:\tetie\notecode\note\natural_blog_core.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py`
- `C:\tetie\notecode\note\tests\test_natural_blog_core.py`
- `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_latest.json`
- `C:\tetie\notecode\logs\current_mainline_ui_long_matrix_latest.json`
- latest artifacts
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\20260315-102928-short\ui-short-comparative-review.txt`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\20260315-103447-long\ui-short-comparative-review-promoted-long.txt`

【現状】
- current mainline owner split は completed のまま
- `section_generator.py` の comparative fragment repair は 2026-03-15 時点で追加 1 回入っている
  - `だけでなく。` を join 対象に追加
  - `...のか。ここ/この/それ/その/そう/こう...` の interrogative fragment join を追加
- `py_compile` は pass
- `pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ad2 or st05ab4 or st05ab6 or st05ab8 or st05ab9 or st05ac or st05ac2 or st07e or comparative_review" -q` は `15 passed`
- `pytest note\tests\test_natural_blog_core.py -k comparative_review -q` は `7 passed`
- strict live short / promoted long は 2026-03-15 に再取得済み
- latest metrics
  - short: `comparative_axis_shift_count=13`, `comparative_absolute_winner_claim_count=0`, `sentence_integrity_warning_count=0`
  - long: `comparative_axis_shift_count=17`, `comparative_absolute_winner_claim_count=0`, `sentence_integrity_warning_count=0`
- 今回の target だった残差は解消済み
  - short の `...だけでなく。...`
  - long の `...のか。ここが...`
  - long の `万能な一択` 由来 absolute winner
- ただし latest 本文に新規残差が残っている
  - short: latest artifact line 24
  - long: latest artifact line 56
- 現時点では `comparative_review long` は watch-only 受入不可
- `discourse_planner.py` を reopen する根拠はまだ不足
- `A/B/C` placeholder 論点は保留のまま

【今回の目的】
- latest short line 24 と latest long line 56 の残差が本当に section-local sentence shaping の問題かを確定する
- もしそうなら `section_generator.py` だけの最小修正方針を決める
- prompt owner / discourse owner / quality owner へ広げるのは根拠が出た場合だけにする
- まだコード編集しない

【主な確認対象】
- latest short line 24 の残差
- latest long line 56 の残差
- `section_generator.py` の comparative fragment cleaner と sentence join 条件
- `natural_blog_core.py` の guard で既に防げている範囲
- metrics pass と manual read のズレ
- `sentence_integrity_warning_count=0` なのに visible residual が残る理由

【進め方】
- 最初に update_plan で 4〜6 steps の作業計画を出す
- まずはコード編集しない
- 次の順で確認する
  - latest short / long artifact の該当行を本文で読み、残差パターンを分類する
  - `section_generator.py` のどの条件で取りこぼしているかを確認する
  - `natural_blog_core.py` で吸収すべき問題か、section-local shaping 問題かを切り分ける
  - `sentence_integrity_warning_count=0` と manual residual のズレが metric owner 側の話かを確認する
  - `discourse_planner.py` まで広げる根拠があるかを確認する
- その後に
  - `section_generator.py` の最小修正でよい
  - まだ owner 確定できない
  - 本文は許容で watch が厳しすぎる
  のどれかを根拠つきで決める
- 最小修正に進むのは「section-local な本文破綻」と確定してから

【やらないこと】
- article_generator.py の再分割
- input_contract / runner / UI / runtime_logging の reopen
- config.json や model policy の変更
- baseline 更新
- aio2-main への着手
- `A/B/C` placeholder 問題の掘り下げ
- 広いリファクタ

【修正が必要になった場合の原則】
- 1回に1論点だけ
- owner はまず `section_generator.py` だけ
- 実装前に「今回は section_generator.py のどの条件を直すか」を明言する
- 実装したら `py_compile`、focused pytest 2 本、strict live short、promoted long の順で再検証する

【必要なテスト】
- 修正しない場合
  - py_compile 対象ファイル
  - pytest `note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ad2 or st05ab4 or st05ab6 or st05ab8 or st05ab9 or st05ac or st05ac2 or st07e or comparative_review" -q`
  - pytest `note\tests\test_natural_blog_core.py -k comparative_review -q`
  - latest short / long artifact の manual read
- 修正する場合
  - py_compile 対象ファイル
  - pytest `note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ad2 or st05ab4 or st05ab6 or st05ab8 or st05ab9 or st05ac or st05ac2 or st07e or comparative_review" -q`
  - pytest `note\tests\test_natural_blog_core.py -k comparative_review -q`
  - strict live short
  - promoted long

【最終的に出してほしい内容】
1. 現状認識
2. findings
- 事実と推測を分ける
- owner を明記する
3. latest 残差の true owner
4. `section_generator.py` の最小修正で足りるか
5. 直すならどの条件を直すか
6. 検証計画
7. AGENTS/WORKLOG 更新要否

【判断原則】
- current mainline 正本
- runtime と品質を混同しない
- 1責務1owner
- まず artifact で本文を確認し、その後に最小修正
- 「直せそう」ではなく「section-local な本文破綻」で初めて修正する
