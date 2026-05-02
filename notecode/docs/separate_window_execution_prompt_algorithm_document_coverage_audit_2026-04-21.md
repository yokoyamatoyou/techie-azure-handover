# separate window execution prompt algorithm document coverage audit 2026-04-21

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
- `ALGORITHM_DOCUMENT_COVERAGE_AUDIT`
- 主目的は `C:\tetie\notecode\ALGORITHM.md` の記載漏れ監査
- code change main ではなく docs-first

今回の目的:
- `ALGORITHM.md` が current mainline の実態を過不足なく説明できているかを評価する
- 特に company introduction repair まわりで
  - prompt-based local repair
  - 後半の問題区間を基点にした bounded edit
  - ただし返却は partial diff ではなく全文 tagged article
  - incomplete repair output は reject
  という理解がドキュメント上で欠けていないかを精査する
- 混乱源になりうる曖昧表現や不足説明を洗い出す

今回の評価対象ドキュメント:
- primary:
  - C:\tetie\notecode\ALGORITHM.md
- source-of-truth / comparison:
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- code truth:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\simple_note_pipeline\postprocess.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の owner scope:
- `ALGORITHM.md` の completeness / correctness / ambiguity 監査
- 必要なら `ALGORITHM.md` だけを更新してよい
- production code / tests / plan docs / AGENTS / WORKLOG は変更しない

このウインドウで最初に確認すること:
1. `ALGORITHM.md` に current source of truth が正しく書かれているか
2. mainline の固定骨格が `single-pass + optional single repair 1回` と一致しているか
3. company introduction repair の説明が、実装上の contract と一致しているか
4. repair output acceptance の説明が、`inspect_tagged_output_contract()` の実装と一致しているか
5. partial patch-style output を reject する理由が、ドキュメント上で説明されているか
6. 既知の破損経路が、読む人に分かる粒度で記載されているか

今回の authoritative implementation facts:
- repair prompt は `prompt_builder.py` で全文 tagged article 再出力を要求する
  - 差分ではなく全文を返す
  - `[TITLE]/[LEAD]/[BODY]/[HASHTAGS]` をすべて返す
  - 未変更箇所も省略しない
- repair acceptance は `pipeline.py` で incomplete output を reject する
  - `plain_fallback` は reject
  - `complete_article=False` は reject
  - rejection reason は `repair_output_contract_incomplete`
- tagged output contract は `postprocess.py` で次に分類される
  - `tag_blocks`
  - `line_recovery`
  - `plain_fallback`
- `line_recovery` は malformed but complete article の救済であり、
  partial patch-style output の許可を意味しない

必須の監査観点:
1. `ALGORITHM.md` を読んだだけで current success path が追えるか
2. local repair と full-article regeneration の関係が明確か
3. 「後半を基点に編集する」と「後半だけ返す」が混同されない書き方になっているか
4. acceptance contract が parse mode ごとに説明されているか
5. line recovery の扱いが誤読されないか
6. fail-closed boundary が十分に明記されているか
7. 既知の corruption path
   - `title=[BODY]`
   - lead に body 流入
   - `#BODY`
   が、なぜ起きるか分かるように書かれているか
8. telemetry / audit の記述が不足していないか
9. retry-stop rule や owner scope の記述が current package と矛盾していないか
10. 実装済み事項なのに未記載のもの、逆に未実装なのに書かれているものがないか

漏れありと判定する条件:
- 実装上 non-negotiable な contract が書かれていない
- 用語はあるが accept/reject boundary が曖昧
- current path を読むのに必要な責務境界が抜けている
- company introduction repair の読解に必要な前提が欠けている
- current code truth と doc がズレている

漏れなしと判定する最低条件:
- source of truth が current package に更新されている
- mainline 骨格が current 実装と一致する
- repair algorithm が prompt-based local repair + full article return として説明されている
- acceptance contract が parse mode 付きで説明されている
- partial patch-style output reject の理由が明示されている
- known corruption path が説明されている
- touched files / owner boundary / telemetry が必要十分に書かれている

今回の禁止:
- production code 修正
- test 修正
- plan docs 更新
- AGENTS / WORKLOG 更新
- 「気になるからついでに構成を大改稿する」こと
- wording 好みだけで差し戻すこと

推奨の進め方:
1. `ALGORITHM.md` を通読する
2. current source-of-truth docs を通読する
3. repair prompt / acceptance contract / parse contract の実装箇所だけ読む
4. `ALGORITHM.md` の各節を
   - correct
   - incomplete
   - ambiguous
   - stale
   に分類する
5. 不足点を severity 付きで列挙する
6. `ALGORITHM.md` だけで補えるなら、その場で最小更新する
7. 更新後にもう一度「初見読者が誤読しないか」を確認する

allowed touched files:
- C:\tetie\notecode\ALGORITHM.md

最終報告フォーマット:
1. 読んだドキュメント / コード
2. `ALGORITHM.md` の coverage 判定
   - complete / incomplete
3. 漏れ or 曖昧さの一覧
   - 各項目に severity
   - なぜ漏れなのか
   - どの実装事実に対する不足か
4. 更新した場合
   - 何を追記 / 修正したか
5. 更新しなかった場合
   - なぜ現状で十分と判断したか
6. 残リスク
7. 追加で別文書へ分離すべき論点があるか

最終報告で必ず明記すること:
- `ALGORITHM.md` だけで current repair algorithm を誤読なく説明できるか
- 「後半基点の局所修復」と「部分出力」を混同する余地が残っているか
- incomplete repair output reject の説明が十分か
- まだ漏れがあるなら、どの節に何を足すべきか
```
