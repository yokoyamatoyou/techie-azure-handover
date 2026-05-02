# separate window owned media explanatory h4 2026-04-16

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\note\owned_media_experiment.py
- C:\tetie\notecode\evaluate_owned_media_experiment.py
- C:\tetie\notecode\note\tests\test_owned_media_experiment.py
- C:\tetie\notecode\note\tests\test_evaluate_owned_media_experiment.py
- C:\tetie\notecode\docs\separate_window_owned_media_explanatory_h1_2026-04-16.md

今回の実施範囲:
- separate-window experimental route の次フェーズ
- owner は `C:\tetie\notecode\note\owned_media_experiment.py` と owner-local tests のみ
- mainline は絶対に変更しない
- current success path は絶対に変更しない
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- AGENTS / WORKLOG / mainline package docs は触らない

開始時に必ず確認する artifact:
- compare baseline:
  - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-102618\report.md
  - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-103833\report.md
  - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-103834\report.md
- current keep after daily H4 diff:
  - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-110131\report.md
- explanatory target artifacts:
  - realistic:
    - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-102618\default_hybrid.json
    - case id: `explanatory_primary_source_handling`
  - fixed:
    - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-103833\default_hybrid.json
    - case id: `explanatory_article`
  - ambiguous:
    - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-103834\default_hybrid.json
    - case id: `explanatory_ambiguous_primary_source`

H1 review から引き継ぐ current judgment:
- H1 `late_evidence_starvation` は primary ではない
- `late_evidence_reservation` は source packet / blueprint / draft prompt に残っている
- explanatory 3条件の live spot でも、FAQ / 判断境界 / operational detail / next action は後半に残りうる
- したがって broad keep は `default_hybrid` のまま維持
- 次に切るなら H4 `expansion_flattening`

current keep state:
- broad keep は `default_hybrid`
- `daily_story + ambiguous` の H4 residual には narrow polish guard が入っている
- この keep diff を reopen しない
- article-type fixed routing table を追加しない
- prompt accretion / hidden reviser accretion をしない
- semantic split を default 化しない

今回の役割:
- あなたは `explanatory_article dense` の expansion/polish flattening reviewer / implementer です
- 目的は H4 `expansion_flattening` が本当に primary かを local evidence と web source で再確認し、
  owner-local な narrow diff がある場合のみ入れることです

今回の narrow hypothesis:
- `explanatory_article` の realistic dense 条件では、
  draft か expand 前半では FAQ / 例外 / 判断境界 / next action の差が存在する
  しかし expand または polish で、
  後半の reserved detail が「前半のまとめ直し」「教科書っぽい一般論」「段落長の均し」に寄って flatten される
- もしこの仮説が正しいなら、owner は `owned_media_experiment.py` の explanatory expand/polish path に閉じられる

candidate hypothesis:
- H4: expansion_flattening
- H2: source_sufficiency_mismatch
- H1: late_evidence_starvation (do not reopen unless decisive contradiction appears)

今回の優先順位:
1. 記事の破綻がないこと
2. 読みやすいこと
3. AIぽさ低減

絶対制約:
- mainline を触らない
- global route を変えない
- broad design change をしない
- semantic split default 化をしない
- explanatory 以外へ横展開しない
- `daily_story` の直近 keep diff を触らない
- H4 と H2 を同時に広く触らない
- H1 を evidence なしで reopen しない
- 1 hypothesis = 1 owner scope に閉じる
- apply_patch で編集する
- same hypothesis unchanged retry は 3 回まで

今回の do:
1. local evidence を優先して、explanatory 3条件の surface を読み直す
2. `late_evidence_reservation` が残っている前提で、
   - draft
   - expand prompt
   - expand 後本文
   - polish prompt
   - polish 後本文
   のどこで均しが強くなるかを切る
3. H4 が primary と言える場合のみ owner-local diff を入れる
4. H4 が primary でなければ実装せず observation だけを report する
5. web search を使い、一次ソースだけで次を補助観察する
   - explanatory / docs 系記事で重要情報を前に置くときの原則
   - FAQ / 例外 / 判断境界 / next action を後半へ置くとき、summary 化しすぎない置き方
   - polish 時に意味を落とさず paragraph breath を崩す方法
   - repeated abstract restatement を避けるために何を削るか

web search rule:
- 必ず web search を使う
- 優先するのは一次ソース:
  - 公式ヘルプ / FAQ
  - 公式ドキュメント style guide
  - 公式リリースノート
  - 公式オウンドメディア
- generic な AI writing tips は source-of-truth にしない
- 見た URL は final report に必ず残す

今回の do not:
- `announcement / branding / case_study / comparative_review / daily_story / industry_analysis` を次 owner にしない
- source thinness 全般の broad 対応を始めない
- formatter-only polish を winner にしない
- prompt-only / persona 増量を winner にしない
- article-type routing table を追加しない
- H1 review をやり直すだけで終わらない

まず行う compare / checks:
- 必須 test:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_owned_media_experiment.py note\tests\test_evaluate_owned_media_experiment.py -q
- 必須 live spot:
  - C:\tetie\notecode\.venv\Scripts\python.exe evaluate_owned_media_experiment.py --live --case-set realistic --case explanatory_primary_source_handling --json
  - C:\tetie\notecode\.venv\Scripts\python.exe evaluate_owned_media_experiment.py --live --case-set fixed --case explanatory_article --json
  - C:\tetie\notecode\.venv\Scripts\python.exe evaluate_owned_media_experiment.py --live --case-set ambiguous --case explanatory_ambiguous_primary_source --json

実装した場合の再検証:
- 上の3 spot を rerun
- その上で broad regression check:
  - C:\tetie\notecode\.venv\Scripts\python.exe evaluate_owned_media_experiment.py --live --case-set realistic --compare-modes --json

判定の目安:
- H4 primary:
  - reservation 自体はある
  - draft または expand 前の設計では後半の差がある
  - expand または polish 後に、後半が前半の言い換え・一般論・総括へ寄る
  - FAQ / 例外 / 判断境界 / next action の回収密度が surface 上で下がる
- H2 primary:
  - realistic dense でも、late reservation item 自体が generic fallback に寄っていて、
    expand/polish を触る前から後半へ置く具体点が弱い
- H1 contradiction:
  - current code / live output で reservation が実際には保持されていない証拠が出た場合だけ reopen 候補

pass condition:
- realistic explanatory で
  - 後半に新しい具体情報が残る
  - FAQ / 例外 / 判断境界 / next action の少なくとも2種類が明確に残る
  - 前半の言い換え総括だけで閉じない
  - `paragraph_length_uniform` を増やさない
  - 破綻や narrator leakage を増やさない
- fixed / ambiguous explanatory で regression がない
- broad realistic compare で `default_hybrid` keep を揺るがさない

rollback / stop condition:
- H4 primary の evidence が足りない
- 実装が H2 broad対応へ膨らむ
- explanatory 以外へ broad regression が出る
- 3 回失敗した
- rollback 不可能な diff が必要になった

最終報告で必ず示すこと:
1. 参照ルールファイル
2. 今回の実施範囲
3. 読んだ explanatory artifact
4. H4 / H2 / H1 contradiction のうち何が primary だったか
5. `expansion_flattening` が本当に効いた condition
6. source thinness と切るべきか、expand/polish flattening と切るべきか
7. 実装した場合:
   - touched owner file
   - narrow diff
   - 実行した tests / compare
8. 実装しなかった場合:
   - なぜ stop したか
   - 次 owner は何か
9. default_hybrid keep を維持できるか
10. 見た web sources の URL 一覧
11. AGENTS / WORKLOG 更新の要否

最終的に欲しい答え:
- explanatory_article dense の残課題は H4 でまだ詰められるのか
- それとも H2 に切り替えるべきか
- 次の 1 owner は `owned_media_experiment.py` のままでよいか
```
