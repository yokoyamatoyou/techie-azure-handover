# current mainline codex prompt — 段落 burstiness 調査結果を踏まえた次ステップ

更新日: 2026-03-31
用途: Codex セッションでそのまま貼る prompt。03-30 Web 調査結果を踏まえて single residual を選ぶ

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md

今回の実施範囲:
- current mainline の kept state を再確認したうえで、03-30 Web 調査で得た定量根拠をもとに single residual を 1つ選び、single hypothesis / owner-local で 1 つだけ試す
- 調査結果は「補助根拠」として使う。調査結果だけで判断せず、local artifact と code を必ず再確認する
- prompt accretion / module accretion を避ける
- simple_note_refactor_2026-03-22 は reopen しない

前提:
- current success path は
  C:\tetie\notecode\note\current_mainline_runner.py
  -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  -> super().generate(...)
  -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- completed 済み simple single-pass refactor は凍結扱い
- UI taxonomy は current kept state（8分類/7種固定）
- comparative の source-grounding 増強仮説は rollback 済み
- announcement の局所文法崩れは narrow fix を keep 済み
- human_resonance 本体は初手では触らない

## 03-30 Web 調査で得た定量根拠（要約）

### 段落長の変動係数（CV）が異常に低い

local output の段落長を計測した結果:

| ジャンル | 段落数 | 平均字数 | min | max | CV |
|----------|--------|----------|-----|-----|-----|
| announcement | 9 | 78 | 31 | 107 | 0.36 |
| explanatory (short) | 18 | 104 | 22 | 132 | 0.29 |
| industry | 17 | 104 | 32 | 144 | 0.29 |
| casestudy | 8 | 55 | 31 | 105 | 0.54 |
| comparative | 20 | 89 | 25 | 132 | 0.38 |
| explanatory (normal) | 20 | 135 | 12 | 174 | 0.30 |

- explanatory / industry / phase2 の CV=0.29-0.30 は「ほぼ全段落が同じ長さ」を意味する
- AI 検出研究（arXiv:2505.01800, Hastewire 2025-11）では「burstiness の欠如＝段落長の均一性」が最強の AI 検出シグナルの一つ
- 人間の文章の CV は 0.5 以上が典型
- note の編集実務（noteヘルプセンター, パーソナル編集者 2025-12）は「短い導入段落→長い説明段落→短い転換段落」の揺れを推奨
- 日本語圏でも「AI が等間隔で改行する癖」は認識されている（渡里左衛子 2026-01-27: 「思考の段差を機械的に刻む」vs「文として流れていく文章」）

### 改善方向は「段落を長くする」ではなく「段落長の分散を広げる」

- Web 編集実務の主流（NNGroup, STUDY HACKER, 株式会社ダンク）は「削る＞足す」で一致
- 水増しは可読性・自然さ・信頼感を損なう
- 正しい方向は「短い段落（1文, 30-50字）と長い段落（4-5文, 150字超）を意図的に混在させる」こと

### comparative generic tail は outline brief の薄さが原因

- comparative 末尾3段落が 39, 38, 47 字の generic 文（「候補Aが向きやすく」等）
- 比較記事の編集実務（桜御前 2023/更新2025）は「○○する人には△△がおすすめ」の形で用途別の具体結論を求める
- 原因は source 不足ではなく outline 段階で末尾セクション brief が薄いこと

## 調査が示す narrow suggestion 3件（優先順）

### Suggestion 1: 段落長 burstiness の後処理導入（推奨: 最初に試す）

- hypothesis: LLM 出力後の後処理段階で、段落長の CV が 0.35 未満のセクションに対し、最短段落を1文に切り詰め（30-50字）、隣接する段落を結合で150字超にする。これにより CV を 0.4-0.5 に引き上げ、等間隔リズムを崩す
- likely owner file: C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py の _add_note_sentence_linebreaks() 付近、または同レイヤーの後処理
- why this is owner-local: 段落の結合/分割は LLM 出力後の文字列操作。prompt 変更なし。既存の _add_note_sentence_linebreaks() と同レイヤー
- why this is not prompt accretion: prompt への指示追加ではなく後処理ロジック。LLM prompt は一切変えない
- expected risk: 低。段落境界の移動のみ。文の追加/削除/書き換えは行わない。テストで CV を計測して効果検証可能
- success 判定: 処理後の段落長 CV が 0.40 以上に上がり、かつ人間読みで不自然な切断がないこと
- rollback 判定: CV 操作で文脈が切れる（意味の途中で段落が割れる）場合は即 discard

### Suggestion 2: 見出し直下リード段落の1文制限

- hypothesis: 各セクションの最初の段落を1文（40-60字）に制限し「導入→詳細」のリズムを作る。これだけで CV が上がり、見出し直下の density pattern が自然になる
- likely owner file: _add_note_sentence_linebreaks() 付近
- why this is owner-local: セクション先頭段落の文字数制限は後処理で可能
- why this is not prompt accretion: prompt 変更なし
- expected risk: 低。セクション冒頭の1文だけが対象

### Suggestion 3: comparative outline brief 末尾セクション具体化

- hypothesis: comparative の最終2-3セクション brief に「具体的な条件名と結論文を含めること」を要求する制約を outline テンプレートの comparative 分岐に追加
- likely owner file: C:\tetie\notecode\note\mixins\outline_mixin.py の comparative 分岐
- why this is owner-local: outline テンプレートの comparative 条件のみ。他ジャンルに影響しない
- why this is not prompt accretion: 既存の outline prompt 内の comparative 条件を修正するだけ。新規 prompt 追加ではない
- expected risk: 中。outline 変更は下流に影響するが comparative 限定
- 注意: source-grounding 強化仮説の再投入ではない。outline brief の情報密度の問題

## 調査が示す禁止事項 3件

1. 全段落を一律に長くする試み → 水増しは Web 実務の禁忌。平均を上げるのではなく CV を上げる
2. prompt に「段落の長さを変えろ」と指示する → prompt accretion。LLM は別の均一パターンに収束するだけ
3. comparative の source-grounding 強化仮説の再投入 → rollback 済み。generic tail の原因は source 不足ではなく outline brief の薄さ

## single residual の選択

- 03-30 handoff では「comparative_review の薄さ」を第一候補としていた
- 03-30 Web 調査により、「段落長 CV の低さ」が comparative だけでなく全ジャンル共通の残差であり、かつ AI 検出シグナルに直結することが判明した
- したがって、single residual の候補を以下の優先順で提示する:
  - 第一候補: 段落長 burstiness（Suggestion 1）— 全ジャンル共通の残差。後処理のみ。risk 最小
  - 第二候補: comparative generic tail（Suggestion 3）— comparative 限定の残差。outline 修正
- どちらを先に試すかは Codex の判断に委ねるが、Suggestion 1 の方が risk が小さく、効果が cross-genre に及ぶため推奨

current kept state:
- keep 済み変更（03-30 と同じ）
  - UI taxonomy 対応
    - C:\tetie\notecode\note\note_writer_app.py
    - C:\tetie\notecode\note\current_mainline_runner.py
    - C:\tetie\notecode\note\current_mainline_profile_resolver.py
  - announcement 句切れ修正
    - C:\tetie\notecode\note\newalgorithm_pipeline\editor_guard.py
    - C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
- discard / rollback 済み
  - comparative の source-grounding 強化仮説

開始時に必ず確認するファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode\docs\current_mainline_quality_status_2026-03-23.md
6. C:\tetie\notecode\docs\simple_note_refactor_status_2026-03-23.md
7. C:\tetie\notecode_current_mainline_handoff_2026-03-30.md

開始時に必ず確認する最新 artifact:
1. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-cross-genre-shortmid-2026-03-30\ 配下の各 txt
2. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-ui-taxonomy-check-2026-03-30\summary.json
3. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-announcement-final-normalize-fix-2026-03-30\summary.json

開始時の既定手順:
1. 上記ファイルと artifact を読み、kept state が崩れていないことを確認する
2. announcement kept fix の保持を確認する
3. comparative rollback 済み状態を確認する
4. Suggestion 1（段落 burstiness 後処理）を試す場合:
   a. _add_note_sentence_linebreaks() のコードを読む
   b. 同レイヤーに段落長 CV を計測し、CV < 0.35 の場合に短段落/長段落を作る後処理を追加する
   c. 処理対象は LLM 出力後・最終整形前
   d. explanatory 1 case で targeted recheck し、CV が 0.40 以上に上がることを確認する
   e. 人間読みで不自然な切断がないことを確認する
5. Suggestion 3（comparative tail）を試す場合:
   a. outline_mixin.py の comparative 分岐を読む
   b. 末尾セクション brief に「条件別の具体結論を含めること」を追加する
   c. comparative 1 case で targeted recheck し、末尾段落の情報密度を確認する

固定ルール:
- 1ターンで扱う residual は 1つだけ
- 1ターンで立てる hypothesis は 1つだけ
- 触る owner file は最大 2 ファイル
- prompt accretion をしない
- module accretion をしない
- failed hypothesis は即 discard し、採用状態を再固定する
- comparative と announcement を同時に触らない
- 段落を一律に長くしない（CV を上げる方向のみ許可）
- prompt に「段落の長さを変えろ」と指示しない

success 条件:
- current success path と kept state を崩していないことを確認できる
- announcement kept fix が code / artifact の両方で保持されている
- comparative rollback 済み仮説が再投入されていない
- Suggestion 1 を試した場合: 処理後 CV >= 0.40 かつ文脈切断なし
- Suggestion 3 を試した場合: 末尾段落に条件別具体結論が含まれている

rollback 条件:
- prompt を長くしないと成立しない仮説だった場合
- module を増やさないと成立しない仮説だった場合
- announcement kept fix に regression が見つかった場合
- CV 操作で文脈が切れる（意味の途中で段落が割れる）場合
- owner file が 2 を超える見込みになった場合

やってはいけないこと:
- simple_note_refactor_2026-03-22 を reopen すること
- prompt を長くして帳尻を合わせること
- module を増やして見かけ上の正しさを作ること
- comparative の rollback 済み source-grounding 強化仮説をそのまま再投入すること
- 全段落を一律に長くすること（水増し）
- prompt に「段落長を揺らせ」と指示すること（prompt accretion）
- external review 未確認のまま全面移行を宣言すること

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- current kept state
- discard 済み仮説
- 今回選んだ single residual
- 試した hypothesis と結果
- 処理前後の段落長 CV（Suggestion 1 の場合）
- owner file
- success / rollback どちらに該当したか
- AGENTS / WORKLOG 更新の有無
```
