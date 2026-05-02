# separate window management memo deepresearch reflection 2026-04-17

## Position

- この文書は current source-of-truth ではない
- `naturalness_recovery_2026-04-07` package を上書きしない
- Claude Opus 4.7 deepresearch と current local evidence を management 観点で圧縮した memo として扱う

## Current Judgment

- current keep-state は維持する
  - `grounded generic default`
  - planning は `opt-in only`
  - `single-pass + optional single repair 1回`
  - blank company intro の best current line は `prompt_builder.py` の `current-business-first keep line`
- current source-of-truth / AGENTS / WORKLOG / package docs はまだ更新しない

## Deepresearch Takeaway

- `reference realization policy` は日本語 NLP 的に部分的には妥当
- ただし current framing のままでは強く推さない
- とくに `subject_reintroduction_policy` は、
  日本語の zero pronoun / topic continuity と衝突する可能性が高い
- `speaker_reference_policy` は残す余地があるが、
  英語的な overt reintroduction ではなく
  register-gated / exophoric speaker slot として再設計したほうが筋がよい
- `proper_noun_repeat_cap` は directionally right だが、
  hard integer cap としては弱い

## Priority Shift

- 次の first candidate は
  - `sentence-final pattern monotony cap + single repair`
  とする
- 理由:
  - 日本語特有の visible AI-feel と接続しやすい
  - current package の symptom と整合する
  - `single-pass + optional single repair 1回` にそのまま乗る
  - owner-local / rollback-first / feature-flag friendly

## What Changes In Priority

### Up

- 文末 monotony / sentence-final variation
- paragraph-local monotony detection
- bounded single repair

### Down

- `reference realization policy` の production priority
- section-level `subject_reintroduction_policy`

### Keep As Separate Evidence

- `reference realization policy` compare line
- company name / `私たち` / `当社` / subject omission の重要性

## What Not To Do

- `reference realization policy` compare を current source-of-truth に昇格しない
- `article-type fixed routing table` に逃げない
- `planning default` を再主張しない
- `prompt-only winner` を断定しない
- formatter / input_contract に責任を逃がさない
- mock path pass を visible improvement の代わりに使わない

## Near-Term Working Order

1. current compare docs は evidence として keep
2. next separate line は `sentence-final monotony cap + single repair` の research / planning へ寄せる
3. `reference realization policy` は compare が終わるまで separate evidence のまま止める
4. management judgment が揃うまで production owner を開かない

## Immediate Conclusion

- current direction を全面否定する必要はない
- ただし次の main candidate は入れ替える
- `reference realization policy first`
  ではなく
- `sentence-final monotony first, reference realization later if still needed`
  を暫定方針とする

