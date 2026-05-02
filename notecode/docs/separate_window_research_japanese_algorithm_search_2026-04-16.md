# separate window research japanese algorithm search 2026-04-16

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md

今回の実施範囲:
- 実装ではなく research 専用
- 世界のどこかにある既存アルゴリズム / 手法 / 論文 / 公式実装 / style guide を探索する
- 日本語特性
  - SOV
  - 膠着語
  - 主語省略
  - topic-comment
  - 文末集中
  - 段落呼吸
  を考慮し、他言語向け手法を日本語向けに改良できるかを調べる
- mainline / current success path / experimental owner files は変更しない
- AGENTS / WORKLOG / package docs は触らない
- コード実装しない

目的:
- 「別のアルゴリズムを考えるべきか」を感覚で決めず、
  日本語 long-form / blog-like generation に効きそうな既存 line を探索して
  adopt 候補 / reject 候補 / 日本語向け改造ポイントを整理する

research の前提:
- 現在の local keep judgment は尊重する
- 現行 keep を壊すための検索ではなく、future separate line 候補を探す
- prompt accretion を正当化するための research にしない
- 「LLM が弱いから全部 rule に戻す」極論に走らない
- 「日本語は難しい」だけで止めない

探索テーマ:
1. 他言語で使われている long-form generation / content planning / discourse planning / revision / style control のアルゴリズム
2. 日本語生成で重要な言語学的特性
   - SOV
   - topic-comment
   - zero pronoun / omission
   - sentence-final load
   - agglutinative morphology
   - connective use
   - paragraph cohesion
3. 日本語 technical writing / explanatory writing / blog writing の公式 style guide
4. 日本語の discourse / rhetoric / text linguistics 研究
5. 他言語アルゴリズムを日本語化するときに必要な改造点
   - section ordering
   - sentence ordering
   - old/new information placement
   - paragraph breath
   - ending variation
   - reference / omission control
   - revision constraints

優先する source:
- 一次ソースを優先
  - ACL / EMNLP / NAACL / COLING / LREC-COLING / EACL などの論文
  - arXiv の原論文
  - university / lab project page
  - official documentation
  - official style guide
- secondary source を使う場合は、一次ソースが弱い箇所の補助に限定
- generic な AI writing tips 記事は source-of-truth にしない

探索で必ず見たいキーワード例:
- discourse planning text generation
- content planning long-form generation
- revision planning NLG
- sentence aggregation NLG
- document planning rhetoric structure generation
- Japanese text generation discourse
- Japanese cohesion paragraph writing
- Japanese technical writing style guide
- Japanese zero pronoun generation
- Japanese information structure topic comment generation
- Japanese sentence-final expression variation
- Japanese agglutinative text generation
- multilingual NLG morphology-aware planning
- planning based generation for low-resource / morphologically rich languages

明示的に調べるべき問い:
1. 既存 long-form generation アルゴリズムで、LLM 前提でも使えそうな structural layer は何か
2. 日本語では、英語向けアルゴリズムのどの前提がそのまま使えないか
3. 日本語では paragraph / sentence / clause のどの単位で制御したほうが自然さが出るか
4. SVO 系の「front-load everything」が日本語ではどこで不自然化するか
5. 日本語の自然さを改善するなら、
   lexical rule より discourse / information placement を先に制御すべきか
6. revision / post-edit アルゴリズムで、日本語に相性がよい制約は何か
7. future candidate を作るなら、
   current codebase に対して narrow に試せる algorithmic slice は何か

do not:
- 実装しない
- コード変更しない
- mainline 批判だけで終わらない
- prompt を盛るだけの案をアルゴリズムと呼ばない
- 「日本語専用巨大ルールベースを作るべき」と短絡しない
- article-type fixed routing table を正当化しない
- 現 package objective を research で上書きしない

最終報告で必ず示すこと:
1. 見た source の URL 一覧
2. source ごとの一言要約
3. adopt 候補アルゴリズム 3〜7 個
4. reject 候補 / 今は弱い候補
5. 他言語アルゴリズムを日本語化するときの改造ポイント
6. 日本語特性として重要だった観点
7. 現 codebase に narrow に試すなら最初の 1 owner はどこか
8. すぐ実装すべきでない理由がある候補
9. 「別アルゴリズムを考えるべきか」の暫定結論
10. AGENTS / WORKLOG 更新の要否

最終的に欲しい答え:
- world-wide な既存アルゴリズムの中で、
  notecode に持ち込む価値がある line はあるか
- あるなら、日本語向けに何を改造すべきか
- 最初の 1 research-to-implementation bridge は何か
```
