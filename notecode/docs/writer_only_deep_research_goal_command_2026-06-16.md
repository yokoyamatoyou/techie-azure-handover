# Writer-only Deep Research Goal Command 2026-06-16

対象: コトメイク writer-only / 新 safe-expansion アルゴリズム / AB test 計画

この文書は、Codex のゴールコマンド相当で長時間自走するための実行指示です。現行 writer-only を残し、新アルゴリズム別ルート計画を深める。実装に進む前に、調査、計画、fixture、AB設計、stop rule を固める。

## 1. 判断

deep research は **先に軽量実施する**。

理由:

- note / はてなブログ / Zenn は、日本語ブログの「人間ぽさ」の方向性が少し違う。
- 体言止め、主語省略、AIぽい均質な文末、過剰な整い方は、短い prompt だけで直すと prompt bloat になりやすい。
- オーケストレーションは、すぐに新フレームワークを入れるより、既存 writer-only の owner / fixture / evaluator / artifact を切るほうが安全。

ただし、広すぎる外部調査は止める。公式/一次情報を優先し、調査結果は短い contract と evaluator 観点に圧縮する。

## 2. ゴールコマンド

以下を新しい長時間自走用の指示として使う。

```text
あなたは TECHIE / notecode / コトメイクの「writer-only 新アルゴリズム別ルート計画・ABテスト設計 owner」です。

目的:
現行 writer-only を本線として残したまま、新しい safe-expansion writer-only ルートを offline/shadow AB test できる状態まで計画・調査・fixture設計を深める。実装はユーザー承認後にする。Route 0506 / Route A / repair loop / quality pipeline は戻さない。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
6. C:\tetie\notecode\note\writer_only_service.py
7. C:\tetie\notecode\note\writer_only_brief.py
8. C:\tetie\notecode\note\writer_only_openai_adapter.py
9. C:\tetie\notecode\note\writer_only_evaluator.py
10. C:\tetie\notecode\note\writer_only_source_bundle.py
11. C:\tetie\notecode\logs\writer_only_generation\writer_only_20260604_233416_91272e8c\draft.md / brief.json / source_bundle.json / evaluation.json

外部調査:
WEB検索を使って、公式/一次情報を優先して確認する。少なくとも次を見る。
- note pro / 法人note / note pro活用事例
- はてなブログ / はてなCMS / はてなブログ上の企業メディア記事
- Zenn / Publication / Publication Pro / 法人向けメニュー
- 日本語AI文体の研究または一次資料。特に品詞bigram、助詞bigram、読点位置、機能語率、文末均質化、体言止め、主語省略
- オーケストレーション。OpenAI Agents SDK、LangGraph/LlamaIndex Workflows/Semantic Kernel等の公式docs。ただし導入前提にしない

調査観点:
1. 企業ブログとしての人間ぽさは、どの媒体で何が支えているか。
2. note系: 運営方針、自己紹介、独自性、共感、読み手との距離。
3. はてな系: 思いや考え、多様な価値観、具体的な体験、少し個人的な導入。
4. Zenn系: 著者性、知見共有、レビュー、統計、技術資産、読者が再利用できる構造。
5. 日本語文体: 体言止めは増やしすぎず、見出し/短い締めで局所使用。主語省略は自然さに効くが、fact attributionを曖昧にしない範囲で使う。
6. AIぽさ: 同じ文末、同じ段落長、過剰な「重要です」「必要です」、説明順の均質さ、抽象名詞過多、毎節の相談前導入の反復。
7. prompt bloatを避けるため、固定promptへ長文ルールを足さず、brief contract / evaluator / fixture reviewへ分散する。
8. 文章が短くなりすぎないため、thin sourceでも C editorial bridge で 700-1200字の自然な記事形を目指す。ただし do_not_pad は維持。
9. source fact / verified external context / editorial bridge / prohibited claim を混ぜない。
10. オーケストレーションは、まず external framework導入ではなく、owner分割、artifact layout、deterministic harness、manual review gateで設計する。

ゴール成果物:
1. C:\tetie\notecode\docs\writer_only_new_algorithm_deep_route_plan_YYYY-MM-DD.md
   - 外部調査サマリー
   - note / はてな / Zenn から得たブログらしさの示唆
   - 日本語文体 guard: 体言止め、主語省略、文末分散、抽象名詞、読点、段落長
   - 新 safe-expansion ルートの設計
   - AB test fixture plan
   - evaluator追加案
   - prompt bloat / module bloat guard
   - orchestration plan
   - 3回エラー停止ルール
2. C:\tetie\notecode\docs\writer_only_new_algorithm_goal_execution_prompt_YYYY-MM-DD.md
   - 次windowで実装に進む場合のcopy-paste prompt
   - live APIを呼ぶ場合の承認ゲート
3. 必要なら C:\tetie\notecode\WORKLOG.md へ計画作成のみ記録

実装禁止:
- ユーザー承認前に product code を変更しない
- live API を呼ばない
- Route 0506 を戻さない
- Route A fallback を戻さない
- repair loop / quality pipeline を戻さない
- raw full source pass をしない
- fixed prompt を長文化しない
- persona table を増やさない
- UIの通常生成ボタンを増やさない

自走ルール:
- 1 slice = 1 narrow hypothesis = 1 owner scope
- 各sliceで自己テストまたは読み戻し確認を行う
- エラー時は最大3回まで自己修正する
- 3回で直らない場合は停止し、block report を出す
- 外部情報が必要ならWEB検索してよい。公式/一次情報を優先し、最終報告にURLを残す
- 調査で得た知見は長いpromptではなく、短い contract / evaluator / fixture review / artifact schema へ圧縮する

slice plan:
Slice 0: 参照docと現行writer-only実装を読む。既存proposalとAB planを要約する。
Self-test: 読んだファイル、実施範囲、非実装境界をメモに残す。

Slice 1: note / はてな / Zenn の企業ブログ・法人発信の公式/公開情報を調査する。
Self-test: 各媒体から1-3個の「アルゴリズムに入れる示唆」へ圧縮する。

Slice 2: 日本語AI文体、人間ぽさ、体言止め、主語省略、文末分散、読点位置、機能語率を調査する。
Self-test: promptへ入れるもの、evaluatorへ入れるもの、manual reviewへ回すものを分ける。

Slice 3: オーケストレーションを調査する。OpenAI Agents SDK / LangGraph / LlamaIndex Workflows / Semantic Kernel等を見るが、導入判断は保留する。
Self-test: 現時点では external framework導入なしで足りるか判定する。

Slice 4: 新 safe-expansion ルート計画を深掘りする。
Self-test: A source fact / B verified external context / C editorial bridge / D prohibited claim が混ざっていないか確認する。

Slice 5: AB test fixture planを作る。
Self-test: thin_company_url / rich_company_url / local_service_url / seasonal_theme / trivia_theme の5ケースがあるか確認する。

Slice 6: evaluatorとmanual review gate案を作る。
Self-test: 文章が短くなりすぎない、AIぽさを過剰修正しない、source groundingを落とさない、の3点を確認する。

Slice 7: docsを作成しWORKLOG必要分を更新する。
Self-test: docs読み戻し、WORKLOG読み戻し、route flags確認。

停止条件:
- 3回連続で同じエラー
- 公式/一次情報が取れず推測が増えすぎる
- prompt bloatなしで実装できないと判断した場合
- source groundingを落とさず膨らませる設計が成立しない場合

最終報告:
- 参照ルールファイル
- 今回の実施範囲
- 外部調査で見た媒体/資料
- note / はてな / Zenn から得た示唆
- 日本語文体 guard
- オーケストレーション判断
- 新ルート計画の要点
- 次に実装するなら最小owner
- AGENTS/WORKLOG更新の要否
```

## 3. 調査メモ

### note pro

示唆:

- 法人オウンドメディアは、単なる商品説明ではなく「運営方針」「自己紹介」「独自性」「読み手の共感」を重視する。
- コトメイクでは、company intro の冒頭に「なぜこの会社が発信するのか」を C editorial bridge として短く入れる余地がある。
- ただし「note」という媒体名は writer-only 出力には出さない。現行の visible media name suppression を維持する。

### はてなブログ / はてなCMS

示唆:

- はてなブログのトップは「思いや考え」「多様な価値観」を前面に出している。
- 企業メディア記事も、スタッフ選定の見出しを見る限り、具体的な体験、比喩、ひっかかり、少し個人的な導入が読みやすさを作っている。
- コトメイクでは、source fact の前に「読者がその話題を自分ごと化する一文」を許す。ただし事実断定ではなく C editorial bridge として扱う。

### Zenn / Publication

示唆:

- Zenn は知見共有、著者性、レビュー、統計、技術資産の蓄積を重視する。
- 企業発信でも「誰がどんな知見を共有するか」「読者が再利用できる構造」が重要。
- コトメイクでは、B2B/技術寄り記事だけ、相談前チェックや再利用できる観点リストを記事後半へ入れる。ただし bullet多用でテンプレ化しない。

### 日本語AI文体

調査で確認した研究観点:

- ChatGPT生成文と人間文は、品詞bigram、助詞bigram、読点位置、機能語率などで差が出る。
- したがって「人間ぽさ」は、単にくだける、体言止めを増やす、主語を消す、ではなく、文末、助詞、読点、段落長、抽象語の分散で見る。

アルゴリズムへ入れる候補:

- evaluator / manual review:
  - 文末同型の連続
  - 「重要です」「必要です」「考えられます」の過多
  - 段落長の均一化
  - 抽象名詞の連続
  - 読点過多
  - 毎H2の開始が同じ構文
- promptではなく brief contract:
  - 体言止めは見出しまたは短い締めに限定し、本文で連発しない
  - 主語省略は editorial bridge では許可し、source fact では主語を明確にする
  - 文章を短くしすぎず、thin sourceでも 700-1200字の自然な記事形を狙う

## 4. オーケストレーション判断

外部framework導入は当面不要。

理由:

- OpenAI Agents SDK は guardrails / handoffs / sessions / tracing を持つが、現行 writer-only AB では production route を増やさず、offline harness と artifact gate で足りる。
- LlamaIndex Workflows は step/event で複雑な流れを保守しやすいが、今の段階では module bloat のほうがリスク。
- Zenn Publication の示唆も、強いのは「レビューと統計」であり、複雑なagent分岐ではない。

採用する orchestration:

```text
deterministic fixture index
-> variant A baseline generation/evaluation
-> variant B safe-expansion generation/evaluation
-> deterministic comparison metrics
-> manual review gate
-> decision.md
```

## 5. Goal実行時の成果判定

成功:

- 長時間自走用 goal command がそのまま使える。
- 別ルート計画が、現行 writer-only を壊さずAB testへ進める。
- 日本語の人間ぽさが、prompt bloatではなく evaluator / brief / manual review に整理されている。
- 文章が短くなりすぎない方針が入っている。
- 3回エラー停止、WEB検索、承認ゲートが明示されている。

失敗:

- promptに長い文体ルールを詰め込むしかない。
- source groundingを犠牲にしないと膨らませられない。
- Route 0506 / Route A / repair / quality pipeline 復帰が必要になる。

## 6. 参照URL

- note pro公式: `https://biz.note.com/`
- はてなブログ: `https://hatena.blog/`
- Zennとは: `https://zenn.dev/about`
- Zenn Publication: `https://zenn.dev/publications`
- Zenn法人向けメニュー: `https://zenn.dev/biz-lp`
- Japanese stylometric analysis paper: `https://arxiv.org/abs/2304.05534`
- OpenAI Agents SDK: `https://openai.github.io/openai-agents-python/`
- LlamaIndex Workflows: `https://developers.llamaindex.ai/python/llamaagents/workflows/`
- Microsoft Semantic Kernel Process Framework: `https://learn.microsoft.com/en-us/semantic-kernel/frameworks/process/process-framework`
