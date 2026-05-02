# First Prompt URL Family SaaS 2026-04-05

更新日: 2026-04-05  
用途: 別ウインドウへそのまま貼る開始 prompt

## Prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md
- C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
- C:\tetie\kotomegane\docs\session_notes\EXECUTION_PLAN_URL_FAMILY_SAAS_2026-04-05.md

今回の実施範囲:
- `kotomegane` のみ
- URL 状態表示と prompt family 連携を、SaaS として価値が伝わる形へ 1 パッケージ進める
- main は軽く、detail 側で深掘りする
- `aio2-main` と `notecode` は触らない

最優先ルール:
1. source of truth は上記ファイルを優先する
2. 実装は `EXECUTION_PLAN_URL_FAMILY_SAAS_2026-04-05.md` に従って自律的に進める
3. 各 Phase は `実装 -> 自己テスト -> 必要なら自己修正 -> 完了判定 -> 次 Phase` の順で進める
4. 自己テストが通ったら、ユーザーを待たずに次の Phase へ進む
5. 同一問題でエラーやバグが出た場合、修正試行は 3 回まで
6. 必要なら Web 検索で一次情報を探してよいが、3 回で直らなければ停止する
7. 3 回失敗したら、その Phase で停止し、エラー内容、試した修正、安全に残っている変更、次に必要な判断をユーザーへ報告する

UX と製品ルール:
- Hick の法則を守る
- Nielsen の 10 原則のうち `Visibility of system status`、`Recognition rather than recall`、`Aesthetic and minimalist design` を優先する
- main の主 CTA と主要選択肢は増やさない
- main の主結果 3 カード構成を壊さない
- user-facing は平易な日本語
- `検索に出た` は provider の `web_search source` に出た意味であり、一般検索順位ではない
- fallback 混在や parse failure、citation/source 不整合は `不明` を優先する

作業開始:
1. まず `EXECUTION_PLAN_URL_FAMILY_SAAS_2026-04-05.md` を読み、Phase 0 から順に進める
2. Start 時に短い plan を出す
3. 以後は各 Phase を自律的に進め、self-test 通過後に次へ進む
4. 完了時は runbook の End Report Format で報告する
```
