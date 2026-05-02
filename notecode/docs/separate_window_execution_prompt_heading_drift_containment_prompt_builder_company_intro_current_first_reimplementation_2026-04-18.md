# separate window execution prompt heading drift containment prompt builder company intro current first reimplementation 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_implementation_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md
- C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\summary.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- narrower re-implementation prompt
- `HEADING_DRIFT_CONTAINMENT_FIRST` line の second narrow owner step
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` owner に閉じて、company intro の current-business-first keep line を nonblank company intro にも効かせる narrow diff を実装する
- explanatory 側で得た partial gain は壊さない
- `pipeline.py` / `quality_guard.py` / AGENTS / WORKLOG / current package docs は更新しない
- owner-local tests、full simple-note、必要最小限の live validation まで自律的に進める

current local finding that must inherit:
- live validation verdict:
  - `REGRESSION`
- exact split:
  - V1 explanatory:
    - partial gain
  - V2 explanatory:
    - gain weak
  - V3 company intro:
    - fail
    - first heading / first section が history-first に再アンカー
  - G1 non-target branding:
    - pass
- important code read:
  - current-business-first line は `_preflight_company_intro_generation_blocks()` で強く入っている
  - ただし trigger は `company_intro_blank_prompt = true` のときだけ
  - live validation の V3 source は
    - `prompt_raw = "自社の事業内容と選ばれる理由を紹介する"`
    - `topic = "自社の事業内容と選ばれる理由を紹介する"`
    であり、blank prompt ではない
- therefore:
  - failure は generic title/lead/heading contract それ自体より、
    `current-business-first keep line が nonblank company intro へ届いていない`
    ことが main candidate である

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- current redirect line:
  - `HEADING_DRIFT_CONTAINMENT_FIRST`
- do not reopen:
  - `pipeline.py`
  - `quality_guard.py`
  - repair acceptance reopen
  - `SECTION_SHADOW` company intro 再導入
  - generic explanatory contract の rollback

implementation hypothesis:
- company intro の current-business-first frame を blank prompt 限定ではなく、
  `generic self-intro / company-intro-intent が明確な nonblank prompt`
  にも narrow に再利用すれば、
  V3 の first heading / first section history-first drift を抑えつつ、
  V1 explanatory の partial gain を壊さずに済む

target line to implement:
- conclusion label:
  - `COMPANY_INTRO_FRAME_REUSE_FOR_NONBLANK_CURRENT_FIRST`
- narrow exact read:
  - blank prompt 専用 line をそのまま全面化するのではなく、
    `company_introduction` かつ `prompt_raw/topic` が generic self-intro intent のときだけ
    current-business-first frame を generation prompt に入れる
- acceptable local shape:
  - title / lead / 最初の見出し / 1節目本文が current business から見える
  - history / 歩み / 沿革 / 創業 は背景か後段に回す
  - explanatory 用 generic contract line は keep
  - non-target branding には広げない

implementation constraints:
- `1 phase = 1 narrow hypothesis = 1 owner scope` を守る
- owner file は `prompt_builder.py` のみ
- helper 追加は最小限
- if 文の追加でもよい
- blank prompt 専用 test を壊さない
- explanatory 向け generic contract line を rollback しない
- prompt accretion 禁止
- module accretion 禁止

what to inspect before editing:
- `company_intro_blank_prompt` の current trigger
- `_build_company_intro_writer_brief()`
- `_preflight_company_intro_generation_blocks()`
- `prompt_raw/topic` が nonblank でも company intro intent が generic なケースを、local evidence でどう見分けるか
- 既存 test が blank prompt だけを固定していること

good implementation shape:
- company intro intent の判定が狭い
- V3 source 相当の generic self-intro prompt にだけ current-first line が届く
- explanatory / branding guard に波及しない
- blank / nonblank の company intro 両方で current-business-first read を保てる

bad implementation shape:
- company intro 全件に強い line を雑に足す
- explanatory まで巻き込む
- title / lead / heading を全部同じ wording に寄せる
- `SECTION_SHADOW` を戻す
- `pipeline.py` の repair line に逃げる

do not:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` を編集しない
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py` を編集しない
- AGENTS / WORKLOG / current package docs を更新しない
- deepresearch を first step にしない
- blank prompt keep line を捨てない
- V1 explanatory の partial gain を rollback しない

touched files:
- code:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- tests:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- optional logs:
  - `C:\tetie\notecode\logs\` 配下の focused validation artifact

self-execution policy:
1. まず local code read で `nonblank company intro intent` の narrow condition を決める
2. 実装する
3. focused tests を実行する
4. full simple-note を実行する
5. 必要なら quality-guard check を実行する
6. V3 company intro と guard 2 cases を narrow に rerun する
7. blocker が出たら local self-fix を先に行う
8. local self-fix だけで解けない blocker に限り、WEB検索を1回だけ行ってよい
9. WEB検索後も解けなければ user report を作って停止する

focused test expectations:
- 既存:
  - `test_blank_company_intro_generation_prompt_locks_first_section_to_current_business`
- add new focused test:
  - nonblank company intro prompt でも
    - current-business-first line が prompt に入る
    - history を背景に回す line が入る
    - explanatory generic contract を壊さない
  のいずれかを固定する
- keep test:
  - `SECTION_SHADOW` company intro omission keep を壊さない

recommended test commands:
- focused:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "blank_company_intro_generation_prompt_locks_first_section_to_current_business or company_intro_generation_prompt_replaces_generic_hints_with_backend_brief or generation_prompt_slims_company_intro_section_shadow_block or longform_explanatory_structure_rules" -q`
- full owner suite:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
- shared check:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`

focused live validation after tests:
- target:
  - V3 company intro guard
- guards:
  - V1 latest adaptive explanatory baseline rerun
  - G1 non-target branding guard
- judge points:
  - V3 で first heading / first section が current business 起点に戻るか
  - title が `歴史を土台に` 方向へ寄らないか
  - V1 explanatory の partial gain を落としていないか
  - G1 non-target regression がないか

success condition:
- focused tests pass
- full simple-note pass
- quality-guard pass
- V3 company intro で current-business-first read が visible に戻る
- V1 explanatory partial gain を維持する
- G1 non-target regression がない

needs-more-work condition:
- V3 は改善するが still main candidate に足りない
- V1 explanatory gain と V3 company intro keep が再び trade-off になる
- owner は `prompt_builder.py` のままでよいが wording boundary をもう一段絞る必要がある

stop conditions:
- `prompt_builder.py` だけでは解けず、`pipeline.py` を触りたくなった
- nonblank company intro intent の判定が local evidence だけでは決まらない
- blank / nonblank / explanatory の 3つを同時に広く触りたくなった
- local self-fix + 1回のWEB検索後も blocker が解消しない

最終報告項目:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. 実装した narrow hypothesis
4. `nonblank company intro intent` をどう判定したか
5. touched files
6. 追加または更新した test
7. 実行したコマンド
8. test / check 結果
9. V3 / V1 / G1 focused validation の visible summary
10. WEB検索を使ったかどうか
11. 次が source-of-truth update か、さらに same-owner triage / implementation か
12. production code / tests 以外の AGENTS / WORKLOG / current package docs を更新していないこと
```
