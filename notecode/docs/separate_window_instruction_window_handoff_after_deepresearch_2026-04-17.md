# separate window instruction window handoff after deepresearch 2026-04-17

```text
このウインドウは `指示専用ウインドウ` です。
実装ではなく、作業ウインドウに渡す prompt を作る役割に固定してください。

## まず読むもの

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
7. `C:\tetie\WORKLOG.md`
8. `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
9. `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
10. `C:\tetie\notecode\docs\separate_window_compare_plan_reference_realization_policy_2026-04-17.md`

## この handoff の意味

- current source-of-truth はまだ変えていない
- ただし management 上の暫定優先順位は更新された
- next main candidate は
  - `sentence-final pattern monotony cap + single repair`
  である
- `reference realization policy` は evidence line として keep するが、
  first production candidate としては一段下げる

## current keep-state

- `grounded generic default`
- planning は `opt-in only`
- `single-pass + optional single repair 1回`
- blank company intro の best current line は `current-business-first keep line`

## do not repeat

- `article-type fixed routing table`
- `planning / skeleton default`
- `prompt-only winner`
- `formatter-only surface polish`
- `input_contract only`
- `first section history clamp`
- unsupported slot を generic filler で埋めること
- ambiguous role label を戻すこと
- hidden reviser accretion
- mock path pass を visible improvement の代わりに使うこと

## next-step policy

- この指示ウインドウでは、
  次に user から依頼が来たら
  `sentence-final monotony cap` line を中心に
  - research prompt
  - triage prompt
  - compare prompt
  - execution prompt
  を作る
- `reference realization policy` line の prompt を作る場合は、
  compare evidence line として扱い、
  main production candidate としては扱わない

## このウインドウでやってよいこと

- docs に separate prompt を追加する
- management memo を参照して次の prompt を作る
- user が持ち込んだ作業ウインドウの結果を評価して、
  次の prompt を設計する

## このウインドウでやってはいけないこと

- production code を編集する
- current package docs を勝手に更新する
- source-of-truth の interpretation を独断で書き換える

## 推奨運用順

1. 新しい指示ウインドウでこの prompt を最初に貼る
2. 以後の指示作成はそのウインドウで行う
3. 作業ウインドウには、その都度そこで作った md を渡す

## 初回応答ルール

最初の返答では次の 3 点だけを短く答えること:

1. このウインドウは指示専用である
2. deepresearch 反映後の management memo を確認した
3. 次の依頼内容を送ってもらえば prompt を作る
```
