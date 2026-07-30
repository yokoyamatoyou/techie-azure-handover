from __future__ import annotations

import os

from nicegui import ui

THEME_TEXT_MAIN = "#3E2C22"
THEME_TEXT_SOFT = "#6B5648"
THEME_TEXT_HELPER = "#8C7668"
THEME_GRID_SOFT = "rgba(107, 86, 72, 0.10)"
THEME_GRID_STRONG = "rgba(107, 86, 72, 0.16)"
THEME_BRAND = "#D96B1F"
THEME_BRAND_DEEP = "#B95416"
THEME_SERIES_BLUE = "#A76637"
THEME_SERIES_TEAL = "#6F8B67"
THEME_SERIES_AMBER = "#C29246"
THEME_SERIES_CORAL = "#BE6B4A"
THEME_SERIES_SLATE = "#8B776A"


def _runtime_url(env_name: str, fallback: str) -> str:
    value = str(os.environ.get(env_name, "")).strip()
    return value or fallback


def add_global_style() -> None:
    ui.add_head_html(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
          <style>
          :root {
            --bg: #f7f1ea;
            --bg-deep: #f1e2d4;
            --surface: #fffdf9;
            --surface-muted: #fbf7f2;
            --surface-raised: rgba(255, 253, 249, 0.98);
            --text: #2f241d;
            --text-soft: #6b5a4d;
            --muted: #6b5a4d;
            --brand: #d96b1f;
            --brand-deep: #b95416;
            --brand-strong: #d96b1f;
            --brand-soft: rgba(217, 107, 31, 0.12);
            --self: #6f8b67;
            --self-soft: rgba(111, 139, 103, 0.12);
            --competitive: #c29246;
            --competitive-soft: rgba(194, 146, 70, 0.16);
            --external: #be6b4a;
            --external-soft: rgba(190, 107, 74, 0.13);
            --border: rgba(191, 174, 159, 0.72);
            --border-strong: rgba(191, 174, 159, 0.90);
            --shadow: 0 10px 28px rgba(42, 31, 26, 0.08);
            --shadow-hover: 0 14px 36px rgba(42, 31, 26, 0.12);
            --nav-bg: #2f241d;
            --nav-text: #e7ddd4;
            --nav-text-hover: #fff9f4;
            --nav-text-active: #f5ba71;
            --bg-soft: rgba(250, 244, 237, 0.92);
            --panel: rgba(255, 251, 246, 0.94);
            --panel-strong: var(--surface-raised);
            --panel-muted: rgba(250, 244, 237, 0.90);
            --line: var(--border);
            --line-strong: var(--border-strong);
            --accent: var(--brand);
            --accent-2: var(--brand-deep);
            --accent-deep: var(--brand-deep);
            --accent-soft: var(--brand-soft);
            --brown: var(--nav-bg);
            --brown-soft: #6b5648;
            --neutral-soft: rgba(122, 98, 83, 0.10);
            --green-mist: rgba(245, 227, 205, 0.44);
            --shadow-soft: 0 18px 40px rgba(84, 60, 46, 0.08);
            --q-primary: #d96b1f;
            --q-secondary: #6b5a4d;
            --q-accent: #b95416;
            --q-info: #a76637;
          }
          html, body {
            font-size: 16px;
            max-width: 100%;
            overflow-x: hidden;
          }
          body {
            font-family: "Noto Sans JP", sans-serif;
            background:
              radial-gradient(circle at 80% 18%, rgba(244, 222, 198, 0.24), transparent 18%),
              radial-gradient(circle at 18% 12%, rgba(255, 255, 255, 0.80), transparent 24%),
              linear-gradient(160deg, var(--bg) 0%, var(--bg-deep) 50%, var(--bg) 100%);
            color: var(--text);
          }
          #app,
          .q-layout,
          .q-page-container,
          .q-page {
            max-width: 100%;
            overflow-x: hidden;
          }
          .brand-font,
          .metric-font,
          .section-font,
          .step-font {
            font-family: "Sora", sans-serif;
          }
          .top-shell {
            background: var(--nav-bg);
            border-bottom: 1px solid rgba(255, 255, 255, 0.10);
            box-shadow: 0 10px 28px rgba(54, 36, 25, 0.18);
          }
          .top-logo-link {
            display: inline-flex;
            align-items: center;
            justify-content: flex-start;
            gap: 12px;
            padding: 4px 0;
          }
          .top-logo-lockup {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 42px;
            padding: 7px 12px;
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(255, 251, 246, 0.98) 0%, rgba(247, 239, 230, 0.96) 100%);
            border: 1px solid rgba(255, 248, 241, 0.28);
            box-shadow: 0 8px 18px rgba(25, 16, 11, 0.16);
          }
          .top-logo-wordmark-image {
            width: 176px;
            height: 24px;
            object-fit: contain;
            object-position: left center;
            display: block;
          }
          .hero-logo-mark {
            overflow: hidden;
            border-radius: 0;
          }
          .hero-logo-mark .q-img__image {
            object-fit: contain !important;
            object-position: center center !important;
          }
          .top-hub-wordmark {
            color: rgba(255, 245, 236, 0.94);
            font-size: 0.98rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            line-height: 1;
            text-transform: uppercase;
          }
          .nav-link {
            color: var(--nav-text);
            font-weight: 700;
            letter-spacing: 0.04em;
            min-height: 44px;
            padding: 0 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 14px;
          }
          .nav-link:hover {
            color: var(--nav-text-hover);
            background: rgba(255, 248, 241, 0.08);
          }
          .nav-link-active {
            color: #fff8f1 !important;
            background: rgba(255, 248, 241, 0.14);
          }
          .hero-context-link {
            display: inline-flex;
            align-items: center;
            min-height: 40px;
            padding: 7px 12px;
            border: 1px solid rgba(154, 52, 18, 0.34);
            border-radius: 10px;
            background: #FFF7ED;
            color: #9A3412 !important;
            font-weight: 800;
            text-decoration: underline;
            text-decoration-thickness: 1px;
            text-underline-offset: 3px;
          }
          .hero-context-link:hover,
          .hero-context-link:focus-visible {
            border-color: rgba(154, 52, 18, 0.62);
            background: #FFEDD5;
            color: #7C2D12 !important;
          }
          .drawer-toggle {
            color: var(--nav-text);
            background: rgba(255, 248, 241, 0.10);
            border: 1px solid rgba(255, 248, 241, 0.12);
            border-radius: 12px;
          }
          .dashboard-drawer {
            background:
              linear-gradient(180deg, rgba(255, 252, 248, 0.98) 0%, rgba(248, 241, 233, 0.96) 100%);
            color: var(--text);
            border-right: 1px solid rgba(137, 111, 92, 0.12);
            box-shadow: 12px 0 28px rgba(39, 24, 16, 0.10);
            width: 292px !important;
          }
          .dashboard-drawer .q-drawer__content {
            padding: 20px 16px 24px;
          }
          .drawer-eyebrow {
            color: rgba(122, 98, 83, 0.72);
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
          }
          .drawer-title {
            color: var(--text);
            font-size: 1.12rem;
            font-weight: 700;
            line-height: 1.3;
          }
          .drawer-summary {
            color: var(--text-soft);
            font-size: 0.88rem;
            line-height: 1.7;
          }
          .drawer-section-label {
            color: rgba(122, 98, 83, 0.62);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
          }
          .drawer-nav-link,
          .drawer-nav-button {
            display: block;
            color: var(--text) !important;
            text-decoration: none;
            border-radius: 18px;
            border: 1px solid rgba(137, 111, 92, 0.10);
            background: rgba(255, 255, 255, 0.78);
            padding: 13px 13px 12px;
            transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
            width: 100%;
            text-align: left;
          }
          .drawer-nav-link:visited,
          .drawer-nav-link:active,
          .drawer-nav-link:hover,
          .drawer-nav-button:visited,
          .drawer-nav-button:active,
          .drawer-nav-button:hover {
            color: var(--text) !important;
          }
          .drawer-nav-link:hover,
          .drawer-nav-button:hover {
            transform: translateX(2px);
            background: rgba(255, 250, 244, 0.98);
            border-color: rgba(217, 107, 31, 0.26);
          }
          .q-btn.drawer-nav-button::before,
          .q-btn.drawer-nav-button .q-focus-helper {
            background: transparent !important;
            opacity: 0 !important;
          }
          .q-btn.drawer-nav-button .q-btn__content {
            justify-content: flex-start;
            width: 100%;
          }
          .drawer-nav-title {
            color: var(--text) !important;
            font-size: 0.92rem;
            font-weight: 700;
            line-height: 1.35;
          }
          .drawer-nav-caption {
            color: var(--text-soft) !important;
            font-size: 0.8rem;
            line-height: 1.55;
            margin-top: 4px;
          }
          .drawer-note-card {
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid rgba(137, 111, 92, 0.10);
            border-radius: 18px;
            padding: 14px;
          }
          .drawer-note-title {
            color: var(--text);
            font-size: 0.9rem;
            font-weight: 700;
          }
          .drawer-note-copy {
            color: var(--text-soft);
            font-size: 0.82rem;
            line-height: 1.65;
          }
          @media (max-width: 1680px) {
            .dashboard-drawer {
              display: none !important;
            }
            .q-page-container {
              padding-left: 0 !important;
            }
          }
          .hero-service-name {
            color: var(--brand-deep);
            font-size: clamp(2rem, 2.6vw, 2.5rem);
            line-height: 1.0;
            font-weight: 700;
          }
          .hero-card {
            background:
              radial-gradient(circle at 84% 18%, rgba(247, 233, 214, 0.34), transparent 24%),
              linear-gradient(135deg, rgba(255, 254, 251, 0.99) 0%, rgba(249, 242, 234, 0.95) 100%);
            border: 1px solid rgba(137, 111, 92, 0.12);
            border-radius: 22px;
            box-shadow: 0 14px 30px rgba(84, 60, 46, 0.06);
          }
          .hero-copy-card {
            max-width: 720px;
            min-width: 0;
          }
          .hero-side-column {
            max-width: 420px;
            min-width: 0;
          }
          .hero-summary {
            color: var(--text-soft);
            font-size: 0.92rem;
            line-height: 1.5;
            max-width: 820px;
          }
          .suite-bridge-card {
            background:
              radial-gradient(circle at 100% 0%, rgba(255, 236, 215, 0.58), transparent 32%),
              linear-gradient(135deg, rgba(255, 251, 246, 0.98) 0%, rgba(247, 239, 229, 0.96) 100%);
            border: 1px solid rgba(137, 111, 92, 0.14);
            border-radius: 22px;
            padding: 18px;
            box-shadow: 0 12px 28px rgba(84, 60, 46, 0.06);
          }
          .suite-product-card {
            position: relative;
            border-radius: 20px;
            padding: 18px;
            min-height: 188px;
            border: 1px solid rgba(137, 111, 92, 0.12);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .suite-product-current {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(249, 242, 234, 0.96) 100%);
          }
          .suite-product-next {
            background: linear-gradient(180deg, rgba(255, 246, 238, 0.97) 0%, rgba(244, 232, 220, 0.95) 100%);
          }
          .suite-product-kicker {
            color: var(--brand-deep);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
          }
          .suite-product-name {
            color: var(--text);
            font-size: 1.25rem;
            line-height: 1.2;
            font-weight: 700;
          }
          .suite-product-copy {
            color: var(--text-soft);
            font-size: 0.9rem;
            line-height: 1.7;
          }
          .suite-handoff-column {
            min-width: 76px;
            gap: 8px;
          }
          .suite-handoff-arrow {
            width: 52px;
            height: 52px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(217, 107, 31, 0.18) 0%, rgba(185, 84, 22, 0.16) 100%);
            color: var(--brand-deep);
            font-size: 1.55rem;
            font-weight: 700;
            border: 1px solid rgba(217, 107, 31, 0.18);
            box-shadow: 0 10px 22px rgba(217, 107, 31, 0.12);
          }
          .suite-handoff-copy {
            color: var(--text-soft);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
          }
          .suite-mini-chip {
            border-radius: 999px;
            padding: 6px 11px;
            background: rgba(255, 253, 249, 0.82);
            border: 1px solid rgba(137, 111, 92, 0.12);
            color: var(--text-soft);
            font-size: 0.77rem;
            font-weight: 700;
          }
          .suite-stage-card {
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid rgba(137, 111, 92, 0.10);
            border-radius: 18px;
            padding: 14px 16px;
          }
          .suite-stage-label {
            color: var(--text-soft);
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.08em;
          }
          .suite-stage-value {
            color: var(--text);
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.5;
          }
          .input-shell {
            border-top: 4px solid var(--accent);
            background: rgba(255, 255, 255, 0.92);
          }
          .semantic-saved-panel {
            background: linear-gradient(180deg, rgba(248, 244, 238, 0.96) 0%, rgba(241, 236, 228, 0.92) 100%);
            border-left: 4px solid rgba(107, 90, 77, 0.28);
          }
          .semantic-schedule-panel {
            background: linear-gradient(180deg, rgba(255, 248, 240, 0.96) 0%, rgba(255, 241, 228, 0.92) 100%);
            border-left: 4px solid rgba(217, 107, 31, 0.24);
          }
          .semantic-settings-expansion .q-expansion-item__container {
            border-radius: 18px;
          }
          .q-btn.readonly-disabled-action,
          .q-btn.readonly-disabled-action.disabled,
          .q-btn.readonly-disabled-action.q-btn--disabled {
            background: #E7E0D8 !important;
            border-color: rgba(116, 102, 88, 0.28) !important;
            color: #75695F !important;
            box-shadow: none !important;
            filter: saturate(0.24) grayscale(0.18) !important;
            opacity: 1 !important;
            cursor: not-allowed !important;
          }
          .q-btn.readonly-disabled-action .q-btn__content {
            color: #75695F !important;
          }
          .readonly-demo-helper {
            display: inline-flex;
            align-items: center;
            width: fit-content;
            max-width: 100%;
            padding: 6px 10px;
            border-radius: 8px;
            background: rgba(231, 224, 216, 0.78);
            border: 1px solid rgba(116, 102, 88, 0.18);
            color: #6F6259;
            font-weight: 700;
          }
          .input-field-card {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(137, 111, 92, 0.12);
            border-radius: 20px;
            padding: 18px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
            min-width: 0;
            overflow: hidden;
          }
          .hero-status-card {
            background: linear-gradient(180deg, rgba(255, 254, 251, 0.98) 0%, rgba(247, 240, 232, 0.96) 100%);
            border: 1px solid rgba(137, 111, 92, 0.14);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44);
          }
          .hero-status-card .ui-tone-chip {
            background: rgba(255, 251, 247, 0.72);
            border-color: rgba(183, 145, 113, 0.10);
            color: rgba(95, 75, 65, 0.82);
          }
          .hero-status-value {
            color: var(--text);
          }
          .hero-observation-shell {
            align-items: stretch;
          }
          .hero-observation-card {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(249, 243, 236, 0.96) 100%);
            border: 1px solid rgba(137, 111, 92, 0.12);
            border-radius: 22px;
            box-shadow: 0 10px 24px rgba(84, 60, 46, 0.06);
          }
          .hero-observation-title {
            color: var(--text-soft);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
          }
          .hero-observation-value {
            color: var(--text);
            font-size: 1.18rem;
            line-height: 1.45;
            font-weight: 700;
          }
          .hero-network-chip {
            border-radius: 999px;
            padding: 6px 11px;
            background: rgba(217, 107, 31, 0.10);
            border: 1px solid rgba(217, 107, 31, 0.12);
            color: var(--brand-deep);
            font-size: 0.78rem;
            font-weight: 700;
          }
          .hero-network-edge {
            color: var(--text);
            font-size: 0.95rem;
            line-height: 1.6;
            font-weight: 700;
          }
          .result-network-card {
            background:
              radial-gradient(circle at 96% 0%, rgba(255, 235, 214, 0.44), transparent 28%),
              linear-gradient(180deg, rgba(255, 252, 248, 0.98) 0%, rgba(247, 240, 232, 0.96) 100%);
          }
          .input-action-card {
            background: linear-gradient(180deg, rgba(255, 251, 246, 0.98) 0%, rgba(247, 240, 232, 0.94) 100%);
            border: 1px solid rgba(122, 98, 83, 0.14);
            border-radius: 22px;
            padding: 18px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.48);
          }
          .followup-cta-panel {
            border-radius: 16px;
            padding: 12px 14px;
            background: rgba(255, 255, 255, 0.54);
            border: 1px dashed rgba(122, 98, 83, 0.18);
          }
          .followup-cta-title {
            color: var(--text);
            font-size: 0.92rem;
            font-weight: 700;
          }
          .followup-cta-note {
            color: var(--text-soft);
            font-size: 0.78rem;
            line-height: 1.5;
          }
          .ui-tone-chip {
            border-radius: 999px;
            padding: 7px 12px;
            background: rgba(255, 251, 247, 0.72);
            border: 1px solid rgba(183, 145, 113, 0.10);
            color: rgba(95, 75, 65, 0.82);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            width: fit-content;
          }
          .result-tone-chip {
            border-radius: 999px;
            padding: 7px 12px;
            background: rgba(249, 231, 211, 0.96);
            border: 1px solid rgba(217, 107, 31, 0.22);
            color: var(--accent-deep);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            width: fit-content;
          }
          .detail-tone-chip {
            border-radius: 999px;
            padding: 6px 11px;
            background: rgba(247, 239, 230, 0.96);
            border: 1px solid rgba(160, 132, 110, 0.16);
            color: var(--text-soft);
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            width: fit-content;
          }
          .card-primary,
          .section-card {
            background: var(--panel-strong);
            border: 1px solid var(--line-strong);
            border-radius: 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(14px);
          }
          .card-secondary,
          .panel-card {
            background: rgba(252, 248, 243, 0.52);
            border: 1px solid rgba(137, 111, 92, 0.06);
            border-radius: 24px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.22);
          }
          .card-detail {
            background: var(--surface-muted);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: none;
          }
          .soft-chip {
            border-radius: 999px;
            padding: 10px 16px;
            background: rgba(255, 251, 247, 0.84);
            border: 1px solid rgba(197, 150, 117, 0.18);
            color: var(--text-soft);
            font-weight: 600;
            max-width: 100%;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .text-wrap-anywhere {
            min-width: 0;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .url-break-all {
            min-width: 0;
            overflow-wrap: anywhere;
            word-break: break-all;
          }
          .headline-clamp-2 {
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            overflow: hidden;
          }
          .provider-card {
            min-height: 208px;
            position: relative;
            overflow: hidden;
          }
          .provider-active {
            background:
              linear-gradient(160deg, rgba(252, 248, 241, 0.98) 0%, rgba(247, 243, 236, 0.94) 100%);
            border: 1px solid rgba(240, 138, 36, 0.24);
            box-shadow: 0 18px 44px rgba(240, 138, 36, 0.10);
          }
          .provider-planned {
            background:
              linear-gradient(160deg, rgba(244, 249, 253, 0.94) 0%, rgba(238, 245, 251, 0.86) 100%);
            border: 1px dashed rgba(94, 124, 154, 0.22);
          }
          .provider-strip {
            position: absolute;
            inset: 0 auto auto 0;
            width: 100%;
            height: 4px;
          }
          .provider-strip-active {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
          }
          .provider-strip-planned {
            background: linear-gradient(90deg, rgba(123, 144, 165, 0.35) 0%, rgba(177, 198, 216, 0.28) 100%);
          }
          .provider-meta {
            margin-top: auto;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }
          .provider-meta-chip {
            border-radius: 999px;
            padding: 8px 12px;
            background: rgba(255, 252, 248, 0.82);
            border: 1px solid rgba(108, 82, 67, 0.10);
            color: var(--text-soft);
            font-size: 0.84rem;
            font-weight: 600;
          }
          .provider-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-top: 18px;
          }
          .provider-state-pill {
            border-radius: 999px;
            padding: 9px 14px;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.03em;
          }
          .provider-state-live {
            background: var(--accent-soft);
            color: var(--accent-deep);
          }
          .provider-state-disabled {
            background: var(--neutral-soft);
            color: var(--text-soft);
          }
          .status-badge {
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.04em;
          }
          .status-active {
            background: var(--accent-soft);
            color: var(--accent-deep);
          }
          .status-planned {
            background: var(--neutral-soft);
            color: var(--text-soft);
          }
          .metric-card {
            min-width: 220px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 250, 254, 0.92) 100%);
          }
          .insight-card {
            min-height: 236px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 249, 253, 0.94) 100%);
          }
          .current-scope-card {
            background: linear-gradient(180deg, rgba(255, 253, 251, 0.98) 0%, rgba(245, 250, 254, 0.94) 100%);
            border-top: 4px solid rgba(217, 107, 31, 0.52);
          }
          .current-empty-card {
            background: linear-gradient(180deg, rgba(255, 253, 249, 0.98) 0%, rgba(249, 242, 234, 0.94) 100%);
            border-top: 4px solid rgba(217, 107, 31, 0.58);
          }
          .result-scope-eyebrow {
            color: var(--accent-deep);
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
          }
          .current-scope-note {
            color: var(--text-soft);
          }
          .scope-status-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            min-height: 30px;
            padding: 7px 12px;
            font-size: 0.78rem;
            font-weight: 800;
            line-height: 1;
            white-space: nowrap;
          }
          .current-status-chip {
            color: var(--accent-deep);
            background: rgba(255, 232, 207, 0.78);
            border: 1px solid rgba(217, 107, 31, 0.20);
          }
          .saved-scope-card {
            background: linear-gradient(180deg, rgba(246, 242, 235, 0.92) 0%, rgba(239, 235, 227, 0.86) 100%);
            border-color: rgba(107, 90, 77, 0.22);
            border-left: 5px solid rgba(107, 90, 77, 0.34);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.26);
          }
          .saved-history-list-card {
            background: linear-gradient(180deg, rgba(250, 247, 241, 0.92) 0%, rgba(242, 237, 229, 0.88) 100%);
            border: 1px solid rgba(107, 90, 77, 0.16);
            border-left: 5px solid rgba(107, 90, 77, 0.26);
          }
          .saved-scope-label {
            width: fit-content;
            border-radius: 999px;
            padding: 5px 10px;
            color: var(--text-soft);
            background: rgba(107, 90, 77, 0.08);
            border: 1px solid rgba(107, 90, 77, 0.12);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
          }
          .saved-status-chip {
            color: var(--text-soft);
            background: rgba(107, 90, 77, 0.08);
            border: 1px solid rgba(107, 90, 77, 0.12);
          }
          .metric-value {
            color: var(--accent-deep);
          }
          .insight-headline {
            color: var(--text);
            line-height: 1.2;
          }
          .soft-label {
            color: var(--text-soft);
          }
          .eyebrow-label {
            color: var(--text-soft);
            letter-spacing: 0.18em;
            text-transform: uppercase;
          }
          .section-title {
            color: var(--brown);
          }
          .accent-button,
          .q-btn.accent-button {
            background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
            background-color: var(--accent) !important;
            border: 1px solid var(--accent-2) !important;
            color: white !important;
            box-shadow: 0 10px 22px rgba(217, 107, 31, 0.18) !important;
            border-radius: 16px;
            min-height: 52px;
            padding: 0 26px;
          }
          .q-btn.primary-run-button {
            min-width: 220px;
            min-height: 58px;
            padding: 0 34px;
            box-shadow: 0 14px 28px rgba(217, 107, 31, 0.22) !important;
          }
          .q-btn.accent-button.bg-deep-orange-7,
          .q-btn.accent-button[class*="bg-deep-orange"] {
            background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
            background-color: var(--accent) !important;
            color: white !important;
          }
          .q-btn.bg-primary:not(.q-btn--disabled),
          .q-btn[class*="bg-primary"]:not(.q-btn--disabled) {
            background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
            background-color: var(--accent) !important;
            color: white !important;
          }
          .q-btn.bg-primary .q-btn__content,
          .q-btn[class*="bg-primary"] .q-btn__content {
            color: white !important;
          }
          .q-btn.accent-button .q-btn__content {
            color: white !important;
            white-space: nowrap;
            word-break: keep-all;
          }
          .q-btn.accent-button::before,
          .q-btn.accent-button .q-focus-helper {
            background: transparent !important;
            opacity: 0 !important;
          }
          .secondary-button,
          .q-btn.secondary-button {
            background: rgba(255, 251, 246, 0.96) !important;
            border: 1px solid rgba(122, 98, 83, 0.18) !important;
            color: var(--accent-deep) !important;
            box-shadow: none !important;
            border-radius: 16px;
            min-height: 52px;
            padding: 0 24px;
          }
          .q-btn.followup-button {
            min-height: 42px;
            padding: 0 16px;
            background: rgba(255, 251, 246, 0.70) !important;
            border-color: rgba(122, 98, 83, 0.14) !important;
            box-shadow: none !important;
          }
          .q-btn.secondary-button.q-btn--outline {
            background: rgba(255, 251, 246, 0.96) !important;
          }
          .q-btn.secondary-button.text-primary,
          .q-btn.secondary-button[class*="text-primary"] {
            color: var(--accent-deep) !important;
          }
          .q-btn.text-primary,
          .q-btn[class*="text-primary"] {
            color: var(--accent-deep) !important;
          }
          .q-btn.q-btn--outline.text-primary,
          .q-btn.q-btn--outline[class*="text-primary"] {
            background: rgba(255, 251, 246, 0.96) !important;
            border: 1px solid rgba(122, 98, 83, 0.18) !important;
          }
          .q-btn.secondary-button .q-btn__content {
            color: var(--accent-deep) !important;
            white-space: nowrap;
            word-break: keep-all;
          }
          .q-btn.text-primary .q-btn__content,
          .q-btn[class*="text-primary"] .q-btn__content {
            color: var(--accent-deep) !important;
          }
          .q-btn.secondary-button::before,
          .q-btn.secondary-button .q-focus-helper {
            background: transparent !important;
            opacity: 0 !important;
          }
          .provider-runtime-card {
            background: linear-gradient(180deg, rgba(255, 251, 246, 0.98) 0%, rgba(247, 240, 232, 0.94) 100%);
            border: 1px solid rgba(122, 98, 83, 0.14);
            border-radius: 18px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.48);
          }
          .provider-chip-rail {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
          }
          .provider-chip-button,
          .q-btn.provider-chip-button {
            min-height: 38px;
            padding: 0 14px;
            border-radius: 999px;
            border: 1px solid rgba(122, 98, 83, 0.16) !important;
            background: rgba(255, 251, 246, 0.98) !important;
            color: var(--text-soft) !important;
            box-shadow: none !important;
            font-weight: 700;
          }
          .provider-chip-button .q-btn__content {
            color: inherit !important;
          }
          .provider-chip-button-active,
          .q-btn.provider-chip-button-active {
            background: linear-gradient(180deg, rgba(251, 236, 214, 0.98) 0%, rgba(245, 225, 196, 0.96) 100%) !important;
            border-color: rgba(217, 107, 31, 0.36) !important;
            color: var(--accent-deep) !important;
            box-shadow: 0 8px 16px rgba(217, 107, 31, 0.10) !important;
          }
          .provider-chip-button-ready,
          .q-btn.provider-chip-button-ready {
            background: rgba(255, 251, 246, 0.96) !important;
            border-color: rgba(122, 98, 83, 0.18) !important;
            color: var(--text-soft) !important;
          }
          .provider-chip-button-disabled,
          .q-btn.provider-chip-button-disabled {
            background: rgba(234, 229, 224, 0.96) !important;
            border-color: rgba(157, 145, 136, 0.22) !important;
            color: #8e837a !important;
            box-shadow: none !important;
          }
          .provider-chip-button-disabled .q-btn__content {
            color: #8e837a !important;
          }
          .q-btn.provider-chip-button::before,
          .q-btn.provider-chip-button .q-focus-helper {
            background: transparent !important;
            opacity: 0 !important;
          }
          .step-rail {
            background: rgba(250, 244, 237, 0.92);
            border: 1px solid rgba(191, 174, 159, 0.56);
            border-radius: 20px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .step-chip-active {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: white;
            box-shadow: 0 10px 18px rgba(217, 107, 31, 0.20);
          }
          .step-chip-muted {
            background: rgba(255, 251, 246, 0.94);
            color: var(--muted);
          }
          .source-pill {
            border-radius: 18px;
            padding: 12px 14px;
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid rgba(94, 124, 154, 0.10);
          }
          .result-highlight-card {
            min-height: 232px;
            min-width: 0;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.99) 0%, rgba(248, 242, 234, 0.96) 100%);
            border: 1px solid rgba(137, 111, 92, 0.14);
          }
          .result-highlight-quiet {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.99) 0%, rgba(248, 242, 234, 0.96) 100%);
          }
          .result-highlight-strong {
            background: linear-gradient(180deg, rgba(255, 250, 244, 0.99) 0%, rgba(247, 239, 230, 0.96) 100%);
            border: 1px solid rgba(217, 107, 31, 0.22);
            border-top: 5px solid var(--accent);
            color: var(--text);
            box-shadow: 0 12px 24px rgba(84, 60, 46, 0.07);
          }
          .result-metric-number {
            color: var(--accent-deep);
            font-family: "Sora", sans-serif;
            font-size: clamp(2.8rem, 5vw, 3.9rem);
            line-height: 1;
            font-weight: 700;
          }
          .result-metric-ratio {
            color: var(--text);
            font-family: "Sora", sans-serif;
            font-size: clamp(1.45rem, 2vw, 1.85rem);
            line-height: 1.2;
            font-weight: 700;
          }
          .result-metric-percent {
            color: var(--accent-deep);
            font-family: "Sora", sans-serif;
            font-size: clamp(2.2rem, 4vw, 3rem);
            line-height: 1;
            font-weight: 700;
          }
          .result-metric-unit {
            color: var(--muted);
            font-size: 1.35rem;
            font-weight: 600;
          }
          .result-metric-caption {
            color: var(--text-soft);
            font-size: 0.95rem;
            line-height: 1.6;
          }
          .result-inline-note {
            color: var(--muted);
            font-size: 0.83rem;
            line-height: 1.6;
          }
          .result-strong-eyebrow {
            color: var(--accent-deep);
          }
          .result-strong-title {
            color: var(--text);
          }
          .result-strong-headline {
            color: var(--text);
            text-shadow: none;
          }
          .result-strong-copy {
            color: var(--text-soft);
          }
          .result-strong-note {
            color: var(--text-soft);
          }
          .ranked-source-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 14px;
          }
          .ranked-source-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(137, 111, 92, 0.10);
          }
          .ranked-source-rank {
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: rgba(217, 107, 31, 0.10);
            color: var(--accent-deep);
            font-family: "Sora", sans-serif;
            font-weight: 700;
            font-size: 0.92rem;
            flex: 0 0 auto;
          }
          .ranked-source-copy {
            min-width: 0;
            flex: 1;
          }
          .ranked-source-title {
            color: var(--text);
            font-size: 0.94rem;
            font-weight: 700;
            line-height: 1.4;
          }
          .ranked-source-meta {
            color: var(--muted);
            font-size: 0.8rem;
            line-height: 1.4;
            margin-top: 2px;
            word-break: break-word;
          }
          .source-influence-compact {
            min-width: 0;
          }
          .source-influence-compact-item {
            padding: 10px 0;
            border-top: 1px solid rgba(137, 111, 92, 0.10);
          }
          .source-influence-compact-item:first-child {
            border-top: 0;
            padding-top: 0;
          }
          .source-influence-bar {
            width: 100%;
            height: 6px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(137, 111, 92, 0.11);
          }
          .source-influence-bar-fill {
            height: 100%;
            border-radius: 999px;
          }
          .source-influence-self {
            background: var(--self);
          }
          .source-influence-competitor {
            background: var(--competitive);
          }
          .source-influence-external {
            background: var(--external);
          }
          .competitive-snapshot {
            border-radius: 18px;
            padding: 14px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(137, 111, 92, 0.12);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44);
          }
          .competitive-snapshot-headline {
            color: var(--text);
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.45;
          }
          .competitive-snapshot-badge {
            color: var(--accent-deep);
            background: rgba(217, 107, 31, 0.10);
            border: 1px solid rgba(217, 107, 31, 0.18);
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.74rem;
            font-weight: 700;
            line-height: 1;
          }
          .competitive-sharebar {
            height: 10px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(137, 111, 92, 0.10);
          }
          .competitive-sharebar-segment {
            height: 100%;
            min-width: 8px;
          }
          .segment-self {
            background: var(--self);
          }
          .segment-competitor {
            background: var(--competitive);
          }
          .segment-external {
            background: var(--external);
          }
          .competitive-snapshot-chip {
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.78rem;
            font-weight: 700;
            line-height: 1;
            border: 1px solid rgba(137, 111, 92, 0.10);
          }
          .chip-self {
            color: var(--self);
            background: var(--self-soft);
          }
          .chip-competitor {
            color: var(--competitive);
            background: var(--competitive-soft);
          }
          .chip-external {
            color: var(--external);
            background: var(--external-soft);
          }
          .judgment-compact-panel,
          .judgment-summary-panel {
            border-radius: 12px;
            padding: 12px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(137, 111, 92, 0.12);
            min-width: 0;
            overflow: hidden;
          }
          .judgment-panel-grid {
            align-items: stretch;
          }
          .judgment-priority-strip {
            border-radius: 16px;
            padding: 14px;
            background: linear-gradient(180deg, rgba(255, 251, 246, 0.94) 0%, rgba(247, 240, 232, 0.90) 100%);
            border: 1px solid rgba(137, 111, 92, 0.14);
          }
          .judgment-priority-step {
            align-items: center;
            gap: 10px;
            border-radius: 14px;
            padding: 12px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(137, 111, 92, 0.12);
            min-width: 0;
            overflow: hidden;
          }
          .priority-step-high {
            border-color: rgba(161, 79, 36, 0.26);
            background: rgba(255, 241, 229, 0.86);
          }
          .priority-step-medium {
            border-color: rgba(166, 104, 55, 0.22);
            background: rgba(255, 248, 236, 0.86);
          }
          .priority-step-low {
            border-color: rgba(66, 125, 95, 0.18);
            background: rgba(240, 249, 243, 0.74);
          }
          .priority-step-unknown {
            border-color: rgba(137, 111, 92, 0.12);
            background: rgba(255, 255, 255, 0.66);
          }
          .priority-step-index {
            width: 26px;
            height: 26px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
            color: white;
            background: var(--brown);
            font-family: "Sora", sans-serif;
            font-size: 0.76rem;
            font-weight: 800;
            line-height: 1;
          }
          .priority-step-icon {
            color: var(--accent-deep);
            font-size: 1.2rem;
            flex: 0 0 auto;
          }
          .priority-step-title {
            color: var(--text);
            font-size: 0.84rem;
            font-weight: 800;
            line-height: 1.3;
            word-break: break-word;
          }
          .priority-step-value {
            color: var(--accent-deep);
            font-size: 0.96rem;
            font-weight: 800;
            line-height: 1.35;
            word-break: break-word;
          }
          .priority-step-next {
            color: var(--text-soft);
            font-size: 0.74rem;
            font-weight: 700;
            line-height: 1.35;
            word-break: break-word;
          }
          .judgment-compact-headline,
          .judgment-card-headline {
            color: var(--text);
            font-size: 0.98rem;
            font-weight: 700;
            line-height: 1.45;
            word-break: break-word;
          }
          .judgment-card-headline {
            font-size: 1.05rem;
          }
          .judgment-badge,
          .judgment-small-badge {
            display: inline-flex;
            align-items: center;
            min-height: 24px;
            border-radius: 999px;
            padding: 5px 9px;
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1;
            border: 1px solid rgba(137, 111, 92, 0.10);
            white-space: nowrap;
          }
          .judgment-badge-low,
          .judgment-badge-stable,
          .judgment-small-badge-low {
            color: var(--self);
            background: var(--self-soft);
          }
          .judgment-badge-medium,
          .judgment-badge-variable,
          .judgment-badge-chance,
          .judgment-small-badge-medium {
            color: var(--competitive);
            background: var(--competitive-soft);
          }
          .judgment-badge-high,
          .judgment-small-badge-high {
            color: var(--external);
            background: var(--external-soft);
          }
          .judgment-badge-unknown {
            color: var(--text-soft);
            background: rgba(137, 111, 92, 0.08);
          }
          .judgment-sharebar {
            height: 10px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(137, 111, 92, 0.10);
          }
          .judgment-sharebar-segment {
            height: 100%;
            min-width: 8px;
          }
          .judgment-meter {
            width: 100%;
            height: 7px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(137, 111, 92, 0.11);
          }
          .judgment-meter-fill {
            height: 100%;
            border-radius: 999px;
          }
          .judgment-meter-label {
            color: var(--text-soft);
            font-size: 0.74rem;
            font-weight: 700;
          }
          .judgment-meter-value {
            color: var(--text);
            font-family: "Sora", sans-serif;
            font-size: 0.76rem;
            font-weight: 700;
          }
          .judgment-segments {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 6px;
          }
          .judgment-segment {
            min-height: 28px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            border: 1px solid rgba(137, 111, 92, 0.10);
            color: var(--text-soft);
            background: rgba(137, 111, 92, 0.06);
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1;
          }
          .judgment-segment-active.judgment-segment-stable {
            color: var(--self);
            background: var(--self-soft);
          }
          .judgment-segment-active.judgment-segment-variable {
            color: var(--competitive);
            background: var(--competitive-soft);
          }
          .judgment-segment-active.judgment-segment-chance {
            color: var(--external);
            background: var(--external-soft);
          }
          .judgment-question-row {
            border-top: 1px solid rgba(137, 111, 92, 0.10);
            padding-top: 8px;
          }
          .judgment-question-row:first-child {
            border-top: 0;
            padding-top: 0;
          }
          .judgment-question-label {
            color: var(--text);
            font-size: 0.86rem;
            font-weight: 700;
            line-height: 1.35;
            min-width: 0;
            word-break: break-word;
          }
          .result-action-panel {
            border-radius: 18px;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.14);
          }
          .detail-fixed-block {
            border-radius: 18px;
            padding: 16px;
            background: rgba(247, 239, 230, 0.92);
            border: 1px solid rgba(160, 132, 110, 0.14);
            min-width: 0;
            overflow: hidden;
          }
          .detail-result-block {
            border-radius: 18px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(137, 111, 92, 0.12);
            min-width: 0;
            overflow: hidden;
          }
          .chart-shell {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 249, 253, 0.94) 100%);
          }
          .summary-eyebrow {
            color: rgba(95, 75, 65, 0.76);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: none;
          }
          .result-highlight-strong .summary-eyebrow,
          .summary-eyebrow.result-strong-title,
          .summary-eyebrow.result-strong-eyebrow {
            color: var(--accent-deep);
          }
          .summary-mainline {
            color: var(--text);
            font-size: clamp(1.55rem, 2.3vw, 2.05rem);
            line-height: 1.15;
            font-weight: 700;
          }
          .support-clamp-1,
          .support-clamp-2,
          .support-clamp-3 {
            display: -webkit-box;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          .support-clamp-1 {
            -webkit-line-clamp: 1;
          }
          .support-clamp-2 {
            -webkit-line-clamp: 2;
          }
          .support-clamp-3 {
            -webkit-line-clamp: 3;
          }
          .question-heatmap {
            border-radius: 18px;
            padding: 14px;
            background: rgba(255, 255, 255, 0.80);
            border: 1px solid rgba(137, 111, 92, 0.10);
          }
          .mini-heatmap {
            border-radius: 18px;
            padding: 12px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(137, 111, 92, 0.10);
          }
          .mini-heatmap-question {
            color: var(--text);
            font-size: 0.8rem;
            font-weight: 700;
            line-height: 1.35;
            width: 82px;
            min-width: 82px;
          }
          .mini-heatmap-axis {
            color: var(--text-soft);
            font-size: 0.7rem;
            font-weight: 700;
            text-align: center;
            width: 58px;
          }
          .mini-heatmap-cell {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 58px;
            height: 28px;
            border-radius: 11px;
            color: var(--text);
            font-family: "Sora", sans-serif;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid rgba(137, 111, 92, 0.08);
          }
          .priority-question-strip {
            border-radius: 16px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(137, 111, 92, 0.10);
          }
          .priority-question-row {
            min-width: 0;
          }
          .priority-question-label {
            color: var(--text);
            font-size: 0.84rem;
            font-weight: 700;
            line-height: 1.35;
            min-width: 72px;
            max-width: 112px;
          }
          .priority-question-chip {
            display: inline-flex;
            align-items: center;
            min-height: 26px;
            border-radius: 999px;
            padding: 5px 9px;
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1;
            border: 1px solid rgba(137, 111, 92, 0.10);
            white-space: nowrap;
          }
          .priority-question-positive {
            color: var(--self);
            background: var(--self-soft);
          }
          .priority-question-neutral {
            color: var(--competitive);
            background: var(--competitive-soft);
          }
          .priority-question-negative {
            color: var(--external);
            background: var(--external-soft);
          }
          .heatmap-header {
            padding-bottom: 2px;
          }
          .heatmap-row {
            min-height: 34px;
          }
          .heatmap-row-label {
            color: var(--text);
            font-size: 0.82rem;
            font-weight: 700;
            min-width: 88px;
            line-height: 1.4;
          }
          .heatmap-row-label-header,
          .heatmap-axis-title {
            color: var(--text-soft);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
          }
          .heatmap-axis-title {
            width: 56px;
            text-align: center;
          }
          .heatmap-cell {
            width: 56px;
            height: 28px;
            border-radius: 12px;
            border: 1px solid rgba(137, 111, 92, 0.08);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.30);
          }
          .heatmap-found {
            background: var(--self-soft);
          }
          .heatmap-cited {
            background: rgba(217, 107, 31, 0.14);
          }
          .heatmap-external {
            background: var(--external-soft);
          }
          .heatmap-intensity-0 {
            opacity: 0.16;
          }
          .heatmap-intensity-1 {
            opacity: 0.34;
          }
          .heatmap-intensity-2 {
            opacity: 0.52;
          }
          .heatmap-intensity-3 {
            opacity: 0.74;
          }
          .heatmap-intensity-4 {
            opacity: 1;
          }
          .bubble-strip {
            min-height: 72px;
          }
          .opportunity-bubble {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            font-family: "Sora", sans-serif;
            font-weight: 700;
            line-height: 1;
            border: 1px solid rgba(137, 111, 92, 0.10);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .bubble-tone-positive {
            background: rgba(111, 139, 103, 0.14);
            color: var(--self);
          }
          .bubble-tone-neutral {
            background: rgba(194, 146, 70, 0.16);
            color: var(--competitive);
          }
          .bubble-tone-external {
            background: rgba(190, 107, 74, 0.14);
            color: var(--external);
          }
          .bubble-size-1 {
            width: 56px;
            height: 56px;
            font-size: 0.72rem;
          }
          .bubble-size-2 {
            width: 68px;
            height: 68px;
            font-size: 0.76rem;
          }
          .bubble-size-3 {
            width: 82px;
            height: 82px;
            font-size: 0.8rem;
          }
          .bubble-size-4 {
            width: 96px;
            height: 96px;
            font-size: 0.84rem;
          }
          .page-opportunity-strip {
            align-items: stretch;
          }
          .page-opportunity-item {
            min-width: 88px;
            border-radius: 18px;
            padding: 12px 12px 10px;
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(137, 111, 92, 0.10);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .page-opportunity-label {
            color: var(--text);
            font-size: 0.86rem;
            font-weight: 700;
            line-height: 1.35;
          }
          .page-opportunity-meta {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
          }
          .page-state-urgent {
            border-top: 4px solid rgba(190, 107, 74, 0.82);
          }
          .page-state-urgent .page-opportunity-meta {
            color: var(--external);
          }
          .page-state-followup {
            border-top: 4px solid rgba(217, 107, 31, 0.80);
          }
          .page-state-followup .page-opportunity-meta {
            color: var(--accent-deep);
          }
          .page-state-maintain {
            border-top: 4px solid rgba(111, 139, 103, 0.78);
          }
          .page-state-maintain .page-opportunity-meta {
            color: var(--self);
          }
          .mini-stat-card {
            border-radius: 18px;
            padding: 14px 14px 12px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.10);
            min-width: 128px;
            overflow: hidden;
          }
          .workflow-lane-card {
            border-radius: 18px;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(94, 124, 154, 0.10);
            min-width: 180px;
          }
          .workflow-stage-card {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 249, 253, 0.94) 100%);
            border: 1px solid rgba(94, 124, 154, 0.14);
            border-radius: 22px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .workflow-step-pill {
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            width: fit-content;
          }
          .workflow-step-pill-active {
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: white;
            box-shadow: 0 10px 18px rgba(217, 107, 31, 0.18);
          }
          .workflow-step-pill-muted {
            background: rgba(255, 251, 246, 0.94);
            color: var(--text-soft);
          }
          .stage-note-card {
            border-radius: 20px;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(137, 111, 92, 0.07);
            min-width: 0;
            overflow: hidden;
          }
          .detail-tabs-shell {
            background: rgba(240, 247, 252, 0.68);
            border: 1px solid rgba(94, 124, 154, 0.18);
            border-radius: 20px;
            padding: 6px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
          }
          .detail-tabs-shell .q-tab {
            border-radius: 16px;
            color: var(--text-soft);
            font-weight: 700;
            letter-spacing: 0.04em;
            min-height: 48px;
          }
          .detail-tabs-shell .q-tab--active {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 250, 254, 0.96) 100%);
            color: var(--accent-deep);
            box-shadow: 0 10px 20px rgba(240, 138, 36, 0.10);
          }
          .detail-tabs-shell .q-tab__indicator {
            display: none;
          }
          .detail-tab-panels {
            background: transparent;
          }
          .settings-provider-card {
            flex: 1 1 auto !important;
            width: 100%;
            max-width: 100%;
          }
          .settings-saved-card {
            flex: 1 1 auto !important;
            width: 100%;
            min-width: 0 !important;
          }
          .settings-overview-row {
            flex-direction: column !important;
            align-items: stretch !important;
          }
          @media (min-width: 761px) {
            .input-main-grid {
              display: grid !important;
              grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.95fr);
              align-items: start !important;
            }
            .input-main-grid > .input-main-column {
              grid-column: 1;
              grid-row: 1;
              min-width: 0 !important;
            }
            .input-main-grid > .input-side-column {
              display: contents;
            }
            .input-main-grid > .input-side-column > .input-field-card {
              grid-column: 2;
              grid-row: 1;
            }
            .input-main-grid > .input-side-column > .input-action-card {
              grid-column: 1 / -1;
              grid-row: 2;
              width: 100%;
              min-width: 0;
            }
          }
          .signal-chip {
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.8rem;
            font-weight: 700;
            max-width: 100%;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .signal-positive {
            background: var(--self-soft);
            color: var(--self);
          }
          .signal-negative {
            background: var(--external-soft);
            color: var(--external);
          }
          .signal-neutral {
            background: var(--competitive-soft);
            color: var(--competitive);
          }
          .action-item {
            border-radius: 18px;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.12);
          }
          .status-row {
            border-radius: 20px;
            background: rgba(245, 250, 254, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.12);
          }
          .source-group-card {
            border-radius: 20px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(94, 124, 154, 0.12);
            min-width: 0;
            overflow: hidden;
          }
          .source-group-positive {
            background: rgba(241, 250, 245, 0.96);
            border-color: rgba(47, 138, 87, 0.22);
          }
          .source-group-negative {
            background: rgba(255, 246, 242, 0.96);
            border-color: rgba(180, 74, 43, 0.20);
          }
          .source-group-neutral {
            background: rgba(255, 248, 239, 0.96);
            border-color: rgba(182, 122, 53, 0.18);
          }
          .evidence-link {
            color: var(--accent-deep);
            overflow-wrap: anywhere;
            word-break: break-all;
          }
          .text-main {
            color: var(--text);
          }
          .text-support {
            color: var(--text-soft);
          }
          .text-helper {
            color: var(--muted);
          }
          .text-brand {
            color: var(--accent-deep);
          }
          .text-self {
            color: var(--self);
          }
          .text-competitive {
            color: var(--competitive);
          }
          .text-external {
            color: var(--external);
          }
          .text-runtime-ready {
            color: var(--self);
          }
          .text-runtime-pending {
            color: var(--external);
          }
          .text-runtime-planned {
            color: var(--competitive);
          }
          .ui-divider {
            color: rgba(122, 79, 48, 0.44);
          }
          .q-field__label,
          .q-field__native,
          .q-field__input,
          .q-item__label,
          .q-select__dropdown-icon {
            font-size: 16px !important;
          }
          .q-textarea textarea,
          .q-field input {
            line-height: 1.55 !important;
          }
          .q-table thead th {
            font-size: 14px !important;
            font-weight: 700 !important;
            color: var(--text-soft) !important;
            background: rgba(236, 245, 251, 0.94);
          }
          .q-table tbody td {
            font-size: 15px !important;
            line-height: 1.55 !important;
            vertical-align: top;
          }
          .q-table th,
          .q-table td {
            padding: 12px 14px !important;
          }
          .q-expansion-item__container {
            border-radius: 18px;
            overflow: hidden;
          }
          .panel-card .q-expansion-item__container {
            background: rgba(255, 251, 246, 0.58);
            border: 1px solid rgba(137, 111, 92, 0.06);
            box-shadow: none;
          }
          .panel-card .q-item {
            min-height: 52px;
          }
          .panel-card .q-expansion-item__content {
            background: rgba(255, 253, 250, 0.64);
          }
          .chart-shell .js-plotly-plot,
          .chart-shell > div {
            width: 100% !important;
          }
          .q-table__container {
            max-width: 100%;
            overflow-x: auto;
          }
          @media (max-width: 1100px) {
            .nav-link {
              font-size: 1.1rem !important;
            }
            .settings-provider-card,
            .settings-saved-card {
              flex: 1 1 100% !important;
              width: 100% !important;
              max-width: 100% !important;
              min-width: 0 !important;
            }
            .hero-card {
              border-radius: 22px;
            }
            .hero-status-card {
              min-width: 150px !important;
            }
            .suite-bridge-flow {
              flex-direction: column;
            }
            .suite-handoff-column {
              min-width: 100%;
              flex-direction: row;
            }
            .suite-handoff-arrow {
              transform: rotate(90deg);
            }
          }
          @media (max-width: 760px) {
            body,
            #app,
            .q-layout,
            .q-page-container,
            .q-page {
              width: 100%;
              max-width: 100%;
              overflow-x: hidden !important;
            }
            .nav-link {
              font-size: 1rem !important;
            }
            .top-nav-shell {
              padding: 6px 8px !important;
            }
            .top-nav-layout {
              flex-wrap: nowrap !important;
              gap: 5px !important;
            }
            .top-logo-link {
              flex: 0 0 auto;
              gap: 0;
            }
            .top-nav-links {
              flex: 1 1 auto;
              min-width: 0;
              flex-wrap: nowrap !important;
              justify-content: flex-end;
              gap: 1px !important;
            }
            .top-nav-links .nav-link {
              flex: 0 1 auto;
              min-width: 0;
              min-height: 40px;
              padding: 0 4px;
              border-radius: 9px;
              font-size: 11px !important;
              letter-spacing: 0;
              white-space: nowrap;
            }
            .top-hub-wordmark {
              display: none;
            }
            .top-nav-layout .top-logo-lockup {
              min-height: 34px;
              padding: 4px 6px;
              border-radius: 11px;
            }
            .top-nav-layout .top-logo-wordmark-image {
              width: 72px;
              height: 16px;
            }
            .q-page [class*="min-w-"],
            .q-page [class*="w-["],
            .q-dialog [class*="min-w-"],
            .q-dialog [class*="w-["] {
              min-width: 0 !important;
              max-width: 100% !important;
            }
            .q-field,
            .q-select,
            .q-input,
            .q-textarea {
              width: 100% !important;
              max-width: 100% !important;
              min-width: 0 !important;
            }
            .q-field__control,
            .q-field__native,
            .q-field__input,
            .q-field__inner {
              min-width: 0 !important;
              max-width: 100% !important;
            }
            .q-btn {
              max-width: 100% !important;
              min-width: 0 !important;
            }
            .q-btn.accent-button,
            .q-btn.secondary-button,
            .q-btn.followup-button {
              width: auto;
              min-width: 216px !important;
              justify-content: center;
              padding-left: 14px !important;
              padding-right: 14px !important;
            }
            .q-btn .q-btn__content {
              white-space: nowrap !important;
              word-break: keep-all !important;
              overflow-wrap: normal !important;
              min-width: max-content;
            }
            .q-page .row {
              max-width: 100%;
            }
            .q-page .section-card,
            .q-page .card-primary,
            .q-page .card-secondary,
            .q-page .input-field-card,
            .q-page .panel-card,
            .q-page .chart-shell,
            .q-page .q-expansion-item {
              flex: 1 1 100% !important;
              width: 100% !important;
              max-width: 100% !important;
              min-width: 0 !important;
            }
            .q-page .chart-shell {
              overflow: hidden;
            }
            .input-main-grid {
              align-items: stretch !important;
            }
            .input-main-grid > .input-main-column,
            .input-main-grid > .input-side-column {
              flex: 1 1 100% !important;
              width: 100% !important;
              max-width: 100% !important;
              min-width: 0 !important;
            }
            .market-context-candidate-row {
              align-items: stretch !important;
            }
            .market-context-category-label {
              flex: 1 1 100% !important;
              width: 100% !important;
            }
            .q-btn.market-context-candidate-button {
              width: 100% !important;
              min-width: 0 !important;
              justify-content: center;
            }
            .q-btn.market-context-candidate-button .q-btn__content {
              min-width: 0 !important;
              white-space: normal !important;
              overflow-wrap: anywhere !important;
              word-break: keep-all !important;
              line-height: 1.35;
            }
            .js-plotly-plot .modebar {
              display: none !important;
            }
            .js-plotly-plot,
            .plot-container,
            .svg-container,
            .main-svg {
              max-width: 100% !important;
            }
            .q-tabs {
              max-width: 100%;
              overflow-x: auto;
            }
            .detail-tabs-shell .q-tab {
              min-width: max-content;
              flex: 0 0 auto;
            }
            .q-table__container {
              max-width: 100%;
              overflow-x: auto;
            }
            .top-logo-lockup {
              min-height: 38px;
              padding: 6px 10px;
              border-radius: 14px;
            }
            .top-logo-wordmark-image {
              width: 146px;
              height: 21px;
            }
            .top-hub-wordmark {
              font-size: 0.84rem;
              letter-spacing: 0.12em;
            }
            .hero-card,
            .section-card,
            .card-primary,
            .workflow-stage-card,
            .workflow-lane-card,
            .step-rail,
            .panel-card,
            .result-highlight-card {
              min-width: 0 !important;
              border-radius: 20px;
            }
            .hero-card {
              padding: 16px !important;
            }
            .hero-summary {
              font-size: 0.86rem;
              line-height: 1.45;
            }
            .hero-status-card {
              padding: 12px !important;
              min-width: calc(50% - 8px) !important;
            }
            .source-group-card,
            .mini-stat-card {
              min-width: 0 !important;
            }
            .result-highlight-card,
            .insight-card,
            .workflow-lane-card {
              width: 100% !important;
              flex: 1 1 100% !important;
            }
            .result-highlight-card {
              min-height: auto;
              padding: 16px !important;
            }
            .stage-note-card {
              padding: 12px 14px;
            }
            .summary-mainline {
              font-size: clamp(1.22rem, 6vw, 1.45rem);
            }
            .signal-chip {
              padding: 6px 10px;
              font-size: 0.76rem;
            }
            .support-clamp-3 {
              -webkit-line-clamp: 2;
            }
            .heatmap-row-label {
              min-width: 70px;
              font-size: 0.76rem;
            }
            .heatmap-axis-title,
            .heatmap-cell {
              width: 48px;
            }
            .opportunity-bubble {
              font-size: 0.72rem;
            }
            .bubble-size-1 {
              width: 50px;
              height: 50px;
            }
            .bubble-size-2 {
              width: 60px;
              height: 60px;
            }
            .bubble-size-3 {
              width: 72px;
              height: 72px;
            }
            .bubble-size-4 {
              width: 84px;
              height: 84px;
            }
            .q-table th,
            .q-table td {
              padding: 10px 12px !important;
            }
          }
          @media (max-width: 600px) {
            .q-page .brand-context-grid.row {
              flex-direction: column !important;
              flex-wrap: nowrap !important;
              align-items: stretch !important;
            }
            .q-page .brand-context-grid.row > .brand-context-field.column {
              flex: 1 1 100% !important;
              width: 100% !important;
              max-width: 100% !important;
              min-width: 0 !important;
            }
          }
        </style>
        """
    )


def render_top_nav() -> None:
    hub_url = _runtime_url("HUB_URL", "http://127.0.0.1:8090/")
    kotomake_url = _runtime_url("KOTOMAKE_URL", "http://127.0.0.1:8080/")
    kotomigaki_url = _runtime_url("KOTOMIGAKI_URL", "http://127.0.0.1:8081/")
    with ui.header().classes("top-shell top-nav-shell items-center px-5 py-3"):
        with ui.row().classes("top-nav-layout w-full max-w-7xl mx-auto items-center justify-between gap-4 flex-wrap"):
            with ui.link("", hub_url, new_tab=True).classes("top-logo-link"):
                with ui.element("span").classes("top-logo-lockup"):
                    ui.image("/branding/kotomegane-logo.svg").classes("top-logo-wordmark-image")
                ui.label("TECHIE HUB").classes("brand-font top-hub-wordmark")
            with ui.row().classes("top-nav-links items-center gap-3 flex-wrap"):
                ui.link("HOME", hub_url, new_tab=True).classes("nav-link text-[17px]")
                ui.link("コトメイク", kotomake_url, new_tab=True).classes("nav-link text-[17px]")
                ui.label("コトメガネ").classes("nav-link nav-link-active text-[17px]")
                ui.link("コトミガキ", kotomigaki_url, new_tab=True).classes("nav-link text-[17px]")


def render_dashboard_drawer(nav_actions: dict[str, callable] | None = None) -> None:
    _ = nav_actions
    return


def render_workflow_rail() -> None:
    with ui.card().classes("step-rail p-3 w-full"):
        with ui.row().classes("w-full gap-3 flex-wrap"):
            for step, title, tone in [
                ("1", "入力する", "workflow-step-pill-active"),
                ("2", "結果を見る", "workflow-step-pill-muted"),
                ("3", "詳細", "workflow-step-pill-muted"),
            ]:
                with ui.column().classes("workflow-lane-card flex-1 gap-2"):
                    ui.label(f"手順 {step}").classes(f"workflow-step-pill {tone}")
                    ui.label(title).classes("section-font text-[22px] font-bold text-main")


def render_stage_header(step: str, title: str, description: str) -> None:
    with ui.row().classes("w-full gap-4 items-center flex-wrap px-1"):
        with ui.row().classes("w-full gap-4 items-center flex-wrap"):
            ui.label(f"手順 {step}").classes("workflow-step-pill workflow-step-pill-active")
            with ui.column().classes("gap-2 flex-1 min-w-[260px]"):
                ui.label(title).classes("section-font section-title text-[24px] font-bold")
                if description:
                    ui.label(description).classes("text-[13px] leading-5 text-support")
