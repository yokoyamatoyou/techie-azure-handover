# vNext 別ウインドウ用 指示プロンプト

日付: 2026-03-21  
推奨ウインドウ: 新しい作業ウインドウ  
推奨モード: Plan mode

```text
新しいウインドウを開いてください。Plan mode で進めます。

参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\notecode\docs\vnext_blog_generation_design_draft_2026-03-21.md
- C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md

今回の実施範囲:
- vNext 実装計画の作成
- dead code quarantine 計画の作成
- adapter 境界と移行フェーズの計画化
- コード変更はまだ行わない
- UI の visible 変更提案は、提案時点で必ず明示し、勝手に確定しない
- AGENTS / WORKLOG はまだ更新しない

前提:
- vNext の設計判断は C:\tetie\notecode\docs\vnext_blog_generation_design_draft_2026-03-21.md を正本候補として扱う
- 初期フェーズでは既存 UI shell を維持する
- discourse_mode / evidence_style / emotion_level はまず内部解決とし、visible UI を増やさない
- compare 専用機能や deep observability は本流に戻さない
- 全文再生成より local repair を優先する

必ず最初に読むもの:
1. C:\tetie\notecode\docs\vnext_blog_generation_design_draft_2026-03-21.md
2. C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\note\current_mainline_runner.py
5. C:\tetie\notecode\note\generation_request_builder.py
6. C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py

今回ほしいアウトプット:
1. vNext 実装フェーズ計画
2. モジュール単位の責務分割案
3. dead code quarantine 対象一覧
4. adapter 境界案
5. テスト移行方針
6. UI 変更が必要な場合の提案一覧

特に詰めるべき論点:
1. section brief schema を実装可能なデータ構造へ落とす
2. evaluator 指標と repair trigger の対応表を作る
3. current から vNext への import 境界を切る
4. legacy / zero_base / quality / compare 系の隔離順序を決める
5. current UI の signal を vNext thin contract へどう写像するかを固定する

やらないこと:
- いきなりコードを書き始める
- UI の新規入力を勝手に増やす
- article_generator や legacy mixin をすぐ削除する
- ALGORITHM.md を先に書き換える

進め方:
1. まず current owner 境界を整理する
2. 次に vNext の新規 owner 候補を置く
3. その後 quarantine 単位を決める
4. 最後に phase 計画とテスト計画へ落とす

返してほしいもの:
1. フェーズ別実装計画
2. 各フェーズの完了条件
3. quarantine 対象と理由
4. adapter の必要性と責務
5. UI 変更の有無
6. AGENTS/WORKLOG 更新要否
```
