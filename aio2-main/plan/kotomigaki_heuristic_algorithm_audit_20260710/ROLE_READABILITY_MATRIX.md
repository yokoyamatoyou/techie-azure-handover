# 役割別可読性マトリクス

## 1. 判定の考え方

同じ分析結果でも、経営判断、マーケティング編集、開発実装、法務/セキュリティ確認、運用監視では必要な粒度が異なる。現行画面と export が、結論、根拠、次行動、技術詳細をどこまで分離しているかをコードから確認した。

| 利用者 | 最初に必要な情報 | 現行で使える面 | current evidence | gap / 誤読リスク | 目標形 | 判定 |
|---|---|---|---|---|---|---|
| 経営・事業責任者 | 重大リスク、期待効果の確度、優先 3 件、投資判断 | 保存結果の評価・やること、Word | `saved_workspace.py:1083-1101` の primary summary、`:371-405` の action 抽出 | 100 超点数、根拠未検証の効果表現、UI/export の action 差、Word に raw 技術情報 | 1 page executive summary。実測/推定/未確認、効果の出典、owner/期限/依存を明示 | fail |
| マーケ・編集者 | どの文章をなぜ直すか、コピー可能案、事実確認箇所 | `文章改善`、引用候補、simulation | `saved_workspace.py:2613-2643`、`citation_generator.py:91-151` | 改善文の source entailment がなく、FAQ/speakable/AI 引用効果を強く言い過ぎる | 各案に source span、fact-check badge、適用条件、公開前 checklist | fail |
| SEO/AIO 担当 | crawl/index/robots/schema/content/link の証拠と優先度 | SEO/AIO tab、技術 summary | `orchestrator.py:3038-3525`、`aio_analyzer.py` | provider false-pass、simple score、Schema parser 競合、CWV proxy、future freshness | evidence ledger から score と action を導出。unverified を独立し、公式基準日を表示 | fail |
| Web 開発者 | ファイル/設定、再現条件、コード例、受入テスト | `実装・設定`、`エンジニア向け`、Markdown/DOCX | `saved_workspace.py:2001-2076` に engineer details | primary 実装面にも内部ヒューリスティックが漏れる。export 間の action 差。Schema 誤検出で不要実装の恐れ | issue-ready task: evidence id、対象 URL、変更面、copyable code、test、rollback | partial |
| 法務担当 | 法域、判断理由、要確認原文、免責、最終人手判断 | legal result と task | `analysis_run_service.py:906-926,1520-1557` | task 組立時に再追加され順位が surface で変わる。法務を自動確定と誤読させない contract が必要 | legal finding は `applicable/not-applicable/unverified/review-required`、法域と evidence を必須化 | partial |
| セキュリティ担当 | threat、到達可能性、secret、tenant、CVE source/date | site health、固定 vuln、engineer export | safe fetch、vulnerability intelligence、technical detail | localhost 前提と Azure 前提の境界が UI にない。URL secret 保存、browser scanner rebind 残余、advisory scan 未実施 | deployment profile、tenant/auth status、redacted evidence、DB/source version、unverified scan を表示 | fail |
| 運用・CS | run 成否、再試行可否、取得時刻、問い合わせに必要な run id | dashboard/history/saved run | `nicegui_app.py:990-1225`, `dashboard.py:281-356` | timeout を broken と断定、GET が旧 snapshot を更新、履歴 keyboard 不可、内部 result path export | immutable run、human-readable error code、retry guidance、artifact id、keyboard 対応 | fail |
| アクセシビリティ担当 | 適用基準、検査 source、違反、手動確認、再現 | site health accessibility | browser scanner + HTML fallback | browser scanner 無効でも同種 score に見え、WCAG 2.2 AA ではない。UI 自身の axe evidence なし | `browser/html/manual` source、基準 version、未確認 SC、axe evidence、manual checklist | fail |

## 2. Surface 別の対象者契約

| 層 | 表示するもの | 根拠への接続 | 隠す/段階開示するもの | 共通契約 |
|---|---|---|---|---|
| 非エンジニア | 結論、止める事項、上位3 action、効果の確度、未確認 | 各actionから短い理由と確認日時へ1段で到達 | raw signal、provider内部値、CVE matcher、path、prompt | action id、priority、state、件数はengineer/exportと同じ |
| エンジニア | URL、status、該当箇所、入力条件、version、変更面、acceptance | raw/normalized evidenceまで追跡 | 経営向け効果の断定 | 同じaction idから技術詳細へ展開 |
| 共通 | 対象run、取得時刻、実測/推定/未確認、owner、次行動 | evidence idとimmutable run | surface固有の再計算・別順位 | UI/CSV/Markdown/DOCX/snapshotでsemantic round-trip |


| surface | 現行の役割 | 望ましい primary audience | 保持する内容 | 別 surface へ移す内容 |
|---|---|---|---|---|
| 保存結果「評価」 | run summary | 経営・運用 | 結論、重大 3 件、実測/推定/未確認、run 時刻 | raw JSON、内部 feature flag、詳細 heuristic |
| 「やること」 | action cards | 経営・担当 manager | canonical 上位 action、owner、効果の確度、依存 | 実装 snippet、全 evidence trace |
| 「文章改善」 | copy suggestions | マーケ・編集 | before/after、source、fact-check 状態、publish checklist | prompt、model raw output |
| 「実装・設定」 | implementation tasks | Web 開発者 | 対象、変更、code、acceptance、rollback | 経営向け効果訴求、未検証の予測値 |
| 「エンジニア向け」 | raw detail | SEO/AIO・開発・セキュリティ | request/evidence/state、scanner source、raw diagnostics | primary decision card |
| 「履歴と比較」 | run history | 運用・経営 | immutable run id、日時、差分理由、同条件性 | ローカル絶対 path |
| CSV | 加工・取込 | 運用/分析 | stable id と canonical actions、redacted URL | formula-capable/raw secret、ローカル path |
| Markdown | issue / handoff | 開発・SEO/AIO | evidence link、owner、acceptance | 根拠のない効果保証 |
| DOCX | 閲覧・印刷 | 経営またはレビュー会 | executive 版と technical appendix を明示分離 | Markdown の単純複製、raw dump |

## 3. 用語の置換契約

| 現行/内部語 | primary UI での推奨 | engineer detail で保持する情報 |
|---|---|---|
| 内部ヒューリスティック | 簡易推定 / 判定根拠 | algorithm id、version、inputs、threshold |
| 参考 | 未確認 / 対象外 / 取得エラーを分ける | machine state と error code |
| AI引用率 +30〜40% | 効果は未実証。改善候補 | 出典、観測条件、confidence。出典がなければ数値を削除 |
| LCP/CLS 推定値 | 実測なし・リスク要因のみ | formula、入力、field/lab source absence |
| provider pass | 利用可能 / ブロック / 未確認 | robots response、対象 path、user-agent、header evidence |
| リンク切れ | 到達不可 / timeout / access denied / 未確認 | status、attempt、timestamp、redirect chain |
| 構造化データ不足 | 検出なし / 無効 / 未確認 / 推奨外 | normalized JSON-LD nodes と validator version |

## 4. 役割別 acceptance

- 経営者が 2 分以内に「止める事項」「今週やる 3 件」「効果の確度」を説明できる。
- 編集者が改善文ごとに原文根拠を開き、根拠なしの数値を公開前に識別できる。
- 開発者が card から変更面、再現、test、rollback を持つ issue を作れる。
- 法務/セキュリティ担当が自動判定と human review required を誤認しない。
- 運用担当が閲覧だけで run が変わらないことを checksum で確認できる。
- 全 role が同じ action id と priority を UI/CSV/Markdown/DOCX で確認できる。
