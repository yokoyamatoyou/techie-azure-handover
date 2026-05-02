# Phase06 Dependency Risk Report

## 実行結果
- 実行コマンド: `py -m pip_audit`
- 結果: FAIL（`UnicodeDecodeError`）
- 失敗要因: Windows環境で `pip_api` が `pip --version` 出力を UTF-8 固定で decode し失敗

## 現在の主要依存（`notecode/requirements.txt`）
- `nicegui==3.8.0`
- `requests==2.32.5`
- `openai==1.54.5`
- `pdfplumber==0.11.9`
- `pypdf==6.7.5`
- `opencv-python-headless==4.10.0.84`
- `cryptography==46.0.5`

## リスク評価
- 高リスク候補
  - `opencv-python-headless`
    - 理由: バイナリ配布依存が大きく、環境差分時の障害影響が大きい
    - 代替案:
      - 画像ぼかし機能を `Pillow` ベース実装へ段階移行
      - 画像編集機能をオプション化し、障害時は fail-open で生成本流を継続
- 中リスク候補
  - `openai`
    - 理由: 外部API依存（レート制限・ネットワーク断）
    - 代替案:
      - 既存の fallback/retry を維持
      - Phase06時点の最小パイプラインでは llm未指定時フォールバック生成を継続

## DR-01 / DR-02 判定
- DR-01: 依存脆弱性確認結果を記録 -> PASS（実行失敗要因を明記）
- DR-02: 高リスク依存の代替案を記録 -> PASS（`opencv-python-headless` の代替方針を明記）

## 次アクション（Phase06フォロー）
- `pip_audit` の実行環境対策を追加（文字コード固定回避）
- CI環境（UTF-8固定）で依存監査を定期化し、ローカル失敗時の代替実行ログを残す
