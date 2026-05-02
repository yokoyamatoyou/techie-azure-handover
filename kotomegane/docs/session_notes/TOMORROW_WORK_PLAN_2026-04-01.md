# Tomorrow Work Plan 2026-04-01

## 0. Purpose

この文書は、2026-04-01 に同日で進める次の3系統作業の詳細計画です。

- `kotomegane` の高付加価値化
- `aio2-main` / `notecode` / `kotomegane` の UI デザイン統一
- `notecode` current mainline の機能向上判断と narrow 改修

AGENTS.md は入口とルール提示に限定し、phase、停止条件、完了条件、更新順はこの文書を正本にします。
次回の開始時にそのまま貼る prompt は C:\tetie\kotomegane\docs\TOMORROW_FIRST_PROMPT_2026-04-01.md を使います。

## 1. Same-Day Scope

### Track A: kotomegane 高付加価値化

前提:
- `引用シェア`
- `質問ごとの揺れ幅`
- 主画面のノイズ退避
- semantic color 分離

は実装済み。

明日の対象は次の残件です。

1. Intent Map
   - 各質問を `比較 / 料金 / FAQ / 事例 / 地域 / 指名 / how-to` に分類する
   - 上段サマリーを「どの意図で勝てていないか」に寄せる
2. Page Gap Navigator
   - `recommended_actions` を制作タスクに変換する
   - `比較ページ不足 / 料金根拠不足 / FAQ不足 / 地域LP不足 / 実績不足` のように落とす
3. Budget Guardrail
   - 実行前コスト見積り
   - 日次上限
   - stop condition
   - `score / cost` 系の判断値
4. Owned-only Audit
   - 市場全体観測とは別に、自社ドメインのみで答えられるかを見るモード
5. Page Brief Generator
   - 明示ボタンでだけ生成する軽量 brief
   - `仮タイトル / 見出し / FAQ / 比較表 / CTA` を返す

### Track B: 3製品 UI 統一

対象:
- `C:\tetie\aio2-main`
- `C:\tetie\notecode`
- `C:\tetie\kotomegane`

基準文書:
- `C:\tetie\kotomegane\docs\UI_UNIFICATION_PLAN_2026-03-31.md`

明日の到達点:
- 3製品を並べたときに同一 SaaS 群と分かる状態まで寄せる
- トークン、ナビ、ヒーロー、CTA、カード階層、バッジ、表ヘッダ、semantic color を統一する

### Track C: notecode 機能向上

前提:
- `notecode` は current mainline の narrow residual 管理が最優先
- 先に大きな新機能へ広げない
- `3 reruns -> artifact review -> deepresearch -> optional 1 hypothesis` の順を守る

参照:
- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-01.md`
- `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md`

## 2. Read Order For Tomorrow

### 2.1 Common First Read

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\kotomegane\AGENTS.md`
3. `C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md`
4. `C:\tetie\kotomegane\docs\DOC_STATUS.md`
5. `C:\tetie\kotomegane\docs\TOMORROW_WORK_PLAN_2026-04-01.md`
6. `C:\tetie\kotomegane\docs\UI_UNIFICATION_PLAN_2026-03-31.md`

### 2.2 Track A Read

1. `C:\tetie\kotomegane\README.md`
2. `C:\tetie\kotomegane\docs\research\deep-research-report (13).md`
3. `C:\tetie\kotomegane\docs\research\research１.txt`
4. `C:\tetie\kotomegane\app.py`
5. `C:\tetie\kotomegane\analysis_lib.py`
6. `C:\tetie\kotomegane\storage.py`
7. `C:\tetie\kotomegane\config.py`
8. `C:\tetie\kotomegane\llmo_client.py`

### 2.3 Track B Read

1. `C:\tetie\kotomegane\docs\UI_UNIFICATION_PLAN_2026-03-31.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\nicegui_app.py`
4. `C:\tetie\notecode\AGENTS.md`
5. `C:\tetie\notecode\note\note_writer_app.py`
6. `C:\tetie\kotomegane\app.py`

### 2.4 Track C Read

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\notecode\ALGORITHM.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-01.md`
5. `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md`
6. `C:\tetie\notecode\GPTPRO.txt`

## 3. Phase Plan

### Phase 0: Preflight

目的:
- 3トラックを同日に回す前に baseline を揃える

やること:
1. 3製品の現行 UI スクリーンショットを保存する
2. `kotomegane` の現在DBと主要画面を開けることを確認する
3. `aio2-main` と `notecode` の current mainline が起動可能かだけを見る
4. `notecode` の compare residual 用の artifact path を確認する
5. 明日触るファイル owner を repo ごとに分ける

完了条件:
- baseline screenshot が3製品分ある
- 参照ドキュメントがすべて開ける
- current blocker がある場合、Phase 1 前に記録済み

### Phase 1: kotomegane 高付加価値化

実装順:
1. Intent Map
2. Page Gap Navigator
3. Budget Guardrail
4. Owned-only Audit
5. Page Brief Generator

#### 1. Intent Map

対象ファイル:
- `app.py`
- `analysis_lib.py`
- 必要なら `storage.py`

やること:
- 質問テキストから意図カテゴリを分類する
- 一覧、上段サマリー、グラフ補助文に意図を出す
- `どの意図で負けているか` を最初に読めるようにする

停止条件:
- 分類が曖昧で誤判定だらけなら、UI露出は限定して内部集計止まりにする

完了条件:
- 質問ごとに少なくとも1つの意図ラベルがつく
- 上段に `弱い意図クラスタ` が出る

#### 2. Page Gap Navigator

対象ファイル:
- `app.py`
- `analysis_lib.py`
- `llmo_client.py` の action text 整形部が必要なら修正

やること:
- アクション提案を制作物単位へ変換する
- `何を直すか` を abstract ではなく page type で出す

完了条件:
- 施策が `制作着手できる粒度` で見える
- マーケ担当と制作者の両方が読める

#### 3. Budget Guardrail

対象ファイル:
- `config.py`
- `analysis_lib.py`
- `app.py`
- 必要なら `llmo_client.py`

やること:
- 実行前概算
- 1日上限
- 上限超過時の停止または警告
- `visibility / cost` 系の軽い指標

停止条件:
- live pricing と config pricing がずれている場合は、実装より先に価格前提を揃える

#### 4. Owned-only Audit

対象ファイル:
- `app.py`
- `analysis_lib.py`

やること:
- 市場観測モードと自社確認モードを切り替える
- サイト改修後に `自社だけで答えられるか` を検証できるようにする

完了条件:
- UI 上でモードが分かる
- 結果一覧と上段サマリーの意味が混ざらない

#### 5. Page Brief Generator

対象ファイル:
- `app.py`
- `llmo_client.py`

やること:
- 行選択または質問選択で brief 生成
- 常時生成はしない
- 手動ボタンでだけ呼ぶ

完了条件:
- コストを増やしすぎずに brief を出せる
- 制作着手メモとしてそのまま使える

### Phase 2: UI 統一実装

実装順:
1. 共通 token 名を固定
2. フォントを `Sora + Noto Sans JP` に揃える
3. ナビ / ヒーロー / CTA / バッジ / カード階層を揃える
4. グラフと semantic color を揃える
5. 3製品横並びの screenshot 比較を行う

#### 2-1. 共通 token 固定

対象:
- `C:\tetie\aio2-main\nicegui_app.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\kotomegane\app.py`

やること:
- `--bg`
- `--surface`
- `--text`
- `--brand`
- `--self`
- `--competitive`
- `--external`
- `--border`
- `--shadow`

を同じ名前と役割に揃える

#### 2-2. 見た目文法統一

やること:
- top nav height を揃える
- hero の情報量と余白を揃える
- primary / secondary / detail card の階層差を揃える
- table header と expansion の見え方を揃える

#### 2-3. 視覚 QA

やること:
- desktop 3画面比較
- mobile 3画面比較
- `同じ会社の SaaS` に見えるかを確認

完了条件:
- CTA と status の色意味が3製品で一致
- card hierarchy が見ただけで分かる
- フォントの印象差が大きく残らない

### Phase 3: notecode current mainline gate

この phase は、UI 統一より後回しでもよい。  
ただし同日内に着手するなら、必ず narrow rule を守る。

実行順:
1. compare residual rerun を 3 回
2. artifact review
3. deepresearch
4. optional 1 hypothesis
5. keep / rollback 判定

#### 3-1. 3 reruns

コマンド:
- `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --live --genres comparative_review`

確認項目:
- `short_gate_passed=5/5`
- rubric の落ち込み有無
- thin section の再発 role
- raw axis token 漏れ
- patch path 発火有無

#### 3-2. deepresearch gate

条件:
- 3 reruns が終わるまで research に進まない
- 一次情報 / 公式情報 / 研究メモに限定
- compare article の section density と 2000字前後 cadence に限定

#### 3-3. optional hypothesis

許可条件:
- residual が surface 問題に見える
- meaning-layer 拡張を伴わない
- owner を局所に閉じられる

禁止:
- prompt accretion
- compare 専用 module の増設
- unrelated genre への拡張
- `human_resonance*` の改変

完了条件:
- keep / rollback が明確
- next narrow slice が1つに絞られている

### Phase 4: Documentation And Close

やること:
1. repo ごとの current state 更新
2. README 更新
3. AGENTS は guide のまま維持
4. plan doc と UI plan doc に差分が出たら更新
5. 必要なら WORKLOG 更新

## 4. Priority Order Across The Whole Day

最優先:
1. `kotomegane` 高付加価値化の骨格
2. 3製品 UI 統一の token と shell

条件付き優先:
3. `notecode` compare residual の rerun / review / deepresearch

後回し:
4. `kotomegane` Page Brief Generator
5. `notecode` の gate を超えた後の追加改善

## 5. Do-Not Rules

- `AGENTS.md` に詳細 TODO を増殖させない
- 3製品統一の前に repo ごとの独自色を増やさない
- `notecode` で gate を飛ばして機能拡張へ進まない
- `kotomegane` でコストの重い生成を常時実行にしない
- UI 統一を理由に、既存の current success path を壊さない

## 6. Deliverables

### kotomegane

- Intent Map
- Page Gap Navigator
- Budget Guardrail
- Owned-only Audit
- 必要なら Page Brief Generator

### UI 共通

- shared token 適用
- shared nav / hero / CTA / card hierarchy
- 3製品比較 screenshot

### notecode

- rerun artifact 3回分
- residual 判定
- deepresearch の要点
- keep / rollback / next narrow slice

## 7. End-Of-Day Report Format

最終報告では必ず次を出す。

1. 読んだ正本ファイル
2. 実施した phase
3. 変更した repo / file
4. keep した変更
5. rollback した変更
6. 残件
7. AGENTS / WORKLOG / plan doc 更新の有無

## 8. Success Condition

次の3点がそろえば、その日の作業は成功とみなす。

- `kotomegane` が `判断 -> 制作着手` に一段近づいている
- `aio2-main` / `notecode` / `kotomegane` が同一 SaaS 群に見える
- `notecode` の current mainline が gate を守ったまま次の narrow slice に進める

