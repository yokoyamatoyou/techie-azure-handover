# 記事品質安定化改修レポート

最終更新: 2026-03-06  
対象: `C:\tetie\notecode` の `zero_base_v2` 記事生成経路

## 1. このドキュメントの目的

- 今回の「人間らしく、一貫した記事」を安定生成するための改修内容を、実装・運用の両面で追跡できるようにする
- 失敗していた原因を固定化し、同じ種類の不具合を再発させないための参照資料にする
- 次回の調査時に「どこを見ればよいか」「何を戻してはいけないか」を明確にする

## 2. 発生していた問題

直近の破綻ログでは、本文が次の状態になっていた。

- 話者が固定されず、「私たち」と第三者説明が混在していた
- 読者への一般的な助言口調が混ざり、誰が誰に話しているか不明になっていた
- 無関係な話題が本文へ混入していた
- 数値上は `alignment_score=1.0` に見えても、実文では不自然だった
- 表示前ガードが止めず、そのまま UI に表示されていた

代表的な観測値:

- `speaker_consistency_score=0.35`
- `pronoun_consistency_score=0.0`
- `contract_alignment_score=1.0`
- `semantic_issue_count=5`
- `blocked_output_redacted=false`

## 3. 原因分類

### 3.1 確定

1. `zero_base_v2` 本流で後段の sanitize 系抑制が本文へ十分接続されていなかった  
   影響:
   - AI定型句
   - 曖昧な逃げ表現
   - 過度な助言口調
   が残りやすかった

2. 話者契約の低スコアが hard block 条件に入っていなかった  
   影響:
   - `speaker/pronoun` が崩れても表示される

3. `forbidden_topics` が `branding` 寄りで、会社紹介・経営者視点 drift を十分に抑止できなかった  
   影響:
   - 採用、福利厚生、チーム連携などの無関係話題が混入しやすかった

4. 品質レポートの一部集約が実態と乖離していた  
   影響:
   - 運用上「問題なし」に見えるケースがあった

### 3.2 有力

1. section prompt が話者契約を十分に拘束しておらず、一般論の説明文へ流れやすかった
2. section 生成後の軽量な契約再検査がなく、局所破綻が全体へ持ち上がっていた

### 3.3 保留

1. `must_cover` 保護つき legal guard の一部 fail-open 経路
2. preview と raw 表示差による見え方の揺れ

## 4. 実施した改修

## 4.1 前処理

対象: `note/article_generator.py`

- `speaker_profile`
- `audience_profile`
- `relationship_mode`
- `register_policy`
- `forbidden_topics`

を `zero_base_v2` 契約として再整理した。

追加したこと:

- 会社紹介、経営者視点、`corporate_culture` 系でも効く `forbidden_topics` 導出
- 許容一人称の導出
- 話者契約診断のための軽量解析関数

## 4.2 生成

対象: `note/article_generator.py`

section prompt に以下を明示注入した。

- 話者プロファイル
- 話者と読者の関係
- 許容一人称
- 許容/禁止文末
- 禁止話題
- 再生成時の補正指示

section 生成後には軽量 contract check を追加し、以下が出た場合は 1 回だけ再生成する。

- 第三者化
- 代名詞不整合
- 一般助言口調への逸脱
- 禁止話題の混入

## 4.3 後処理

対象: `note/article_generator.py`

- `Phase7Sanitize` 相当を zero-base minimal postprocess に接続
- `review_points` を zero_base_v2 でも採取
- 実際の pre/post テキストを `hard_soft_thresholds` 比較へ渡すよう修正

これにより、`rewrite_ratio=0.0` 固定化を避け、後段書き換えの監視を実態に寄せた。

## 4.4 出力ガード

対象: `note/note_writer_app.py`

新たに hard block 対象へ昇格:

- `speaker_consistency_score < 0.55`
- `pronoun_consistency_score < 0.50`
- `relationship_consistency_score < 0.50`
- `section_contract_issue_count > 0`

自然さ指標の扱い:

- `semantic_issue_count`
- `heading_alignment_mean`

は新本流では observe-only / soft warning 優先に変更した。自然さ不足だけで即 hard block しない。

追加した reason code:

- `SYS_SPEAKER_CONTRACT_MISMATCH`
- `SYS_FORBIDDEN_TOPIC_DRIFT`

既存の `SYS_CONTRACT_ALIGNMENT_MISMATCH` は継続利用する。

## 4.5 UI表示

対象: `note/note_writer_app.py`

- block 時は raw 本文を表示せず fail-closed 停止
- `reason_code`
- `error_class`
- `needs_input_items`

を UI と保存スナップショットへ残す運用を維持/強化した。

## 5. 変更ファイル一覧

- `notecode/note/article_generator.py`
- `notecode/note/note_writer_app.py`
- `notecode/note/tests/test_zero_base_phase04.py`
- `notecode/note/tests/test_zero_base_phase06.py`
- `notecode/note/tests/test_offline.py`
- `notecode/ALGORITHM.md`
- `WORKLOG.md`
- `notecode/docs/generation_failure_prevention_log.md`
- `notecode/docs/article_quality_stabilization_report_2026-03-06.md`

## 6. 検証結果

### 6.1 回帰テスト

実施コマンド:

```bash
py -m pytest note/tests/test_zero_base_phase04.py note/tests/test_zero_base_phase06.py note/tests/test_offline.py -q -k "phase04 or phase06 or output_guard or quality_report_payload or pipeline_check_contract_alignment"
```

結果:

- `29 passed`

追加で focused regression も実施:

- `10 passed`

### 6.2 既存失敗ログの再評価

対象:

- `notecode/logs/latest_generation_output.json`

現行ガードでの再評価結果:

- `blocked=true`
- `reason_code=SYS_SPEAKER_CONTRACT_MISMATCH`

主な block 理由:

- `contract_alignment_speaker_consistency<0.55`
- `contract_alignment_pronoun_consistency<0.50`
- `naturalness_heading_alignment<0.12`

## 7. 影響・副作用

### 期待できる改善

- 話者/読者/文体/論旨の一貫性が崩れにくくなる
- AI定型句と過度な助言口調が減る
- 無関係トピック混入が生成前後の両方で抑止される
- 不整合記事は表示前に止まり、`reason_code` が残る

### 想定副作用

- 以前なら表示されていた記事が block されることがある
- `forbidden_topics` の広がりにより、一部記事で話題の自由度が下がることがある
- sanitize により言い回しが軽く変わることがある

## 8. ロールバック条件

以下が増えた場合は段階的に切り戻しを検討する。

1. 正常記事の誤ブロックが増える  
   対応:
   - まず閾値のみを緩和する
   - reason code と監査項目は残す

2. `forbidden_topics` の false positive が増える  
   対応:
   - 記事タイプ別の除外語を縮小する

3. sanitize が文体を壊す  
   対応:
   - zero-base 専用 sanitize 呼び出しだけを切り戻す

4. section 再生成が不安定化する  
   対応:
   - section の retry 回数を 0 に戻し、診断だけ observe-only 化する

## 9. 次回の確認ポイント

- 実 API で `corporate_culture` の失敗ケースを再生成し、実文がどこまで自然化したかを見る
- block された場合に `reason_code` と本文の違和感が一致しているか確認する
- `section_contract_reports` と `contract_alignment_reason_codes` が保存されているか確認する
- `latest_generation_quality_report.json` の `flat_zone_count` が hard-soft 側と一致しているか確認する

## 10. まず試すテスト

現時点では、一度あなたが UI からテストして大丈夫です。むしろ次の順で 1 回確認するのがよいです。

1. まず、以前破綻した会社紹介/経営者視点の入力で再生成する
2. 正常に通った場合は、話者が一貫しているかを本文で確認する
3. わざと話者がぶれそうな入力も 1 件試し、表示前に block されるか確認する
4. block された場合は `reason_code` を記録する

推奨確認観点:

- 誰が誰に語っているか
- 読者への一般助言に逃げていないか
- 採用/福利厚生/社内制度などの無関係話題が混入していないか
- `reason_code` が本文の違和感と一致しているか

## 11. 関連資料

- `notecode/docs/generation_failure_prevention_log.md`
- `notecode/ALGORITHM.md`
- `WORKLOG.md`
