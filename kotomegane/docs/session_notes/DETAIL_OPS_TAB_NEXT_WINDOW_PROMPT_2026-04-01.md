# Detail/Ops Tab Next Window Prompt

## 参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\kotomegane\AGENTS.md`

## 今回の実施範囲

- `kotomegane` の `詳細を見る > 運用` まわりを、非エンジニア向けにさらに再設計する
- 対象は `kotomegane` のみ
- 機能追加はしない
- backend の batch / schedule / import の仕組みは維持し、表現と情報構造を見直す
- このファイル自体は次ウインドウで使う指示プロンプトであり、plan ファイルは編集しない

## 背景

主画面は `入力 -> 分析を実行 -> 結果` の最小導線へかなり寄せたが、`詳細を見る > 運用` はまだコンテキスト圧迫が大きい。

特に次が残課題:

- `一括実行` が非エンジニアに意味不明
- `Batch` / `job` / `import` の内部語が残っている
- `質問セット / 定期チェック / まとめて確認 / 履歴 / 出力 / モデル` が同じ密度で並び、優先順位が伝わりにくい
- 説明文を読んでも理解しにくい
- 将来拡張の provider 情報が主役化しやすい

## 事前に読む

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\kotomegane\AGENTS.md`
3. `C:\tetie\kotomegane\README.md`
4. `C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md`
5. `C:\tetie\kotomegane\app.py`
6. `C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md`
7. `C:\tetie\aio2-main\AGENTS.md`
8. `C:\tetie\kotomegane\docs\research\deep-research-report (13).md`

## 直近の前提

- 主画面の `結果を見る` は、実行後だけ表示する方針
- 青系のボタン/進捗色は使わない
- `接続先` は大きなカードではなく、小さなモデル表示に寄せる
- UI 表示名は `OpenAI` ではなく `ChatGPT` を優先する
- `Claude / Gemini / Perplexity` は非アクティブ表示でよい
- batch backend は残すが、表面では内部実装語を減らす

## ローカル参照から引くべき共通方針

- `techie-hub` 共通方針:
  - 最初に見せる主要判断は 3 つまで
  - 高度な設定は初期表示しない
  - `入力 / 主結果 / 詳細 / 運用` の順序を崩さない
- `aio2-main` の寄せ方:
  - 主画面は URL 入力と要約を先に見せる
  - 固定テンプレ説明は常設しない
  - 補足は必要箇所だけに退避する
- `kotomegane` の残課題:
  - 運用タブだけ、SaaS の主操作より「実装機構の説明」に寄っている

## 海外SaaSの観察から守るべき言い換え

SEO / AIO / AI visibility 系SaaSでは、次の表現が多い:

- `Project`
- `Scheduled checks`
- `Monitoring`
- `Reports`
- `History`
- `Model coverage`
- `Mentions`
- `Citations`

逆に、前面に出しにくい語:

- `batch`
- `job`
- `import`
- `endpoint`
- `provider adapter`
- `runtime`

つまり、「どう実装しているか」ではなく「何が起きるか」でラベルを付けること。

## このウインドウでやってほしいこと

1. `詳細を見る > 運用` の情報を棚卸しし、主役と脇役を分ける
2. 非エンジニア向けに語彙を再命名する
3. 同じタブに置くべきものと、別タブまたは二段階開閉へ逃がすべきものを分ける
4. `batch` backend は残したまま、表面ラベルを `まとめて確認` 系へ統一する
5. `質問セット / 定期チェック / まとめて確認 / 履歴 / 出力 / モデル` の優先順を設計する
6. `ChatGPT` を主表示、`Claude / Gemini / Perplexity` を非アクティブの弱い補助表示にする
7. 説明を増やさず、余白・順序・折りたたみで理解させる
8. 実装後は `app.py` 構文確認と desktop/mobile の確認を行う

## 絶対にしないこと

- 新機能追加
- backend の batch 機構の削除
- plan ファイルの編集
- `aio2-main` / `notecode` への変更
- 英語の内部語を UI 前面へ戻すこと
- 青系アクセントの再導入
- 説明カードを足して理解させようとすること

## 成果物

- `app.py` の必要最小限のUI再整理
- 必要なら `README.md` と `docs/CURRENT_STATE_2026-03-30.md` の最小同期
- 完了報告では次を必ず示す
  - 何を主役から外したか
  - 何をどう言い換えたか
  - どのSaaSパターンに寄せたか
  - 何を別タブ/別開閉に逃がしたか
  - 実施した検証

## 実行用プロンプト

以下を次ウインドウへそのまま貼ってください。

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md

今回の実施範囲:
- kotomegane の `詳細を見る > 運用` を、非エンジニア向けの最小構成へ再設計する
- 対象は kotomegane のみ
- 機能追加はしない
- plan ファイルは編集しない

必ず最初に読む:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md
- C:\tetie\kotomegane\README.md
- C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
- C:\tetie\kotomegane\app.py
- C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md
- C:\tetie\aio2-main\AGENTS.md
- C:\tetie\kotomegane\docs\research\deep-research-report (13).md

背景:
- 主画面はかなり削れたが、`詳細を見る > 運用` がまだ重い
- `一括実行` は非エンジニアに伝わりにくい
- batch/job/import など内部実装語が残っている
- `質問セット / 定期チェック / まとめて確認 / 履歴 / 出力 / モデル` の優先順位が伝わりにくい
- 接続先は `ChatGPT` を主表示、`Claude / Gemini / Perplexity` は非アクティブ表示でよい

デザイン判断基準:
- Nielsen 10 Heuristics
- Hick's Law
- progressive disclosure
- recognition over recall
- Notion っぽい静けさ
- Google 的な即読性
- ただし kotomegane の暖色ブラウン / ベージュ / オレンジは維持

海外SaaSから寄せる方向:
- SEO/AIO/AI visibility 系でよく使う語は `Project`, `Scheduled checks`, `Monitoring`, `Reports`, `History`, `Model coverage`
- `batch`, `job`, `import`, `endpoint` のような内部語は主画面に出さない
- 「どう実装しているか」ではなく「何が起きるか」でラベルを付ける

このウインドウでやること:
1. 運用タブの現状を棚卸しする
2. 主役と脇役を分ける
3. `一括実行` を非エンジニア向けの語へ再整理する
4. 同じタブに残すものと、別タブまたは二段階開閉へ逃がすものを決める
5. 余白・順序・折りたたみで理解させる方向へ寄せる
6. app.py を更新する
7. 構文確認と desktop/mobile 確認をする
8. 必要最小限で README / CURRENT_STATE を同期する

絶対にしないこと:
- 新機能追加
- backend の batch 機構削除
- plan ファイル編集
- aio2-main / notecode への変更
- 青系アクセント再導入
- 説明カード追加

完了時に報告してほしいこと:
- 何を前面から外したか
- 何をどう言い換えたか
- どのSaaSパターンに寄せたか
- どこを別タブ/別開閉に逃がしたか
- 更新ファイル
- 実施した検証
- AGENTS/WORKLOG更新の要否
```
