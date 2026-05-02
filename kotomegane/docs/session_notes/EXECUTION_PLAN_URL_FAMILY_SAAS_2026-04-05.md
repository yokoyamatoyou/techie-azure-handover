# URL Family SaaS Execution Plan 2026-04-05

更新日: 2026-04-05  
用途: `kotomegane` の URL 状態表示と prompt family 連携を、SaaS として価値が伝わる形へ 1 パッケージ進めるための完走用 runbook

## 0. Goal

今回の goal は次です。

1. `引用された / 検索ソースに出たが未引用 / 不明` の URL 状態を、非技術者でも誤読しにくい形で見せる
2. `managed prompt taxonomy` を `prompt family` 主体で読めるようにし、どの family で外部優勢かを分かるようにする
3. `main は軽く、detail で深掘り` を維持しながら、SaaS としての価値を上げる

## 1. Non-Negotiables

- 対象は `C:\tetie\kotomegane` のみ
- `aio2-main` と `notecode` は触らない
- `main` に重い新規 card / plot / table を追加しない
- user-facing は平易な日本語
- `検索に出た` は provider の `web_search source` に出た意味であり、一般検索順位ではない
- fallback 混在や parse failure、citation/source 不整合は `不明` を優先する
- 既存互換を壊さない

## 2. UX Guardrails

### Hick's Law

- 1ブロック内の主要選択肢は最大 3 個
- main の主 CTA は増やさない
- main の主結果 3 カード構成を崩さない
- 深い説明は detail 側へ送る

### Nielsen 10 Heuristics

- Visibility of system status:
  - 引用 / 未引用 / 不明 の状態を短く示す
- Match between system and the real world:
  - `citation` や `source_url` の内部語を前面に出さない
- Recognition rather than recall:
  - family 名、質問タイプ、判定意味を画面内で読めるようにする
- Aesthetic and minimalist design:
  - main に分析情報を積みすぎない
- Help users recognize, diagnose, and recover from errors:
  - `不明` は「失敗」ではなく「判定保留」として説明する

## 3. Source Of Truth

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\kotomegane\AGENTS.md`
3. `C:\tetie\kotomegane\docs\DOC_STATUS.md`
4. `C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md`
5. `C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
6. `C:\tetie\kotomegane\docs\LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
7. `C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
8. `C:\tetie\kotomegane\README.md`
9. `C:\tetie\kotomegane\storage.py`
10. `C:\tetie\kotomegane\llmo_core\openai_client.py`
11. `C:\tetie\kotomegane\analysis_core\source_evidence.py`
12. `C:\tetie\kotomegane\analysis_core\trends.py`
13. `C:\tetie\kotomegane\ui\detail_views.py`
14. `C:\tetie\kotomegane\ui\dashboard_views.py`
15. `C:\tetie\kotomegane\prompt_catalog.py`

## 4. Reading Rule

### Start で必ず読む

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\kotomegane\AGENTS.md`
3. `C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md`
4. この runbook

### Phase ごとに追加で読む

- 集計ロジックを触る直前:
  - `analysis_core/source_evidence.py`
  - `analysis_core/trends.py`
  - `prompt_catalog.py`
- UI を触る直前:
  - `ui/detail_views.py`
  - `ui/dashboard_views.py`
  - `docs/DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
- 保存や runtime を触る必要が出た時だけ:
  - `storage.py`
  - `llmo_core/openai_client.py`
  - `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`

### 原則読まない

- `archive/**`
- `docs/cross_product/**`
- 今回の Phase に関係ない session note

## 5. Runtime Rule

各 Phase は次の順で進める。

1. 実装
2. 自己テスト
3. 失敗時の自己修正
4. 完了条件判定
5. 次 Phase へ進む

自己テストを通過したら、ユーザーを待たずに次の Phase へ進む。

## 6. Error Handling Rule

同一問題でエラーやバグが出た場合:

1. まずローカル文脈で原因を切り分ける
2. 必要なら Web 検索で一次情報を探す
3. 最小差分で修正する

制限:

- 修正試行は 3 回まで
- Web 検索も 3 回まで
- 優先ソースは公式 docs、NN/g、Interaction Design Foundation

3 回失敗したら停止し、次を報告する。

1. 失敗した Phase
2. 実行コマンド
3. エラーメッセージ
4. 試した修正 1 / 2 / 3
5. 現在安全に残っている変更
6. 次に必要な判断

## 7. Phase Plan

### Phase 0: Preflight

目的:

- 正本 docs と現行 code の整合を確認する
- 今回の owner files と変更境界を固定する

Owner files:

- `storage.py`
- `llmo_core/openai_client.py`
- `analysis_core/source_evidence.py`
- `analysis_core/trends.py`
- `ui/detail_views.py`
- `ui/dashboard_views.py`
- `prompt_catalog.py`

Allowed edits:

- 原則コード変更しない
- 必要ならメモ程度の整理だけ

Tasks:

1. URL 状態モデルの現在値を確認する
2. `prompt family` と `prompt label` の保存・表示責務を確認する
3. `docs/session_notes/TOMORROW_FIRST_PROMPT_2026-04-05.md` の配置を確認する

Self-tests:

1. `.venv\Scripts\python.exe -m py_compile app.py analysis_lib.py storage.py`
2. `.venv\Scripts\python.exe -m py_compile analysis_core\source_evidence.py analysis_core\trends.py ui\detail_views.py ui\dashboard_views.py`
3. `.venv\Scripts\python.exe -c "import analysis_lib, app"`

Done criteria:

- owner files が明確
- import smoke が通る

### Phase 1: Information Design Freeze

目的:

- main と detail の責務を固定する
- SaaS としての見せ方を先に決める

Owner files:

- `ui/detail_views.py`
- `ui/dashboard_views.py`

Allowed edits:

- 文言方針メモ
- UI の責務整理
- この Phase では新しい重い UI 要素を足さない

Tasks:

1. main を `結論 / 次の一手` に固定する
2. detail を `何が起きているか -> 何を直すか -> 根拠URL` の順に固定する
3. family summary の文言を決める
4. `不明` の user-facing 文言を決める

Self-tests:

1. main に新カードを足さない方針になっていることを確認する
2. family summary が 1 ブロックで読める短さに収まることを確認する

Done criteria:

- UI の役割分担を 5 行程度で説明できる
- `main は軽く、detail で深掘り` が具体的な制約になっている

### Phase 2: Family Aggregation Logic

目的:

- `prompt family` 主体の source 集計を返せるようにする

Owner files:

- `analysis_core/source_evidence.py`
- 必要なら `analysis_core/trends.py`

Allowed edits:

- helper 追加は 1〜3 個まで
- DB migration はしない
- 互換 alias は維持してよい

Tasks:

1. family 単位の rollup を返す
2. `prompt label` を補助情報へ下げる
3. `dominance_label` を family 主体で返す
4. 必要なら `unknown_count` または `unknown_rate` を返す

Self-tests:

1. `.venv\Scripts\python.exe -m py_compile analysis_core\source_evidence.py analysis_core\trends.py`
2. `.venv\Scripts\python.exe -c "from config import load_config; from storage import Storage; from analysis_core.source_evidence import build_source_priority_actions; cfg=load_config(); db=Storage(); rows=db.list_recent_results(limit=40); print(len(build_source_priority_actions(rows, db.list_sources, cfg)))"`
3. family rollup が 1 件以上返ることを確認する

Done criteria:

- family summary が返る
- unknown を含んでも落ちない
- `searched_only` 条件が壊れていない

### Phase 3: Detail UI

目的:

- detail 側で family ごとの見え方を分かりやすくする

Owner files:

- `ui/detail_views.py`

Allowed edits:

- 既存 card 内の順序変更
- 補助文追加
- family summary の表示追加
- 新規の大セクションや複数 card の乱立は禁止

Tasks:

1. `質問タイプごとの見え方` を `質問の系統ごとの見え方` に寄せる
2. `prompt family` を主見出しにする
3. `prompt label` を補助情報にする
4. `不明` の説明を短く追記する
5. action と family のつながりが自然に読める順へ整える

Self-tests:

1. `.venv\Scripts\python.exe -m py_compile ui\detail_views.py`
2. `.venv\Scripts\python.exe -c "import ui.detail_views, app"`
3. family summary の読み順を目視確認する

Done criteria:

- detail を開けばどの系統で外部優勢かが短時間で分かる
- `引用 / 未引用 / 不明` の意味が誤読されにくい

### Phase 4: Main Copy Adjustment

目的:

- main を重くせずに SaaS 価値を少し強める

Owner files:

- `ui/dashboard_views.py`

Allowed edits:

- 文言差し替えのみ
- 新規 plot / table / card は禁止

Tasks:

1. `次に見直すポイント` の文言に family 観点を織り込めるか確認する
2. 既存の `source 根拠ベースの優先アクション` が family 主体で自然に読めるようにする

Self-tests:

1. `.venv\Scripts\python.exe -m py_compile ui\dashboard_views.py`
2. `.venv\Scripts\python.exe -c "import ui.dashboard_views, app"`
3. main の 3 カード構成と CTA 数が変わっていないことを確認する

Done criteria:

- main は重くなっていない
- `現状把握 -> 次の一手` が前より読みやすい

### Phase 5: Docs Sync

目的:

- current decision を docs に反映する

Owner files:

- `README.md`
- `docs/CURRENT_STATE_2026-03-30.md`

Allowed edits:

- 今回の decision に直接関係する行だけ

Tasks:

1. `prompt family` 主体の current state を反映する
2. `detail で深掘り` の current decision を必要最小限で追記する

Self-tests:

1. docs と code が矛盾しないことを確認する

Done criteria:

- docs が今回の実装方針を正しく示す

### Phase 6: Final Verification

目的:

- 一連の変更が局所的に壊れていないことを確認する

Self-tests:

1. `.venv\Scripts\python.exe -m py_compile app.py analysis_lib.py storage.py analysis_core\source_evidence.py analysis_core\trends.py ui\detail_views.py ui\dashboard_views.py`
2. `.venv\Scripts\python.exe -c "import analysis_lib, app; from analysis_core.source_evidence import build_source_priority_actions"`
3. family 集計のローカル smoke
4. 可能なら `http://127.0.0.1:8083/` の HTTP 200

Done criteria:

- import と py_compile が通る
- family summary と action が 1 件以上返る
- main/detail の読み順が守られている

## 8. End Report Format

完了時は次を報告する。

1. 読んだ正本ファイル
2. 実施した Phase
3. 変更したファイル
4. UX 原則の適用点
5. 自己テスト結果
6. 3回自己修正が発生した箇所
7. 未完了項目
8. `AGENTS / CURRENT_STATE / README / WORKLOG` 更新有無
