# Route B UI Kyoto Kogyo Validation Next Window Prompt 2026-06-17

目的: コトメイク通常UIの `記事を生成` が Route B (`route_b_0506_structured_blog_v1`) で本文生成されることを、京都工業ソースで実画面から確認する。Route A は明確に切り離し、比較実行・自動 fallback・手動 fallback として使わない。

## 参照順

1. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\AGENTS.md`
2. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\AGENTS.md`
3. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\ALGORITHM.md`
4. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\WORKLOG.md`

## 実施範囲

- 通常UIから1回、京都工業ソースで本文生成する。
- Route B の実行判定を latest output / quality report / audit log / per-run artifact で確認する。
- Route A / writer-only / old rejected routes は使わない。
- 生成失敗時も Route A へ fallback しない。失敗理由と logs の flags を報告する。
- 実装修正は原則しない。Route B 経路の明確な不具合が見つかった場合だけ、最小差分で別途報告してから直す。

## 起動

作業場所:

```powershell
cd "C:\Users\横山裕明\Documents\実行環境準備完了\tetie"
```

既存サーバーが古い環境変数で起動している可能性があるため、可能なら force 起動する。

```powershell
.\techie-hub\start.bat force
```

確認URL:

```text
http://127.0.0.1:8080/
```

Kotomake launcher の log で `BLOGGEN_LLM_MODE: openai` が出ていることを確認する。

```powershell
Get-Content -Encoding UTF8 .\techie-hub\logs\kotomake.log -Tail 20
```

## UI入力

ソースは、過去ログ `notecode\logs\writer_only_generation\writer_only_20260616_235556_0bb025c1\run.json` / `brief.json` に残っている京都工業URLセットを使う。過去の writer-only 出力本文は使わない。

追加するURL:

```text
https://www.kyotokogyo.co.jp/
https://www.kyotokogyo.co.jp/about/coprof/
https://www.kyotokogyo.co.jp/about/history/
https://www.kyotokogyo.co.jp/service/
https://www.kyotokogyo.co.jp/strength/
```

記事生成カード:

```text
目的: 会社・サービス紹介
温度感: 真面目
想定読者: 就職活動中で、京都工業株式会社の歴史・事業・働く姿勢を知りたい人
短い指示: 京都工業株式会社について、就職活動中の読者が会社の背景、事業転換、データ入力やRPA支援の特徴を自然に理解できる記事にしてください。会社側の一人称で書き、ソースにない断定や比較優位は足さないでください。
```

`記事を生成` を押す。

## Route A 切り離しルール

- Route A を明示実行しない。
- `current_mainline_runner` / `newalgorithm_pipeline` / `simple_note_pipeline` を検証目的で呼ばない。
- Route B が失敗しても、Route A へ再実行しない。
- 旧 Route 0506 / old rejected routes / deepresearch 系を復活させない。
- 過去ログの writer-only 生成結果は、ソースURL確認用だけに使う。

## 検証コマンド

生成後、別 PowerShell で実行する。

```powershell
cd "C:\Users\横山裕明\Documents\実行環境準備完了\tetie"

$latestPath = ".\notecode\logs\latest_generation_output.json"
$qualityPath = ".\notecode\logs\latest_generation_quality_report.json"
$auditPath = ".\notecode\logs\generation_audit_log.jsonl"

$latest = Get-Content -Encoding UTF8 $latestPath | ConvertFrom-Json
$quality = Get-Content -Encoding UTF8 $qualityPath | ConvertFrom-Json

$latest | Select-Object run_id, success, blocked, route_id, route_b_used, route_a_used, fallback_used, old_routes_reopened, artifact_root
$quality.route_flags | ConvertTo-Json -Depth 10
Get-Content -Encoding UTF8 $auditPath -Tail 5
```

run_id が取れたら per-run artifact を確認する。

```powershell
$runId = $latest.run_id
$runRoot = ".\notecode\logs\route_b_generation\$runId"

Get-ChildItem $runRoot
Get-Content -Encoding UTF8 "$runRoot\route_b_summary.json" | ConvertFrom-Json | Select-Object route_id, route_source_workspace, external_llm_send, llm_client, source_count, genre_id
Get-Content -Encoding UTF8 "$runRoot\input_contract.json" | ConvertFrom-Json | Select-Object route_id, article_type, semantic_article_key, target_reader
```

旧 route 混入 scan:

```powershell
$runRoot = ".\notecode\logs\route_b_generation\$($latest.run_id)"
rg -n -F -e "current_mainline_runner" -e "newalgorithm_pipeline" -e "simple_note_pipeline" -e '"route_a_used": true' -e '"fallback_used": true' $runRoot .\notecode\logs\latest_generation_output.json .\notecode\logs\latest_generation_quality_report.json
```

この scan は no hits が期待値。

## 合格条件

- UI操作で記事本文が生成される。
- `latest_generation_output.json`:
  - `route_id = route_b_0506_structured_blog_v1`
  - `route_b_used = true`
  - `route_a_used = false`
  - `fallback_used = false`
  - `old_routes_reopened = false`
- `latest_generation_quality_report.json` の `route_flags` も同じ flags。
- `generation_audit_log.jsonl` の最新行でも `route_b_used=true`, `route_a_used=false`, `fallback_used=false`。
- `route_b_summary.json`:
  - `route_source_workspace = notecode/0506`
  - `external_llm_send = true`
  - `llm_client` が `LocalPipelineClient` ではない。
- `rg` scan で old route / Route A fallback の混入が出ない。

## 失敗時の扱い

- URL取得や robots / 403 / policy block で止まった場合:
  - Route A へ fallback しない。
  - `reason_code`, `message`, `route flags`, `run_id`, `source URL` を報告する。
- OpenAI key / `BLOGGEN_LLM_MODE` / client selection で止まった場合:
  - Route A へ fallback しない。
  - `techie-hub\logs\kotomake.log`, `notecode\logs\app.log`, latest JSON の flags を確認して報告する。
- 生成は成功したが flags が期待と違う場合:
  - 作業停止。
  - Route A fallback が混入した可能性として、対象 artifact と該当 keys を報告する。

## 完了報告テンプレート

```text
decision: route_b_ui_validated | blocked
ui_generation: success | blocked | failed
source_set: kyotokogyo_urls_from_writer_only_20260616_235556_0bb025c1
run_id:
route_id:
route_b_used:
route_a_used:
fallback_used:
old_routes_reopened:
route_source_workspace:
external_llm_send:
llm_client:
route_a_fallback_used: false
old_routes_reopened: false
latest_output_path:
quality_report_path:
audit_log_checked:
old_route_scan:
AGENTS_update_needed:
WORKLOG_update_needed:
```
