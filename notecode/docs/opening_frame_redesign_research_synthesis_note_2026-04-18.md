# opening frame redesign research synthesis note 2026-04-18

## Position

- docs-only note for `OPENING_FRAME_REDESIGN_RESEARCH_SYNTHESIS`
- implementation prompt ではない
- `naturalness_recovery_2026-04-07` package reopen note ではない

## Read Rule Files

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\management_stop_report_after_failed_pipeline_current_first_triage_2026-04-18.md`
- `C:\tetie\notecode\docs\parked_package_prompt_naturalness_recovery_2026-04-18.md`
- `C:\tetie\notecode\docs\management_prompt_keep_naturalness_recovery_parked_2026-04-18.md`
- `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md`
- `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md`
- `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt`

## Scope

- external research 3 本の共通点と差分を current parked boundary に照合する
- current package を reopen せず、next line を separate redesign line として切る必要があるかだけを判断する
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## Research 3本の共通結論

1. 主問題は wording 追加ではなく `opening frame ownership` である。
   - `title / lead / first heading / first section` を同じ面で曖昧に兼務させると drift が起きやすい、という読みで一致している。
2. `company introduction` の opener は `current-business-first` を invariant として持つべきで、history は背景・後段へ送るべきだと見ている。
3. `prompt accretion continuation` は支持していない。
   - 3 本とも「rule を足して押し切る」より「責務を減らす / 分ける / 優先順位を固定する」を支持している。
4. 次の制御は broad rewrite ではなく `minimal structural signal` または `deterministic opening invariant` であるべきだと見ている。
5. `planning / skeleton default reopen` や giant rewrite は支持していない。

## Research 3本の主な差分

- research A:
  - `source ordering` / `current_business-history-other` のような upstream control を強めに推している
  - `prompt_builder` simplification と最小 upstream hint の併用を提案している
- research B:
  - `prompt_builder` 側の frame card / variable 化 / deterministic flag を強めに推している
  - prompt management と role separation の説明が厚い
- research C:
  - `prompt_builder` simplification pass を最短手と見ている
  - 最小 guard と editorial role 分離を中心にしている

差分の要点:

- 共通しているのは `opening owner を分けるべき` という問題設定
- まだ一致していないのは `最小 control layer をどこへ置くか`
  - `prompt_builder.py`
  - `newalgorithm_pipeline/pipeline.py` 周辺
  - tiny guard / detector

## Current Parked Judgment と矛盾しない読み方

- current package が止めたのは
  - `prompt_builder.py` simplification-first wording line
  - `pipeline.py` current-first source ordering / hint triage
  という single-owner retry line である
- research 3 本が本当に支持しているのは、その retry を unchanged で再開することではない
- むしろ research は
  - opener ownership
  - role separation
  - minimal control placement
  という cross-owner design question が残っている、と読める
- したがって current package の `parked / not fixed` judgment は正しい
  - current package の中で legal な `1 owner / 1 hypothesis` が確定していない
  - same failed line を current package 内で reopen すると do-not-retry と衝突する
- external research は current package reopen の根拠ではなく、
  `current package の外に separate redesign line を切る根拠` として読むのが最も整合的である

## Conclusion

- fixed conclusion:
  - `START_NEW_PACKAGE_OPENING_FRAME_REDESIGN_DOCS_FIRST`

理由:

- research の共通点は `minimal_control_layer の実装位置` より
  `opening frame ownership を再設計する必要` に強く収束している
- `minimal_control_layer` はその新 line の設計論点の 1 つではあるが、theme 名としてはまだ早い
- よって new package / new redesign line の最小テーマ名は `opening_frame_redesign` が妥当

## New Line の最小テーマ名

- `opening_frame_redesign`
- recommended future package path:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`

## First Owner Candidate

- first line は implementation ではなく `docs-first / design-triage first` にするべきである
- first docs owner candidate:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
- tentative first code owner candidate after docs:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` 周辺の最小 opening-frame control surface

補足:

- これは research 3 本の差分からの推論であり、current package reopen judgment ではない
- `prompt_builder.py` wording simplification の unchanged retry に戻す提案ではない
- `pipeline.py` current-first hint triage の unchanged retry に戻す提案でもない
- unresolved point が `opener selection / structural signal placement` だから、wording owner より upstream 側を暫定候補に置くほうが自然である

## Why First Line Should Stay Docs-First

- research 3 本は問題設定には収束しているが control placement にはまだ収束していない
- current package では `prompt_builder.py` と `pipeline.py` の narrow retry がどちらも exhausted している
- この状態で code へ直行すると
  - same failed line の rename retry
  - multiple owner reopen
  - prompt accretion continuation
  のいずれかへ滑りやすい
- したがって first line は
  - objective
  - non-goals
  - do-not-retry boundary
  - first owner candidate
  - evaluation boundary
  を docs-only で固定するほうが安全である

## Next Prompt

- created:
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_opening_frame_redesign_docs_first_2026-04-18.md`
- this prompt is docs-first only
- production code edit は依頼していない

## WEB Search

- not used
- local research files と local source-of-truth の読取りだけで足りた

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current package docs は更新していない
