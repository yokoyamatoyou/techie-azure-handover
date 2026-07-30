# Nielsen 10 原則マトリクス

## 1. 判定条件

このマトリクスは現行コード、テスト、current docs による構造監査である。in-app Browser 接続が 3 回 timeout したため、current-run screenshot に基づく視覚監査ではない。`pass` は使わず、確認範囲に応じて `partial` / `fail` / `unverified` とした。

| # | 原則 | 判定 | current evidence | 主な問題 | 優先度 | owner / 受入条件 |
|---:|---|---|---|---|---|---|
| 1 | システム状態の可視性 | partial | `nicegui_app.py:736-768,825-869,990-1160` に status/progress、完了後の保存 route 移動がある | 状態更新に `role=status` / `aria-live` がなく、支援技術へ通知されない。実 browser の進行・error 表示は未確認 | P1 | NiceGUI accessibility owner。状態、進行、完了、失敗を polite/assertive live region へ分離し、keyboard/screen reader で通知を確認 |
| 2 | 実世界との一致 | partial | 保存画面は `やること`、`文章改善`、`実装・設定` 等の日本語へ整理 (`saved_workspace.py:2613-2643`) | `unknown` が「参考」へ丸められ、`内部ヒューリスティック` 等の内部語が primary 実装面に残る (`:1710-1734`)。CWV proxy も実測風 | P1 | saved-workspace truth owner。未確認/推定/実測、対象者、取得時刻を平易な語で明示 |
| 3 | ユーザーの主導権と自由 | partial | 自動遷移を止める「今は移動しない」がある (`nicegui_app.py:749-752,780-787,1163`) | 分析処理の cancel ではない。保存結果 GET が DB を更新し得る。閲覧だけで状態を変えない期待を破る | P1 | saved-workspace truth owner。GET 無書込、明示 migration、分析 cancel の状態契約を別 owner で設計 |
| 4 | 一貫性と標準 | fail | primary/secondary tab helper は存在 (`saved_workspace.py:2562-2586`) | 実 renderer は別の flat 5 tabs (`:2613-2643`)。helper test だけが通り、UI/CSV/Markdown の優先 action も不一致 | P1 | saved-workspace truth owner。単一 IA / action model を renderer と export contract test で固定 |
| 5 | エラー防止 | partial | URL error label と click 時 validation がある (`nicegui_app.py:663-668,789-808,990+`) | invalid input 時も button が enable され、click 後に止める。URL query secret を保存前に防止しない。provider 取得失敗も pass 化 | P1 | input/privacy owner と provider owner。入力段階 disable、error association、secret redaction、unverified state |
| 6 | 記憶より認識 | partial | 保存結果にカテゴリ tab、概要、アクションを表示。primary/engineer 分離の意図がある (`saved_workspace.py:1083-1101,2001-2076`) | 最大 5 件に切る一方「残り」総数の母集団が別で、9 件目以降へ到達できない。略語・内部語の補助が不均一 | P2 | saved-workspace truth owner。全件への導線、同じ total、用語説明と evidence drill-down |
| 7 | 柔軟性と効率 | partial | 保存 route、history、CSV/MD/DOCX、auto-open opt-out がある | モバイル/desktop history は card/row click 前提で keyboard activation がない。export 内容が surface ごとに違い、再確認コストが高い | P1 | saved UI + accessibility owner。native link/button、同一 action set、再訪状態の保持 |
| 8 | 美的で最小限のデザイン | partial | 5 tabs 上限と audience 分離の意図 | 実装者向け raw/内部ヒューリスティックが primary tab へ漏れ、Word にも technical/raw がそのまま含まれる。視覚密度は未確認 | P2 | role-readability owner。primary conclusion/evidence/next action を先にし、raw は明示展開または engineer export |
| 9 | エラー認識・診断・回復 | partial | UI は日本語 error status を出し、safe fetch は error を保持 | `broken` と timeout、`pass` と取得失敗、`reference` と unknown が混ざる。再試行条件・取得時刻・影響が一貫しない | P1 | evidence-state contract owner。machine state と日本語 explanation、再試行、証拠時刻を共通 schema 化 |
| 10 | ヘルプと文書 | partial | current `AGENTS.md` / `ALGORITHM.md` と多数 planning package がある | tab helper/renderer/completed artifact の不一致、FAQ/llms/speakable の公式更新差、モデル温度表現差がある | P2 | docs owner。current owner と実 renderer を照合する doc test、公式基準日を記録 |

## 2. 主要導線ごとの状態

| 導線 | コードで確認 | 実 browser | 判定 |
|---|---|---|---|
| URL 入力 → validation | 視覚 error label、click 時 validation | 未確認 | partial |
| 分析開始 → progress → 完了 | status/progress/auto-open | 未確認。ARIA 通知なし | partial |
| 完了 → 保存結果 | `/runs/{id}` へ遷移 | 未確認。GET 書込残余 | fail |
| 保存結果 → action drill-down | tab と action card | 未確認。全件到達性に欠落 | fail |
| history → 過去 run | clickable card / rowClick | 未確認。keyboard semantics なし | fail |
| export download | CSV/MD/DOCX service と UI control | 未確認。action parity 不一致 | fail |

## 3. 原則別の利用者影響と再現

| # | 非エンジニアへの影響 | エンジニアへの影響 | 再現手順または未確認理由 |
|---:|---|---|---|
| 1 | 分析の進行・完了・失敗に気づけない可能性 | status text はあるが支援技術通知を契約テストできない | `nicegui_app.py` の status 更新と ARIA 不在を検索。実 screen reader は browser timeout で未確認 |
| 2 | 「参考」を低リスクと誤読し、proxyを実測と考える | machine state と表示語の対応を追跡しづらい | unknown fixture の UI adapter を追跡。CWV formula と snapshot label を比較 |
| 3 | 閲覧だけで結果が変わり、元へ戻せない | legacy migration が GET と混在し再現性を失う | competitor 付き旧 bundle の load→refresh→save 引数を静的追跡。実保存routeはデータ保護のため開かず |
| 4 | 画面と持ち出し資料の優先事項が違う | helper test が実 renderer を守らず、複数consumerを保守する | helper/renderer、base/workspace/export action buildersを比較。targeted tests はpassするが不一致を検出しない |
| 5 | 入力後に初めてerrorとなり、秘密付きURLも保存され得る | validation、fetch、persistenceの責務が分断 | invalid stateでもbutton enable、queryのend-to-end伝播を追跡。外部fetchなし |
| 6 | 表示外の重要actionがあると気づけない | totalとvisible sliceの母集団が別でdebug困難 | 9件超fixture相当のslice条件をコード追跡。実UI件数はbrowser timeoutで未確認 |
| 7 | keyboard利用で履歴/再訪が困難 | surface差を手作業で照合する必要 | card/rowClickのsemantic handler不在を検索。keyboard実操作は未確認 |
| 8 | 初回面で専門語/rawに圧倒される | technical detailとprimaryの責務が曖昧 | primary tabとengineer tab、DOCX/Markdown rendererを比較。視覚密度は未確認 |
| 9 | timeoutを故障、未確認を問題なしと誤解する | retry可否とerror原因をprogrammaticに分けられない | link/provider/state mappingのfixtureと分岐を追跡 |
| 10 | 古いFAQ/llms/speakable前提を正しい改善策と考える | current docsと実renderer/公式更新がずれ、owner判断を誤る | current docs、planning PROGRESS、code、2026-07-10公式一次資料を比較 |

## 4. 先に固定すべき interaction contract

1. 閲覧 GET はデータを書き換えない。
2. `pass/fail/unverified/not-applicable/error` を全 surface で同じ意味にする。
3. canonical priority actions を UI/CSV/Markdown/DOCX が同じ id/order で参照する。
4. 主要導線を native semantic control と live status で keyboard/screen reader 対応する。
5. 実ブラウザが使える環境で screenshot、keyboard、zoom、axe、console の current-run evidence を残す。
