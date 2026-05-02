# Codex 作業指示書（2026-02-28）

## 概要

コトメイク（`C:\tetie\notecode`）の記事生成エンジンに対して「R19: 人間ぽさアルゴリズム再設計」を実施済み。
再起動後の回帰テストと実生成による品質確認を行う。

---

## 1. 環境

- 作業ディレクトリ: `C:\tetie\notecode`
- Python: `py` コマンドで起動（`python` ではなく `py` を使用）
- パス: bash内ではフォワードスラッシュを使用（`note/tests/` のように）
- OS: Windows 11

---

## 2. 回帰テスト（最優先）

### 2-1. 全テスト実行

```bash
cd C:\tetie\notecode
py -m pytest note/tests/ -q
```

**期待値: 392 passed, 2 skipped**（skipped はAPI依存テスト）

### 2-2. メインテスト詳細

```bash
py -m pytest note/tests/test_offline.py -v
```

**期待値: 188 passed**

### 2-3. R19関連テスト確認

```bash
py -m pytest note/tests/test_offline.py -v -k "r19"
```

**期待値: 12 passed**。以下のテストが含まれる:
- `test_r19_sentence_under_130_chars_not_split` — 130文字以下の文が分割されない
- `test_r19_theme_keyword_not_diversified` — テーマ語がキーワード多様化されない
- `test_r19_theme_prodrop_cross_paragraph` — テーマ語prodropが段落をまたいで動作
- `test_r19_cap_colloquial_allows_two` — colloquial endingが2回まで許容
- `test_r19_break_ending_monotony_disperses_masu_run` — 文末単調性が分散される
- `test_r19_break_ending_monotony_across_paragraphs` — 段落をまたぐ「ます。」連続も分散される
- `test_r19_break_ending_monotony_handles_arimasu_series` — 「あります。」連続でも分散される
- `test_r19_short_paragraph_not_merged` — 40文字以下の短い段落が結合されない
- `test_r19_soften_assertive_expressions` — 断定的表現がソフトに言い換えられる
- `test_r19_dedupe_cross_section_sentences` — セクション間の同一フレーズ文が削除される
- `test_r19_banned_phrases_expanded` — 新BANNED_PHRASESが含まれている
- `test_r19_ai_like_ending_rewrites_expanded` — 新ENDING_REWRITESが追加されている

---

## 3. テスト失敗時の対応

失敗した場合はログを確認し、以下を判断:

### import エラーの場合
- `style_policy.py` の BANNED_PHRASES / AI_LIKE_ENDING_REWRITES の構文を確認
- `article_generator.py` の `_soften_assertive_expressions` / `_dedupe_cross_section_sentences` が正しく定義されているか確認

### assertion エラーの場合
- テストの期待値と実際の出力を比較
- R19で変更した定数値（`NON_CASUAL_COLLOQUIAL_ENDING_MAX=2`, `max_sentence_chars=130` 等）が正しいか確認

### 修正が必要な場合
- 修正は最小限にし、R19の設計意図（引き算アプローチ＝制御を減らす）を尊重する
- 修正後は必ず `py -m pytest note/tests/ -q` で全テスト通過を確認

---

## 4. 実生成テスト（テスト通過後）

### 4-1. アプリ起動

```bash
cd C:\tetie\notecode
py -m note.note_writer_app
```

ブラウザで `http://127.0.0.1:8080/` を開く

### 4-2. テスト生成条件

以下の条件で記事を生成:
- **テーマ**: 「教育現場でのAI活用」または任意のテーマ
- **記事タイプ**: ai（デフォルト）
- **ソース**: なし or 任意URL1件

### 4-3. 品質チェック項目

生成後、`notecode/logs/latest_generation_output.txt` と `.json` を確認:

| チェック項目 | 確認方法 | OK基準 |
|-------------|---------|--------|
| AI特有の表現 | 「欠かせません」「不可欠です」「恐れがあります」「潜んでいます」を検索 | 0件 |
| 断定的表現 | 「必ず」「確実に」「100%」を検索 | 0件（ソフト化されているべき） |
| 文レベル重複 | 同一フレーズ（14文字以上）が2回以上出現するか | 1回以下 |
| review_points | `.json` の `review_points` を確認 | 空 or 軽微なもののみ |
| hard_failed | `.json` の `hard_failed` を確認 | False |
| 見出し順 | 導入→本論→結論の順になっているか | OK |
| 文末の多様性 | 「ます。」が4連続以上続かないか | 3連続以下 |

### 4-4. Fingerprint指標（`.json` 内）

| 指標 | 目標値 |
|------|--------|
| `sentence_ending_entropy` | > 1.5 |
| `subject_explicit_rate` | < 0.60 |
| `sentence_length_cv` | > 0.20 |
| `flat_zone_flags` | < 5 |

---

## 5. R19で変更したファイル一覧

| ファイル | 変更概要 |
|---------|---------|
| `config.json` | max_sentence_chars 88→130, paragraph_clog_min_chars 165→240, focus_pipeline_overrides追加 |
| `note/article_generator.py` | _diversify_overused_keywords削除, _extract_theme_entities/prodrop拡張, プロンプト重複排除, _soften_assertive_expressions, _dedupe_cross_section_sentences, _break_ending_monotony, review_points修正閾値緩和 |
| `note/post_processor_mixin.py` | パターン2結合40字制限, CV guard, focus override |
| `human_resonance/style_policy.py` | BANNED_PHRASES+6, AI_LIKE_ENDING_REWRITES+7, AI_TEMPLATE_STRUCTURE_PATTERNS削除 |
| `note/policy_engine.py` | participant_mode追加 |
| `note/custom_genres.json` | participant_mode: "auto" 追加 |
| `note/tests/test_offline.py` | R19テスト10件（新規4+既存6） |

---

## 6. 設計背景（修正判断に必要な知識）

### 引き算アプローチの原則
- 後段処理が互いに打ち消し合い、LLMの自然な揺らぎを破壊していたのが根本原因
- **制御を追加するのではなく、不要な制御を外す**のが正しい方向
- 同じルールが複数箇所（Tier B / core_guide / セクション【ルール】）に記載されるとLLMが硬直する

### review_points の設計変更
- 以前: 検出してUIに表示するだけ（ヒント扱い）
- 現在: 検出した問題を `_run_readability_polish_pass` で実際に修正する
- `_should_run_readability_polish` の閾値を緩和し、断定的表現や結論順序の問題もトリガーにした

### BANNED_PHRASES vs AI_LIKE_ENDING_REWRITES
- BANNED_PHRASES: 文中のどこにあっても削除対象
- AI_LIKE_ENDING_REWRITES: 文末パターンを別表現に置換（意味は保持）
- 両方に追加する必要はない。文末なら REWRITES、文中なら BANNED

---

## 7. Codex の作業範囲

本指示書は **notecode（コトメイク）のテスト・品質確認のみ** を対象とする。
aio2-main（コトミガキ）の PLAN2 は別途スケジュール。

---

## 8. 実行前の確認事項（重要）

### 8-1. テスト期待値の確定

本文書の期待値は `2026-02-28 14:00` 時点。実行前に最新を確認:
```bash
cd C:\tetie\notecode
py -m pytest note/tests/ --co -q | tail -1    # 実装数確認
py -m pytest note/tests/ -q --tb=no           # 実行結果確認
```

**期待値と異なる場合**:
- テストの新規追加・削除がないか確認（`git log --oneline note/tests/` で確認可能）
- 異なる場合は本文書の期待値を更新してから報告

### 8-2. 変更ファイルの完全性確認

以下のファイルが実際に変更されているか確認:
```bash
git diff --name-only HEAD~1 | grep -E "(config.json|article_generator.py|post_processor_mixin.py|style_policy.py|policy_engine.py|custom_genres.json|test_offline.py)" | wc -l
```

期待値: **7ファイル**（すべて修正済みであること）

---

## 9. 参照ドキュメント

- 全体入口: `C:\tetie\AGENTS.md`
- 作業記録: `C:\tetie\WORKLOG.md`（2026-02-28セクション）
- アルゴリズム仕様: `C:\tetie\ALGORITHM.md`
- プロジェクト優先順位: `C:\tetie\WORKLOG.md` の「予定」セクション
