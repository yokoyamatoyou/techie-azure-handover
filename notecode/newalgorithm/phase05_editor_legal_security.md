# Phase05: Editor/Legal/Security

## Goal
- 編集1層と生成後リーガルを導入し、安全性と実運用性を確保する。

## Input
- Phase04 のUI接続完了版
- Phase03 の最小パイプライン

## Output
- 編集1層モジュール
- 生成後リーガルモジュール
- UIの再チェック/提案反映導線

## Steps
1. `editor_guard` を実装（重複/文法/AIぽさ）。
2. 生成完了直後に `legal_postcheck` を自動実行する。
3. UIに「再チェック」「提案反映（必要時）」を追加する。
4. 危険出力の最終ガードを追加する。
5. failure時は本文保持 + 再実行可能にする。

## Deliverables
- `editor_guard` 実装
- `legal_postcheck` 実装
- UIリーガル導線実装

## Exit Criteria
- 生成後リーガルが自動で走り、結果が同画面で確認できる。
- リーガル失敗時に本文が失われない。
- 任意再実行が1クリックで動作する。

## Self Test
- ST-01 正常: 生成直後にリーガル結果が表示される。
- ST-02 異常: リーガル失敗時も本文保持 + 再実行可能。

## LLM Vulnerability Test
- LT-01: プロンプト注入耐性。
- LT-02: 越権命令拒否。
- LT-03: 危険断定誘導拒否。
- 記録形式は `pass/fail + reason` を固定。

## Pipeline Review
- PR-01: editorとlegalが責務分離され、順序が固定される。

## Module/Dependency Risk Check
- DR-01: legal実装で過剰な外部依存が増えていない。

## Rollback
- 条件: 生成停止や誤検知多発で運用不能
- 戻し先: legalを任意実行に一時切替、根因修正後に再有効化
