# コトミガキ現行ヒューリスティック監査 2026-07-10

## 1. 結論

コトミガキは、取得系の主経路にある SSRF 防御、分析件数・本文量の上限、保存結果の日本語要約、CSV/Markdown/DOCX 出力、固定脆弱性 DB 参照など、ローカル単独利用を安全に成立させる土台を持つ。一方で、現行の数値や判定には「測定済み」と「推定」、「不合格」と「未確認」、「公開画面」と内部用画面の境界が混ざる箇所があり、意思決定用プロダクトとしては真偽契約を先に揃える必要がある。

今回の最優先問題は次のとおり。

- provider bot 判定が robots 取得失敗時にも合格表示になり得る。
- 業界補正後の点数が 100 を超え、SEO/AIO の重点配分が不足側と逆になる。
- SEO スコアが 7 個の単純加点で、noindex、壊れた canonical、リンク到達性、国際 SEO、メディア等の重要所見と分離している。
- Schema.org の `@graph` / 入れ子を正しく読めない検証器があり、同じ入力に複数の判定ロジックが存在する。
- 保存 UI、CSV、Markdown で「優先アクション」の母集団と並び順が一致しない。
- 保存結果を開く GET が旧 snapshot を再構築して DB を更新し、競合情報を消す可能性がある。
- 未確認値を「参考」へ変換する表示があり、確認できていないことが伝わらない。
- コトミガキ自身のキーボード操作、状態通知、入力エラー関連付けが不足し、内蔵ブラウザ検査も現環境では無効だった。
- 外部公開を想定した認証・tenant 境界はコード上に存在せず、入力 URL の query に含まれる秘密値が保存・出力され得る。

P0 の確定所見はない。外部公開版へ現状の保存ルートをそのまま持ち出す場合は tenant 越境が成立し得るため、公開前の P1 リリースブロッカーとして扱う。

## 2. 参照ルールと監査境界

参照した current source of truth:

- `../../../AGENTS.md`
- `../../AGENTS.md`
- `../../ALGORITHM.md`
- `../../WORKLOG.md`（履歴として参照）
- `../CURRENT_AND_NEXT_IMPROVEMENTS.md`
- `../seo_llmo_coverage_2026-04-06/{README,TASK,PROGRESS}.md`
- `../tab_ia_rework_2026-04-04/{README,TASK,PROGRESS}.md`
- `EXECUTION_PROMPT_GPT56SOL.md`

今回の current owner は、このフォルダに新しい監査レポート 7 点を作成することだけである。コード、設定、データ、現行仕様、`AGENTS.md`、`ALGORITHM.md`、`WORKLOG.md` の変更、外部 API 実行、修正実装は non-owner とした。

## 3. 監査対象と方法

対象は 2026-07-10 13:15 JST から読み取ったローカル working snapshot。チェックアウトは Git repository として認識されなかったため、commit hash は付与できない。

実施した確認:

- current docs と planning package の owner / completed / not-started の整合確認
- NiceGUI 入口、保存結果、分析 orchestration、SEO/AIO/Schema/法務/サイトヘルス/固定脆弱性 DB、出力層の静的追跡
- 外部通信を伴わない fixture / unit / integration 回帰テスト
- Python owner module の `py_compile`
- `pip check` によるインストール済み依存の整合確認
- 公式 Google Search、OpenAI、Perplexity、Anthropic、W3C、OWASP 文書との照合
- Nielsen 10 原則、役割別可読性、SEO/LLMO、WCAG 2.2 AA、セキュリティのマトリクス化

## 4. 検証結果

| 検証 | 結果 | 注記 |
|---|---:|---|
| 横断 targeted pytest | `192 passed in 52.74s` | 30 test modules。外部 API なし |
| UI / 保存結果 targeted pytest | `77 passed in 8.46s` | UI helper、export、characterization を含む |
| SEO / LLMO targeted pytest | `23 passed in 25.36s` | bot、SEO、Schema、ページ体験等 |
| Security / accessibility targeted pytest | `72 passed in 6.11s` | safe fetch、scanner、export 等 |
| owner modules `py_compile` | pass | syntax/import-time compile のみ |
| `pip check` | `No broken requirements found.` | advisory/CVE scan ではない |

各 pytest 集合には重複があるため、通過数を合算して一意の test 数とは扱わない。

## 5. 実 UI 監査の制約

指定された in-app Browser の runtime 初期化を 3 回試したが、いずれも timeout で kernel が reset された。同一箇所で 3 回失敗した停止条件に従い、それ以上の接続や別ブラウザへの切替は行っていない。このため、今回の次の項目は **未確認** であり、合格とはみなさない。

- 現行画面の current-run screenshot
- 実 viewport での配置、切れ、余白、コントラスト
- キーボードのみの完走、フォーカス順、screen reader、200% / 400% zoom
- UI 自身への axe WCAG 2.2 AA
- 実ルート、保存結果、export download、console / page error

コードとテストから確認できた UX 所見は `NIELSEN_MATRIX.md` と `ROLE_READABILITY_MATRIX.md` に分離し、視覚確認済みとは記載していない。また、配布環境の `tools/accessibility_scanner/node_modules` がなく、`browser_accessibility_enabled()` は `False` だった。

## 6. レポート構成

- `FINDINGS.md`: 重大度、再現方法、影響、owner、受入条件
- `NIELSEN_MATRIX.md`: Nielsen 10 原則による current UI のコード・テスト監査
- `ROLE_READABILITY_MATRIX.md`: 経営、マーケ、実装、法務/セキュリティ、運用の読み分け
- `SEO_LLMO_A11Y_SECURITY_MATRIX.md`: 公式仕様との照合と未確認項目
- `REMEDIATION_BACKLOG.md`: 依存順、変更面、検証、non-owner を含む修正候補
- `EVIDENCE_INDEX.md`: 参照箇所、コマンド結果、公式 URL、制約

## 7. 「高度だがユーザーにはシンプル」の総合判定

総合判定は **partial / 現状のままでは意思決定面を合格にできない**。検査範囲、安全な取得、出力形式は広く、技術基盤は相応に高度である。一方、その高度さを一つの evidence state と canonical action model へ収束できていないため、初回利用者には単純な点数・合格・参考として過度に簡略化される。

| 初回利用者の質問 | 判定 | 理由 |
|---|---|---|
| 1. 何を調べた結果か | partial | 分析カテゴリは見えるが、実測/HTML推定/browser未実施、取得範囲、時刻が同じ粒度で並ばない |
| 2. いま最も重要な問題は何か | fail | scoreが100超、priority actionsがsurface別、unknownの丸めにより順位の真偽が安定しない |
| 3. まず何をすればよいか | fail | UIは一部actionしか見せず、CSV/Markdownと順番・母集団が違う |
| 4. その判断の根拠は何か | partial | engineer detailは存在するが、provider/Schema/CWV/LLM文章の一部で根拠から公開判定まで追跡できない |
| 5. 技術担当者に何を渡せば直せるか | partial | Markdown/DOCXと実装詳細はあるが、canonical action id、同一priority、再現/acceptanceが全surfaceで固定されない |

情報を増やす前に、primary 面を「今回の結論」「止める事項」「まず3件」「未確認」に絞り、根拠・全件・raw は段階的に開く。削減対象は内部ヒューリスティック語、根拠のない効果数値、実測に見えるproxy、重複action。保持対象はrun時刻、evidence state、owner、acceptance、engineer traceである。

## 8. 単一の次実装 owner

**完了owner: `saved-workspace truth and action parity owner`**

`analysis_run_service.py` と `saved_workspace.py` を中心に、保存結果を開くGETの無書込化、`unknown/unverified`の保持、canonical actionのstable ID・順位・audience・evidence・status、UI/CSV/Markdown/DOCXの同一契約を実装し、対象テスト204件を通過させた。

**次実装 owner: `provider-readiness evidence owner`**

robots.txtの取得失敗・対象URL path・User-Agent優先順位・X-Robots-Tagを、`pass / fail / unverified / not_applicable`の共通evidence contractとして表示・scoreへ接続する。R-01の保存/出力契約、UI刷新、Schema、LLM、認証/tenantは混ぜない。

non-owner は、SEO/AIO scoring、crawler/provider 判定、Schema validator、LLM prompt、認証/tenant 化、内蔵 accessibility scanner、法務判定である。これらは同じ実装 slice に混ぜない。
