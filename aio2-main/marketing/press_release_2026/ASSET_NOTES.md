# コトミガキ プレスリリース素材メモ

## 作成物

- `press_release_kotomigaki_draft.md`
  - ブラッシュアップ済みプレスリリース本文。
  - タイトルは「何のサービスか」と価格が3秒で分かる形に整理。
  - リード文は診断内容と価格が10秒で分かる形に整理。
- `kotomigaki_radar_ui.png`
  - プレスリリース添付用の見本UI画像。
  - `build_press_release_assets.py` から再生成可能。
- `kotomigaki_key_visual.png`
  - プレスリリース・SNS・営業資料の冒頭に使う告知用イメージ画像。

## 文言ルール

- ChatGPT以外のAIサービス名は出さない。
- 法務チェックの訴求は入れない。
- 「脆弱性」は使わず、「サイトの弱点(セキュリティの穴)」に統一する。
- 断定的な被害表現や不安を煽る表現は避ける。

## キービジュアル生成プロンプト

Use case: ads-marketing  
Asset type: press release key visual, landscape 16:9  
Primary request: Create a polished, text-free visual image for a Japanese website health-check SaaS called Kotomigaki. Show a small business website being checked on a laptop/dashboard, with abstract radar chart shapes, check marks, and gentle security/AI discovery cues. No readable text, no logos, no brand names, no watermarks.  
Scene/backdrop: bright modern office desk, laptop screen with clean dashboard UI shapes, subtle website cards floating behind it.  
Subject: website health diagnosis for small and medium businesses, URL input simplicity, AI search readiness, site weak-point checks, usability improvement.  
Style/medium: refined editorial 3D illustration blended with realistic product-marketing lighting; premium Japanese B2B SaaS visual.  
Composition/framing: wide horizontal image with the laptop/dashboard centered-left and open negative space on the right for press release layout cropping.  
Lighting/mood: optimistic, clear, trustworthy, practical.  
Color palette: off-white background, teal, warm amber, graphite, small green accents.  
Constraints: no readable text, no fake UI words, no law/legal symbols, no scary hacker imagery, no padlock as the main subject, no watermark.

