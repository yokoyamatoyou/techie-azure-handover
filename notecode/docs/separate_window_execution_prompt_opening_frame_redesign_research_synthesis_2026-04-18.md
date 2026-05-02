# separate window execution prompt opening frame redesign research synthesis 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\management_stop_report_after_failed_pipeline_current_first_triage_2026-04-18.md
- C:\tetie\notecode\docs\parked_package_prompt_naturalness_recovery_2026-04-18.md
- C:\tetie\notecode\docs\management_prompt_keep_naturalness_recovery_parked_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt

今回の依頼種別:
- docs-only redesign synthesis prompt
- `OPENING_FRAME_REDESIGN_RESEARCH_SYNTHESIS`
- implementation prompt ではない
- current package reopen prompt ではない

今回の実施範囲:
- external deepresearch 3本の共通点と差分を current stop boundary に照合する
- `naturalness_recovery_2026-04-07` package を reopen せず、
  研究上どの redesign line が妥当かを docs-only で整理する
- production code / tests / AGENTS / WORKLOG は編集しない
- current source-of-truth を broad rewrite しない

current fixed judgment:
- current package:
  - `naturalness_recovery_2026-04-07`
- package state:
  - `parked / not fixed`
- current success path:
  - keep
- failed / rollback 済み / unchanged retry 禁止:
  - `prompt_builder.py` simplification-first wording line
  - `pipeline.py` current-first source ordering / hint triage
  - `pipeline.py` core_message current-first hint
- next owner:
  - not fixed
- next narrow hypothesis:
  - not fixed

why this window exists:
- research 側では
  - `prompt accretion を止める`
  - `title / lead / first heading / first section の役割分離`
  - `current-business-first を opening invariant に寄せる`
  - `最小 structural signal / deterministic flag`
  という方向がかなり強く収束している
- ただし current package は parked なので、
  そのまま実装へ走ると source-of-truth と衝突する
- よって今回は
  - `research が何を支持しているか`
  - `それを current package の外でどう切り出すべきか`
  を docs-only で固定する

this window role:
- research understanding の確認
- local failure と external research の接続
- future reopen を current package の延長でやるべきか、
  新しい redesign line として切るべきかの判断
- 必要なら next line 用の prompt を 1 本だけ作る
- production 実装はしない

core question:
- research 3本の共通結論を、
  `current parked package` と矛盾せずに次の line へ落とすなら、
  何を `new package / new redesign line` の最小問題設定にするべきか

required reading focus:
1. research 共通点
  - prompt accretion continuation を否定しているか
  - opening frame ownership 問題として見ているか
  - title / lead / H2_1 / section_1 の役割分離を支持しているか
  - history-first を source salience と rhetorical priority のズレとして捉えているか
2. local stop boundary
  - `prompt_builder.py` と `pipeline.py` の owner-local retry が 3 回失敗済みであること
  - current package は parked であること
3. future line boundary
  - current package reopen ではなく、
    separate redesign line として切る必要があるか

what to decide:
1. research 3本の共通結論
2. research 3本の差分
3. current parked judgment と矛盾しない読み方
4. next line を current package reopen ではなく
   new package / new redesign line に分けるべきか
5. 分けるなら最小テーマ名
6. first owner candidate をどこに置くべきか
7. first line が implementation ではなく triage / design であるべきか

strong bias:
- current package を reopen しない
- `prompt_builder.py` / `pipeline.py` の同系統 retry prompt を作らない
- production code 実装に進まない
- giant rewrite proposal にしない
- skeleton / planning default reopen に戻らない
- broad source-of-truth rewrite にしない

preferred output shape:
- docs-only note 1 本
- 必要なら次の prompt 1 本まで
- 結論は次のどれか 1 つに固定する
  - `KEEP_PARKED_AND_DO_NOT_OPEN_NEW_LINE_YET`
  - `START_NEW_PACKAGE_OPENING_FRAME_REDESIGN_DOCS_FIRST`
  - `START_NEW_PACKAGE_MINIMAL_CONTROL_LAYER_DOCS_FIRST`

decision guidance:
- research の共通点が
  - `role separation`
  - `opening owner`
  - `minimal structural control`
  に収束しており、
  current package の failed hypotheses と owner-local に重ならないなら
  new package / new redesign line を docs-first で切るのは合法
- 逆に
  current package の failed line とほぼ同じ問いに戻るだけなら
  parked 維持で止める

if you conclude a new line should start:
- implementation prompt ではなく
  `docs-first / design-triage first` の prompt を 1 本だけ作る
- prompt は
  - new package の objective
  - non-goals
  - do-not-retry boundary
  - expected first owner candidate
  - why this is not prompt accretion continuation
  を含める
- production code edit を依頼しない

recommended output files:
- synthesis note:
  - C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md
- if new line is justified:
  - C:\tetie\notecode\docs\separate_window_execution_prompt_opening_frame_redesign_docs_first_2026-04-18.md

WEB search policy:
- 原則不要
- local research files と local source-of-truth の読取りだけで足りるなら使わない
- 足りない場合のみ 1 回だけ許可
- 使った場合は query と採用理由を短く示す

stop conditions:
- research 3本の共通点を 1 line に収束できない
- current parked judgment と矛盾せずに next line を定義できない
- implementation を始めたくなった
- current package reopen prompt を作りたくなった

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. research 3本の共通結論
4. research 3本の主な差分
5. current parked judgment と矛盾しない読み方
6. conclusion
7. new line を切るならその最小テーマ名
8. next prompt を作ったかどうか
9. WEB検索を使ったかどうか
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
