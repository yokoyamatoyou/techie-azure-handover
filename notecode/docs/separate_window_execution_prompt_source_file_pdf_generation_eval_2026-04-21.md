# separate window execution prompt source file pdf generation eval 2026-04-21

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate window execution prompt
- `SOURCE_FILE_PDF_GENERATION_EVAL`
- ローカル Markdown / ローカル DOCX / Chrome PDF viewer URL / 横書き PDF を source として記事生成できるか確認する
- 生成物と評価結果を `C:\tetie\notecode\新しいフォルダー` に配置する
- 各ケースは 1 回ずつだけ実行する
- 同じケースの再試行で結果をよく見せない

今回の目的:
- URL source だけでなく、ローカル `.md` / `.docx` / PDF URL から source_documents を作れるか確認する
- `chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/...` 形式の Chrome PDF viewer URL を、実体の `https://...pdf` に正規化して扱えるか確認する
- 横書き PDF のテキスト抽出ができるか確認する
- 生成後、記事の自然さを Codex が人手レビュー視点で評価する
- 同じ生成物に対してアルゴリズム評価も出す
- ユーザー評価を後から追記できる評価シートも同じフォルダーに出す

今回の対象 source:
1. Local Markdown
   - `C:\tetie\notecode\AI文章の人間らしさに関する研究.md`
   - 事前確認:
     - file exists: true
     - size observed: 47318 bytes
   - 用途:
     - explanatory_article / learning_case のどちらが自然かを contract で確認し、基本は explanatory_article として1回生成する
   - 想定テーマ:
     - AI文章の人間らしさに関する研究内容を、実務で読みやすい形に整理する
2. Local DOCX
   - `C:\tetie\notecode\データエントリー（手入力）市場の推移とAI-OCR・生成AI・DXによる「消滅／変質」プロセス分析.docx`
   - 事前確認:
     - file exists: true
     - size observed: 35856 bytes
   - 用途:
     - industry_analysis or explanatory_article として1回生成する
   - 想定テーマ:
     - データエントリー市場がAI-OCR・生成AI・DXでどう変質するかを整理する
3. Chrome PDF viewer URL / direct PDF
   - original user URL:
     - `chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://www.cas.go.jp/jp/seisaku/digital_gyozaikaikaku/kaigi13/kaigi13_siryou1.pdf`
   - normalized URL:
     - `https://www.cas.go.jp/jp/seisaku/digital_gyozaikaikaku/kaigi13/kaigi13_siryou1.pdf`
   - related page:
     - `https://www.cas.go.jp/jp/seisaku/digital_gyozaikaikaku/kaigi13/gijishidai13.html`
   - 事前確認:
     - direct PDF HEAD observed: `200 application/pdf`, approximately 2.9MB
     - related page HEAD observed: `200 text/html`
   - 用途:
     - explanatory_article として1回生成する
   - 想定テーマ:
     - デジタル行財政改革の進捗と更なる対応について、資料に基づいて要点を整理する

出力先:
- `C:\tetie\notecode\新しいフォルダー`
- このフォルダーは存在確認済み
- 出力ファイル名は衝突しないよう `20260421_source_file_pdf_eval_` prefix を付ける

成果物:
- `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_summary.md`
- `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_results.json`
- `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_user_review_sheet.md`
- caseごとの生成物:
  - `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_01_md_naturalness_article.md`
  - `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_02_docx_data_entry_article.md`
  - `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_03_pdf_digital_admin_article.md`
- caseごとの評価:
  - `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_01_md_naturalness_eval.md`
  - `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_02_docx_data_entry_eval.md`
  - `C:\tetie\notecode\新しいフォルダー\20260421_source_file_pdf_eval_03_pdf_digital_admin_eval.md`

このウインドウで読むべきコード:
- source ingest / UI handoff:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- generation:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- quality / algorithm metrics:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- tests as needed:
  - `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase01_contract.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

事前チェック:
1. `C:\tetie\notecode\新しいフォルダー` が存在するか確認する
2. local Markdown / DOCX が読めるか確認する
3. Chrome PDF viewer URL を正規化する関数または手順を用意する
   - prefix `chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/` を取り除く
   - 残った `https://...pdf` を source URL として扱う
   - 他の Chrome extension id でも `chrome-extension://<id>/https://...` なら同じ方針で扱えるか確認する
4. PDF direct URL に HEAD/GET できるか確認する
5. PDF のテキスト抽出で、横書き資料の本文が page order で取れるか確認する
6. `.docx` は Python の `python-docx` などで段落・表テキストを抽出する
7. `.md` は Markdown 本文として読ませる。YAML front matter や見出しは本文構造として扱う

依存関係:
- 可能なら Codex desktop の workspace dependencies を使う
- `.docx`:
  - `python-docx` が使えるか確認
  - 表がある場合は table cells も抽出
- `.pdf`:
  - `pypdf`, `PyMuPDF`, or bundled PDF tooling のいずれかで抽出
  - 横書き PDF なので、行順が崩れていないか先頭3ページ程度を spot check
- dependency がない場合は、インストールではなく使える既存手段を確認し、どうしても不可なら `source_extraction_failed` として記録する

実行ケース:
1. `local_md_naturalness_research`
   - source: `C:\tetie\notecode\AI文章の人間らしさに関する研究.md`
   - article_type: `explanatory_article`
   - expected:
     - source_documents count >= 1
     - source_grounding_required = true
     - source_grounding_items が空ではない
     - source_fit.status != block
     - 生成物が source の研究内容から逸脱しない
     - 不自然に長くしない
2. `local_docx_data_entry_market`
   - source: `C:\tetie\notecode\データエントリー（手入力）市場の推移とAI-OCR・生成AI・DXによる「消滅／変質」プロセス分析.docx`
   - article_type: `industry_analysis` が使えるならそれを優先。不可なら `explanatory_article`
   - expected:
     - DOCX の段落と表が source_documents に入る
     - AI-OCR / 生成AI / DX / 手入力市場の変質プロセスが source-backed になる
     - source が厚い場合でも一般論で薄めない
3. `chrome_pdf_digital_admin_reform`
   - original source input:
     - `chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://www.cas.go.jp/jp/seisaku/digital_gyozaikaikaku/kaigi13/kaigi13_siryou1.pdf`
   - normalized source:
     - `https://www.cas.go.jp/jp/seisaku/digital_gyozaikaikaku/kaigi13/kaigi13_siryou1.pdf`
   - article_type: `explanatory_article`
   - expected:
     - Chrome extension URL は fetch 対象にせず、必ず normalized URL を fetch する
     - PDF direct URL から source_documents を作る
     - 横書き PDF の本文順が大きく崩れていない
     - PDF テキスト抽出が薄い場合は LLM 補強せず、抽出不足として分類する

各ケースで記録する source telemetry:
- case_id
- source path or original URL
- normalized source
- source kind: `local_markdown|local_docx|chrome_pdf_url|direct_pdf_url`
- extraction method
- extraction status: `ok|partial|failed`
- extracted char count
- page count if PDF
- paragraph count if DOCX/Markdown
- table count if DOCX
- source_documents count
- source document titles
- source document char counts
- source_grounding_required
- source_grounding_status
- source_grounding_items count
- source_fit.status
- source_fit.missing_buckets
- input_decision.action
- input_decision.reason_code

生成後に記録する algorithm evaluation:
- attempt_id
- runtime_reason_code
- output_guard.blocked
- output_guard reasons
- source_trace_coverage
- source_grounding_reflection_ratio
- must_cover_reflection_rate
- body chars
- title chars
- lead chars
- fingerprint / naturalness warnings if available
- quality_report path if generated
- latest_generation_output / latest_generation_quality_report から取れる場合は該当値を転記

生成後に Codex が行う自然さ評価:
- 各生成物を Codex が読み、以下を5段階で評価する
  - source fidelity: source にない断定が混じっていないか
  - naturalness: AIっぽい均一な説明になっていないか
  - rhythm: 文長・段落長が均一すぎないか
  - specificity: source の具体事実が使われているか
  - readability: 読み手が自然に読めるか
  - article fit: 記事タイプに合っているか
- 各項目に短い根拠を書く
- 問題がある場合は、修正ではなく `observed issue` として記録する
- 生成物本文をこの評価で直接書き換えない

ユーザー評価を合わせる方法:
- 可能
- `20260421_source_file_pdf_eval_user_review_sheet.md` に、各ケースごとのユーザー評価欄を作る
- ユーザー評価欄には以下を用意する
  - user score 1-5
  - 自然だった点
  - 不自然だった点
  - source と違う/怪しいと感じた点
  - 採用可否
  - コメント
- 最終 summary には Codex 評価・アルゴリズム評価・ユーザー評価を横並びにできる表を用意する
- ユーザー評価はこの実行時点では空欄でよい

評価の見方:
- algorithm evaluation:
  - 機械的な品質指標、source reflection、guard 判定を見る
- Codex evaluation:
  - 実際に読んだときの自然さ、説明の均一さ、source にない補強を見つける
- user evaluation:
  - 最終的な好み・実運用上の許容可否を見る
- 3つは別物として扱い、どれか1つだけで合否を決めない

今回の禁止:
- source 抽出が薄いのに LLM に事実補強させる
- PDF や DOCX の内容を読めていないのに推測で記事化する
- Chrome extension URL をそのまま HTTP fetch しようとして失敗扱いする
- output_guard.py の閾値変更
- naturalness 評価で本文を勝手に修正してから保存する
- 生成失敗ケースを再試行して成功扱いにする
- `C:\tetie\notecode\新しいフォルダー` 以外に成果物を散らす
- AGENTS / WORKLOG / plan docs 更新

pass 条件:
- Markdown source から source_documents と記事が作れる
- DOCX source から source_documents と記事が作れる
- Chrome PDF viewer URL から normalized PDF URL を取り出し、PDF source として処理できる
- 横書き PDF の抽出結果が記事化に使える程度に読める
- 生成物が `C:\tetie\notecode\新しいフォルダー` に配置される
- Codex 評価、アルゴリズム評価、ユーザー評価シートが同じフォルダーに揃う
- source insufficient / extraction failed の場合は LLM 補強せず、明確に stop/classify する

expected block / stop 条件:
- `.docx` 抽出に失敗した
- PDF の text extraction がほぼ空、または行順が壊れて意味を取れない
- source_documents はできたが source_grounding_items が空
- source_fit.status が block
- input_decision.reason_code が `INP_SOURCE_CONTEXT_INSUFFICIENT`
- この場合は記事生成へ進まず、評価ファイルに `expected_block` と理由を書く

実行後の summary に必ず書くこと:
- 3種類の source は処理可能だったか
- Chrome extension URL はどのように normalized されたか
- 横書き PDF の抽出は問題なかったか
- 生成物の保存パス
- Codex 評価の要約
- アルゴリズム評価の要約
- ユーザー評価欄の場所
- 残ったリスク
- 追加修正が必要か

最終報告フォーマット:
1. 読んだ正本 / 証跡 / コード
2. source extraction 結果
   - Markdown
   - DOCX
   - Chrome PDF URL / normalized PDF
3. 生成実行結果
4. 保存した成果物
5. アルゴリズム評価
6. Codex 自然さ評価
7. ユーザー評価シート
8. 可能だったこと / 不可だったこと
9. 残るエラー要因
10. 追加修正要否
```
