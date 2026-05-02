# Human Resonance Pipeline - 進捗管理

## 概要
統計言語学に依存せず、心理学・言語学の知見を活用して「共感・興味・人間味」を生み出すテキスト処理パイプライン。

## ステータス凡例
- [ ] 未着手
- [~] 作業中
- [x] 完了
- [!] 要確認/ブロック

---

## Phase 一覧

| Phase | ファイル名 | 内容 | ステータス |
|-------|-----------|------|------------|
| 0 | phase0_persona.py | 一人称・口癖固定 | [x] 完了 |
| 1 | phase1_empathy.py | 共感注入 | [x] 完了 |
| 2 | phase2_curiosity.py | 興味設計 | [x] 完了 |
| 3 | phase3_humanity.py | 人間味付与 | [x] 完了 |
| 4 | phase4_rhythm.py | リズム・テンポ調整 | [x] 完了 |
| 5 | phase5_editor.py | 編集者校正 + ファクトチェック | [x] 完了 |
| 6 | phase6_legal.py | 法務リスクチェック | [x] 完了 |
| 7 | phase7_sanitize.py | 禁止フレーズ除去 | [x] 完了 |
| 8 | phase8_platform.py | note/LinkedIn最適化 | [x] 完了 |
| - | pipeline.py | 統合実行エンジン | [x] 完了 |
| - | __init__.py | パッケージ初期化 | [x] 完了 |

---

## ドキュメント

| ファイル名 | 内容 | ステータス |
|-----------|------|------------|
| ALGORITHM.md | 人間用アルゴリズム説明 | [x] 完了 |
| PROGRESS.md | 進捗管理（本ファイル） | [x] 完了 |

---

## 次のステップ（明日の作業）

### 優先度: 高 - article_generator.py との統合

#### 作業内容
1. `note/article_generator.py` の `generate()` メソッド末尾で、新パイプラインを呼び出す
2. 既存の `_humanize_check`, `_editor_review`, `_legal_check` を新パイプラインに置き換える

#### 統合コード例
```python
# note/article_generator.py の generate() メソッド内、
# 現在の _editor_review, _legal_check, _humanize_check の代わりに:

from human_resonance import HumanResonancePipeline, PipelineConfig

# パイプライン初期化（generate内またはクラス初期化時）
hr_config = PipelineConfig(
    platform=output_format,  # "note" or "linkedin"
    use_llm_for_legal=True,
    use_llm_for_editor=False,
)
hr_pipeline = HumanResonancePipeline(config=hr_config, llm_client=self.llm)

# 本文処理
hr_result = hr_pipeline.process(
    text=body,
    perspective=perspective,  # "blogger", "corporate", etc.
    source_text=merged_context,  # ファクトチェック用
    hashtags=hashtags,
)
body = hr_result.text

# LinkedIn用も同様に処理
if output_format == "linkedin":
    linkedin_body = hr_result.text  # 既にplatform最適化済み
```

#### 削除/置換対象の既存メソッド
- `_humanize_check` → Phase 1-4 で代替
- `_editor_review` → Phase 5 で代替
- `_legal_check` → Phase 6 で代替
- `_postprocess` → Phase 7 で代替
- `_format_for_linkedin` → Phase 8 で代替

#### 注意事項
- 既存メソッドは一旦残し、新旧両方でテストしてから削除
- `EDITOR_REVIEW_POINTS`, `LEGAL_CHECK_PROMPT` 等の定数は `human_resonance/` に移動済み
- `llm_client` は既存の `self.llm` をそのまま渡す

---

### 優先度: 中 - テスト作業

#### 統合後の確認項目
1. note記事生成が正常に動作するか
2. LinkedIn投稿生成が正常に動作するか
3. 一人称が記事全体で統一されているか
4. 法務チェックが正常に機能するか
5. 禁止フレーズが除去されているか

#### テスト用コマンド（統合後）
```python
# 単体テスト
from human_resonance import analyze_text

sample = "テスト用の記事本文..."
result = analyze_text(sample)
print(result["total_resonance_score"])
```

---

### 優先度: 低 - 将来タスク

| タスク | 内容 |
|--------|------|
| パフォーマンス最適化 | 長文での処理速度改善 |
| スコア可視化 | UI上で共感/興味/人間味スコアを表示 |
| A/Bテスト | 旧アルゴリズムと新アルゴリズムの比較 |

---

## 作業ログ

### 2026-01-31
- プロジェクト開始
- PROGRESS.md 作成
- ALGORITHM.md 作成（人間用アルゴリズム説明書）
- Phase 0〜8 全ファイル作成完了
  - phase0_persona.py: 一人称・口癖固定
  - phase1_empathy.py: 共感注入（感情心理学、ナラトロジー、語用論）
  - phase2_curiosity.py: 興味設計（認知心理学、修辞学）
  - phase3_humanity.py: 人間味付与（心理言語学、発達心理学）
  - phase4_rhythm.py: リズム調整（散文リズム論）
  - phase5_editor.py: 編集者校正 + ファクトチェック
  - phase6_legal.py: 法務リスクチェック（景表法、薬機法等）
  - phase7_sanitize.py: 禁止フレーズ・インジェクション除去
  - phase8_platform.py: note/LinkedIn最適化
- pipeline.py 作成（統合実行エンジン）
- __init__.py 作成（パッケージ化）

