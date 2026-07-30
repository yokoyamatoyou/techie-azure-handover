# 日本語ライティング品質アルゴリズム監査メモ（結論・重大指摘・修正方針）

## 0. 前提
- 目的: notecode 生成アルゴリズムが「AIっぽくない自然な文章」を安定して出せる設計かを、仕様（ALGORITHM.md）と実装（Python）両面から監査。
- 監査対象ファイル:
  - `ALGORITHM.md`
  - `article_generator.py`
  - `note_writer_app.py`
  - `post_processor_mixin.py`
  - `prompt_echo_detector.py`
  - `semantic_dedupe.py`（後から追加アップロード）

---

## 1. 結論（5行以内）
**判定: 不可（現状のまま本番運用は危険）**
- 主因1: `hard_failed=True` が **UI 依存**で fail-closed が実装境界で保証されない（UI外経路で fail-open し得る）。
- 主因2: prompt echo 対策が **must_cover を参照に入れて substring 包含判定**するため、偽陽性（正常文削除/ブロック）構造が避けられない。
- 主因3: ブロック出力も監査ログに保存され、漏えい面の逃げ道が残る。
- 主因4: UI ガードが `issue_count>0` で即ブロックし得て、安定運用を阻害。

---

## 2. 重大指摘トップ10（severity順）

> 形式: Severity / 位置（ファイル・行 or 関数）/ 問題 / 再現 / 最小修正

### 1) Severity: Critical — hard_failed の fail-closed が UI 依存
- 位置
  - `article_generator.py` `_postprocess_article`（hard_failed を返すだけ）
  - `note_writer_app.py` `_evaluate_generation_output_guard`（UI 側で止める前提）
- 問題
  - `hard_failed=True` でも generator は例外も停止もせず本文を返す。「fail-closed by UI」という設計依存が残り、UI 外経路（API/バッチ/別UI）で fail-open。
- 再現
  - hard/enforce 設定で文法破綻を誘発 → generator 直呼びで本文が返る。
- 最小修正
  - generator 側で `hard_failed && mode==enforce` の場合 **例外送出**または返却値に **`blocked=True`** を付与し、呼び出し側で必ず拒否。

### 2) Severity: Critical — prompt echo 検出が must_cover 誤爆（substring 包含）
- 位置
  - `prompt_echo_detector.py` `_has_reference_echo`: `ref_norm in sent_norm`
  - `article_generator.py` `build_prompt_echo_references`: must_cover を references に投入
  - `post_processor_mixin.py` `_clean_meta_output`: 検出 segment を無条件 drop
- 問題
  - must_cover が 8文字以上程度の名詞句だと、本文中の自然な使用まで prompt echo 判定→削除/ブロック。
- 再現
  - must_cover="料金体系の比較" → 本文で普通に使うと段落が落ちる。
- 最小修正
  - references から **must_cover を除外**（まず止血）。
  - 包含判定は撤廃/条件化（長文 ref のみ許可、短文は類似度閾値で二段判定）。
  - drop は「メタ強一致」条件付きに限定。

### 3) Severity: Critical — ブロック出力もスナップショット保存（漏えい経路）
- 位置
  - `note_writer_app.py` `_persist_latest_generation_snapshot`
- 問題
  - UI でブロックした出力も固定パスへ保存。prompt echo や機密が混入した場合、漏えい面の逃げ道。
- 再現
  - user_prompt にメール/電話/内部語を混入→ブロック→ログに本文が残る。
- 最小修正
  - ブロック時は本文保存しない（メタ+ハッシュのみ） or redaction 後に保存。

### 4) Severity: High — `issue_count>0` をブロック条件に入れている
- 位置
  - `note_writer_app.py` `_evaluate_generation_output_guard`
- 問題
  - hard/soft 分離と矛盾し、軽微な揺らぎで停止→再生成ループ/ガード無効化圧を誘発。
- 再現
  - `contextual_naturalness_report.issue_count=1` が頻発する設定で常時ブロック。
- 最小修正
  - `issue_count` は監視指標へ降格（shadow ログのみ）。ブロックは hard/重大のみ。

### 5) Severity: High — 仕様（minimal postprocess）と実装（多段変形）が乖離
- 位置
  - `ALGORITHM.md` Current: "minimal postprocess" 記載
  - `article_generator.py` 実装: resonance/clean/polish/compacted pipeline 等
- 問題
  - 説明と挙動が別物になり、監査・回帰・事故時説明が破綻。
- 再現
  - 運用が「minimalだから意味破壊しない」前提→実際は多段で語彙/文体/改行が変わる。
- 最小修正
  - 仕様を実装に合わせて更新するか、Current 経路を本当に minimal に分岐。

### 6) Severity: High — LinkedIn 文字数超過時に末尾が `.`
- 位置
  - `article_generator.py` `_format_for_linkedin`
- 問題
  - 日本語本文末尾が `.` になるのは強い違和感（AIっぽさシグナル）。
- 再現
  - target_chars 超過 → `.` 付与。
- 最小修正
  - `.` を `。` または `…` に変更。できれば句点境界で切る。

### 7) Severity: High — demographic label の一律置換が語義破壊し得る
- 位置
  - `post_processor_mixin.py` `_clean_meta_output`（"高齢者"→"読者" 等）
  - `ALGORITHM.md`（語義破壊を禁止の趣旨）
- 問題
  - 属性が内容の核の場合に不正確/不自然。
- 再現
  - 「高齢者の転倒予防」等で本文の事実まで置換。
- 最小修正
  - 宛先句（CTA）に限定、本文説明は温存。もしくはデフォルトOFF＋置換箇所数ログ。

### 8) Severity: Medium — 文破綻検出は過検知/取りこぼしリスク
- 位置
  - `article_generator.py` 文法破綻検出（助詞終止/途中切れ/混在）
- 問題
  - 体言止め等の正当例を誤検知し得る一方、混在検出は閾値が粗く取りこぼし。
- 再現
  - 見出し直下の短文/箇条書きで破綻カウント増。
- 最小修正
  - 見出し直下/箇条書き/引用を除外。
  - polite/plain は比率・段落単位で判定。

### 9) Severity: Medium — 改行 jitter が再現性/回帰を壊し得る
- 位置
  - `post_processor_mixin.py` `_fix_paragraph_clogging`（閾値 jitter + ランダム改行）
- 問題
  - 微小差で改行挙動が変わり、評価ブレ/回帰不安定。
- 再現
  - 同一テーマで1文違い→改行位置が変わりスコア分散増。
- 最小修正
  - jitter を決定的ルールへ寄せる or テスト時に jitter=0 固定。

### 10) Severity: Medium — `parallel_sections` のスレッドセーフ性不明
- 位置
  - `article_generator.py` `ThreadPoolExecutor` で並列生成
- 問題
  - 同一 `self` 共有でクライアント非スレッドセーフの場合に品質揺れ/交差汚染。
- 再現
  - parallel_sections=True 高負荷で揺れ増/例外。
- 最小修正
  - クライアントを thread-local 化、または並列無効化設定。

---

## 3. 「AIぽさ」観点の定量チェック提案（最低8指標）

> 目的: 生成品質を“観測→改善→回帰”できるようにする。

1) 文末エントロピー
- 定義: 文末終止カテゴリ分布のエントロピー
- 推奨閾値: 1.6〜2.4
- 解釈: 低=定型連打 / 高=文体散乱

2) 接続詞開始率
- 定義: 文頭が接続詞で始まる割合
- 推奨閾値: ≤0.25
- 解釈: 超過=論説テンプレ化

3) 同型文反復率
- 定義: 正規化文型の上位3型合計比率
- 推奨閾値: ≤0.18
- 解釈: 超過=構文テンプレ反復

4) n-gram反復率（文字4-gram）
- 定義: 重複4-gramの比率
- 推奨閾値: ≤1.5%
- 解釈: 超過=言い換え不足/冗長

5) 名詞化率
- 定義: 「こと/もの/ため/点/面/状況」等の抽象止め比率
- 推奨閾値: ≤0.22
- 解釈: 超過=レポート文体化

6) 主語明示率
- 定義: 主語・呼びかけ語を含む文の割合
- 推奨閾値: 0.10〜0.35
- 解釈: 低=無機質 / 高=くどい

7) 文長CV
- 定義: 文長の変動係数
- 推奨閾値: 0.35〜0.75
- 解釈: 低=単調 / 高=破綻疑い

8) ですます/常体混在指数
- 定義: polite 終止と plain 終止の混在率（引用除外）
- 推奨閾値: 指定口調なら片方≤2%
- 解釈: 超過=修復/後処理で口調崩れ

9) prompt echo 率
- 定義: 出力が入力（user_prompt 等）と高類似な部分の割合
- 推奨閾値: 0%（許容でも≤0.5%）
- 解釈: 超過=指示文混入 or 検出不足

10) 句読点異常率
- 定義: `.` 終端や不自然な句読点パターン密度
- 推奨閾値: `.` 終端=0%
- 解釈: 超過=整形バグ/外形AIっぽさ

---

## 4. 失敗パターン別テスト設計（最低12ケース）

1) must_cover 誤爆（短い名詞句）
- 入力: must_cover="料金体系の比較" 等
- 期待: 本文で使用しても削除/ブロックされない
- 切り分け: echo detector 発火 → clean_meta drop

2) user_prompt の丸写し
- 入力: user_prompt に番号付き指示
- 期待: 指示文が出力に残らない、本文欠落なし
- 切り分け: instructional pattern vs 参照一致

3) 間接プロンプト注入（ソースにIGNORE文）
- 入力: ソース本文に "IGNORE ALL…" を混入
- 期待: 出力に混入しない
- 切り分け: detector パターン検知/サニタイズ

4) hard_failed のE2E fail-closed
- 入力: 文法破綻を増やし hard_failed を誘発（enforce）
- 期待: 表示/保存/コピーが止まる
- 切り分け: generator 停止か UI 依存か

5) issue_count 軽微でも出るケース
- 入力: 接続詞多め等で issue_count=1
- 期待: 監視ログのみ、ブロックしない
- 切り分け: UI ガード条件

6) 体言止め（正当例）
- 入力: 段落末を体言止めにする
- 期待: hard_failed にならない
- 切り分け: non-terminal/particle break のカウント

7) 助詞終止（破綻例）
- 入力: 「〜の。」「〜が。」
- 期待: 検出→修復/ブロック
- 切り分け: signals の該当フラグ

8) ですます/常体混在
- 入力: lead ですます、body だ/である
- 期待: 混在検知→修復 or ブロック
- 切り分け: polite/plain 判定閾値

9) 太字崩れ修復の非破壊性
- 入力: `**` 閉じ忘れ/語中強調
- 期待: 表示崩れのみ修正、意味保持
- 切り分け: fix_broken_bold の過剰発火

10) LinkedIn末尾`.`バグ
- 入力: target_chars 超過長文
- 期待: `。`/`…` で終端、`.`禁止
- 切り分け: format_for_linkedin

11) ブロック時ログの機微最小化
- 入力: PII 混入→ブロック
- 期待: 本文非保存 or マスク
- 切り分け: snapshot 保存分岐

12) parallel_sections 再現性
- 入力: parallel_sections=True 同一入力10回
- 期待: 指標分散が許容内
- 切り分け: スレッドセーフ性/例外率

---

## 5. 最小修正ロードマップ（即日 / 1週間 / 2-4週間）

### Phase 1（即日）
- 変更ファイル
  - `prompt_echo_detector.py`: must_cover 誤爆止血（参照集合分離、包含判定条件化）
  - `post_processor_mixin.py`: clean_meta の drop を強一致条件に限定
  - `note_writer_app.py`: `issue_count>0` をブロック条件から除外
  - `article_generator.py`: hard_failed enforce を例外/blocked返却化、LinkedIn末尾`.`修正
- リスク
  - prompt echo 偽陰性が一時増える可能性
- ロールバック条件
  - prompt echo 率が >0.5% に悪化、または指示文混入の報告が増加

### Phase 2（1週間）
- 変更ファイル
  - `ALGORITHM.md`: Current/Legacy の実態に合わせて正本更新 or Current を minimal 分岐
  - `note_writer_app.py`: ブロック時スナップショットの本文非保存/マスク化
  - テスト追加（echo/clean_meta/grammar/linkedin）
- リスク
  - デバッグ容易性が落ちる（本文ログが減る）
- ロールバック条件
  - MTTR 悪化 → 暗号化/権限制御案へ切替

### Phase 3（2-4週間）
- 変更ファイル
  - prompt echo を構造中心へ（指示領域と本文領域を強制分離、二段判定）
  - 後処理の idempotent 化（複数回適用で変化しない性質）
  - メトリクス基盤（上記指標）を CI に組込み
- リスク
  - 実装範囲拡大による短期バグ
- ロールバック条件
  - 主要指標が継続悪化（3指標以上）→ Phase2 へ戻す

---

## 6. 「修正」か「ゼロベース」かは可能か？（判断メモ）

### 共通の致命点（どちらでも先に潰す）
1) fail-closed が UI 依存 → generator 側で停止保証
2) prompt echo が must_cover 誤爆 → must_cover を参照から外す（まず止血）
3) UI が issue_count で即ブロック → 監視指標へ降格

### A) 既存（HumanResonance/Legacy）修正
- 可能。ただし「後処理を増やす」より「段数を減らして副作用を抑える」方向が安全。
- 現アップロード範囲では resonance 本体の中身が十分見えないため、改修はまず呼び出し側のガード/回数制限/ログ整備から。

### B) ゼロベース（zero_base_v1）移行
- 可能。むしろ dispatch と minimal 経路は既に存在。
- `semantic_dedupe.py` は fail-open 監査を返す構造で、embedder 初期化/埋め込み失敗に強い。
- 推奨: **zero_base_v1 を本流**に寄せ、Legacy を互換/非常用へ。

---

## 7. 監査の不確実点（明示）
1) `contextual_naturalness_report` / `quality_pipeline_check` の算出ロジック本体が未提示 → issue_count の実頻度・偽陽性率は断定不可。
2) generator の利用経路（UIのみか、API/バッチがあるか）が不明 → UI依存 fail-closed の実害は運用次第。
3) ログ保存先の権限制御/共有範囲が不明 → 漏えいリスクの大きさは環境依存。
4) LLM設定（モデル/温度/システムプロンプト）が未提示 → AIっぽさの寄与分解が未完。

---

## 付録: すぐ実装すべき「最小ステップ」3点
1) **must_cover を prompt echo 参照集合から外す**（UI/生成器の双方）
2) **hard_failed を generator 側で停止保証**（例外 or blocked返却）
3) **UI ブロック条件から issue_count を外す**（監視へ降格）

