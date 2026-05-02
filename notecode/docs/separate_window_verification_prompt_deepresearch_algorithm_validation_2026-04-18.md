# separate window verification prompt deepresearch algorithm validation 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- verification window first prompt
- `DEEPRESEARCH_ALGORITHM_VALIDATION`
- implementation prompt ではない
- production code edit prompt ではない

今回の目的:
- 外部AI 4本の deepresearch を 1 本ずつ読み、current docs-first source-of-truth と照合する
- 対症療法を排除したうえで、改善アルゴリズムを本当に作成可能そうかを深く判定する
- local docs と external proposals の gap を特定し、次に進めるなら「何を source-of-truth に採用しうるか」を整理する
- 必要な WEB検索も使って、research の主張が一般論として妥当か、より良い一次情報があるかを確認する

current fixed judgment:
- current top-level docs-first line:
  - C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18
- current Phase 01 fixed baseline:
  - contract axes は `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level`
  - source role は `fact / continuity / style_memory`
  - `opening_frame` は `opener_mode` の subproblem
  - `reuse_level` default は `none`
- `naturalness_recovery_2026-04-07` は parked / not fixed
- `opening_frame_redesign_2026-04-18` は reference line
- exact code owner:
  - not fixed
- actual archive:
  - not yet
  - inventory only

検証対象ファイル:
1. C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\compass_artifact_wf-9377f670-1e65-44ff-b072-40f936d6dae8_text_markdown.md
2. C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\deep-research-report (32).md
3. C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\notecode ブログ生成アルゴリズム再設計.md
4. C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\新規 テキスト ドキュメント.txt

この window の実施範囲:
1. 上の 4 ファイルを 1 本ずつ順に読む
2. 各提案を current package docs と照合する
3. prompt accretion / fixed routing table / rename retry / hidden reviser accumulation / symptom-first fix に落ちていないかを検証する
4. 必要な WEB検索を行い、主張の妥当性を一次情報で補強または否定する
5. 「改善アルゴリズムを作成可能そうか」を最終判断する
6. 必要なら docs-only の検証メモを 1 本だけ作る

この window でやらないこと:
- production code edit
- test edit
- AGENTS edit
- WORKLOG edit
- current package docs edit
- implementation prompt 作成
- exact code owner fix
- actual archive 実行
- prompt wording の局所改善案を積み上げること

必須の検証観点:

1. problem framing
- 外部AI提案が local failure を正しく `UI contract / source role / self-blog reuse / opener ownership` の問題として読めているか
- 単なる persona 不足や prompt 不足へ矮小化していないか

2. anti-symptom check
- 提案が対症療法になっていないか
- `prompt_builder retry` の別名再提案になっていないか
- `pipeline hint retry` の別名再提案になっていないか
- fixed routing table の別名になっていないか
- hidden repair / hidden guard accumulation になっていないか

3. contract coherence
- `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level` の 5 軸に還元できるか
- article type ごとの例外ルール集に戻っていないか

4. source role coherence
- `fact / continuity / style_memory` を混線させていないか
- self-blog を default fact source にしていないか
- fallback が branch table 依存ではなく、evidence mode 起点で説明できるか

5. opener ownership coherence
- `title / lead / first heading / first section` を同じ opener anchor で扱えているか
- `company introduction` の `current-business-first` invariant を壊していないか
- history を support only に落とせているか

6. skeleton / planning treatment
- 骨格 / planning / section path を default winner として再導入していないか
- selective activation なら条件が narrow で説明可能か
- current evidence:
  - `company / announcement / daily` で safe majority を作れなかった
  - `daily` は `none_safe_majority`
  - `technical explain` は coverage-first 問題
  を無視していないか

7. migration plausibility
- giant rewrite なしで移行できるか
- rollback-first の順序を持てるか
- exact file mapping を決めなくても owner boundary と pass gate を説明できるか

WEB検索ルール:
- 必ず必要な検索を行う
- 目的:
  - deepresearch 4本で出てくる主要主張の妥当性確認
  - 日本語記事設計、retrieval / style memory separation、long-context / prompt bloat / control-layer設計の一次情報確認
- 検索は一次情報優先
  - 論文
  - 公式 docs
  - NN/g のような原典
- 単なる一般ブログ要約を根拠の中心にしない
- local docs と conflict した場合は、source-of-truth を優先しつつ「外部知見から見た tension」を明示する

推奨する進め方:
1. 4ファイルを 1 本ずつ読み、各ファイルごとに
   - core claim
   - good point
   - current docs と整合する点
   - 危険な点
   - 採用候補
   を短くメモする
2. 4 本を横断して
   - 共通結論
   - 衝突点
   - shallow proposal
   - deep proposal
   を分ける
3. WEB検索で主要主張を検証する
4. 最後に
   - algorithm redesign が現実的に作成可能そうか
   - もし可能なら、どの粒度の redesign なら legal か
   - まだ足りない情報は何か
   を判断する

必要なら作成してよい file:
- C:\tetie\notecode\docs\deepresearch_algorithm_validation_note_2026-04-18.md

stop conditions:
- 対症療法の比較に流れ始める
- prompt wording の細部提案に流れる
- exact code owner を early fix したくなる
- current package reopen と同じ話に戻る
- giant rewrite 前提でしか成立しない
- WEB検索なしで結論を急ぎたくなる

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 読んだ deepresearch 4ファイル
3. WEB検索で確認した主要 source
4. 4本の共通結論
5. 4本の危険な点 / 採用しない点
6. 改善アルゴリズムが本当に作成可能そうかの判断
7. legal な next step が docs-only なのか、management prompt なのか、implementation design なのか
8. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
