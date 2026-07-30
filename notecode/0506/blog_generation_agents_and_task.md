# AGENTS.md

## Project Goal

日本語ブログ生成ソフトを開発する。ユーザーが URL、PDF、Word ファイルなど複数ソースをアップロードし、UI で記事分類を指定すると、ソース情報に基づいた自然な日本語ブログを生成する。

重要な目的は以下。

- AI感の少ない自然な日本語ブログを生成する
- 複数ソースの重複、矛盾、古い情報を整理する
- ソース外の事実を追加しない
- 日本語特有の主語省略、ゼロ照応、一人称揺れを制御する
- 記事分類ごとに文体、構成、CTA、主語省略レベルを変える
- 生成、編集、検査、限定修正を分離し、品質を安定させる

---

## Core Architecture

一発生成は避ける。以下のパイプラインを基本とする。

```text
Source Upload
  ↓
Text Extraction / Noise Removal
  ↓
Source Card Extraction
  ↓
Knowledge Pack Integration
  ↓
Article Brief Generation
  ↓
Draft Writer
  ↓
Style Editor
  ↓
Japanese Quality Checker
  ↓
Targeted Rewriter
  ↓
Final Article
```

### Why This Architecture

長文ソースを直接ブログ生成プロンプトに入れると、以下が起きやすい。

- 意味の重複
- 一人称の揺れ
- 見出し間の話題重複
- ゼロ照応による主体不明
- ソース外事実の混入
- AIっぽい定型表現
- 分割生成時のトーン不一致

そのため、ソース本文を直接生成モデルに渡しすぎず、記事生成用の構造データに変換してから本文生成する。

---

# Agent Definitions

## 1. source_card_extractor

### Role

URL、PDF、Word などの各ソースから、ブログ作成に使える事実、表現、注意点を抽出する。

### Input

```json
{
  "source_id": "pdf_001",
  "source_type": "pdf | url | word | manual",
  "source_text": "...",
  "metadata": {
    "title": "...",
    "url": "...",
    "published_or_updated_at": "..."
  }
}
```

### Output

```json
{
  "source_id": "pdf_001",
  "source_type": "pdf",
  "title": "会社案内2026",
  "published_or_updated_at": "2026-04-20",
  "reliability": "official | external | user_uploaded | unknown",
  "main_topics": ["事業内容", "沿革", "代表メッセージ"],
  "facts": [
    {
      "fact_id": "F001",
      "claim": "株式会社Aは2018年に創業した",
      "category": "company_profile",
      "importance": 5,
      "source_span": "p.2",
      "usable_in_article": true
    }
  ],
  "quotes_or_phrases": [
    {
      "text": "地域に根ざしたサービス",
      "usage": "tone_reference",
      "source_span": "p.4"
    }
  ],
  "warnings": [
    "売上高の記載は古い可能性あり"
  ]
}
```

### Rules

- 要約ではなく、記事に使える素材として抽出する
- 推測で情報を補完しない
- 数字、日付、固有名詞は原文に忠実に扱う
- 古い可能性がある情報は warnings に入れる
- 曖昧な情報は断定しない

---

## 2. knowledge_pack_integrator

### Role

複数の source cards を統合し、ブログ本文生成に使う article_knowledge_pack を作る。

### Input

```json
{
  "source_cards": []
}
```

### Output

```json
{
  "article_knowledge_pack": {
    "confirmed_facts": [
      {
        "claim_id": "C001",
        "claim": "株式会社Aは2018年創業で、地域密着型のサービスを展開している",
        "supporting_fact_ids": ["F001", "F014"],
        "confidence": "high | medium | low",
        "preferred_expression": "2018年の創業以来、地域に根ざしたサービスを展開"
      }
    ],
    "conflicts": [
      {
        "issue": "従業員数がPDFでは30名、Webでは35名",
        "resolution": "Webの更新日が新しいため35名を採用",
        "do_not_mention": false
      }
    ],
    "deduped_themes": [
      "地域密着",
      "丁寧な対応",
      "法人向けサービス",
      "代表者の想い"
    ],
    "do_not_infer": [
      "業界No.1とは書かない",
      "効果を保証する表現は使わない"
    ]
  }
}
```

### Rules

- 同じ意味の事実を統合する
- ソース間の矛盾を検出する
- 原則として新しい公式情報を優先する
- 使うべき claim と使わない情報を分ける
- 誇大表現、根拠不足、法務リスクのある表現を do_not_infer に入れる

---

## 3. article_brief_builder

### Role

UI 設定と article_knowledge_pack をもとに、本文生成用の article_brief を作る。

### Input

```json
{
  "ui_settings": {
    "category": "企業紹介",
    "target_reader": "初めて会社名を知った見込み顧客",
    "goal": "会社への信頼感を高め、問い合わせにつなげる",
    "first_person": "当社",
    "tone": "誠実で親しみやすい",
    "target_chars": 1200,
    "cta": "問い合わせ"
  },
  "article_knowledge_pack": {}
}
```

### Output

```json
{
  "article_brief": {
    "category": "企業紹介",
    "target_reader": "初めて会社名を知った見込み顧客",
    "goal": "会社への信頼感を高め、問い合わせにつなげる",
    "narrator": "当社",
    "persona": {
      "tone": "誠実で親しみやすい",
      "distance": "丁寧だが堅すぎない",
      "avoid": [
        "過剰に感動的な表現",
        "AIがよく使う抽象表現",
        "同じ意味の言い換えの連発"
      ]
    },
    "article_structure": [
      {
        "heading": "地域に根ざしたサービスを大切にしています",
        "purpose": "会社の基本姿勢を伝える",
        "claims": ["C001", "C004"],
        "approx_chars": 300,
        "main_subject": "当社",
        "secondary_subjects": ["地域のお客様"],
        "discourse_rules": {
          "first_sentence_subject_required": true,
          "subject_shift_requires_explicit_marker": true,
          "avoid_repeating_subject_more_than_twice": true
        }
      }
    ],
    "style_rules": {
      "sentence_length": "一文は原則60字以内",
      "paragraph_length": "2〜4文",
      "first_person": "当社",
      "ending_style": "です・ます調",
      "forbidden_phrases": [
        "いかがでしたでしょうか",
        "〜と言えるでしょう",
        "〜することができます",
        "この記事では",
        "ぜひ参考にしてみてください"
      ]
    }
  }
}
```

### Rules

- article_brief は本文生成の唯一の設計書とする
- 各見出しに使う claim_id を明示する
- 同じ claim_id を複数見出しに使い回さない
- 一人称、文体、CTA、禁止表現を明確にする
- 主体、話題、主語省略ルールをセクション単位で持たせる

---

## 4. draft_writer

### Role

article_brief と article_knowledge_pack に基づき、ブログ初稿を作成する。

### Prompt Template

```text
あなたは日本語ブログの初稿作成担当です。

目的:
article_brief と knowledge_pack に基づき、ブログ初稿を作成する。

守ること:
- source claims にある事実だけを使う
- article_brief の構成に従う
- 一人称は {{first_person}} のみ
- 各見出しでは指定された claim_id のみ使う
- 同じ claim を別見出しで繰り返さない
- 完成度より、事実の正確さと構成の自然さを優先する

避けること:
- AIっぽい総括
- 根拠のない美辞麗句
- 誇大表現
- ソース外の補完

日本語制御:
- 段落の最初では、主語または話題を明示する
- 同じ段落内で主体が変わらない場合のみ、主語省略を許可する
- 主体が「当社」「お客様」「スタッフ」「地域」「代表者」の間で変わる場合は、必ず明示する
- 責任、予定、実績、依頼、価格、日程に関する文では主語を省略しない
- 一人称は article_brief.style_rules.first_person のみ使用する

出力:
ブログ本文のみ。
```

### Rules

- 本文生成時に元ソース全文を渡しすぎない
- 原則として article_brief と confirmed_claims を使う
- 生成ロールに過剰な編集責任を持たせない
- 完成度より、正確な初稿を優先する

---

## 5. style_editor

### Role

初稿の事実を変えずに、日本語として自然に整える。

### Prompt Template

```text
あなたは日本語ブログの編集担当です。

目的:
初稿の事実を変えずに、自然で読みやすい日本語に整える。

編集対象:
- 一人称の統一
- 文末の単調さ
- 接続語の重複
- 意味の重複
- 主語省略の不自然さ
- 段落の流れ
- AIっぽい定型表現

禁止:
- 新しい事実を追加しない
- 数字・固有名詞・日付を変更しない
- claim にない強みや実績を足さない
- 見出し構成を大きく変えない

出力:
編集後の本文のみ。
```

### Rules

- 事実判断を主目的にしない
- 文体、重複、一人称、主語省略に集中する
- 長すぎる文を分割する
- 接続語や文末を分散する
- CTA を自然にする

---

## 6. japanese_quality_checker

### Role

編集後本文を公開前に検査し、問題箇所を JSON で返す。

### Input

```json
{
  "article_brief": {},
  "article_knowledge_pack": {},
  "edited_article": "..."
}
```

### Output

```json
{
  "pass": false,
  "score": 82,
  "issues": [
    {
      "type": "subject_ambiguity",
      "severity": "medium",
      "text": "今後も改善を続けていきます。",
      "reason": "誰が改善するのか曖昧",
      "fix_instruction": "主語を当社として明示する"
    },
    {
      "type": "ai_like_phrase",
      "severity": "low",
      "text": "ぜひ参考にしてみてください。",
      "reason": "汎用的なAI風の締め表現",
      "fix_instruction": "記事内容に即した自然な締めに変更する"
    }
  ],
  "rewrite_needed": true
}
```

### Check Items

- source claims にない事実がないか
- 一人称が統一されているか
- 主語省略で主体が曖昧な文がないか
- ゼロ照応のリスクがある文がないか
- 同じ意味の説明が重複していないか
- AIっぽい定型表現がないか
- 記事分類に合う文体か
- CTA が自然か
- 文末が単調でないか
- 接続語が連続していないか

### Issue Types

```text
unsupported_claim
first_person_inconsistency
subject_ambiguity
zero_anaphora_risk
duplication
ai_like_phrase
style_mismatch
cta_issue
forbidden_phrase
sentence_too_long
ending_repetition
connector_repetition
```

---

## 7. targeted_rewriter

### Role

QA issues で指摘された箇所だけを修正する。

### Prompt Template

```text
あなたは日本語ブログの修正担当です。

目的:
QA issues で指摘された箇所だけを修正する。

守ること:
- 指摘されていない部分は原則変えない
- 事実を追加しない
- 数字、固有名詞、日付を変更しない
- 一人称は {{first_person}} に統一する
- 修正後も自然な日本語にする

入力:
- article_brief
- knowledge_pack
- edited_article
- QA issues

出力:
修正後のブログ本文のみ。
```

### Rules

- 全文再生成ではなく限定修正を行う
- 問題箇所以外の文体を大きく変えない
- QA issues の severity が high または medium のものを優先する
- 修正後に再度 japanese_quality_checker を通す

---

# Japanese-Specific Rules

## First Person Control

一人称は UI で必須指定する。

分類ごとのデフォルト例。

| 記事分類 | 推奨一人称 |
|---|---|
| 日々のできごと | 私たち、店舗名、施設名 |
| 企業紹介 | 当社 |
| お知らせ | 当社、店舗名 |
| 代表ブログ | 私 |
| 採用記事 | 私たち |
| 導入事例 | 企業名、当社 |
| セミナー告知 | 当社、主催者名 |

禁止:

- 「当社」「弊社」「私たち」「当店」などを混在させない
- 自動判定に任せない

---

## Subject Omission Rules

日本語では主語省略を完全禁止しない。制御する。

```text
- 段落の最初の文では主体を明示する
- 同じ段落内で主体が変わらない場合は省略してよい
- 主体が「当社」から「お客様」「地域」「スタッフ」に変わる場合は必ず明示する
- 責任・実績・予定・約束に関わる文では主体を明示する
- お知らせ、価格、日程、採用条件では主語を省略しすぎない
```

分類ごとの許容度。

| 記事分類 | 主語省略の許容度 |
|---|---|
| 日々のできごと | 高め。自然さ優先 |
| 企業紹介 | 中。段落冒頭は明示 |
| お知らせ | 低め。誰が何をするか明確に |
| 採用 | 中。会社と応募者の主体を分ける |
| 導入事例 | 低め。自社・顧客・第三者の区別が重要 |
| 代表ブログ | 高め。ただし「私」と「当社」を混ぜない |

---

## Zero Anaphora Handling

ソース抽出または knowledge_pack 統合時に、曖昧な主体を補完する。

```json
{
  "claim_id": "C014",
  "surface_text": "資料を確認し、問題がなければ明日公開します。",
  "explicit_subject": "当社",
  "explicit_object": "お知らせページ",
  "actor": "当社の担当者",
  "action": "確認し、公開する",
  "allowed_omission": true,
  "blog_expression": "当社では内容を確認したうえで、問題がなければ明日お知らせページに公開します。"
}
```

本文生成時は、自然な範囲で省略してよい。ただし、誰の行動・意見・実績か不明になる省略は禁止。

---

## Discourse State

各セクションに談話状態を持たせる。

```json
{
  "discourse_state": {
    "current_subject": "当社",
    "current_topic": "地域密着の取り組み",
    "current_timeframe": "現在",
    "current_reader_relation": "見込み顧客",
    "allowed_pronoun_or_omission": true,
    "must_not_shift_to": ["お客様主体の実績", "代表者個人の意見"]
  }
}
```

---

# Stylometry Checks

スタイロメトリは、文章を直接よくするものではなく、修正指示を作るために使う。

検査対象:

- 平均文長
- 長文率
- 文末分布
- 接続語の反復
- 一人称の揺れ
- 抽象名詞の多用
- 同一表現の反復
- AIっぽい締め表現

出力例。

```json
{
  "stylometry_check": {
    "avg_sentence_length": 54.2,
    "long_sentence_ratio": 0.18,
    "ending_distribution": {
      "です": 12,
      "ます": 18,
      "でしょう": 6,
      "できます": 9
    },
    "repeated_connectors": ["また", "さらに"],
    "first_person_variants": ["当社", "私たち"],
    "risk": "medium",
    "fix_targets": [
      "できます の多用",
      "一人称の揺れ",
      "接続語の単調さ"
    ]
  }
}
```

---

# Article Category Presets

## 日々のできごと

```json
{
  "category": "日々のできごと",
  "tone": "親しみやすく、少し温度感がある",
  "goal": "活動の雰囲気を伝える",
  "avoid": ["企業PR色を強くしすぎる", "大げさな学びで締める"],
  "structure": ["できごとの導入", "具体的な場面", "感じたこと", "自然な締め"],
  "subject_omission_level": "high",
  "cta_strength": "none_or_soft"
}
```

## 企業紹介

```json
{
  "category": "企業紹介",
  "tone": "誠実で信頼感がある",
  "goal": "初見読者に会社の特徴を理解してもらう",
  "avoid": ["業界No.1風の表現", "抽象的な理念だけで終わる"],
  "structure": ["会社の概要", "大切にしている姿勢", "具体的な強み", "問い合わせ導線"],
  "subject_omission_level": "medium",
  "cta_strength": "medium"
}
```

## お知らせ

```json
{
  "category": "お知らせ",
  "tone": "簡潔で正確",
  "goal": "必要情報を迷わず伝える",
  "avoid": ["前置きが長い", "情緒的すぎる", "曖昧な日時表現"],
  "structure": ["結論", "詳細", "対象者", "注意点", "問い合わせ先"],
  "subject_omission_level": "low",
  "cta_strength": "low"
}
```

## 採用記事

```json
{
  "category": "採用",
  "tone": "誠実で具体的",
  "goal": "応募前の不安を減らす",
  "avoid": ["家族のような職場など曖昧な表現", "過剰な歓迎ムード"],
  "structure": ["仕事の概要", "働く環境", "向いている人", "応募導線"],
  "subject_omission_level": "medium",
  "cta_strength": "medium"
}
```

---

# Forbidden / Risky Phrases

初期禁止表現。

```text
いかがでしたでしょうか
〜と言えるでしょう
〜することができます
この記事では
ぜひ参考にしてみてください
このように
また、
さらに、
大切にしています
魅力があります
さまざまな
多くの方に
```

注意:
禁止表現は絶対禁止ではなく、文脈次第でリスク判定する。特に「また」「さらに」は連続使用や多用を問題にする。

---

# Publish Readiness

公開可否スコアを出す。

```json
{
  "publish_readiness": {
    "score": 86,
    "auto_publish_allowed": false,
    "reasons": [
      "一人称は統一済み",
      "根拠なし事実はなし",
      "主語省略リスクが2箇所残る",
      "CTAがやや定型的"
    ]
  }
}
```

目安。

| スコア | 処理 |
|---:|---|
| 90以上 | 自動公開候補 |
| 80〜89 | 人間確認 |
| 70〜79 | 自動修正後に再検査 |
| 69以下 | 再生成 |

企業紹介、お知らせ、採用、医療、士業、金融系は自動公開しない。

---

# Implementation Notes

## Model Usage

GPT-5.4 mini を使う場合、一つの巨大プロンプトで全工程を処理しない。

推奨:

- 抽出は source_card_extractor
- 統合は knowledge_pack_integrator
- 記事仕様は article_brief_builder
- 本文生成は draft_writer
- 編集は style_editor
- 検査は japanese_quality_checker
- 修正は targeted_rewriter

品質重視の案件では、japanese_quality_checker または fact checking のみ上位モデルを使う。

## Structured Outputs

JSON が必要な工程では Structured Outputs / JSON Schema を使う。

対象:

- source_card_extractor
- knowledge_pack_integrator
- article_brief_builder
- japanese_quality_checker
- stylometry_check
- publish_readiness

本文生成工程では自然文のみを出力する。

---

# task.md

## Task: Build Japanese Blog Generation Pipeline

### Objective

URL、PDF、Word ファイルを複数ソースとして受け取り、UI で指定された記事分類に基づいて、AI感の少ない日本語ブログを生成するパイプラインを実装する。

---

## Functional Requirements

### 1. Source Upload

ユーザーは以下のソースを複数アップロードまたは指定できる。

- URL
- PDF
- Word file
- manual text

各ソースには source_id を付与する。

### 2. Text Extraction

各ソースから本文テキストを抽出する。

実装要件:

- URL は本文領域を抽出し、ナビゲーション、フッター、広告を除去する
- PDF はページ番号と対応するテキスト位置を保持する
- Word は見出し、段落、表を可能な範囲で保持する
- 抽出結果には source_span を付与できるようにする

### 3. Source Card Extraction

各ソースから source_card を生成する。

実装対象:

- source_card_extractor agent
- JSON Schema validation
- fact_id の採番
- warnings の抽出

完了条件:

- 各ソースごとに facts が抽出される
- 推測による情報追加がない
- 古い情報や矛盾候補が warnings に入る

### 4. Knowledge Pack Integration

複数 source_card を統合し、article_knowledge_pack を生成する。

実装対象:

- knowledge_pack_integrator agent
- confirmed_facts の生成
- conflicts の生成
- do_not_infer の生成
- deduped_themes の生成

完了条件:

- 同じ意味の fact が統合されている
- 矛盾が検出されている
- claim_id が生成されている
- ブログ本文に使う情報と使わない情報が分離されている

### 5. UI Settings

UI では最低限以下を指定できる。

```json
{
  "category": "日々のできごと | 企業紹介 | お知らせ | 採用 | 導入事例 | セミナー告知 | custom",
  "target_reader": "string",
  "goal": "string",
  "first_person": "当社 | 弊社 | 私たち | 私 | 店舗名 | custom",
  "tone": "string",
  "target_chars": 1200,
  "cta": "string | none",
  "source_priority": ["url", "pdf", "word", "manual"]
}
```

UI 上で first_person は必須にする。

### 6. Article Brief Generation

article_brief_builder により article_brief を生成する。

完了条件:

- 記事分類に合った構成になっている
- 各見出しに claim_id が割り当てられている
- 一人称、禁止表現、文体が明示されている
- セクションごとに main_subject と discourse_rules がある

### 7. Draft Generation

article_brief と article_knowledge_pack から初稿を生成する。

完了条件:

- ブログ本文のみを出力する
- article_brief の見出し構成に従う
- 指定 claim のみを使う
- 一人称が統一されている
- ソース外事実を追加しない

### 8. Style Editing

style_editor で初稿を編集する。

完了条件:

- 事実を変えずに日本語を自然にする
- 文末の単調さを改善する
- 接続語の反復を減らす
- 主語省略の不自然さを改善する
- AIっぽい定型表現を削る

### 9. Japanese Quality Check

japanese_quality_checker で品質検査する。

検査項目:

- unsupported_claim
- first_person_inconsistency
- subject_ambiguity
- zero_anaphora_risk
- duplication
- ai_like_phrase
- style_mismatch
- cta_issue
- forbidden_phrase
- sentence_too_long
- ending_repetition
- connector_repetition

完了条件:

- score が返る
- issues が JSON で返る
- rewrite_needed が返る

### 10. Targeted Rewrite

QA issues がある場合、targeted_rewriter で限定修正する。

完了条件:

- 指摘箇所だけを修正する
- 事実追加がない
- 数字、固有名詞、日付を変えない
- 修正後に再度 japanese_quality_checker を通す

---

## Non-Functional Requirements

### Quality

- 生成本文は人間編集者が公開前確認できる品質を目指す
- 自動公開は score 90 以上かつ high severity issue なしの場合のみ候補とする
- 医療、士業、金融、採用条件、価格、法務リスクのある内容は自動公開しない

### Reliability

- 各 agent の入出力をログに残す
- article_knowledge_pack と article_brief を保存する
- 最終本文がどの claim_id に基づくか追跡できるようにする

### Evaluation

最低 20〜100 件の eval セットを作る。

評価項目:

- 一人称一致率
- 禁止表現の出現率
- ソース外事実の混入率
- 重複段落率
- 記事分類一致率
- CTA自然度
- 人間編集者の5段階評価
- 公開可能率

---

## Acceptance Criteria

### MVP Acceptance

- 複数ソースを入力できる
- source_card が生成される
- knowledge_pack が生成される
- UI 記事分類から article_brief が生成される
- draft_writer → style_editor → japanese_quality_checker → targeted_rewriter が動く
- 最終ブログ本文が生成される
- QA score と issues が確認できる

### Quality Acceptance

- 一人称揺れが検出・修正される
- 明らかなソース外事実が検出される
- 主語省略による主体不明が検出される
- 「いかがでしたでしょうか」などの定型表現が検出される
- 同じ claim の重複使用が抑制される
- 記事分類ごとの文体差が出る

---

## Suggested File Structure

```text
/app
  /agents
    source_card_extractor.ts
    knowledge_pack_integrator.ts
    article_brief_builder.ts
    draft_writer.ts
    style_editor.ts
    japanese_quality_checker.ts
    targeted_rewriter.ts
  /schemas
    source_card.schema.json
    knowledge_pack.schema.json
    article_brief.schema.json
    quality_check.schema.json
    publish_readiness.schema.json
  /prompts
    source_card_extractor.md
    knowledge_pack_integrator.md
    article_brief_builder.md
    draft_writer.md
    style_editor.md
    japanese_quality_checker.md
    targeted_rewriter.md
  /services
    text_extraction.ts
    source_priority.ts
    stylometry.ts
    article_pipeline.ts
  /evals
    cases.jsonl
    metrics.ts
```

---

## Development Order

1. Define JSON schemas
2. Implement text extraction placeholders
3. Implement source_card_extractor
4. Implement knowledge_pack_integrator
5. Implement article_brief_builder
6. Implement draft_writer
7. Implement style_editor
8. Implement japanese_quality_checker
9. Implement targeted_rewriter
10. Add publish_readiness scoring
11. Add eval cases
12. Add UI controls

---

## Core Principle

モデルに長い指示を読ませて賢く振る舞わせるのではなく、モデルが迷わない中間データを作る。

```text
Bad:
Long sources + huge prompt → final blog

Good:
Sources → structured facts → article brief → draft → edit → check → targeted rewrite
```

これを守る。守らないと、重複、一人称揺れ、ゼロ照応、AIっぽいまとめが復活する。

