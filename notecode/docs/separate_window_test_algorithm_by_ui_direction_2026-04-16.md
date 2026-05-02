# separate window test algorithm by ui direction 2026-04-16

## Purpose

- UI 上のブログ記事の方向性差を `fixed routing table` ではなく `direction prior + Japanese realization policy` として narrow に試す
- `WORKLOG.md` と current package の失敗を再投入せず、別ウインドウで rollback 可能な test algorithm を実装するための spec を固定する
- target は「各記事タイプごとに別アルゴリズムを増やす」ことではなく、「共通の談話制御に日本語向け参照表現 / 省略 / AI-feel 抑制を足す」こと

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
7. `C:\tetie\notecode\docs\ui_role_clarity_record_2026-04-08.md`
8. `C:\tetie\WORKLOG.md`
9. このファイル

## Scope

- separate window 実装用
- current mainline を直接の source-of-truth として上書きしない
- `1 phase = 1 narrow hypothesis = 1 owner scope`
- 初手では `branding / company_introduction / explanatory_article / daily_story / industry_analysis` を対象候補にする
- `announcement` は factual constraint が強いため、この test algorithm の初手 owner にしない
- source-less WEB mode の allowed / disallowed boundary は `autonomous_blog_productization_2026-04-14` を尊重する

## Why This Line

- current code にはすでに `topic_seed / reader_question / bridge_hint / paragraph_break_policy / ending_distribution_hint` があり、談話計画の土台はある
- ただし、`会社名 / 私たち / 当社 / 主語省略` の参照表現 policy は section-level で十分に明示されていない
- AI-feel は単語単体より、`抽象語密度 / 同型文末連続 / 接続の単調さ / 主語の露出過多 / 段落呼吸不足` の複合で出る
- よって、次の narrow line は prompt 増量ではなく `Japanese realization policy` を section 計画に足す方向が最も整合する

## Failure Memory From Current Docs And WORKLOG

### Do Not Repeat

- `article-type fixed routing table` を作らない
- `planning / skeleton default` を再主張しない
- `prompt-only winner` の断定から入らない
- `formatter-only surface polish` を本丸にしない
- `input_contract.py` upstream summary だけで直そうとしない
- `natural_blog_core.py` の `first section history clamp` を再投入しない
- `unsupported slot` を generic filler で埋めない
- `運営側` のような曖昧 role label を UI / prompt に戻さない
- `hidden reviser accretion` や multi-pass rewrite を増やさない

### Keep

- default route interpretation は `grounded generic default`
- planning は `feature gate を通ったときだけ opt-in`
- `single-pass + optional single repair 1回`
- `branding/company_introduction` では current-business-first keep line を尊重する
- role clarity を UI でも runtime でも維持する

## Direction Model

この test algorithm は article type ごとに別々の generator を作らない。  
まず UI / semantic / source shape から `direction family` を推定し、その family に応じた realization policy を足す。

### Direction Families

- `trust_intro`
  - `branding / company_introduction / product_introduction` のうち、価値説明と現在の事業輪郭を中心に置く line
- `explain_analysis`
  - `explanatory_article / industry_analysis`
- `reflection`
  - `daily_story`
- `case_process`
  - `case_study`
- `comparison`
  - `comparative_review`

### Important Constraint

- これは `fixed route` ではなく `prior`
- 実際の section order や realization hint は、must-cover density / source coverage / reader question / current article prior を見て narrow に決める
- `direction family = article type` の 1:1 hard mapping にしない

## Test Algorithm

### Layer 1: Discourse Direction Prior

- input:
  - article type
  - semantic article key
  - role choice
  - source bucket shape
  - must-cover count
  - current heading plan
- output:
  - direction family
  - article-level stance
  - first-section obligation
  - section-to-section information shift policy

### Layer 2: Reference Realization Policy

各 section に以下を追加する。

- `speaker_reference_policy`
  - `company_name_once`
  - `watashitachi_preferred`
  - `tousha_preferred`
  - `subject_omission_preferred`
  - `no_first_person`
- `subject_reintroduction_policy`
  - `lead_only`
  - `section_shift_only`
  - `closing_reanchor`
- `proper_noun_repeat_cap`
  - 同一 section / adjacent section での固有名詞反復上限

### Layer 3: Japanese Information Placement

- `old -> new` の順で置く
- 日本語では `front-load everything` を避ける
- 1文の後半へ情報を詰め込み過ぎず、必要なら次文へ送る
- paragraph 単位で
  - topic continuation
  - role shift
  - judgment shift
  を管理する

### Layer 4: Statistical AI-Feel Suppression

blacklist だけにしない。以下の複合シグナルで optional single repair を発火させる。

- `abstract_noun_density`
  - 価値 / 可能性 / 課題 / 支援 / 取り組み / 重要 などの抽象語が高密度
- `company_name_repeat_ratio`
  - 会社名や `○○株式会社` が近接反復
- `explicit_subject_ratio`
  - 全文で主語を言い直し過ぎている
- `ending_max_run`
  - 同型文末の連続
- `connective_monotony`
  - `また / そして / 一方で / そのため` 等の偏り
- `template_phrase_hits`
  - 既知の AI-like phrase 群への一致
- `paragraph_breath_flatness`
  - 段落長の分散が低すぎる

### Layer 5: Optional Single Repair

- repair は 1 回だけ
- lexical rewrite ではなく、優先順は次の通り
  1. 主語の言い直しを削る
  2. 会社名反復を `私たち / 当社 / 省略` に置換する
  3. 抽象まとめ文を具体文へ寄せる
  4. 同型文末を崩す
  5. 段落境界を 1 箇所だけ調整する

## Family-Specific Policy

### trust_intro

- first section は `現在の事業 / 現在の役割 / いまの価値` を優先する
- history は source-backed なときだけ後段で使う
- 初出で会社名を許可しても、その後は `私たち / 当社 / 省略` を分配する
- `○○株式会社では` の段落頭反復は禁止

### explain_analysis

- 原則 `no_first_person`
- ただし UI role が corporate speaker のときだけ `当社` を限定的に許可
- 文末は断定一辺倒にせず、`判断 / 留保 / 条件` を混ぜる

### reflection

- 一人称は許可する
- ただし段落頭の `私は / 私たちは` 反復は避ける
- `気づき -> 理由 -> 次に試すこと` の流れを優先し、感想語だけで閉じない

### case_process

- 成功談だけで閉じない
- 変化、条件、限界を残す
- 主語は人より `状況 / 手順 / 対応` を中心に置く

### comparison

- 候補名の連打を避け、比較軸を主語化する
- 「A は」「B は」の往復より、軸先行で差分を書く

## First Narrow Implementation Slice

### Recommended Owner 1

- `C:\tetie\notecode\note\natural_blog_core.py`

### Why

- 既存で `DiscourseSectionPlan` に近い単位を持つ
- `topic_seed / reader_question / bridge_hint / new_information / paragraph_break_policy / ending_distribution_hint` がすでにある
- section 計画へ `speaker_reference_policy` と `subject_reintroduction_policy` を足すだけなら blast radius が狭い

### Owner 1 Hypothesis

- `trust_intro` と `explain_analysis` に限って section-level `reference realization policy` を追加すると、会社名反復と主語露出過多が減り、日本語 blog-like naturalness が上がる

### Owner 1 Non-Goals

- pipeline route default を変えない
- formatter を先に触らない
- input contract 要約だけに責任を寄せない
- UI label を同時に増やさない

## Suggested Implementation Order

1. `natural_blog_core.py`
   - section plan に `speaker_reference_policy` / `subject_reintroduction_policy` / `proper_noun_repeat_cap` を追加
2. `simple_note_pipeline/prompt_builder.py`
   - 上記 policy を短い generation hint に変換する
3. `quality_guard` or pipeline telemetry
   - `company_name_repeat_ratio` / `explicit_subject_ratio` / `template_phrase_hits` の lightweight telemetry を追加
4. optional single repair
   - しきい値超過時だけ narrow repair

## Evaluation

### Required Compare

- `company_introduction`
- `branding`
- `explanatory_article`
- `daily_story`

### Primary Human Checks

- 会社名や `株式会社` が前景で反復していないか
- `私たち / 当社 / 省略` の配分が不自然でないか
- 主語を毎文言い直していないか
- AI 的な抽象まとめで段落が埋まっていないか
- 段落の呼吸が平坦でないか

### Machine Checks

- `company_name_repeat_ratio`
- `explicit_subject_ratio`
- `ending_bucket_max_run`
- `connective_monotony`
- `template_phrase_hits`
- `paragraph_breath_flatness`

## Stop Conditions

- same hypothesis で 3 回失敗
- route default を変えないと進めない
- formatter か input_contract 単独へ責任が逃げ始める
- fixed routing table を作らないと回らない設計になった
- `announcement` へ安易に拡張したくなった

## Interim Verdict

- 作成可能
- ただし「記事タイプ別アルゴリズム」ではなく
  - `direction prior`
  - `reference realization policy`
  - `Japanese AI-feel suppression`
  の 3 層に分けるべき
- first bridge は `natural_blog_core.py` owner が最も安全

