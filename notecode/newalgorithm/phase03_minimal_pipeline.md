# Phase03: Minimal Pipeline Build

## Goal
- 新パイプラインの最小経路を成立させる。

## Target Flow
- contract resolve -> discourse plan -> section generation -> dedupe -> minimal editor guard -> output format -> telemetry

## Input
- `input_contract_draft.md`（確定版）
- Phase02のrunbook/復活手順

## Output
- 最小経路で動く生成コード
- 最小エラーコード定義
- パイプラインI/O仕様メモ

## Steps
1. 新モジュール雛形を作成（contract/discourse/section/dedupe/editor/output/log）。
2. 1経路で疎通する `generate` フローを実装する。
3. `daily_story` + `media=seo` で `style_compact_for_seo=true` を自動付与する。
4. semantic_dedupe呼び出しをアダプタ経由で接続する。
5. 失敗時の最小フォールバック（LLM失敗/入力不正）を実装する。

## Deliverables
- 最小実装コード
- フロー図（簡易）
- エラーコード一覧（最小）

## Exit Criteria
- 3媒体 x 7記事タイプで少なくとも1件ずつ生成成功。
- 各ステップのI/Oがドキュメント化される。
- 失敗時にエラーコードとログが残る。

## Self Test
- ST-01 正常: 3媒体 x 7記事タイプで最低1件成功。
- ST-02 異常: source未指定時に入力エラーで停止。
- ST-03 異常: article_type不正時に入力エラーで停止。
- ST-04 異常: LLM失敗時にフォールバック/リトライが動作。

## LLM Vulnerability Test
- LT-01: 指示上書き注入への耐性確認。
- LT-02: 危険な法務断定誘導の拒否確認。

## Pipeline Review
- PR-01: 各ステップの入出力契約が明示される。
- PR-02: 途中失敗時のログ記録が残る。

## Module/Dependency Risk Check
- DR-01: 新規依存は最小化し、追加依存は採用理由を記録。

## Rollback
- 条件: 最小経路が通らない、または出力品質が基準未達
- 戻し先: Phase02で準備したarchive復活手順に従う
