# GPT-5.4 相談結果：カテゴリ別パラメータと読者段階

最終更新: 2026-03-07  
出典: ユーザーが GPT-5.4 にブログ生成アルゴリズムを相談した返答の要約  
参照: [Using GPT-5.4](https://developers.openai.com/api/docs/guides/latest-model/), notecode/ALGORITHM.md, algorithm_complexity_and_gpt54_direction.md

---

## 1. 相談で評価された設計

**①ソース → ②書く内容指示 → ③カテゴリUI → ④生成** は、**法人ブログ生成アルゴリズムとしてかなり良い構造**との評価。

- 現行 notecode の「ソース（URL/PDF/テキスト）→ user_prompt → article_type 等 UI → generate」と一致している。
- 内部で「カテゴリ → パラメータ変更 / プロンプト変更 / 構成変更」をやる設計も、現行の contract resolve → discourse plan → section generation と対応する。

---

## 2. GPT-5.4 推奨の基本パラメータ（ブログ用途）

- **reasoning: none**（ブログは推論不要）
- **top_p: 0.9**
- **presence_penalty: 0.2**
- **frequency_penalty: 0.1**

※ temperature / top_p は reasoning が `none` のときのみ使用可能（公式仕様）。notecode の「本文は temperature で揺らぎ」と整合。

---

## 3. カテゴリ別パラメータ（相談返答の要約）

| カテゴリ（相談側） | 目的 | temperature | verbosity | presence_penalty | スタイル・構成 |
|--------------------|------|-------------|-----------|------------------|----------------|
| **① 解説（HowTo/ナレッジ）** | SEO・専門性・信頼性 | 0.2〜0.4 | high | (基本 0.2) | 見出し多め・図解・FAQ・手順。結論→概要→背景→具体例→FAQ→まとめ |
| **② 日々のできごと（ストーリー/日記）** | ファン化・人間味・SNS | 0.7 | medium | 0.5 | ストーリー・感情・会話。今日の出来事→背景→感じたこと→学び→読者への問い |
| **③ 商品・企業ブランディング** | ブランド理解・共感・世界観 | 0.5 | high | 0.4 | ストーリー・思想・開発秘話。問題→なぜ作った→どう作った→思想→未来 |
| **④ お知らせ** | 情報伝達・正確性（SEO不要） | 0.1 | low | 0 | 公式・簡潔。概要→詳細→日時→リンク |

### 現行 notecode との対応

| 相談のカテゴリ | notecode の article_type | メモ |
|----------------|--------------------------|------|
| ① 解説 | `ai`, `explanatory_article` | 解説記事。temperature 低め・verbosity high にすると整合。 |
| ② 日々のできごと | `daily_happenings`（branding と同プロファイル） | ストーリー系。temperature 0.7, presence_penalty 高め。 |
| ③ ブランディング | `branding` | 既存。temperature 0.5, verbosity high。 |
| ④ お知らせ | `announcement` | 既存。**temperature 0.1, verbosity low** は research２の「事実ロック・簡潔」と一致。 |
| ⑤ 社員・チーム紹介 | （現行は corporate_culture / company_profile に近い） | 採用・開発者紹介。 |
| ⑥ ケーススタディ | `case_study` | 既存。 |
| ⑦ 思想 / thought leadership | （ai や column に近い） | 業界分析・マーケ戦略。 |
| ⑧ 比較・レビュー | （カスタムジャンル or ai の一種） | SEO 強い。 |

---

## 4. 取り込み案（実装方針）

### 4.1 すぐ効かせられるもの

- **reasoning: none**  
  config で `reasoning_effort: "none"` にし、GPT-5.4 利用時は temperature を有効にする。既に gpt54_migration_simplification_memo で推奨済み。
- **お知らせ（announcement）**  
  section 生成時の temperature を **0.1〜0.2** に固定（または config で `article_type_params.announcement.temperature` を 0.1 に）。verbosity は API が対応していれば `low`。
- **基本ペナルティ**  
  `presence_penalty: 0.2`, `frequency_penalty: 0.1` を config の llm セクションに追加し、`llm_client` で送信する（モデルが対応する場合のみ）。

### 4.2 カテゴリ別 temperature / verbosity

- **設計**: `config.json` に `llm.article_type_params` のようなマッピングを設け、article_type ごとに `temperature`, `verbosity`, `presence_penalty` を上書きする。
- **例**:
  - `announcement`: temperature 0.1, verbosity low
  - `ai` / `explanatory_article`: temperature 0.2〜0.4, verbosity high
  - `branding`: temperature 0.5, verbosity high
  - `daily_happenings`: temperature 0.7, verbosity medium, presence_penalty 0.5
- **実装**: `article_generator` の section 生成で `article_type` を渡し、`llm_client.generate_text()` が config の article_type_params を参照して temperature / verbosity を決める。

### 4.3 読者段階（認知→興味→比較→購入）

相談では「**カテゴリよりもっと重要なものは読者段階**」との指摘あり。マーケのファネル（認知・興味・比較・購入）で記事の型が変わる。

- **現行**: 明示的な「読者段階」はない。writing_focus（experience / explanation 等）や audience_profile で近い役割はある。
- **取り込み**: まずは **設計メモとして保持**し、UI に「読者段階」を 1 段追加するか、既存の writing_focus / content_goal にマッピングするかを検討する。カテゴリ別パラメータを入れた後に、必要なら discourse plan やプロンプトに「認知訴求／比較訴求」などを渡す形が現実的。

---

## 5. UI の推奨（相談返答）

- **記事タイプ**: 解説 / 日常 / ブランド / お知らせ / 事例 / 業界分析 / 比較レビュー
- **媒体**: note / はてな / SEO記事

notecode は現状「記事タイプ」が article_type で、「媒体」は output_format（note / linkedin）に近い。はてな・SEO記事は将来的な拡張として、まずは **記事タイプ（article_type）とパラメータの連動** を確実にする。

---

## 6. 参照・更新先

- パラメータ変更時: `docs/generation_parameter_tuning_log.md`（なければ WORKLOG または本ファイルにメモ）
- GPT-5.4 移行: `docs/gpt54_migration_simplification_memo.md`
- 方向性・UI 連動: `puran6/algorithm_complexity_and_gpt54_direction.md`
- 現行 article_type: `note/article_generator.py` の `ARTICLE_TYPE_LABELS`, `ZERO_BASE_CATEGORY_CONTRACT_PROFILES`
