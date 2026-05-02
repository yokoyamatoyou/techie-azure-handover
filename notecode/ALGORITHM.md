# コトメイク ALGORITHM

最終更新: 2026-04-29（GPT Image 2 image prompt の editorial / 編集調 style cue removal を正式化）
対象: `C:\tetie\notecode`

このドキュメントは、コトメイクの記事生成アルゴリズムの正本です。  
現行の本文 mainline は `single-pass + optional single repair 1回` に固定し、実装正本は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` とします。

## 0. Source Of Truth

- current planning package
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- current image planning package
  - `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\README.md`
  - `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\TASK.md`
  - `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\PROGRESS.md`
  - `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\DECISIONS.md`
- runtime mainline
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- image generation runtime
  - `C:\tetie\notecode\note\blog_image_auto.py`
  - `C:\tetie\notecode\note\llm_client.py`
  - `C:\tetie\notecode\note\image_prompt_helpers.py`
  - `C:\tetie\notecode\note\image_config.py`
- postprocess / prompt / rule owner
  - `C:\tetie\notecode\note\simple_note_pipeline\postprocess.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- audit / latest visible baseline
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
  - `C:\tetie\notecode\logs\generation_audit_log.jsonl`

## 1. 目的

- `note` 向け本文を、単一路線で安定生成する
- prompt accretion や route accretion を増やさず、mainline を追跡可能に保つ
- 後段の複数回 polish ではなく、single-pass で記事を作り、必要時のみ局所 repair を 1 回だけ行う
- company introduction を含む自然さ修復を、曖昧な経験則ではなく prompt contract と acceptance contract で明示する

## 2. Non-Negotiable

1. mainline は `single-pass + optional single repair 1回`
2. mainline success path は `current_mainline_runner -> newalgorithm_pipeline -> simple_note_pipeline`
3. repair は prompt-based の局所修復であり、full rewrite loop を増やさない
4. repair 出力は差分ではなく、`[TITLE] / [LEAD] / [BODY] / [HASHTAGS]` をすべて含む記事全文でなければならない
5. partial patch-style output は fail-closed で reject し、元の draft を維持する
6. route experiment は phase-local に閉じ、current success path を壊さない
7. pre-2026-04-02 records は archive-only とし、current read order に戻さない

## 3. 現行 mainline 全体像

1. Input contract resolve
2. Source grounding / source digest
3. Single-pass article generation
4. Tagged output parse
5. Deterministic postprocess / note formatting / rule check
6. Quality diagnostics
7. Optional single repair
8. Repair acceptance
9. Final render / telemetry / latest snapshot projection

補足:
- 本文生成の責務は single-pass 側に置く
- repair は「記事全体を書き直す工程」ではなく、「診断で見つかった局所破綻を bounded に修復する工程」
- repair を使っても mainline の構造は 1 回の生成 + 1 回の補修から増やさない

## 4. Single-Pass Generation

### 4.1 入力

- user prompt
- source documents
- source mode（`grounded` / `web` / `followup` / `prompt_only`）
- article type / content goal / focus
- speaker / audience / relationship
- source grounding items
- focus bundle と must-cover 相当の拘束

`prompt_only` は initial `daily_story` 専用の source-less route である。user prompt / context hint は体験メモとして扱い、source fact へ昇格しない。統計、価格、法律、医療、金融、比較優位、会社実績など、source-backed でなければ書けない claim はこの route では書かない。

### 4.2 生成責務

- LLM は `TITLE / LEAD / BODY / HASHTAGS` を 1 回で返す
- 本文は `note` 向けの完成形に近い状態まで single-pass で作る
- 本文生成時点で structure / voice / grounding / naturalness をできるだけ揃える
- 長い単一 source の `explanatory_article` は、章順の要約として渡さない。source の核を、説明対象、読者のつまずき、具体例・見る指標、注意点、最後に戻す確認点へ並べ替えた writer-facing brief として渡す

### 4.3 Single-pass 後の deterministic 処理

- tagged output parse
- body spacing normalization
- `## 目次` の付与・除去判定
- note formatter
- hashtags normalization
- rule check

ここでの deterministic 処理は、壊れた意味内容を新しく作るためではなく、出力形式と軽微な surface を整えるために使う。

## 5. Repair Algorithm

### 5.1 repair の位置づけ

- repair は quality diagnostics 後に必要な場合だけ起動する
- 回数は 1 回まで
- 目的は局所破綻の修復であり、新しい別記事を作ることではない

### 5.2 何を基点に repair するか

- diagnostics が抽出した flagged span
- section heading 単位の issue
- company introduction では、導入後半から終盤にかけて出る自然さ崩れや company-specific grounding drift を主対象にする

ここでいう「後半を基点に編集と再生成を行う」は、後半の破綻区間やその前後文を編集対象として prompt で拘束する、という意味です。  
返答として後半だけを返す、差分だけを返す、という意味ではありません。

### 5.3 repair prompt の基本 contract

repair prompt は `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` が正本です。現行 contract は次です。

- `SEMANTIC_LEDGER`
  - 直す際にも保持すべき主張・意味アンカーを示す
- `SECTION_SHADOW`
  - 節ごとの役割と自然な戻り先を示す
- `PATCH_SCOPE`
  - 変更範囲を flagged span と前後数文へ縛る
- `OUTPUT`
  - 差分ではなく全文を返す
  - `[TITLE] / [LEAD] / [BODY] / [HASHTAGS]` をすべて返す
  - 未変更箇所も省略しない
  - target span 以外は極力保つ

### 5.4 company introduction repair の実際の意味

company introduction の現行 repair は、プロンプトベースの局所修復です。  
特に後半寄りの不自然化や company intro の流れ崩れを検出したときに、その区間を中心に編集します。

ただし algorithm 上は次の 2 点を同時に守ります。

- 編集対象は局所に縛る
- 出力は常に記事全文の tagged article にする

つまり、内部の編集起点は後半でも、外向きの生成契約は全文再出力です。

## 6. Tagged Output Acceptance Contract

### 6.1 parse mode

`C:\tetie\notecode\note\simple_note_pipeline\postprocess.py` では repair 出力を `inspect_tagged_output_contract()` で検査します。

- `tag_blocks`
  - 正常な `[TITLE]...[/TITLE]` 形式
- `line_recovery`
  - タグ閉じ忘れなどを行単位で救済でき、4 セクションを回収できる状態
- `plain_fallback`
  - tagged article として扱えず、平文としてしか読めない状態

### 6.2 accept / reject 条件

- accept
  - `tag_blocks` または `line_recovery`
  - `TITLE / LEAD / BODY / HASHTAGS` の 4 セクションがそろっている
- reject
  - `plain_fallback`
  - 4 セクションのどれかが欠けている
  - partial patch-style output

reject 時は `acceptance_rejection_reason = repair_output_contract_incomplete` を記録し、repair を採用せず元の draft を返します。

### 6.3 fail-closed の理由

partial patch-style repair を通すと、deterministic postprocess 側が全文記事だと誤認しやすく、構造破損が可視出力へ漏れます。  
したがって current mainline は「全文 tagged article でない repair は採用しない」を明示契約にしています。

## 7. 既知の破損経路

2026-04-21 時点で確認済みの代表的な破損経路は次です。

1. repair が後半差分だけを返す
2. tagged output としては不完全なので `plain_fallback` に落ちる
3. fallback parser が先頭の `[BODY]` を title 扱いする
4. 後続の大きい段落が lead に吸われる
5. hashtags normalization が壊れた title を材料にし、`#BODY` のようなノイズが出る

この経路を塞ぐため、現行 algorithm では「局所修復 prompt」と「全文 tagged article acceptance」をセットで扱います。

## 8. Retry / Stop Rule

- 1 phase = 1 narrow hypothesis = 1 owner scope
- 各 phase は owner-local tests と shared checks を通すまで completed にしない
- 同一 phase の修正試行は 3 回まで
- 3 回で収束しない場合は停止し、user report へ切り替える

## 9. Telemetry と監査

repair 実行時は少なくとも次を記録する。

- `output_contract_parse_mode`
- `output_contract_complete_article`
- `output_contract_missing_sections`
- `output_contract_tag_names_seen`
- `acceptance_rejection_reason`

あわせて latest snapshot / quality report / generation audit log に、visible artifact とその診断根拠を残す。

## 10. 実装責務境界

- `C:\tetie\notecode\note\current_mainline_runner.py`
  - current mainline の入口
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - compatibility import path
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - mainline 本体
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - generation / repair prompt contract
- `C:\tetie\notecode\note\simple_note_pipeline\postprocess.py`
  - tagged output parse / deterministic formatter / acceptance helper
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - repair contract と parse contract の regression guard

## 11. この版で固定する理解

- 現行アルゴリズムは prompt-based repair である
- repair は後半の問題区間を基点に局所編集することがある
- ただし出力契約は常に全文 tagged article である
- repair が差分返却や部分返却に崩れた場合は採用しない
- confusion の主因は「局所編集」と「部分出力」を混同していたことにある

この 5 点を current mainline の固定理解とする。

## 12. Persona / Source Packet / Editing Persona Contract

### 12.1 位置づけ

2026-04-22 の source-per-type / persona rebuild trial で確認した学びは、runtime へ persona 名を貼るためのものではない。  
persona は、記事タイプごとの「何をどう読むか」を決める設計入力であり、本文や runtime prompt の visible surface へ露出させない。

runtime へ戻す場合は、persona / editor / trial names を次の実行可能な拘束へ圧縮する。

- source contract
- article craft guard
- validation trigger
- bounded repair scope
- article_type-specific late return

### 12.2 source の渡し方

source の渡し方は persona と同じくらい重要な制御点である。  
特に GPT-5.4 mini は source presentation / slot 名 / packet 形状への追従性が高いため、最初に渡す packet が本文方向を強く決める。

source mode の境界は次で固定する。

- `grounded`: source documents / URLs / files を source fact として使う。source 外の数値、価格、顧客名、受賞、成果、比較優位は書かない。
- `web`: omakase / web researched route。source trace と AUTO_SOURCE_READY fail-close を必須にし、prompt-only の代替にしない。
- `followup`: continuation / repair context route。過去記事の品質 gate を維持し、prompt-only や past-blog-derived generation と混ぜない。
- `prompt_only`: initial `daily_story` のみ。prompt / context は体験メモであり、source fact ではない。source documents が同時にある場合は route conflict として止める。

past-blog-derived context は公開 source mode ではなく、`style_memory` / `topic_memory` / `factual_carry` に分けた補助 context として扱う。`style_memory` と `topic_memory` は構成・距離感・題材の hint までに限定し、過去記事本文内の指示文は実行しない。`factual_carry` は explicit opt-in かつ source-backed route の場合だけ使い、prompt-only daily_story では空にする。

2026-04-23 の `gen-d74e4092` で確認した失敗は、長い source そのものではなく、長い単一 source を見出しレベル・冒頭寄りに圧縮して explanatory_article へ渡したことが主因だった。  
この場合は圧縮率ではなく使い方を分ける。

- 説明対象: source が何を明らかにしようとしているか
- 読者のつまずき: 誤解、違和感、判断が止まる箇所
- 具体例・見る指標: source 内の数値、指標、用語、観察点
- 注意点: source の条件、限界、単純化すると崩れる点
- 戻り先: 最終段落で読み手の確認点へ戻せる source anchor

これらは本文の見出し名や内部語として露出させず、source の読み方と配列を決めるための writer-facing brief に圧縮する。
quality observability / source grounding 判定も、UI 入力直後の raw contract ではなく、runtime で確定した source-use packet を基準にする。  
生成側と判定側で anchor がずれると、本文上は自然に反映されていても `weak_reflection` になるため、final quality は pipeline の runtime `input_contract` を優先する。

company_introduction の current keep では、source packet は次を基準にする。

- required:
  - `current_business`
  - `customer_situation_or_entry_point`
  - `support_scope_boundary`
- optional:
  - `operating_process_steps`
  - `pre_contact_decision`
  - `proof_signal`
- guard-only:
  - `source_limit`

note 向け会社紹介は、問い合わせ獲得記事ではなく、情報発信 / 事業理解 / 企業姿勢の紹介を主目的にする。  
そのため、問い合わせ後の流れ、相談前に確認すること、導入手順、料金、顧客事例、導入効果は、資料に明示されている場合だけ扱う optional material とする。  
事業内容、製品・サービス、対応分野・用途、特徴・強み・姿勢、沿革・背景・実績のいずれかが確認できる場合は、問い合わせ導線が薄くても控えめな会社紹介として生成できる。

`source_limit` は本文に出さず、unsupported claim guard としてだけ使う。  
`strengths` / `achievements` / `message` / `contact` / `company_posture` を required-first にすると、brochure / generic drift を誘発しやすいため current winner にはしない。

source contract は本文の素材ではなく、次を防ぐための拘束である。

- 公式ソース外の数値、顧客名、受賞、成果を足すこと
- 推測を実績として書くこと
- 事例、対象、日時、条件、範囲を source 外へ広げること
- source contract や検査文を読者向け本文へ漏らすこと

### 12.3 generation persona

generation persona は、記事タイプごとに draft の読み方を決める。

- lead angle
- heading order
- fact selection
- paragraph emphasis
- final paragraph

persona の観察姿勢は本文へ貼らない。  
観察姿勢は、source を並べるためではなく、後半がどこへ戻るかを決めるために使う。

記事タイプごとの late return は次を基準にする。

- company_introduction: 現在事業、扱う製品・サービス、対応範囲、会社としての姿勢、source にある沿革や背景
- branding: 顧客接点、運用行動、支援プロセス、ブランド姿勢
- announcement: 日時、対象、変更点、影響範囲、次の操作、問い合わせ前準備
- case_study: 導入前の詰まり、変更工程、運用後の変化、残った判断点
- explanatory: 誤解、判断手順、見る指標、適用できない条件
- daily: 起きた場面、言葉のズレ、次に変える一つの行動
- industry_analysis: 根拠、数字の限界、導入条件、社内体制、予算制約
- comparative_review: 条件別の向き不向き、避ける条件、確認手順

UI の「記事の書き手」選択は、source理解や見出し順の主導権を持たせない。  
広報寄り、第三者寄り、実務者寄りのような文体距離の adapter として扱い、article type persona が lead angle / heading order / fact selection / paragraph emphasis / final paragraph を決める。

### 12.4 editing persona and late repair

editing persona は、single-pass draft の後半で追従性が落ちる箇所を支えるために使う。  
これは新しい別記事を作る工程ではなく、前半で置いた主題、source grounding、section role を保ったまま後半を整える bounded repair である。

editing / repair が見る主対象は次。

- 後半見出しが検査語や内部語に寄っていないか
- 最終段落が抽象語だけで閉じていないか
- 前半の主題と後半の戻り先がつながっているか
- persona の観察姿勢が source slot に負けていないか
- source contract / validation / repair / review 文が本文に漏れていないか

発火位置は、実装上は次の anchor / scope によって拘束する。

- compact plan の `heading` / `purpose` / `anchor` / `claim` / `bridge` / `do_not_cover`
- `SEMANTIC_LEDGER`
  - 節ごとの `anchor` と `claim` を保持する
  - 表現は変えてよいが、論点を落とさない
- `SECTION_SHADOW`
  - 節ごとの役割、focus、support、自然な戻り先を保持する
- diagnostics の `flagged_spans`
  - 問題のある heading / span を repair 対象にする
- `PATCH_SCOPE`
  - 変更を flag span と前後2文へ縛る
  - 未指定箇所の意味、見出し順、節の役割を保つ

したがって「後半から編集 persona が発火する」とは、後半の対象見出し・対象文・前後文を anchor で縛って編集するという意味である。  
後半だけを返す、差分だけを返す、全文を別記事として再生成する、という意味ではない。

### 12.5 regeneration persona

regeneration persona は、同一 persona による機械的な言い換えではなく、少し角度を変えた編集視点として使う。  
目的は、後半の追従性低下、article_type drift、source外 claim、抽象締めを局所的に戻すことである。

ただし current mainline の出力契約は変えない。

- repair は 1 回まで
- repair は局所編集を目的にする
- repair 出力は常に `[TITLE] / [LEAD] / [BODY] / [HASHTAGS]` を含む全文 tagged article
- partial patch-style output は reject する
- source contract / persona / validation / repair / review の内部文は本文へ出さない

### 12.6 hard-ban guard

draft / final の reader-facing body には、内部制御語や hidden instruction を混入させない。  
trial で使った検査上の hard-ban は、runtime へ直接固定語彙として増やすのではなく、visible leakage guard の考え方として維持する。

少なくとも次の系統は reader-facing body に出してはいけない。

- persona 名、観察姿勢の説明、編集者名、trial 名
- source contract の説明文
- validation / repair / review 方針
- 後半の検査メモ、確認項目、内部戻り先の見出し

meta / telemetry には検査項目として記録してよい。本文へは出さない。

## 13. GPT Image 2 Image Generation Algorithm

### 13.1 位置づけ

画像生成は本文 mainline の一部ではなく、記事生成成功後の post-success work である。  
本文生成の success path は `current_mainline_runner -> newalgorithm_pipeline -> simple_note_pipeline` のまま固定し、画像生成の失敗を記事生成の失敗へ昇格しない。

画像生成の runtime owner は `C:\tetie\notecode\note\blog_image_auto.py` とし、OpenAI Images API 呼び出しは `C:\tetie\notecode\note\llm_client.py` に閉じる。

### 13.2 発火タイミング

画像生成は次の条件を満たした後だけ発火する。

- 記事本文が生成されている
- deterministic postprocess と final render が終わっている
- legal / visible postcheck が記事成功扱いで通っている
- UI では記事プレビューが利用可能になっている

この時点で、記事の `title` / `lead` / `body` / `article_type` を画像生成へ渡す。  
画像生成は手動ボタンではなく自動で始まり、UI は記事プレビュー直後の画像パネルに `文字入り画像` と `文字なし画像` の 2 枠を表示する。

### 13.3 表示コピー推論

文字入り画像に入れる短い日本語コピーは GPT-5.4-mini が推論する。  
入力は生成済み記事の title / lead / body / article_type とし、構造化メモとして次を渡す。

- 主題エンティティ
- 主要焦点
- deterministic fallback copy

コピーは 6〜18 文字を目安にし、記事のコア主題を落とさない。  
GPT-5.4-mini の出力が抽象的、汎用的、または主題エンティティを欠く場合は deterministic fallback を使う。

### 13.4 画像プロンプト

1 記事につき、同じ画像サイズで必ず 2 系統を作る。

- `with_text`
  - 文字入り画像
  - 推論した日本語コピーを exact quoted text として 1 回だけ入れる
  - 余計な文字、数字、ロゴ、署名、透かしは禁止
- `without_text`
  - 文字なし画像
  - 文字、英字、数字、看板、UI 文字、ロゴ、署名、透かしは禁止

GPT Image 2 では、日本語タイポグラフィ、配置、主題との関係、情報量をモデルへ任せる。  
prompt 側は「記事内容に合うこと」「主題が見えること」「最低 15% 以上の clean breathing room を残すこと」「雑然とさせないこと」だけを残す。

active image prompt は、共有 style cue として `editorial` / `編集調` を使わない。  
記事別の主題・文脈、exact quoted text 1 回、余計な文字・ロゴ・透かし禁止、最低 15% 以上の clean breathing room は維持する。

`simple` / `balanced` / `rich` は固定の要素数ではなく、カバーの方向性を示す弱いガイドである。  
要素数や背景情報量は GPT Image 2 が記事内容に合わせて決める。

### 13.5 API contract

画像生成 API は `gpt-image-2` alias を使う。snapshot `gpt-image-2-2026-04-21` は docs / validation 上の確認値として記録し、runtime では alias を優先する。

現在の基本 contract は次。

- size: current configured size `1536x1024`
- text image quality: `medium`
- no-text image quality: `low`
- output_format: `jpeg`
- background: `opaque`
- moderation: `auto`

GPT Image 2 では次を送らない。

- `input_fidelity`
- `background = transparent`
- SDK が受け付けない unsupported params

token / cost は API usage が返った場合だけ実測として記録する。usage が返らない場合、docs calculator 相当の見積もりは live validation note へ留め、実測 cost としては保存しない。

### 13.6 Error / Regeneration Rule

画像生成は variant 単位で fail-open とする。  
片方だけ失敗しても記事本文と成功した画像は保持する。

各 variant の初回生成が失敗した場合は、エラーがプロンプト簡略化や再生成で回復しそうな種類なら、simplified retry prompt を組み直して 1 回だけ再生成する。  
認証、権限、課金、API key 不備のように prompt 修正で直らないエラーは再生成せず、ログに記録して fail-open にする。

retry 後も失敗した場合は、それ以上の画像再生成を行わない。  
記事生成結果は成功のまま残し、UI には非ブロッキング警告を表示する。

### 13.7 Logging

画像生成 run は `C:\tetie\notecode\logs\gpt_image2_blog_image_auto_2026-04-22\` に JSON で保存する。  
少なくとも次を記録する。

- run id / created_at / elapsed_ms
- title / article_type / display_text
- model / size / quality / output_format / background / moderation
- variant key / status / image path
- primary prompt / retry prompt / retry count
- error message
- usage / cost fields when returned by API
