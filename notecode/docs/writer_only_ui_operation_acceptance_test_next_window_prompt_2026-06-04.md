# Next Window Prompt: writer-only UI operation acceptance test

以下を別ウインドウのCodexへ貼って作業を開始する。

```text
goal: writer_only_ui_operation_acceptance_test_before_user_test

C:\tetie\notecode の writer-only 通常UIを、ユーザーテスト前の受け入れ確認として実際にブラウザ操作してください。特に、生成前の画像トーン選択、1本のプログレス表示、不要入力の非表示、ファイルアップロードからの生成が成立するかを確認します。

このwindowの主目的はテストです。原則として product code は変更しません。明確な実装バグを見つけた場合は、まず最小の再現と原因を artifact に残し、修正してよいか判断してから最小修正に限定してください。

最初に読むファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\WORKLOG.md
- C:\tetie\notecode\docs\writer_only_ui_port_2026-06-02.md
- C:\tetie\notecode\docs\writer_only_pre_generation_image_tone_next_window_prompt_2026-06-04.md
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\note_writer_app_writer_only_ui.py
- C:\tetie\notecode\note\note_writer_app_generated_image_panel.py
- C:\tetie\notecode\note\note_writer_app_main_page_sections.py
- C:\tetie\notecode\note\note_writer_app_source_input_helpers.py
- C:\tetie\notecode\note\writer_only_source_bundle.py
- C:\tetie\notecode\note\blog_image_auto.py
- C:\tetie\notecode\note\tests\test_note_writer_app_writer_only_ui.py
- C:\tetie\notecode\note\tests\test_note_writer_app_source_helpers.py
- C:\tetie\notecode\note\tests\test_writer_only_generation.py

前提:
- 通常UIの本文生成主経路は writer-only。
- Route 0506 / Route A / `newalgorithm_pipeline` / `simple_note_pipeline` は通常起動・通常生成へ戻さない。
- 画像生成は writer-only 成功後の fail-open post-success work。
- ファイルアップロードは UI の `ファイルを追加 (PDF/DOCX/txt/md/png/jpg/jpeg/webp)` から確認する。
- writer-only source policy では、アップロードされた `.pdf`, `.docx`, `.txt`, `.md` は `note\uploads` 配下の local document として許可されるべき。任意ローカルパスや unsupported 拡張子は許可しない。

禁止:
- OPENAI_API_KEY の値を表示しない。存在有無だけを報告する。
- ユーザー承認なしに実API送信しない。
- Route 0506 / Route A / repair / quality pipeline を復元しない。
- 画像生成アルゴリズム、画像プロンプト、SNS/LinkedIn生成、source intake policy を勝手に変更しない。
- テストのために product code を広く書き換えない。

artifact root:

```text
C:\tetie\notecode\artifacts\writer_only_ui_operation_acceptance_20260604\
```

最低限作るartifact:
- `ui_acceptance_plan.md`
- `server_start.md`
- `upload_test.md`
- `dom_check.md`
- `live_generation_preflight.md`
- `api_send_plan.md`
- `decision_before_live_api.md`
- live API を承認されて実施した場合のみ `live_generation_result.md`
- `final_acceptance_summary.md`

Phase 1: read-only / no-API preflight

1. 現在の変更状態を確認する。git repo でない場合はその旨だけ記録する。
2. 次を no-API で実行する。

```powershell
py -3.11 -m py_compile note\note_writer_app.py note\note_writer_app_writer_only_ui.py note\note_writer_app_generated_image_panel.py note\note_writer_app_main_page_sections.py note\note_writer_app_source_input_helpers.py note\writer_only_source_bundle.py
py -3.11 -m pytest note\tests\test_note_writer_app_writer_only_ui.py note\tests\test_note_writer_app_source_helpers.py note\tests\test_writer_only_generation.py note\tests\test_blog_image_auto.py -q
```

3. `OPENAI_API_KEY` は presence only で確認する。値は絶対に表示しない。
4. live API 実行前の想定送信数を `api_send_plan.md` に書く。
   - 通常見込み: writer-only本文/SNS 1 send + display-copy推論 1 send + 画像2 variants 2 sends = 4 sends
   - retry込み上限案: 6 sends
   - live実行は明示承認があるまで止める

Phase 2: local server and browser UI operation, no API submit yet

1. 既存サーバーがなければ一時ポートで起動する。例:

```powershell
$env:PORT="8099"; $env:HEADLESS="1"; py -3.11 run_kotomake.py
```

既に 8080 などで動いている場合は衝突しないポートを使う。起動ログとURLを `server_start.md` に残す。

2. Browser plugin / in-app browser を使って実際にUIを開く。明示的にブラウザ操作で確認する。HTTP 200だけで済ませない。

3. DOM/画面で確認する:
   - writer-only の `記事を生成` が見える。
   - `画像のトーン` が生成前の入力エリアで選べる。
   - 4択が見える: `シンプル`, `ブログ見出し画像風`, `フラットイラスト`, `温かい手描き風`。
   - 通常カードに `会社側の語り手`, `記事目的`, `読者の課題` が表示されていない、または詳細/任意扱いに退避している。
   - `想定読者` がある場合は任意に見える。
   - プログレスバーは主表示として1本だけに見える。
   - `記事の向き先`, `記事の前提`, Route 0506 / Route A を想起させる通常生成UIが見えない。

4. 画像トーン操作:
   - `画像のトーン` を `フラットイラスト` に変更する。
   - 値がUI上で保持されることを確認する。
   - この段階ではまだ `記事を生成` を押さない。API承認前に止める。

Phase 3: upload UI operation check

1. artifact root にテスト用ファイルを作る。product code に混ぜない。最低1つは `.md` または `.txt` を使う。

推奨サンプル:

```text
C:\tetie\notecode\artifacts\writer_only_ui_operation_acceptance_20260604\sample_source.md
```

内容例:

```markdown
# ユーザーテスト前のUI確認

この資料は、ブログ生成UIのユーザーテスト前に確認するためのテストソースです。
主な確認点は、資料アップロード、生成前の画像トーン選択、ブログ本文、SNS文章、画像生成の進行表示です。
ユーザーは、社内でブログ運用を始める担当者です。
記事では、初回テスト前に確認すべき操作導線と、アップロード資料から記事を作れることを説明します。
```

2. Browserで `ファイルを追加` uploader を操作し、このファイルをアップロードする。
   - in-app Browser が file chooser / upload に対応していない場合は、Chrome plugin など利用可能なブラウザ操作手段を使う。
   - どのブラウザ操作手段でもアップロードできない場合は `blocked` として、UI upload操作ができなかった理由を記録する。helper直叩きだけで「UI確認済み」とはしない。

3. アップロード後に画面上の `追加済みソース` にファイルが表示されることを確認する。
4. 可能ならアップロード保存先が `C:\tetie\notecode\note\uploads\...` になっていることをログまたはUI状態から確認する。
5. no-APIで可能な範囲で、writer-only source policy が uploaded local document を許可することを確認する。既存テスト/ヘルパーで確認してよいが、UI操作確認とは分けて記録する。

Phase 4: live UI generation test, only after explicit approval

ここから先はAPI送信を伴う可能性がある。Phase 1-3 の結果と `api_send_plan.md` を報告し、明示承認があるまで停止する。

承認された場合だけ、UIで次を実行する:

1. アップロード済み `.md` / `.txt` ソースを使う。
2. `今回書きたいこと` または `短い指示` に、次を入力する:

```text
ユーザーテスト前に、資料アップロードからブログ本文、SNS文章、画像生成まで一通り確認する記事にしてください。
```

3. `画像のトーン` を `フラットイラスト` にする。
4. `記事を生成` をクリックする。
5. 実行中に、1本のプログレス表示が以下のようなユーザー向け状態へ進むか観察する:
   - 資料確認
   - ブログ本文作成
   - SNS文章作成
   - 画像作成
   - 完了または画像fail-open
6. 完了後に確認する:
   - 記事プレビューが表示される。
   - SNS/LinkedIn用文章が表示される。
   - 画像パネルに `文字入り画像` と `文字なし画像` の枠または結果が表示される。
   - 画像生成に失敗しても、本文とSNS文章は保持される。
   - 最新ログに `touch_profile_key` が `flat_illustration` になっている、または image generation call/logの `pattern_key` が `flat_illustration` である。
   - 生成結果に Route 0506 / Route A / repair / quality pipeline が使われていない。

Phase 5: acceptance decision

`final_acceptance_summary.md` と最終報告に必ず含める:

- decision: ready_for_user_test | needs_fix_before_user_test | blocked
- tested_url:
- browser_tool_used:
- product_code_changed:
- api_send_count:
- upload_ui_tested:
- uploaded_file_path:
- uploaded_file_visible_in_ui:
- uploaded_file_policy_result:
- image_tone_pre_generation_select:
- selected_image_tone:
- selected_tone_reached_image_log_or_call:
- progress_bar_count:
- progress_copy_user_facing:
- article_preview_visible:
- sns_text_visible:
- image_panel_visible:
- generated_image_paths:
- route_0506_used: false
- route_a_used: false
- repair_used: false
- quality_pipeline_used: false
- source_intake_changed:
- image_algorithm_changed:
- sns_linkedin_changed:
- blockers:
- user_test_recommendation:

ready_for_user_test 条件:
- ブラウザUI上でファイルアップロードができ、追加済みソースとして見える。
- 生成前に画像トーンを選べる。
- 選んだ画像トーンが初回画像生成へ渡る証拠がある。
- プログレスバーが主表示として1本で、状態説明がユーザー向け。
- live承認済みの場合、アップロードファイルから本文/SNS/画像までUIで到達する。
- live未承認の場合は、`ready_for_user_test` ではなく `needs_live_approval_before_user_test` 相当の判断を明記する。
```
