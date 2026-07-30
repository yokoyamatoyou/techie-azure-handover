# セルフパースペクティブ型日本語ブログ生成のための設計フォローアップ

## 概観

**結論だけ先に言うと、次の実装スコープは「source handoff 単独」でも「generation 単独」でもなく、`late-half quality audit → anchor-based repair target handoff → bounded local repair` の境界を主対象にした、狭い combined boundary 修正に置くべきです。** ただし、その中心は repair handoff です。今回の実験ログでは、主要な失敗は source grounding ではなく、repair の局所性が失われて本文全体が圧縮・再構成されてしまうことでした。したがって、優先順位は **repair handoff が最優先、audit alignment が次、generation contract はその後に最小追加、source handoff は小幅な補強だけ** です。（添付 `05_generation_method_diagnosis.json` 27–80行、`04_anchor_patch_route_plan.md` 16–59行、`06_anchor_handoff_implementation_summary.json` 19–41行）

**実質的なボトルネックは、source packet の事実性不足ではなく、「局所修復すべき問題が、局所修復としてモデルに渡っていないこと」です。** case_003 では unsupported claims 0、source grounding warnings 0、must-cover warnings 0、internal leakage 0 で、失敗は `ending_bucket_monotony` を直そうとした repair candidate が本文全体を 1825字から 1522字へ縮め、fail-closed acceptance に正しく弾かれたことでした。つまり、acceptance は壊れておらず、target handoff が弱すぎた、という診断がもっとも整合的です。（添付 `05_generation_method_diagnosis.json` 27–55行、`04_anchor_patch_route_plan.md` 27–38行）

前回レポートの大きな方向性――「素材化してから one-pass で書き、後半重点の監査と局所修復を入れる」――自体は、今回の添付仕様とも矛盾していません。むしろ今回のファイル群は、その方向性のうち **repair handoff だけがまだ甘い** ことを示しています。これは、近年の長文処理研究が示す「長い文脈では位置バイアスが起きやすい」こと、そして最新の entity["company","OpenAI","ai company"] 公式ガイドが「outcome-first」「短い personality」「per-response writing controls」「prompt を肥大化させない」ことを勧めている流れとも一致します。citeturn0search0turn4view0turn4view2turn5view1turn4view5

## ソース素材化と生成契約

**source handoff は全面改修ではなく、小さく強くするべきです。** 現行の experimental source-materialized generation route は、すでに `must_use`、`explicit_mentions`、`implicit_style`、`later_recall`、`no_inference`、`avoid_expression`、`source_coverage_expectation` を持っており、source prose をそのまま smooth summary にしないという方針も正しいです。（添付 `02_experimental_route_spec.md` 128–174行） 前回レポートも、source は「読みやすい要約」ではなく「事実オブジェクト」として扱い、記事タイプ別に `must_use / optional_background / implicit_style / explicit_mentions / later_recall / hard_facts / no_inference` へ振り分けるのがよいと整理していました。（添付 `01_previous_deep_research_report.md` 69–81行）

そのうえで、**self-perspective を安全に成立させるために source packet に追加すべきなのは、自由な一人称スタンスではなく、`safe reflective angle` と `self-reference mode` です。** 私の推奨 schema は次です。

- `writer_position`: `implicit_author | editorial_we | neutral_internal_voice`  
- `reader_problem`: 読者がいま解きたい具体的な問い  
- `must_cover_facts`: 事実として必ず触れる要素  
- `do_not_claim_boundaries`: 言ってはいけないこと  
- `no_personal_fabrication`: 体験・判断・成果・保証の捏造禁止  
- `safe_reflective_angles`:  
  - 何を先に押さえるべきか  
  - どこに注意を置くべきか  
  - どの対比が効くか  
  - どの具体を後半で回収すべきか  
- `stance_moves_allowed`: `selection | emphasis | contrast | caution | reflection_without_experience`
- `personalization_limits`:  
  - 「見た」「使った」「感じた」「話した」「試した」は source に根拠がない限り禁止  
  - 「〜と考えています」も、運営主体の source evidence がない限り禁止  
- `closing_recall_candidates`: 終盤で戻る具体要素  
- `transition_materials`: 段落をつなぐための原因・対比・条件・例外  
- `forbidden_article_shapes`: `third_party_intro`, `textbook_explanation`, `generic_listicle`, `source_by_source_summary`

この構成なら、モデルは「書き手の視点」を **経験の捏造ではなく、焦点の置き方・段落の寄せ方・締め方** として使えます。これは、OpenAI の prompt guidance が customer-facing prose で「personality」と「writing controls」を分けるべきだと述べ、自然な prose には persona、channel、emotional register、formatting、hard length limit の指定が効くと明示していることとも合います。citeturn5view0turn5view1turn5view2

**逆に packet に入れないほうがよいものもはっきりしています。** 入れないほうがいいのは、長い要約 prose、ブランド賛辞の下書き、擬似的な人間味指示、長い persona lore、role labels の重ね貼り、source contract そのものを prose 化した文章、URLごとの説明文、そして「人間らしく」「自然に」といった粗い抽象指示です。現行 spec でも `Do not rewrite source contract as article prose`、`Do not expose material bucket names in visible text`、`Do not add persona names to visible output` とされており、この方向は維持すべきです。（添付 `02_experimental_route_spec.md` 170–174行） 生成前の packet を長い滑らかな日本語にしてしまうと、その時点で「AIっぽい要約文体」が本文へ伝播しやすくなります。前回レポートでも、query-focused / article-type-aware な素材化へ寄せるべきだと整理されていました。（添付 `01_previous_deep_research_report.md` 75–81行）

**generation contract は、今の “compact outcome-first” を壊さずに、self-perspective を安全に定義する一枚だけを足すのがよいです。** いまの spec はすでに「one-pass」「continuous flow」「no section-by-section independent generation」「no prompt accretion」「2000字前後では outline split を使わない」としており、これは正しいです。（添付 `02_experimental_route_spec.md` 176–207行） 追加すべきなのは次のような短い contract です。

```text
Perspective:
- Write as an internal-facing blog writer with legitimate standing to frame the topic,
  but do not invent lived experience, action taken, measurement, conversation, or outcomes.
- Self-perspective means selection, emphasis, contrast, caution, and reflective framing only.
- If first-person would imply experience not present in source, use implicit author voice instead.

Article shape:
- One continuous blog article, around 2000 Japanese characters when supported.
- Do not default to many headings or listicle structure.
- Prefer 5–7 paragraphs; vary paragraph length.
- Do not summarize sources one by one.

Flow:
- Opening: anchor on one concrete reader problem, scene, or point of friction from the packet.
- Middle: unfold mechanism / example / caveat with source-backed specifics.
- Late half: recall one earlier concrete item instead of drifting into generalities.
- Ending: close on a narrowed takeaway, not a generic moral.

Japanese rhythm:
- Avoid 3 or more consecutive sentences with the same ending bucket.
- In the final 3 sentences, use distinct functions: recall / narrow / close.
```

この contract は「人格を厚くする」のではなく、**記事の視点・形・終盤の役割** を固定します。OpenAI の docs でも、GPT-5.4 は persistent personality と per-response writing controls を分けると customer-facing prose をよりうまく制御できるとされ、また reasoning モデルには「think step by step」のような chain-of-thought prompts を避け、短く直接的な指示を使うべきだとされています。citeturn5view1turn4view4turn4view5

**日本語の終盤単調化は、単語禁止ではなく、終盤の機能分化で抑えるべきです。** ここで効くのは「同じ語尾を禁止する」ではなく、最終3文を `事実回収 / 角度を絞る / 余韻を閉じる` に分けることです。段落ごとにも `観察 / 背景 / 具体 / 例外 / 回収` の役割を軽く持たせると、第三者説明調や教科書調に寄りにくくなります。これは前回レポートの「later_recall を後半で回収する」「結論は general moral で閉じない」という提案とも整合します。（添付 `01_previous_deep_research_report.md` 86–101行） また、長いコンテキストでは中ほどの情報が使われにくいという long-context 研究を踏まえると、後半で earlier concrete を再投入する設計は理にかなっています。citeturn0search0turn5view1

## 修復ハンドオフと受理原則

**repair handoff は、いまの実験群を見る限り、もっとも優先度が高い改善点です。** 診断ファイルは、materialization を「partial gap not root cause」、generation prompt を「secondary gap」、late-half audit を「handoff gap」、optional repair target handoff を「primary gap」、repair acceptance を「not_the_gap」と分類しています。（添付 `05_generation_method_diagnosis.json` 56–80行） つまり、直すべき対象は「acceptance を緩めること」ではなく、「repair が局所書き換えとして成立するよう、warning を concrete target に変換すること」です。

**そのため、repair target handoff schema は、最低でも次の fields を持つべきです。**

- `issue_type`
- `target_section_id`
- `target_section_heading`
- `target_paragraph_indices`
- `target_sentence_ids`
- `target_sentence_excerpts`
- `left_anchor_sentence_id`
- `left_anchor_sentence_text`
- `right_anchor_sentence_id`
- `right_anchor_sentence_text`
- `repeated_ending_class`
- `local_run_length`
- `allowed_operation`
- `protected_section_ids`
- `protected_section_hashes`
- `required_material_claim_ids_to_keep`
- `material_recall_hint`
- `title_must_preserve`
- `lead_must_preserve`
- `hashtags_must_preserve`
- `headings_must_preserve`
- `non_target_copy_required`
- `target_char_budget_min`
- `target_char_budget_max`

添付の anchor patch plan はすでに、その骨格をかなり正しく捉えています。`section_anchors` と `sentence_anchors` を deterministic に作り、`target_section_heading`、`target_sentence_ids`、`left_anchor_sentence_id`、`protected_section_ids`、`required_material_claim_ids_to_keep` を repair へ渡す方針は妥当です。（添付 `04_anchor_patch_route_plan.md` 61–132行） 実装 summary でも、blank section heading を sentence/section anchors から回復し、`rewrite only target sentence cluster and immediate neighbor`、`do not compress, summarize, reorder, or rewrite non-target sections`、`keep title/lead/hashtags/headings` を repair prompt に入れる設計がテスト済みです。（添付 `06_anchor_handoff_implementation_summary.json` 19–41行）

**bounded local repair の visible output contract は、full tagged output のままで構いません。** ただしその意味を、「全文自由再生成」ではなく、**“元の全文を再掲しつつ、target cluster と immediate neighbor だけを書き換える reconstruction”** に変える必要があります。添付 plan も、current parser の都合で full tagged article を維持しつつ、`ANCHOR_PATCH_HANDOFF` で局所性を強制する方針を採っています。（添付 `04_anchor_patch_route_plan.md` 124–132行） これは broad rewrite ではなく、既存 contract の意味論を変える狭い修正です。

**acceptance は今の fail-closed を維持し、必要なら route-local にさらに厳しくするのが正解です。** `flagged_scope_drift` で reject されたのは誤判定ではなく、正しい安全動作でした。（添付 `05_generation_method_diagnosis.json` 77–90行） したがって accepted repair の条件は、少なくとも次にすべきです。

- unsupported claims 0  
- must-cover regressions 0  
- source grounding warnings 増加 0  
- title / lead / hashtags / headings 保持  
- protected non-target section hashes 一致  
- non-target sentence hashes 一致  
- body compression outside target anchor が閾値内  
- target issue 指標は改善  
- visible internal term leakage 0  

逆に reject 条件は、添付の evaluation matrix と anchor patch plan に忠実でよく、**threshold relaxation を要求した時点で停止**すべきです。`V1 reduces fingerprint warnings by making the article thin or generic` で reject、`V1 needs more than 1 repair loop` で reject、`V1 passes by inventing unsupported details` で reject、これはそのままでよいです。（添付 `03_evaluation_matrix.md` 161–178行、`04_anchor_patch_route_plan.md` 134–144行）

## 評価ルーブリック

**評価は、日本語 blog naturalness を「source faithful か」だけで見ず、authorial stance と repair scope preservation を分けて見るべきです。** 添付 matrix は naturalness / source faithfulness / late-half の3軸A/Bを採っていますが、今回の follow-up では self-perspective と repair containment を明示的に足したほうがよいです。（添付 `03_evaluation_matrix.md` 116–142行）

私の推奨 rubric は、各項目 0–4 点です。

- **source grounding**  
  0: unsupported / distorted  
  2: 事実は守るが素材活用が浅い  
  4: source-backed facts を自然に織り込み、誇張も不足も少ない  

- **authorial stance**  
  0: 第三者紹介文・教科書要約  
  2: わずかに視点はあるが平板  
  4: 書き手の焦点・取捨選択・対比・注意の置き方が明確で、経験捏造はない  

- **paragraph flow**  
  0: source-by-source summary / section islands  
  2: 接続はあるが論理の反復が目立つ  
  4: 各段落の役割が異なり、前段の具体が後段で回収される  

- **ending rhythm**  
  0: 終盤が単調で generic  
  2: monotony は弱いが締めが丸い  
  4: 後半も具体性を失わず、最終段落が earlier concrete を回収する  

- **absence of AI-summary tone**  
  0: まとめ調・説明調・無難な moral が強い  
  2: 一部に残る  
  4: source を説明する文章ではなく、source を踏まえて書かれた blog になっている  

- **absence of invented personal experience**  
  0: 体験・会話・使用感・結果を捏造  
  2: ぎりぎり主観表現が危うい  
  4: authorial stance はあるが経験は捏造していない  

- **repair scope preservation**  
  0: target 外が書き換わる  
  2: 軽度の drift  
  4: target cluster と immediate neighbor 以外は実質不変  

この rubric は manual A/B で使い、同時に自動指標も薄く添えるのがよいです。自動側は、`unsupported_claim_count`、`must_cover_warning_count`、`late_half monotony max run`、`body_char_delta_outside_target`、`protected_hash_change_count`、`non_target_sentence_change_count` を主指標にし、自然さは人手主導で見ます。長文文脈研究と correction survey の両方を踏まえると、post-hoc correction は有効ですが、改善したつもりで別の劣化を起こすことがあるため、**修正局所性の検査** を独立した評価軸にするのは理にかなっています。citeturn8search0turn8search2turn0search0

**この follow-up で明示的に避けるべき評価の罠は三つあります。**  
ひとつは、warning count が減っただけで「よくなった」とみなすこと。二つ目は、repair accepted を quality 向上の代理指標にしてしまうこと。三つ目は、source faithfulness と naturalness を一つの総合点に潰してしまうことです。添付 matrix も、adoption 候補にするには自然さ・faithfulness・warning の全条件を要求しており、continue_shadow / reject を分けています。この gate 設計は維持すべきです。（添付 `03_evaluation_matrix.md` 144–178行）

## 中期実装計画

**中期計画は、広い刷新ではなく、5つの narrow phase に分けるのがよいです。** すでに anchor inventory と handoff の実装・テストは入り、no-flag current route への影響なし、internal leakage なし、repair count 追加なし、threshold 変更なしまで確認されています。まだ足りないのは live validation です。（添付 `06_anchor_handoff_implementation_summary.json` 42–89行、`07_latest_longrun_blocked_summary.json` 19–37行）

**Phase A: audit-to-repair alignment**  
- owner scope: quality/audit owner  
- change: `late-half quality audit` と final quality guard の issue taxonomy を揃える  
- validation: case_003 の既存 artifact replay で、`ending_bucket_monotony` が audit 段階で repair candidate として同じ target class を出せるか確認  
- stop condition: audit が target section を決められない  
- rollback: false positive が増え、clean draft に repair を誤発火する  

**Phase B: anchor-based repair target handoff の live validation**  
- owner scope: repair pipeline owner  
- change: すでに実装済みの deterministic anchor inventory を用いて、case_003 で 1 回だけ live compare  
- validation: `flagged_scope_drift` が消え、non-target range が保持され、monotony が改善するか  
- stop condition: second call が必要になる / scope drift 再発 / visible leakage  
- rollback: repair handoff block を外し、no-flag 現行動作を維持  

**Phase C: self-perspective generation contract の最小追加**  
- owner scope: prompt owner  
- change: source packet はそのままに、generation contract へ `safe reflective angle` と `self-reference mode` を追加  
- validation: case_003 1件 + branding 1件で、第三者説明調の減少、source faithfulness 非悪化を確認  
- stop condition: unsupported claim 増加、summary tone 悪化、prompt bloat  
- rollback: self-perspective block を切り戻し、anchor repair だけ残す  

**Phase D: source handoff の小幅拡張**  
- owner scope: materialization owner  
- change: `safe_reflective_angles`, `writer_position`, `personalization_limits`, `closing_recall_candidates`, `forbidden_article_shapes` を packet へ追加  
- validation: packet inspection と 1 live case  
- stop condition: packet length 増大で prose が summary 化  
- rollback: 追加 buckets を縮小し、`must_use / later_recall / no_inference` 中心へ戻す  

**Phase E: one case から three cases へ拡張**  
- owner scope: evaluation owner  
- change: case_003 を通過したら case_001 と case_002 へ拡張  
- validation: 添付 matrix と同じく current stable baseline との manual A/B  
- stop condition: source faithfulness delta が負、または naturalness 改善が 1記事種にしか出ない  
- rollback: continue_shadow のまま固定し、採用判定を止める  

この順序にした理由は、**bottleneck の因果順に直すため**です。いま source handoff を先に大きくいじると、case_003 で観測された「repair target が弱い」という主因をぼかしてしまいます。先に repair containment を通し、その後で self-perspective を generation contract に足すほうが、因果の切り分けが可能です。前回レポートも、まず one-pass と local repair を軸に据えるべきだとしていました。（添付 `01_previous_deep_research_report.md` 86–101行）

## 次の実験と避ける設計

**最初に走らせるべき実験は、case_003 の 1 live compare です。** それも、source handoff の schema 拡張や broad prompt rewrite をまだ入れず、**anchor-based repair target handoff と audit alignment だけ** を有効にした状態で、current stable baseline と experimental source-materialized generation route を比較するのがよいです。これが通らない限り、「self-perspective block を generation に足すべきか」という次論点へ進むべきではありません。添付 summary でも、live validation 自体は network reset と private payload 制約で blocked されており、未完了項目として Phase 2 successful B2 live validation、Phase 3 self-perspective contract、Phase 5 3-case shadow compare が残っています。（添付 `07_latest_longrun_blocked_summary.json` 1–37行）

**この first next experiment の成功条件は、かなり明確です。**  
- unsupported claims 0  
- source grounding warnings 0  
- must-cover regressions 0  
- internal leakage 0  
- repair accepted であること自体ではなく、**non-target scope preserved** であること  
- target ending monotony が改善  
- body compression outside target が許容範囲内  
- manual naturalness が current stable baseline と少なくとも tie、できれば +1  
- late-half delta が +1 以上  

expand / revert / continue の判断もここで切れます。  
- **continue**: target 局所性は守れたが自然さ改善がまだ弱い  
- **revert**: scope drift が再発、または source faithfulness が悪化  
- **expand**: case_003 で局所修復が成立し、manual 自然さが非悪化以上  

この gate 運用は、添付 evaluation matrix の adopt / reject / continue_shadow 基準と一致しています。（添付 `03_evaluation_matrix.md` 144–178行）

**最後に、明示的に避けるべき設計をまとめます。**

- source handoff / generation / repair を一気に全部作り直す broad rewrite  
- current stable baseline への fallback を成功経路として混ぜること  
- threshold relaxation や broad acceptance relaxation  
- patch plan 用の追加 LLM call  
- target anchor のない full-body repair  
- 2000字前後での default section-by-section generation  
- persona 名・editor 名・contract text の visible leakage  
- 「人間らしく」「自然に」といった抽象語を積み増す prompt bloat  
- self-perspective を「一人称体験の捏造」に誤変換する設計  
- warning count を減らすために本文を薄くする設計  
- case_003 が未通過のまま 3-case rerun へ広げること  

これらは、添付の診断・patch plan・evaluation matrix がすべて non-goal として避けている方向でもあります。（添付 `04_anchor_patch_route_plan.md` 158–169行、`05_generation_method_diagnosis.json` 82–99行、`03_evaluation_matrix.md` 161–178行）

**最終判断**としては、次に着手すべき主対象は **repair handoff 単独ではなく、generation output の後半品質検知と repair target concretization をつなぐ combined boundary** です。ただし owner を一人に置くなら、**repair handoff owner** に置くのが正しいです。source handoff は「もう一度大きく作り直す」段階ではなく、generation contract は「いま直ちに広く盛る」段階でもありません。先に局所修復の境界を締め、そのあとで self-perspective を generation contract へ最小追加する。この順番が、いまのファイル群から見て最も筋の通った実装方針です。前回レポートが推した「source materialization → one-pass generation → late-half audit → bounded local repair → fail-closed acceptance」という大枠は、そのまま維持してよいです。（添付 `01_previous_deep_research_report.md` 67–101行、`02_experimental_route_spec.md` 7–10行） そのうえで、最新の OpenAI ガイドが勧める outcome-first、短い personality、writing controls の分離、prompt 単純化の方針に合わせ、長文では位置バイアスが残るという研究知見を踏まえると、今やるべきなのは「より長い prompt」ではなく「より狭い handoff」です。citeturn4view0turn4view2turn5view1turn4view5turn0search0turn8search0turn8search2