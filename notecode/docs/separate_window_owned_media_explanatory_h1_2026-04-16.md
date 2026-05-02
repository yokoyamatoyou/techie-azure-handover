# separate window owned media explanatory h1 2026-04-16

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

current keep state:
- broad keep は `default_hybrid`
- `daily_story + ambiguous` の H4 residual には narrow polish guard が入っている
- この keep diff を reopen しない
- article-type fixed routing table を追加しない
- prompt accretion / hidden reviser accretion をしない
- semantic split を default 化しない

今回の役割:
- あなたは `explanatory_article dense` の late-evidence starvation reviewer / implementer です
- 目的は H1 `late_evidence_starvation` が本当に primary かを local evidence と web source で再確認し、
  owner-local な narrow diff がある場合のみ入れることです

今回の narrow hypothesis:
- `explanatory_article` の realistic dense 条件では、
  `late_evidence_reservation` 自体は存在するが、
  後半で FAQ / 例外 / 判断境界 / next action が十分に新情報として回収されず、
  expand / polish の段階で前半の言い換え寄りに均される
- もしこの仮説が正しいなら、owner は `owned_media_experiment.py` の explanatory late-evidence path に閉じられる

candidate hypothesis:
- H1: late_evidence_starvation
- H2: source_sufficiency_mismatch
- H4: expansion_flattening

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
- H1 と H4 を同時に広く触らない
- 1 hypothesis = 1 owner scope に閉じる
- apply_patch で編集する
- same hypothesis unchanged retry は 3 回まで

今回の do:
1. local evidence を優先して、explanatory 3条件の surface を読み直す
2. `late_evidence_reservation` が
   - source packet
   - blueprint
   - draft prompt
   - expand/polish 後本文
   のどこで薄まるかを切る
3. H1 が primary と言える場合のみ owner-local diff を入れる
4. H1 が primary でなければ実装せず observation だけを report する
5. web search を使い、一次ソースだけで次を補助観察する
   - source が薄いときに何を削るか
   - 後半で FAQ / 例外 / 判断境界 / next action をどこに置くか
   - 締め前に意味重複をどう避けるか
   - 段落呼吸をどこで崩すか

web search rule:
- 必ず web search を使う
- 優先するのは一次ソース:
  - 公式ヘルプ / FAQ
  - 公式リリースノート
  - 公式オウンドメディア
  - 公式 note
- generic な AI writing tips は source-of-truth にしない
- 見た URL は final report に必ず残す

今回の do not:
- `announcement / branding / case_study / comparative_review / daily_story / industry_analysis` を次 owner にしない
- source thinness 全般の broad 対応を始めない
- formatter-only polish を winner にしない
- prompt-only / persona 増量を winner にしない
- article-type routing table を追加しない

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
- H1 primary:
  - reservation 自体はある
  - source fit はある程度保てている
  - それでも後半の新情報が early summary へ寄る
  - FAQ / 例外 / 判断境界 / next action の回収密度が後半で足りない
- H2 primary:
  - dense と見えても reservation item が generic fallback に寄り、
    後半で足す具体点自体が弱い
- H4 primary:
  - draft までは後半の差があるのに、expand または polish 後に均される

pass condition:
- realistic explanatory で
  - 後半に新しい具体情報が残る
  - FAQ / 例外 / 判断境界 / next action の少なくとも2種類が明確に残る
  - 前半の言い換え総括だけで閉じない
  - 破綻や narrator leakage を増やさない
- fixed / ambiguous explanatory で regression がない
- broad realistic compare で `default_hybrid` keep を揺るがさない

rollback / stop condition:
- H1 primary の evidence が足りない
- 実装が H2 や H4 の broad 対応へ膨らむ
- explanatory 以外へ broad regression が出る
- 3 回失敗した
- rollback 不可能な diff が必要になった

最終報告で必ず示すこと:
1. 参照ルールファイル
2. 今回の実施範囲
3. 読んだ explanatory artifact
4. H1 / H2 / H4 のうち何が primary だったか
5. `late_evidence_starvation` が本当に効いた condition
6. source thinness と切るべきか、late reservation と切るべきか
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
- explanatory_article dense の残課題は H1 でまだ詰められるのか
- それとも H2/H4 に切り替えるべきか
- 次の 1 owner は `owned_media_experiment.py` のままでよいか
```
