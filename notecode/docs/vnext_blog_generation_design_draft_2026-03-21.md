# コトメイク vNext 設計書ドラフト

最終更新: 2026-03-21  
対象: `C:\tetie\notecode`  
位置づけ: current mainline を置換対象とした再設計ドラフト。まだ実装計画ではなく、設計判断の正本候補。  
状態: Draft v0.1

---

## 0. 参照

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode\PRO\PRO.txt`
- `C:\tetie\notecode\PRO\deep-research-report (10).md`
- `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
- `C:\tetie\notecode\puran6\algorithm_complexity_and_gpt54_direction.md`
- `C:\tetie\notecode\docs\gpt54_migration_simplification_memo.md`

---

## 1. 背景と再設計の目的

### 1.1 現行で起きている問題

- モジュールが肥大化しており、生成ロジックの責務境界が厚すぎる
- section prompt が長く、失敗モードのたびに局所ルールが増えやすい
- article type ごとの構成ルールと局所ガードが重なり、実際の生成責務が読みづらい
- 同じ意味内容の section が複数発生することがある
- 日本語特有の主語省略、一人称の自然な出入り、段落呼吸の制御が prompt 依存になっている
- 後段の観測・品質・比較コードが本流の理解負荷を押し上げている

### 1.2 vNext の目的

- ブログ本文生成の本流を細く再定義する
- 記事タイプごとの読みやすい構成を、prompt ではなく planner で制御する
- AIっぽさを「ルールの足し算」で抑えるのではなく、計測と局所修復で抑える
- 日本語の主語省略、語尾、段落、改行、感情度を style profile と evaluator で扱う
- dead code 候補を段階的に隔離し、新規依存を止める

### 1.3 本設計の前提

- 初期スコープは `note` 本文に限定する
- タイトル、CTA、ハッシュタグ、画像は本体完成後に再接続する
- current mainline はいきなり破棄せず、並走期間を設ける
- vNext は「現行の複雑化した current を直す」のではなく、「最小核から再構成する」

---

## 2. 設計原則

### 2.1 Non-Negotiable

1. prompt を増やして品質問題を潰し続けない
2. 生成前に文書全体の意味配置を決める
3. 生成後は全文再生成ではなく局所 repair を優先する
4. 方向性は UI と contract で決め、source は事実の根拠として使う
5. quality / observability は本流の外へ寄せ、本流は細く保つ

### 2.2 守るべき基本思想

- `plan before generate`
- `measure before repair`
- `source-grounded but not source-dictated`
- `thin prompt, rich plan`
- `local repair only`
- `dead code quarantine before deletion`

---

## 3. スコープと非スコープ

### 3.1 初期スコープ

- `note` 本文
- URL / PDF / docx / image からの source 取り込み
- input contract
- document planner
- section writer
- evaluator
- local repair
- paragraph reflow
- output formatter の本文部分

### 3.2 非スコープ

- 画像プロンプト生成
- 画像編集 UI
- LinkedIn addendum
- ハッシュタグ自動生成
- タイトル最適化の細部
- compare 専用 downstream observability の再実装

---

## 4. 現行システム診断

### 4.1 現行で残すべき最小核

- UI shell と current mainline 起動導線
  - `note/current_mainline_runner.py`
- source 読み取りと入力正規化の考え方
- `input contract -> discourse plan -> section generation -> format` の骨格
- 監査ログと snapshot の保存導線

### 4.2 現行で縮退・置換対象にする部分

- 長大な section prompt 構築
  - `note/natural_blog_core.py`
- 過剰な input contract 分岐
  - `note/newalgorithm_pipeline/input_contract.py`
- current mainline 本流に食い込んだ quality / observability
  - `note/newalgorithm_pipeline/quality_observability_mixin.py`
- legacy / zero_base 互換 Mixin 群
  - `note/article_generator.py`
  - `note/article_legacy_*`
  - `note/zero_base_*_mixin.py`

### 4.3 現行の失敗パターン

- section の意味役割が曖昧で、同内容 section が発生する
- 毎 section で書き手が再宣言され、一人称が過剰に出る
- 段落が 1 文 1 行化しやすく、均一な改行になる
- prompt に構造・文体・主語・語尾・法務・source grounding が積み上がる
- 記事タイプごとの構成差が prompt 断片の差になり、全体構成差として安定しない

---

## 5. vNext 全体アーキテクチャ

### 5.1 全体フロー

1. UI / user prompt / source から raw request を受ける
2. source を Canonical Source に正規化する
3. thin contract を確定する
4. document mode / discourse mode を決める
5. coverage planner で non-overlap の section map を作る
6. section writer が短い prompt で本文を生成する
7. evaluator が AIっぽさと読みやすさを計測する
8. local repair で局所修正する
9. paragraph reflow で段落と改行を整える
10. formatter / logs / audit へ流す

### 5.2 モジュール構成

- `vnext/source/`
- `vnext/contract/`
- `vnext/planner/`
- `vnext/writer/`
- `vnext/style/`
- `vnext/evaluator/`
- `vnext/repair/`
- `vnext/format/`

### 5.3 本流に入れないもの

- compare 専用判定
- deep observability の詳細比較
- GPT モデル比較のための診断 field
- legacy compatibility alias

---

## 6. 入力モデルと UI 制御方針

### 6.1 UI 境界の前提

初期フェーズでは、既存 UI shell を維持する。  
vNext はまず既存 UI の値を thin contract へ写像し、内部で `discourse_mode` などへ解決する。

この方針の理由:

- 生成本流の再設計と UI 改修を同時に進めると、失敗原因の切り分けができない
- 既存 UI には `ui_journey`、`content_goal`、`writing_focus`、`tone_profile` などの十分な signal がある
- 新規 UI 項目は、vNext の planner / evaluator が安定した後に追加可否を判断する

### 6.2 current UI から引き継ぐ入力

既存 UI から受け取る current signal は次を正本とする。

- `ui_journey.purpose_key`
- `ui_journey.target_key`
- `ui_journey.detail_key`
- `comparison_axes`
- `article_type`
- `content_goal`
- `writing_focus`
- `length_mode`
- `tone_profile`
- `speaker_profile`
- `audience_profile`
- `prompt_raw`

### 6.3 UI が決めるもの

- `article_type`
- `speaker_profile`
- `audience_profile`
- `content_goal`

初期フェーズでは次は UI 明示入力にせず、内部解決で扱う。

- `discourse_mode`
- `evidence_style`
- `emotion_level`

### 6.4 LLM / source / resolver が決めるもの

- section 数
- 各 section の意味役割
- source facts の配分
- 段落内の論点順
- transition の自然なつなぎ方
- `discourse_mode`
- `evidence_style`
- `emotion_level`

### 6.5 current UI から vNext への内部写像

| current UI signal | vNext での一次用途 | 備考 |
|---|---|---|
| `purpose_key + target_key` | `article_type` / high-level route | current mainline の route map を初期踏襲 |
| `detail_key` | `semantic subtype` | branding / case / compare の細分化に使う |
| `comparison_axes` | `coverage planner` の比較軸 | comparative 以外では無効化 |
| `content_goal` | `discourse_mode` 補助 signal | 構成の意図を絞る |
| `writing_focus` | `evidence_style` / section density | 後方互換のため当面維持 |
| `tone_profile` | `emotion_level` / style profile 補助 | tone を感情度へ直結させすぎない |
| `speaker_profile` | narrator contract | 書き手の表面化量にも使う |
| `audience_profile` | reader question / complexity | section brief の読者前提に使う |

### 6.6 将来 UI に持たせる候補

次は planner の品質が安定してから、明示 UI 化を検討する。

- `discourse_mode`
- `evidence_style`
- `emotion_level`

UI 化の条件:

- 自動推定より user-visible に改善する
- 現在の `writing_focus` や `tone_profile` と役割重複しない
- confirm preview で意味が説明できる

### 6.7 UI に持たせるべき最小選択の将来候補

#### article_type

- `announcement`
- `branding`
- `daily_story`
- `explanatory_article`
- `case_study`
- `comparative_review`
- `industry_analysis`

#### discourse_mode

- `announcement`
  - `standard_notice`
  - `maintenance_notice`
  - `policy_change_notice`
  - `release_note`
- `branding`
  - `fact_profile`
  - `problem_value`
  - `story_driven`
  - `founder_voice`
  - `case_led`
- `daily_story`
  - `observation_reflection`
  - `event_then_learning`
- `explanatory_article`
  - `concept_breakdown`
  - `problem_solution`
- `case_study`
  - `implementation_case`
  - `improvement_case`
  - `incident_case`
- `comparative_review`
  - `criteria_first`
  - `usecase_first`
- `industry_analysis`
  - `structure_shift`
  - `trend_implication`

#### evidence_style

- `fact_first`
- `balanced`
- `story_first`

### 6.8 UI 変更ポリシー

- Phase 0 では visible UI を増やさない
- `discourse_mode` などを UI 提案する場合は、事前にユーザー承認を取る
- 既存の `writing_focus` / `tone_profile` をすぐ削らない
- current UI shell の owner 境界を崩さず、まず contract resolver 側で吸収する

### 6.9 UI で持たせないもの

- section 単位の微細ルール
- 語尾ルールの直接選択
- モデル名
- compare / quality pipeline のモード

---

## 7. Canonical Source Layer

### 7.1 目的

- 入力 source のばらつきを本流の前で吸収する
- 後段で使う事実、メタ情報、重要 span を保全する
- source の品質差を evaluator ではなく source layer で扱う

### 7.2 データモデル

`PRO.txt` の `CanonicalDocument` を踏襲し、最低限次を保持する。

- `raw_text`
- `norm_text`
- `blocks`
- `metadata`
- `critical_spans`
- `source_type`
- `ocr_mode`
- `fact_cards`

### 7.3 source の役割

- source は文体を決めない
- source は事実、用語、日付、主体、根拠を供給する
- source 不足時は fail-closed または style downgrade を選ぶ

### 7.4 Fact Cards

各 source から抽出した事実を次の形に正規化する。

- `fact_text`
- `fact_type`
- `entity`
- `date_or_period`
- `source_title`
- `locator`
- `confidence`
- `critical`

---

## 8. Contract Layer

### 8.1 方針

現行 contract を縮める。vNext では「生成に必要な契約」だけ残す。

### 8.2 必須項目

- `article_type`
- `discourse_mode`
- `evidence_style`
- `emotion_level`
- `speaker_profile`
- `audience_profile`
- `prompt_raw`
- `topic_statement`
- `source_documents`
- `fact_cards`

### 8.3 任意項目

- `core_message`
- `allow_experience`
- `relationship_mode`
- `content_goal`

### 8.4 fail-closed 条件

- 記事タイプが不明
- source 必須タイプで根拠不足
- prompt が meta request で本文生成意図を満たさない
- branding / case study で discourse mode が決まらず、source からも絞れない

### 8.5 削る対象

- current の細かい clarify 条件のうち、本流説明を複雑にするもの
- compare / observability 専用 field
- legacy 互換の alias

---

## 9. Document Mode / Discourse Mode 設計

### 9.1 基本方針

- `article_type` は高位カテゴリ
- `discourse_mode` はそのカテゴリ内の読み方の型
- 同じ `branding` でも構成は複数持つ
- source が強くても、読み方の型は planner が決める

### 9.2 mode 解決の優先順位

初期フェーズでは、明示 UI 入力よりも current UI signal と source を使って内部解決する。

1. 明示 UI 指定がある場合の `discourse_mode`
2. `ui_journey` 由来の semantic subtype
3. `content_goal`
4. `prompt_raw` の意図 signal
5. source の事実形
6. `article_type` 既定値

### 9.3 discourse_mode 解決ルール

#### announcement

- source に日時・変更点・対象・確認事項が揃う場合:
  - `standard_notice`
- メンテナンスや停止予定が中心:
  - `maintenance_notice`
- 規約、料金、運用条件、方針変更が中心:
  - `policy_change_notice`
- 新機能や提供開始の告知が中心:
  - `release_note`

#### branding

- source が会社概要、事業内容、沿革、強み中心:
  - `fact_profile`
- prompt が課題起点で価値説明を要求:
  - `problem_value`
- prompt に場面、エピソード、観察があり source もそれを支える:
  - `story_driven`
- 話者性が強く、創業者・担当者の声が主役:
  - `founder_voice`
- 実例で価値を見せる意図が強い:
  - `case_led`

#### daily_story

- 出来事観察から内省へ流す:
  - `observation_reflection`
- 出来事と学びを直結する:
  - `event_then_learning`

#### explanatory_article

- 概念や仕組みを分解して理解させる:
  - `concept_breakdown`
- 問題提起から解決策へ進む:
  - `problem_solution`

#### case_study

- 導入や適用の筋道が中心:
  - `implementation_case`
- 改善前後の変化が中心:
  - `improvement_case`
- 障害やトラブルと再発防止が中心:
  - `incident_case`

#### comparative_review

- 先に評価軸を置く:
  - `criteria_first`
- 先に用途別の向き不向きを置く:
  - `usecase_first`

#### industry_analysis

- 市場構造や前提変化を主に見る:
  - `structure_shift`
- 直近トレンドと示唆を主に見る:
  - `trend_implication`

### 9.4 evidence_style 解決ルール

- source が dense で fact card が強い場合:
  - `fact_first`
- prompt と source が均衡している場合:
  - `balanced`
- prompt に場面・経験・観察の要求が強く、source が補助根拠に回る場合:
  - `story_first`

### 9.5 emotion_level 解決ルール

- `announcement`: `0`
- `industry_analysis`: `0-1`
- `explanatory_article`: `1`
- `branding`: `1-2`
- `case_study`: `1-2`
- `daily_story`: `2-3`

tone は直接 emotion と一致させず、次の補正だけを許す。

- `formal` または `calm`: 上限を 1 段下げる
- `warm`: 上限を 1 段上げる
- source が高 preservation 必須: 感情度を下げる

### 9.6 記事タイプ別 skeleton

#### announcement

- change
- target_and_when
- impact
- check
- action

#### branding.fact_profile

- company_or_offer_outline
- problem_background
- concrete_strength
- why_it_matters
- closing

#### branding.story_driven

- scene
- tension_or_question
- action_or_choice
- realized_value
- reader_connection

#### daily_story.observation_reflection

- observation
- felt_shift
- concrete_scene
- later_insight
- quiet_close

#### explanatory_article.concept_breakdown

- question
- concept_definition
- mechanism
- practical_example
- takeaway

#### case_study

- initial_problem
- approach
- adjustment
- result
- reuse_condition

#### comparative_review.criteria_first

- comparison_frame
- criteria
- differences
- fit_by_usecase
- conclusion

#### industry_analysis.structure_shift

- market_context
- structure_change
- key_difference
- implication
- next_watchpoint

### 9.7 planner の役割

- skeleton を選ぶ
- section 数を決める
- 各 section の primary claim を置く
- `forbidden_overlap` を明示する
- transition を設計する

### 9.8 planner が source に委ねないもの

- skeleton の型
- section role の定義
- closing の役割
- overlap 禁止ルール

source は facts を供給するが、文書構成の source of truth にはしない。

---

## 10. Coverage Planner と Non-Overlap 制御

### 10.1 本章の位置づけ

vNext の本体はここである。  
AIっぽさより先に、ブログとして同内容 section を防ぐ。

### 10.2 section brief

各 section は最低限次を持つ。

- `section_id`
- `section_role`
- `primary_claim`
- `supporting_facts`
- `reader_question`
- `transition_target`
- `forbidden_overlap`
- `narrator_visibility`
- `emotion_target`

### 10.3 planner の入力

- thin contract
- resolved `article_type`
- resolved `discourse_mode`
- resolved `evidence_style`
- resolved `emotion_level`
- fact cards
- prompt intent summary
- source coverage summary

### 10.4 planner の出力

- ordered section briefs
- section count
- global thesis
- used fact registry
- overlap constraints
- transition map
- narrator state initialization

### 10.5 coverage 生成手順

1. skeleton を選ぶ
2. skeleton の各 slot に `section_role` を割り当てる
3. fact cards を主役候補と補助候補に分ける
4. 各 slot に unique primary claim を置く
5. 各 slot の `forbidden_overlap` を埋める
6. closing が summary 再掲で終わらないよう next action / implication を固定する
7. section 間の transition を張る

### 10.6 生成前 overlap gate

- section brief 同士の claim 類似度を測る
- 類似が高い場合は
  - merge
  - role の再割り当て
  - evidence の再配分
  のどれかを行う

### 10.7 生成前 overlap gate の hard rule

- 同一 primary claim を複数 section に置かない
- 同一 fact card を複数 section の主役にしない
- intro と closing の中心命題を一致させない
- explanation section と example section を同じ意味にしない
- branding の価値説明 section と実例 section を混同しない

### 10.8 生成後 overlap gate

- section body の意味類似を測る
- 重複 section があれば、その section だけ差し替える
- 全文再生成はしない

### 10.9 生成後 overlap gate の処理順

1. body から section claim を抽出する
2. section 間 similarity を計測する
3. overlap の原因が planner か writer かを切り分ける
4. planner 原因なら brief を再生成
5. writer 原因なら該当 section だけ書き直す

### 10.10 overlap を防ぐための planner ルール

- 同一 fact card を複数 section の主役にしない
- 同一 reader question を複数 section に持ち込まない
- closing は summary の再掲ではなく、次の判断か一歩を置く
- introduction は定義だけで終わらせず、後続 section と意味役割を分ける

### 10.11 UI との関係

coverage planner は UI の代替ではなく、UI で与えられた方向性を文書構成へ展開する owner である。

- UI は文書の方向性を決める
- planner は section の意味配置を決める
- writer は各 section を文章化する

この境界を崩すと、UI 変更と生成品質変更が再び混線する。

---

## 11. Section Writer 設計

### 11.1 方針

- prompt は短いまま保つ
- 役割、主張、根拠、声だけを与える
- 主語省略や改行は prompt の長い説明で解決しない

### 11.2 prompt の最大方針

- 8〜12 行程度
- 明示ルールは最大 5〜6 個
- 否定ルールは必要最小限
- source facts は最大 2〜3 件

### 11.3 prompt に入れるもの

- section role
- primary claim
- supporting facts
- reader question
- previous transition
- narrator visibility
- emotion target

### 11.4 prompt に入れすぎないもの

- 長い banned phrase 群
- article type ごとの局所枝ルールの列挙
- 段落や文末に関する細かすぎる禁止事項
- compare 専用指標

### 11.5 stateful generation

writer は各 section 生成時に次の state を受け取る。

- `active_entities`
- `narrator_state`
- `topic_chain`
- `used_facts`
- `used_claims`

これにより、毎 section で書き手を再宣言しない。

---

## 12. Style Profile と感情度

### 12.1 感情度を正式に持つ

vNext では `emotion_level` を style profile の主要項目にする。

- `0`: 事実のみ
- `1`: 低い主観
- `2`: ほどよい熱量
- `3`: 高めの内省・温度感

### 12.2 style profile の項目

- `emotion_level`
- `subjectivity_level`
- `empathy_level`
- `narrator_visibility`
- `subject_explicitness_target`
- `sentence_burst_target`
- `paragraph_breath_profile`
- `polite_ratio_target`
- `ending_diversity_target`

### 12.3 article type ごとの初期値

- `announcement`
  - `emotion_level=0`
  - `narrator_visibility=low`
  - `subject_explicitness_target=high`
- `branding`
  - `emotion_level=1-2`
  - `narrator_visibility=medium`
  - `subject_explicitness_target=medium-low`
- `daily_story`
  - `emotion_level=2-3`
  - `narrator_visibility=medium-high`
  - `subject_explicitness_target=low`
- `case_study`
  - `emotion_level=1-2`
  - `narrator_visibility=medium`
- `comparative_review`
  - `emotion_level=0-1`
  - `narrator_visibility=low`

### 12.4 感情度の扱い

- 感情語を増やす制御にはしない
- 主観文率、観察文率、内省文率、疑問文率、語尾、文長揺れで表現する

---

## 13. 日本語特有の主語省略・一人称制御

### 13.1 問題設定

- AI は各 section で「私は」「私たちは」を再点火しやすい
- 日本語では主語は自然に省略されるが、省略しすぎると照応負荷が上がる

### 13.2 vNext の扱い

- 主語省略は prompt 依存でなく evaluator + repair で扱う
- narrator は section ごとに `visible / implicit / hidden` を持つ
- 初出、視点転換、比較対象切替のときだけ主語を明示する

### 13.3 追う指標

- `subject_explicit_rate`
- `zero_subject_chain_length`
- `anaphora_risk`
- `first_person_repetition_rate`

### 13.4 repair ルール

- 冗長な一人称は削る
- 曖昧すぎる省略だけ主語を補う
- 同一段落内で主語の明示と省略が不自然に揺れたら整える

---

## 14. Evaluator 設計

### 14.1 evaluator の役割

- AIっぽさの症状を計測する
- 記事タイプに対して文体が外れていないか見る
- repair 対象 section を決める

### 14.2 初期採用指標

- 文長 CV
- 段落長 CV
- 文頭反復率
- 語尾多様性
- 丁寧体比率
- 説明マーカー密度
- 一人称反復率
- 主語明示率
- ゼロ主語連鎖長
- 段落呼吸スコア
- 1文1行率
- section 間意味類似度

### 14.3 指標の位置づけ

- fail-closed は契約違反と source 不整合に限定する
- AIっぽさ指標は基本 soft gate にする
- soft gate を超えた section のみ repair 対象にする

### 14.4 PRO との関係

本 evaluator は `PRO.txt` と `deep-research-report (10).md` を要約実装した層として位置づける。

---

## 15. Local Repair 設計

### 15.1 原則

- 全文再生成は禁止
- section 単位または paragraph 単位のみ
- 事実損失を起こさない

### 15.2 repair 操作

- `split_long_sentences`
- `merge_short_sentences`
- `vary_sentence_endings`
- `omit_redundant_subjects`
- `restore_ambiguous_subjects`
- `compress_explanations`
- `reflow_paragraphs`
- `replace_overlapped_section`

### 15.3 repair の打ち切り

- repair は最大 1〜2 回
- fact loss が閾値超過なら打ち切る
- お知らせは high preservation で扱う

---

## 16. Paragraph Reflow / Output Formatter

### 16.1 改行は本流の一部

AIっぽさは本文の意味だけでなく、改行と段落呼吸にも強く出る。  
vNext では paragraph reflow を正式な責務として持つ。

### 16.2 paragraph reflow の原則

- 1 文ごと改行しない
- 意味役割が切り替わる場所でだけ段落を切る
- 観察、事実、補足、判断が混ざった段落をほぐす
- 短文の連打を均一段落にしない

### 16.3 note 本文への整形

- `lead -> body -> references`
- summary / toc は document mode に応じて可否を決める
- branding と daily_story は目次を弱くする

---

## 17. ログ・評価・改善ループ

### 17.1 残すもの

- latest generation snapshot
- generation audit log
- section 単位の evaluator report
- repair operations log

### 17.2 本流から外すもの

- compare 専用差分計測
- downstream-neutral compare config
- reopened comparative heuristics

### 17.3 ship 判定

- source 整合
- non-overlap
- readability
- article type alignment
- section repair 率

---

## 18. デッドコード分離計画

### 18.1 方針

- すぐ削除しない
- まず隔離して新規依存を止める
- 隔離後に回帰がなければ削除候補へ進める

### 18.2 dead code quarantine の対象候補

- `note/article_generator.py`
- `note/article_legacy_section_runtime_mixin.py`
- `note/article_legacy_compatibility_mixin.py`
- `note/article_legacy_addendum_mixin.py`
- `note/zero_base_section_helper_mixin.py`
- `note/zero_base_postprocess_guard_mixin.py`
- `note/zero_base_contract_mixin.py`
- `note/zero_base_contract_guard_mixin.py`
- `human_resonance/` の本流外 phase
- `human_resonance2/` の compare / observability と重なる層

### 18.3 quarantine 原則

- 旧モジュールへ新機能を足さない
- adapter 以外からの import を増やさない
- 新本流は quarantine 配下へ依存しない

### 18.4 隔離先の考え方

- `note/legacy_current/`
- `note/archive_compat/`
- `note/vnext_adapters/`

実装時にどこへ寄せるかは、import 衝突と test 配置を見て確定する。

### 18.5 削除判定基準

- production direct call がない
- adapter 経由でも未使用
- vNext 並走で回帰なし
- rollback 手順が文書化済み

---

## 19. 移行方針

### 19.1 段階移行

#### Phase 1

- Canonical Source
- thin contract
- discourse mode

#### Phase 2

- coverage planner
- minimal section writer

#### Phase 3

- evaluator
- local repair
- paragraph reflow

#### Phase 4

- shadow run
- current / vNext 比較

#### Phase 5

- dead code quarantine
- adapter fixed boundary

#### Phase 6

- current mainline retirement

### 19.2 並走期間

- current と vNext を同じ入力セットで回す
- overlap、主語、一人称、改行、article type alignment を比較する
- no-op でなく user-visible 改善が出たときだけ切替候補とする

---

## 20. 受け入れ基準

### 20.1 構造

- 同内容 section が発生しない
- article type ごとの skeleton が読める
- closing が summary の再掲だけで終わらない

### 20.2 文体

- 一人称が毎 section で不必要に出ない
- 省略が過剰で読者が迷わない
- 改行が均一でない
- 1 文 1 行率が高すぎない

### 20.3 source

- critical facts が落ちない
- お知らせで事実順序が崩れない
- branding で source にない具体例を作らない

### 20.4 保守性

- 本流モジュール数が明確
- prompt builder が 1 ファイル肥大化に戻らない
- 記事タイプ追加時に rule の横展開が最小で済む

---

## 21. open questions

1. `discourse_mode` を UI で明示選択にするか、自動推定を既定にするか
2. evaluator のどこまでを soft gate にし、どこから repair 必須にするか
3. `announcement` の preservation 優先度をどこまで強くするか
4. `branding` の story-driven と fact-profile を source 量に応じてどう切り替えるか
5. GiNZA 導入を初期から必須にするか、subject metrics は regex 近似から始めるか

---

## 22. 次に作る文書

この設計書の次段では、別ウインドウで次を作る。

1. vNext 実装計画
2. quarantine 計画
3. adapter 境界定義
4. current から vNext への test 移行計画

本ドキュメントでは、実装順よりも先に「何を作り、何を作らないか」を固定する。

---

## 23. 要約

vNext の本体は次の 4 点である。

1. `document_mode + discourse_mode` で全体構成を先に固定する
2. `coverage planner` で同内容 section を生成前に防ぐ
3. `PRO` 由来の evaluator で日本語らしさと AIっぽさを計測する
4. dead code は削除前に quarantine して、新規依存を止める

この設計は「prompt を賢くする」案ではない。  
「構成を決め、測って、局所修復する」ための再設計である。
