"""Head asset registration helpers for note_writer_app."""
from __future__ import annotations

from typing import Any


APP_THEME_COLORS = {
    "primary": "#C7371B",
    "secondary": "#9A3412",
    "accent": "#E64424",
    "dark": "#241915",
    "positive": "#0F766E",
    "negative": "#B42318",
    "info": "#C7371B",
    "warning": "#C77A1B",
}


BASE_HEAD_HTML = """
<link rel="icon" type="image/png" href="/static/favicon_v2.png">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
/* SVGアイコン - シンプルな線ベースデザイン */
.icon {
  display: inline-block;
  width: 18px;
  height: 18px;
  vertical-align: middle;
  margin-right: 6px;
}
.icon-link {
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23C7371B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71'/%3E%3Cpath d='M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71'/%3E%3C/svg%3E") no-repeat center;
}
.icon-file {
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23C7371B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cline x1='16' y1='13' x2='8' y2='13'/%3E%3Cline x1='16' y1='17' x2='8' y2='17'/%3E%3C/svg%3E") no-repeat center;
}
.icon-article {
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23C7371B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7'/%3E%3Cpath d='M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z'/%3E%3C/svg%3E") no-repeat center;
}
.icon-person {
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23C7371B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E") no-repeat center;
}
.icon-edit {
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23C7371B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 19l7-7 3 3-7 7-3 0 0-3z'/%3E%3Cpath d='M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z'/%3E%3Cpath d='M2 2l7.586 7.586'/%3E%3Ccircle cx='11' cy='11' r='2'/%3E%3C/svg%3E") no-repeat center;
}
.icon-rocket {
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z'/%3E%3Cpath d='M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z'/%3E%3Cpath d='M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0'/%3E%3Cpath d='M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5'/%3E%3C/svg%3E") no-repeat center;
}
/* ニールセンの10原則に基づくUI設計 */
:root {
  --bg: #F7F1EA;
  --bg-deep: #F1E2D4;
  --surface: #FFFDF9;
  --surface-muted: #FBF7F2;
  --text: #2F241D;
  --muted: #6B5A4D;
  --text-muted: var(--muted);
  --accent: #D96B1F;
  --accent-2: #B95416;
  --accent-strong: #D96B1F;
  --accent-deep: #7A3A16;
  --accent-soft: rgba(217, 107, 31, 0.12);
  --border: rgba(191, 174, 159, 0.72);
  --border-strong: rgba(191, 174, 159, 0.90);
  --shadow: 0 10px 28px rgba(42, 31, 26, 0.08);
  --shadow-hover: 0 14px 36px rgba(42, 31, 26, 0.12);
  --nav-bg: #2F241D;
  --nav-text: #E7DDD4;
  --nav-text-hover: #FFF9F4;
  --nav-text-active: #F5BA71;
  --nav-height: 52px;
  --logo-height: 52px;
  /* 黄金比スペーシングスケール */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 13px;
  --space-lg: 21px;
  --space-xl: 34px;
  --space-2xl: 55px;
  /* 黄金比タイポグラフィスケール */
  --text-xs: 14px;
  --text-sm: 16px;
  --text-base: 17px;
  --text-lg: 20px;
  --text-xl: 26px;
  --text-2xl: 34px;
}
body {
  font-family: 'Noto Sans JP', sans-serif;
  background: linear-gradient(160deg, var(--bg) 0%, var(--bg-deep) 50%, var(--bg) 100%);
  color: var(--text);
  margin: 0;
  padding: 0;
  min-height: 100vh;
}

/* #1 幅を大幅に拡張 - 画面の95%を使用 */
.app-shell {
  width: min(94%, 1180px);
  max-width: none;
  margin: calc(var(--nav-height) + 8px) auto 36px;
  padding: 0;
  display: grid !important;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: auto auto auto auto auto;
  gap: 18px;
  align-items: start;
}
.app-shell > * {
  min-width: 0;
}
.brand-header,
.step-track {
  grid-column: 1 / -1;
}
.brand-header {
  grid-row: 1;
}
.step-track {
  grid-row: 2;
}
.input-stage-card {
  max-width: none;
  width: 100%;
  margin: 0;
}
.step-card-1,
.step-card-2,
.output-stage-shell {
  grid-column: 1;
}
.step-card-1 {
  grid-row: 3;
}
.step-card-2 {
  grid-row: 4;
}
.output-stage-shell {
  grid-row: 5;
}
.narrow-support-card {
  background: linear-gradient(180deg, #FFFDFC 0%, #FFF7F3 100%);
  border: 1px solid rgba(230, 68, 36, 0.18);
  border-radius: 14px;
}
.required-input-card {
  background: linear-gradient(180deg, #FFF9F6 0%, #FFFDFB 100%);
  border: 1px solid rgba(199, 55, 27, 0.18);
  border-radius: 16px;
}
.source-mode-choice-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.source-mode-choice-card {
  border: 1px solid rgba(72, 58, 50, 0.14);
  border-radius: 16px;
  background: linear-gradient(180deg, #FFFDFC 0%, #FFF8F3 100%);
  box-shadow: 0 6px 16px rgba(42, 31, 26, 0.04);
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease, background 0.18s ease;
}
.source-mode-choice-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(42, 31, 26, 0.08);
}
.source-mode-choice-card-active {
  border-color: rgba(199, 55, 27, 0.42);
  background: linear-gradient(180deg, #FFF3EA 0%, #FFF9F4 100%);
  box-shadow: 0 14px 28px rgba(199, 55, 27, 0.14);
}
@media (max-width: 720px) {
  .source-mode-choice-row {
    grid-template-columns: 1fr;
  }
}

.brand-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-md);
  margin-bottom: 6px;
}
.brand-logo-inline {
  height: var(--logo-height);
  width: auto;
  max-width: 360px;
  object-fit: contain;
  min-height: var(--logo-height);
  display: block;
}
.brand-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  padding-top: 2px;
}
.brand-pill {
  background: #FFF1EC;
  color: #9A3412;
  border: 1px solid rgba(231, 67, 35, 0.3);
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  padding: 4px 10px;
  letter-spacing: 0.04em;
}

.hero-title {
  font-family: 'Sora', 'Noto Sans JP', sans-serif;
  font-size: 36px;
  font-weight: 700;
  margin: 0;
  color: var(--accent-2);
  line-height: 1.1;
}
.hero-role {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-deep);
}
.hero-sub {
  color: var(--text-muted);
  font-size: 16px;
  margin: 0;
  max-width: 720px;
}
.hero-next {
  color: var(--accent-deep);
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}
.suite-link-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.suite-link-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 16px;
  border: 1px solid rgba(191, 174, 159, 0.72);
  background: #FFFDF9;
  color: var(--text);
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
}
.suite-link-btn:hover {
  border-color: rgba(217, 107, 31, 0.42);
}

/* #2 カードの境界を明確に - 視認性向上 */
.card {
  background: var(--surface);
  border-radius: 18px;
  border: 2px solid var(--border-strong);
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease;
}
.card:hover {
  box-shadow: var(--shadow-hover);
}
/* 出力カード: 入力カードと明確に区別 */
.output-card {
  background: linear-gradient(160deg, #FFFCFA 0%, #FFF8F4 100%);
  border-radius: 18px;
  border: 1px solid var(--border-strong);
  box-shadow: 0 10px 28px rgba(42, 31, 26, 0.08);
  transition: box-shadow 0.2s ease;
}
.output-card:hover {
  box-shadow: 0 14px 36px rgba(42, 31, 26, 0.12);
}
.output-stage-shell {
  width: 100%;
  margin-top: 0;
  padding: 22px;
  border-radius: 24px;
  border: 1px solid rgba(72, 58, 50, 0.14);
  background: linear-gradient(180deg, #FFFDFC 0%, #FFF7F1 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}
.output-stage-heading {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #7A5544;
  text-transform: uppercase;
}
.output-stage-note {
  font-size: 15px;
  line-height: 1.6;
  color: #6E564C;
}
.output-static-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(72, 58, 50, 0.16);
  background: #F7F0EC;
  color: #70574C;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.generated-preview-shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.generated-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.generated-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(177, 90, 43, 0.16);
  color: #8A4426;
  font-size: 13px;
  font-weight: 700;
}
.generated-stats {
  font-size: 12px;
  color: #6F574C;
}
.generated-preview-card {
  padding: 18px 20px;
  border-radius: 18px;
  border: 1px solid rgba(177, 90, 43, 0.18);
  background: linear-gradient(180deg, #FFFFFF 0%, #FFF8F2 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}
.generated-output-expansion,
.secondary-support-expansion,
.collapsed-support {
  border: 1px solid rgba(72, 58, 50, 0.10);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.76);
}
.generated-output-expansion .q-expansion-item__container,
.secondary-support-expansion .q-expansion-item__container,
.collapsed-support .q-expansion-item__container {
  border-radius: 16px;
}
.generated-output-expansion .q-item,
.secondary-support-expansion .q-item,
.collapsed-support .q-item {
  min-height: 56px;
}
.generated-output-expansion .q-item__label,
.secondary-support-expansion .q-item__label,
.collapsed-support .q-item__label {
  font-weight: 700;
  color: #3D2E28;
}
.secondary-tools-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.generated-readonly .q-field__control {
  background: linear-gradient(180deg, #FFFFFF 0%, #FFF7F2 100%) !important;
  border-color: rgba(177, 90, 43, 0.24) !important;
}
.generated-readonly .q-field__label {
  color: #8A4426 !important;
  font-size: 14px !important;
}
.section-muted-note {
  font-size: 14px;
  line-height: 1.5;
  color: #5D4A41;
}
.quality-summary-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid rgba(185, 84, 22, 0.28);
  background: linear-gradient(180deg, #FFF8F1 0%, #FFFDF9 100%);
}
.quality-summary-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.quality-summary-badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #FFE5D1;
  color: #8A3F18;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.quality-summary-title {
  font-size: 16px;
  line-height: 1.45;
  font-weight: 700;
  color: #4B3428;
}
.quality-summary-note {
  font-size: 14px;
  line-height: 1.6;
  color: #5D4A41;
}
.quality-summary-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.quality-summary-row-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.quality-summary-row-title {
  font-size: 14px;
  line-height: 1.45;
  font-weight: 700;
  color: #4B3428;
}
.quality-summary-row-detail {
  font-size: 14px;
  line-height: 1.55;
  color: #5D4A41;
}
.quality-summary-row-codes {
  font-size: 12px;
  line-height: 1.5;
  color: #8A5B45;
}
.quality-hint-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #FFF4E8;
  border: 1px solid rgba(185, 84, 22, 0.18);
}
.quality-hint-title {
  font-size: 14px;
  line-height: 1.45;
  font-weight: 700;
  color: #7A3A16;
}
.quality-hint-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: #F9DABF;
  color: #7A3A16;
  font-size: 12px;
  font-weight: 700;
}
.quality-hint-text {
  font-size: 14px;
  line-height: 1.55;
  color: #5D4A41;
}

/* #3 セクションタイトルの強調 */
.section-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text);
  border-bottom: 2px solid rgba(177, 90, 43, 0.55);
  padding-bottom: var(--space-sm);
  margin-bottom: var(--space-lg);
  display: inline-block;
}

/* #4 ボタンの一貫性と認識しやすさ */
.primary-btn {
  background: linear-gradient(135deg, var(--accent-strong), var(--accent-deep));
  color: white;
  border-radius: 10px;
  font-weight: 600;
  font-size: var(--text-sm);
  padding: 12px 24px;
  border: none;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 8px 18px rgba(42, 31, 26, 0.12);
}
.q-btn.primary-btn {
  min-height: 44px !important;
  border-radius: 10px !important;
  padding: 0 18px !important;
  box-shadow: 0 8px 18px rgba(42, 31, 26, 0.12) !important;
}
.q-btn.primary-btn .q-focus-helper {
  opacity: 0 !important;
  background: transparent !important;
}
.q-btn.bg-primary:not(.q-btn--disabled),
.q-btn[class*="bg-primary"]:not(.q-btn--disabled) {
  background: linear-gradient(135deg, var(--accent-strong), var(--accent-deep)) !important;
  color: #FFFFFF !important;
}
.q-btn.primary-btn.bg-primary,
.q-btn.primary-btn[class*="bg-primary"] {
  background: linear-gradient(135deg, var(--accent-strong), var(--accent-deep)) !important;
  color: #FFFFFF !important;
}
.q-btn.primary-btn:not(.q-btn--outline) {
  background: linear-gradient(135deg, var(--accent-strong), var(--accent-deep)) !important;
  color: #FFFFFF !important;
  border: none !important;
}
.q-btn.primary-btn:not(.q-btn--outline) .q-btn__content {
  color: #FFFFFF !important;
  font-weight: 700 !important;
}
.q-btn.primary-btn.q-btn--outline {
  background: #FFF7F3 !important;
  color: #9A3412 !important;
  border: 1px solid rgba(230, 68, 36, 0.45) !important;
}
.q-btn.primary-btn.q-btn--outline .q-btn__content {
  color: #9A3412 !important;
  font-weight: 700 !important;
}
.q-btn.primary-btn.q-btn--disabled,
.q-btn.primary-btn[disabled],
.q-btn.primary-btn:disabled {
  opacity: 1 !important;
  background: linear-gradient(135deg, #B86B4D, #A95B3D) !important;
  color: #FFF8F4 !important;
  border: 1px solid rgba(122, 72, 51, 0.45) !important;
  box-shadow: none !important;
}
.q-btn.primary-btn.q-btn--disabled .q-btn__content,
.q-btn.primary-btn[disabled] .q-btn__content,
.q-btn.primary-btn:disabled .q-btn__content {
  color: #FFF8F4 !important;
  font-weight: 700 !important;
  opacity: 1 !important;
  text-shadow: 0 1px 0 rgba(79, 40, 24, 0.16);
}
.bg-primary {
  background: var(--accent-strong) !important;
}
.text-primary {
  color: var(--accent-strong) !important;
}
.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(42, 31, 26, 0.16);
}

/* #5 入力フィールドの視認性向上 - ニールセン#2,#6, Fittsの法則 */
/* 入力欄が背景と明確に区別されるよう白背景＋強調枠線 */
.q-field--outlined .q-field__control {
  background: #FFFFFF !important;
  border: 2px solid #C9A69C !important;
  border-radius: 10px !important;
  transition: all 0.2s ease !important;
  min-height: 48px !important;  /* Fittsの法則: タッチターゲット拡大 */
}
.q-field--outlined .q-field__control:hover {
  border-color: var(--accent) !important;
  box-shadow: 0 2px 8px rgba(231, 67, 35, 0.18) !important;
}
.q-field--outlined.q-field--focused .q-field__control {
  border-color: var(--accent-2) !important;
  box-shadow: 0 0 0 3px rgba(231, 67, 35, 0.24) !important;
}
/* ラベルの強調 - ニールセン#6: 認識による負荷軽減 */
.q-field__label {
  font-weight: 600 !important;
  color: #4D3E37 !important;
  font-size: 16px !important;
}
.q-field__native,
.q-field__input,
.q-select__dropdown-icon {
  font-size: 16px !important;
  color: #2B211E !important;
}
/* プレースホルダーの視認性 */
.q-field__native::placeholder {
  color: #8A776D !important;
  font-style: italic !important;
}
/* テキストエリアの高さ確保 */
.q-textarea .q-field__control {
  min-height: 100px !important;
}
/* 入力フィールドのフォールバック（旧形式対応） */
.nicegui-input, .nicegui-textarea, .nicegui-select {
  border: 2px solid #C9A69C !important;
  border-radius: 10px !important;
  background: #FFFFFF !important;
  transition: border-color 0.2s ease !important;
}
.nicegui-input:focus, .nicegui-textarea:focus {
  border-color: var(--accent) !important;
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(231, 67, 35, 0.24) !important;
}

/* #6 結果表示エリアの明確な境界 */
.article-preview.article-preview-placeholder {
  min-height: 120px;
  padding: 14px 16px;
  background: linear-gradient(to bottom, #FFFDFC, #FFF9F6);
  border-style: dashed;
}
.article-preview-placeholder p {
  color: #6B7280;
  font-style: italic;
  font-family: 'Noto Sans JP', sans-serif;
  text-align: center;
  padding: 14px 0;
  font-size: 14px;
}
.article-preview {
  font-family: 'Shippori Mincho', 'Noto Serif JP', serif;
  font-size: var(--text-base);
  line-height: 1.9;
  background: linear-gradient(to bottom, #FFFDFC, #FFF3EE);
  border-radius: 12px;
  padding: 24px;
  border: 2px solid var(--border-strong);
  min-height: 200px;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

/* #7 バッジスタイル */
.badge {
  background: linear-gradient(135deg, rgba(231,67,35,0.16), rgba(199,55,27,0.1));
  color: #9A3412;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: var(--text-xs);
  font-weight: 600;
  border: 1px solid rgba(231,67,35,0.3);
}

/* #8 セパレーターの視認性 */
.nicegui-separator {
  border-top: 2px solid var(--border-strong) !important;
  margin: var(--space-lg) 0 !important;
}

/* 出力サブセクション共通見出し */
.output-section-title {
  font-weight: 600;
  font-size: var(--text-base);
}

.q-expansion-item {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  overflow: hidden;
}
.q-expansion-item__header {
  background: var(--surface-muted);
  font-weight: 600;
}
.q-expansion-item--expanded .q-expansion-item__header {
  background: var(--accent-soft);
}
.q-expansion-item__content {
  background: var(--surface);
}

/* #9 ソース一覧の明確な境界 */
.source-item {
  background: #FFF6F2;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  margin: 4px 0;
}
.text-xs {
  font-size: 14px !important;
  line-height: 1.6 !important;
}
.text-sm {
  font-size: 16px !important;
  line-height: 1.65 !important;
}
.text-base {
  font-size: 17px !important;
  line-height: 1.72 !important;
}
.text-lg {
  line-height: 1.45 !important;
}
.text-gray-400 {
  color: #A58F83 !important;
}
.text-gray-600 {
  color: #6F625B !important;
}
.text-gray-700 {
  color: #4D3E37 !important;
}
.text-blue-500,
.text-blue-600 {
  color: #6A5A52 !important;
}
.bg-gray-50 {
  background: #FBF4EF !important;
}
.bg-gray-100 {
  background: #F4E8E1 !important;
}
.bg-orange-50 {
  background: #F8F1EB !important;
}
.bg-orange-100 {
  background: #F3E7DE !important;
}
.bg-orange-500 {
  background: var(--accent-strong) !important;
}
.bg-amber-100 {
  background: #F2E8E0 !important;
}
.bg-green-100 {
  background: #EEF3ED !important;
}
.text-orange-400 {
  color: #9C8174 !important;
}
.text-orange-600,
.text-orange-700,
.text-orange-800 {
  color: #7A5544 !important;
}
.text-amber-700,
.text-amber-800 {
  color: #7A5544 !important;
}
.text-green-700 {
  color: #4E6654 !important;
}
.kotomake-uploader {
  height: 48px !important;
  max-height: 48px !important;
  min-height: 48px !important;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(199, 55, 27, 0.18);
  background: #FFFDFC;
  box-shadow: none !important;
}
.kotomake-uploader.q-uploader,
.kotomake-uploader .q-uploader {
  height: 48px !important;
  max-height: 48px !important;
  min-height: 48px !important;
}
.kotomake-uploader .q-uploader__header {
  background: linear-gradient(135deg, var(--accent-strong), var(--accent-deep)) !important;
  color: #FFFFFF !important;
  height: 48px !important;
  max-height: 48px !important;
  min-height: 48px !important;
  padding: 6px 12px !important;
}
.kotomake-uploader .q-uploader__header-content {
  height: 36px !important;
  min-height: 0 !important;
  padding: 0 !important;
  align-items: center !important;
}
.kotomake-uploader .q-uploader__title {
  font-size: 13px !important;
  font-weight: 700 !important;
  line-height: 1.25 !important;
}
.kotomake-uploader .q-uploader__subtitle {
  display: none !important;
}
.kotomake-uploader .q-uploader__list {
  display: none !important;
}
.kotomake-uploader .q-uploader__file-header {
  color: #4D3E37 !important;
}
.kotomake-uploader .q-btn,
.kotomake-uploader .q-icon {
  color: #FFFFFF !important;
}
.kotomake-uploader .q-btn {
  min-width: 34px !important;
  min-height: 34px !important;
  padding: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.kotomake-uploader .q-uploader__dnd {
  color: #9A3412 !important;
  font-size: 13px !important;
}
.kotomake-uploader .q-uploader__content {
  display: none !important;
  height: 0 !important;
  max-height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
}
@media (prefers-reduced-motion: reduce) {
  .card,
  .output-card,
  .primary-btn,
  .q-btn.primary-btn {
    transition: none !important;
  }
}
.warm-canvas {
  background: #FBF4EF !important;
}

/* #10 フィードバックとアニメーション */
.fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ---- TECHIE nav ---- */
.hub-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--nav-height);
  background: var(--nav-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 14px;
  padding: 0 24px;
  z-index: 9999;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  pointer-events: auto;
}
.hub-nav * {
  pointer-events: auto;
}
.hub-nav a {
  color: var(--nav-text);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  min-height: 44px;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  transition: color 0.2s;
  border-radius: 999px;
}
.hub-nav a:hover {
  color: var(--nav-text-hover);
}
.hub-nav a.hub-nav-active {
  color: var(--nav-text-active);
  background: rgba(255, 249, 244, 0.08);
}
.hub-nav a.hub-nav-home {
  color: #ffffff;
  background: linear-gradient(135deg, var(--accent-strong), var(--accent-deep));
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(199, 55, 27, 0.3);
}
.hub-nav a.hub-nav-home:hover {
  color: #ffffff;
  box-shadow: 0 6px 16px rgba(199, 55, 27, 0.38);
}
.hub-nav .hub-nav-sep {
  color: #A1887C;
  font-size: 12px;
  user-select: none;
}
.q-field__native span.ellipsis,
.q-field__label.ellipsis {
  line-height: 1.4 !important;
}
.q-field__native span.ellipsis {
  white-space: normal !important;
}

/* レスポンシブ: 小さい画面での調整 */
@media (max-width: 1200px) {
  .app-shell {
    width: 98%;
    padding: 0 12px;
    grid-template-columns: 1fr;
  }
  .step-card-1,
  .step-card-2,
  .output-stage-shell {
    grid-column: 1;
    grid-row: auto;
  }
  .input-stage-card {
    max-width: 100%;
  }
}
@media (max-width: 768px) {
  .app-shell { width: 100%; padding: 0 var(--space-sm); gap: 18px; }
  .hero-title { font-size: 24px; }
  .hero-role { font-size: 12px; }
  .brand-header { align-items: center; }
  .brand-copy { gap: 0; }
  .hero-sub { font-size: 14px; }
  .hero-next { font-size: 13px; }
  .hub-nav { gap: 10px; padding: 0 12px; }
  .hub-nav a { font-size: 12px; min-height: 44px; padding: 0 10px; }
  .generated-preview-card { padding: 16px 14px; }
}

/* ステップ進捗スティッキーバー */
.step-track {
  position: sticky;
  top: var(--nav-height);
  z-index: 500;
  background: rgba(255, 248, 245, 0.97);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  padding: 6px 0;
  display: flex !important;
  align-items: center;
  justify-content: center;
  gap: 10px;
}
.step-track-item {
  font-size: 14px;
  font-weight: 700;
  padding: 5px 16px;
  border-radius: 99px;
  transition: background 0.3s ease, color 0.3s ease;
  white-space: nowrap;
}
.step-track-active {
  background: var(--accent-strong);
  color: white !important;
  box-shadow: 0 3px 10px rgba(199,55,27,0.28);
}
.step-track-done {
  background: #D1FAE5;
  color: #065F46 !important;
}
.step-track-pending {
  background: #F4E8E1;
  color: #9F867A !important;
}
.journey-stage-card {
  border: 1px solid #F1D7CC !important;
  background: #FFFDFC !important;
}
.journey-stage-card-active {
  border-color: rgba(199, 55, 27, 0.24) !important;
  box-shadow: 0 6px 16px rgba(199, 55, 27, 0.08) !important;
}
</style>
"""


STICKY_STEP_HEAD_HTML = """
<script>
(function(){
  var ALL = ['step-track-active','step-track-done','step-track-pending'];
  var STEPS = [
    {sel:'.sticky-s1', lbl:'\\u2460 \\u5165\\u529b',             done:'\\u2713 \\u5165\\u529b'},
    {sel:'.sticky-s2', lbl:'\\u2461 \\u751f\\u6210\\u6e96\\u5099', done:'\\u2713 \\u751f\\u6210\\u6e96\\u5099'},
    {sel:'.sticky-s3', lbl:'\\u2462 \\u751f\\u6210\\u7d50\\u679c', done:'\\u2713 \\u751f\\u6210\\u7d50\\u679c'},
  ];
  var scrollStep = 0;
  var doneCount  = 0;
  /* nav(40px) + step-track bar(約36px) = 76px。
     カード底辺がこの高さを下回ったら「画面外」と判定する。 */
  var STICKY_H = 76;

  function refreshBar() {
    STEPS.forEach(function(s, i) {
      var el = document.querySelector(s.sel);
      if (!el) return;
      /* step-track-done は Python(タイマー)が管理するため JS は触らない */
      if (el.classList.contains('step-track-done')) return;
      el.classList.remove('step-track-active', 'step-track-pending');
      el.classList.add(i === scrollStep ? 'step-track-active' : 'step-track-pending');
      el.textContent = s.lbl;
    });
  }

  var cards = [];

  function calcScrollStep() {
    /* カードの底辺が sticky バー以下に入ったら次のステップへ。
       「STEP1 が画面から消えてから STEP2 に切り替わる」挙動。 */
    var newActive = 0;
    for (var i = 0; i < cards.length - 1; i++) {
      if (!cards[i]) continue;
      var bottom = cards[i].getBoundingClientRect().bottom;
      if (bottom <= STICKY_H + 8) {
        newActive = i + 1;
      }
    }
    if (newActive !== scrollStep) {
      scrollStep = newActive;
      refreshBar();
    }
  }

  function initScrollSpy() {
    var cardSels = ['.step-card-1', '.step-card-2', '.step-card-3'];
    cards = cardSels.map(function(s) { return document.querySelector(s); });
    if (cards.some(function(c) { return !c; })) {
      setTimeout(initScrollSpy, 250);
      return;
    }
    window.addEventListener('scroll', calcScrollStep, { passive: true });
    calcScrollStep();
    refreshBar();
  }

  setTimeout(initScrollSpy, 450);
})();
</script>
"""


def register_note_writer_app_colors(app: Any) -> None:
    app.colors(**APP_THEME_COLORS)


def register_note_writer_app_base_head_html(ui: Any) -> None:
    ui.add_head_html(BASE_HEAD_HTML, shared=True)


def register_note_writer_app_sticky_step_head_html(ui: Any) -> None:
    ui.add_head_html(STICKY_STEP_HEAD_HTML, shared=True)
