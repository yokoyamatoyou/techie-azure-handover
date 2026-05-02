# naturalness recovery follow-up plan 2026-04-09

参照ルール: `C:\tetie\AGENTS.md`, `C:\tetie\notecode\AGENTS.md`

## 今日の要約

- UI 通常経路の本文 owner を `note_writer_app -> current_mainline_runner -> newalgorithm_mainline -> simple_note_pipeline` に再統一した
- `body_generation_experiment` を production path から外し、UI 選択肢だけでは hidden route に入らない状態へ戻した
- `company_introduction` は source が十分ある場合のみ `core_message` 欠落で stop しないように調整した
- 骨格 inspection 4 ケースで、primary failure point は `focus_bundle / must_cover / discourse_plan` 側だと確認した
- `main_focus` instruction 圧縮と `topic_seed` broken fragment clamp を入れた
- branding/company-intro 向けに `私たち` lead と便利句反復を抑える surface guard を追加した
- その後の live 比較で、AI 定型句と一人称は改善したが、明示主語の多さと段落均一感は残った
- 最後に `company_introduction` 専用の repeated company subject clamp と paragraph rebalance を formatter に追加した

## 主要変更

### routing / production path

- `branding/company_introduction` の自動 section route を外し、通常 UI 経路を single-pass mainline に戻した
- `announcement` も通常 UI 選択では hidden experiment route に入らない状態を維持した

### input / UI clarity

- `company_introduction` の話者 auto 表示を曖昧に読みにくい文言から調整した
- `core_message` helper / placeholder を route 別の具体例へ変更した
- `core_message` 必須判定は UI ローカルではなく contract 側を正本に寄せた

### skeleton / discourse

- `main_focus` の instruction-like 長文化を compact proposition に戻す self-check を追加した
- `topic_seed` の broken short fragment を `must_cover / source anchor / heading` に戻す clamp を追加した
- 4 ケースの bone inspection を作成し、`support_points` / `topic_seed` / late-section anchoring の劣化を確認した

### surface / style

- `company_introduction` の lead で `私たち...` を優先しないよう変更した
- `だからこそ / たとえば / 輪郭` 系の便利反復を prompt/guard で抑制した
- source が薄い `announcement` は `adaptive` target chars を短めに寄せた
- `company_introduction` 専用に repeated company subject clamp と paragraph rebalance を追加した

## live compare の現状

### 2026-04-09 post-guard compare

- artifact root:
  - `C:\tetie\notecode\logs\stepwise_three_article_gate\20260409-style-retest-post-guard\`
- summary:
  - `C:\tetie\notecode\logs\ad_hoc_quality_compare\20260409-style-retest-post-guard\summary_refined.json`
- reading:
  - AI 定型句と一人称はかなり減った
  - ただし `explicit_subject_count` と paragraph cadence の均一感は残った

### 2026-04-09 post-subject-clamp compare

- artifact root:
  - `C:\tetie\notecode\logs\stepwise_three_article_gate\20260409-style-retest-post-subject-clamp\`
- summary:
  - `C:\tetie\notecode\logs\ad_hoc_quality_compare\20260409-style-retest-post-subject-clamp\summary_refined.json`
- reading:
  - `optimized` は paragraph cadence のばらつきが戻った
  - `ai_phrase_total` は `0` まで下がった
  - それでも `explicit_subject_count` はまだ prompt-only baseline より多い
  - gate 総合は `rubric_mean_total = 7.67` で keep、advance しない

## 次の作業

1. `company_introduction` の sentence-level explicit subject clamp
   - `テティエ株式会社の主力は` -> `主力は`
   - `テティエ株式会社は...会社です` は先行文脈がある場合だけ主語省略
   - paragraph 冒頭だけでなく文中の固有名詞反復まで減らす
2. paragraph packing の second pass を narrow に追加
   - company-intro のみ
   - source-grounded section で 2-2-2 配列に寄ったら local merge を許可
3. live compare を same 3 cases で再実行
   - target:
     - `ui-short-branding-company-grounded`
     - `ui-short-branding-trust`
   - guard:
     - `ui-short-case-study-explain`

## stop / keep

- prompt をこれ以上肥大化させて解決しない
- persona を増やして回避しない
- route experiment は reopen しない
- 次の owner は引き続き `note\newalgorithm_pipeline\output_formatter.py` の narrow surface control を優先する

## quick links

- current package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- today record:
  - `C:\tetie\notecode\docs\naturalness_recovery_followup_plan_2026-04-09.md`
