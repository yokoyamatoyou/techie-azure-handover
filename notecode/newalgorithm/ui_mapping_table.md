# UI項目対応表（Phase01 確定版）

## 前提
- Phase01は「現行UI維持のまま新アルゴリズム接続」が目的。
- ここでの `非表示` は **Phase04以降の候補区分**。Phase01時点では削除・非表示を実施しない。
- 必須3要素（`記事種類セレクタ` / `生成ボタン+結果表示` / `画像生成（TOP/本文）`）は固定で残す。

| 現行UI項目 | 新input_contract項目 | 扱い（残す/非表示/削除） | 理由 | 移行メモ |
|---|---|---|---|---|
| ソースURL入力 + 追加 | `source` / `source_inputs` | 残す | 生成入力の必須要素 | URL取得失敗時のfail-closed挙動を維持 |
| ファイルアップロード（PDF/DOCX/txt/md/png/jpg/jpeg/webp） | `source` / `source_inputs` | 残す | 生成入力の必須要素 | URLと同じsource配列へ正規化 |
| 記事タイプセレクタ | `article_type` | 残す | 必須3要素の1つ、主キー | 7固定キーへ正規化（UI入力追加なし） |
| 記事の目的 | `content_goal` | 残す | 生成意図の補助入力 | prompt補助文生成を維持 |
| 指示内容（テーマ・対象読者・トーン） | `topic` / `user_instruction` | 残す | 生成要求の核 | 空時はsource側から補完、両方空はreject |
| 第二ペルソナ | `perspective` / `article_viewpoint` | 残す | 語り口の補助制御 | 既存のauto判定フォールバック維持 |
| 話者（選択） | `speaker_profile` / `writer_role` | 残す | 話者契約の主入力 | テーマ文誤入力は既存警告で無効化 |
| 話者（自由入力）+ トグル | `speaker_profile` / `writer_role` | 残す | 上級者向け補助 | 80文字上限の安全制約を維持 |
| 記事の流れ（型） | `structure` | 残す | 構成制御の主要パラメータ | auto時は既存プリセット補正を維持 |
| 本文の重心 | `writing_focus` | 残す | 構成/文体制御に直結 | category fail-safe降格の既存挙動を維持 |
| 語り口トーン | `tone_profile` | 残す | 文体選択の主要入力 | auto連動を維持 |
| 体験談挿入許可 | `allow_experience` | 残す | 体験談混入の安全制御 | 解説系でのfail-safe降格を維持 |
| 記事の長さ | `length_mode` | 残す | 出力長制御に直結 | adaptive既定を維持 |
| 生成前インタビュー回答 | `interview_answers` | 残す | must_cover生成の根拠 | target/perspective/message優先を維持 |
| 曖昧語の語義確認ダイアログ | `ambiguity_resolutions` | 残す | 誤解・誤生成リスク低減 | 契約前適用を維持 |
| 生成実行（ボタン）+ 結果表示 | `generation_request` / `generation_output` | 残す | 必須3要素の1つ | fail-closed理由表示を維持 |
| 画像プロンプト入力（生成後自動投入含む） | `image_generation.prompt` | 残す | 必須3要素（画像生成） | TOP/本文向けの既存運用を維持 |
| 画像生成実行（ボタン） | `image_generation.enabled` / `image_generation.mode` | 残す | 必須3要素の1つ | 既存画像I/F互換を維持 |
| 生成画像編集（テキスト重ね/フィルタ/グラデ/ぼかし） | `image_editing.*` | 非表示 | 新アルゴリズム本流外（編集補助） | 1リリース計測後、未使用+代替ありなら削除候補 |
| ソース画像のプライバシーぼかし | `source_privacy_blur.*` | 非表示 | 生成本流外（入力前処理） | 1リリース計測後に判定 |
| カスタムジャンル管理（追加/編集/削除） | `custom_genre.*` | 非表示 | Phase01の固定7タイプ方針と衝突 | 代替（固定7タイプ）移行後に削除可否判定 |
| 簡易リーガルチェック（任意再実行） | `post_legal_check.manual` | 残す | 固定仕様「自動+任意再実行」に必要 | 自動実行は生成パイプライン側、UIは任意再実行導線を維持 |

## 棚卸し結果
- 総項目: 22
- `残す`: 19
- `非表示`: 3
- `削除`: 0
- `未分類`: 0

## 判定ルール（確定）
- 本流（生成品質・安全性・運用）に直結: `残す`
- 固定仕様と衝突する補助機能: `非表示` 候補として計測し、安定化後に判定
- 削除実施条件: `未使用 + 非稼働 + 代替あり` のログ根拠が揃った時のみ
