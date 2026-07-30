# current_mainline_fail_closed_ux_policy_2026-04-25 README

## Objective

- current mainline の final quality guard は緩めず、本文生成済みの fail-closed を SaaS UX として分類する。
- 「何も返らない」体験を避けるため、公開品質 / 確認が必要なドラフト / 入力修正が必要な停止を分ける。
- threshold 緩和、prompt 追加、repair 追加、warning-only demote 拡大では解決しない。

## Source Evidence

- `C:\tetie\notecode\plan\current_mainline_article_type_ui_quality_validation_2026-04-25\PROGRESS.md`
- `C:\tetie\notecode\logs\current_mainline_article_type_ui_quality_validation_20260425-223000\`
- `C:\tetie\notecode\plan\current_mainline_fingerprint_policy_resolution_2026-04-25\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_source_grounding_metric_correction_2026-04-25\PROGRESS.md`
- `C:\tetie\WORKLOG.md`

## UX Taxonomy

- `publishable_success`
  - 通常成功。本文を公開候補として表示する。
- `review_required_draft`
  - 本文はあるが、資料反映、説明具体性、文体の単調さなどに確認が必要。
  - 危険な内部語漏れ、source外 claim、入力不整合、route mismatch はない。
  - UI は本文を表示するが、「確認が必要なドラフト」として警告付きで扱う。
- `input_required_block`
  - 本文空、source不足、route mismatch、source外 claim、内部語漏れ、形式破損、明確な policy / source contract failure。
  - 本文は表示しない。ユーザーに追加資料や入力修正を具体的に返す。

## Artifact Classification

| Case | Runtime | UX classification | Reason |
| --- | --- | --- | --- |
| `company_introduction_kyoto_4urls` | `SYS_QUALITY_WARNINGS_UNRESOLVED`, body exists | `review_required_draft` | rich source, no leakage/outside claim, source reflection/style warning remains |
| `bl-announcement-spec-change` | `SYS_QUALITY_WARNINGS_UNRESOLVED`, body exists | `review_required_draft` | route match, must-cover complete, no leakage/outside claim |
| `bl-daily-learning-log-grounded` attempt 2 | `SYS_QUALITY_WARNINGS_UNRESOLVED`, body exists | `review_required_draft` with synthetic caveat | non-legal warning shape; UX evidence only |
| `bl-daily-learning-log-grounded` attempt 1 | `SYS_QUALITY_WARNINGS_UNRESOLVED`, body exists | `input_required_block` | legal/guarantee warning appears |
| `bl-branding-values-stance` | `SYS_PIPELINE_FAILURE`, body empty | `input_required_block` | route mismatch / empty body |

## User-Facing Copy

- Draft banner: `確認が必要なドラフトです`
- Draft explanation: `本文は作成できましたが、資料の反映や説明の具体性に確認したい点があります。公開前に資料と照らし合わせて確認してください。`
- Copy/save warning: `コピーや保存はできますが、公開前の確認が必要です。`
- Input block: `本文を表示できませんでした。記事タイプや資料が合っているか確認してください。`
- Source/action hint: `事業内容、対象範囲、進め方が分かる資料を追加して、もう一度生成してください。`

## Non-Goals

- final guard を消すこと。
- fail-closed を success 扱いにすること。
- `fingerprint-only` 以外へ warning-only demote を広げること。
- source不足、source外 claim、内部語漏れ、route mismatch の本文を表示すること。
- UI に `source_grounding` / `fingerprint` / `SYS_*` / `must_cover` / `contract_alignment` などの内部語を出すこと。
