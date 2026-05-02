# Start Prompt For Separate Window

作業ディレクトリは `C:\tetie\notecode`。

最初に読むこと:

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\docs\persona_ui_quality_fail_handoff_2026-04-23.md`
4. `C:\tetie\WORKLOG.md`
5. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

目的:

UIの「記事の書き手」選択と記事タイプ persona が衝突していないかを確認し、直近の quality fail-closed を、対症療法ではなく persona / source understanding / voice adapter の設計で改善する。

直近エラー:

- `attempt_id`: `gen-d74e4092`
- `article_type`: `explanatory_article`
- `semantic_article_key`: `explanatory_article`
- source file:
  - `C:\tetie\notecode\note\uploads\3c0e4fcb65d1415e94e52f7b36010548_AI______________.md`
- UI route:
  - purpose: `explain`
  - target: `concept`
  - source mode: `grounded`
  - prompt: empty
  - tone: auto
  - perspective: auto
- stopped with:
  - `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - `fingerprint:bigram_mono_low`
  - `fingerprint:vocab_repetition`
  - `fingerprint:syntactic_complexity_low`
  - `fingerprint:ending_repetition`
  - `fingerprint:comma_overuse`
  - `source_grounding:weak_reflection`

重要方針:

- 品質閾値を下げない。
- fail-open にしない。
- blacklist / regex / surface cleanup を増やす方向から始めない。
- prompt 肥大で直さない。
- WORKLOG にある通り、対症療法は過去に逆効果になりやすかったため、最初の仮説は persona / source delivery / UI voice adapter に置く。
- UIの「記事の書き手」は、記事タイプ persona と競合する別 persona にしない。
- UI writer role は voice adapter として扱う。
- article-type persona が lead angle / heading order / fact selection / paragraph emphasis / final paragraph を支配する。
- source contract / validation / repair / persona 名を本文や writer evidence に漏らさない。

まず確認するログ:

- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- `C:\tetie\notecode\logs\app.log`
- `C:\tetie\notecode\logs\generation_audit_log.jsonl`

最初に見る実装候補:

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`

推奨する狭い仮説:

`explanatory_article` の long single-source / empty prompt ケースで、writer が source を heading-level summary として圧縮しすぎ、source-specific anchor が本文に足りない。article-type persona が source の対比・具体 anchor を選ぶ工程を持てば、source reflection と自然さが同時に改善する。

作業手順:

1. 直近ログから `gen-d74e4092` の failure を再確認する。
2. UI writer role / perspective / speaker_profile が persona とどう合成されているか確認する。
3. source digest / source grounding / distilled brief が long single-source explanatory にどう渡っているか確認する。
4. 変更するなら、owner scope を1-2ファイルに限定する。
5. まずテストを追加して、UI writer role は voice adapter、article-type persona は構造と source selection を持つことを固定する。
6. live 再現は、同じ upload source と同じ UI route で行う。
7. 成功した場合のみ、ALGORITHM.md の更新要否を判断する。

成功条件:

- `gen-d74e4092` 相当の入力で fail-closed しない。
- quality guard は下げない。
- source reflection が改善する。
- fingerprint warnings が減る。
- 本文に hidden instruction / source contract / validation / repair / persona 名が漏れない。
- source outside claim が増えない。
- UI writer role と article persona が衝突しない。
- 日本語として、主語・文末・読点・段落の単調さが軽くなる。

停止条件:

- blacklist / regex cleanup の追加でしか改善しない。
- prompt が大きく肥大する。
- quality threshold を下げる必要が出る。
- source外 claim が残る。
- hidden/internal term leakage が残る。
- 同じ narrow hypothesis で3回失敗する。

最後に報告すること:

- 変更したファイル
- 直近ログの再現可否
- UI writer role と persona の衝突有無
- 採用した設計
- テスト結果
- live rerun 結果
- ALGORITHM.md 更新の要否
