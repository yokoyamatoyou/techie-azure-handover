# separate window owned media explanatory h2 2026-04-16

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
- C:\tetie\notecode\docs\separate_window_owned_media_explanatory_h4_2026-04-16.md

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

H1/H4 review から引き継ぐ current judgment:
- H1 `late_evidence_starvation` は primary ではない
- H4 `expansion_flattening` も primary ではない
- `late_evidence_reservation` は source packet / blueprint / draft / expand に残っている
- explanatory 3条件の live spot でも、後半 detail は一定程度残る
- したがって broad keep は `default_hybrid` のまま維持
- 次に切るなら H2 `source_sufficiency_mismatch`

current keep state:
- broad keep は `default_hybrid`
- `daily_story + ambiguous` の H4 residual には narrow polish guard が入っている
- この keep diff を reopen しない
- article-type fixed routing table を追加しない
- prompt accretion / hidden reviser accretion をしない
- semantic split を default 化しない

今回の役割:
- あなたは `explanatory_article dense` の source-sufficiency-mismatch reviewer / implementer です
- 目的は H2 `source_sufficiency_mismatch` が本当に primary かを local evidence と web source で再確認し、
  owner-local な narrow diff がある場合のみ入れることです

今回の narrow hypothesis:
- explanatory_article では `late_evidence_reservation` 自体は存在するが、
  fixed / ambiguous とくに source thin 条件では reservation item が generic fallback に寄りやすく、
  FAQ / 例外 / 判断境界 / next action として後半へ置く具体点が弱い
- realistic dense でも、source_packet 側の explanatory source-fit 選別が広すぎるか弱すぎるため、
  reservation の中身が「使える具体 detail」より「抽象説明句」に寄る run がある
- もしこの仮説が正しいなら、owner は `owned_media_experiment.py` の
  `_build_explanatory_late_evidence_reservation()` 周辺に閉じられる

candidate hypothesis:
- H2: source_sufficiency_mismatch
- H4: expansion_flattening (do not reopen unless decisive contradiction appears)
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
- H2 と H4 を同時に広く触らない
- H1/H4 を evidence なしで reopen しない
- 1 hypothesis = 1 owner scope に閉じる
- apply_patch で編集する
- same hypothesis unchanged retry は 3 回まで

今回の do:
1. local evidence を優先して、explanatory 3条件の source packet surface を読み直す
2. `_build_explanatory_late_evidence_reservation()` の
   - candidate 抽出
   - explanatory source-fit 判定
   - generic fallback への落ち方
   - specific_facts / faq_or_exceptions / operational_details / next_actions / close_takeaways の配分
   を切る
3. realistic / fixed / ambiguous の差を見て、
   H2 が primary と言える場合のみ owner-local diff を入れる
4. H2 が primary でなければ実装せず observation だけを report する
5. web search を使い、一次ソースだけで次を補助観察する
   - source thin な explanatory content で何を削り、何を残すか
   - FAQ / 例外 / 判断境界 / next action に値する detail の最小単位は何か
   - docs / help / conceptual content で generic summary を避けるための原則

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
- H4 review をやり直すだけで終わらない

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
- H2 primary:
  - reservation 自体はある
  - しかし reservation item が generic fallback に寄り、
    後半へ置く detail が source-backed な具体度を欠く
  - fixed / ambiguous でその傾向が強く、
    realistic でも source-fit 抽出に改善余地が見える
- H4 contradiction:
  - reservation item は十分具体だが、expand/polish で失われる decisive evidence が出た場合だけ reopen 候補
- H1 contradiction:
  - reservation path 自体が保持されていない decisive evidence が出た場合だけ reopen 候補

pass condition:
- realistic explanatory で
  - reservation item が generic fallback に寄りすぎない
  - FAQ / 例外 / 判断境界 / next action に相当する具体項目が source-backed に残る
  - 前半の抽象説明句の言い換えだけで後半を作らない
  - 破綻や narrator leakage を増やさない
- fixed / ambiguous explanatory で regression がない
- broad realistic compare で `default_hybrid` keep を揺るがさない

rollback / stop condition:
- H2 primary の evidence が足りない
- 実装が broad source-thinness 対応へ膨らむ
- explanatory 以外へ broad regression が出る
- 3 回失敗した
- rollback 不可能な diff が必要になった

最終報告で必ず示すこと:
1. 参照ルールファイル
2. 今回の実施範囲
3. 読んだ explanatory artifact
4. H2 / H4 contradiction / H1 contradiction のうち何が primary だったか
5. `source_sufficiency_mismatch` が本当に効いた condition
6. source thinness と切るべきか、reservation path と切るべきか
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
- explanatory_article dense の残課題は H2 でまだ詰められるのか
- それとも別 hypothesis に切り替えるべきか
- 次の 1 owner は `owned_media_experiment.py` のままでよいか
```
