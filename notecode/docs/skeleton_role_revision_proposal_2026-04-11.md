# skeleton_role_revision_proposal_2026-04-11

## Verdict

- 骨格ベース自体が悪いのではなく、`notecode` では骨格の責務を広げすぎていた可能性が高い
- 研究で優位だった骨格は `content planning / ordering / source alignment` のための骨格であり、本文の見え方や見出し順を固定するための骨格ではない
- current failure は `bone structure exists` ではなく `bone structure controls visible prose too much` と解釈する

## What Was Wrong

- source にない節役割まで先に固定していた
  - 例: source に厚い outcome がないのに `結果` 節を独立させる
- source から組み上げる前に、記事タイプごとの順番テンプレートを強く押していた
  - 例: `改善前 -> 対応 -> 工夫 -> 結果 -> 再現条件`
- planner の都合を writer surface に出しすぎていた
  - 見出しの役割が毎回似る
  - 節冒頭の運びが揃う
  - 「整理カード」的な surface が出やすくなる
- source digest と骨格の対応はあるが、骨格が `何を書くか` より `どの型で見せるか` を支配していた

## Revised Interpretation

- 骨格は残す
- ただし責務は次の 3 つに限定する
  - `何を書くか`
  - `どの source fact をどの節へ割り当てるか`
  - `どの節同士を混ぜないか`
- 骨格は次を直接支配しない
  - 見出しの固定順
  - 段落長
  - 節冒頭の言い回し
  - 一人称の出し方
  - prose の呼吸

## Proposed Algorithm Revision

### 1. Contract Resolve

- current `input_contract_v1` を維持する
- `self_reference_policy` は keep する
- ただし `self_reference_policy` は planner 用の骨格ではなく、writer の realization rail として扱う

### 2. Source Digest

- current source digest は維持する
- source は `summary` ではなく `fact cards` として薄く保つ
- 各 fact card は次だけ持つ
  - `fact_id`
  - `fact_text`
  - `source_title`
  - `source_locator`
  - `usable_for`
  - `cannot_support`

### 3. Optional Micro-Skeleton

- full skeleton ではなく `micro-skeleton` を使う
- 出力は本文の順番テンプレではなく、節ごとの役割メモだけに絞る
- shape:

```json
{
  "reader": "...",
  "core_message": "...",
  "section_candidates": [
    {
      "role": "problem|background|reason|operation|condition|closing",
      "fact_ids": ["fact1"],
      "must_cover": ["..."],
      "do_not_mix": ["..."],
      "merge_allowed_with": ["condition"]
    }
  ]
}
```

- 重要:
  - `role` は section title ではない
  - `role` は固定順を持たない
  - source が薄い role は削除できる
  - source が薄い `result` は `condition` や `closing` へ merge してよい

### 4. Writer = Prompt-Only First, Hybrid Rails Second

- writer の基本姿勢は `prompt-only` に近づける
- writer が主に読むものは次で固定する
  - `prompt_raw`
  - compact persona / naturalness rails
  - source fact cards
  - micro-skeleton
- 優先順位:
  - 1st: user prompt / source facts
  - 2nd: micro-skeleton role allocation
  - 3rd: style rails
- writer に渡す禁止事項:
  - `結果 -> 再現条件` のような固定順テンプレ
  - source がない節を作る指示
  - 「各節の1文目は〜」のような硬い surface 制約

### 5. Planner / Writer Boundary

- planner は `section title` を決めすぎない
- planner が決めるのは次だけ
  - 節の役割
  - 使う fact
  - 混ぜない論点
  - merge 可能性
- writer は次を自由に決めてよい
  - 見出し wording
  - 導入の入り方
  - 段落配分
  - 接続の仕方
  - 一人称の出し入れ

### 6. Editor / Repair

- editor は skeleton 違反を厳格に直しすぎない
- editor の責務は次に限定する
  - source 逸脱
  - AI 的反復
  - paragraph breath の均しすぎ
  - 主語消失
- editor は次をしない
  - skeleton 順の強制復元
  - source にない空節の補完
  - 見出し役割の再テンプレ化

## Non-Negotiable Rules

- `no source, no standalone section`
- `no forced fixed sequence unless source supports it`
- `role is hidden, prose is visible`
- `skeleton may merge, but should not invent`
- `self-reference policy belongs to realization, not planning`

## UI Policy

- 一人称 UI は採用候補として妥当
- ただし役割は限定する
  - `私`
  - `私たち`
  - `当社`
  - `弊社`
  - `なし寄り`
- これは骨格ではなく realization parameter として writer へ渡す
- UI で増やしてよいが、planner の role allocation には混ぜない

## Immediate Design Changes For notecode

### Keep

- `self_reference_policy` UI / contract
- company introduction の source-aware prune
- prompt surface preservation
- source grounding rails

### Remove Or Relax

- article_type ごとの固定順テンプレを writer の visible prompt に強く出すこと
- `各見出しの1文目は〜` のような surface 直結の planner 指示
- source が薄い場合でも `結果節` や `強み節` を独立させる pressure
- compat prompt を疑似 source として evidence に混ぜる流れ

### Add

- `micro-skeleton` の `merge_allowed_with`
- `no standalone section without exclusive fact`
- `role hidden / title free` rule
- `section exists only if it owns at least one exclusive fact or question`

## Evaluation Rule

- compare の採否は次で見る
  - target で prompt-only 以上
  - guard で non-target regression なし
  - source coverage 低下なし
  - visible heading template 化なし
- `one narrow hypothesis per loop` を維持する
- prompt accretion ではなく planner responsibility reduction を優先する

## Practical Conclusion

- はい、骨格の使い方を間違えていた可能性が高い
- ただし誤りは `骨格を使ったこと` ではなく、`骨格に prose の型まで持たせたこと`
- `notecode` の次の正解は
  - `prompt-only の書き味`
  - `minimum hybrid の source / role / no-hallucination rail`
  - `micro-skeleton only`
  の組み合わせだと考える
