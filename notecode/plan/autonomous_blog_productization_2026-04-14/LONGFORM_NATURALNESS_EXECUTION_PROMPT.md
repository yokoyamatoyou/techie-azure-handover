# autonomous_blog_productization_2026-04-14 LONGFORM NATURALNESS EXECUTION PROMPT

## purpose

- この prompt は `2026-04-14` 時点の current mainline に対して、`AIっぽさの低減` と `記事全体の読みやすさ改善` を最優先で進める別ウインドウ実装用である
- 現在の最大課題は `機能不足` ではなく、`短すぎる構成による硬さ / 呼吸不足 / 管理ラベル感` とみなす
- `gpt-5.4-mini` で `2000〜3000字級の explanatory_article` は十分成立しうる前提に立ち、**prompt / distilled brief / length policy** を主レバーとして扱う
- route の追加や helper accretion ではなく、既存 mainline の writer handoff を自然な日本語ブログに寄せる

## separate-window use

- 別ウインドウ起動後は、このファイルの `prompt` ブロックをそのまま使う
- default は `prompt and length policy first` であり、不要な owner 拡散を避ける
- 実装が必要なら narrow diff で進める
- same failed hypothesis unchanged retry は 3 回まで

## fixed decision for this window

- 最重要課題:
  - `AIぽい`
  - `記事全体として読みにくい`
- current interpretation:
  - short は通るが、short 前提だと explanatory と announcement に硬さが残る
  - explanatory は `2000〜3000字帯` で改善余地が大きい
  - company introduction は `900〜1500字帯` を keep し、無理に長文化しない
  - announcement は `200〜600字帯` を keep する
- strongest lever:
  - `simple_note_pipeline/ui_prompt_distillation.py`
  - `simple_note_pipeline/prompt_builder.py`
- not first lever:
  - article-type fixed routing
  - planner accretion
  - formatter-only polish
  - source-less WEB scope expansion

## reference note

- `C:\tetie\notecode\下書き.txt` を reference として読む
- 特に keep する判断:
  - `announcement = 200〜600字`
  - `company introduction = 900〜1500字`
  - `explanatory = 2200〜3500字`
  - `search-oriented explanatory = 3000〜4500字`
- ただし current window の first target は
  - `source-backed explanatory_article = 2000〜3000字で human-like に読む`

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\README.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\TASK.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\PROGRESS.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\ROLLBACK.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\VISUAL_REVIEW_EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\LONGFORM_NATURALNESS_EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\README.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\PROGRESS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\下書き.txt

今回の mission:
- current mainline の visible weakness を `AIっぽさ` と `全体の読みにくさ` に絞って改善する
- 特に `source-backed explanatory_article` を `2000〜3000字帯` で自然に読める主力カテゴリとして立て直す
- `gpt-5.4-mini` で十分書ける前提で、prompt / brief / handoff / style constraint を主レバーに使う
- route expansion や planner accretion ではなく、既存 success path の writer prompt を強くする

最重要前提:
- short battery は動く
- しかし short 前提では explanatory / announcement に visible flatness が残る
- いま必要なのは feature 追加ではなく、カテゴリ別 length policy と human-readable prompt shaping

絶対ルール:
- current success path
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を bypass しない
- source-less WEB mode を `branding/company_introduction` や `announcement` に広げない
- prompt accretion を無制限に増やさない
- hidden reviser を足さない
- same failed hypothesis unchanged retry は 3 回まで
- blocker が出たときだけ narrow owner を直す
- formatter-only の応急 polish を first remedy にしない

今回の fixed length policy:
- `announcement`
  - `200〜600字`
- `branding/company_introduction`
  - `900〜1500字`
- `daily / culture / light report`
  - `800〜1500字`
- `case_study / event / interview`
  - `1200〜2200字`
- `source-backed explanatory_article`
  - `2000〜3000字`
- `search-oriented explanatory_article`
  - `3000〜4500字`
  - ただし current window では secondary target

今回の narrow hypothesis:
- current explanatory が AIっぽく見える主因は、モデル能力不足より `short default + prompt surface不足 + 段落呼吸不足` にある
- `ui_prompt_distillation.py` と `prompt_builder.py` で
  - length policy
  - title / lead の入り方
  - current-business-first / question-first の導入
  - 段落呼吸
  - 文末変化
  - 管理ラベル感の禁止
  を明示すれば、`gpt-5.4-mini` でも 2000〜3000字帯はかなり自然になる

owner priority:
1. `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
2. `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
3. `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
4. 必要時だけ `C:\tetie\notecode\note\current_mainline_runner.py`

not first owner:
- `output_formatter.py`
- `natural_blog_core.py`
- fixed routing table
- search module split

開始直後に確認:
1. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\PROGRESS.md`
2. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\artifacts\visual_review_2026-04-14\short_matrix_summary.json`
3. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\artifacts\visual_review_2026-04-14\short\ui-short-explanatory-source-backed-acceptance.txt`
4. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\artifacts\visual_review_2026-04-14\short\ui-short-branding-company-grounded.txt`
5. `C:\tetie\notecode\下書き.txt`

最初に言語化すること:
- current artifact のどこが AIっぽいか
- 読みにくさが title / lead / paragraph breath / ending monotony / information ordering のどれに強く出ているか
- 今回の owner を 1 つに閉じる理由

実装方針:
- first diff は `prompt and brief shaping` に閉じる
- explanatory を short で無理に要約させるより、normal/long で息継ぎを作る
- title は card label や管理ラベルに見せない
- lead は `この記事では` を default にしない
- section 冒頭を同じ調子で揃えすぎない
- facts は列挙ではなく、読み物の順番へ流し込む
- must-cover は keep するが、見出しと本文の口調を硬くしすぎない

prompt shaping で強く見る点:
- explanatory:
  - `問い -> 短い結論 -> 背景 -> 判断軸 -> 実務での使い方 -> まとめ`
  - ただし見出し名を説明カード化しない
- company introduction:
  - `何をしているか -> どんな場面を支えるか -> なぜ選ばれるか -> 姿勢`
  - 沿革先行に戻さない
- announcement:
  - safety 優先
  - 文字数を伸ばして自然さを取りにいかない

human-like writing constraints:
- 導入文の2文目までに論点を置く
- 1段落1〜2文を基準にする
- 同じ文末を3連続させない
- `重要です / 必要があります` の連打を避ける
- 同じ主語や同じ名詞句を続けすぎない
- 具体と抽象を交互に置き、全部を同じ密度で説明しない
- `この記事では` `以下で解説します` `ポイントは次の通りです` のような管理語を default にしない

禁止事項:
- persona をどんどん足す
- prompt の末尾に style slogan を積み増す
- explanatory を short のまま compare だけ増やす
- 2000〜3000字帯の acceptance を見ないまま「モデル限界」と結論する

owner-local test expectation:
- touched owner に対応する focused tests を追加または更新する
- explanatory longform / human-like lead / paragraph breath を狙った narrow test が必要なら足す

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q

live verification target:
- source-backed explanatory_article を最低 1 case、`normal` または `long` で live 実行する
- company introduction を 1 case 再比較する
- announcement は regression check に留める

pass condition:
- explanatory の title / lead が管理ラベル感を減らす
- explanatory の本文が 2000〜3000字帯で段落呼吸を保つ
- visible AI feel が short baseline より改善する
- company introduction の current-business-first keep-state を壊さない
- announcement に regression がない

report 必須項目:
- 読んだ source-of-truth
- 採用した length policy
- touched owner
- hypothesis
- owner-local tests
- shared checks
- live artifact path
- explanatory の before/after 所見
- company introduction の regression 有無
- announcement の regression 有無
- unresolved risk
- rollback要否
```
