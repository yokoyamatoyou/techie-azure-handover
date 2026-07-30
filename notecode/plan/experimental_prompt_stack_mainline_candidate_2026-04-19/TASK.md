# experimental_prompt_stack_mainline_candidate_2026-04-19 TASK

## Global Rules

- current mainline path
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  を壊さない
- `experimental_prompt_stack` の名前を維持する
- broad rewrite に広げない
- prompt accretion を増やしすぎない
- source safety を弱めない
- rigid heading skeleton へ戻さない
- editor を全文 rewrite に戻さない
- `body_generation_experiment` を再び strip しない
- 各 slice 完了後に必ず self-test を行う
- self-test fail 時は slice 内で最大 3 回まで自己修正する
- 同一 slice で 3 回失敗したら停止して user report
- context が増えすぎたら clean boundary で停止し、PROGRESS と EXECUTION_PROMPT を次ウインドウ用に更新する

## Promotion Gate

- 以下を満たしたときだけ mainline 候補昇格を許可する
  - experiment propagation が end-to-end で保たれる
  - targeted tests が pass
  - success condition が Codex / user から視認できる
  - historical compare で current baseline より改善根拠を説明できる
  - default 昇格で shared checks を壊さない

## Slice Map

### Slice 01 Success Visibility

- Objective:
  - success condition を Codex / user から読める surface に出す
- Candidate scope:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - compare / reporting helper
  - related tests
- Required output:
  - `audit_result`
  - experiment summary
  - success / fail reason が artifact から追えること
- Exit:
  - targeted tests pass
  - visibility surface がローカル artifact または result payload で確認できる

### Slice 02 Historical Compare

- Objective:
  - current proposal を past baseline と比較できる narrow compare path を作る
- Candidate scope:
  - compare helper
  - logs reader
  - minimal tests
- Required compare targets:
  - `latest_generation_quality_report.json`
  - `ad_hoc_quality_compare/.../summary.json`
  - `direct_gpt54_prompt_only_same_source_2026-04-03.json`
  - `prompt_only_probe_2026-04-03_same_source.json`
- Exit:
  - compare output が再現可能
  - old prompt-only failure が input-contract failure か content failure か区別できる

### Slice 03 Promotion Prep

- Objective:
  - mainline 昇格前提の switch / gate / tests を最小差分で準備する
- Candidate scope:
  - current mainline runner
  - UI matrix / execution path
  - targeted tests
- Constraint:
  - default flip は promotion gate pass 後だけ
- Exit:
  - switch condition が明文化される
  - targeted tests pass

## Entry Gate

- this package docs を読んでいる
- current implementation files を読んでいる
- current passed tests を baseline として把握している

## Pass Gate

- touched slice に対する self-test が pass
- previously passed baseline tests を壊していない
- `experimental_prompt_stack` の core invariants
  - source safety
  - flow/article contract
  - suffix edit
  - audit
  を維持している

## Stop Gate

- 同一 slice で 3 回 self-repair しても fail
- shared path の breakage が広がる
- unrelated subsystem まで owner scope が拡大する
- context 増大で handoff を書いた方が安全
