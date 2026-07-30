# company_intro_polish_spinout_2026-04-13 TASK

この package は blank `branding/company_introduction` の separate line だけを扱う。  
current package source-of-truth は更新しない。

## Global Rules

- current package keep-state を壊さない
- current package docs / AGENTS / WORKLOG は更新しない
- blank `branding/company_introduction` 以外へ広げない
- primary owner は `input_contract.py` と `prompt_builder.py` の 2 本まで
- `output_formatter.py` を main owner にしない
- `natural_blog_core.py` を reopen しない
- `pipeline.py` の route default を変えない
- UI を触らない
- labeled block 露出を増やさない
- long persona を足さない
- prompt accretion 禁止
- article-type fixed routing table 禁止
- same hypothesis unchanged retry 禁止
- 3 attempts で止める

## Entry Gate

- keep baseline / prompt-only floor / skeleton signal / rollback lines が separate package docs に固定されている
- paired hypothesis が `input_contract.py + prompt_builder.py` に閉じている
- implementation target が blank `branding/company_introduction` のみである

## Pass Gate

- owner-local tests pass
- shared checks pass
- rerun artifact が keep baseline と prompt-only floor の両方に compare されている
- must-cover / grounding / anchor を落とさずに自然さ改善を示せる
- first heading / lead が current-business-first を維持する
- public web compare pattern に寄る

## Stop Gate

- 3 attempts で keep baseline と prompt-only floor の両方を超えられない
- must-cover / grounding / anchor を落としてしか自然さ改善できない
- paired owner set を超える diff が必要
- same hypothesis のまま retry するしかなくなる

## Phase Map

### Phase S0 Docs Lock

- Objective:
  - spin-out line の objective / baseline / rollback boundary / owner set を current package と切り分けて固定する
- Owner:
  - `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\`
- Exit:
  - README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT が揃っている

### Phase S1 Input Distillation Guard

- Objective:
  - blank company intro で history-led main focus を current-business-first distillation に戻す
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- Hypothesis:
  - blank company intro 専用に `topic_statement / core_message / focus_bundle / must_cover` の history drift を止めれば、current-business-first keep line を崩さず writer-facing handoff を安定化できる
- Exit:
  - history が background 扱いに留まり、main focus と must-cover 先頭が current-business-first になる

### Phase S2 Writer Handoff Polish

- Objective:
  - distilled summary を label 露出なしで短く自然に writer brief へ渡す
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- Hypothesis:
  - blank company intro の writer brief が current-business-first / background-later / repetition-avoidance を短く受け取れば、brochure/card feel と AI 感を下げられる
- Exit:
  - writer brief が current-business-first を維持しつつ、history を background として短く扱う

### Phase S3 Compare And Verdict

- Objective:
  - separate line として keep / rollback / stop を決める
- Owner:
  - paired owner artifact only
- Exit:
  - rerun artifact と compare report が残り、verdict が明示される

## Required Tests

### Owner-Local

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase01_contract.py -k "company_intro or pr12 or pr13" -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "company_intro or blank_company_intro" -q
```

### Shared Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
```

### Optional Boundary Check

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st08h or st07g6ad1" -q
```
