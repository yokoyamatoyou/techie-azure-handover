# current_mainline_pre_generation_ux_preflight_2026-04-27

## Objective

Launch 前 UX blocker のうち、Phase 0 baseline hygiene と Phase 1 UI separation だけを実施した。

- `不足を確認` / `内容を確認` は生成を開始しない。
- 実生成は明示ボタン `この内容で生成を開始` だけで開始する。
- journey 未確認または stale signature のまま生成ボタン経路に入っても、自動確認せず停止する。
- URL source retention helper は変更しない。
- Phase 2 source preflight と Phase 3 naturalness / repair trigger は未実装。

## References

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\`
- `C:\tetie\WORKLOG.md`

## Scope

### Phase 0

`prompt_builder.py` は failed `company_introduction naturalness prompt surface` の after hash `4F29076F...` 状態だった。Git repo / exact backup は見つからなかったため、accepted baseline hash `82DC095B...` への完全復元ではなく、WORKLOG の failed patch 記述に沿って prompt surface 追加分を手動 rollback した。

Accepted launch-blocker の `company_intro_source_contract.py` / `company_intro_source_contract_guard.py` は保持した。

### Phase 1

UI owner 範囲だけ実装した。

- `journey_confirm_button.on(...)` から `run_generation()` 呼び出しを外した。
- journey mode でも明示生成ボタンを表示し、`この内容で生成を開始` とした。
- `run_generation()` は未確認 / stale signature を自動 confirm しない。
- 未確認時は confirmation required view で停止し、`Generation started` へ到達しない。
- `未確認` バッジと `内容を確認` に寄せ、強い警告風の文言を避けた。

## Non-Goals

- Phase 2 source preflight は実装しない。
- Phase 3 naturalness / repair trigger は実装しない。
- repair 回数、quality threshold、fingerprint threshold、source grounding threshold、target chars、length mode は変更しない。
- prompt_builder へ禁止語 / few-shot / 追加 prompt を積み増さない。
- persona registry / central source contract registry は作らない。

## AGENTS Update

AGENTS 更新は不要。今回の package は current source-of-truth の置換ではなく、launch blocker の separate narrow package であり、既存の owner scope / current mainline rules で扱える。
