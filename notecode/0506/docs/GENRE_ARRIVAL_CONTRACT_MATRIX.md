# Genre Arrival Contract Matrix

Status: planning contract for Route V / article brief v2
Owner: `app/agents/article_brief_builder.py` and `app/services/article_brief_source_shape_v2.py`
Default runtime: Route B v1 remains unchanged unless `ROUTE_B_ARTICLE_BRIEF_ALGORITHM=v2`

## Purpose

Route V の自然さは、`company_service_intro` だけで決まらない。UI の記事タイプごとに、読者がどの温度感で来るか、source からどこまで膨らませてよいか、どこから unsupported claim になるかを整理する。

この document は実装前の contract matrix であり、prompt を長くするための文案集ではない。実装時は短い `genre_id x source_shape` table へ落とす。

## Shared Assumptions

- 読者は、記事タイプに関わらず、検索結果・サムネイル・リンクからなんとなく開いた低関心/探索中の読者を含む。
- 自己視点ブロガーは `私たち` / `当社` の自己発信を保つが、読者を「すでに強い興味がある人」に限定しない。
- 発信主体は会社だけではない。幼稚園、学校、行政、施設、店舗、団体、プロジェクトも含む。
- source-grounding, unsupported claim guard, third-party viewpoint ban, QA threshold は緩めない。
- raw full source documents pass では解決しない。
- 文章を増やす場合、事実を増やすのではなく、source にある要素から近い距離の場面描写・接続・推論を増やす。

## Source-Derived Expansion

Allowed expansion means proximity inference from source elements, not new facts.

Use source elements such as:

- place: 園庭、教室、体育館、窓口、倉庫、地域の会場
- time: 朝、放課後、季節、年度末、雨の日
- object/tool: 絵本、苗、タブレット、避難袋、掲示物、申請書
- action: 準備する、並ぶ、確かめる、片付ける、声をかける、記録する
- sequence: 集まる、説明を聞く、やってみる、振り返る
- constraint: 天気、時間、安全確認、持ち物、人数、期限
- role: 園、学校、行政、会社、施設として普段担う役割

Allowed:

- source にある名詞・動作・場所・順番から見える範囲の場面描写
- 発信主体の役割から近く読める必要性や意図
- 「この作業は地味だが必要」のような、source の作業内容に近い自己視点の受け
- source facts の間をつなぐ読み物としての文

Not allowed unless source explicitly says it:

- 第三者の心理や反応: 喜んでいた、安心した、驚いた
- 成果や効果: 理解が深まった、問い合わせが減った、成長につながった
- 強い因果: これにより必ず改善する
- 数字、実績、評価、比較優位
- 美談化、PR化、強い CTA

Avoid generic bridge phrases such as:

- `この活動は、ふだんの取り組みともつながっています`
- `大切にしています`
- `今後も取り組んでいきます`
- `ポイントは`
- `確認しましょう`

Replace them with source-near description. Example:

- source: `年長組が園庭でさつまいもの苗を植えました。`
- better: `土をならして、苗を置いて、上からそっと土をかぶせる。短い時間の中にも、順番を待つことや、友だちの手元を見ることが自然に入っていました。`

## Matrix

| genre_id | arrival contract | natural expansion | main risk |
|---|---|---|---|
| `company_service_intro` | 会社名・商品名を見かけて軽く開いた読者。すでに会社や商品に強い関心があるとは限らない。 | プロフィールやカタログから始めず、source にある暮らし・仕事・選定・運用・知見の接点から入る。人・文化・採用・裏側は source にある場合だけ扱う。 | 商品カタログ化、会社案内化、source にない社員の声・カルチャー・採用文脈・裏側の追加。 |
| `market_explanation` | テーマを軽く眺めに来た読者。専門的に知りたいとは限らない。 | source の論点を、読者が追える順番に並べ替える。資料要約ではなく、見る順番を作る。 | PDF/資料の第三者要約調、発信主体の混同。 |
| `announcement` | 必要情報だけを探す読者。長い読み物を求めていない可能性が高い。 | 日付、対象、変更点、注意点を短く整理する。背景は source にある範囲だけ。 | ブログ化しすぎ、余韻の追加、不要な自己語り。 |
| `case_study` | 事例に少し関心があるが、成果話を信じに来たとは限らない読者。 | source から読める範囲の推論は許可する。課題、対応、変化の順序を自然につなぐ。 | source にない成果、顧客感情、因果、成功断定。 |
| `comparison_guide` | 迷っているとは限らず、違いを軽く見たい読者。 | source にある違いを比較軸へ整理する。選び方の断定ではなく、見る観点を示す。 | `ポイント` 記事化、ランキング化、未根拠のおすすめ。 |
| `daily_activity` | なんとなく読みに来た読者。日記風でよい。 | source の場所、動作、道具、順番、制約から場面を近接推論で膨らませる。source が薄ければ短めでもよい。 | AI 的な一般橋渡し、感情/成果の盛り、1400字への水増し。 |

## Daily Activity Length Rule

`daily_activity` は会社紹介や価格表と同じ本文長 floor を前提にしない。source が薄い場合は、自然な日記記事として 800-1200 字程度でも合格候補にする。

ただし、source に十分な場面要素がある場合は、次で増やせる。

- activity setup: 何を準備したか
- observed sequence: source から読める順番
- source-near detail: 場所、道具、手順、制約
- quiet self-viewpoint: 私たち側の受け止め。ただし成果や感情を断定しない
- closing return: 強い CTA ではなく、その日の場面へ静かに戻す

## Case Study Inference Rule

`case_study` は source からの推論を許可する。ただし推論の強さを分ける。

- allowed: source にある課題/対応/結果の順番を読みやすくつなぐ
- allowed: source facts から自然に読める「確認が必要だった」「手順を揃えた」程度の近い推論
- not allowed: 数値成果、顧客満足、売上改善、心理、強い因果を source なしで断定する

## Implementation Notes

- First implementation slice should verify code/docs/logs before editing.
- Prefer one compact matrix helper or existing v2 maps over per-genre prompt bloat.
- Do not change Route B v1 default behavior.
- Do not loosen QA or source grounding to make diary/case-study expansion pass.
- Add tests that prove company intro changes do not leak into other genres, and non-company genre contracts do not overwrite `table_or_list` price behavior.
