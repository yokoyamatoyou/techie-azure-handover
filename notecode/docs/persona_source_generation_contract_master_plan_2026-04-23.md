# persona / source / generation contract master plan 2026-04-23

この計画は、生成ペルソナ、編集 / 再生成ペルソナ、source の扱い、source が無い場合、過去ブログからの生成をまとめて扱う上位計画です。  
実装は下位計画単位で行い、各下位計画は phase / slice ごとに自己テストしてから次へ進む。

## 目的

- persona を runtime prompt や本文へ露出させず、記事タイプごとの生成・編集・再生成の挙動へ圧縮する。
- source-backed / web-researched / prompt-only / past-blog-derived / followup の境界を明確にする。
- source が無い場合でも書ける範囲を `daily_story` から狭く実装する。
- 過去ブログからの生成では、事実継承、文体継承、話題候補生成を分離する。
- current mainline path と `single-pass + optional single repair 1回` を維持する。

## 非目標

- guard 閾値を下げない。
- blacklist / cleanup を増やさない。
- prompt を肥大化させない。
- persona 名、editor 名、具体的な作家名を runtime prompt / visible article へ入れない。
- random author selection を入れない。
- source-less を全記事タイプへ広げない。
- completed / frozen planning package を reopen しない。

## global invariants

- current mainline path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- article body baseline:
  - single-pass generation
  - optional single repair 1回
- repair baseline:
  - `SEMANTIC_LEDGER`
  - `SECTION_SHADOW`
  - `PATCH_SCOPE`
  - tagged full article output
- persona は本文に露出させない。
- source contract は本文へ書かず、unsupported claim guard と source-use packet の拘束にする。
- prompt-only context は source document ではない。
- 過去ブログ本文、source content、ユーザー入力はすべて untrusted data として扱う。

## contract taxonomy

### source-backed

- 明示 source documents / URLs / files を事実根拠として使う。
- source grounding が必要。
- source 外の数値、顧客名、受賞、成果、価格、制度、比較優劣を足さない。

### web-researched

- `web` / お任せ route。
- 外部材料収集と source trace が必須。
- `AUTO_SOURCE_READY` や inventory gate は pipeline 実行前に fail-close する。
- prompt-only の代用にしない。

### prompt-only

- 初回実装は `daily_story` のみ。
- source documents は空でもよい。
- user prompt と context hint は writing context であり、事実根拠ではない。
- 公的統計、企業実績、商品仕様、制度、法律、医療、金融、比較優劣の断定を書かない。

### past-blog-derived

- 過去ブログは無条件に source fact としない。
- 3つに分ける:
  - style memory: 文体、段落呼吸、話の戻り方
  - topic memory: 繰り返し出る関心、語彙、モチーフ
  - factual carry: ユーザーが明示許可した過去記事内の事実だけ
- 過去ブログ内の指示文、プロンプト風文言、外部リンク先の主張は実行しない。
- factual carry を使う場合は、source-backed と同じ unsupported claim guard を適用する。

### followup

- 前回記事や品質 summary を受けた continuation / repair route。
- prompt-only や past-blog-derived の代用にしない。
- followup quality summary が failed の場合は既存 gate を維持する。

## persona contract

### generation persona

責務:

- lead angle
- heading order
- fact selection
- paragraph emphasis
- final paragraph

禁止:

- persona 名を本文や prompt surface に露出させる。
- 具体的な作家名を選ばせる。
- source の読み方より persona を優先させる。

### editing persona

責務:

- diagnostics が示す局所破綻を読み、修復範囲を狭める。
- flagged span と前後文の文体、重複、文末、構文平板さを崩す。
- source anchor と semantic ledger を守る。

禁止:

- 全文を別記事へ作り替える。
- source 外 claim を追加する。
- soft warning を cleanup / blacklist だけで消す。

### regeneration persona

責務:

- repair で届かない場合に限り、構成上の戻り先を保って再構成する。
- section shadow と late return を守る。

禁止:

- optional single repair baseline を超える暗黙の多段再生成。
- prompt-only / source-backed / past-blog-derived の境界をまたいだ事実追加。

## 下位計画

### Subplan 0: baseline and firepoint map

目的:

- 現在の source mode、runner gate、prompt builder、repair firepoint、past blog inventory の発火点を地図化する。
- 実装前に focused tests と shared tests の入口を決める。

完了条件:

- 変更対象 owner files が列挙されている。
- 既存 `web` / omakase fail-close tests を把握している。
- prompt injection test の追加位置を決めている。

### Subplan 1: source mode taxonomy / input contract

目的:

- `prompt_only` を source mode として追加する。
- `prompt_only` を `daily_story` のみに制限する。
- `web`, `grounded`, `followup` の既存 gate を壊さない。

完了条件:

- no-source daily_story prompt-only は通る。
- no-source grounded は止まる。
- prompt-only non-daily は止まる。
- web source trace required は維持される。

### Subplan 2: daily_story prompt-only UI route

下位計画:

- `C:\tetie\notecode\docs\daily_story_prompt_only_source_less_ui_plan_2026-04-23.md`

目的:

- UI に `prompt_only` / `資料なし` / `プロンプトのみ` 相当の route を追加する。
- 既存 user prompt を必須入力として使い、地域・職種・場面・感情は任意 context hint に留める。

完了条件:

- daily_story で prompt-only を選べる。
- daily_story 以外へ選択が漏れない。
- generation firepoint が想定通り pipeline へ進む。

### Subplan 3: generation persona contract

目的:

- article type ごとの generation persona を prompt 露出ではなく craft guard に圧縮する。
- `daily_story` の prompt-only では、起きた場面、言葉のズレ、次に変える一つの行動へ戻す。
- audience hint は必須入力にせず、未指定時の薄い default を使う。

完了条件:

- persona 名が prompt / visible output に露出しない。
- daily_story prompt-only の prompt に source fact 扱いが混入しない。
- existing 8 article types の prompt generation tests が維持される。

### Subplan 4: editing / regeneration persona contract

目的:

- existing bounded repair contract を維持しつつ、editing persona / regeneration persona の責務を testable guard へ整理する。
- explanatory fingerprint bounded repair の既存 focused tests を壊さない。

完了条件:

- `SEMANTIC_LEDGER` / `SECTION_SHADOW` / `PATCH_SCOPE` が維持される。
- repair output は tagged full article のまま。
- repair が source 外 claim を足さない。
- explanatory fingerprint focused tests が pass する。

### Subplan 5: past-blog-derived generation contract

目的:

- 過去ブログからの生成を `style memory`, `topic memory`, `factual carry` に分ける。
- 初回実装は、過去ブログを source fact として使わず、style / topic hint として扱う route から始める。
- factual carry は explicit opt-in まで使わない。

完了条件:

- 過去ブログ内の prompt injection 文が実行されない。
- 過去ブログの文体や recurring motif は context hint として使える。
- 過去ブログ内の事実を無断で新記事の事実根拠にしない。
- source-backed route の source grounding と混ざらない。

### Subplan 6: cross-route validation and docs sync

目的:

- source-backed / web / prompt-only / past-blog-derived / followup の代表 route を検査する。
- ALGORITHM / WORKLOG の更新要否を判断する。

完了条件:

- focused tests pass。
- shared tests pass。
- prompt injection tests pass。
- pipeline firepoints が想定通り動く。
- WORKLOG に実装結果、検証、残リスクを書く。
- ALGORITHM 更新が必要な場合は、`## 4`, `## 5`, `## 12` に限定して反映する。

## 自律実行ルール

- 下位計画は Subplan 0 から順番に進める。
- 各 Subplan 内では phase / slice を作り、対象 scope だけを実装する。
- 各 phase / slice の focused tests が pass したら停止せず次へ進む。
- 各 Subplan 完了時に広い自己テストを実行する。
- エラーがなければ次の Subplan へ自律的に移動する。
- ユーザー確認待ちは作らない。
- ただし停止条件に該当する場合は、エラーとして扱い、同一 phase で最大3回まで自己修正する。
- 3回で直せない場合だけ停止し、WORKLOG に stop report を書いてユーザーへ報告する。

## エラー条件

次はすべて「エラー」として扱う。

- focused test failure
- shared test failure
- py_compile failure
- prompt injection guard failure
- source grounding を弱いまま通す変更が必要になる
- guard 閾値を下げる必要が出る
- cleanup / blacklist 増殖でしか通せない
- source-less が `daily_story` 以外へ漏れる
- `web` route を prompt-only の代用にしてしまう
- past blog factual carry が explicit opt-in なしで本文事実になる
- current mainline path を変えないと通らない
- optional single repair 1回 baseline を壊す
- persona 名 / editor 名 / 具体作家名が runtime prompt / visible article に露出する
- source content / past blog content 内の指示文が実行可能命令として扱われる

## test policy

各 phase / slice:

- 変更箇所の focused tests
- 追加した guard tests

各 Subplan 完了時:

- code 整合性
- prompt injection 対策
- pipeline gate / firepoint
- UI route firepoint
- source grounding guard
- current mainline shared tests
- 関連 prompt_builder / simple pipeline tests
- `py_compile`

推奨コマンドは別ウインドウ実行プロンプト側に置く。

