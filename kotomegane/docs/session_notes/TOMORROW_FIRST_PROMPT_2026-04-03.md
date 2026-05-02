# Tomorrow First Prompt 2026-04-03

更新日: 2026-04-02  
用途: 次回起動時の最初にそのまま貼り、`kotomegane` の残作業を feature-first で再開するための開始プロンプト

## Prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\kotomegane\AGENTS.md
- C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
- C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md

今回の実施範囲:
- `kotomegane` だけを対象にする
- 今日は `aio2-main` と `notecode` に触れない
- 上段デザインは大枠 fixed 済みとみなし、明確な崩れ以外では作り直さない
- 以降は `低工数で高付加価値` な機能導入を優先する
- OpenAI のみ live 実行、Gemini / Claude は UI 枠のみ維持する

重要な現在値:
- H1 は最小化済みで、上段は `コトメガネ` を短く見せる構成
- 上部ナビは raw URL を見せず、`共通アイコン + TECHIE` の高コントラスト lockup に修正済み
- UI にモデル名は出さない
- UI に出す provider 表記は `ChatGPT / Gemini / Claude` のみ
- 現状は `ChatGPT` のみ active、`Gemini / Claude` は gray inactive
- prompt caching は 24時間保持を優先要求し、未対応条件では自動 fallback
- `まとめて確認` は batch 割引を優先する内部運用のまま維持

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\kotomegane\AGENTS.md
3. C:\tetie\kotomegane\docs\DOC_STATUS.md
4. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
5. C:\tetie\kotomegane\docs\TOMORROW_WORK_PLAN_2026-04-01.md
6. C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md
7. C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md
8. C:\tetie\kotomegane\README.md
9. C:\tetie\kotomegane\Saas\LLMO対策SaaS 低コスト構築提案.md
10. C:\tetie\kotomegane\Saas\deep-research-report (11).md
11. C:\tetie\kotomegane\app.py
12. C:\tetie\kotomegane\analysis_lib.py
13. C:\tetie\kotomegane\storage.py
14. C:\tetie\kotomegane\config.py
15. C:\tetie\kotomegane\llmo_client.py
16. C:\tetie\kotomegane\docs\TOMORROW_FIRST_PROMPT_2026-04-03.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\kotomegane\AGENTS.md
3. C:\tetie\kotomegane\docs\DOC_STATUS.md
4. C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md
5. C:\tetie\kotomegane\docs\TOMORROW_WORK_PLAN_2026-04-01.md
6. C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md
7. C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md
8. C:\tetie\kotomegane\README.md
9. C:\tetie\kotomegane\Saas\LLMO対策SaaS 低コスト構築提案.md
10. C:\tetie\kotomegane\Saas\deep-research-report (11).md
11. C:\tetie\kotomegane\app.py
12. C:\tetie\kotomegane\analysis_lib.py
13. C:\tetie\kotomegane\storage.py
14. C:\tetie\kotomegane\config.py
15. C:\tetie\kotomegane\llmo_client.py

今回の考え方:
- もう `ヘッダをどうするか` から考え直さない
- `高付加価値機能を先に決める -> 低工数順に入れる` を優先する
- デザイン変更は、機能導入に伴って必要な最小差分だけに留める
- 既存 backend と DB は壊さず、前に進める

今回の最優先:
1. `Saas` 提案を踏まえて、低工数で高付加価値な機能を 2〜3 件に絞る
2. そのうち少なくとも 1〜2 件はこのセッションで実装する
3. 既存の compact header / provider 表示 / brown theme を壊さない
4. ドキュメントを現在値へ追従させる

優先候補:
1. `週次差分サマリ`
- 前回比で `自社露出 / 外部優勢質問 / 引用ドメイン` がどう変わったかを出す
- 既存 DB と履歴を使いやすく、経営判断価値が高い

2. `不足ページナビ強化`
- `recommended_actions` と `page gap` を制作着手にもっと直結させる
- `何を直すか` を abstract ではなくページ種別と優先度で出す

3. `意図クラスタ別の負け筋`
- どの質問群で負けているかを、意図単位でまとめる
- `比較 / 料金 / FAQ / 事例 / 地域 / 指名 / how-to` の勝ち負けを整理する

履歴表示の方針:
- 上段の主役KPIは `自社露出率` を優先する
- 履歴の主役グラフは `visibility スコア推移` にする
- `外部サイト優勢率` は補助指標として扱う
- `実行履歴` テーブルは監査用として残すが、主役にはしない
- source 周りは `回答で実際に citation として出た URL` を中心に扱う
- `consulted but not cited` のような上級者向け診断は今回の scope に入れない

後回し:
- Gemini / Claude live 接続
- 高度な Sankey / ヒートマップ
- 複雑な narrative 解析
- マルチモデル同時比較
- header / hero の大きな再設計

実装順:
1. 最初に短い計画を作る
2. 次に `Saas` 提案と現行コードの接点を確認する
3. その上で、優先候補 2〜3 件を `低工数 / 中工数 / 後回し` に分ける
4. 低工数のものから 1〜2 件を実装する
5. UI の見せ方を最小調整する
6. `README.md` と `docs/CURRENT_STATE_2026-03-30.md` を更新する

UIルール:
- H1 は再び説明だらけに戻さない
- モデル名や小型 tier 名は UI に出さない
- provider の表記は `ChatGPT / Gemini / Claude` のみ
- active / inactive は一目で分かる状態を維持する
- 背景と文字とロゴのコントラストは崩さない

do-not:
- `aio2-main` や `notecode` を触らない
- H1 の説明文を復活させない
- Perplexity を戻さない
- モデル名を UI に出さない
- いきなり大きな新規アルゴリズムを追加しない
- 既存の Batch / prompt cache 運用を壊さない

最低限の検証:
1. `.venv\\Scripts\\python.exe -m py_compile app.py analysis_lib.py config.py llmo_client.py storage.py`
2. `.venv\\Scripts\\python.exe -c "import app"`
3. `C:\tetie\techie-hub\start.bat force`
4. `http://127.0.0.1:8083/` が 200 を返すこと
5. header / provider 表示 / 新規機能UI が崩れていないこと

完了時に必ず報告すること:
- 読んだ正本ファイル
- 採用した優先機能
- 実装した機能と後回しにした機能
- 既存UIに与えた影響
- 更新したドキュメント
- 検証内容
- AGENTS/WORKLOG更新の要否
```
