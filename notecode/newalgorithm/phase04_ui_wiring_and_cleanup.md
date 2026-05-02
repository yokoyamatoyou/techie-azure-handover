# Phase04: UI Wiring and Cleanup

## Goal
- 既存UIレイアウトを維持しつつ、新パイプラインへ接続する。

## UI Policy
- 残す: 記事種類、生成実行、画像生成
- 当面維持: 既存UIは一旦残す（新アルゴリズム安定化まで）
- 削除開始条件: 安定化後ログで「未使用 + 非稼働 + 代替あり」を満たした項目

## Input
- `ui_mapping_table.md` 確定版
- Phase03の最小パイプライン

## Output
- UI接続更新コード
- 削除/非表示確定一覧（例外画面を明記）

## Steps
1. 既存UIの生成導線を新 `input_contract` へ接続する。
2. 結果表示を新出力オブジェクトに合わせる。
3. 本PhaseではUI削除を行わず、計測タグを付与して利用ログを取得可能にする。
4. 画像機能呼び出しI/Fが維持されることを確認する。
5. Nielsen/Hick観点で「選択肢過多」「曖昧ラベル」を削減する。
6. 次リリース向けに削除候補リスト（ログ根拠付き）を作成する。

## Deliverables
- 更新済みUI接続コード
- 削除候補一覧（ログ根拠付き）

## Exit Criteria
- レイアウト崩れなしで必須3要素が動作する。
- 削除候補の理由とログ根拠が一覧化される。
- UIから旧パイプライン直結参照がなくなる。

## Self Test
- ST-01 正常: 既存レイアウト維持で生成完了。
- ST-02 異常: 旧UI要素が残っていても新パイプライン動作を阻害しない。

## LLM Vulnerability Test
- LT-01: UI入力欄経由の注入文が本流に影響しない。

## Pipeline Review
- PR-01: UI -> contract -> pipeline -> output -> legal -> log が追跡可能。

## Module/Dependency Risk Check
- DR-01: UI層が旧モジュールへ直接依存していない。

## Rollback
- 条件: UI操作性低下または生成不能
- 戻し先: UI変更を最小限に戻し、計測のみ継続
