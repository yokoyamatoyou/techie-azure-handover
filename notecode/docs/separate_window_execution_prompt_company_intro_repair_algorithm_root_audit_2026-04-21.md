# separate window execution prompt company intro repair algorithm root audit 2026-04-21

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate window execution prompt
- `COMPANY_INTRO_REPAIR_ALGORITHM_ROOT_AUDIT`
- docs-only analysis ではなく、必要なら production code / tests / live rerun まで行う

今回の実施範囲:
- company introduction の `後半起点での見直し / repair` アルゴリズム全体を end-to-end で精査する
- 今回の主題は `repair output integrity` だけに閉じない
- ただし owner scope は `company introduction repair algorithm` とその direct contract surface に留める
- 対症療法の追加は禁止
- 既存の対症療法が紛れ込んでいないかも必ず監査する
- current success path を壊さない

このウインドウで最初に読む証跡:
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\app.log
- 必要なら:
  - C:\tetie\notecode\logs\generation_audit_log.jsonl

このウインドウで読むべきコード:
- primary:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\simple_note_pipeline\postprocess.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\simple_note_pipeline\rendering.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- secondary if needed:
  - C:\tetie\notecode\note\current_mainline_runner.py
  - C:\tetie\notecode\note\note_writer_app.py
  - C:\tetie\notecode\note\llm_client.py
- 参照のみ:
  - C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py

今回の authoritative evidence:
- latest authoritative corruption attempt:
  - attempt_id = gen-e451e736
  - timestamp = 2026-04-21 00:16:11 JST
  - article_type = branding
  - semantic_article_key = company_introduction
  - runtime_reason_code = SYS_QUALITY_WARNINGS_UNRESOLVED
  - observed corruption:
    - title = `[BODY]`
    - lead に本文全体が流入
    - hashtags = `#BODY ...`
    - body / hashtags 混線
- latest local follow-up rerun:
  - attempt_id = gen-live-rerun-20260421-002758
  - timestamp = 2026-04-21 00:28:20 JST
  - runtime_reason_code = OK
  - format corruption は消えた
  - ただし
    - must_cover_reflection_rate = 0.3333
    - source_grounding_reflection_ratio = 0.0
    - source_grounding:weak_reflection 系は soft に残る
- management read:
  - format corruption は guard-facing main cause の一つだった可能性が高い
  - ただし latest rerun が OK になったからといって root cause close とみなさない
  - current patch が root fix か symptom patch かを再監査する

現在疑うべき root cause cluster:
1. repair prompt が「後半の局所見直し」を要求しているのに、
   parser / normalizer / acceptance 側が「完全な tagged article 再出力」を暗黙前提にしている
2. repair path の contract が曖昧で、
   partial tagged output / malformed tagged output / local patch style output のどれを正式に許すか決まっていない
3. parser fallback / normalize / title_hint / hashtag cleanup が、
   壊れた出力を隠しながら次段に通す symptom layer になっている
4. format corruption を直しても must_cover / source_grounding が戻っていないため、
   repair algorithm 自体が current-business-first / source-backed company intro を回復する設計になっていない可能性がある

今回の禁止:
- output_guard.py の fail-close 条件変更
- strict_saas_mode 変更
- telemetry_writer.py / quality_observability_mixin.py の tokenizer 修正
- compat cleanup reopen
- unrelated cleanup
- 「落ちたから regex を 1 本足す」式の延命
- 「latest rerun が OK だから close」で終えること

対症療法 NG の判定ルール:
- 壊れた出力を downstream regex で隠すだけなら NG
- malformed output を parser が飲み込むだけで upstream contract 不整合を残すなら NG
- acceptance / normalize / build_result のどこかで silent correction して artifact を作るだけなら NG
- root contract を明示せずに fallback を増やすだけなら NG
- article_type=company_introduction 専用の ad-hoc 条件を積み増して general repair 設計を曖昧にするなら NG

root fix と認める条件:
- repair 出力 contract が明文化される
- prompt / parser / normalizer / acceptance / result build の期待値が同じになる
- malformed / partial output を許容するなら、その理由と formal boundary がコード上で説明できる
- 局所 repair なのか全文再出力なのかが flow 上で一貫する
- corruption を隠すのではなく、なぜ壊れなくなるかを call chain で説明できる
- latest rerun で少なくとも format corruption 主因は消え、主因が別系統へ移ったと説明できる

必須の監査観点:
1. actual call chain を end-to-end で short map 化する
   - repaired_raw
   - parse_tagged_output(repaired_raw)
   - _normalize_draft(...)
   - finalize_note_draft(...)
   - build_result(...)
   - output_guard handoff
2. repair prompt が local patch を要求しているか、full article regeneration を要求しているかを明文化する
3. parser fallback が silent recovery になっていないか確認する
4. normalize / title_hint / hashtag normalization が contract mismatch を隠していないか確認する
5. acceptance が format integrity を前提にしているか確認する
6. company introduction rescue path が must_cover/source_grounding を実際に回復しうる設計か確認する
7. 現在の `postprocess.py` 側 salvage が root fix か symptom patch かを明示判定する

最初の作業手順:
1. 正本 / 証跡 / 対象コードを読む
2. `company introduction repair algorithm map` を 1 枚作る
3. `contract mismatch points` を列挙する
4. `symptom patches candidate list` を列挙する
5. それぞれを
   - root contract layer
   - algorithm layer
   - normalization layer
   - presentation layer
   に分類する
6. そのうえで 1 本の root hypothesis に絞る
7. 必要なら実装修正する
8. owner-local tests と exact live rerun を行う

症状再現の最低条件:
- `gen-e451e736` 型の壊れ方を再現または同型で説明できること
- `title=[BODY]` がどの fallback で発生するか示すこと
- `lead に body 全量流入` がどこで固定されるか示すこと
- `hashtags=#BODY ...` がどこで生まれるか示すこと

allowed touched files:
- production:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\simple_note_pipeline\postprocess.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\simple_note_pipeline\rendering.py
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - 必要最小限なら current mainline runner / regression tests

do-not-touch unless absolutely proven necessary:
- C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\plan\...
- AGENTS / WORKLOG

implementation policy:
- まず remove / simplify / align を考える
- fallback を増やす前に contract を揃える
- local heuristics を足すなら、なぜそれが contract-aligned で symptom patch ではないかを書く
- 同じ問題を prompt 側 / parser 側 / normalize 側で二重に吸収しない
- parser salvage を keep する場合も、その前提 contract をコードと tests で固定する
- 「company intro だけ特別扱い」の ad-hoc ではなく、repair algorithm として説明できる形を優先する

tests / checks:
- focused:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "company_intro or repair or tagged_output or malformed" -q
- owner-local:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- 必要なら:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -k "company or branding" -q

live rerun:
- exact same live input line を再実行する
- latest logs を更新し、
  - format corruption が消えたか
  - must_cover/source_grounding がどう変わったか
  - reason_code がどう変わったか
  - 主因が format corruption から別系統へ移ったか
  を確認する

stop conditions:
- scope を超えないと root fix できない
- multiple owner simultaneous reopen が必要
- output_guard / strict_saas / telemetry / compat cleanup を触らないと前進できない
- rerun 主因が別系統
  - 例: SYS_PIPELINE_FAILURE, unrelated article_type regression, LLM client failure
- root fix を説明できず symptom patch しか残らない

最終報告フォーマット:
1. 読んだ正本 / 証跡 / コード
2. end-to-end algorithm map
3. corruption 発生段階の特定結果
4. contract mismatch points
5. symptom patches candidate list
6. そのうち root fix / symptom patch の判定結果
7. touched files
8. 実装内容
9. 実行した tests と結果
10. live rerun attempt id / timestamp / exact outcome
11. before / after の latest reason
12. must_cover / source_grounding の before / after
13. 残リスク
14. AGENTS / WORKLOG / plan docs 更新要否

最終報告で必ず明記すること:
- `current patch に対症療法が残っているか / 残っていないか`
- 残っているなら何がなぜ NG か
- 取り除いたなら何をどう揃えたか
- `OK` になっても close と言ってよい状態か、まだ言えないか
```
