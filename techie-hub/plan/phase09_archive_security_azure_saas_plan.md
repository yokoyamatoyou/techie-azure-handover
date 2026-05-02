# phase09_archive_security_azure_saas_plan.md

## 0. この計画の位置づけ
- 対象: `C:\tetie` 全体
- 状態: **計画のみ**（実ファイル移動・削除・インストールは未実施）
- 目的:
  - ディレクトリを整理し、必要な機能ファイル + `AGENTS.md` + `WORKLOG.md` を中心に再編する
  - 脆弱性/セキュリティチェックを網羅実施する
  - 外部企業へAzure SaaS化を委託できる最小かつ十分な移管データを `C:\tetie\Azure` に整備する

## 1. 完了定義（Definition of Done）
1. `C:\tetie\archive\YYYYMMDD_HHMM\` が作成され、不要ファイルが復元可能な形で移動済み
2. 移動ログ（manifest）が存在し、元位置/移動先/件数が追跡可能
3. セキュリティ点検レポート（依存関係、秘密情報、設定、アプリ診断）が揃っている
4. `C:\tetie\Azure\` に外部移管用の最小構成が揃っている
5. Azure移管手順書（マルチテナント、リセラー制、Stripe決済方針を含む）が完成している

## 2. 実行フェーズ

### Phase A: 事前凍結（変更防止）
- 実行前に作業ルールを固定:
  - 破壊的削除は禁止（`archive` への移動のみ）
  - シークレット値は移管物に含めない
  - すべての移動に manifest を残す
- 生成物:
  - `C:\tetie\techie-hub\plan\phase09_execution_checklist.md`（実行チェックリスト）

### Phase B: 棚卸しと分類
- `C:\tetie` 全体を以下に分類:
  - KEEP-CORE: 実行に必要な機能ファイル
  - KEEP-DOC: `AGENTS.md`, `WORKLOG.md`, 運用必須ドキュメント
  - ARCHIVE: 当面不要だが保管すべきファイル
  - EXCLUDE: `.venv`, `logs`, `outputs`, キャッシュ、一時ファイル等（Azure移管対象外）
- 判断ルール:
  - 「起動に必要」「依存解決に必要」「実装理解に必要」なら KEEP
  - それ以外は ARCHIVE

### Phase C: archive へ移動（削除禁止）
- 作成先:
  - `C:\tetie\archive\YYYYMMDD_HHMM\`
- 実施内容:
  - ARCHIVE分類のみ移動
  - 元構造を保持して移動
  - manifest を作成（CSV/MD）
- 生成物:
  - `C:\tetie\archive\YYYYMMDD_HHMM\MANIFEST.csv`
  - `C:\tetie\archive\YYYYMMDD_HHMM\README_restore.md`

### Phase D: セキュリティ/脆弱性総点検
- 点検範囲（網羅）:
  - 依存関係脆弱性（Pythonパッケージ）
  - シークレット混入（APIキー、トークン、秘密情報）
  - 設定不備（CORS、debug、ログ出力、エラー露出）
  - アプリ入力経路（URL/PDF/DOCXアップロード、プロンプト入力）
  - 認可/認証境界（将来SaaS化で必要な分離要件）
- レポート出力:
  - `C:\tetie\techie-hub\plan\security\` 配下に保存
  - Critical/High/Mediumで優先度付け
  - 修正要否と受容判断を明記

### Phase E: Azure移管パッケージ整備
- 作成先:
  - `C:\tetie\Azure\`
- 含める（必要最小限）:
  - `techie-hub` / `notecode` / `aio2-main` の実装本体（不要物除外後）
  - `requirements*.txt`, 設定テンプレ（`.env.example`）
  - 実行手順、運用手順、障害対応手順
  - AGENTS/WORKLOG（2月以降の追跡が可能な範囲）
  - Azure設計草案（後述Phase F）
- 含めない（重依存・再生成可能）:
  - `.venv`, `__pycache__`, `logs`, `outputs`, 一時生成物
  - 機微データ、実キー入りファイル

### Phase F: Azure SaaS設計ドキュメント作成（外部委託向け）
- 必須章:
  1. ターゲット構成（Azure上の実行構成）
  2. マルチテナント方針（テナント分離単位、データ分離、権限制御）
  3. リセラー制（代理店/顧客階層、権限委譲、請求責任境界）
  4. Stripe連携（課金モデル、サブスク/従量、Webhook運用、失敗時再試行）
  5. 監査ログ、障害対応、SLA/SLO案
  6. 移行ステップ（PoC→Pilot→本番）
- 出力先:
  - `C:\tetie\Azure\docs\azure_saas_handover.md`

### Phase G: 公式情報のWeb調査タスク（実行時に実施）
- 調査対象（一次情報優先）:
  - Microsoft Learn / Azure Architecture Center（マルチテナント、SaaS、運用）
  - Stripe公式ドキュメント（Billing, Checkout, Webhooks, Connect）
- 調査成果物:
  - `C:\tetie\Azure\docs\research_sources.md`
  - 採用判断（採用/保留/非採用）を明記

## 3. 実行時の安全ガード
- `archive` 移動前に件数確認（0件/想定外件数は停止）
- 上書き禁止（同名衝突時はタイムスタンプ付与）
- 途中中断時も manifest を更新
- 復元手順を常に先に作成してから移動開始

## 4. 直近の再開手順（会議後）
1. `C:\tetie\AGENTS.md` を開く
2. `C:\tetie\techie-hub\plan\WORKLOG.md` の最新行を確認
3. 本ファイル `phase09_archive_security_azure_saas_plan.md` を開く
4. Phase A から順番に実行する（いきなり移動しない）

## 5. 現時点の判断
- この方針で実行可能
- 先に「計画固定」と「追跡ログ導線」を整備してから作業に入るため、会議後の再開が容易

