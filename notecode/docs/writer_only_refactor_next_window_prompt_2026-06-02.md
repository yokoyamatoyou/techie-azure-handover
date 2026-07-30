# Next Window Prompt: writer-only refactor / Route 0506 isolation

以下を別ウインドウのCodexへ貼って作業を開始する。

```text
C:\tetie\notecode を、writer-only UI を主経路として軽量化してください。

重要:
- いきなり Route 0506 / current_mainline / newalgorithm / simple_note_pipeline を大量削除しないでください。
- git前提にしないでください。
- まず read-only で依存関係、起動時import、UI到達可能性、ログ出力先を確認してください。
- ユーザーの目的は、失敗アルゴリズムだった Route 0506 系を現行UIから完全に別扱いにし、通常起動と通常生成をシンプルにすることです。
- 現在の本文生成主経路は writer-only です。Route 0506 を復活させないでください。
- Route 0506 のファイル群は、削除より先に archive plan / disabled legacy package として扱ってください。
- 大量移動や削除を行う前に、候補一覧、参照根拠、戻し方を artifact に残してください。

最初に読むファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\WORKLOG.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\notecode\docs\writer_only_ui_port_2026-06-02.md
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\writer_only_service.py
- C:\tetie\notecode\note\writer_only_source_bundle.py
- C:\tetie\notecode\note\writer_only_brief.py
- C:\tetie\notecode\note\writer_only_openai_adapter.py
- C:\tetie\notecode\note\writer_only_evaluator.py
- C:\tetie\notecode\note\writer_only_config.py

現在の確認済み状態:
- UI上の可視ボタンは `+ 追加` と writer-only の `記事を生成`。
- `記事の向き先` / `記事の前提` など旧 current-mainline wizard は表示されない。
- `note_writer_app.py` は `note.route_0506_ui_bridge` を起動時importしない。
- `import note.note_writer_app` 後、`sys.modules` に `route_0506` 系moduleが載らないことを確認済み。
- Route 0506 ファイル群はディスク上に残っている。
- dev server確認済み: `http://127.0.0.1:8095/`

今回の目標:
1. writer-only UIを通常起動・通常生成の唯一の本文生成経路として保つ。
2. Route 0506 系を現行UI/通常起動から完全に分離する。
3. Route 0506 ファイル群を削除可能/アーカイブ可能な候補として、安全に分類する。
4. current_mainline / newalgorithm / simple_note_pipeline のうち、writer-only UIの通常起動に不要な起動時importを減らす。
5. 変更後も `+ 追加` -> `記事を生成` -> writer-only source policy -> source_bundle -> brief -> writer -> smoke -> Markdown preview が動くことを確認する。

絶対に避けること:
- Route 0506 を再び default main route にする。
- Route A fallback を戻す。
- repair loop を戻す。
- quality pipeline を writer-only 本文生成の本線へ戻す。
- source full_text をLLMへ渡す。
- モデル名やAPIパラメータをアプリ本体やpromptに直書きする。
- `.env` や実APIキーを触る、ログへ出す。
- `C:\tetie\notecode` 外へ勝手に大量コピーする。
- 広範囲削除を根拠なしに行う。

推奨artifact root:

```text
C:\tetie\notecode\logs\writer_only_refactor_route_0506_isolation_20260602\
```

最低限作るartifact:
- `inventory.md`
- `startup_import_before.txt`
- `startup_import_after.txt`
- `route_0506_reference_scan.txt`
- `current_mainline_reference_scan.txt`
- `archive_candidates.json`
- `decision_before_edit.md`
- `validation_summary.md`

最初のread-only確認コマンド例:

```powershell
rg -n "route_0506|ROUTE_0506|run_route_0506|resolve_ui_body_route_selection" C:\tetie\notecode\note --glob "*.py" --glob "!**/__pycache__/**"
rg -n "current_mainline|newalgorithm_pipeline|simple_note_pipeline|MinimalPipeline" C:\tetie\notecode\note\note_writer_app.py
py -3.11 - <<適切なPowerShell形式で実行し、import note.note_writer_app 後の sys.modules を確認する>>
```

PowerShellでは heredoc を bash 形式で使わず、必要なら次の形にする:

```powershell
@'
import sys
import note.note_writer_app
print("\n".join(sorted(name for name in sys.modules if "route_0506" in name)) or "no route_0506 modules loaded")
'@ | py -3.11 -
```

実装の進め方:
1. read-only inventoryを作る。
2. `note_writer_app.py` の通常表示/通常生成で不要な起動時importを1グループずつ外す。
3. 各グループごとに `py_compile` と focused tests を実行する。
4. Route 0506ファイル群は、まず通常起動から参照されないことを証明する。
5. 削除ではなく、次のどちらかを提案する:
   - archive move案: `C:\tetie\notecode\archive\writer_only_refactor_route_0506_20260602\...`
   - disabled legacy package案: `note\legacy_route_0506\...` へ分離し、通常import不可にする
6. archive moveを実施する場合は、移動前後で参照scan、hash、起動確認を残す。
7. 1 turnで不安が残る場合は、archive plan作成までで止める。

優先順位:
1. `note_writer_app.py` の Route 0506 起動時依存を完全にゼロにする。
2. writer-only UIに不要な旧 wizard / current_mainline import を減らす。
3. Route 0506ファイル群のarchive planを作る。
4. ユーザー承認がある場合だけ、Route 0506ファイル群をarchiveへ移動する。

検証コマンド:

```powershell
py -3.11 -m py_compile note\note_writer_app.py note\writer_only_service.py note\writer_only_source_bundle.py note\writer_only_brief.py note\writer_only_openai_adapter.py note\writer_only_evaluator.py note\writer_only_config.py
py -3.11 scripts\validate_writer_only_config.py
py -3.11 -m pytest note\tests\test_writer_only_generation.py -q
py -3.11 -m pytest note\tests\test_note_writer_app_generation_execution_helpers.py note\tests\test_note_writer_app_post_success_helpers.py -q
```

UI確認:

```powershell
$env:PORT="8095"
py -3.11 run_kotomake.py
```

Browserで確認すること:
- `http://127.0.0.1:8095/` が開く。
- 旧 `記事の向き先` / `記事の前提` が表示されない。
- 可視ボタンが `+ 追加` と `記事を生成` を中心に整理されている。
- writer-onlyの `記事を生成` が主ボタンである。

完了時の報告:
- 変更ファイルをファイル単位で列挙。
- どのimport/依存を外したか。
- Route 0506が通常起動で読まれていない証拠。
- archive/delete候補と、まだ削除していない理由。
- 実行した検証コマンドと結果。
- 起動URLとPID。
- AGENTS/WORKLOG更新の要否。

報告フォーマット:

```text
decision: fixed_continue_main | archive_plan_only | blocked
artifact_root:
product_code_changed:
route_0506_startup_import: false
route_0506_visible_ui: false
route_0506_generation_reachable: false
route_a_fallback_used: false
repair_used: false
quality_pipeline_used_for_body: false
changed_files:
tests:
browser_check:
archive_candidates:
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```
```
