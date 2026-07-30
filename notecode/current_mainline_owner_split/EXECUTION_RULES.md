# Execution Rules

- Last Updated: 2026-03-14

## Operating Principle

- current mainline を正本として進める。
- runtime と品質課題を混同しない。
- 1責務 1owner を維持する。
- 1回に 1論点だけ扱う。
- 「直せそう」ではなく「仕様として矛盾している」で初めて修正する。

## Per-Phase Mandatory Checks

各 Phase の末尾で必ず以下を実施する。

- コードバグ確認
- パイプライン疎通確認
- LLM 安全性確認
- 必要な `py_compile`
- 必要な `pytest`
- ログと UI 表示の整合確認

## Retry and Stop Rules

- 同一事象に対する修正試行は最大 2 回までとする。
- 2 回失敗したら停止し、以下をユーザーへ報告する。
  - 失敗した Phase と Task
  - 試した修正内容
  - エラー箇所
  - 影響範囲
  - 次に必要な判断

## Autonomous Progression Rule

- 各 Phase の exit criteria を満たし、必須確認がすべて通った場合のみ次 Phase に進む。
- エラーがなければ、`PROGRESS.md` を更新して次 Phase を `in_progress` に変更する。
- エラーが残る状態では次 Phase に進まない。

## Evidence Recording Rule

- 各 Phase で以下を記録する。
  - 変更対象 owner
  - 確認したログ
  - 実施したテスト
  - 事実と推測の切り分け
  - rollback 条件

## Update Rule for PROGRESS and WORKLOG

- 現在地、次アクション、Phase 状態は `PROGRESS.md` を正とする。
- 時系列の変更記録は `C:\tetie\WORKLOG.md` に残す。
- Phase の途中状態は `WORKLOG.md` ではなく `PROGRESS.md` にだけ記載する。

## Prohibited Expansions

- `article_generator.py` の再分割
- `comparative_review` の品質修正
- `config.json` や model policy の変更
- baseline 更新
- `aio2-main` への着手
- 広いリファクタ

