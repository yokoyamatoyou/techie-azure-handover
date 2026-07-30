# note/LinkedIn 記事ジェネレーター

高品質な **note** および **LinkedIn** 向け記事を、URLやPDF/DOCX/TXT/MDを元に自動生成するライティングツールです。

## 主要機能

- **法言語学的ヒューマナイズ**: AI臭さを排除し、人間らしい自然な文章を生成
- **リーガル & リスク監修**: 20以上の法令（薬機法・景表法等）に基づき企業の安全性を確保
- **簡易リーガルチェック**: 既存テキストを貼り付けてリスクと修正根拠を即座に確認
- **インタビューステップ**: 生成前にAIが質問を行うことで、一次情報と個性を記事に注入
- **多段階検証**: ファクトチェックAI + 編集者AIによる校正
- **動的ペルソナ**: 企業・専門家・ブロガー等、視点を自動/手動で選択
- **カスタムジャンル**: オリジナルの記事タイプをAIで最適化・登録
- **同時出力**: note用（Markdown）とLinkedIn用（短縮・絵文字付き、387〜1568文字目安）を一度に生成
- **入力ソース拡張**: URL / PDF / DOCX / txt / md / 画像アップロードに対応
- **入力回復UI**: 狭幅では必須の資料入力を開始方式の説明より先に表示し、資料不足時は1つの警告からソースURL欄へ戻れる

## プロジェクト構造

```
notecode/
├── note/                    # 記事生成コア
│   ├── note_writer_app.py   # メインUI (NiceGUI)
│   ├── article_generator.py # 生成ロジック
│   ├── llm_client.py        # OpenAI連携
│   └── ALGORITHM.md         # アルゴリズム仕様
├── core/                    # 共通ユーティリティ
│   ├── token_tracker.py     # コスト管理
│   └── model_selector.py    # モデル選択
├── config.json              # LLM設定
├── noteout/                 # SaaS外注用コア
├── archive/                 # SEO/AIO関連（別プロジェクト移管予定）
├── WORKLOG.md               # 作業記録
└── run_note.bat             # 起動スクリプト
```

## セットアップ

1. **環境変数**: `.env` ファイルに `OPENAI_API_KEY` を設定
2. **モデル設定**: `config.json` の `llm.model_name` 等を必要に応じて調整
3. **依存関係**: `pip install -r requirements.txt`
4. **起動**: `run_note.bat` をダブルクリック

例: `config.json`
```
{
  "llm": {
    "model_name": "gpt-4.1-mini-2025-04-14",
    "fallback_model": "gpt-4o",
    "reasoning_effort": "low",
    "timeout": 30,
    "top_p": null
  }
}
```

## 技術スタック

- **UI**: NiceGUI
- **LLM**: GPT-4.1-mini-2025-04-14
- **検証**: Forensic Linguistics + Multi-Agent Editorial Review
