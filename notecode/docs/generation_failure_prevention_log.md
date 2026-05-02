# 生成失敗再発防止台帳

最終更新: 2026-03-07
対象: `C:\tetie\notecode` の `zero_base_v2` 生成経路

## 目的
- 同種失敗（指示と本文の乖離、商品説明欠落、抽象定型句化）の再発を防止する。
- 失敗を reason code と計測値で再現可能にし、同じ対処を繰り返さない。

## 運用ルール（固定）
1. ユーザー指示プロンプトを最優先に扱う（骨格・見出し・本文重心）。
2. 本文はソース由来情報を主根拠に生成する。
3. URL周辺情報の補完は LLM 知識で許容するが、指示と矛盾する拡張は禁止。
4. fail-closed は入力不足・話者契約違反・禁止話題逸脱を中心に適用し、自然さ指標だけでは停止しない。
5. 契約整合系の system block は停止前に1回だけ自動補修リトライし、再失敗時のみ fail-closed へ移行する。

## 失敗記録

### F-2026-04-02-03
- 症状:
  - section の均一感対策として、`HARD_CONTRACT` に「箇条書きのように短文を空行で積まず、つながる説明は同じ段落でまとめる」を追加した rerun が悪化
  - 3 case rerun の `codex-section-rhythm-20260402-r4` で `branding 8 -> 6`、`announcement 8 -> 7`
  - live artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-section-rhythm-20260402-r4`
- 想定影響:
  - ぶつ切れ感を減らすつもりが、会社紹介やお知らせまで段落を詰めすぎて、読みやすさと自然さを落とす
  - section の厚みは変わっても、文の呼吸が重くなり、かえって説明カード感が戻る
- 根本原因:
  - paragraph reflow を prompt の hard contract で縛りすぎ、genre ごとの自然な空白の取り方まで抑制した
  - 「断片的すぎる」問題を、説明統合の強制で止めようとして可読性を落とした
- 実装対策:
  - anti-fragment paragraph bundling line は rollback する
  - 段落リズムは `HARD_CONTRACT` ではなく、section の厚み guidance と `一文だけの独立段落を連続させない` 程度に留める
- 検知条件（rollback）:
  - same 3-case rerun で `branding` または `announcement` の rubric が baseline より低下
  - 目視で段落が詰まり、息継ぎ位置が減って読みにくくなる

### F-2026-04-02-02
- 症状:
  - section の均一感対策として `compact plan` に `span=lean|standard|thick` を追加し、`SECTION_RHYTHM` block を generation prompt に直持ちした rerun が不安定化
  - 3 case rerun の `codex-section-rhythm-20260402-r1` で `branding 8 -> 7`、`announcement 6 -> 6` のまま、`explanatory` は本文が痩せて sentence break も不自然になった
  - live artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-section-rhythm-20260402-r1`
- 想定影響:
  - 見出しごとの厚みは散るが、本文が「plan を守るための圧縮」に寄り、自然な膨らみを失う
  - title や本文の自然さが落ち、company introduction では説明の厚みより人工的な配分が前に出る
- 根本原因:
  - section rhythm を plan schema と generation block の両方で具体指定し、単一 pass の書き手に配分制約を与えすぎた
  - 量の散らし方を明示しすぎて、内容のまとまりより配分遵守が優先された
- 実装対策:
  - `span` schema / `SECTION_RHYTHM` block は rollback する
  - keep するのは `STRUCTURE` 側の軽い guidance と company introduction 向けの「導入や締めはやや短め」程度に留める
- 検知条件（rollback）:
  - `branding` rubric が baseline を下回る
  - `explanatory` で body が不自然に短くなり、sentence break の違和感が増える

### F-2026-04-02-01
- 症状:
  - `bl-branding-values-stance` の company introduction 再調整で、`HARD_CONTRACT` に company voice を強く入れた rerun が `rubric 8 -> 6` に悪化
  - 会社視点は出るが、社名・会社主体の出し直しが強すぎて本文が平坦になり、`source_grounding_reflection_ratio=0.6667` まで低下
  - live artifact:
    - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-branding-perspective-20260402-attempt1`
- 想定影響:
  - 「誰視点」を強めるつもりが、説明カードのような均一な本文になり、会社紹介としての自然さを損なう
  - source fact の残り方が薄くなり、branding/company introduction の grounding が落ちる
- 根本原因:
  - `prompt_builder.py` の company introduction 向け voice 指示を `HARD_CONTRACT` に直入れし、見出し冒頭の話者再アンカーを強制しすぎた
  - tone 制御より contract 制御が前に出て、section ごとの自然な膨らみより「条件を守る言い回し」が優先された
- 実装対策:
  - failed hypothesis は rollback し、company voice 指示は `HARD_CONTRACT` から撤去する
  - 2回目の fix では、同じ要件を `STRUCTURE` の軽い guidance に移し、`社名や『当社』を機械的に繰り返さない` を明示する
  - style learner / quality guard 側の feature extraction 正常化は keep し、variation 指標の zero fallback は戻さない
- 検知条件（rollback）:
  - same case rerun で `rubric_total` が baseline より低下
  - `source_grounding_reflection_ratio < 1.0`
  - `human_visible_ai_feel=flat_or_repetitive`

### F-2026-03-06-03
- 症状:
  - `speaker_profile` が経営者視点でも、本文が「私たち」視点・第三者ナレーション・読者への一般助言に混在
  - `alignment_score=1.0` でも `speaker_consistency_score=0.35` / `pronoun_consistency_score=0.0` が表示停止に結び付かない
  - `latest_generation_quality_report.json` 上位の `flat_zone_count` と failure 内の値が乖離し、現場判断を誤らせる
- 想定影響:
  - 読者に「誰が誰に語っているか」が伝わらず、企業記事としての信頼を損なう
  - スコア上は正常に見えても、実文では不自然な記事がSaaS表示される
- 根本原因:
  - `zero_base_v2` 本流で sanitize 系抑制が section/postprocess に未接続
  - output guard が `speaker/pronoun/relationship` を hard 条件として扱っていなかった
  - `forbidden_topics` が `branding` 偏重で、会社紹介/経営者視点 drift を十分に抑止できなかった
  - quality report の `flat_zone_count` が fingerprint 依存で、hard-soft metrics の値を落としていた
- 実装対策:
  - section prompt に `speaker_profile` / `relationship_mode` / `register_policy` / `allowed_pronouns` を注入
  - section 生成後の軽量 contract check と1回再生成を導入
  - minimal postprocess に `Phase7Sanitize` 相当を接続
  - guard に `SYS_SPEAKER_CONTRACT_MISMATCH` / `SYS_FORBIDDEN_TOPIC_DRIFT` を追加
  - quality report の `flat_zone_count` は hard-soft metrics を優先する
- 検知条件（出力停止）:
  - `speaker_consistency_score < 0.55`
  - `pronoun_consistency_score < 0.50`
  - `relationship_consistency_score < 0.50`
  - `section_contract_issue_count > 0`

### F-2026-03-06-04
- 症状:
  - 会社紹介や解説記事でも section ごとの prompt が禁止列挙に寄りすぎ、本文が無難で平坦になりやすい
  - 後段の品質評価が強すぎると、自然さ不足だけで fail-closed が多発し、SaaS利用回数を無駄にする
  - `zero_base_outline` だけでは 4000字級本文の談話設計が粗く、長文で論点の橋渡しが弱い
- 想定影響:
  - 文章が「正しいが人間らしくない」状態に寄る
  - 表示停止が増え、生成品質改善より reject 対応に工数が流れる
- 根本原因:
  - 長文用の中間表現が `heading / new_information / reader_question` に限定されていた
  - section prompt が短い肯定形ではなく、禁止と抑制の列挙に寄っていた
  - 自然さ指標と契約違反が同じ hard gate に近い扱いだった
- 実装対策:
  - `note_4000` planner を導入し、`topic_seed` / `related_terms` / `bridge_hint` / `intent` を内部 state として保持
  - `natural_style_profile` を導入し、register / linebreak / ending variation を section 生成の入力へ移した
  - section prompt を短い肯定形へ置換し、`直前要約` と `ユーザー指示（最優先）` を固定注入
  - note本文経路の `hard_soft_eval` を observe-only へ緩和し、自然さ不足は soft warning で監視する
- 検知条件（監視）:
  - `semantic_issue_count >= 5`
  - `heading_alignment_mean < 0.12`
  - `review_points` に構成リスクが残る
  - `section_contract_reports` は0だが本文が平坦な場合、prompt 設計側を再評価する

### F-2026-03-06-01
- 症状:
  - タイトルが商品ブランディングなのに本文がチーム/連携中心へ逸脱
  - 「具体例を挙げると」の後が具体化されず、抽象語が連続
  - 商品説明・価値訴求の本文比率が低く、販売/紹介ブログとして破綻
- 想定影響:
  - 目的不達によるUX悪化
  - 誤品質判定（スコア高でも実利用価値が低い）
- 根本原因:
  - ブランディング見出しプールに商品軸と競合する見出しが混在
  - `zero_base_v2` 経路で hard/soft/contextual 評価が未発火のまま `off` 相当で通過
  - contract alignment が prompt/source の核語被覆を十分検知できていない
- 実装対策:
  - 商品ブランディング見出しプールを商品価値・選定軸・活用シーン中心へ再編
  - `zero_base_v2` の最終段で quality signals（contextual/hard-soft/final eval）を必ず評価
  - contract alignment に以下指標を追加し、UI guard へ連携
    - `prompt_anchor_coverage`
    - `anchor_term_coverage`
    - `section_focus_coverage`
  - guard reason code 追加: `SYS_CONTRACT_ALIGNMENT_MISMATCH`
  - interview回答の文脈シグネチャ管理を導入し、古い回答の混入を防止
- 検知条件（出力停止）:
  - `alignment_score < 0.45`
  - `category_mismatch_detected = true`
  - `must_cover_reflection_rate < 0.50`（must_cover>=2）
  - `prompt_anchor_coverage` と `anchor_term_coverage` の同時低下
  - `section_focus_coverage < 0.60`（section>=3）

### F-2026-03-06-02
- 症状:
  - 指示基点を強めるために prompt文全体を `must_cover` 扱いすると、本文が適切でも契約乖離判定が過敏化
  - 非採用の `branding` でも interview target に「採用候補者」が混入し、話題ドリフトを誘発
- 想定影響:
  - 正常記事の誤ブロック（false positive）
  - 商品紹介記事で採用文脈に寄るリスク
- 根本原因:
  - must_cover 反映率が「語句完全一致」寄りで長文指示に弱い
  - fallback質問のターゲット候補が文脈条件なしで採用候補者を提示
- 実装対策:
  - prompt全文must_cover強制注入を撤回（DI-12-02）
  - must_cover反映に語句アンカー一致を補助導入
  - `branding` の採用候補者提示を recruiting intent 時のみに限定（DI-12-01）
  - prompt-anchor hard block は section focus 低下時に限定
- 検知条件（監視）:
  - `must_cover_reflection_rate` が急低下しつつ `section_focus_coverage` が高い場合は閾値誤作動を疑う
  - 非採用文脈で target options に「採用候補者」が出たら設定不整合

## 再発防止チェックリスト
- [ ] 骨格「誰が誰に向けて書くか」が `input_contract` に存在する
- [ ] section prompt に `speaker_profile` / `relationship_mode` / `register_policy` / `allowed_pronouns` が注入されている
- [ ] タイトル主題と見出し主題が一致している
- [ ] 商品/サービスの説明・価値・選定観点が本文に明示される
- [ ] `speaker_consistency_score` / `pronoun_consistency_score` / `relationship_consistency_score` を監査ログで確認した
- [ ] `section_contract_reports` と `contract_alignment_reason_codes` が保存されている
- [ ] `zero_base_discourse_plan` と `natural_style_profile` が保存されている
- [ ] naturalness 指標は warning として確認し、hard stop 条件と混同していない
- [ ] guard 停止時、`ui_guard_retry_count` と再試行後 reason_code を監査ログで確認した
- [ ] prompt injection / prompt echo / data leakage / fail-open の対策を維持
- [ ] blocked時は reason code と failed_parameters を監査ログへ保存

## 2026-03-07 phase05 完了後の固定ルール

- `must_cover` に audience / perspective / ガード文を再注入しない
  - 例: `一般読者`, `〜視点`, `主題から逸脱しない`
- `topic_statement` は prompt 主題を優先し、`interview_answers.perspective` のメタ値を流用しない
- `contract_alignment` へ `topic_statement / must_cover_items / audience_profile / question_source_counts` を必ず保存する
- branding 系では `私` と `わたし` を等価の許容一人称として扱い、表記差だけで話者契約違反にしない
- company introduction のような説明系ケースでは、`topic_statement` を空欄で通さず、prompt 主題から補完する

## 関連ファイル
- `note/article_generator.py`
- `note/note_writer_app.py`
- `PLAN5/phase11_prompt_priority_alignment_hotfix.md`
- `PLAN5/phase11_result_2026-03-06.md`
