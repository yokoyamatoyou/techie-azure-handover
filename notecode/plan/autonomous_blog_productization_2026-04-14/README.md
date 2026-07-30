# autonomous_blog_productization_2026-04-14 README

この package は current package の continuation ではない。  
`C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\` と `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\` の keep-state を壊さず、別ウインドウで `minimal UI + source-less web-grounded generation + autonomous completion loop` を productization する separate execution package として扱う。

## Objective

- current success path を維持したまま、別ウインドウで phase を自律完走できる execution package を固定する
- source 無しでも `daily_story / explanatory_article / industry_analysis` を対象に、WEB検索で current な一次情報または一次情報に近い情報を集めて source-backed generation へ変換する
- `branding/company_introduction` と `announcement` は source-backed を維持し、unsafe な source-less auto generation へ広げない
- UI は first view の文字数と選択肢を極小化し、`何を出すか / 何を書くか / 何から書くか` の 3 decision と 1 行入力で動けるようにする
- phase ごとに owner-local tests と shared checks を通し、同一仮説の失敗は 3 回まで自己修正し、無理なら停止して user report する
- autonomous 完走後は `company_introduction / explanatory_article / announcement` の 3 blog を生成し、Codex 視認評価まで実施する

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\README.md`
4. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\TASK.md`
5. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\PROGRESS.md`
6. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\ROLLBACK.md`
7. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
9. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
10. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
11. `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\README.md`
12. `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\PROGRESS.md`
13. `C:\tetie\notecode\ALGORITHM.md`
14. `C:\tetie\WORKLOG.md`

## Source Of Truth Boundary

- current keep-state source-of-truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- completed distilled-brief reference:
  - `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\`
- separate execution package source-of-truth:
  - `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\`
- runtime mainline baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Fixed Product Direction

- first-screen decisions:
  - `どこに出すか`
  - `何を書くか`
  - `何から書くか`
- first-screen free text:
  - 1 行だけ
- source modes:
  - `資料`
  - `テーマ(Web)`
  - `続編`
- source-less WEB mode allowed:
  - `daily_story`
  - `explanatory_article`
  - `industry_analysis`
- source-less WEB mode not allowed:
  - `branding/company_introduction`
  - `announcement`
  - `case_study`
  - `comparative_review`
- source-less WEB mode must become source-backed before generation:
  - query
  - source URL
  - publisher
  - exact date
  - extracted fact / excerpt

## Interface Principles

### Nielsen 10

- visibility of system status:
  - status は短い 1 行と progress state のみ
- match between system and the real world:
  - label は `出す / 書く / 材料` の短語へ寄せる
- user control and freedom:
  - first screen から戻れる
  - 詳細設定は畳む
- consistency and standards:
  - article type / source mode 名称を screen 間で固定する
- error prevention:
  - `announcement` は date / target / change が不足したら生成しない
  - source-less WEB mode は allowed categories 以外で拒否する
- recognition rather than recall:
  - 過去入力や業界 hint を UI で再利用し、記憶依存を減らす
- flexibility and efficiency of use:
  - 1 行入力で開始し、詳細は必要時だけ追加する
- aesthetic and minimalist design:
  - first view は 3 selectors + 1 text input + 1 CTA を基準にする
- help users recognize, diagnose, and recover from errors:
  - error は短い理由 + 次の 1 アクションだけ示す
- help and documentation:
  - 長文ヘルプではなく inline micro-copy を採用する

### Hick's Law

- first view の primary decisions は 3 groups に固定する
- 各 group の visible options は 3〜5 に抑える
- advanced options は second layer へ退避する
- title / tone / CTA / SEO のような secondary choices を first view に置かない

## Success Criteria

- phase 実行は `1 phase = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- same phase failed hypothesis の unchanged retry は 3 回まで
- phase pass 後は user 待ちせず次 phase へ自律継続する
- source-less WEB mode が allowed categories で source-backed digest を作れる
- prompt / module / telemetry の accretion を最小限に保てる
- final evaluation で `company_introduction / explanatory_article / announcement` の 3 category を生成し、Codex 視認評価を残せる

## Non-Goals

- planner / generator core を初手で全面置換すること
- `branding/company_introduction` や `announcement` を source-less WEB mode に広げること
- prompt-only winner の断定から入ること
- fixed routing table を article type ごとに追加すること
- first screen に title / tone / CTA / SEO / persona を並べること
- source trace が残らない WEB summary generation を通すこと
- UI refresh を理由に route / repair / formatter を同時多発で触ること
- module accretion を前提に search / UI / logging を別々に肥大化させること
