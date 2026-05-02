# グループA完了判定用 指示文パック

更新日: 2026-03-11  
対象: `C:\tetie\notecode` current mainline

## 使い方

- 新しいウィンドウで使う前提の送信用指示を 3 本に分けている。
- 推奨順序は `調査専用版` -> `実装専用版` -> `外部比較専用版`。
- いずれも `notecode` 配下のみ対象。`aio2-main` には広げない。

## 共通前提

- 参照ルールファイルは `C:\tetie\AGENTS.md`, `C:\tetie\WORKLOG.md`, `C:\tetie\notecode\ALGORITHM.md`。
- 対象は `notecode` の current mainline のみ。
- `2026-03-11` のグループA実装は投入済み前提で、今回は完了扱いにできるかの確認が目的。
- phase06 で既に `keep-for-compat` / `keep-observe` と分類済みの資産は、`notecode/puran6/phase06_artifacts_2026-03-07.md` を初期除外ラインとして扱う。
- 最新のローカル証跡では fail-closed 自体は動作しており、直近ログは `2026-03-10 21:08:32` の `POL_PROMPT_ECHO` block と `source_grounding_reflection_ratio=0.1667` が残課題候補。
- archive 退避は動線確認後だけ行う。確認前に移動しない。
- 1 回の実装は最優先 1 件だけに限定する。

---

## 調査専用版

```text
参照ルールファイル: C:\tetie\AGENTS.md, C:\tetie\WORKLOG.md, C:\tetie\notecode\ALGORITHM.md
今回の実施範囲: WORKLOGのグループAの残作業確認と完了判定

対象は notecode の current mainline のみです。aio2-main には広げないでください。
2026-03-11 の「グループA実装」は入っている前提で、今回はグループAを完了扱いにできるかを確認し、不足分があれば最小単位で埋める前提を固めてください。

最初のターンではコード変更を急がず、まず以下を調査・整理してください。
- 未使用モジュールの棚卸しと archive 候補分類
  - ただし `notecode/puran6/phase06_artifacts_2026-03-07.md` の `keep-for-compat` / `keep-observe` は既知の除外ラインとして先に確認し、既済分類を掘り返さないでください
  - 棚卸し結果は `current runtime` / `keep-for-compat or keep-observe` / `archive候補` の3区分で整理してください
- current mainline の prompt / UI / contract / formatter / guard の内部競合の残り
- prompt injection 耐性、入力サニタイズ、fail-closed / fail-open 境界の残り
- セクション単位の意味重複、終盤のメタ文混入、UI選択と出力 personalization 一致の残り
- latest_generation_output.json、generation_audit_log.jsonl、latest_generation_quality_report.json を使った現状確認
  - 直近ログでは `POL_PROMPT_ECHO` と `source_grounding_reflection_ratio=0.1667` が見えているため、事実かどうかを再確認してください
- WORKLOGに未記載の「除外した仮説」「最小修正方針」の明文化
- 可能なら外部比較の必要性と実施範囲の切り分け
  - ただし今回は比較実行までは進めず、必要性判断と比較設計までに留めてください

出力は必ずこの順で出してください。
- すでに完了している点
- 未完了の点
- 根本原因
- 除外した仮説
- 最小修正方針
- 1件ずつの実施順序
- 今回触らない範囲
- WORKLOG追記文案

制約:
- 一度に全部直さない
- 初回ターンは調査と整理だけに固定する
- 1回の実装は最優先1件だけ
- notecode 配下のみ触る
- archive 退避は動線確認後だけ
- 実装したら必ず検証まで行う
- WORKLOG更新は「原因確定 + 修正 + 検証」が終わった小タスクだけ追記する
```

---

## 実装専用版

```text
参照ルールファイル: C:\tetie\AGENTS.md, C:\tetie\WORKLOG.md, C:\tetie\notecode\ALGORITHM.md
今回の実施範囲: WORKLOGのグループAの残作業確認と完了判定

前回の整理結果に基づき、最優先の未完了1件だけ実装してください。
対象は notecode の current mainline のみです。aio2-main には広げないでください。
他の論点には広げず、今回の1件だけを完了条件まで進めてください。

変更前に、次の4点を短く示してください。
- 対象ファイル
- 根本原因
- 除外した仮説
- 最小修正方針

実装時の制約:
- 一度に全部直さない
- 1回の実装は最優先1件だけ
- notecode 配下のみ触る
- archive 退避は動線確認後だけ
- phase06 で既に `keep-for-compat` / `keep-observe` と整理済みの資産は、直接の根拠がない限り今回の修正対象にしない

実装後は必ずテストまたは再現確認を行ってください。
最後に次を出してください。
- 実施した修正の要点
- 実行した検証
- 検証結果
- 今回は触らなかった論点
- WORKLOG.md へ追記する文案

WORKLOG追記文案は、「原因確定 + 修正 + 検証」が終わったこの小タスクだけに限定してください。
```

---

## 外部比較専用版

```text
参照ルールファイル: C:\tetie\AGENTS.md, C:\tetie\WORKLOG.md, C:\tetie\notecode\ALGORITHM.md
今回の実施範囲: グループAの外部比較フェーズの切り出し

ローカル確認が終わったら、グループAの「外部比較」を別フェーズとして切り出してください。
対象は notecode の current mainline のみです。aio2-main には広げないでください。

今回は比較実行までは行わず、以下だけを決めてください。
- 比較観点
- 比較対象
- 評価基準
- 実施順序
- 今回はまだ実行しない理由

比較設計では、まずローカルの固定比較導線を前提にしてください。
- `C:\tetie\notecode\evaluate_newalgorithm_cases.py`
- offline 固定ケースを先、live や外部公開AI比較は後

整理時の観点:
- AIっぽさ
- prompt echo / メタ文
- 意味重複
- personalization 一致
- source grounding の反映
- fail-closed で止めるべき問題と、比較観察に回すべき問題の境界

出力は次の順で出してください。
- 外部比較を切り出す理由
- 比較観点
- 比較対象
- 評価基準
- 実施順序
- 今回は実行しない範囲
- 次ターンで使う実施指示文
```
