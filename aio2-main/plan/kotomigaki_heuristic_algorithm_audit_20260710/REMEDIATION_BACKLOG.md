# Remediation Backlog

## 1. 運用規則

- この文書は監査結果から作った候補 backlog であり、実装を開始した記録ではない。
- 1 slice は 1 current owner とし、owner doc を更新してから着手する。
- `pass/fail/unverified/not-applicable/error` の evidence state と、UI/export が参照する canonical model を先に固定する。
- live URL、外部 API、Azure、dependency advisory scan は、その owner と許可を別途開く。

## 2. 実装順

| 順 | ID | 優先度 | bounded owner | 変更候補 | 依存 | 必須検証 | non-owner |
|---:|---|---|---|---|---|---|---|
| 1 | R-01 | P1 | **saved-workspace truth and action parity owner** | `analysis_run_service.py`, `saved_workspace.py`, CSV/MD/DOCX adapter。GET 無書込、unknown 保持、canonical action ids/order/count | なし。ローカル fixture で完結 | legacy bundle byte equality、competitor 保持、UI/CSV/MD/DOCX top IDs 一致、unknown round-trip | score、crawler、Schema、LLM、auth、法務 |
| 2 | R-02 | P1 | provider-readiness evidence owner | `aio_analyzer.py`, orchestrator。robots fetch/path/user-agent/header の4-state化 | evidence state contract | fetch error/non-200/path-specific/X-Robots fixtures | score/UI IA |
| 3 | R-03 | P1 | scoring-contract owner | `[0,100]` contract、industry adjustment、gap-based focus、version表示 | R-02 の state semantics | bounds/property test、low-AIO focus、legacy snapshot表示 | content extraction 全面改修 |
| 4 | R-04 | P1 | structured-data evidence owner | 単一 normalized JSON-LD graph parser と consumer adapter | evidence state contract | multi-block/array/@graph/nested/invalid contract suite | suggestion text redesign |
| 5 | R-05 | P1 | URL privacy owner | raw fetch URL と redacted persistent URL の分離、userinfo拒否 | persistence schema判断 | encoded/case/key fixtures、DB/log/exportにsecretなし | tenant/auth |
| 6 | R-06 | P1 | NiceGUI accessibility owner | landmarks/headings、input-error relation、live status、native history controls | R-01 の画面契約 | keyboard main journey、axe WCAG2.2 Critical/Serious 0、NVDA status | visual redesign、engine changes |
| 7 | R-07 | P1 | accessibility scanner packaging owner | dependency pin/self-check、HTML-only表示、WCAG2.2 profile/manual list | packaging owner | packaged clean install、`source=browser`、missing dependency state | NiceGUI IA |
| 8 | R-08 | P1 | grounded-rewrite owner | sentence→source evidence、unsupported number/name reject | R-04 normalized evidence が望ましい | invented fact fixtures、citation trace、fallback behavior | model/provider変更 |
| 9 | R-09 | P1 external | Azure/auth tenant owner | tenant schema/query/artifact/download、local profile分離 | deployment architecture | cross-tenant 403/404、SAS expiry、history/compare/export isolation | local analysis heuristics |
| 10 | R-10 | P2 | SEO evidence owner | 7加点を hard gate/graded/unverified へ分解、日本語 content metric | R-02/R-03/R-04 | noindex+high-content、bad canonical、日本語、broken link fixtures | UI IA |
| 11 | R-11 | P2 | page-experience owner | proxy LCP/CLS 数値を未測定+risk factorsへ変更 | evidence state contract | no source→no numeric CWV、field/lab metadata fixtures | external PSI API |
| 12 | R-12 | P2 | freshness/link owner | future date validation、timeout/broken/blocked 分離 | evidence state contract | 2099/date-role/timeouts fixtures | crawler全面変更 |
| 13 | R-13 | P2 | official-claims/docs owner | FAQ/llms/speakable/AI効果の文言・eligibility・基準日 | R-08 が望ましい | golden copy、official URL/date、保証表現 grep | engine score |
| 14 | R-14 | P2 | export hardening owner | CSV Unicode/control fixtures、`result_path`除外、DOCX metadata/semantics | R-01/R-05 | hostile cell suite、no absolute path、Word checker | report content再設計 |
| 15 | R-15 | P2 | scanner security owner | port allowlist、DNS cache/IP pin、per-hop check | R-07 | mock rebind/private redirect/port tests | Python safe_fetch |
| 16 | R-16 | P2 | vulnerability intelligence owner | DB `mode=ro/query_only`、checksum/version、range/prerelease coverage | fixed DB packaging | write attempt fail、complex range fixtures、quick_check | DB content更新 |
| 17 | R-17 | P2 | current-docs owner | actual saved tabs、robots owner、model/temperature、scanner stateをcurrent docsへ同期 | 各実装 owner 完了後 | docs links/strings validator | 新機能実装 |
| 18 | R-18 | unverified | live validation owner | current-run visual/keyboard/zoom/axe/console/export evidence | browser runtime復旧、R-01/R-06/R-07 | evidence pack with screenshots/logs | code change |
| 19 | R-19 | unverified | dependency assurance owner | lock/SBOM/advisory scan | 許可されたnetwork/DB | reproducible command、exceptions、date | package upgrade |

### 修正種別ごとの一覧

| 種別 | backlog IDs | 目的 |
|---|---|---|
| docs のみ | R-13, R-17 | 公式基準日、保証不可、current owner/renderer/model/scanner状態を同期 |
| UI文言・情報設計 | R-01, R-06, R-13 | primary/engineer分離、未確認、状態通知、同一action導線 |
| engine | R-02, R-03, R-04, R-08, R-10, R-11, R-12, R-16 | bot、score、Schema、grounding、SEO、page experience、freshness/link、vulnerability matching |
| security/privacy | R-05, R-09, R-15 | URL secret、tenant/auth/artifact、browser scanner SSRF |
| test | 全実装ownerに内包、横断contractはR-01/R-02/R-03/R-04 | characterization、snapshot semantic round-trip、security regression |
| live検証 | R-18, R-19 | current browser evidence、advisory/SBOM evidence |

### Cross-layer impact checklist

score、threshold、取得範囲、evidence state を変える R-02/R-03/R-04/R-10/R-11/R-12 は、同じ owner 内で次を評価し、影響がない場合も明記する。

- `ALGORITHM.md` の algorithm id/version と current説明
- characterization test と旧 snapshot compatibility
- snapshot schema/version/migration/no-write view
- UI、CSV、Markdown、DOCX のlabel・件数・priority
- empty/error/unverified/not-applicable の各状態

Security trade-off:

- port/host/byte/time を狭めれば SSRF と資源枯渇は下がるが、非標準portや遅い正当siteの未確認が増える。拒否を「問題あり」へ変換せず、policy-blocked/unverified と表示する。
- tenant/auth を導入するとlocal運用が複雑になる。local-only profileとshared deployment profileを分離し、local既定を黙って外部bindしない。
- URL redaction は再現URLを失うため、raw URLは実行中memoryだけに置き、保存側にはredacted URLと秘密でないfingerprintを残す。

## 3. 最初の slice: R-01 詳細

### Current owner

`saved-workspace truth and action parity owner`

### 問題

1. 保存結果を開く GET が legacy snapshot を再構築して書き戻す。
2. 再構築時に competitor 情報を渡さず、既存値を空へ変え得る。
3. absent/unknown/unverified が表示 adapter で「参考」へ変わる。
4. priority action が base export と UI workspace で別に追加・切断される。
5. UI/CSV/Markdown/DOCX の順番、件数、total が同一契約ではない。

### 変更面候補

- `core/application/analysis_run_service.py`
  - canonical `PriorityAction` shape と stable id
  - read-only legacy view adapter
  - explicit migration を別 command/service に隔離
  - state enum の round-trip
- `core/ui/saved_workspace.py`
  - canonical list の filter/view のみ
  - total と表示件数を同じ母集団から算出
  - unverified を理由・時刻付きで表示
- `core/application/csv_export_service.py`
- `core/application/markdown_report_service.py`
- `core/application/docx_report_service.py`
  - 同一 canonical action IDs/order を surface 固有 renderer へ渡す
- tests
  - `test_analysis_run_service.py`
  - `test_characterization_ui.py`
  - `test_csv_export_service.py`
  - `test_markdown_report_service.py`
  - `test_docx_report_service.py`

### Acceptance

- 保存 route GET の前後で DB row と snapshot artifact の hash が同じ。
- competitor を持つ legacy fixture を開いても competitor が保持される。
- `unverified` は UI/CSV/Markdown/DOCX のすべてで `unverified` 相当の日本語になり、`参考/pass` へ変換されない。
- canonical 10 actions の fixture で、全 surface の action id と priority 順が一致する。
- UI で一部だけを見せる場合も「全 N 件中 M 件」と全件導線が同じ canonical list に基づく。
- current 192-test targeted set と R-01 contract tests が pass。
- owner 完了時に `ALGORITHM.md` / `AGENTS.md` / `WORKLOG.md` の更新要否を判断する。

### Explicit non-owner

- SEO/AIO score formula
- robots/provider crawler behavior
- Schema parser
- LLM/model/prompt
- auth/tenant/Azure
- accessibility scanner packaging
- legal decision rules

## 4. P1 release gates

| release context | gate |
|---|---|
| 現行 local-only | R-01、R-02、R-03 の公開判定真偽を閉じる |
| 「WCAG 2.2 AA 検査」と表示 | R-06、R-07 と current-run browser evidence が必要 |
| AI文章を copy/publish | R-08 と source trace が必要 |
| Azure/共有公開 | R-05、R-09 を閉じるまで公開しない |
| CWV 実測値として表示 | field/lab source、device、timestamp、sample が必要 |

## 5. 今回開始しないこと

- 上記 backlog の code 実装
- live URL/API 分析
- dependency download / advisory network access
- Azure schema migration
- 既存 run の一括 migration
- current docs/WORKLOG の更新
