# separate window execution prompt ui required inputs minimalization visual validation 2026-04-20

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_omakase_inventory_gate_2026-04-20.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate-window implementation prompt
- `UI_REQUIRED_INPUTS_MINIMALIZATION_AND_VISUAL_VALIDATION`
- docs-only prompt ではない
- verification-only prompt ではない

今回の user request:
- UI の選択肢が多いので、必須項目を最小化して current mainline UI を軽くしたい
- UI 配置は Hick's Law と Nielsen の usability heuristics に従って整理する
- hard required は原則:
  - 記事タイプ
  - 誰向け
  - 誰視点
  だけに寄せたい
- `誰向け` が blank のときに UI 上で `おすすめ` のような自動値になり、そのまま generate で error になる挙動がある気がするので確認したい
- LLM からの follow-up 質問はほぼ出ないので、不要なら current path から削る / safety-critical のみに縮めたい
- 実装後は各記事タイプごとに 3 回ずつ生成し、Codex が視認テストする
- 視認観点は:
  - 改行位置が自然か
  - 主語省略が自然か
  - 日本語の呼吸が不自然に機械的でないか

この window の primary objective:
- current UI を「生成開始までの認知負荷が低い 3 必須中心の面」に整理し、
- required 判定と generate gate を一致させ、
- 各記事タイプの visible output を 3 run ずつ確認して、
- UI simplification が visible naturalness を壊していないことまで確認する

今回の前提:
- current success path は
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を維持する
- pre-2026-04-02 records は current read order に戻さない
- completed / frozen package は reopen しない
- prompt accretion はしない
- broad redesign ではなく current mainline UI の narrow simplification に閉じる
- source-mode safety rule は壊さない
- article-type ごとの safety gate、source gate、announcement factual gate は必要なら残してよい

current code facts you must start from:
- C:\tetie\notecode\note\note_writer_app.py
  - `FIXED_ARTICLE_TYPE_LABELS` は現状 7 種:
    - `explanatory_article`: 解説・ノウハウ
    - `daily_story`: 日常のできごと
    - `branding`: 紹介
    - `announcement`: お知らせ
    - `case_study`: 事例・お客様の声
    - `industry_analysis`: 業界・市場の話題
    - `comparative_review`: 比較・選び方
  - `_prepare_current_mainline_required_inputs()` では現状 hard required は:
    - `speaker_profile` ただし `semantic_article_key == company_introduction` は除外
    - `audience_profile`
  - `core_message` は現状 hard required ではなく、条件付き表示
  - `writer role` は select で初期値あり
  - `audience_profile` は text input で、少なくとも current code 上は select の `おすすめ` ではない
  - visible source mode は `grounded` と `web(お任せ)` の 2 つ
- C:\tetie\notecode\note\current_mainline_runner.py
  - confirm / preview 時点で question policy と input decision がまだ残っている
  - ただし current path では UI 側 required gate が先に働きやすく、LLM question は低頻度
- C:\tetie\notecode\note\note_writer_app.py
  - `announcement` は `web` で止める inline rule がある
  - no-source guard と article-type guard が generation 前に走る

design principles you must explicitly follow in this slice:
- Hick's Law
  - 初回意思決定で同時に見せる分岐を減らす
  - 主経路で必要ない選択肢を 1 画面目に並べない
  - 「必須」と「任意」を見た目と配置で明確に分ける
- Nielsen heuristics
  - visibility of system status:
    - 今何が必須か、何が不足しているかを即読できること
  - match between system and real world:
    - `誰向け` / `誰視点` / `記事タイプ` の語彙は user language に寄せる
  - recognition rather than recall:
    - 初期値や補助文で思い出させるが、誤って送信できる auto fill にはしない
  - error prevention:
    - blank のまま進めないなら、generate 前にその理由を field 近傍で示す
  - aesthetic and minimalist design:
    - default 面では 3 required 以外を畳む、もしくは任意セクションへ退避する

this window's narrow scope:
1. required-input surface simplification
   - main surface の hard required を
     - 記事タイプ
     - 誰向け
     - 誰視点
     の 3 つへ寄せる
   - `core_message` / `tone` / `writing_focus` / `self_reference_policy` / その他補助入力は任意か詳細設定へ落とす
   - 「今の必須は何か」が UI 上で読めるようにする
2. default / blank behavior verification
   - `誰向け` blank 時の current behavior を確認する
   - 特に
     - UI 表示上 blank のままか
     - 自動で `おすすめ` 相当の値へ変換されるか
     - confirm では通るが generate で error になるか
     - field source / contract / generation gate のどこで崩れるか
     を特定する
   - bug が再現するなら narrow fix を入れる
3. LLM question lane reduction
   - current question policy のうち、通常系 clarification を減らすか bypass する
   - ただし safety-critical clarification は残してよい
   - 目標は「必須不足は UI が止める」「LLM は普段聞かない」
4. execution consistency
   - UI required 表示
   - confirm preview
   - generation gate
   の required 判定を一致させる
5. article-type validation
   - 7 記事タイプそれぞれで 3 run ずつ、計 21 run を行う
   - Codex が output を視認確認し、改行位置 / 主語省略 / AIっぽい硬さをレビューする

implementation boundary:
- `current_mainline_runner.py` と `note_writer_app.py` を中心に narrow に閉じる
- source mode / omakase gate の recent slice を壊さない
- dormant compatibility code は必要以上に触らない
- prompt wording の大規模変更で押し切らない
- naturalness package の source-of-truth を壊さない

recommended implementation order:
1. inspect current required-input mapping and question policy entry points
2. inspect actual UI widget defaults for:
   - article type
   - writer role
   - audience
   - source mode
3. reproduce the suspected `誰向け blank -> おすすめ or hidden default -> generate error` behavior
4. simplify the main UI so required fields are visually and logically limited to 3 items
5. move optional controls into details or demote them to non-blocking inputs
6. align confirm / preview / generation gate with the same required-field contract
7. reduce normal LLM clarification questions while preserving safety-critical stops
8. add / update tests for required inputs, blank behavior, and question-lane reduction
9. run targeted pytest
10. run 21 generation checks
11. perform Codex visual review and summarize per article type

files you will likely inspect and may edit:
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\tests\test_note_writer_app_phase01_minimal_ui.py
- C:\tetie\notecode\note\tests\test_note_writer_app_generation_gate_helpers.py
- C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py
- C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py
- if needed:
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py

hard requirements for the UI after this slice:
- required と表示するのは実際に generate を止める項目だけ
- main surface で user が最初に迷う choices を増やさない
- `誰向け` は blank を blank のまま扱うならその場で明示的に止める
- blank を内部 default へ勝手に変換してから generate failure にする挙動は許容しない
- `誰視点` は current article type / semantic に応じた初期値を持ってよい
- ただし「初期選択済み」と「必須入力済み」を混同させない

question-lane rules for this slice:
- keep:
  - source不足など safety-critical stop
  - `announcement` の factual不足
  - current path を unsafe にする clarification
- remove or narrow:
  - 通常の「誰向けかをもう少し具体的に」系 follow-up
  - UI 必須項目で十分回収できる質問
- final state:
  - 普段は質問しない
  - 危険時だけ fail-close or ask

minimum tests you should add or update:
1. required inputs contract
   - `speaker_profile` / `audience_profile` / article-type selection の扱いが current intended contract と一致する
   - optional inputs を空にしても required error にならない
2. audience blank behavior
   - `誰向け` blank のまま confirm / generate した時の挙動が一貫する
   - hidden auto fill や misleading placeholder が field value として流れない
3. question lane
   - 普通の required不足は UI gate で止まり、LLM question item を量産しない
   - safety-critical case だけ clarification or fail-close になる
4. UI surface
   - main visible required controls が 3 中心である
   - optional controls が details / non-blocking area に分離されている
5. generation gate
   - confirm では通るのに generate で required error になる不整合がない

minimum pytest commands:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_note_writer_app_phase01_minimal_ui.py note\tests\test_note_writer_app_generation_gate_helpers.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_note_writer_app_generation_execution_helpers.py note\tests\test_current_mainline_runner.py -q
- if required/input-contract regression risk is high:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py -q

article types you must test after implementation:
- `explanatory_article` / 解説・ノウハウ
- `daily_story` / 日常のできごと
- `branding` / 紹介
- `announcement` / お知らせ
- `case_study` / 事例・お客様の声
- `industry_analysis` / 業界・市場の話題
- `comparative_review` / 比較・選び方

generation validation protocol:
- each article type must be run 3 times
- total runs: 21
- do not rely only on unit tests
- use the actual current mainline generation path
- use minimal but valid inputs for the simplified UI
- prefer the simplest safe source mode allowed by each article type
- if an article type is blocked in `web`, use grounded inputs instead of forcing unsupported flow
- keep run notes so each output can be traced to:
  - article type
  - run number
  - source mode
  - input summary
  - result status

visual review checklist for every generated output:
- 改行位置:
  - 段落の切れ目が意味の切れ目と合っているか
  - 1 文ごとに不自然に改行されていないか
  - 長段落が連続しすぎていないか
- 主語省略:
  - 日本語として自然な省略になっているか
  - 省略で指示対象がぼけていないか
  - 企業 / 読者 / 書き手の主語が急に入れ替わっていないか
- AIっぽさ:
  - 接続詞の反復がないか
  - 末尾パターンが単調でないか
  - 要点の言い換え反復がないか
  - 不自然に「まず / 次に / 最後に」が並んでいないか
  - 体温のない説明調だけで押し切っていないか
- article-type fit:
  - 解説は説明に寄っているか
  - 紹介は company / product intro として自然か
  - お知らせは案内文として短く明確か
  - 事例は変化と学びが見えるか
  - 比較は評価軸と分け方が崩れていないか

run execution guidance:
- if a reusable local script or helper exists for repeated current-mainline generation, use it
- otherwise drive the same path through the current app/runtime without broad harness creation
- keep inputs narrow and comparable across runs
- for each article type, vary only lightly between 3 runs so naturalness variance can be seen
- do not silently skip failed runs; record them as failures

success criteria for this window:
1. current UI main surface is visibly simpler and organized around 3 required inputs
2. optional inputs are demoted without breaking safety gates
3. `誰向け` blank behavior is confirmed and fixed if broken
4. normal LLM follow-up questions are reduced or removed from the current path
5. confirm / preview / generation gate behave consistently
6. targeted pytest passes
7. 21 generation runs are completed or stopped with explicit reason
8. Codex visual review is completed for all successful runs
9. final report can state whether simplification is user-test-ready

stop conditions:
- simplifying required inputs starts breaking source-mode safety or article-type safety
- `誰向け` blank bug depends on a broad unrelated state-management rewrite
- generation validation requires external systems not available in the repo
- visible naturalness regresses badly across multiple article types
- the slice expands into broad prompt / pipeline redesign

final report must include:
1. files changed
2. final required inputs shown in UI
3. what optional inputs were demoted or moved
4. result of the `誰向け` blank verification
5. whether normal LLM follow-up questions were removed, narrowed, or left in place
6. pytest commands run and results
7. 21 generation run matrix with pass/fail counts
8. article-type-by-article-type visual review summary
9. major naturalness issues found, if any
10. whether user-test-ready status is achieved
11. if not fully achieved, the exact blocking point
```
