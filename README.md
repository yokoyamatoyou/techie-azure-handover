# Azure 移行用パッケージ（azure０３０７）

> **2026-08-04 current identity notice:** Microsoft／Google／メールログインの
> canonical identity resolver はローカル実装・テスト済みですが、ライブDB、
> API、Entra本番フロー、Stripeにはまだ反映していません。現在の正本は
> [docs/identity_resolver_rollout_20260803.md](docs/identity_resolver_rollout_20260803.md)
> です。以下の「実装は未実装」は旧Azure移行パッケージの説明であり、
> 現在の認証・課金ランタイム全体の状態を示すものではありません。

このフォルダは、TECHIE を Azure へ移行するために必要な**最小セット**をまとめたパッケージです。復元用のアーカイブ資産は含みません。**外部システム会社への引き渡し用**であり、開発ログ・Deep Research 結果・内部メモ・生成物は含めていません。

---

## システム会社の皆様へ — まず読んでいただく順

受け取り後、次の順で読むと**復元・実行・Azure 移行**の流れが把握しやすくなります。

| 順 | 読むもの | 目的 |
|----|----------|------|
| **1** | **この README（本ファイル）** | パッケージの全体像、含まれるサービス、含めていないもの、設定の入口。このあと「サービスのディレクトリ構成」でフォルダ構造を確認してください。 |
| **2** | **[docs/azure_migration_engineer_guide.md](docs/azure_migration_engineer_guide.md)** | **復元と実行方法**・**Azure 移行方法**の本編。前提条件（Python・環境変数・設定テンプレ）、ローカル/ Azure 上のデプロイ構成、Stripe リセラーモデル、マルチテナント、移行ステップ（PoC→Pilot→本番）、運用手順への参照がまとまっています。 |
| **3** | 各サービスの `requirements.txt` と `config.json.example`（notecode のみ） | 実行環境の復元手順。notecode は `config.json.example` を `config.json` にコピーし、環境変数で API キー等を設定してください。フォントは README の「容量削減のため含めていない資産」を参照し、必要に応じて配置してください。 |
| **4** | **[docs/azure_handoff_summary.md](docs/azure_handoff_summary.md)** | 既存の変更履歴・受け入れチェックの要約。デプロイ後の検証時に参照します。 |
| **5** | **notecode/newalgorithm/** の `rollback_runbook.md`・`acceptance_report.md` | コトメイクのロールバック手順と受入基準。障害時やリリース判定時に参照します。 |

**復元と実行の流れ（要約）**  
1. このパッケージを任意のディレクトリに展開する。  
2. 各サービスで `pip install -r requirements.txt` を実行し、notecode は `config.json.example` → `config.json` のコピーと環境変数（`OPENAI_API_KEY` 等）を設定する。  
3. フォントが必要な場合は README の「容量削減のため含めていない資産」に従い配置する。  
4. 統合起動なら `techie-hub/start.bat` を実行し、ブラウザで HUB（8090）→ 各サービス（8080/8081/8082）にアクセスする。詳細は [azure_migration_engineer_guide.md](docs/azure_migration_engineer_guide.md) の「前提条件」「Azure 上のデプロイ構成」「移行ステップ」を参照してください。

**Azure 移行の流れ（要約）**  
[docs/azure_migration_engineer_guide.md](docs/azure_migration_engineer_guide.md) に、デプロイ構成候補（App Service / Container Apps 等）、ポート・認証、Stripe 連携リセラーモデル、マルチテナント、PoC→Pilot→本番の移行ステップ、監査ログ・障害対応が書かれています。この記述は旧移行パッケージの設計入口です。現在のidentity実装・適用ゲートは [docs/identity_resolver_rollout_20260803.md](docs/identity_resolver_rollout_20260803.md) を優先してください。

---

## サービスのディレクトリ構成

```
azure０３０７/
├── README.md                    # 本ファイル（入口・構成・手順）
├── docs/                        # 移行・運用向けドキュメント
│   ├── azure_migration_engineer_guide.md   # エンジニア向け移行指示書（Stripe リセラー）
│   └── azure_handoff_summary.md            # 既存引継ぎの要約
│
├── notecode/                    # コトメイク（記事・SNS 文の自動生成）  ※ポート 8080
│   ├── requirements.txt
│   ├── config.json.example      # 設定テンプレ（本番は config.json にコピーして編集）
│   ├── ALGORITHM.md            # 記事生成アルゴリズム仕様
│   ├── note/                    # UI・生成コア・パイプライン
│   │   ├── note_writer_app.py
│   │   ├── article_generator.py
│   │   ├── input_contract_v1.py
│   │   ├── newalgorithm_pipeline/
│   │   └── ...
│   ├── core/                    # 設定・モデル選択
│   ├── human_resonance/         # 文体・法務パイプライン
│   ├── human_resonance2/        # 品質パイプライン
│   ├── zero_base/               # 重複抑止等
│   ├── newalgorithm/            # 運用必須ドキュメント（PROGRESS, rollback, acceptance 等）
│   └── docs/                    # 本パッケージでは移行不要な内部ドキュメントは含めていない
│
├── aio2-main/                   # コトミガキ（SEO/AIO・法務・サイトヘルス分析）  ※ポート 8081
│   ├── requirements.txt
│   ├── AGENTS.md
│   ├── ALGORITHM.md
│   ├── nicegui_app.py, run_app.py
│   ├── core/
│   └── plan/                    # 本番参照用のみ（内部改善メモは含めていない）
│
├── doorknock/                   # コトムスビ（代理店向け 2 ページ PDF）  ※ポート 8082
│   ├── requirements.txt
│   └── 実行用スクリプト・assets
│
└── techie-hub/                  # 統合起動用 UI 入口  ※8090
    ├── index.html, style.css, start.bat
    └── plan/                    # phase09（Azure 計画）・doorknock 仕様等
```

## 目的

- 外部エンジニアが Azure 上でコトメイク・コトミガキ・コトムスビをデプロイする際の**コード・設定テンプレ・運用ドキュメント**を一括参照できるようにする。
- 課金・提供形態は **Stripe 連携のリセラーモデル** を前提とした設計指示を含む。

## 入口ドキュメント

| ドキュメント | パス | 用途 |
|-------------|------|------|
| **エンジニア向け Azure 移行指示書** | [docs/azure_migration_engineer_guide.md](docs/azure_migration_engineer_guide.md) | デプロイ手順・Stripe リセラー・マルチテナント・移行ステップ |
| **Azure 引継ぎ要約** | [docs/azure_handoff_summary.md](docs/azure_handoff_summary.md) | 既存の変更履歴・受け入れチェックの参照用要約 |

## 含まれるサービス

- **notecode** … コトメイク（記事・SNS 文の自動生成）
- **aio2-main** … コトミガキ（SEO/AIO・法務・サイトヘルス分析）
- **doorknock** … コトムスビ（代理店向け 2 ページ PDF）
- **techie-hub** … 統合起動用 UI 入口

## 含めていないもの

- `.venv` / `__pycache__` / `logs/` / `outputs/` / 実キー入りファイル
- アーカイブ復元用（`restore_guide` / `archive_execution_runbook` / `archive_target_inventory`）
- `C:\tetie\archive\` 配下の資産

**ドキュメントの区別（本パッケージでは以下を含めていません）**
- **含めていない**: 開発ログ・進捗メモ（progress/WORKLOG/archive_checklist）、Deep Research の結果・プロンプト、内部の品質監査レポート・失敗防止ログ、GPT 移行メモ、生成結果のテキスト（image 配下の .txt 等）、UI 改善の内部計画
- **含めている**: 移行手順・運用手順・アルゴリズム仕様・契約仕様（input_contract/article_type）・ロールバック・受入報告・ログ互換・依存リスクレポート・サービス別 AGENTS/ALGORITHM

**容量削減のため含めていない資産（デプロイ時に別途用意）**
- **notecode/note/generated_images/** … 記事用に生成された画像。実行時に再生成されるため含めていません。
- **notecode/assets/fonts/** … 画像テキスト重ね用フォント（NotoSansJP 等）。`config.json` の `images.text_overlay_font_path` で参照するため、環境にフォントをインストールするか、取得して指定パスに配置してください。
- **aio2-main/PDFreport/fonts/** … PDF レポート用日本語フォント（NotoSansJP 等）。環境にインストールするか、PDFreport が参照するパスに配置してください。

## 設定テンプレ

- **notecode**: `notecode/config.json.example` を `notecode/config.json` にコピーし、環境に合わせて編集する。
  - **手順**: (1) `config.json.example` を `config.json` としてコピー。(2) API キー等のシークレットは **ファイルに書かず**、環境変数 `OPENAI_API_KEY` または Azure Key Vault 等で注入する。(3) モデル名・`quality_pipeline.mode`・`poc.token_csv_path` 等は必要に応じて変更する。
  - 項目の詳細は [docs/azure_migration_engineer_guide.md](docs/azure_migration_engineer_guide.md) の「前提条件」を参照する。

## 本番ソースの参照

このパッケージは「移行用スナップショット」です。最新の変更履歴・受け入れ基準・ロールバック手順は、可能であれば本番リポジトリの以下を参照してください。

- 全体入口: `C:\tetie\AGENTS.md`
- Azure 引継ぎ（詳細）: `C:\tetie\azure-handoff-2026-02-09-ja.md`
- コトメイク newalgorithm 運用: `C:\tetie\notecode\newalgorithm\rollback_runbook.md` / `acceptance_report.md`
