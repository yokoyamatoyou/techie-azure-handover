# ux_heuristic_audit_followup_2026-04-13 PROGRESS

## Current Goal

- `aio2-main` の UI を、2026-04-13 のヒューリスティック監査で見つかった P1/P2 を別ウインドウで順次解消できる package にする

## Current Status

- Package status: completed
- Current phase: complete
- Status: completed
- Owner scope:
  - closeout complete
- Attempts used: 1/3
- Web search attempts used: 0/3
- Next action:
  - none

## Baseline Findings

- input phase は空 URL のみ強く見ており、URL 形式不備の事前防止が弱い
- analysis 実行後は user control が薄く、自動遷移が主導権を奪う
- dashboard 上段は案内が中心で、commercial な価値訴求が薄い
- saved workspace は non-technical user に対して tab 選択コストが高い
- `実装・設定` は actionable / reference が 1 スクロールに混在している

## Success Bar

- input error prevention が実行前に機能する
- analysis 後の移動と滞在を user が選べる
- home first view で価値と行動が伝わる
- saved workspace の primary navigation が軽くなる
- `実装・設定` の停止基準が明確になる
- regression / live verify が green

## Phase Ledger

| Phase | Status | Attempts | Web | Evidence | Next |
|------|--------|----------|-----|----------|------|
| 0 package bootstrap | completed | 1/3 | 0/3 | docs skeleton 作成 | 1 |
| 1 baseline and success lock | completed | 1/3 | 0/3 | compile pass + `/` `/runs/84` 200 + scope/success lock | 2 |
| 2 input guardrails | completed | 1/3 | 0/3 | URL 正規化 helper + inline error copy + regression pass | 3 |
| 3 analysis control recovery | completed | 1/3 | 0/3 | auto-open toggle + `今は移動しない` 導線 + regression pass | 4 |
| 4 dashboard value proposition | completed | 1/3 | 0/3 | value cards 化 + latest outcome surfacing + regression pass | 5 |
| 5 workspace IA simplification | completed | 1/3 | 0/3 | primary tab 4件 + secondary expansion 化 | 6 |
| 6 implementation/reference split | completed | 1/3 | 0/3 | `ここまで見れば十分` stop message + reference 後退 | 7 |
| 7 verification and closeout | completed | 1/3 | 0/3 | final compile/pytest/live route verify + WORKLOG 更新 | complete |

## Per-Phase Execution Record

### Phase 0

- Status:
  - completed
- Implementation:
  - `README.md`, `TASK.md`, `PROGRESS.md`, `ROLLBACK.md`, `EXECUTION_PROMPT.md`, `artifacts\README.md` を作成
- Self-tests:
  - doc completeness review pass
- Evidence:
  - package path: `C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\`
- Next action:
  - Phase 1 baseline lock

### Phase 1

- Status:
  - completed
- Implementation:
  - 監査 findings を `README.md` / `TASK.md` / `ROLLBACK.md` と current mainline に照合し、success / non-scope / phase order を確定
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py`
    - PASS
  - `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8081/`
    - 200
  - `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8081/runs/84`
    - 200
- Evidence:
  - baseline として `入力時バリデーション弱い / 自動遷移が強い / dashboard 価値訴求が弱い / saved workspace が6タブ同列 / 実装・設定の停止基準が弱い` を確認
- Next action:
  - Phase 2 input guardrails

### Phase 2

- Status:
  - completed
- Implementation:
  - `nicegui_app.py` に `_normalize_input_url()` / `_validate_analysis_input_url()` を追加
  - bare host 入力時は `https://` を補い、対象URL / 比較競合URLの形式不備を実行前に inline 表示するよう変更
  - main/competitor 同一URLの比較実行も事前停止
  - input note を `形式不備は実行前に知らせる` 文言へ変更
- Self-tests:
  - compile gate PASS
  - targeted regression gate PASS (`38 passed`)
- Evidence:
  - `tests/test_dashboard_ui.py` に URL 正規化 / optional competitor / invalid format の regression を追加
  - live route 200 は維持
- Next action:
  - Phase 3 analysis control recovery

### Phase 3

- Status:
  - completed
- Implementation:
  - `nicegui_app.py` に `完了後に保存結果を開く` toggle を追加
  - 分析中に `今は移動しない` で stay-on-page へ切り替えられる導線を追加
  - progress / completion / saved status copy を auto-open choice に応じて切り替える helper を追加
- Self-tests:
  - compile gate PASS
  - targeted regression gate PASS (`39 passed`)
- Evidence:
  - auto-open helper copy の regression を `tests/test_dashboard_ui.py` に追加
  - auto navigation は維持しつつ、user choice で stay-on-page に変更可能になった
- Next action:
  - Phase 4 dashboard value proposition

### Phase 4

- Status:
  - completed
- Implementation:
  - `core/ui/dashboard.py` の上段カードを説明中心から value proposition card へ再編
  - `このソフトで分かること` と `最近の成果 / 次の入口` の2系統に変更
  - rows があるときは最新保存結果の URL / score summary / priority / first action を surfacing
- Self-tests:
  - compile gate PASS
  - targeted regression gate PASS (`40 passed`)
- Evidence:
  - `build_dashboard_value_cards()` を追加し、`tests/test_dashboard_ui.py` で latest outcome surfacing を固定
- Next action:
  - Phase 5 workspace IA simplification

### Phase 5

- Status:
  - completed
- Implementation:
  - `core/ui/panels.py` の saved workspace を `サマリー / やること / 文章改善 / 実装・設定` の primary tab に整理
  - `エンジニア向け` と `履歴と比較` は `補足メニュー` の expansion へ後退
  - `まずは サマリー → やること → 実装・設定` の主導線を追加
- Self-tests:
  - compile gate PASS
  - targeted regression gate PASS (`41 passed`)
- Evidence:
  - `_build_workspace_tab_plan()` を追加し、primary / secondary 分離を `tests/test_characterization_ui.py` で固定
- Next action:
  - Phase 6 implementation/reference split

### Phase 6

- Status:
  - completed
- Implementation:
  - `core/ui/panels.py` の `実装・設定` に `ここまで見れば十分` stop message を追加
  - actionable count / refresh count に応じて、先に見るべき範囲を短文で提示
  - `参考` を `参考（後で見る）` に変更し、参考情報の後退配置を明示
- Self-tests:
  - compile gate PASS
  - targeted regression gate PASS (`41 passed`)
- Evidence:
  - `_build_implementation_stop_message()` を追加し、`tests/test_characterization_ui.py` で 3 ケース固定
- Next action:
  - Phase 7 verification and closeout

### Phase 7

- Status:
  - completed
- Implementation:
  - final compile / regression / live route verify を再実行
  - `PROGRESS.md` を complete 状態へ更新
  - `WORKLOG.md` に follow-up 実装内容を追記
- Self-tests:
  - `C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py`
    - PASS
  - `C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_dashboard_ui.py tests\test_characterization_ui.py tests\test_analysis_run_service.py tests\test_executive_summary.py`
    - PASS (`41 passed`)
  - `C:\tetie\techie-hub\start.bat force`
    - PASS
  - `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8081/`
    - 200
  - `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8081/runs/84`
    - 200
- Evidence:
  - shell 経由の route HTML では NiceGUI hydration の都合で新文言文字列までは安定取得できなかったが、route availability と regression は green
- Next action:
  - monitor only

## Residual Notes

- shell-only 環境のため、desktop / mobile の最終視認チェックは route availability + regression + copy helper test まで
- ブラウザ実機での文字折り返し / focus ring / mobile 崩れは、必要なら追加で目視確認するとより確実

## Failure Log

- Phase 2 / local fix
  - failure:
    - targeted regression で `tests/test_analysis_run_service.py` の旧 snapshot 期待値が current snapshot refresh contract と不一致
  - tried fix:
    - current schema version / measured note contract に合わせて test fixture と assertion を更新
  - result:
    - targeted regression pass

## User Report Template

失敗停止時は最低限これを user に返す。

- current phase
- failure summary
- attempts used
- web search attempts used
- tried fixes
- likely cause
- rollback need / no need
- next decision required from user
