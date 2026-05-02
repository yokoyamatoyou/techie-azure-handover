# UI Left Column Simplification 2026-04-14

更新日: 2026-04-14
対象:
- `C:\tetie\notecode\note\note_writer_app.py`

## 目次

1. Purpose
2. Evidence Lock
3. Current Problem
4. Keep / Remove
5. New UI Spec
6. Runtime Mapping
7. Minimal Diff Plan
8. Non-Goals

## Purpose

- 左カラムを `複雑な algorithm を見せる UI` ではなく、`prompt 主導 + minimal hybrid + 生成前チェック` の current official state に合わせて縮退する
- current success path を壊さず、本文生成アルゴリズムの複雑化なしに、入力から生成までの視線誘導を明確にする
- `現在の設定メモ` と常設 `AIからの確認` を主導線から外し、`入力 -> 生成前チェック -> 生成` を main route に戻す
- 生成結果は右常設カラムではなく main route の下部へ置き、生成完了後にそこへ自然に移動させる

## Evidence Lock

- `prompt-only / simpler default` は local compare 上で algorithm tuning accumulation より優勢だった
- ただし current official state は `full prompt-only immediate cutover` ではない
- current keep state は
  - `grounded generic default`
  - `planning opt-in only`
  - `prompt strategy winner`
  - `minimal hybrid / prompt-led current mainline`
  である
- よって UI も `複雑な route 説明` ではなく `短い task / core input / minimal confirmation` を前面に置く

根拠:

- `plan\naturalness_recovery_2026-04-07\README.md`
  - `prompt-only = floor`
  - `skeleton / planning = conditional signal only`
  - `article-type fixed routing table` 非採用
- `plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `grounded generic default`
  - `planning / skeleton route = opt-in`
- `docs\separate_window_initial_prompt_2026-04-11_prompt_only_compare5.md`
  - `best practice = minimal hybrid`
  - `full prompt-only immediate cutover` 非採用
- `docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md`
  - stable winner は `prompt strategy`
  - add より `replace / compress`

## Current Problem

- 左カラムに block が多く、`今どこを決めれば生成できるか` が一目で分かりにくい
- `現在の設定メモ` は runtime に効かないが、主導線の途中で attention を奪う
- `AIからの確認（任意）` は常設だと、質問が必要でないケースでも「何かしないと足りない」印象を作る
- 生成ボタンは runtime 上は `記事を生成` が本線なのに、未確定時の説明を button text 側へ背負わせすぎている
- `生成前チェック` 自体は current runtime reality に接続しているが、その価値が周辺 UI に埋もれている

## Keep / Remove

### Keep

- `STEP 1` の `開始方式 + 1行テーマ + 資料入力`
- `STEP 2` 内の `journey purpose / target` による article type resolution
- `生成前チェック`
  - confirm preview
  - source fit
  - grounding status
  - missing inputs
- role clarity keep state
  - company introduction の `自動（おすすめ） / 企業広報として語る`
  - `運営側` のような曖昧 role label を戻さない
- `補助設定` に入っている runtime-connected controls
  - `writing_focus`
  - `pattern`
  - `branding subtype / focus`
  - `allow_experience`
  - `length_mode`

### Remove / Demote

- `現在の設定メモ`
  - display only
  - runtime owner ではない
  - 主導線から削除する
- 常設 `AIからの確認（任意）`
  - default 表示しない
  - unresolved slot / clarify 必要時だけ conditionally 出す
- generate button text による長い状態説明
  - button は基本 `記事を生成`
  - 生成不可理由は補助テキストへ移す

## New UI Spec

左カラム block は 3 つまでに固定する。

### Block 1: 入力

タイトル:
- `入力`

含める要素:
- 開始方式
- 1行テーマ
- 資料入力
- 記事の向き先
  - `どこに出すか`
  - `何を書くか`
  - 比較時のみ `比較条件`

表示ルール:
- 開始方式の初期導線は `資料あり / お任せ` を基本とし、旧 `続編` は入口UIの常設選択肢に戻さない
- `どこに出すか` と `何を書くか` は 1 card にまとめ、体感 step 数を増やさない
- `比較条件` は `comparative_review` のときだけ表示
- 資料入力は `grounded / followup` のとき表示
- `omakase` 判定カードは `source_mode = web` のときだけ表示

意図:
- prompt 主導の入口を最上段に固定する
- `journey` は article type routing explanation ではなく、読者向けの向き先選択として見せる
- `SaaS` `current mainline` `free text` のような implementation 語は UI 本文に出さない
- URL入力とファイル追加は初回表示で見せるが、空の一覧や大型アップローダーで Step 2 を画面外へ押し出さない

### Block 2: 生成前チェック

タイトル:
- `生成前チェック`

含める要素:
- 選択内容の短い要約
- source fit
- grounding status
- missing items
- confirm actions
  - `内容を確認`
  - `この内容で確定`
- CTA
  - `記事を生成`
- 補助テキスト
  - 生成可能
  - 未確定
  - ソース不足
  - お任せ preflight 保留

表示ルール:
- 常時表示する
- `確認が必要な項目` の補助カードは次の場合だけ表示
  - preview / question policy で unresolved slot がある
  - clarify が必要
  - user が確認項目表示を実行した後
- `AIからの確認` という固定見出しは使わない
- 質問が不要なときは質問 UI を出さない

CTA ルール:
- button 文言の第一候補は常時 `記事を生成`
- disabled 時も button 文言は極力変えず、理由は下の hint text へ出す
- 例外:
  - `omakase AUTO_SOURCE_READY` のみ current runtime reality を優先し、`材料判定を進める` を許可

不足情報時の表示:
- 直接入力で補うべき場合:
  - amber text で `上の入力欄を補ってから再確認`
- question item で補える場合:
  - conditionally `確認が必要な項目` card を出す
  - button: `確認項目を表示`
- confirm 未実施の場合:
  - `まだ確定されていません。内容を確認して確定してください。`

### Block 3: 詳細設定

タイトル:
- `詳細設定`

含める要素:
- 本文の重心
- 文章の運び
- branding subtype / focus
- 体験談許可
- 記事の長さ

表示ルール:
- default collapsed
- branding 固有項目は branding 時のみ展開中に表示
- custom genre 管理は current 非表示運用を継続

意図:
- runtime には効くが main route ではない controls を閉じ込める

### Result Surface

配置:
- 右常設カラムに固定しない
- `生成前チェック` の下に続く結果セクションとして配置する

表示ルール:
- 生成前は placeholder のまま低主張で待機
- 生成完了後に smooth scroll で結果セクション先頭へ移動する

意図:
- 右カラムへの大きな視点移動をやめる
- `生成ボタンの直後に結果を見る` という因果を強くする

## Runtime Mapping

runtime に効く:

- `source_mode`
- `user_prompt`
- `sources`
- `journey purpose / target / comparison_axes`
- `content_goal`
- `speaker_profile`
- `audience_profile`
- `tone_profile`
- `core_message`
- `self_reference_policy`
- `writing_focus`
- `pattern_key`
- `branding_subtype_key`
- `branding_focus_key`
- `allow_experience`
- `length_mode`
- conditional question answers
- confirm signature / preview

display only:

- `現在の設定メモ`
- `question_policy_copy` の常設表示
- button 文言での長い理由説明

mixed:

- `AIからの確認`
  - question policy 自体は runtime connected
  - ただし常設 block は display layer choice にすぎない
  - したがって function は keep しつつ、surface は conditional に下げる

## Minimal Diff Plan

owner file:
- `C:\tetie\notecode\note\note_writer_app.py`

diff order:

1. `補助設定` を `詳細設定` に改名
2. `現在の設定メモ` block を削除
3. `AIからの確認（任意）` 常設 expansion を廃止
4. 生成前チェック配下に `確認が必要な項目` の conditional container を置く
5. generate CTA を `記事を生成` 基本へ寄せ、不可理由は hint text へ寄せる

reuse points:

- `build_current_mainline_confirm_preview()`
- `build_journey_confirm_preview_view_core()`
- `assess_current_mainline_question_policy()`
- `_build_generate_gate_surface()`
- 既存 `load_interview_questions()` 実装

implementation rule:

- algorithm owner は触らない
- new route / hidden reviser / planning default は入れない
- left column surface だけを thin にする

## Non-Goals

- `prompt-only winner` へ full cutover すること
- `planning / skeleton default` を UI から再正当化すること
- `現在の設定メモ` の文言を増やして延命すること
- `AIからの確認` を常設のまま残すこと
- article-type fixed routing table を足すこと
- prompt accretion / module accretion
- current success path の変更
