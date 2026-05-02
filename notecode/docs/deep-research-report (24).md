# notecode における branding/company introduction の修復非作動分析

## notecode の目的と現行 success path の全体像

`notecode`（コトメイク）は、URL / PDF / テキスト入力と UI 選択（記事タイプ、話者、読者など）を `input_contract_v1` として正規化し、**AI っぽさが目立たない自然な日本語ブログ文**を安定的に生成することを主目的に設計されています。ここで言う「自然さ」は、改行の呼吸、一人称や話者の一貫性、主語省略の自然さ、文末の単調さ回避、ブログとしての流れ（読ませ方）の一貫性を重視しています。fileciteturn0file0

現行の本文生成は、`note_writer_app.py`（UI shell）→ `current_mainline_runner.py`（route 解決と payload 組み立て）→ `newalgorithm_pipeline`（契約・監査・投影）→ `simple_note_pipeline`（`MinimalPipeline` による本文生成）という **単一路線（mainline）** を原則とし、競合する複数ルートの補正（旧 AB 的な並列経路）を排しています。fileciteturn0file0

アルゴリズム骨格（v2 固定骨格 / Non-Negotiable）は、次の順序で定義されています。fileciteturn0file0

- Contract Resolve（UI 入力を契約として確定し、追跡可能にする）
- Source Digest（根拠素材を圧縮・整理する）
- Optional Semantic Plan Prepass（条件付きで意味レイヤの固定を先に行う）
- Single-Pass Body Generation（本文は原則 1 回で仕上げる）
- Deterministic Note Postprocess / Rule Check（整形・ルール検査は決定的に行う）
- Score-Based Quality Guard / Optional Single Surface Repair（スコアで監査し、必要なら **単回の surface-only repair**）
- Output / Telemetry（結果と監査ログを保存する）

この設計は「後段の多重リライトで整える」流儀ではなく、**意味を先に固定（semantic ledger / plan）し、本文は single-pass で自然さを出す**ことを中心に据えています。fileciteturn0file0

また、AI っぽさの既往原因としては、主題の二重三重注入（`topic` / `topic_statement` / `must_cover` / formatter など）、低信号 source facts の混入、prompt 過密、formatter の契約直写し、guard の過剰拘束が主要因として整理され、`focus_bundle.main_focus` を正本化する等の「契約の一本化」が実施済みです。fileciteturn0file3

## repair / acceptance / patch path の責務と、mainline での位置

現行 mainline における repair は、「生成のやり直し」ではなく、**本文生成後の監査（quality guard）で検知された “surface 側の問題” を最小範囲で直すための optional な単回処理**として位置づけられています。fileciteturn0file0

責務を分解すると、repair 周辺は概ね次の 3 つの役割を持ちます。

**検知（detect）**  
品質ゲート（quality guard）は、契約逸脱（話者不整合・禁止話題逸脱など）を hard block、自然さ指標（文末単調など）を observe-first / warning 寄りで扱う方針を基本にしつつ、`ai_index` や文末監視（`same_ending_runs`、加えて `ending_bucket_counts`/`ending_bucket_monotony_score` など）をテレメトリとして保持します。fileciteturn0file0

**適用可否判定（scope / eligibility）**  
repair は “いつでも何でも直す” のではなく、対象範囲（semantic ledger がある場合は claim/anchor を壊さない）や、限定された局所 issue（例：`ending_bucket_monotony`、`heading_reanchor` など）に絞って適用する設計です。さらに **flagged span patch** は `PATCH_SCOPE` で変更範囲を前後 2 文に縛り、全面リライトへ転ばないことが明記されています。fileciteturn0file0

**受理（acceptance）**  
repair を実行したとしても、それが本文へ反映されるには「修正を採用してよい（安全で、劣化を起こしていない）」という acceptance 側の判断が必要になります。この役割は、契約違反を増やさず、意味レイヤ（claim/anchor）を保持し、目的の指標（例：文末単調）を改善しているかを確認するための “採用判定” です。現 package では、この repair/acceptance が **検知だけで止まり、本文へ効いていない可能性**が重点論点になっています。fileciteturn0file1fileciteturn0file5

ここで重要なのは、repair を「文章を良くする魔法の仕上げ」ではなく、**mainline の責務分担（single-pass + deterministic postprocess + quality guard）を壊さない範囲での局所回復手段**として扱っている点です。したがって、repair が非作動のときに起きることは「検知はしているのに、設計上 “直す手” が本文に反映されない」＝品質が下がったまま success として返る、という現象です。fileciteturn0file0fileciteturn0file1

## branding/company introduction の症状と、UI role 改善の影響範囲

対象症状は、branding/company introduction における `flat_or_repetitive`、説明カード化、後半の言い換え重複、文末の単調さ、抽象名詞過多などで、role 語やメタ説明が surface に出ると不自然さが増幅する、という観測が共有されています。fileciteturn0file5

UI 側については、role/speaker の曖昧さが本文へ直結しやすい（追従性の高いモデルが “曖昧な立場語” をそのまま話者正本として扱いがち）という学びが記録され、`運営側` のような曖昧ラベルを current UI へ戻さない方針が固定されています。company introduction では `自動（おすすめ）` / `企業広報として語る` を keep し、曖昧な role 語の露出を避ける guard も追加されています。fileciteturn0file4

一方で、UI role clarity が改善されても visible quality が十分に戻っていないことから、**UI 起点の “話者曖昧さ” は主要因から後退している**一方、mainline 内側（route ownership / style owner / defaults / repair/acceptance）の問題が残っている、という切り分けが現状の前提になっています。fileciteturn0file5fileciteturn0file1

この切り分けは、過去の root cause map が示した「UI と runtime 契約のズレ」「契約の重複保持」「formatter の契約直写し」などを解消してきた流れとも整合します。つまり、UI を改善しても残る “後段の平板化・反復” は、UI ではなく mainline の **生成 owner / style owner / repair の作動条件**側に原因がある可能性が高い、という位置づけです。fileciteturn0file3fileciteturn0file1

## telemetry が示す repair non-actuation の根拠

現行 package の中心的な根拠は、「単に repair trigger が弱い」のではなく、**repair を本文へ反映するパス（patch path / acceptance）が scope 側で詰まっている**という点にあります。fileciteturn0file1fileciteturn0file2

具体的には、最新の baseline で次が同時に成立しています。

- 文末単調系の指標が強く悪化している（例：`ending_bucket_max_run = 29`、`ending_bucket_monotony_score = 1.0`、`flat_zone_flags = 6`）。fileciteturn0file1
- それにもかかわらず、`repair_applied = false`、`patch_path_used = false` のまま success としてレンダリングされている。fileciteturn0file1fileciteturn0file2
- さらに downstream telemetry として、`patch_path_refusal_reason = compact_plan_scope_ineligible` が記録されている。fileciteturn0file1fileciteturn0file2

この組み合わせは、「単調さは検知されているが、**patch path の適用対象（scope）に入れられず repair が採用されていない**」という “repair non-actuation” の説明と整合します（推定）。fileciteturn0file1fileciteturn0file2

同時に、branding/company introduction の baseline では、生成と文体の owner が branding 専用に切り替わっていない兆候も残っています。

- `primary_generation_owner = simple_note_pipeline`、`writer_of_record = simple_note_pipeline`、`route_branch = single_pass_default`。fileciteturn0file1fileciteturn0file2
- `style_profile_source = newalgorithm_pipeline.default_style_profile`、`linebreak_profile = note_standard_spacing`。fileciteturn0file1fileciteturn0file2

つまり、repair が非作動であることに加えて、そもそも **branding 向けの style control が visible surface owner になっていない**（default な単一路線のまま）という別軸も見えています。fileciteturn0file1

また、`missing_buckets = ["strength_or_history"]` といった source fit の warning が同時に存在し、company introduction の default slots（強み/歩み/提供価値）が source bucket 不足でも要求されやすく、generic filler を増やす圧として働きうる、という仮説も併記されています。fileciteturn0file2fileciteturn0file1

このため、「repair 非作動が主犯か？」は、次のように分解して答えるのが妥当です。

- **“文末単調や平板化が検知されているのに改善されない” という現象**については、repair/patch path が scope 側で拒否されていることが強い説明力を持つ（主因寄り）。fileciteturn0file1fileciteturn0file2
- **“そもそも文章がカード化しやすい / 後半で言い換えが増える” のような生成内容の質**については、style owner・defaults・source-aware plan の不足が並行して効いている可能性が高く、repair だけ直しても十分条件にならない（副因〜共犯）。fileciteturn0file1fileciteturn0file5

## root cause ranking

以下は、提示された telemetry と既存設計（ALGORITHM / package ledger）から、**「branding/company introduction の visible quality 低下」を説明する力（寄与の大きさ）**で並べたランキングです。根拠はすべて現行 docs に基づき、因果は明示的に “推定” として扱います。fileciteturn0file0fileciteturn0file1fileciteturn0file2fileciteturn0file5

| 順位 | 要因（推定） | 代表的な観測根拠 | 「repair だけではない」ポイント |
|---|---|---|---|
| 最優先 | **patch path scope（compact plan scope）外に branding が置かれ、repair が採用されない** | `patch_path_refusal_reason = compact_plan_scope_ineligible` と `repair_applied=false / patch_path_used=false` の同時成立。fileciteturn0file1fileciteturn0file2 | ここが詰まると「検知→修正」の経路が閉じ、単調さが残留する。 |
| 高 | **生成 owner / style owner が branding 用に立っておらず default 化している** | `writer_of_record=simple_note_pipeline`、`route_branch=single_pass_default`、`style_profile_source=default_style_profile`。fileciteturn0file1fileciteturn0file2 | repair が動いても、元の “語りの設計” が平板だと改善幅が頭打ちになりうる。 |
| 高 | **company introduction defaults が source-aware でなく、bucket 不足時に filler を増やす圧がある** | `missing_buckets=["strength_or_history"]`、defaults が強み/歩み/提供価値を要求しうる、という指摘。fileciteturn0file2fileciteturn0file1 | repair は surface の局所修正が主で、内容の “根拠不足→抽象化→反復” を根治しにくい。 |
| 中 | **input_contract の compression で micro-surface 指示が落ち、prompt 由来の自然さが失われる** | raw prompt の surface 指示が落ちうる、という仮説提示。fileciteturn0file1fileciteturn0file2 | repair では拾えない “最初から持っていたはずの制約” が消えると、生成が平均化しやすい。 |
| 条件付き | **output normalize が branding の段落呼吸を均しすぎる** | upstream fix 後に残る場合のみ着手、という package 条件。fileciteturn0file2fileciteturn0file1 | 先に normalize を緩めると原因の切り分けを失うリスクが高い。 |
| 低（現状） | **UI role の曖昧さ** | 既に “曖昧 role label を戻さない” が keep され、guard も追加済み。fileciteturn0file4 | 影響はあるが、現状は主因というより再発防止の維持条件。 |

このランキングに基づく結論は次の通りです。

- 「repair non-actuation（検知止まり）」は、**文末単調や flat_zone の残留**を説明する上では **主因級**です。fileciteturn0file1fileciteturn0file2
- ただし、branding/company introduction の “説明カード化・言い換え重複” まで含めた visible quality 低下全体では、**style owner / defaults / source-aware plan**が同程度に効いている可能性が高く、repair を直しても単独では十分条件になりにくい、という位置づけになります（推定）。fileciteturn0file5fileciteturn0file1

したがって、prompt-only 改善より algorithm-side fix を優先すべきか、という問いには、「はい、優先すべき」が現時点の資料からは妥当です。理由は、問題が “指示が弱い” というより **route/state/repair の責務境界（作動条件）**に見えており、prompt の付け足しは原因を隠すだけで、再発条件（state loss / scope refusal）を残しやすいからです。fileciteturn0file1fileciteturn0file0

## 最小変更での解決策

制約（success path を壊さない、prompt/module accretion を避ける、completed/frozen package を reopen しない、大規模 rewrite を避ける、owner-local で narrow）を満たしつつ、効果が見込める順に **最大 3 件**までに絞ると、次が最短経路になります。fileciteturn0file1fileciteturn0file2

**優先案 A：branding/company introduction を patch path の eligible scope に入れ、acceptance で本文反映まで通す（最小の repair 作動回復）**  
狙いは、現在の詰まり点である `compact_plan_scope_ineligible` を owner-local に解消し、「検知されている単調さ」が本文へ反映される経路を開けることです。対象 owner は package ledger で `simple_note_pipeline/pipeline.py` と明示されています。fileciteturn0file1fileciteturn0file2  
設計的には、ALGORITHM が定義する **単回・局所・surface-only** の範囲を維持し、`PATCH_SCOPE` の縛り（前後 2 文）や full rewrite を増やさない方針を守ったまま、「branding も “ending_bucket_monotony” などの局所 issue だけは patch 対象にする」形が最小です。fileciteturn0file0  
acceptance は、少なくとも `ending_bucket_monotony_score` / `ending_bucket_max_run` の改善と、話者契約系 hard block の非増加、semantic 逸脱の不発（または観測の悪化がない）を条件に “修正版を採用” するのが筋になります（推定）。fileciteturn0file0fileciteturn0file1

**優先案 B：company introduction の discourse/slot defaults を source-aware に prune し、bucket 不足時に filler を要求しない（内容側の反復圧を下げる）**  
`missing_buckets=["strength_or_history"]` が警告として存在する一方で、その不足が “強み/歩み/提供価値” を埋める圧になり、抽象名詞や言い換え重複を増やしうる、という仮説が示されています。fileciteturn0file2  
この場合の最小変更は、足りない bucket を **埋めに行く**のではなく、足りない bucket を前提にした節や要求を **最初から作らない**ことです（plan prune）。これは prompt accretion ではなく、`natural_blog_core.py` の “genre / style / discourse prompt contract” に寄せた owner-local な修正として扱えます。fileciteturn0file0fileciteturn0file1  
期待効果は、repair が直しにくい「内容の根拠不足 → 抽象化 → 反復」という流れを upstream で減らすことです（推定）。fileciteturn0file5fileciteturn0file2

**優先案 C：input_contract の compression で落ちる micro-surface 指示を “最小限だけ” 保持し、style owner に届く形で渡す（state loss の回復）**  
現 package は、raw prompt の micro-surface 指示が contract compression で落ちる可能性を挙げています。fileciteturn0file1  
ここでの最小変更は、`prompt_raw` を本文へ再掲するのではなく、**落ちやすいが効く 1〜2 要素だけを contract 側に残し、writer prompt の `[STYLE]` などへ “短い bounded memo” として伝える**ことで、state loss を抑える方向です（推定）。fileciteturn0file0fileciteturn0file2  
これは prompt accretion ではなく、既存の contract-first 設計の範囲で「状態の受け渡し」を回復する修正なので、成功パスを壊さずに効かせやすい類型です。fileciteturn0file0fileciteturn0file1

上記 3 件の関係は重要で、A（repair 作動回復）は “症状を残留させないための出口” を開け、B/C は “そもそも平板化・反復に落ちにくい入口” を整えます。A だけで十分条件にならない可能性がある一方、A を直さずに B/C だけ進めると「検知はしているのに直らない」状態が残り、観測の解釈が難しくなります。fileciteturn0file1fileciteturn0file2

## 先にやる一手と、避けた方が良い対策

**先にやるべき一手**は、「branding/company introduction の `compact_plan_scope_ineligible` を解消し、patch path が作動し acceptance で本文へ反映されること」を、最小の回帰範囲で確認することです。理由は、現 baseline が “検知止まり” を強く示しており、ここを通さない限り、以後の改善（defaults や style）の効果が **repair 非作動の残留**に隠れて判別しづらいからです。fileciteturn0file1fileciteturn0file2

**やらない方がいい対策**は、資料上すでに “blocked / not adopted” とされている方針と整合させるのが安全です。具体的には、prompt-only 強化を先に始めること、persona 拡張を初手にすること、formatter の regex 追加で branding を救うこと、成功パスを崩す全面 rewrite から入ることは避けるべき、とされています。fileciteturn0file2fileciteturn0file1

加えて UI については、role clarity の keep が再発防止として明確に位置づけられているため、`運営側` のような曖昧 role label を戻す方向は避け、現行の UI role 選択肢（company introduction は “自動/企業広報” を中心）を維持するのが妥当です。fileciteturn0file4