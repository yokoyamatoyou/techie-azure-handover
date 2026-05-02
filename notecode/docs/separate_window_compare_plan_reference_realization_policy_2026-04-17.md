# separate window compare plan reference realization policy 2026-04-17

## Execution Note

- 参照ルールファイル:
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\WORKLOG.md`
  - `C:\tetie\notecode\docs\separate_window_test_algorithm_by_ui_direction_2026-04-16.md`
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_direction_test_algorithm_2026-04-16.md`
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_pure_output_guard_triage_2026-04-16.md`
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_mock_path_alignment_2026-04-16.md`
- 今回の実施範囲:
  - compare / inspection / report のみ
  - 日本語ブログ runtime / production path は変更しない
  - current source-of-truth / AGENTS / WORKLOG / current package docs は更新しない
- current keep-state:
  - route default は `grounded generic`
  - `planning` は `opt-in only`
  - blank company intro の best current line は `prompt_builder.py` の `current-business-first keep line`
- compare 対象の experimental line:
  - `natural_blog_core.py` に入った section-level `reference realization policy`
  - `trust_intro` と `explain_analysis` にだけ narrow に入っている
  - current first slice では `daily_story` には policy を足していない
- compare の前提判断:
  - `pure output guard` failure は stale mock / stale expectation line と分離して扱う
  - compare の primary judge は visible text と human rubric であり、mock path の pass/fail を勝敗条件にしない
  - `latest_generation_*` は keep-state symptom の確認先であり、この compare の baseline case には使わない
- current provisional verdict:
  - `NO_GO_BEFORE_COMPARE`
  - まだ production owner を開かない
  - まず fixed case compare で、visible gain が `reference realization policy` に閉じて説明できるか確認する

## Compare Setup

### Lane Definition

- lane A:
  - current keep-state baseline
  - production path unchanged
  - `grounded generic default` のまま
- lane B:
  - separate experimental line
  - `natural_blog_core.py` の section-level `reference realization policy` を含む状態
- lane C:
  - optional fallback reference only
  - `prompt-only floor`
  - winner 判定には使わず、B が baseline より悪いときの下限確認に留める

### Fixed Rules

- same case / same source / same role / same config で比較する
- source や role label を compare 途中で差し替えない
- route default / formatter / input_contract / output_guard threshold を compare 中に変えない
- `article-type fixed routing table` を追加しない
- compare は 1 case あたり `3 repeats` を基本にする
- 判定は `single best run` ではなく `median` と `2/3 repeat consistency` を見る

### Compare Output Pack

- 各 repeat で保存するもの:
  - full text
  - short note
    - company name repetition
    - pronoun / omission distribution
    - subject reintroduction timing
    - abstraction feel
    - paragraph breath
    - article integrity
- supporting metrics:
  - `explicit_subject_ratio`
  - `ending_bucket_max_run`
  - `abstract_term_density`
  - `paragraph_length_cv`
  - company-name / proper-noun repeat count
- metrics は補助であり、visible improvement の代替にしない

## Compare Case List

| role | article type | fixed case | use | note |
|---|---|---|---|---|
| target 1 | `company_introduction` | `ui-short-branding-company-grounded` | main target | `trust_intro` で会社名反復と current-business-first の自然さを見る |
| target 2 | `branding` | `ui-short-branding-trust` | main target | `trust_intro` が value / trust line でも brochure 化を減らせるかを見る |
| target 3 | `explanatory_article` | `bl-explanatory-misread-metric` | main target | `explain_analysis` の `no_first_person` と subject control が効くかを見る |
| guard | `daily_story` | `bl-daily-learning-log-grounded` | regression guard | current first slice の対象外なので、policy bleed-through や unintended flattening がないかだけ見る |

## Human Check Rubric

各項目を `0 / 1 / 2` で採点する。  
`0 = visible problem`, `1 = mixed`, `2 = clear pass`。

| item | check | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | 固有名詞前景反復 | 段落頭や近接文で会社名 / `株式会社` が連打される | lead 後に少し残る | 初出以降は自然に落ちる |
| 2 | `私たち / 当社 / 省略` 配分 | どれかに偏りすぎる / 不自然 | 一部ぎこちない | 流れに応じて自然に切り替わる |
| 3 | 主語再導入 timing | ほぼ毎文で主語を言い直す | section shift 以外でも時々戻る | 話題転換や結びでだけ軽く戻る |
| 4 | AI 的抽象まとめ抑制 | `価値 / 重要 / 支援 / 課題` の抽象文で埋まる | 抽象文が散発する | 具体的な事実や判断が前に出る |
| 5 | 段落の呼吸 | 段落長が平坦 / 一文段落の単調反復 | 少し平坦 | 強弱があり読み進めやすい |
| 6 | article integrity | genre 固有の読み味を壊す | 一部ずれる | genre に合う |

### Article Integrity Rule

- `company_introduction` / `branding`
  - company intro は `現在の事業 / 現在の役割 / 現在の価値` が先に立つこと
  - history は後段で短く使うこと
- `explanatory_article`
  - 不必要な一人称を出さない
  - corporate narrator に寄せすぎない
- `daily_story`
  - 反省や気づきの個人線を消さない
  - corporate / explanatory の硬さへ寄らない

## Judgment Rule

### Go

- production owner を開いてよいのは、以下をすべて満たしたときだけ
- `company_introduction` と `branding` の median rubric が lane A より `+2` 以上
- 上記 2 case で `2/3 repeats` 以上、会社名反復と主語言い直しの両方が目視で改善
- `explanatory_article` が lane A 以上で、かつ不必要な一人称追加がない
- `daily_story` は guard case として lane A より悪化しない
- gain の説明が `reference realization policy` に閉じており、route default や formatter change を持ち込まなくてよい
- judge memo が「metrics が良い」ではなく、本文中の具体箇所で改善を説明できる

### No-Go

- 以下のいずれかに当てはまれば production owner は開かない
- `company_introduction` か `branding` で `株式会社` / 会社名の前景反復が lane A と同等以上に残る
- `explanatory_article` で一人称抑制の代わりに硬直した説明カード調が増える
- `daily_story` が dry / corporate / explanatory に寄る
- gain が 1 run の当たりに依存し、`2/3 repeats` を越えない
- compare を進めるために `article-type fixed rule` や prompt accretion が欲しくなる
- mock path / pure output guard の pass を visible improvement の代わりに使いたくなる

## Next Owner Gate

- compare 前:
  - `do not open production owner`
- compare 後に `GO` なら:
  - first production owner candidate は `C:\tetie\notecode\note\natural_blog_core.py`
  - ただし touched owner は 1 file に閉じる
- compare 後に `NO_GO` なら:
  - `reference realization policy` line は separate evidence として止める
  - `prompt-only winner` や fixed routing へ逃げず、management window に差し戻す

## Final Pre-Compare Judgment

- compare case list:
  - `ui-short-branding-company-grounded`
  - `ui-short-branding-trust`
  - `bl-explanatory-misread-metric`
  - `bl-daily-learning-log-grounded`
- rubric:
  - 6 items x `0 / 1 / 2`
- go / no-go:
  - company / branding の visible gain が中心
  - explanatory は no-first-person guard
  - daily は regression guard
- next production owner を今すぐ開くべきか:
  - `no`
  - compare evidence が揃うまで開かない
