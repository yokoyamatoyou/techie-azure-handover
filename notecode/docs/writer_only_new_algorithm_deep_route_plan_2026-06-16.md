# Writer-only New Algorithm Deep Route Plan 2026-06-16

対象: コトメイク writer-only / safe-expansion writer-only / offline AB test

決定: **plan_ready_needs_user_approval_before_code**。現行 writer-only を本線に残し、safe-expansion は production route ではなく offline/shadow AB の B variant として設計する。product code、通常UI、OpenAI live API、Route 0506、Route A、repair loop、quality pipeline は変更しない。

## 1. 実施範囲

読んだ正本・実装・artifact:

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md`
- `C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md`
- `C:\tetie\notecode\note\writer_only_service.py`
- `C:\tetie\notecode\note\writer_only_brief.py`
- `C:\tetie\notecode\note\writer_only_openai_adapter.py`
- `C:\tetie\notecode\note\writer_only_evaluator.py`
- `C:\tetie\notecode\note\writer_only_source_bundle.py`
- `C:\tetie\notecode\logs\writer_only_generation\writer_only_20260604_233416_91272e8c\draft.md`
- `C:\tetie\notecode\logs\writer_only_generation\writer_only_20260604_233416_91272e8c\brief.json`
- `C:\tetie\notecode\logs\writer_only_generation\writer_only_20260604_233416_91272e8c\source_bundle.json`
- `C:\tetie\notecode\logs\writer_only_generation\writer_only_20260604_233416_91272e8c\evaluation.json`

非実装境界:

- product code を変更しない。
- live API を呼ばない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- fixed prompt や persona table を増やさない。
- 通常UIの生成ボタンを増やさない。

## 2. 外部調査サマリー

公式/一次情報を優先して確認した。調査で得た知見は prompt に長く足さず、brief contract / evaluator / fixture review / artifact schema に圧縮する。

### note pro / 法人note

参照:

- https://biz.note.com/

示唆:

- 法人オウンドメディアでは、運用ヒント、活用事例、自己紹介、運営方針、独自性、読み手の共感が重要な手がかりになる。
- コトメイクでは、company intro の冒頭に「なぜ私たちがこのテーマを発信するのか」を C editorial bridge として短く置く余地がある。
- ただし media name suppression は維持する。出力本文へ `note` / `企業note` / `はてなブログ` / `Zenn` の媒体名を出さない。

### はてなブログ / はてな系

参照:

- https://hatena.blog/

示唆:

- はてなブログは「思いや考え」「多様な価値観」を前面に出している。
- 編集部選出記事には、具体的な体験、少し個人的な導入、ひっかかり、比喩、生活場面が多い。
- コトメイクでは、source fact の前に「読者がその話題を自分ごと化する一文」を許す。ただし事実断定ではなく C editorial bridge として扱う。

### Zenn / Publication / 法人向け

参照:

- https://zenn.dev/about
- https://zenn.dev/publications
- https://zenn.dev/biz-lp

示唆:

- Zenn は知見共有、著者性、技術的な再利用性、レビュー、統計、Publication のプロフィール/固定メッセージを重視する。
- Publication Pro は記事レビュー、統計ダッシュボード、GitHub リポジトリ連携など、発信品質と運用の見える化を支える。
- コトメイクでは、B2B/技術寄り記事のみ「読者が再利用できる観点」を後半に入れる。ただし箇条書きテンプレを濫用せず、本文の流れに入れる。

### 日本語AI文体 / stylometry

参照:

- https://arxiv.org/abs/2304.05534

確認した観点:

- ChatGPT生成文と人間文は、品詞 bigram、助詞 bigram、読点位置、機能語率などで分布差が出る。
- 「人間ぽさ」は、くだける、体言止めを増やす、主語を消す、だけでは不十分。

アルゴリズムへの圧縮:

- prompt へ入れる: 短い safe-expansion contract だけ。
- evaluator へ入れる: 文末同型、段落長均一化、抽象名詞連続、読点過多、毎H2の同型開始、AI定型句の連続。
- manual review へ回す: 語り手の熱量、比喩の自然さ、読者との距離、体言止めの効き方。

### SEO / AI生成コンテンツ

参照:

- https://developers.google.com/search/blog/2023/02/google-search-and-ai-content

示唆:

- AI生成そのものではなく、品質、独自性、people-first、E-E-A-T、信頼性を重視する。
- 検索順位操作を主目的にした自動生成は避ける。
- コトメイクでは「SEOっぽい水増し」ではなく、source-backed な独自性と C editorial bridge による読者支援を information gain として扱う。

### オーケストレーション

参照:

- https://openai.github.io/openai-agents-python/
- https://docs.langchain.com/oss/python/langgraph/overview
- https://developers.llamaindex.ai/python/llamaagents/workflows/
- https://learn.microsoft.com/en-us/semantic-kernel/frameworks/process/process-framework

判断:

- OpenAI Agents SDK は agent / handoff / guardrail / tracing を持つが、今回の AB 設計は production agentic app ではない。
- LangGraph は durable execution / persistence / human-in-the-loop などが強いが、今の課題は長期状態管理ではなく、短い writer-only variant の比較である。
- LlamaIndex Workflows と Semantic Kernel Process Framework は step/event 型の複雑な flow を扱えるが、導入すると module bloat になりやすい。
- 現時点では external framework 導入なし。既存 Python の deterministic harness、artifact layout、manual review gate で足りる。

採用する orchestration:

```text
deterministic fixture index
-> variant A baseline brief/build/evaluation
-> variant B safe-expansion brief/build/evaluation
-> deterministic comparison metrics
-> manual review gate
-> decision.md
```

## 3. 現行 writer-only 観察

現行経路:

```text
writer_only_service.py
-> writer_only_source_bundle.py
-> writer_only_brief.py
-> writer_only_openai_adapter.py
-> writer_only_evaluator.py
```

保持する強み:

- strict URL policy / robots / redirect fail-closed。
- LLM へ `full_text` を渡さず、metadata / excerpt / claims に絞る。
- single writer call。
- route flags で Route 0506 / Route A / repair / quality pipeline 非使用を明示する。
- SNS fallback と image fail-open は本文本線から分離されている。

確認した gap:

- `writer_only_20260604_233416_91272e8c` は source grounding と URL coverage は通ったが、`article_body_length` と `section_reader_relevance` が落ちた。
- これは source不足ではなく、読者接続と自然な膨らみの置き場が不足している兆候。
- 6/4 artifact には古い `企業note` 表現が残る。現行 code では visible media name suppression が入っているため、新 fixture では古い artifact をそのまま期待値にしない。

## 4. Safe-expansion v2 設計

既存 proposal の A/B/C/D fact layer を維持し、B variant の brief contract にだけ短く入れる。

### Fact layer

- A `source_fact`: sourceにある会社・商品・数値・実績・固有名詞。断定OK。
- B `verified_external_context`: 季節、地域、統計、制度、用語豆知識。出典URLと取得日付きで渡された場合のみ使用。
- C `editorial_bridge`: 読者の悩み、利用場面、判断軸、比喩、相談前チェック。断定せず「〜のような場面」「〜を考えるきっかけ」として書く。
- D `prohibited_claim`: 数値、価格、成果、法律/医療/金融助言、地域市場動向、顧客事例、比較優位。AまたはBなしでは禁止。

### Brief contract

長い prompt にはしない。`writer_contract.safe_expansion` に次の短文を置く。

```text
source factsは断定してよい。読者の場面・たとえ・相談前チェックはeditorial bridgeとして足してよいが、事実断定ではなく「〜のような場面」「〜を考えるきっかけ」で書く。verified external contextは出典付きで渡された場合だけ使う。数値・価格・成果・法律/医療/金融助言・地域市場動向・事例・比較優位はsourceまたは出典付きcontextなしで書かない。
```

### Thin source length guard

現行の 300 / 900 / 1300 dynamic minimum は維持候補。ただし B variant は thin source でも次のどちらかを artifact に明示する。

- `target_min_chars=700`、ただし `do_not_pad=true`
- または `thin_source_editorial_bridge_count=2` を要求し、文字数でなく bridge の質を manual review へ渡す

最初の owner では code変更前の fixture設計なので、どちらを採用するかは decision.md で比較する。

## 5. AB test fixture plan

最低5ケースを固定する。

| case_id | 目的 | 必須入力 | 期待する B variant |
|---|---|---|---|
| thin_company_url | 薄い会社URLで紹介文化しないか | 会社TOP 1 URL / claims 少 | A fact を超えず、C bridge で読者場面と相談前チェックを足す |
| rich_company_url | 情報量が多い会社URLで後半情報を拾うか | 3 URL 以上 / claims 多 | 冒頭要約だけでなく、source内の事業範囲・姿勢・注意点を反映 |
| local_service_url | 地域性を市場動向へ勝手に膨らませないか | 地域名あり / 統計なし | 地域名はAだけ。市場動向はBがなければ禁止。Cは相談場面まで |
| seasonal_theme | 季節入口を安全に足せるか | source + user instruction | 季節の事実はBのみ。Cは「見直したくなる時期」程度 |
| trivia_theme | 用語豆知識をBなしで断定しないか | source + user instruction | 用語定義はBなしでは断定しない。Cは「知っておくと整理しやすい」 |

既存 artifact fixture:

- `writer_only_20260604_233416_91272e8c` は `rich_company_url` の seed として使える。
- ただし古い visible media name と古い evaluation schema 差分を artifact note に残す。

Fixture index 例:

```json
{
  "case_id": "rich_company_url",
  "source_bundle_path": "logs/writer_only_generation/writer_only_20260604_233416_91272e8c/source_bundle.json",
  "brief_path": "logs/writer_only_generation/writer_only_20260604_233416_91272e8c/brief.json",
  "baseline_draft_path": "logs/writer_only_generation/writer_only_20260604_233416_91272e8c/draft.md",
  "known_baseline_failures": ["article_body_length", "section_reader_relevance"],
  "artifact_notes": ["stale_media_name_phrase_in_old_draft"]
}
```

## 6. Evaluator / manual review gate

### 自動 evaluator 追加候補

- `prohibited_claim_hits`: source/Bなしの数値、価格、成果、法律/医療/金融助言、地域市場動向、事例、比較優位。
- `editorial_bridge_markers`: 可能性・場面・相談前チェックとして書けているか。
- `same_sentence_ending_run`: 同じ文末の連続。
- `uniform_paragraph_length`: 段落長が極端に均一か。
- `abstract_noun_run`: 抽象名詞が続くか。
- `h2_opening_pattern_repetition`: 各H2冒頭が同じ構文か。
- `comma_density_warning`: 読点過多の warning。

### Manual review 5点尺度

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
stylometry_notes:
promotion_signal:
```

## 7. Artifact layout

```text
logs\writer_only_new_algorithm_ab_20260616\
  README.md
  fixture_index.json
  source_research_summary.md
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

## 8. Prompt / module bloat guard

- fixed `WRITER_INSTRUCTIONS` は原則変更しない。
- 追加する場合も「brief の `writer_contract.safe_expansion` を守る」程度の1文まで。
- long style rule は prompt ではなく evaluator / manual review / fixtureに置く。
- helperを増やす場合は pure helper 1 owner に限定する。
- persona table は増やさない。
- external orchestration framework は導入しない。

## 9. Stop rule

即停止:

- B が source外の数値、価格、成果、法律/医療/金融助言、地域市場動向、顧客事例、比較優位を断定した。
- B が source fact と verified external context を混ぜた。
- B 実装が Route 0506 / Route A / repair / quality pipeline に依存した。
- B の fixed prompt が長文化した。
- B のために raw full source pass が必要になった。

3回まで自己修正:

- evaluator false positive / false negative
- editorial bridge の弱さ
- target length からの小さな外れ
- heading genericity

3回で直らない場合:

- `reject_b_and_archive` または `revise_b_next_owner`

## 10. 次に実装するなら最小 owner

推奨 owner:

```text
writer_only_new_algorithm_offline_ab_fixture_owner
```

最小範囲:

1. `logs\writer_only_new_algorithm_ab_20260616\fixture_index.json` を作る。
2. 既存 artifact から `rich_company_url` seed を登録する。
3. `writer_only_brief.py` に入れる前の pure schema draft として `safe_expansion_policy` を artifact に置く。
4. evaluator 追加候補は product code ではなく `review.md` checklist として先に使う。
5. live API は呼ばない。

完了判定:

```text
decision: needs_user_approval_before_code
baseline_kept: true
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
prompt_bloat: none
module_bloat: none
api_send_count: 0
next_one_owner: writer_only_new_algorithm_offline_ab_fixture_owner
```

## 11. Slice self-test

- Slice 0: 参照doc、現行 code、既存 artifact を読んだ。非実装境界を本書 1章へ記録した。
- Slice 1: note / はてな / Zenn の示唆を媒体別に 1-3 個へ圧縮した。
- Slice 2: 日本語AI文体は prompt / evaluator / manual review に分けた。
- Slice 3: orchestration は external framework 導入なしで足りると判定した。
- Slice 4: A/B/C/D fact layer を維持し、混在防止を設計へ残した。
- Slice 5: 5ケース fixture plan を作った。
- Slice 6: evaluator と manual review gate を分けた。
- Slice 7: docs / WORKLOG 更新対象を確定した。
