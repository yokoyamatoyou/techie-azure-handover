# separate window instruction first request sentence final monotony 2026-04-17

```text
deepresearch 反映後の最初の依頼です。

次に別の `作業ウインドウ` へ渡すための md を 1 本作成してください。
この指示ウインドウ自身は実装せず、prompt 作成だけを担当してください。

## 依頼内容

- priority revision に従い、
  `sentence-final pattern monotony cap + single repair`
  を next main candidate として扱う
- ただし初手では production code を触らない
- まず `planning / triage 用の作業ウインドウ prompt` を docs に作成する

## 参照必須

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
7. `C:\tetie\WORKLOG.md`
8. `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
9. `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`

## 作ってほしいもの

- docs 配下に、
  `sentence-final monotony cap + single repair`
  line 専用の `作業ウインドウ向け execution prompt md`
  を 1 本作る

## その prompt に必ず入れること

- 参照ルールファイル
- 今回の実施範囲
- current keep-state
- deepresearch reflection を踏まえた priority shift
- `reference realization policy` は今回 main line ではないこと
- production code は初手で変更しないこと
- 初手の目的は
  - narrow owner candidate の特定
  - detector / telemetry / repair scope の切り分け
  - docs-first の planning / triage
  であること
- do not
  - fixed routing table
  - planning default
  - formatter-only polish
  - hidden reviser accretion
  - giant rewrite
  - current source-of-truth update
- touched files の許可範囲
  - 初手は docs のみ
- stop conditions
- 最終報告で必ず示すこと

## 重要

- 今回あなたが作るのは `作業ウインドウ向け prompt` であり、
  実装 md ではない
- prompt の対象は
  `sentence-final monotony cap + single repair`
  の planning / triage である
- 日本語ブログ runtime を変更しない前提で作る

## 出力

- 作成した md の絶対パス
- その md を次にどのウインドウへ貼るか
- 1〜2文の短い使い方
```
