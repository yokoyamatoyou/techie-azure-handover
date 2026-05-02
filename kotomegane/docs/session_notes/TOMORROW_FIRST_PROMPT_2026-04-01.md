# Tomorrow First Prompt 2026-04-01

更新日: 2026-04-01  
用途: 次回起動時の最初にそのまま貼り、`kotomegane` をデザイン込みで完成させるための開始プロンプト

## Prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md

今回の実施範囲:
- `kotomegane` を TECHIE 共通UIの先行基準として、デザイン込みで完成に近づける
- 今回は `kotomegane` だけを対象にし、`aio2-main` と `notecode` には着手しない
- 主目的は「設定したキーワードや質問で、自社や自社製品が AI 回答に出るかを見ること」
- 競合比較は残すが補助機能として扱う
- OpenAI のみ正式対応として実装を整理する
- 次回起動時は、まず実装ではなく `計画作成` から始める

重要な前提:
- `techie-hub` が TECHIE 全体の入口
- `kotomegane` は共通H1、共通アイコン、共通導線の最初の基準実装
- `90ドル` は実際の価格ではない
- `90ドル相当` は「高そうに見える」「信頼感がある」「安っぽくない」見た目の目標を意味する
- 価格表示や価格設計の実装は今回の主題ではない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md
3. C:\tetie\kotomegane\AGENTS.md
4. C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md
5. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
6. C:\tetie\kotomegane\docs\DOC_STATUS.md
7. C:\tetie\kotomegane\README.md
8. C:\tetie\kotomegane\app.py
9. C:\tetie\kotomegane\docs\TOMORROW_FIRST_PROMPT_2026-04-01.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md
3. C:\tetie\kotomegane\AGENTS.md
4. C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md
5. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
6. C:\tetie\kotomegane\docs\DOC_STATUS.md
7. C:\tetie\kotomegane\README.md
8. C:\tetie\kotomegane\app.py

現状の確定事項:
- H1 の共通アイコンと favicon は `コトメイク` / `コトミガキ` と同じ資産へ統一済み
- 質問入力は 1件を既定表示、`＋` で追加、最大3件の方向で実装済み
- Batch は残すが主導線ではない
- 手動実行が主導線
- OpenAI のみで先に仕上げる
- 競合比較は残すが、上段の主役にはしない
- `自社が出たか / よく一緒に出る外部名や外部サイトは何か / 次に見るべき質問は何か` を主結果にする
- タブ分けは許容する
- ただし、初見の主導線は軽く保ち、タブ数を増やしすぎない

次回の作業順:
1. まず `計画作成`
2. 次に `デザイン骨格を決める`
3. その後 `機能を当てはめる`
4. 最後に `文言と見た目を整える`

優先順の判断:
- 今回は `デザインが先、機能は後`
- ただし、絵だけ先に作るのではなく `情報設計 -> 画面構造 -> 機能配置` の順に進める
- 既存機能を壊さず、どこに置くかを先に決める

今回の最優先:
1. まず `kotomegane` の完成形を文章で設計する
2. 認知負荷をさらに下げる
3. 初見で「何を入れて何を見るツールか」が一目で分かるようにする
4. H1 から各機能への遷移が分かりやすい状態にする
5. `入力 / 主結果 / 詳細運用` の3段構造を見た目で明確にする
6. 英語や内部語をさらに減らす
7. `高そうに見えるが分かりやすい` デザインへ寄せる

UI原則:
- Nielsen 10 Heuristics
- Hick's Law
- recognition over recall
- progressive disclosure
- consistency and standards

デザインの方向:
- 入口体験は Google 寄り
  - 情報を絞る
  - 迷わせない
  - 余白を使う
- 作業画面は Microsoft 寄り
  - 情報構造を明確にする
  - 状態や結果を追いやすくする
- ただし全体としては軽く、やわらかく、安っぽく見せない

今回の作業で優先すること:

0. Planning First
- 最初に実装へ入らない
- 現行UIを読み、残す機能、後退させる機能、タブへ逃がす機能を整理する
- `完成後の画面構造` を先に箇条書きで固定する
- 必要なら 1 画面内のタブ分けを使ってよい
- ただしタブは「主結果を隠すため」ではなく、詳細運用を整理するために使う
- 計画が固まってから実装する

A. Top / Hero
- 共通H1を前提に、ブランドマーク、サービス名、価値訴求を短く整理する
- 1画面目で高さを取りすぎない
- 最初に「AI回答で自社や製品が出るかを見るツール」だと分かるようにする

B. Input
- 通常は質問1件だけ見せる
- `＋ 質問を追加` で増やす
- 最大3件
- 入力欄まわりで迷わせない
- 競合欄は残すが、主役より一段下げる

C. Primary Result
- 最初に見る判断は3つまで
- 自社が出たか
- 外部名 / 外部サイトが見えたか
- 次に見直す質問は何か
- カード数が多すぎるなら削る

D. Detail / Operations
- 質問セット
- 定期バッチ
- 比較
- brief
- export
- これらは価値を落とさず、初見の主導線から一段下げる
- 必要ならタブ分けしてよい
- 候補:
  - `詳細`
  - `運用`
  - `比較`
  - `保存済み`
- ただしタブ名は日本語で短く、数は増やしすぎない

E. Copy
- UI の英語を減らす
- 内部実装語を出さない
- `競合` を主語にしすぎない
- 固い語には補助説明を付ける

F. Shared Future
- 今回は `kotomegane` の完成を優先する
- ただし将来 `techie-hub`、`aio2-main`、`notecode` に移植できる共通骨格は壊さない
- OpenAI 専用実装で進めるが、責務は将来の provider 拡張を残す

do-not:
- `aio2-main` や `notecode` の改修に入らない
- 新しい大機能を増やさない
- 競合比較を主役に戻さない
- 複雑なアルゴリズムを先に増やさない
- 「90ドル」を実価格のように扱わない
- 安っぽい演出や過剰な装飾に寄せない

作業の進め方:
1. まず現行 `app.py` の H1、入力、主結果、詳細運用の見え方を確認する
2. 次に `完成後の画面構造案` を文章で作る
3. その上で、主役ではないカードや説明を削るか後退させる
4. 必要ならタブ分けで詳細運用を整理する
5. その後、日本語文言と視線誘導を整える
6. `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を実装に合わせて更新する
7. 必要なら `C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md` と `docs/DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md` も同期する

完了条件:
- 起動直後にツールの目的が分かる
- 主役操作が少なく迷わない
- 質問1件からすぐ使える
- 競合比較は残っているが主役ではない
- H1 が共通資産として成立している
- 見た目が高級寄りで、説明過多でも装飾過多でもない
- 次に `aio2-main` と `notecode` へ展開できる共通文法になっている

最低限の検証:
1. `python -m py_compile app.py`
2. `.venv\\Scripts\\python.exe -c "import app"`
3. 起動後に H1、入力欄、主結果、詳細運用の階層が崩れていないこと
4. 質問1件 + 追加で最大3件の入力が自然に見えること
5. 主要文言が日本語として不自然でないこと

完了時に必ず報告すること:
- 先に作った計画の要点
- 読んだ正本ファイル
- 変更したUIの要点
- 採用した画面構造
- タブ分けした場合はその理由
- 削ったもの / 一段下げたもの
- 残した競合比較の位置づけ
- 共通UIとして次に流用できる要素
- 更新したドキュメント
- 検証内容
- AGENTS/WORKLOG更新の要否
```
