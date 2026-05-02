# ゼロベース再構築 — 計画作成の手順（1 ファイル or フェーズ別＋PROGRESS）

**用途**: 計画を作成するときの**手順と出力形式**の説明です。出力形式は **A) 1 ファイル＋PROGRESS**（推奨）か **B) フェーズごと別ファイル＋PROGRESS** を選べます。

**重要**: このファイルは**自分用の手順**です。計画を作成させるチャットには **@ で読ませないでください**。「別タブで…」「最初に書くプロンプト」などの表現が含まれるため、AI が「送るプロンプトを出力する」と勘違いすることがあります。参照 13 本と creation_prompt だけ @ し、**送る文言は `docs/zero_base_rebuild_plan_prompt_to_send.md` からコピー**して送ってください。

---

## 「@first_prompt を読んで計画作成して」で通じるか

**このファイル（first_prompt）を計画作成用チャットで @ すると勘違いします。** first_prompt には「別タブで…」「最初に書くプロンプト」などの手順が書いてあり、AI が「送るプロンプトを出力する」と解釈するおそれがあります。

**正しい進め方**: 計画作成用チャットでは **first_prompt を @ しない**。参照 13 本と creation_prompt だけ @ し、**送る文言は `zero_base_rebuild_plan_prompt_to_send.md` からコピー**して送る。計画の**中身**（背景・制約・スコープ・成果物）は creation_prompt と参照ドキュメントにあり、**形式**（1 ファイル＋PROGRESS・導線）は prompt_to_send に書いてある。

---

## どう進めたらいいか（手順）

1. **計画作成用のチャットを開く**  
   ハイエンドの AI モデルで新しいチャットを開く。

2. **参照ドキュメントだけを読み込む**  
   次の 13 ファイルを **@** で指定して読み込ませる。**このファイル（first_prompt）は @ しない。**
   - `C:\tetie\notecode\docs\zero_base_rebuild_plan_creation_prompt.md`
   - `C:\tetie\AGENTS.md`
   - `C:\tetie\notecode\ALGORITHM.md`
   - `C:\tetie\notecode\puran6\GAP_AND_NEXT_POLICY.md`
   - `C:\tetie\notecode\puran6\algorithm_complexity_and_gpt54_direction.md`
   - `C:\tetie\notecode\docs\gpt54_consultation_category_params.md`
   - `C:\tetie\algorithm-proposals\人間ぽさアルゴリズム草案.md`
   - `C:\tetie\AI文章の人間らしさに関する研究.md`
   - `C:\tetie\notecode\puran6\style_guide_implementation_plan.md`
   - `C:\tetie\notecode\puran6\ai_blog_japanese_style_guide_adoption_note.md`
   - `C:\tetie\notecode\docs\gpt54_migration_simplification_memo.md`
   - `C:\tetie\notecode\puran6\research２\01_system_goal_and_constraints.md`
   - `C:\tetie\notecode\puran6\research２\03_target_state_and_acceptance.md`

3. **送るプロンプトを送る**  
   **`notecode/docs/zero_base_rebuild_plan_prompt_to_send.md`** の「送るプロンプト」をコピーし、@ で読み込ませた直後にそのまま送る。

4. **出力を保存する**  
   - 計画本文 → `notecode/docs/zero_base_rebuild_plan_YYYY-MM-DD.md` として保存。  
   - PROGRESS 雛形 → `notecode/plan/zero_base_rebuild_YYYY-MM-DD/PROGRESS.md` などに保存。

5. **計画を確認・承認する**  
   内容を確認し、問題なければ承認。承認後にのみ archive と新規実装に着手する。

6. **承認後**  
   計画の「アーカイブ対象一覧」「フェーズと作業順序」に従い、実装を進める。

---

## 送るプロンプトの置き場所

送る文言は **`docs/zero_base_rebuild_plan_prompt_to_send.md`** に記載しています。そこからコピーして送ってください。このファイル（first_prompt）には「別タブ」「最初に書く」などの表現があるため、計画作成用チャットには @ で読ませません。

## 推奨: 1 ファイル＋PROGRESS で出す場合

送る内容は **`docs/zero_base_rebuild_plan_prompt_to_send.md`** に記載。参照 13 本を @ で読み込ませたあと、そのファイルから「送るプロンプト」をコピーして送る。

## B) フェーズごと別ファイルで出す場合のプロンプト

```
あなたは、大規模リファクタとアーキテクチャ設計に強いシニアエンジニアです。

これから **notecode（C:\tetie\notecode）の「生成部分」をゼロから再構築するための計画** を作成してもらいます。計画の**出力形式と運用ルール**は次のとおりです。この形式に従って計画を出力してください。

---

## 【計画の出力形式と運用ルール】

1. **フェーズごと別ファイル**
   - 計画は 1 本の巨大な md ではなく、**フェーズごとに別の md ファイル**に分けて出力する。
   - 例: `phase01_archive_and_scope.md`, `phase02_pipeline_minimal.md`, `phase03_ui_contract.md`, `phase04_params_style.md`, `phase05_audit_docs.md` など（フェーズ名・ファイル名は内容に合わせてよい）。
   - 各ファイルには「そのフェーズの目的・前提・作業一覧・完了条件・ロールバック条件・archive から復活する場合の参照先」を含める。

2. **PROGRESS ファイルで進捗管理**
   - **PROGRESS.md** を 1 つ用意し、全フェーズの進捗を一覧できるようにする。
   - 記載内容の例: フェーズ一覧、各フェーズの状態（未着手 / 進行中 / 完了）、現在どのフェーズをやっているか、直近の更新日、次のアクション。必要なら「依存関係の復活手順」「archive 一覧へのリンク」も PROGRESS にまとめる。

3. **不要物はすべて archive**
   - 計画対象外の既存 md やドキュメント・不要な成果物は、**すべて archive に退避**する。計画で「残す」と明示したもの以外は archive でよい。
   - 現在の計画用 md（例: `zero_base_rebuild_plan_creation_prompt.md` や既存の `zero_base_rebuild_plan_*.md`）も、計画承認後は **archive に移す** 運用にしてよい（参照用にコピーを残すかはプロジェクト方針に合わせる）。
   - archive 先は例: `notecode/archive/zero_base_rebuild_YYYY-MM-DD/docs/` や `.../plan/`。コードの archive とは別に「ドキュメント・計画の archive」を一覧に含めること。

4. **フェーズ進行中に必要になったら archive から復活**
   - 作業中に「過去の仕様やコードを参照したい」となった場合は、**archive から必要なだけ復活**する。一括復活はしない。
   - 各フェーズの md に「このフェーズで参照しがちな archive のパス・復活手順」を 1 行ずつ書いておく。PROGRESS にも「依存関係の復活手順」への参照を書く。

---

## 【あなたがやること】

- 上記の「フェーズ別ファイル・PROGRESS・archive 一括・必要時復活」のルールに従い、**計画の骨子**（フェーズ一覧・各フェーズのファイル名・PROGRESS の項目例）を先に示す。
- 続けて、依頼者から渡される【背景】【制約】【参照ドキュメント】【成果物の指定】（`zero_base_rebuild_plan_creation_prompt.md` に記載の内容）を読み、**各フェーズの中身**を上記形式で詳細に出力する。つまり:
  - **PROGRESS.md** の雛形
  - **phase01_xxx.md** 〜 **phase0N_xxx.md** の各ファイルの内容
  - **archive 対象一覧**（コード・WORKLOG・**既存の計画用 md や不要ドキュメント**を含む）
  - **復活手順**（PROGRESS または phase01 に記載）

依頼者が参照ドキュメントを @ で読み込ませたあと、この指示と `zero_base_rebuild_plan_creation_prompt.md` のプロンプトを合わせて送れば、上記形式で計画が出力されるようにしてください。
```

---

## このやり方の中立的な評価

### メリット

- **フェーズ単位で文脈が分かれる**: いま実行しているフェーズのファイルだけ開けばよく、巨大 1 ファイルをスクロールしなくてよい。
- **PROGRESS で一覧できる**: 「いまどこまで進んだか」「次は何か」を 1 ファイルで把握しやすい。
- **archive で作業ディレクトリがすっきりする**: 不要な md や古い成果物を一括退避できるため、計画〜実装のルートが明確になる。
- **必要時だけ復活**: 依存関係を一括で戻さず、必要な部分だけ archive から参照・復活できるため、新コードの依存を少なく保ちやすい。

### デメリット・リスク

- **ファイル数が増える**: フェーズ数ぶん md が増え、参照するときに「どのファイルに何が書いてあったか」を覚える必要がある。
- **フェーズ間の参照が面倒**: 「Phase 2 の完了条件は Phase 3 の前提」のように横断的な記述が、複数ファイルに分散すると重複したり抜けたりしやすい。
- **復活手順を毎回確認する手間**: 「このフェーズで復活する可能性があるもの」を各 phase に書いても、実際に復活するときは archive のパスや import を都度確認する必要がある。
- **PROGRESS と各 phase の二重更新**: 進捗を変えたときに PROGRESS と該当 phase の両方を更新しないと不整合になる。

### 中立まとめ

- **チーム規模が小さい・計画を細かく切りたい・「今やっているフェーズ」だけ集中したい**場合は、フェーズ別ファイル＋PROGRESS は合う。
- **計画を 1 本のドキュメントとして読みたい・参照を少なくしたい**場合は、1 ファイルの方が向く。
- 「不要物はすべて archive」は、**archive 先の一覧と復活手順を明文化しておけば**運用しやすい。復活手順が曖昧だと、のちのち「どこに何があったか」が分からなくなるリスクがある。

---

## もっと良い方法の候補

### 案 A: 1 ファイル＋目次＋PROGRESS のみ別（シンプル）

- 計画の**本文は 1 つの md**（例: `zero_base_rebuild_plan_YYYY-MM-DD.md`）にまとめ、目次でフェーズを飛ばし読みする。
- **PROGRESS.md だけ別ファイル**にし、「現在のフェーズ・完了済み・次のアクション」だけを PROGRESS で管理する。
- **メリット**: 参照するファイルが 2 つ（計画 1 本＋PROGRESS）だけ。横断的な記述が 1 ファイル内で完結する。  
- **デメリット**: 計画ファイルが長くなる。フェーズごとに「この部分だけ印刷したい」というときは範囲指定が必要。

### 案 B: 計画は 1 ファイル、実行時チェックリストは PROGRESS に集約

- 計画の「何をするか・順序・成果物」は **1 ファイル**に書く。
- **PROGRESS** には「フェーズ別のチェックリスト（やること一覧）・完了日・備考」だけを書き、実装担当は PROGRESS を見ながら作業し、詳細は計画ファイルの該当セクションを参照する。
- **メリット**: 計画と進捗の役割がはっきりする。計画は読み物、PROGRESS は実行用。  
- **デメリット**: 計画ファイルが長いまま。

### 案 C: ハイブリッド（概要 1 ファイル＋フェーズ詳細だけ別ファイル）

- **概要・スコープ・archive 一覧・復活手順・リスク**は **1 ファイル**（例: `zero_base_rebuild_overview_YYYY-MM-DD.md`）にまとめる。
- **各フェーズの詳細**（作業手順・完了条件・ロールバック）だけ **phase01_xxx.md 〜 phase0N_xxx.md** に分ける。
- PROGRESS では「いまどのフェーズか」と「各 phase ファイルへのリンク」を書く。
- **メリット**: 全体像は 1 ファイルで把握でき、細部はフェーズファイルに分かれて読みやすい。  
- **デメリット**: 概要とフェーズ詳細の間で記述が重複することがある。

---

## 使い分けの目安

| 優先したいこと | 向くやり方 |
|----------------|------------|
| **参照を少なくしたい・1 本で読みたい・分かりやすさ重視** | **案 A（1 ファイル＋PROGRESS のみ別）— 推奨** |
| フェーズごとに文脈を切りたい、ファイルを分けて担当を分けたい | フェーズ別ファイル＋PROGRESS＋archive 一括 |
| 計画は読み物・進捗はチェックリストで管理したい | 案 B（計画 1 本＋PROGRESS でチェックリスト） |
| 全体像は 1 ファイル、フェーズの細部は別ファイル | 案 C（ハイブリッド） |

**ファイルは 1 つのほうが分かりやすい**場合は、このファイル冒頭の「推奨: 1 ファイル＋PROGRESS で出す場合のプロンプト」をそのまま使えばよいです。
