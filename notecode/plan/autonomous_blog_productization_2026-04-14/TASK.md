# autonomous_blog_productization_2026-04-14 TASK

この package は `minimal UI + source-less web-grounded generation + autonomous completion loop` を別ウインドウで実装するための task 正本である。  
current keep-state を壊さず、phase pass ごとに自律継続し、同一仮説は 3 回まで自己修正する。

## Global Rules

- current success path を壊さない
- `1 phase = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- same failed hypothesis unchanged retry は 3 回まで
- 3 回失敗したら rollback 後に停止し user report する
- phase pass 後は user 待ちせず次 phase へ進む
- prompt accretion 禁止
- module accretion 禁止
- 新 helper は `既存 owner に安全な置き場がない` かつ `より大きい inline logic を防ぐ` 場合だけ 1 phase 1 個まで許可する
- source-less WEB mode は `daily_story / explanatory_article / industry_analysis` だけ許可する
- `branding/company_introduction` と `announcement` は source-backed を維持する
- source-less WEB mode で使う facts は URL / publisher / exact date / excerpt trace を残す
- current な WEB情報を扱うときは absolute date を保存する
- primary / official source を優先し、まとめサイトだけで generation を通さない
- UI first view は 3 primary decision groups と 1 text input を上限目安にする
- title は first view に置かない
- final acceptance では `company_introduction / explanatory_article / announcement` を生成し、Codex 視認評価を残す
- source-less WEB mode の acceptance は別枠で `daily_story` または `explanatory_article` を追加確認する

## Gates

### Entry Gate

- package docs が `README -> TASK -> PROGRESS -> ROLLBACK -> EXECUTION_PROMPT` で固定されている
- current keep-state と separate package boundary が明記されている
- phase hypothesis が `UI / contract / fetch / prompt / guard / evaluation` を同時に混ぜていない

### Pass Gate

- owner-local tests pass
- shared checks pass
- current success path regression なし
- `PROGRESS.md` と `ROLLBACK.md` 更新済み
- touched owner が narrow に説明できる
- source-less WEB mode を追加する phase では source trace と exact date が artifact で確認できる

### Stop Gate

- same hypothesis 3 failures
- broad regression
- source-less WEB mode が trace なし出力しか作れない
- UI refresh のために multiple owner simultaneous edit が必要になった
- final evaluation の 3 category で visible regression が出る

## Shared Checks

### Mainline Boundary

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

### Simple Note / Quality

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
```

### Owner-Local Rule

```text
owner file に対応する targeted tests が無ければ、phase 内で最小の owner-local test を追加してから shared checks へ進む
```

## Phase Map

### Phase 00 Package Lock And Baseline Freeze

- Objective:
  - current keep-state と separate execution line の境界を固定する
- Hypothesis:
  - 先に docs / rollback / final acceptance を固定すれば、別ウインドウの autonomous run が route drift しにくい
- Owner:
  - `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\`
- Tasks:
  - package docs を固定する
  - source-less WEB mode の allowed / blocked categories を固定する
  - final evaluation battery を固定する
- Exit:
  - separate window が docs だけで開始できる

### Phase 01 Minimal UI Journey

- Objective:
  - first view を `3 decision groups + 1 text input + 1 CTA` に縮退する
- Hypothesis:
  - UI text と choices を削れば、Hick's Law と Nielsen の minimalism を満たしつつ current mainline への入力 ambiguity を減らせる
- Owner:
  - `C:\tetie\notecode\note\note_writer_app.py`
- Tasks:
  - `どこに出すか / 何を書くか / 何から書くか` を first view に固定する
  - title / tone / CTA / SEO / detailed settings を fold 下へ退避する
  - `資料 / テーマ(Web) / 続編` の source mode を UI で選べるようにする
  - `announcement` に必要 facts が不足する場合は短い inline error で止める
- Exit:
  - first view が短い日本語で理解でき、extra prose なしで current mainline 入力へ進める

### Phase 02 Source Mode Contract Narrowing

- Objective:
  - source mode と industry hint を bounded contract として保持する
- Hypothesis:
  - `source_mode / web_research_allowed / industry_hint / source_trace_policy` を narrow に contract へ載せれば、後段で WEB mode を unsafe に広げずに済む
- Owner:
  - `C:\tetie\notecode\note\input_contract_v1.py`
- Tasks:
  - minimal source mode fields を contract に追加する
  - allowed categories と blocked categories を contract / policy 上で説明できるようにする
  - field sprawl を防ぐ
- Exit:
  - UI から runner まで source mode の意味が一意に通る

### Phase 03 WEB Research To Source Documents

- Objective:
  - source-less WEB mode を current mainline の `source_documents` へ hydrate する
- Hypothesis:
  - WEB検索結果を raw summary で渡さず、dated source documents に落とせば current mainline を壊さずに使える
- Owner:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
- Tasks:
  - allowed categories だけで WEB search を起動する
  - user prompt / industry hint / article type から 3〜5 query を作る
  - trusted source を収集し `source_documents` へ hydrate する
  - query / URL / publisher / date / excerpt を trace に残す
  - source 不足時は fail-closed する
- Exit:
  - source-less WEB mode が generation 前に source-backed 化される

### Phase 04 Distilled Brief For WEB-Grounded Generation

- Objective:
  - WEB-derived source digest を prompt bloat なしで generation に渡す
- Hypothesis:
  - `ui_prompt_distillation` の短い brief へ WEB source digest を足すだけなら、prompt-only 化せずに naturalness と grounding を両立できる
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
- Tasks:
  - WEB-derived digest を 4〜6 文へ圧縮する
  - exact date と current relevance が消えないようにする
  - company intro の neutral explainer keep-state を壊さない
  - announcement を WEB mode へ流さない
- Exit:
  - prompt length を過度に増やさず WEB-grounded daily/explanatory を書ける

### Phase 05 Guard And Trace Enforcement

- Objective:
  - WEB-derived output を trace / safety / category policy で fail-closed 管理する
- Hypothesis:
  - output guard が category boundary と source trace を強制すれば、unsafe な source-less generation を product mode に入れずに済む
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- Tasks:
  - blocked categories で WEB mode を拒否する
  - trace 不足 / stale / trusted-source不足を拒否する
  - failure reason を短い reason_code に落とす
- Exit:
  - WEB mode は allowed case だけ通り、unsafe case は fail-closed する

### Phase 06 Fixed Evaluation Battery And Codex Visual Review

- Objective:
  - autonomous 完走後の acceptance を fixed battery で確定する
- Hypothesis:
  - final battery を fixed にし、Codex 視認評価も残せば、数値だけでなく business-ready 判断ができる
- Owner:
  - `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
- Tasks:
  - fixed source-backed cases を `company_introduction / explanatory_article / announcement` で確定する
  - source-less WEB mode 用に `daily_story` または `explanatory_article` の representative case を 1 つ固定する
  - 各 case で generation artifact を保存する
  - Codex 視認評価で `stable pass / unstable pass / unresolved` を記録する
- Exit:
  - final 3 category + WEB mode case の verdict が docs と artifact に残る

## Final Acceptance

- source-backed final categories:
  - `branding/company_introduction`
  - `explanatory_article`
  - `announcement`
- source-less WEB mode final category:
  - `daily_story` or `explanatory_article`
- required outputs:
  - generated artifact
  - tests result
  - exact source trace for WEB mode
  - Codex visual judgment
- final judgment labels:
  - `stable pass`
  - `unstable pass`
  - `unresolved`
