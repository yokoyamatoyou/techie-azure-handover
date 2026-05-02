# daily_story prompt-only source-less UI plan 2026-04-23

この計画は、別ウインドウで `daily_story` の source-less generation UI route を実装するための小計画です。

## 目的

- UI から「資料なし / プロンプトのみ」で `daily_story` を生成できる経路を追加する。
- `web` / お任せの外部材料収集経路とは分ける。
- source document なしでも、日々のできごと・場面・感情をもとに自然な note / はてなブログ向け本文を作れるようにする。
- source grounding が必要な記事タイプを弱いまま通さない。

## 背景

現状の UI source mode は `資料あり` と `お任せ` のみで、`お任せ` は prompt-only 生成ではなく、外部ソース材料収集 preflight である。

確認済みの入口:

- `C:\tetie\notecode\note\note_writer_app.py`
  - `SOURCE_MODE_LABELS`
  - `_SOURCE_MODE_INPUT_REQUIRED_MODES`
  - `_build_source_mode_input_surface`
  - `_build_omakase_surface_state`
  - `_build_generate_gate_surface`
  - `run_generation`
- `C:\tetie\notecode\note\input_contract_v1.py`
  - `SOURCE_MODES`
  - `normalize_source_mode`
  - `WEB_RESEARCH_ALLOWED_ARTICLE_TYPES`
- `C:\tetie\notecode\note\current_mainline_runner.py`
  - `validate_current_mainline_generation_gate`
  - `build_current_mainline_input_contract`
  - `execute_current_mainline_generation`

## 決定

- source mode key は `prompt_only` を第一候補にする。
- UI label は `プロンプトのみ` または `資料なし`。実装時は既存 UI 文言と並べて自然な方を選ぶ。
- 初回実装は `daily_story` のみ。
- 他の記事タイプへ広げない。
- `web` mode を流用しない。
- `followup` mode を流用しない。
- 具体的な作家名や editor / persona 名を runtime prompt へ入れない。
- random author selection は入れない。揺らぎは構成・例・文末・段落の craft guard に圧縮する。

## UI 方針

- ユーザーの認知負荷を増やしすぎない。
- 必須入力は既存の user prompt / 1行テーマを使う。
- 地域、職種、場面、感情は個別必須フィールドにしない。
- 入れる場合は、1つの任意入力 `文脈メモ` 程度に留める。
- `届いてほしい相手` は必須にしない。
- 未指定時は内部の薄い audience hint を使う。

推奨デフォルト:

- UI 表示: `未指定なら記事タイプに合わせて自動調整`
- `daily_story` 内部 default audience hint:
  - `たまたま読みに来たが、似た感覚を持っている一般読者`

注意:

- audience hint は本文へ露出させない。
- 「あなたのような読者へ」のような呼びかけにしない。
- audience hint は語彙、説明量、例の粒度を調整するだけにする。

## source-less fact guard

`prompt_only` では、ユーザー入力は source document ではない。

- 書いてよい:
  - 日々のできごとの場面
  - 書き手の感じた違和感、迷い、気づき
  - 次に変える一つの行動
  - ユーザーが明示した範囲の経験
- 書かない:
  - 公的統計
  - 企業の実績、顧客名、受賞歴
  - 商品仕様、価格、制度、法律、医療、金融などの断定
  - source のない比較優劣

## phase plan

### Phase 0: current behavior tests

- 現状の `web` / omakase fail-close tests を確認する。
- `prompt_only` を追加しても、既存の `web` trace required / `AUTO_SOURCE_READY` fail-close を崩さない。

### Phase 1: input contract and runner gate

- `input_contract_v1.py` に `prompt_only` を追加する。
- `prompt_only` は `daily_story` のみ許可する。
- source trace policy は web trace required にしない。
- source documents が空でも、user prompt があれば runner gate を通す。
- `omakase_preflight_status` に依存させない。

### Phase 2: UI route

- `SOURCE_MODE_LABELS` に prompt-only mode を追加する。
- `daily_story` 以外では prompt-only を非表示または選択不可にする。
- article type が変わって prompt-only が不適合になった場合は、`grounded` に戻すか gate で明確に止める。
- `run_generation` の no-source rejection は `prompt_only` daily_story を通す。

### Phase 3: prompt / context hint

- `prompt_only` の context は source facts ではなく context hint として contract に渡す。
- 必要なら `prompt_only_context` / `audience_hint` / `context_hint` のような薄いフィールドを使う。
- prompt は肥大化させない。
- `daily_story` の late return は ALGORITHM `## 12` の基準に合わせる:
  - 起きた場面
  - 言葉のズレ
  - 次に変える一つの行動

### Phase 4: regression

- focused tests を追加して通す。
- existing `web` / omakase / grounded source tests を維持する。
- simple note pipeline と current mainline runner の shared tests を通す。

## success conditions

- `daily_story` / `prompt_only` / no source / user promptありで generation gate を通る。
- `web` mode の source trace guard は維持される。
- `AUTO_SOURCE_READY` は従来どおり pipeline 実行前に fail-close する。
- `branding`, `announcement`, `case_study`, `comparative_review`, `industry_analysis`, `explanatory_article` へ source-less を広げない。
- prompt-only 入力が source document 扱いされない。
- 本文が説明書・要約調にならず、日々のできごとの場面と気づきへ戻る。
- AGENTS / WORKLOG 更新要否を final report に含める。

## stop conditions

- `prompt_only` 対応が `web` research route の改変を必要とする。
- guard 閾値変更が必要になる。
- source grounding を弱いまま通す変更が必要になる。
- cleanup / blacklist を増やさないと通らない。
- 1 phase の修正が 2 route 以上へ広がる。
- 同一 phase で 3 回修正しても focused tests が通らない。

