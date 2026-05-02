# 記事タイプ確定表（Single Source / Phase01確定）

## 固定ルール
- 以下7キーを **変更禁止** とする（追加・改名・削除禁止）。
- custom genreはPhase01では運用対象外（Phase04で導線整理）。

| 表示名 | 内部キー（固定） | 媒体差分（note/hatena/seo） | contract補足 |
|---|---|---|---|
| 解説 | `explanatory_article` | 共通（SEOは見出し/根拠を強化） | `evidence_priority=high` |
| 日常 | `daily_story` | note/hatena寄り（SEOは冗長抑制） | `style_compact_for_seo=true`（`media=seo`時） |
| ブランド | `branding` | 共通（SEOは主張根拠を明示） | `brand_claim_with_evidence=true` |
| お知らせ | `announcement` | 共通（質問スキップ既定） | `question_mode=skip_default` |
| 事例 | `case_study` | SEOは再現手順・数値項目を強化 | `repro_steps_required=true` |
| 業界分析 | `industry_analysis` | SEOは比較軸・結論の構造化を強化 | `structured_axes_required=true` |
| 比較レビュー | `comparative_review` | SEOは比較表現・評価軸を強化 | `comparison_axes_required=true` |

## 互換マッピング（現行UI/既存キー -> 固定キー）
- `ai` -> `explanatory_article`
- `daily_happenings` -> `daily_story`
- `corporate_culture` -> `branding`
- `company_profile` -> `branding`
- `company_introduction` -> `branding`
- `corporate` -> `branding`

## 正規化の確定仕様
- `article_type=daily_story` かつ `media=seo` のとき、system-ownedで `style_compact_for_seo=true` を付与する。
- `style_compact_for_seo` はUI編集不可（contract正規化のみで決定）。

