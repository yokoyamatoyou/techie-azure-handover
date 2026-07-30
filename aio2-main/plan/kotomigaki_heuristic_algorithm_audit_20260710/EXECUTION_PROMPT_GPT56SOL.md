# コトミガキ総合監査・修正案調査 指示書

## 実行条件

- 実行モデル: GPT-5.6sol
- 実行場所: 別ウインドウ
- 対象: `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main`
- 目的: コトミガキの現行アルゴリズムとUIが、非エンジニアにもエンジニアにも理解しやすく、かつSEO・LLMO・アクセシビリティ・セキュリティ監査として十分に高度かを、実装・実画面・テスト・ドキュメントの4面から調査する。問題があれば、根拠付きの修正案を作成する。
- 今回の作業は調査と修正案の作成まで。コード、設定、データ、現行仕様書、WORKLOGは変更しない。実装は別途承認されたowner作業として扱う。

## 必ず最初に読むファイル

1. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\AGENTS.md`
2. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main\AGENTS.md`
3. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main\ALGORITHM.md`
4. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main\WORKLOG.md`
5. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md`（存在する場合）
6. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\README.md`
7. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\TASK.md`
8. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\aio2-main\plan\tab_ia_rework_2026-04-04\` 配下の現行資料（存在する場合）

現行docsと過去のWORKLOG・plan・生成物が矛盾する場合、実装や仕様変更をせず、矛盾を明示する。`WORKLOG`は履歴であり、現行ownerの根拠にはしない。

## 調査対象の現行owner

少なくとも以下をコードで確認する。ファイル名だけで「対応済み」と判定しない。

- エンジン: `core/engine/orchestrator.py`, `core/aio_analyzer.py`, `core/scoring_engine.py`
- SEO/LLMO: `core/seo/`, `core/aio/`, `core/robots_analyzer.py`, `core/sitemap_analyzer.py`, `core/citation_generator.py`, `core/application/technical_summary_builder.py`
- サイトヘルス: `core/site_health/`（accessibility / security / vulnerability intelligence / OGP）
- UI入口: `nicegui_app.py`, `core/ui/dashboard.py`, `core/ui/panels.py`, `core/ui/saved_workspace.py`, `core/ui/panel_components.py`, `core/ui/styles.py`, `core/ui/tabs/`
- 保存・出力: `core/application/analysis_run_service.py`, `core/application/csv_export_service.py`, `core/application/markdown_report_service.py`, `core/application/docx_report_service.py`
- テスト: `tests/` の characterization、engine、UI、SEO/LLMO、site-health、security、accessibility 関連

## 監査A: Nielsenの10原則

UIの各主要導線を実際に確認する。

1. システム状態の可視性
2. 現実世界との一致
3. ユーザーの主導権と自由
4. 一貫性と標準
5. エラー予防
6. 思い出すより見て分かる
7. 柔軟性と効率
8. 美的で最小限のデザイン
9. エラーからの回復
10. ヘルプとドキュメント

対象導線は「URL入力→分析開始→進捗→完了→保存済み結果→最優先アクション→詳細→エンジニア向け情報→CSV/Markdown/DOCX出力→エラー・再試行→履歴比較」とする。

各原則について、次の形式で記録する。

- 判定: pass / partial / fail / unverified
- 具体的な画面・操作・コード位置
- 非エンジニアへの影響
- エンジニアへの影響
- 再現手順または確認できなかった理由
- 優先度: P0 / P1 / P2 / P3
- 修正案（実装owner、変更対象、受入条件）

## 監査B: 非エンジニア向けとエンジニア向けの分離・接続

次を確認する。

- 「今回の結論」「まずやること」「改善方法」が、専門知識なしで理解できるか。
- スコア、リスク、優先度、根拠、次アクションの関係が一読で分かるか。
- `matched_fields`、`canonical_terms`、raw signal、provider、CVE等の開発者語が、非エンジニア画面に露出していないか。
- 詳細を開けば、エンジニアが再現・修正できる十分な根拠（URL、HTTP status、該当箇所、検査条件、合格条件、確認日時）があるか。
- 非エンジニア向けの要約とエンジニア向けの詳細で、件数・判定・優先度が食い違っていないか。
- 「未取得」「対象外」「未確認」「問題なし」を混同していないか。
- UI、CSV、Markdown、DOCX、保存済みsnapshotで同じ意味が保たれているか。

## 監査C: SEOの高度さと妥当性

実装とテストを照合し、次の網羅性だけでなく誤判定・重複・優先順位・証拠品質を調べる。

- crawlability、robots.txt、sitemap/sitemapindex、canonical、noindex、redirect、HTTP error
- title、description、heading、lang、hreflang/x-default、mobile-first parity
- Core Web Vitalsまたはpage experienceの測定条件と未測定時の表示
- 内部リンク構造、リンク切れ、アンカー品質、孤立ページ候補
- structured dataのpage type別検証とJSON-LDの安全な扱い
- 画像・動画のdiscoverability、alt品質、OGP
- YMYL/E-E-A-Tや法務関連の扱いがSEOスコアを不当に操作していないか
- 1回の分析で取得する範囲、タイムアウト、巨大HTML、robots拒否、動的サイトの限界
- 公式仕様と実装の差分、古いGoogle/検索サービス前提、根拠URLと確認日

## 監査D: LLMO/AIOの高度さと誠実性

LLM検索向けの表現は「検索順位やAI引用を保証しない」ことを前提に評価する。

- entity linking、表記ゆれ、組織・著者・場所などのentity根拠
- E-E-A-T、引用候補、FAQ、speakable、構造化データの実効性と限界
- robots/AI crawler、SSR、llms.txt、provider別の扱いが混同されていないか
- 引用候補がページ本文の事実から抽出され、捏造・過度な要約・文脈欠落を防いでいるか
- LLM出力を使う箇所のtemperature、再現性、失敗時、入力の外部データ汚染、prompt injection耐性
- 固定辞書・キャッシュ・Wikidata等の鮮度、参照日時、API失敗時の誤表示
- 「AIに評価される」「引用される」など、根拠なしの断定や誤解を招くUI文言
- LLMOの指標がSEOの総合点に与える影響と、改善アクションとの因果関係

## 監査E: アクセシビリティ

可能ならローカルUIを起動し、ブラウザで確認する。静的検査だけで合格としない。

- WCAG 2.2 AAを基準に、キーボード操作、フォーカス可視性、見出し階層、ランドマーク、ラベル、エラー関連付け
- 色だけに依存しない状態表現、コントラスト、文字サイズ、ズーム、レスポンシブ幅
- 進捗・完了・エラー・保存後遷移のスクリーンリーダー向け通知
- tab、expansion、tooltip、dialog、data table、chart、コピー操作のアクセシビリティ
- 長文・専門語・リンク・ボタンの理解しやすさ
- PDF/DOCX/CSV出力のアクセシビリティ上の欠落
- 画面が「見える」だけでなく、支援技術で意味と順序が伝わるか

自動ツールが使えない場合は、できなかった検査を明記し、手動代替と残余リスクを分ける。

## 監査F: セキュリティ

攻撃手順やPoCを作成せず、防御・再現可能な安全な検査に限定する。

- SSRF、redirect、private/local IP、DNS rebinding、scheme/port制限
- robots.txt、巨大レスポンス、timeout、rate limit、crawl depth、同一host制約
- HTML/JS/CSS/JSONのサニタイズ、XSS、unsafe HTML、Markdown/DOCX/CSV injection
- URL・ファイル名・ログ・エラーメッセージへの秘密情報や個人情報の混入
- APIキー、LLM入力、外部取得HTML、prompt injection、保存snapshotのテナント分離
- 固定脆弱性DBの鮮度、照合ロジック、誤検知、CVEやexploit情報の露出境界
- 認証・認可・download endpoint・短期限SASの設計（ローカル版とAzure想定の差）
- 依存ライブラリ、subprocess、ファイル出力、SQLite、ログローテーション

## 監査G: 「高度だがユーザーにはシンプル」の総合判定

実際の初回ユーザーが、次の5問に迷わず答えられるかを確認する。

1. 何を調べた結果か。
2. いま最も重要な問題は何か。
3. まず何をすればよいか。
4. その判断の根拠は何か。
5. 技術担当者に何を渡せば直せるか。

加えて、初回表示の情報量、認知負荷、専門語、スコアの意味、優先順位、詳細への段階的開示、エラー時の回復、結果の共有可能性を評価する。単に情報量を増やす提案は禁止し、削る・まとめる・順序を変える案も含める。

## 検証方法

- `rg`で実装・文言・テスト・現行docsを横断検索する。
- 必要に応じて `.venv\Scripts\python.exe -m py_compile` と対象テストを実行する。ただし調査目的の読み取り・ローカルテストに限定する。
- UIは可能なら `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\techie-hub\start.bat force --no-pause` の既存運用に従って起動し、`http://127.0.0.1:8081/` と保存済み結果画面をブラウザで確認する。既存プロセスやデータを破壊しない。
- `200 OK`やファイル存在だけをUI検証の根拠にしない。実際の表示、操作、保存後ルート、コンソール/ページエラー、表示件数とデータ整合性を確認する。
- 外部の最新仕様を参照する場合は公式一次情報を優先し、URL、ページタイトル、確認日、実装への含意を記録する。Google、W3C、OWASP、OpenAI等の公式文書と、対象プラットフォームの公式仕様を優先する。

## 成果物

次の順序でレポートを作る。ファイル作成先は `aio2-main\plan\kotomigaki_heuristic_algorithm_audit_20260710\` とし、既存ファイルを上書きしない。

1. `README.md`: 調査範囲、対象commit/作業時点、未確認範囲、結論
2. `FINDINGS.md`: 重大度順の発見事項。各項目に証拠、影響、再現、推奨修正、owner、受入条件
3. `NIELSEN_MATRIX.md`: 10原則の判定表
4. `ROLE_READABILITY_MATRIX.md`: 非エンジニア/エンジニア/共通の表示・根拠・用語・導線の差分
5. `SEO_LLMO_A11Y_SECURITY_MATRIX.md`: 4領域の coverage、品質、限界、残課題
6. `REMEDIATION_BACKLOG.md`: 修正案を「docsのみ / UI文言・情報設計 / engine / security / test / live検証」に分け、依存関係とownerを付ける
7. `EVIDENCE_INDEX.md`: コード位置、テスト結果、画面URL/操作、スクリーンショット、公式出典の一覧

## 修正案の品質基準

- 「改善する」「分かりやすくする」のような抽象案は禁止。対象ファイル、責務owner、変更内容、受入条件まで書く。
- スコア式・判定閾値・取得範囲を変える案は、必ず `ALGORITHM.md`、characterization test、snapshot schema、UI/CSV/Markdown/DOCXの影響を併記する。
- UIの修正案は、非エンジニア向けラベル、エンジニア向け詳細、エラー文、空状態、未確認状態を分けて示す。
- セキュリティ修正案は、可用性・誤検知・分析範囲とのトレードオフを示す。
- 公式仕様で裏付けられないLLMO効果は、仮説・参考シグナル・保証不可として明示する。
- 実装していないものを「修正済み」「検証済み」と書かない。

## 終了条件

- 7つの監査（A〜G）を埋め、passだけでなくpartial/fail/unverifiedを残す。
- P0/P1の候補があれば、修正案・owner・受入条件を明記する。
- 実装は開始しない。修正案の承認待ちで終了する。
- 同じ検証箇所で3回連続して失敗した場合は、原因・試したこと・必要な追加権限または判断を記録して停止する。
- 最終報告の末尾に、次の実装ownerを1つだけ指定し、非owner範囲（今回触らない範囲）も明記する。
