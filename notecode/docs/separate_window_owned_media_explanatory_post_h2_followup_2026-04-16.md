# separate window owned media explanatory post h2 followup 2026-04-16

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
- C:\tetie\notecode\docs\separate_window_owned_media_explanatory_h2_2026-04-16.md

今回の実施範囲:
- H2 keep diff 後の explanatory follow-up residual review
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
  - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-110131\report.md
- H2 keep 後 broad compare:
  - C:\tetie\notecode\logs\owned_media_experiment_compare_20260416-122805\report.md
  - もしこの path が存在しなければ、`C:\tetie\notecode\logs\owned_media_experiment_compare_*` の最新 compare artifact を使う
- explanatory target artifacts:
  - realistic:
    - latest H2 keep 後 compare artifact の `default_hybrid.json`
    - case id: `explanatory_primary_source_handling`
  - fixed:
    - latest H2 keep 後の live output / compare artifact
    - case id: `explanatory_article`
  - ambiguous:
    - latest H2 keep 後の live output / compare artifact
    - case id: `explanatory_ambiguous_primary_source`

H1/H4/H2 review から引き継ぐ current judgment:
- H1 `late_evidence_starvation` は primary ではない
- H4 `expansion_flattening` も primary ではない
- H2 `source_sufficiency_mismatch` が primary で keep diff 済み
- H2 keep diff は explanatory reservation の placeholder 除外 / bucket 横断重複防止 / category-aware 配分に閉じている
- broad keep は `default_hybrid`
- `2026-04-16 12:28:05 JST` broad compare rerun は overall_preferred_mode = `default_hybrid`、7/7 cases default_hybrid 優勢

current keep state:
- broad keep は `default_hybrid`
- `daily_story + ambiguous` の H4 residual keep diff は reopen しない
- article-type fixed routing table を追加しない
- prompt accretion / hidden reviser accretion をしない
- semantic split を default 化しない

今回の役割:
- あなたは H2 keep 後の explanatory residual reviewer / implementer です
- 目的は、H2 keep diff で explanatory residual が十分に縮んだかを再確認し、
  まだ owner-local に詰められる残差がある場合のみ narrow diff を入れることです

今回の narrow hypothesis:
- H2 keep diff 後は、fixed / ambiguous の reservation bucket role collapse は主要因ではなくなっている
- 残差があるとしても、それは reservation source-fit 以外の owner-local surface に narrow に切れる
- もし residual が H1/H4 broad reopen か別 owner を要求するなら、実装せず stop する

candidate hypothesis:
- post-H2 no-major-residual
- post-H2 owner-local minor residual in `owned_media_experiment.py`
- reopen not allowed by default:
  - H1
  - H4
  - broad source-thinness line

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
- H1/H4 を evidence なしで reopen しない
- broad source-thinness 対応を始めない
- 1 hypothesis = 1 owner scope に閉じる
- apply_patch で編集する
- same hypothesis unchanged retry は 3 回まで

今回の do:
1. H2 keep 後の realistic / fixed / ambiguous explanatory 3条件を読み直す
2. reservation bucket role が本当に改善したかを source packet / live output で確認する
3. 残差があるなら、それが
   - owner-local に narrow に切れるか
   - H1/H4 broad reopen なしで扱えるか
   を先に判定する
4. narrow residual がある場合のみ owner-local diff を入れる
5. broad reopen が必要なら実装せず observation だけを report する
6. web search を使い、一次ソースだけで次を補助観察する
   - explanatory/conceptual/help content で residual genericity をどこまで許容するか
   - examples / use cases / next action を reader-task に結びつける最小条件

web search rule:
- 必ず web search を使う
- 優先するのは一次ソース:
  - 公式ヘルプ / FAQ
  - 公式ドキュメント style guide
  - 公式オウンドメディア
- generic な AI writing tips は source-of-truth にしない
- 見た URL は final report に必ず残す

今回の do not:
- `announcement / branding / case_study / comparative_review / daily_story / industry_analysis` を次 owner にしない
- formatter-only polish を winner にしない
- prompt-only / persona 増量を winner にしない
- article-type routing table を追加しない
- H2 keep diff の勝ち筋を崩す broad rewrite をしない

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
- stop / keep:
  - H2 keep 後に explanatory 3条件で major residual が見えない
  - broad keep を崩さない
- narrow owner-local residual:
  - residual が `owned_media_experiment.py` 1 file に閉じる
  - H1/H4 reopen を伴わない
  - fixed / ambiguous / realistic のどれかで一貫した local symptom がある
- stop / escalate:
  - residual が broad route / broad source-thinness / H1/H4 reopen を要求する
  - or owner-local 1 file に閉じない

pass condition:
- realistic explanatory で
  - 後半の具体情報が残る
  - FAQ / 例外 / 判断境界 / next action の役割差が維持される
  - 前半の抽象説明句の言い換えだけで後半を作らない
  - 破綻や narrator leakage を増やさない
- fixed / ambiguous explanatory で regression がない
- broad realistic compare で `default_hybrid` keep を揺るがさない

rollback / stop condition:
- owner-local residual evidence が足りない
- 実装が broad reopen へ膨らむ
- explanatory 以外へ broad regression が出る
- 3 回失敗した
- rollback 不可能な diff が必要になった

最終報告で必ず示すこと:
1. 参照ルールファイル
2. 今回の実施範囲
3. 読んだ explanatory artifact
4. H2 keep 後の residual judgment
5. residual が owner-local にまだ詰められるか
6. 実装した場合:
   - touched owner file
   - narrow diff
   - 実行した tests / compare
7. 実装しなかった場合:
   - なぜ stop したか
   - 次 owner は何か
8. default_hybrid keep を維持できるか
9. 見た web sources の URL 一覧
10. AGENTS / WORKLOG 更新の要否

最終的に欲しい答え:
- H2 keep 後の explanatory residual はまだ owner-local に詰める価値があるか
- それともここで stop して keep judgment を固定すべきか
- 次の 1 owner は `owned_media_experiment.py` のままでよいか
```
