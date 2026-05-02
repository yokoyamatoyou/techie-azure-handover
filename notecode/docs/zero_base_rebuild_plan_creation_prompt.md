# notecode 生成部分ゼロベース再構築 — 計画作成用プロンプト

**用途**: 別タブでハイエンドの AI モデルを使い、**詳細な計画**を作成するときにこのファイルの指示に従ってください。  
**手順**: 計画を承認したあと、この計画に基づいて archive と新規実装を行います。archive は依存関係を復活可能な形で行います。

---

## プロンプト（そのままコピーして別タブに貼る）

```
あなたは、大規模リファクタとアーキテクチャ設計に強いシニアエンジニアです。

以下の【背景】【制約】【参照ドキュメント】【成果物の指定】を読み、**notecode（C:\tetie\notecode）の「生成部分」をゼロから再構築するための詳細な計画**を作成してください。

計画が承認されたのち、実装担当がその計画に従って
1) 対象コードの削除と archive（依存関係は復活可能な形で保持）
2) WORKLOG の圧縮と archive
3) 新パイプライン・新 UI のゼロベース実装
に進みます。したがって、計画には「何をいつ archive するか」「何を残すか」「新構成とフェーズ」「依存関係の復活手順」まで含めてください。

---

## 【背景】

- **プロジェクト**: TECHIE の 1 サービス「コトメイク」。テーマ・URL・PDF から日本語ブログ記事を生成する。本流は generation_mode: zero_base_v2。
- **現状**: 生成パイプラインと UI が肥大化している。
  - article_generator.py: 約 11,500 行（契約・談話・section・dedupe・後処理・guard が 1 ファイルに集中）
  - note_writer_app.py: 約 5,350 行
  - human_resonance/: 8 phase 約 4,500 行（本流では外しているがコードは残存）
  - human_resonance2/: quality pipeline 等 約 6,500 行
  - 禁止オープニング・文末・一人称などが prompt / Phase5・7 / guard に重複配置されている
- **判断**: 修正の積み重ねを避け、「生成部分＋UI をゼロからリファクタ」する方針（GAP_AND_NEXT_POLICY の選択肢 C）。
- **前提**: ①ソース → ②書く内容指示 → ③カテゴリUI → ④生成 の一本道を維持。カテゴリ別に temperature・verbosity・discourse 構成を 1 か所で定義。禁止・ルールは 1 層に集約。質問は必要に応じて（announcement は質問スキップを既定）。
- **現行の編集・リーガル**: 現在は **編集ペルソナ**（LLM に【編集ペルソナ】ブロックで渡す）と **Phase5Editor**（human_resonance）、**Phase6Legal**（human_resonance）がある。UI に「簡易リーガルチェック」あり。**方針（確定）**: **human_resonance は全体を archive** する。**編集**は新パイプラインで**軽量 1 層**にまとめる（意味の重複チェック・文法・AI ぽさがないかのチェック）。**リーガル**は**生成後にチェック**し、必要に応じて書換える。計画ではこの方針に沿って新構成を書くこと。

---

## 【制約】

1. **アーカイブ**: 削除するコードは「削除」ではなく **archive に移す**。ディレクトリ構成は archive 内で保持し、必要なら依存関係を復元できるようにする。
2. **WORKLOG**: ルートの WORKLOG.md（C:\tetie\WORKLOG.md）と notecode 固有の作業記録は、**要約・圧縮したうえで archive に退避**し、新規 WORKLOG はゼロベースで開始する。
3. **計画先行**: いきなり削除しない。**計画を詳細に作成し、ユーザーが承認してから** archive と新規実装に着手する。
4. **UI の形は変えず**: **画面レイアウト・タブ構成・見た目は現状のまま維持**する。ゼロベースにするのは「記事生成パイプラインの内部」および「生成ボタン〜結果表示までの呼び出し経路・契約連動」であり、**UI の形（レイアウト・コンポーネント配置）の作り直しは行わない**。変更するのは生成まわりのロジック・データの流れ・記事種類とパラメータの対応のみ。
5. **画像生成機能は保持**: **画像生成機能**（TOP画像・本文用画像プロンプト、画像編集・テキストオーバーレイ、プレビュー保存など）は**そのまま残す**。`note/image_prompt_mixin.py`・`note/image_editing.py`・`note/image_config.py` および note_writer_app 内の画像まわり UI は **archive 対象に含めない**。新パイプラインからも既存と同じインターフェースで画像生成を呼び出し、ユーザーが使っている画像機能は維持する。
6. **残すもの**: ソース取得（article_fetcher）、ログ・監査の仕様、llm_client・app_config・token_tracker、embedding による dedupe（zero_base/semantic_dedupe）の「呼び出し仕様」は残すか明確にし、必要なら archive から復活可能にしておく。
7. **仕様の取り込み**: スタイルガイド（ai_blog_japanese_style_guide.md）、GPT-5.4 相談のカテゴリ別パラメータ（temperature / verbosity / presence_penalty）、adoption_note の確定リストは、新パイプラインの**仕様**として計画に明記する。

---

## 【参照ドキュメント】（必ず読み、計画に反映すること）

以下のファイルを @ で指定して読み、計画に反映してください。

1. **C:\tetie\AGENTS.md** — プロジェクト全体の入口。notecode の役割・ディレクトリ・ログ・モデル設定。
2. **C:\tetie\notecode\ALGORITHM.md** — コトメイクのアルゴリズム正本。zero_base_v2 骨格・入力契約・監査項目。
3. **C:\tetie\notecode\puran6\GAP_AND_NEXT_POLICY.md** — 「完了してまだ全然」の整理、選択肢 A/B/C、**§6 ゼロベースリファクタのスコープと原則**（6.1 スコープ、6.2 原則、6.3 着手前に決めること）。
4. **C:\tetie\notecode\puran6\algorithm_complexity_and_gpt54_direction.md** — モジュール要不要、GPT-5.4 利用、UI 連動、ブログの方向性で表現・質問は必要に応じて。
5. **C:\tetie\notecode\docs\gpt54_consultation_category_params.md** — カテゴリ別パラメータ（解説／ストーリー／ブランド／お知らせ）、取り込み案、読者段階の扱い。
6. **C:\tetie\algorithm-proposals\人間ぽさアルゴリズム草案.md** — **人間ぽさアルゴリズム**の設計正本。談話計画・記事タイプ別 style profile・語彙連鎖・後処理（重複削除・リズム・一人称統一・段落化）・人間らしさスコア。新パイプラインで人間らしさをどう取り込むかはこの文書を反映すること。
7. **C:\tetie\AI文章の人間らしさに関する研究.md** — 人間らしさの研究（語彙多様性の異常・堆積した文体・バースト性・日本語の文末・プロンプト/パラメータ戦略）。人間ぽさアルゴリズムの根拠として参照する。
8. **C:\tetie\notecode\puran6\style_guide_implementation_plan.md** — SG1–SG4 の実装計画。禁止リスト・section 文言・discourse 明文化。
9. **C:\tetie\notecode\puran6\ai_blog_japanese_style_guide_adoption_note.md** — スタイルガイド採用方針・チェックリスト・config 方針。
10. **C:\tetie\notecode\docs\gpt54_migration_simplification_memo.md** — GPT-5.4 移行（reasoning none、カテゴリ別パラメータの参照先）。
11. **C:\tetie\notecode\puran6\research２\01_system_goal_and_constraints.md** — ソフトの目的・現行アーキテクチャ・守りたい制約。
12. **C:\tetie\notecode\puran6\research２\03_target_state_and_acceptance.md** — あるべき姿・受け入れ基準（announcement 等）。

必要に応じて以下も参照してください。
- C:\tetie\notecode\puran6\phase06_artifacts_2026-03-07.md — current/legacy 境界・rollback 単位。
- C:\tetie\notecode\AGENTS.md — notecode 直下の入口。

---

## 【成果物として求める計画の構成】

以下の構成で、**詳細な計画**を出力してください。見出しレベルと番号はこのとおりでなくてもよいが、内容はすべて含めること。
特に、**計画本文の独立章として「承認後の archive 整理手順（手順・順序・確認リスト）」を必須で含める**こと。

### 1. スコープの固定
- ゼロから書き直す対象: ファイル・ディレクトリの一覧、および「生成パイプライン」「UI（生成まわり）」の範囲の定義。**UI の形（レイアウト・タブ・見た目）は変えず、変更するのは生成呼び出し・契約連動・記事種類とパラメータの対応のみ**とする。
- **画像生成機能は archive しない**: image_prompt_mixin.py / image_editing.py / image_config.py および note_writer_app の画像まわり UI はそのまま残し、新パイプラインからも同じインターフェースで呼び出す。
- 対象外: ソース取得、ログ出力先、techie-hub、他サービス（aio2-main, doorknock）、**画像生成・画像編集の機能と UI** など。

### 2. アーカイブ対象一覧
- **コード**: archive に移すファイル・ディレクトリの一覧。パスは notecode 相対（例: `note/article_generator.py`）。**human_resonance は 8 phase 含め全体を archive** する（Phase5Editor・Phase6Legal を含む）。編集・リーガルの代替は「編集＝軽量 1 層」「リーガル＝生成後チェック→必要に応じて書換」で新実装する。
- **WORKLOG**: C:\tetie\WORKLOG.md および notecode 配下の作業記録の「圧縮・archive」方針。圧縮後の要約をどこに残すか、archive 先のパス。
- **archive 先**: 例 `notecode/archive/zero_base_rebuild_YYYY-MM-DD/` のような日付付きディレクトリ。その中に `code/`, `worklog/` などを置くか。

### 3. 残す・再利用するもの
- 残すファイル（そのまま稼働させる）: llm_client, app_config, article_fetcher, token_tracker, core/, config.json のうちどれを残すか。**画像生成まわり**: image_prompt_mixin.py, image_editing.py, image_config.py は残す。
- 仕様として再利用（コードは archive してもインターフェース・設定は新実装から参照）: semantic_dedupe の呼び出し、natural_blog_core の banned_openings 一覧の参照元、など。
- 依存関係の復活: archive したコードを後から参照したい場合の手順（パス、import の変更、テストの復旧）。

### 4. 新構成（ゼロベース実装後の目標）
- 新パイプラインのモジュール構成（ファイル名・責務を 1 行ずつ）。
- **新 UI の「記事種類」（記事タイプ）の一覧**: ユーザーが選択する記事種類の**表示ラベル**と**内部 article_type キー**の対応表。GPT-5.4 相談で推奨された「解説／日常／ブランド／お知らせ／事例／業界分析／比較レビュー」および現行の announcement, branding, ai, case_study 等を踏まえ、新 UI で提供する記事種類をすべて列挙すること。媒体（note / はてな / SEO記事）の扱いも計画に含める。
- 新 UI の画面フローと、input_contract に含める項目の一覧（記事種類・長さ・トーン等）。
- 記事種類（article_type）→ パラメータ（temperature, verbosity, presence_penalty）→ discourse 構成の対応表を 1 つ（表形式）。
- **人間ぽさアルゴリズムの取り込み**: `algorithm-proposals/人間ぽさアルゴリズム草案.md` および `AI文章の人間らしさに関する研究.md` を参照し、新パイプラインで**談話計画・記事タイプ別 style profile・後処理（重複削除・リズム・一人称統一・段落化）・人間らしさ評価**をどう実現するか（プロンプトに寄せるか／軽量後処理 1 層にまとめるか）を計画に明記すること。
- **編集・リーガルチェックの扱い（方針確定）**: human_resonance は**全体 archive** する。新パイプラインでは次のとおりとする。
  - **編集**: **軽量 1 層**のみ。意味の重複チェック、文法チェック、AI ぽさがないかのチェックを 1 モジュールにまとめる。編集ペルソナの長いプロンプトブロックは廃止し、必要ならプロンプト用の短い編集方針に要約するか省略する。
  - **リーガル**: **生成後にチェック**し、問題があれば**必要に応じて書換**する。本流の生成ループ内にはリーガル phase を入れない。**UI の「簡易リーガルチェック」**（テキスト貼り付け→根拠付き結果表示）は維持する。実装は Phase6Legal 相当を archive から復活させるか、新規 1 モジュールで実装するかを計画に明記する。
- 禁止・ルールの置き場所（プロンプトのみ / 1 つの postprocess のみ、のどちらか）。

### 5. フェーズと作業順序
- Phase 1: 計画承認〜archive 実行（削除ではなく移動、WORKLOG 圧縮と退避）。
- Phase 2: 新パイプラインの最小実装（contract → discourse → section → dedupe → minimal postprocess → gate の 1 本が通るまで）。
- Phase 3: 新 UI の実装（①ソース→②指示→**③記事種類（カテゴリ）**→④生成の一本道）。記事種類の選択肢と input_contract の 1:1 対応を含める。
- Phase 4: カテゴリ別パラメータ・スタイルガイド仕様の組み込みと検証。
- Phase 5: 監査・ログ・guard の接続とドキュメント更新。
- 各 Phase の成果物・完了条件・ロールバック条件を 1 行ずつ書く。
- **承認後の archive 整理手順**: 計画承認後、実装担当がすぐに実行する **archive の具体的な手順**を計画の一章に含める。内容の例: 何をどの順でどこに移動するか、archive 先ディレクトリの作成、WORKLOG の圧縮・退避の手順、実行後の確認リスト。計画を開けば archive の進め方が分かるようにする。

### 6. 依存関係の復活手順
- archive 後に「やはり旧コードのこの部分を参照したい」となった場合の手順（archive からのコピー先、import の修正、テストの追加）。
- 完全ロールバックの手順（新実装を止め、archive から復元して動かす方法）。

### 7. リスクとロールバック
- 新実装が品質・期限で届かない場合の切り戻し方。
- archive の保持期間と、いつ「完全削除」してよいかの判断基準（任意）。

---

## 【注意】

- 計画は**実装前に承認**される。承認前に archive（削除・移動）は行わない。
- 計画作成時点では、**コードの削除や archive は行わず、計画ドキュメントの出力のみ**を行う。
- 出力は Markdown 形式とし、そのまま `notecode/docs/zero_base_rebuild_plan_YYYY-MM-DD.md` のようなファイル名で保存できる形にする。
```

---

## このプロンプトの使い方

1. 上記の **「プロンプト（そのままコピーして〜）」の ``` で囲まれたブロック全体** をコピーする。
2. 別タブでハイエンドの AI モデルを開く。
3. 【参照ドキュメント】に挙げた 10 ファイルを @ で指定して読み込ませる（または先にそれらを開いてからプロンプトを送る）。
4. プロンプトを送信し、**計画の全文** を出力させる。
5. 出力を `notecode/docs/zero_base_rebuild_plan_YYYY-MM-DD.md` として保存する。
6. ユーザーが計画を確認・承認する。
7. 承認後、実装担当（別セッションまたは同じ AI）が計画の「2. アーカイブ対象一覧」「5. フェーズと作業順序」に従って archive と新規実装に進む。

---

## 参照

- **計画の出力形式・手順**: `docs/zero_base_rebuild_plan_first_prompt.md`（手順のみ・計画作成チャットでは @ しない）。送るプロンプトは **`docs/zero_base_rebuild_plan_prompt_to_send.md`** にあり、そこからコピーして送る。
- ゼロベースのスコープと原則: `puran6/GAP_AND_NEXT_POLICY.md` §6
- カテゴリ別パラメータ: `docs/gpt54_consultation_category_params.md`
- スタイルガイド実装: `puran6/style_guide_implementation_plan.md`
- **人間ぽさアルゴリズム**: `C:\tetie\algorithm-proposals\人間ぽさアルゴリズム草案.md`（談話計画・style profile・後処理・評価の設計）。研究根拠: `C:\tetie\AI文章の人間らしさに関する研究.md`。
