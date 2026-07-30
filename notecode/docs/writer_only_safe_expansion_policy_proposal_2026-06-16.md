# Writer-only Safe Expansion Policy Proposal 2026-06-16

対象: コトメイク writer-only 日本語ブログ生成アルゴリズム

決定案: **adjust**。writer-only の source 忠実性、strict URL policy、single writer call、Route 0506 / Route A / repair / quality pipeline 非復帰は維持する。ただし、現行は「source fact だけで記事化する」圧力が強く、薄い source やブログらしい導入で、要約・紹介文・相談前メモに寄りやすい。安全な膨らませ方を短い contract と brief enrichment に分けて追加する。

## 1. 調査サマリー

公式ページ優先で確認した示唆:

- Transcope: SEOライティング、競合分析、キーワード分析、検索順位調査、社内情報学習、URL/画像/音声入力を組み合わせる設計。ChatGPT単体は意図や重要キーワードを落とすため、競合分析と重要キーワードを使う思想。
- EmmaTools: キーワード調査、競合サイト分析、上位サイトのスコア/文字数/キーワード使用率/見出し構成、コンテンツスコアリング、景表法/薬機法/コピー率/ファクトチェック。
- Catchy: 100種類以上の用途別生成ツール。記事作成、広告、資料、セールスレターなど、用途ごとに生成面を分ける思想。
- SAKUBUN: SEO記事制作に強いAIライティングツールとして確認。ただし取得本文は限定的。
- ラクリン: キーワード提案、見出し作成、本文、リード、まとめ、URL調査、本文作成（リファレンス有）、長文リライトで2-3倍程度膨らませる機能。
- Jasper: brand voice、style guide、audience profiles、product knowledge、Knowledge Base を全出力へ適用するブランド文脈管理。
- Writesonic: AI visibility / citation gap / content fixes / FAQ blocks / comparison tables / self-contained passages など、AI検索で引用される構造と不足箇所を改善する思想。
- Surfer: keyword density、structure、readability、content gap、complementary topics、Content Editor でライターの判断を支援する設計。
- Copy.ai: Infobase と Brand Voice。会社情報の集中リポジトリとブランドらしさを生成に使う思想。
- Semrush Content Hub: AI Writer、Brand Voice、SEO Article Generator、コンテンツアイデア、生成、最適化を一体化する方向。
- Google Search Central: AI生成そのものではなく、品質・独自性・people-first・E-E-A-T・信頼性を重視。単なるコピー/書き換えではなく追加価値が必要。AIを検索順位操作目的に使うのはspam。YMYLでは信頼性を強く見る。

## 2. 現行評価

### fact grounding

強い点:

- `full_text` をLLMへ渡さず、`excerpt` と `claims` に絞る。
- robots / redirect / content-type / URL数を fail-closed にしている。
- route flags で Route 0506 / Route A / repair 非使用を明示している。

弱い点:

- `CLAIMS_LIMIT=8` は source fact の広がりを早い段階で切る。長い会社URLでは上部の営業文・導入文だけが claims 化され、後半のサービス範囲、注意点、FAQ、地域情報が落ちやすい。
- `EXCERPT_LIMIT=800` は長い単一sourceの読み替えには不足しやすい。
- evaluator の unsupported generalization は固定語リスト型で、狭い語には過敏だが、実際の出力に混ざる「市場状況」「近隣需要」「行政代執行」などは見逃し得る。

### blog naturalness

現行は会社側一人称、相談前整理、H2 reader relevance を持つため、最低限のブログ形は作れる。ただし、薄い source では `min_chars=300` となり、読者の場面、比喩、相談前チェック、季節性、地域文脈を足す設計がない。ブログというより「sourceの要点紹介 + 相談促し」になりやすい。

### information gain

競合ツールは keyword intent、competitor gap、content score、brand voice、citation/AI visibility、FAQ/table/schema などで追加価値を作る。現行 writer-only は source外一般論を抑える設計のため、嘘は減るが、追加価値の正式な置き場がない。

### Japanese readability

日本語としては読みやすいが、evaluator が「各H2は読者の迷いから始める」を強めるため、節の入りが似る。導入の比喩、季節の入口、読者の生活場面などの C 層 editorial bridge を許すと自然さが上がる。

### SEO usefulness

現行はSEO tool的な keyword intent / gap / content score を持たない。Google方針上、SEOをやること自体は問題ではないが、people-first で sourceを焼き直さず追加価値を出す必要がある。軽量導入なら「検索意図メモ」「読者が再検索しがちな疑問」「不足見出し1つ」までで十分。

### risk

source fact と一般論の境界が2層しかないため、B verified external context と C editorial bridge が混ざる。法律/医療/金融/統計/価格/成果/比較優位は D prohibited claim として明示分離すべき。

## 3. Safe Expansion Policy 案

事実を4層に分ける。

- A source fact: sourceにある会社・商品・数値・実績・固有名詞。断定OK。本文に出せる。
- B verified external context: 季節行事、地域情報、統計、制度、用語豆知識。使うなら公式/信頼ソースで確認し、`external_context_bank` に出典URL、取得日、短いfactを保存。未検証なら使わない。
- C editorial bridge: 読者の悩み、利用場面、判断軸、たとえ話、相談前チェック。断定ではなく「〜のような場面」「〜を考えるきっかけ」「相談前に整理しやすい観点」として書く。出典不要だが fact に見せない。
- D prohibited claim: 数値、価格、成果、法律/医療/金融助言、地域市場動向、顧客事例、比較優位、行政手続きの断定。AまたはBなしでは禁止。

短い writer contract 案:

```text
Use source facts as facts. You may add editorial bridges for reader situations, analogies, and pre-consultation checks, but write them as possibilities or prompts, not facts. Use verified external context only when provided with source_url. Do not invent numbers, outcomes, laws, prices, market trends, cases, or superiority claims.
```

日本語化して `writer_contract.safe_expansion` に入れる場合:

```text
source factsは断定してよい。読者の場面・たとえ・相談前チェックはeditorial bridgeとして足してよいが、事実断定ではなく「〜のような場面」「〜を考えるきっかけ」で書く。verified external contextは出典付きで渡された場合だけ使う。数値・価格・成果・法律/医療/金融助言・地域市場動向・事例・比較優位はsourceまたは出典付きcontextなしで書かない。
```

## 4. 最小 owner 候補

推奨 owner: `writer_only_safe_expansion_contract_brief_owner`

実装範囲:

- `writer_only_brief.py` に `expansion_policy` を追加。
- source metrics に応じて `article_body_contract.min_chars` を 300/900/1300 から、薄いsourceでも 700 を標準候補に再検討。ただし `do_not_pad` は維持。
- `writer_only_source_bundle.py` の `claims` を「先頭8文」から、既存のままでもよいので `claim_topics` を軽量分類するか、claimsを最大12-16へ引き上げる。まずは `CLAIMS_LIMIT=12` と `EXCERPT_LIMIT=1200` の小変更候補。
- `writer_only_evaluator.py` は fixed NG語ではなく、出力内の expansion marker を見て B/D だけ厳しくする。C editorial bridge は落とさない。
- OpenAI固定instructionsは増やさず、`brief.writer_contract.safe_expansion` を守る1文だけ維持する。

非推奨:

- 新しい repair loop。
- Route 0506 / Route A / quality pipeline 復帰。
- 長大な persona table。
- 競合分析クローラやフルSEOスコアリングの追加。
- raw full source documents pass。

## 5. 検証ケースと期待 shape

| ケース | baseline 現行に出やすい形 | safe expansion 期待形 |
|---|---|---|
| 薄い会社URL 1本 | 会社概要の言い換え、短い紹介文、CTA中心 | A: 会社情報。C: 読者が相談前に迷う場面、確認チェック、問い合わせ前の整理。断定的な実績・比較優位は書かない |
| 情報量の多い会社URL 1本 | excerpt冒頭に偏った要約。後半情報を落とす | A: source内の事業範囲/特徴/注意点を複数claimから拾う。C: 見出しを読者状況に並べ替える |
| 地域性のあるサービスURL | 地域名だけを入れた一般紹介、または地域市場動向の推測 | A: sourceの地域名・対応範囲。B: 地域統計や制度を使うなら公式確認済みだけ。C: 地元で相談しやすい確認観点 |
| 季節性を足したくなるテーマ | 季節一般論を断定するか、まったく触れない | B: 公式/信頼ソースの季節行事・制度日程がある時だけ事実化。C: 「年度替わりに見直したくなる」程度の入口は可 |
| 豆知識を足したくなるテーマ | 用語説明をsourceなしで断定、またはsource要約だけ | B: 用語定義が公的/信頼ソースにある時だけ説明。C: 「言葉を知ると相談時に整理しやすい」という橋渡し |

## 6. 実装しない境界

- Route 0506 を default route に戻さない。
- Route A fallback を戻さない。
- repair loop / quality pipeline を writer-only 本文生成へ戻さない。
- raw full `source_documents` pass で解決しない。
- prompt bloat / module bloat を増やさない。

## 7. 判定

`keep` では弱い。`replace` は過剰。現行 writer-only は主経路として維持し、**adjust** で safe expansion policy、source/verified/editorial/prohibited の分離、薄いsource時の最低ブログ深度、claims/excerptの微増、evaluatorのC許容/B-D厳格化を入れるのが妥当。

実装前の次アクション:

1. この proposal を承認するか確認。
2. 承認後、1 owner で `writer_only_brief.py` と `writer_only_evaluator.py` 中心に最小変更。
3. テストは `note\tests\test_writer_only_generation.py` に safe expansion の fixture を追加。
