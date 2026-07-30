# Next Window Prompt: writer-only pre-generation image tone and lean inputs

以下を別ウインドウのCodexへ貼って作業を開始する。

```text
goal: writer_only_pre_generation_image_tone_and_input_simplification_ui

C:\tetie\notecode で、writer-only通常UIの生成前入力を小さく整理し、画像トーンをブログ生成前に選べるようにしてください。

このownerはUI配線だけです。product code変更は許可しますが、本文生成アルゴリズム、画像生成アルゴリズム、プロンプト品質、ソース取得、SNS/LinkedIn生成、Route 0506/Route Aには触れないでください。実API送信は禁止です。

最初に読むファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\WORKLOG.md
- C:\tetie\notecode\docs\writer_only_ui_port_2026-06-02.md
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\note_writer_app_writer_only_ui.py
- C:\tetie\notecode\note\note_writer_app_generated_image_panel.py
- C:\tetie\notecode\note\note_writer_app_main_page_sections.py
- C:\tetie\notecode\note\image_prompt_helpers.py
- C:\tetie\notecode\note\blog_image_auto.py
- C:\tetie\notecode\note\writer_only_brief.py
- C:\tetie\notecode\note\writer_only_service.py
- C:\tetie\notecode\note\tests\test_note_writer_app_writer_only_ui.py
- C:\tetie\notecode\note\tests\test_blog_image_auto.py
- C:\tetie\notecode\note\tests\test_note_writer_app_main_page_sections.py

現状:
- 画像生成は writer-only 記事生成成功後の fail-open post-success work として自動実行される。
- 画像トーンの値は、値が取得できれば `IMAGE_PATTERN_LABEL_TO_KEY` -> `selected_image_pattern_key` -> `pattern_key` -> `generate_blog_images_for_article(...)` へ渡る。
- ただし現UIの `画像のトーン` selector は生成結果側の画像パネルにあるため、初回ブログ生成前には実質選べない。
- 過去のWORKLOGには「生成前に見える」と読める古い記録があるが、必ず現コードを確認して判断すること。
- そのため初回の自動画像生成はほぼ default の `シンプル` になる。
- writer-only可視入力カードには `会社側の語り手`、`記事目的`、`読者の課題` があり、通常利用では不要または混乱しやすい。

今回の実装目標:
1. `画像のトーン` selector をブログ生成前の writer-only生成カードへ移す、または同等に生成前に選択できるようにする。
2. 4つの選択肢は現行のまま維持する。
   - `シンプル`
   - `ブログ見出し画像風`
   - `フラットイラスト`
   - `温かい手描き風`
3. 生成前に選んだ値が、初回の post-success image generation の `pattern_key` に渡るようにする。
4. 通常UIから `会社側の語り手` を削除または非表示にする。writer-only service contract には内部 default `会社側の担当者` を渡してよい。
5. 通常UIから `記事目的` を削除または非表示にする。writer-only service contract には `短い指示` 由来、または safe default `相談前の判断軸を整理する` を渡してよい。
6. 通常UIから `読者の課題` を削除または非表示にする。writer-only service contract には safe default `判断材料を整理したい` を渡してよい。
7. `想定読者` は残す場合も任意・詳細扱いにしてください。必須に見せないでください。
8. 1本の `generation_progress` を使い、本文完了後に `1.0` へ行ってから画像生成で `0.92` に戻るような見え方を避ける。
9. status/progress copy はユーザー向けにしてください。例:
   - `資料を確認しています。`
   - `ブログ本文を作成しています。`
   - `SNS文章を作成しています。`
   - `画像を作成しています。`
   - `ブログ・SNS文章・画像を作成しました。`
   - `画像生成に失敗しました。ブログ本文とSNS文章はそのまま使えます。`

重要な境界:
- `note\blog_image_auto.py` の画像生成アルゴリズムは変更しない。
- `note\image_prompt_helpers.py` の4択ラベル、normalize、prompt direction は変更しない。ただしUI移動に必要な import/use は可。
- `note\writer_only_image_handoff.py` は変更しない。
- `BLOG_IMAGE_VARIANTS` の `with_text` / `without_text` 2枠契約を変更しない。
- OpenAI API / Images API を呼ばない。
- Route 0506 / Route A / `newalgorithm_pipeline` / `simple_note_pipeline` を復元しない。
- repair loop / quality pipeline を writer-only本文生成の本線へ戻さない。
- SNS/LinkedIn生成ロジックを変更しない。
- source intake / upload / manual legal UI を変更しない。
- prompt bloatを増やさない。

推奨実装方針:
- `note\note_writer_app_writer_only_ui.py` の `WriterOnlyControls` に image tone select を追加する。
- `render_writer_only_generation_card(...)` に `IMAGE_PATTERN_OPTIONS` / default label などを注入するか、過剰な import を避ける薄いhelperを使う。
- `build_writer_only_generation_kwargs(...)` は本文生成引数だけを扱う。画像トーンは本文生成kwargsに混ぜず、`run_writer_only_generation_click(...)` の `selected_image_pattern_key` で渡す。
- 不要入力をUIから消す場合でも `WriterOnlyControls` / `build_writer_only_generation_kwargs(...)` の contract が壊れないよう、内部 default を集中して扱う。
- 生成結果側の画像パネルでは、画像トーン selector を二重表示しない。生成済み画像表示と保存説明だけにする。
- 既存の `run_writer_only_post_success_images(...)` は fail-open のまま保つ。

最低限のテスト:
- `note\tests\test_note_writer_app_writer_only_ui.py`
  - 画像トーン selector が writer-only生成カード側にあること。
  - 選んだ `フラットイラスト` などが初回 image generation call の `pattern_key` へ渡ること。
  - `会社側の語り手`、`記事目的`、`読者の課題` が通常UIの visible writer-only card source から消えるか、少なくとも通常カードに表示されないこと。
  - 画像失敗時は本文/SNS/LinkedInを保持すること。
- `note\tests\test_blog_image_auto.py`
  - 4択 tone contract はそのまま通ること。
- 必要なら `note\tests\test_note_writer_app_main_page_sections.py`
  - 進行表示が1本の main progress 前提から外れないこと。

推奨validation:
```powershell
py -3.11 -m py_compile note\note_writer_app.py note\note_writer_app_writer_only_ui.py note\note_writer_app_generated_image_panel.py note\note_writer_app_main_page_sections.py
py -3.11 -m pytest note\tests\test_note_writer_app_writer_only_ui.py note\tests\test_blog_image_auto.py note\tests\test_note_writer_app_main_page_sections.py -q
py -3.11 -m pytest note\tests\test_writer_only_generation.py note\tests\test_writer_only_image_handoff.py note\tests\test_note_writer_app_subviews.py note\tests\test_api_send_counter_harness.py -q
```

UI/event-bindingを触った場合は、APIなしで起動確認してください。既存のポートが使われていれば別ポートでよいです。

完了報告に必ず含める:
- decision: fixed | needs_next_owner | blocked
- product_code_changed:
- changed_files:
- image_tone_pre_generation_select:
- removed_or_hidden_inputs:
- progress_bar_count:
- api_send_count: 0
- tests:
- route_0506_restored: false
- route_a_restored: false
- repair_restored: false
- quality_pipeline_restored: false
- sns_linkedin_changed:
- image_algorithm_changed:
- source_intake_changed:
- next_one_owner:
```
