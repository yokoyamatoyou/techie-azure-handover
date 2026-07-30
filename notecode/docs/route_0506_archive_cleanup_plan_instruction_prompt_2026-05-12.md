# Route 0506 Archive Cleanup Plan Instruction Prompt 2026-05-12

以下を新しい Codex 作業ウィンドウにそのまま貼り付けてください。

```text
cwd: C:\tetie\notecode

あなたは C:\tetie\notecode の Route 0506 main route stabilization を引き継ぐ Codex です。
このウィンドウの目的は、506ルート実装に不要なコードを今後アーカイブするための read-only 計画を作ることです。

重要:
- product code を変更しない。
- ファイルやディレクトリを移動・削除しない。
- Route A を再生成しない。
- URL refetch しない。
- API send しない。
- Route A fallback を追加しない。
- QA threshold / repair_acceptance を緩めない。
- old rejected routes を戻さない。
- raw full source_documents pass で解決しない。
- prompt/persona を肥大化させない。
- 1 issue = 1 narrow hypothesis = 1 owner scope を守る。

最初に必ず読む:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\WORKLOG.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode\docs\directory_map.md
6. C:\tetie\notecode\logs\route_0506_main_route_replacement_20260511\decision.md
7. C:\tetie\notecode\logs\route_0506_main_route_replacement_20260511\fail_safe_check.md
8. C:\tetie\notecode\logs\route_0506_main_route_replacement_20260511\persona_final_check.md
9. C:\tetie\notecode\logs\module_deadcode_bloat_inventory_20260512\inventory.md
10. C:\tetie\notecode\logs\module_deadcode_bloat_inventory_20260512\decision_before_edit.md
11. C:\tetie\notecode\logs\module_deadcode_bloat_inventory_20260512\unreferenced_python_candidates.json
12. C:\tetie\notecode\logs\module_deadcode_bloat_inventory_20260512\import_graph_by_package.json

現在の確認済み状態:
- 2026-05-11 に Route 0506 は UI body default main route へ切り替え済み。
- default route: route_0506_structured_blog_ui_v1
- explicit legacy opt-out: NOTECODE_UI_BODY_ROUTE=route_a
- Route A fallback: false
- Route 0506 は source/security/quality blocker で fail-closed。
- category 05 / 07 は source contract が満たせない場合、生成前 confirmation/source gate で止める。
- 昨日の Route 0506 確立記録は C:\tetie\notecode\logs\route_0506_main_route_replacement_20260511\ に残っている。
- notecode 固有 WORKLOG は C:\tetie\notecode\WORKLOG.md。
- 責務別ディレクトリ図は C:\tetie\notecode\docs\directory_map.md。

今回作る成果物:
- C:\tetie\notecode\docs\route_0506_archive_cleanup_plan_2026-05-12.md
- 必要なら read-only artifact root:
  C:\tetie\notecode\logs\route_0506_archive_cleanup_plan_readonly_20260512\

成果物に必ず含める:
1. Current Route 0506 contract
   - default route
   - Route A opt-out
   - no fallback
   - fail-closed gates

2. Archive policy
   - いま移動してよいもの、まだ移動してはいけないものを分ける。
   - 今回は plan-only。実移動は禁止。

3. Classification table
   次の分類で候補を整理する。
   - active_runtime
   - route_0506_main_runtime
   - route_a_legacy_opt_out
   - local_0506_reference
   - test_or_fixture
   - docs_or_handoff
   - archive_candidate
   - delete_never_without_user_approval

4. First archive candidates
   既存 inventory から特に次を確認する。
   - C:\tetie\notecode\backups\...
   - C:\tetie\notecode\docs\新しいフォルダー (5)\*.py
   - rejected route / snapshot 系
   ただし、削除や移動はしない。候補として根拠を書く。

5. Do-not-archive list
   最低限、次は archive しない。
   - C:\tetie\notecode\note\route_0506_ui_bridge.py
   - C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
   - C:\tetie\notecode\note\route_0506_stage_output_guard.py
   - C:\tetie\notecode\note\route_0506_security_gate.py
   - C:\tetie\notecode\note\route_0506_usage_ledger.py
   - C:\tetie\notecode\0506\
   - C:\tetie\notecode\note\tests\test_route_0506*.py
   - Route A legacy opt-out に必要な current_mainline_runner / newalgorithm_pipeline / simple_note_pipeline

6. Responsibility split recommendation
   ベストプラクティス判断として、次のどちらを優先するか明記する。
   - Route 0506 を先に固める
   - 不要コード archive を先に行う
   現時点の推奨は「Route 0506 を先に固める。archive は read-only plan まで」です。

7. Execution phases
   phase を細かく分ける。
   - Phase 0: no-code plan
   - Phase 1: archive candidate verification
   - Phase 2: one-owner archive move proposal
   - Phase 3: optional actual archive move only after user approval
   - Phase 4: tests and directory map / WORKLOG sync

8. Validation / rollback
   - no API
   - no route generation
   - static reference checks only
   - actual archive move時は import smoke / focused pytest / route 0506 tests が必要
   - rollback は archive move manifest から戻せる形にする

9. Final decision contract
   最後に以下を出す。
   decision: needs_next_owner | blocked
   artifact_root:
   product_code_changed: false
   api_send_count: 0
   archive_move_performed: false
   route_a_regenerated: false
   url_refetched: false
   route_a_fallback_used: false
   threshold_relaxed: false
   repair_acceptance_relaxed: false
   prompt_bloat: none | found
   module_bloat: found
   next_one_owner:
   AGENTS_update_needed:
   WORKLOG_update_needed:

推奨 next_one_owner:
- route_0506_archive_cleanup_plan_readonly

エラーで停止した場合:
- その場で修正を広げない。
- どのファイルを読み、どのコマンドで止まったかを書く。
- C:\tetie\notecode\logs\route_0506_archive_cleanup_plan_readonly_20260512\blocked.md を作成できる場合は、そこに error text / last completed step / next retry step を残す。
- blocked.md が作れない場合は、チャットに同じ内容を報告する。
```
