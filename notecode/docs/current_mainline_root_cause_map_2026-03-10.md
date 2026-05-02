# current mainline Root Cause Map

更新日: 2026-03-10  
対象: `notecode` current mainline

## 1. 衝突マップ

| 層 | 旧状態 | 衝突内容 | 症状 | 根本原因 | 今回の処置 |
|---|---|---|---|---|---|
| UI | `structure` を選ばせる | current mainline では実質未使用 | 選択肢過多、意味の重複 | UI が runtime 契約とずれていた | UI から削除し、内部は `auto` 固定 |
| input_contract | `topic` / `topic_statement` / `must_cover` / `prompt_context_items` が同時に主題を保持 | 同じ要求を別表現で重複注入 | title/lead の硬さ、本文の prompt echo | 契約の正本が複数あった | `focus_bundle.main_focus` を正本化 |
| source grounding | 礼儀文やメタ行も候補化 | 低信号文が事実アンカーに混入 | 終盤のメタ文、会社紹介の不自然さ | source facts の抽出粒度が粗かった | courtesy / meta / CTA 行を除外 |
| discourse plan | must_cover と lens を節ごとに追加注入 | 論点より契約追従が強くなる | 文頭単調、主語過多、論点の詰め込み | 談話計画が過密 | `main_focus + support_points` のみで配分 |
| section prompt | 長い prompt、否定制約が多い | style / contract / guard の要求が同時に乗る | 硬い導入、反復、AIっぽい締め | 主命令が過密 | `28行以内 / 否定制約4個以内` に圧縮 |
| formatter | audience prefix / role template 依存 | 本文ではなく契約文を title/lead 化 | `一般読者に伝えたい`、`として語るとして` | formatter が contract boilerplate を優先 | body + source facts 優先へ変更 |
| guard | anchor coverage / must_cover reflection を hard block 寄りで扱う | 自然さより契約追従を優先 | 追従過多の硬さ、再試行圧 | guard の責務過大 | safety と明確な逸脱だけ hard block |

## 2. UI入力項目と内部契約の対応

| UI入力 | 内部契約 | 現在の扱い |
|---|---|---|
| 記事タイプ | `article_type` | 正本 |
| 目的 | `content_goal` | 正本。ただし長い must_cover は作らない |
| 本文の重心 | `writing_focus` | style hint のみ |
| 語り口トーン | `tone_profile` | style hint のみ |
| 体験談許可 | `allow_experience` | quality / style 補助 |
| 話者 | `speaker_profile` | 正本 |
| 読者 | `audience_profile` | 正本 |
| 核メッセージ | `core_message` | `focus_bundle.support_points` の候補 |
| 指示文 | `prompt_raw` / `topic` | 生ログ保存用。主命令には再掲しない |
| source | `source_documents` / `source_grounding_items` | 会社紹介時の事実正本 |
| 構成 | `structure` | current mainline では `auto` 固定 |

## 3. AIっぽさの主因

- 主因1: 契約の重複保持。主題が `topic` / `topic_statement` / `must_cover` / `formatter` で増幅していた。
- 主因2: low-signal source facts。礼儀文と事実文を同じ重みで拾っていた。
- 主因3: prompt 過密。文体、禁止事項、契約、構成が section prompt に同時注入されていた。
- 主因4: formatter の契約直写し。title/lead が本文ではなく contract boilerplate 由来だった。
- 主因5: guard の過剰拘束。自然な本文でも coverage 指標で hard stop しやすかった。

## 4. 除外した一次原因

- `semantic_dedupe`
- `Human Resonance`
- sampling parameter

上記は観測上の差分要因ではあるが、current mainline の硬さや prompt echo の一次原因ではなかった。

## 5. 最小簡素化案と実装結果

- `focus_bundle` を追加し、`main_focus` を第1正本へ統一した。
- `must_cover` は最大3件の短いアンカーへ縮小した。
- `prompt_context_items` は最大1件の具体文脈だけ残すようにした。
- section prompt から `system_hint_items` / `retry_memo` の主命令注入を外した。
- title/lead は本文と source facts を優先し、契約テンプレート依存を外した。
- guard は prompt echo / forbidden topic / speaker drift / legal / input不足を hard block とし、それ以外は soft warning へ移した。
- UI は `structure` を外し、Hick の法則に反する余剰選択を削った。

## 6. Nielsen / Hick 確認

- `structure` 選択は可視性より認知負荷が勝っていたため削除した。
- primary input は `article_type / content_goal / speaker / audience / core_message(条件付き)` に寄せた。
- `writing_focus / tone / allow_experience` は詳細設定へ残し、主契約を増やす用途から外した。
- current mainline の explainability は `pipeline_check.focus_bundle` と `contract_trace` に集約した。

## 7. 検証メモ

- offline fixed cases:
  - branding `topic_echo_body_only_ratio: 1.0 -> 0.1667`
  - industry_analysis `1.0 -> 0.3333`
  - case_study `1.0 -> 0.4286`
  - announcement `1.0 -> 0.2857`
- live API small set:
  - branding: `success=true`, `retry=0`, `fallback=false`, title=`導入初期の運用の迷いを減らす価値`
  - case_study: `success=true`, `retry=0`, `fallback=false`, title=`オンボーディング初回設定の案内導線を見直した事例`
  - announcement: `success=true`, `retry=0`, `fallback=false`, `announcement_invalid_modal_pattern_count=0`
