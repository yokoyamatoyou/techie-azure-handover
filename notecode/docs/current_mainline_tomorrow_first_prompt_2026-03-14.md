C:\tetie\notecode の current mainline を主対象に進めてください。
PLANモードで作業してください。

【最初に読む】
- C:\tetie\AGENTS.md
- C:\tetie\WORKLOG.md
  - 特に 2026-03-13 の以下
    - current mainline UI journey 導線実装
    - tomorrow handoff files
- C:\tetie\notecode_current_mainline_handoff_2026-03-11.md
- C:\tetie\notecode_current_mainline_handoff_2026-03-13.md
- C:\tetie\notecode\ALGORITHM.md

【既知の状態】
- live short は実環境で 7/7 pass
- live long も実環境で 7/7 pass
- runtime blocker はなし
- company_introduction は実UI受入で OK
- announcement も実UI受入で OK
  - ただし UI 上は quality warning only 付き success
- case_study / improvement_case は single-source / 2-source の両方で preview stop
  - runtime_reason_code=INP_SOURCE_CONTEXT_INSUFFICIENT
  - needs_input_fields=['source']
  - semantic_article_key=improvement_case
  - source_fit_status=pass
- 今回の論点は runtime ではなく、case_study gate が仕様か過剰 gate か

【最優先目的】
- improvement_case の source gate を仕様として受け入れるか、最小修正対象かを判断する
- source_fit_status=pass と preview stop の非対称を owner 単位で説明できる状態にする
- 必要なら current mainline owner 内の最小修正方針だけを決める
- いきなり article_generator.py の再分割や他カテゴリ品質調整へは進まない

【主な確認対象】
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\generation_request_builder.py
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\current_mainline_runtime_logging.py
- C:\tetie\notecode\logs\latest_ui_journey.json
- C:\tetie\logs\ui_journey_log.jsonl
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\generation_audit_log.jsonl

【進め方】
- 最初に update_plan で 4〜6 steps の作業計画を出す
- まずはコード編集しない
- 次の順で確認する
  - improvement_case の source 要件がどこで定義されているか
  - source_fit.status=pass が何を保証しているか
  - INP_SOURCE_CONTEXT_INSUFFICIENT を確定している owner はどこか
  - confirm preview と generation 本体で別判定になっていないか
- その後に
  - 仕様として妥当
  - 仕様として強すぎる
 かを根拠つきで決める
- 最小修正に進むのは「仕様ではない」と確定してから

【やらないこと】
- article_generator.py の再分割
- comparative_review の品質修正
- config.json や model policy の変更
- baseline 更新
- aio2-main への着手
- 広いリファクタ

【修正が必要になった場合の原則】
- 1回に1論点だけ
- まず confirm / input decision / source gate だけを対象にする
- owner は input_contract.py / current_mainline_runner.py / note_writer_app.py のいずれか 1 箇所から始める
- 実装前に「どの owner を直すか」を明言する

【必要なテスト】
- 修正しない場合
  - ログとコードの整合確認だけでよい
- 修正する場合
  - py_compile 対象ファイル
  - pytest note\tests\test_current_mainline_runner.py -q
  - pytest note\tests\test_current_mainline_regressions.py -q
  - pytest note\tests\test_newalgorithm_phase04_ui_wiring.py -q
  - pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q
  - 必要時のみ test_generation_request_builder.py / test_current_mainline_ui_matrix.py

【最終的に出してほしい内容】
1. 現状認識
2. findings
- 事実と推測を分ける
- owner を明記する
3. improvement_case の source gate は仕様かどうか
4. source_fit_status=pass なのに preview stop する理由
5. 直すならどのファイルの最小修正か
6. 直さないなら UI 文言 / 受入条件をどう固定するか
7. 検証計画
8. AGENTS/WORKLOG 更新要否

【判断原則】
- runtime と品質課題を混同しない
- 1責務1owner
- current mainline 正本
- まず仕様確認、その後に最小修正
- 「直せそう」ではなく「仕様として矛盾している」で初めて修正する
