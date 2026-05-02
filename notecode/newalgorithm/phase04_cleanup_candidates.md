# Phase04 Cleanup Candidates（ログ根拠つき）

## 前提
- Phase04では UI 削除は実施しない（非表示開始のみ）。
- 判定根拠は `notecode/logs/app.log*` の実測 + Phase04で追加した `ui_usage` 計測タグを併用する。

## 必須3要素（維持）
- 記事種類セレクタ: 維持（7固定）
- 生成ボタン + 結果表示: 維持
- 画像生成（TOP/本文）: 維持

### ログ根拠（直近ローテーション）
- `Generation started|Generation completed` のヒット:
  - `app.log: 38`
  - `app.log.1: 21`
  - `app.log.2: 25`
  - `app.log.3: 30`
  - `app.log.4: 42`
  - `app.log.5: 28`
  - 合計: `184`

## 非表示開始（削除候補）
- `custom_genre`（カスタムジャンル管理）
  - 理由: Phase01で記事タイプ7固定を確定済み。UI選択肢過多を抑制（Hick）。
  - 現在: Phase04で UI 非表示化（コードは保持）。
  - 計測タグ: `ui_usage {"feature":"custom_genre", ...}`
- `generated_image_edit`（生成後の詳細画像編集）
  - 理由: 必須要素ではない追加編集導線。初期リリースで複雑性を下げる。
  - 現在: UI残置（削除なし）。
  - 計測タグ: `ui_usage {"feature":"generated_image_edit", ...}`
- `source_privacy_blur`（素材画像の個人情報ぼかし）
  - 理由: 必須3要素の外。B2B運用で必要なケースはあるため即削除はしない。
  - 現在: UI残置（削除なし）。
  - 計測タグ: `ui_usage {"feature":"source_privacy_blur", ...}`

## 例外画面（維持）
- `manual_legal_check`（簡易リーガルチェック）
  - 理由: 生成後リーガルの「任意再実行」導線として必要。
  - 計測タグ: `ui_usage {"feature":"manual_legal_check", ...}`

## 今回の観測値（Phase04開始時点）
- `ui_usage` ヒット: 0（Phase04で計測タグを追加した直後のため）
- 運用判定ルール:
  - 4週間観測で `未使用 + 非稼働 + 代替あり` を満たした項目のみ削除候補へ昇格
