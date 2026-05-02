# separate window execution prompt daily_story prompt-only source-less UI 2026-04-23

この prompt は別ウインドウ開始用。`daily_story` に限定して、UI から source-less / prompt-only 生成できる経路を追加する。

## 目的

- `daily_story` だけ、資料なしでもユーザープロンプトから生成できる UI route を追加する。
- 既存の `資料あり` と `お任せ` を壊さない。
- `お任せ` / `web` 外部材料収集とは別 mode にする。
- source document がない記事タイプを無制限に増やさない。

## 最初に読む

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\WORKLOG.md`
  - `2026-04-23 追記（notecode daily_story prompt-only source-less UI planning prompt）`
- `C:\tetie\notecode\docs\daily_story_prompt_only_source_less_ui_plan_2026-04-23.md`

## 現在の前提

- latest current mainline path は維持する:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- UI の source mode は現状 `資料あり` と `お任せ` のみ。
- `お任せ` は prompt-only 生成ではなく、外部材料収集 / omakase preflight route。
- `AUTO_SOURCE_READY` / inventory gate は pipeline 実行前に fail-close する既存仕様。
- `input_contract_v1.py` の source mode は現状 `grounded`, `web`, `followup`。
- guard 閾値を下げない。
- blacklist / cleanup を増やさない。
- prompt を肥大させない。
- persona 名、editor 名、具体的な作家名を runtime prompt / visible article へ入れない。

## 実装仮説

`daily_story` は source grounding よりも、場面、書き手の違和感、次に変える一つの行動が品質を決める。  
そのため `daily_story` に限り、source document なしの `prompt_only` route を作り、ユーザー入力を source ではなく context hint として渡す。

## 非目標

- `explanatory_article` の fingerprint bounded repair を触らない。
- `industry_analysis`, `case_study`, `comparative_review`, `branding`, `announcement` へ source-less を広げない。
- `web` mode を prompt-only の代用にしない。
- `followup` mode を prompt-only の代用にしない。
- 外部検索や source hydration を追加しない。
- 具体的作家のランダム選定を入れない。
- 過去ブログ蓄積からの生成 persona は今回実装しない。必要なら別 phase に記録する。

## 推奨 mode

- internal source mode key: `prompt_only`
- UI label: `プロンプトのみ` または `資料なし`
- 初期表示は既存どおり `資料あり`
- prompt-only は `daily_story` のみ有効

`prompt_only` の意味:

- source documents: empty allowed
- source trace: not required
- web research: false
- omakase preflight: not used
- user prompt / optional context hint: source ではなく writing context

## UI 方針

- 必須入力は増やさない。
- 既存 user prompt / 1行テーマを必須として使う。
- 地域、職種、場面、感情は、最初は placeholder / helper text で促す。
- フィールドを増やす場合も、1つの任意 `文脈メモ` に留める。
- `届いてほしい相手` は必須にしない。
- 未指定時は内部 default audience hint を使う。

内部 default audience hint:

- `daily_story`: `たまたま読みに来たが、似た感覚を持っている一般読者`

この hint は本文に直接書かない。語彙、説明量、例の粒度だけに使う。

## owner files

まず確認する:

- `C:\tetie\notecode\note\note_writer_app.py`
  - `SOURCE_MODE_LABELS`
  - `_SOURCE_MODE_INPUT_REQUIRED_MODES`
  - `_resolve_source_mode_selection`
  - `_build_source_mode_helper_text`
  - `_build_source_mode_input_surface`
  - `_build_omakase_surface_state`
  - `_build_generate_gate_surface`
  - `run_generation`
- `C:\tetie\notecode\note\input_contract_v1.py`
  - `SOURCE_MODES`
  - `normalize_source_mode`
  - `normalize_input_contract`
- `C:\tetie\notecode\note\current_mainline_runner.py`
  - `build_current_mainline_input_contract`
  - `validate_current_mainline_generation_gate`
  - `execute_current_mainline_generation`
- 必要な場合のみ:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`

## 作業計画

### Phase 0: characterize current tests

- 既存の `web` / omakase / source mode tests を確認する。
- `AUTO_SOURCE_READY` fail-close を維持する test を先に把握する。
- prompt-only の focused tests を先に足せるなら足す。

### Phase 1: input contract / gate

- `input_contract_v1.py` に `prompt_only` を追加する。
- `prompt_only` は `daily_story` のみ許可する。
- `prompt_only` のとき `web_research_allowed=False`、`source_trace_policy` は web trace required にしない。
- user prompt が空なら block、source が空でも user prompt があれば daily_story は通す。
- `current_mainline_runner.py` の gate で `prompt_only` を omakase preflight と無関係に扱う。

### Phase 2: UI

- source mode card / select に prompt-only を追加する。
- daily_story 以外では prompt-only を非表示または選択不可にする。
- daily_story 以外へ切り替わったとき、prompt-only が選ばれたままにならないようにする。
- `run_generation` の no-source rejection は `prompt_only` daily_story を通す。
- `web` の `AUTO_SOURCE_READY` / inventory gate 挙動は変えない。

### Phase 3: prompt hint

- user prompt を source document にしない。
- 追加するなら `prompt_only_context` / `context_hint` / `audience_hint` のような薄い contract field にする。
- prompt は `daily_story` の late return に圧縮する:
  - 起きた場面
  - 言葉のズレ
  - 次に変える一つの行動
- source-less fact guard を入れる:
  - 統計、会社実績、顧客名、受賞、価格、制度、法律、医療、金融などの断定を書かない。

### Phase 4: regression

Focused:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -q
.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
.\.venv\Scripts\python.exe -m pytest note\tests\test_note_writer_app_phase01_minimal_ui.py -q
```

Pipeline prompt coverage if touched:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
```

Shared:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

Useful explicit focused tests to add:

- prompt-only daily_story input contract accepts no sources with prompt
- prompt-only non-daily article type is blocked
- prompt-only daily_story generation gate accepts no sources
- prompt-only does not require web source trace
- web `AUTO_SOURCE_READY` still fail-closes before pipeline
- grounded no-source still blocks
- UI visible modes include prompt-only only for daily_story, or gate blocks it clearly outside daily_story

## 成功条件

- UI から `daily_story` / `prompt_only` / sourceなし / user promptありで生成経路へ進める。
- `web` / omakase の existing fail-close tests が維持される。
- `grounded` source required behavior が維持される。
- source-less route が source grounding bypass として他記事タイプへ漏れない。
- prompt-only context が source fact として扱われない。
- 本文が説明書・要約調ではなく、場面と気づきのある `daily_story` へ寄る。
- 変更後に WORKLOG へ実装結果、検証、残リスクを追記する。

## 停止条件

- `prompt_only` 実装が `web` research route の大幅変更を必要とする。
- guard 閾値を下げる必要が出る。
- cleanup / blacklist 増殖でしか通せない。
- source grounding を弱いまま通す必要が出る。
- `daily_story` 以外へ source-less 許可を広げないと通らない。
- 同一 phase で 3 回修正しても focused tests が通らない。

停止時は、変更ファイル、失敗 test、reason code、残る diagnostics、次の最小 owner scope を `C:\tetie\WORKLOG.md` に記録して報告する。

