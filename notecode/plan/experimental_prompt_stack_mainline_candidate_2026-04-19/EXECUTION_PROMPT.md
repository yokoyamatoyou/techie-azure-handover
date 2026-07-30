# experimental_prompt_stack_mainline_candidate_2026-04-19 EXECUTION_PROMPT

以下を次ウインドウへそのまま貼って使う。

---

あなたは `C:\tetie\notecode` で作業する。目的は `experimental_prompt_stack` を current mainline default へ昇格できるかを判定し、条件を満たす場合にだけ最小差分で昇格実装すること。  
今の baseline はすでに一段入っている。`body_generation_experiment` は current mainline 経路で保持され、`experimental_prompt_stack` は `SOURCE_PACKET -> ARTICLE_CONTRACT -> writer -> suffix editor -> audit` まで実装済みである。  
さらに success visibility / historical compare / promotion gate surface は UI matrix payload と artifact に出る状態まで進んでいる。  
今回の window では broad rewrite をせず、phase / slice を自律的に進め、3回連続失敗しない限り package goal まで完走する。

## 必須 read order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\README.md`
4. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\TASK.md`
5. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\PROGRESS.md`
6. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\ROLLBACK.md`
7. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\note\generation_request_builder.py`
9. `C:\tetie\notecode\note\current_mainline_runner.py`
10. `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
11. `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
12. `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
13. `C:\tetie\notecode\note\tests\test_generation_request_builder.py`
14. `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
15. `C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py`
16. `C:\tetie\notecode\note\tests\test_current_mainline_genre_sweep.py`
17. `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
18. `C:\tetie\notecode\logs\latest_generation_output.txt`
19. `C:\tetie\notecode\logs\latest_generation_quality_report.json`

historical compare が必要なときだけ:

- `C:\tetie\notecode\logs\ad_hoc_quality_compare\20260410-083045-prompt-only-vs-current-mainline-company-grounded\summary.json`
- `C:\tetie\notecode\logs\direct_gpt54_prompt_only_same_source_2026-04-03.json`
- `C:\tetie\notecode\logs\prompt_only_probe_2026-04-03_same_source.json`
- `C:\tetie\notecode\logs\prompt_only_probe_2026-04-03_same_source_force_accept.json`

## 実行契約

- phase / slice を自律進行する
- 1 slice ごとに最小差分で進める
- 各 slice 完了後に必ず self-test を実行する
- self-test が pass したら、確認待ちせず次の slice へ進む
- phase が完了したら、確認待ちせず次の phase へ進む
- self-test または実装が fail したら、その slice / phase 内で最大 3 回まで自己修正する
- 3 回失敗したら、その時点で停止して user へ報告する
- hard blocker がない限り user に質問せず進める
- hard blocker がなく、3 回失敗していない限り途中停止しない
- self-test が pass したら、次の slice に自律的に進む
- context が増えすぎた場合だけ clean boundary で止めて、`PROGRESS.md` と必要なら `EXECUTION_PROMPT.md` を更新して handoff を残す
- 途中で止めるときは、必ず「completed slice / passed tests / next exact slice / unresolved blocker」を docs に残す

## 品質判定の原則

- 合格判定は主に視認ベースで行う
- metric / payload / compare summary は補助根拠として使う
- 単に test が通るだけでは昇格根拠として不十分
- 記事を人が読んで、途中で論点が抜けないか、段落同士が自然につながるか、意味の重複や崩れがないかを重視する
- quality に迷いがある場合は default 昇格を見送る

## 再発監視

- prompt-only 再発条件:
  - 記事途中で prompt follow / anchor / must-cover の保持が弱くなる
  - 前半は合っていても後半で論点が薄くなる
  - audit / compare summary で追従低下を説明できない
- 骨格ベース 再発条件:
  - section 間の意味重複が目視で明確
  - 記事全体のつながりが崩れ、何を伝えたいかが読みにくい
  - 記事としての意味破綻がある
  - audit / quality warning が残り、解消根拠がない
- 上記の再発が視認ベースで確認された場合、default 昇格を止める

## 肥大抑制

- prompt accretion を増やしすぎない
- module accretion を増やしすぎない
- compare helper や gate surface は narrow scope に閉じる
- broad rewrite をしない
- 既存 mainline route を壊さない
- default flip 以外で不要な route 変更をしない

## 優先順位

1. shared checks / promotion evidence を確認する
2. default 昇格を許可するか判定する
3. gate pass 後にだけ mainline 昇格条件を実装する
4. gate fail なら default は維持したまま blocker を明文化する

## 絶対に戻さないもの

- `body_generation_experiment` strip
- planner-centered rigid section skeleton
- full-article editor rewrite
- source safety / prompt injection defense の弱体化
- broad rewrite

## current baseline で pass 済みのテスト

`pytest` は PATH にないので `python -m pytest` を使う。

- `python -m pytest C:\tetie\notecode\note\tests\test_generation_request_builder.py -q`
- `python -m pytest C:\tetie\notecode\note\tests\test_current_mainline_runner.py C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py C:\tetie\notecode\note\tests\test_current_mainline_genre_sweep.py C:\tetie\notecode\note\tests\test_simple_note_pipeline.py -q`

## current completed surface

- success visibility:
  - `audit_verdict / next_action / compare_ready / compare_reason` が result payload / UI artifact に出る
- historical compare:
  - `latest_generation_quality_report.json`
  - `ad_hoc_quality_compare/.../summary.json`
  - `direct_gpt54_prompt_only_same_source_2026-04-03.json`
  - `prompt_only_probe_2026-04-03_same_source.json`
  - `prompt_only_probe_2026-04-03_same_source_force_accept.json`
  を narrow compare summary に集約済み
- promotion gate:
  - `default_flip_allowed` はまだ `false`
  - measured checks は payload に出る
  - external checks は `targeted_tests_pass / shared_checks_pass`

## 自律進行 phase map

### Phase 1 Promotion Evidence Verification

- Slice 1:
  - `historical_compare` と `promotion_gate` の payload / artifact を確認する
  - old prompt-only failure が input-contract block か content failure かを再確認する
- Slice 2:
  - 旧失敗を「昇格停止条件」として current candidate に照らして確認する
  - 視認ベースで
    - 途中の prompt 追従低下
    - section 間重複
    - article collapse
    が出ていないか確認する
- Slice 3:
  - 必要な targeted tests / shared checks を追加実行し、evidence を固める
- Exit:
  - 昇格可否を yes/no で判断できる状態にする

### Phase 2 Promotion Decision

- Phase 1 の evidence を使って default 昇格可否を判定する
- gate pass:
  - Phase 3 へ自動移行する
- gate fail:
  - default は維持する
  - blocker / failure reason を `PROGRESS.md` に固定する
  - 追加の局所修正で解消できるなら同一 phase で最大 3 回まで自己修正する
  - 3 回失敗したら停止して user report する

### Phase 3 Default Promotion

- gate pass 時だけ実行する
- default flip を最小差分で実装する
- broad rewrite はしない
- 実装後に targeted tests / shared checks を再実行する
- regression があれば同一 phase で最大 3 回まで自己修正する
- pass したら Phase 4 へ自動移行する

### Phase 4 Closeout

- 完了時は `PROGRESS.md` を更新する
- 必要なら `EXECUTION_PROMPT.md` を次 window 用に更新する
- final report では
  - 何を確認したか
  - 何を変更したか
  - 実行したテスト
  - 昇格可否
  - 残 blocker
  を短く報告する

## promotion gate

以下が揃うまで default mainline へは上げない。

- experiment propagation end-to-end pass
- targeted tests pass
- success condition visibility pass
- historical compare readable
- old prompt-only failure と content failure を区別できる
- prompt-only 的な途中の追従低下が current candidate で再発していない
- 骨格ベース的な section 重複 / article collapse が current candidate で再発していない
- shared path no regression

## final output rule

- 各 slice 後は何を変えたか、何をテストしたか、pass/fail、次 slice を短く報告する
- 3 回失敗時は、その slice の failure reason と試した修正を簡潔にまとめて停止する
- package goal を完了したら、昇格可否とその根拠を短く明記する

---
