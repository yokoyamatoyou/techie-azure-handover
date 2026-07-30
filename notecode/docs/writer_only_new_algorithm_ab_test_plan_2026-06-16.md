# Writer-only New Algorithm AB Test Plan 2026-06-16

対象: コトメイク writer-only 日本語ブログ生成アルゴリズム

決定: **現行 writer-only を本線として残し、新アルゴリズムは shadow / offline AB test から開始する。**

この計画は実装前計画です。本文生成コード、UI route、OpenAI送信、画像生成、Route 0506 / Route A / repair / quality pipeline は変更しない。

## 1. 目的

現行 writer-only の安全性を維持しながら、ブログとしての自然な膨らみと information gain を改善できるかを検証する。

特に次を分けて評価する。

- source fact に忠実か
- source に近すぎて要約・紹介文になっていないか
- editorial bridge により読者の状況、比喩、相談前チェックを安全に足せているか
- verified external context と source fact と editorial bridge が混ざっていないか
- prompt / module bloat を増やしていないか

## 2. 比較対象

### A: baseline writer-only

現行本線:

```text
note\writer_only_service.py
-> writer_only_source_bundle.py
-> writer_only_brief.py
-> writer_only_openai_adapter.py
-> writer_only_evaluator.py
```

保持するもの:

- strict URL policy / robots / redirect fail-closed
- full_text を LLM へ渡さない
- source_bundle の metadata / excerpt / claims
- single writer call
- smoke evaluator
- post-success image は fail-open
- Route 0506 / Route A / repair / quality pipeline 非使用

### B: new safe-expansion writer-only

現行 writer-only の派生として作る。新 route ではなく、AB用 owner 内の variant として扱う。

追加候補:

- `expansion_policy`
- A/B/C/D fact layer contract
- source claim surface の軽微な増加
- thin source でもブログとして成立する最低深度
- editorial bridge を許容し、D prohibited claim を厳しく見る evaluator

## 3. 新アルゴリズムの最小仕様

新アルゴリズムは次の4層を brief に入れる。

- A `source_fact`: sourceにある会社・商品・数値・実績・固有名詞。断定OK。
- B `verified_external_context`: 季節、地域、統計、制度、用語豆知識。出典URL付きで渡された場合のみ使用。
- C `editorial_bridge`: 読者の悩み、利用場面、判断軸、比喩、相談前チェック。断定せず「〜のような場面」「〜を考えるきっかけ」として書く。
- D `prohibited_claim`: 数値、価格、成果、法律/医療/金融助言、地域市場動向、顧客事例、比較優位。AまたはBなしでは禁止。

短い contract:

```text
source factsは断定してよい。読者の場面・たとえ・相談前チェックはeditorial bridgeとして足してよいが、事実断定ではなく「〜のような場面」「〜を考えるきっかけ」で書く。verified external contextは出典付きで渡された場合だけ使う。数値・価格・成果・法律/医療/金融助言・地域市場動向・事例・比較優位はsourceまたは出典付きcontextなしで書かない。
```

## 4. Owner 分割

### Owner 0: docs / fixtures readiness

目的:

- AB test の入力ケースを固定し、比較がぶれないようにする。

作業:

- この計画を正本候補として置く。
- `logs\writer_only_generation\writer_only_20260604_233416_91272e8c\` など、既存 writer-only artifact を fixture 候補にする。
- 不足している検証ケースは保存済み source_bundle / brief のみ作る。live API は呼ばない。

終了条件:

- 5ケース分の input fixture list がある。
- baseline artifact の有無が記録されている。

### Owner 1: new algorithm offline variant

目的:

- 本線に影響しない B variant を作る。

候補実装:

- `writer_only_brief.py` に `expansion_policy` を追加。
- `writer_only_source_bundle.py` は、まず `CLAIMS_LIMIT=12` / `EXCERPT_LIMIT=1200` までの小変更候補に留める。
- `writer_only_openai_adapter.py` は固定 instructions を増やさず、既存の「briefのwriter_contractを守る」で吸収する。必要なら1文だけ。
- `writer_only_evaluator.py` に `editorial_bridge_allowed` と `prohibited_claim_guard` を足す。

禁止:

- 新 repair loop
- raw full source pass
- Route 0506 / Route A / quality pipeline 復帰
- prompt table / persona table の肥大化

終了条件:

- no-API unit tests pass
- A variant と B variant を同一 fixture で生成/評価できる local harness がある
- B variant は通常UIから呼ばれない

### Owner 2: offline AB test

目的:

- 保存済み source / fixture で A と B を比較し、API回数を使わずにまず shape と evaluator を確認する。

検証ケース:

| case | 目的 | fixture 候補 |
|---|---|---|
| thin_company_url | 薄い会社URLで紹介文化しないか | 会社TOPのみ |
| rich_company_url | 情報量の多い会社URLで後半情報を拾えるか | 小泉グループ3URL |
| local_service_url | 地域性を勝手に市場動向化しないか | REJP / 東大阪系 |
| seasonal_theme | 季節入口をC層で安全に足せるか | source + user instruction |
| trivia_theme | 用語豆知識をBなしで断定しないか | source + user instruction |

評価軸:

- fact grounding
- blog naturalness
- information gain
- Japanese readability
- SEO usefulness
- risk
- prompt bloat
- module bloat

終了条件:

- 各ケースで A/B の差分レビューがある。
- B が A より良いケースと悪いケースが明記されている。
- B が unsupported claim を増やした場合は reject / revise。

### Owner 3: approved live AB 1-3 cases

目的:

- ユーザー承認後に限り、少数 live API で A/B を比較する。

ルール:

- 1 validation window 最大 3 source cases。
- A と B の入力 source を固定。
- 失敗時は同一ownerで自己修正3回まで。
- API回数、model、run_id、artifact_root を記録。
- live結果は通常UIの最新表示へ自動投影しない。

終了条件:

- B が A に対して、安全性を落とさず、ブログ自然さ / information gain のどちらかで明確に勝つ。
- route flags が維持される。

### Owner 4: UI shadow AB

目的:

- 通常ユーザー出力は A のまま、B を shadow artifact としてだけ保存する。

ルール:

- UI visible output は A のみ。
- B は `logs\writer_only_ab_shadow\<run_id>\variant_b\` に保存。
- B が失敗しても UI 上は A 成功を維持。
- B の結果をユーザーに出す場合は明示承認後。

終了条件:

- 10件程度の shadow run で B の risk が A 以下。
- B の blog naturalness / information gain が A を上回る傾向。
- prompt / module bloat が none または minor。

### Owner 5: promotion decision

目的:

- B を本線へ昇格するか、Aを継続してBをparkするか判断する。

判断:

- `promote_b_to_writer_only_main`
- `keep_a_and_continue_shadow`
- `revise_b_next_owner`
- `reject_b_and_archive`

昇格条件:

- source grounding regression なし
- prohibited claim 増加なし
- thin source で 700-1200字程度の自然な記事形が出る
- rich source で後半情報の落ちが減る
- evaluator false positive / false negative が減る
- fixed prompt が短いまま
- module増加が 1 owner で説明可能

## 5. Metrics

### 自動指標

- article_char_count
- section_count
- source_url_coverage
- source_claim_reflection_count
- prohibited_claim_hits
- unsupported_generalizations
- editorial_bridge_markers
- reader_relevance_pass
- visible_media_name_absent
- route flags

### 手動レビュー

5点尺度:

- fact grounding
- blog naturalness
- information gain
- Japanese readability
- SEO usefulness
- risk

判定メモ:

```text
case_id:
variant_a_summary:
variant_b_summary:
winner:
reason:
risk_notes:
safe_expansion_notes:
promotion_signal:
```

## 6. Artifact Layout

```text
logs\writer_only_new_algorithm_ab_20260616\
  README.md
  fixture_index.json
  case_01_thin_company_url\
    input\
      brief.json
      source_bundle.json
    variant_a\
      draft.md
      evaluation.json
      review.md
    variant_b\
      draft.md
      evaluation.json
      review.md
    decision.md
  summary.md
```

Shadow UI stage:

```text
logs\writer_only_ab_shadow\<run_id>\
  variant_a_visible\
  variant_b_shadow\
  comparison.json
```

## 7. Stop / Reject Rules

即停止:

- B が source外の数値、価格、成果、法律/医療/金融助言、地域市場動向、顧客事例、比較優位を断定した。
- B が source fact と verified external context を混ぜた。
- B 実装が Route 0506 / Route A / repair / quality pipeline に依存した。
- B の prompt が長文化し、固定 instructions が読みづらくなった。
- B のために raw full source pass が必要になった。

3回まで自己修正:

- evaluator false positive / false negative
- editorial bridge の書き方が弱い
- article length が target から小さく外れる
- headings が generic

3回で直らない場合:

- `reject_b_and_archive` または `revise_b_next_owner`

## 8. Non-goals

- 現行 writer-only の即置換
- Route 0506 復帰
- Route A fallback 復帰
- repair loop 復帰
- quality pipeline 復帰
- SEO suite / competitor crawler の新設
- long prompt / persona table の追加
- UIの通常ボタンを増やすこと

## 9. 最初の実装候補

最初の owner は `writer_only_new_algorithm_offline_ab_fixture_owner`。

最小変更案:

1. fixture index と offline harness を作る。
2. B variant は production path から呼ばない。
3. `writer_only_brief.py` の pure helper として `build_safe_expansion_policy(...)` を追加する。
4. evaluator に prohibited claim guard のテストだけ追加する。
5. `note\tests\test_writer_only_generation.py` に A/B contract test を追加する。

この owner では live API を呼ばない。

## 10. 最終判定フォーマット

```text
decision: promote_b_to_writer_only_main | keep_a_and_continue_shadow | revise_b_next_owner | reject_b_and_archive
artifact_root:
baseline_kept: true
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
api_send_count:
winning_cases:
losing_cases:
risk_findings:
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```
