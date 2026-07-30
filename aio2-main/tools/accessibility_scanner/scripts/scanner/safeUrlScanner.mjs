/* global CSS, HTMLFormElement, HTMLImageElement, HTMLInputElement, HTMLSelectElement, HTMLTextAreaElement, Node, document */

import { randomUUID } from "node:crypto";
import AxeBuilder from "@axe-core/playwright";
import { chromium } from "@playwright/test";
import { calculateScoreSnapshot } from "./scoring.mjs";
import { redactText, redactUrl, validateUrlForScanning } from "./urlSafety.mjs";

const DEFAULT_OPTIONS = {
  maxRedirects: 5,
  navigationTimeoutMs: 30_000,
  idleTimeoutMs: 10_000,
  maxTabSteps: 20,
  viewport: {
    width: 1366,
    height: 768,
    deviceScaleFactor: 1,
  },
};

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);
const BLOCKED_HEADER_NAMES = new Set(["authorization", "cookie", "proxy-authorization"]);
const DEFAULT_PROFILE_IDS = ["jis-2016-aa"];
const JIS_2016_AA_AXE_TAGS = ["wcag2a", "wcag2aa"];
const STANDARDS_CHECKED_AT = "2026-06-11";
const DEFAULT_PAGE_ROLE = "top";
const DEFAULT_PAGE_WEIGHT = 1;
const COLLECTION_LIMITS = {
  headings: 80,
  landmarks: 80,
  controls: 160,
  images: 160,
  axeNodesPerIssue: 20,
  axeChecksPerNode: 12,
};

export async function scanUrl(input, options = {}) {
  const scanOptions = { ...DEFAULT_OPTIONS, ...options };
  const startedAt = new Date().toISOString();
  const scanRunId = randomUUID();
  const requestedUrl = redactUrl(input);
  const safety = await validateUrlForScanning(input, {
    allowLocalFixture: scanOptions.allowLocalFixture === true,
  });

  if (!safety.ok) {
    return createFailedReport({
      scanRunId,
      requestedUrl: safety.redactedUrl || requestedUrl,
      startedAt,
      errorCategory: safety.errorCategory,
      errorMessage: safety.message,
      viewport: scanOptions.viewport,
    });
  }

  const browser = await chromium.launch({ headless: true });
  const blockedRequests = [];
  const redirectChain = [];
  let navigationRequestCount = 0;

  try {
    const context = await browser.newContext({
      viewport: {
        width: scanOptions.viewport.width,
        height: scanOptions.viewport.height,
      },
      deviceScaleFactor: scanOptions.viewport.deviceScaleFactor,
      javaScriptEnabled: true,
      bypassCSP: false,
      storageState: { cookies: [], origins: [] },
    });

    await context.addInitScript(() => {
      document.addEventListener(
        "submit",
        (event) => {
          event.preventDefault();
          event.stopImmediatePropagation();
        },
        true,
      );

      HTMLFormElement.prototype.submit = function submitBlocked() {
        return undefined;
      };

      HTMLFormElement.prototype.requestSubmit = function requestSubmitBlocked() {
        return undefined;
      };
    });

    const safetyCache = new Map();
    await context.route("**/*", async (route, request) => {
      const method = request.method().toUpperCase();
      const requestUrl = request.url();

      if (!SAFE_METHODS.has(method)) {
        blockedRequests.push({
          url: redactUrl(requestUrl),
          method,
          reason: "blocked_unsafe_method",
        });
        await route.abort("blockedbyclient");
        return;
      }

      if (request.isNavigationRequest()) {
        navigationRequestCount += 1;
        if (navigationRequestCount > scanOptions.maxRedirects + 1) {
          blockedRequests.push({
            url: redactUrl(requestUrl),
            method,
            reason: "max_redirects_exceeded",
          });
          await route.abort("blockedbyclient");
          return;
        }
      }

      const requestSafety = await cachedValidateUrl(requestUrl, safetyCache, scanOptions);
      if (!requestSafety.ok) {
        blockedRequests.push({
          url: requestSafety.redactedUrl || redactUrl(requestUrl),
          method,
          reason: requestSafety.errorCategory,
        });
        await route.abort("blockedbyclient");
        return;
      }

      await route.continue({ headers: stripSensitiveHeaders(request.headers()) });
    });

    const page = await context.newPage();
    page.on("response", (response) => {
      if (response.request().isNavigationRequest()) {
        redirectChain.push({
          url: redactUrl(response.url()),
          status: response.status(),
        });
      }
    });

    const response = await page.goto(safety.url, {
      waitUntil: "domcontentloaded",
      timeout: scanOptions.navigationTimeoutMs,
    });

    if (!response) {
      throw new ScannerError("navigation_failed", "ページ読み込みのHTTPレスポンスを取得できませんでした。");
    }

    await page.waitForLoadState("networkidle", { timeout: scanOptions.idleTimeoutMs }).catch(() => undefined);

    const screenshotArtifact = await captureScreenshotMetadata(page, scanOptions.viewport);
    const domSummary = await extractDomSummary(page);
    const tabOrderSample = await collectTabOrderSample(page, scanOptions.maxTabSteps);
    const axeRaw = await new AxeBuilder({ page }).withTags(JIS_2016_AA_AXE_TAGS).analyze();
    const pageId = "page-1";
    const axe = normalizeAxeResults(axeRaw);
    const pageReport = {
      page_id: pageId,
      page_role: scanOptions.pageRole ?? DEFAULT_PAGE_ROLE,
      page_weight: Number.isFinite(scanOptions.pageWeight) ? scanOptions.pageWeight : DEFAULT_PAGE_WEIGHT,
      url: redactUrl(page.url()),
      http_status: response.status(),
      redirect_chain: redirectChain,
      title: domSummary.title,
      lang: domSummary.lang,
      viewport: scanOptions.viewport,
      headings: domSummary.headings,
      landmarks: domSummary.landmarks,
      controls: domSummary.controls,
      images: domSummary.images,
      collection_limits: domSummary.collection_limits,
      tab_order_sample: tabOrderSample,
      axe,
    };
    pageReport.screen_reader_preview = createScreenReaderPreview(pageReport);
    const findings = createFindingsFromAxe(pageId, axe.violations);
    const completedAt = new Date().toISOString();

    return {
      schema_version: "0.1.0",
      scan_run: {
        scan_run_id: scanRunId,
        requested_url: safety.redactedUrl,
        final_url: redactUrl(page.url()),
        profile_ids: DEFAULT_PROFILE_IDS,
        started_at: startedAt,
        completed_at: completedAt,
        status: "completed",
        error_category: null,
        standards_checked_at: STANDARDS_CHECKED_AT,
      },
      pages: [pageReport],
      findings,
      criteria_mappings: [],
      score_snapshot: calculateScoreSnapshot({
        findings,
        pages: [pageReport],
        profileIds: DEFAULT_PROFILE_IDS,
        scanStatus: "completed",
      }),
      artifacts: [
        screenshotArtifact,
        {
          artifact_id: "request-block-log",
          kind: "log",
          path: null,
          redacted: true,
          blocked_request_count: blockedRequests.length,
        },
      ],
    };
  } catch (error) {
    const safeError = normalizeScannerError(error);
    return createFailedReport({
      scanRunId,
      requestedUrl: safety.redactedUrl,
      startedAt,
      errorCategory: safeError.errorCategory,
      errorMessage: safeError.message,
      viewport: scanOptions.viewport,
      finalUrl: safety.redactedUrl,
      redirectChain,
    });
  } finally {
    await browser.close();
  }
}

async function captureScreenshotMetadata(page, viewport) {
  try {
    const screenshot = await page.screenshot({
      type: "png",
      fullPage: false,
      animations: "disabled",
    });
    return {
      artifact_id: "viewport-screenshot",
      kind: "screenshot",
      path: null,
      redacted: true,
      capture_status: "captured_not_saved",
      stored: false,
      width: viewport.width,
      height: viewport.height,
      byte_length: screenshot.byteLength,
      note: "CLI MVPでは秘密情報保存を避けるためスクリーンショット画像は保存しません。",
    };
  } catch (error) {
    return {
      artifact_id: "viewport-screenshot",
      kind: "screenshot",
      path: null,
      redacted: true,
      capture_status: "failed",
      stored: false,
      error_category: "screenshot_failed",
      message: redactText(error instanceof Error ? error.message : "screenshot failed", 160),
    };
  }
}

async function cachedValidateUrl(url, safetyCache, scanOptions) {
  const hostname = new URL(url).hostname;
  if (!safetyCache.has(hostname)) {
    safetyCache.set(
      hostname,
      validateUrlForScanning(url, {
        allowLocalFixture: scanOptions.allowLocalFixture === true,
      }),
    );
  }
  return safetyCache.get(hostname);
}

function stripSensitiveHeaders(headers) {
  return Object.fromEntries(Object.entries(headers).filter(([name]) => !BLOCKED_HEADER_NAMES.has(name.toLowerCase())));
}

async function extractDomSummary(page) {
  return page.evaluate(() => {
    const controlSelector = [
      "a[href]",
      "button",
      "input",
      "select",
      "textarea",
      "summary",
      "[role='button']",
      "[role='link']",
      "[role='checkbox']",
      "[role='radio']",
      "[role='switch']",
      "[role='combobox']",
      "[role='textbox']",
      "[role='searchbox']",
      "[role='slider']",
    ].join(",");

    const landmarkSelector = [
      "main",
      "nav",
      "header",
      "footer",
      "aside",
      "form",
      "section[aria-label]",
      "section[aria-labelledby]",
      "[role='main']",
      "[role='navigation']",
      "[role='banner']",
      "[role='contentinfo']",
      "[role='complementary']",
      "[role='search']",
      "[role='form']",
      "[role='region']",
    ].join(",");

    const normalize = (value, maxLength = 160) => {
      const compact = String(value ?? "")
        .replace(/[\r\n\t]+/g, " ")
        .replace(/\s{2,}/g, " ")
        .trim()
        .replace(/(token|secret|password|passwd|auth|authorization|api[-_]?key|session|cookie|jwt)=([^&\s]+)/gi, "$1=[redacted]");
      return compact.length > maxLength ? `${compact.slice(0, maxLength - 1)}...` : compact;
    };

    const selectorFor = (element) => {
      const parts = [];
      let current = element;
      while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.documentElement) {
        const tag = current.tagName.toLowerCase();
        const parent = current.parentElement;
        if (!parent) {
          parts.unshift(tag);
          break;
        }

        const siblings = [...parent.children].filter((child) => child.tagName === current.tagName);
        const index = siblings.indexOf(current) + 1;
        parts.unshift(siblings.length > 1 ? `${tag}:nth-of-type(${index})` : tag);

        if (parts.length >= 5) {
          break;
        }
        current = parent;
      }
      return parts.join(" > ");
    };

    const textOf = (element) => normalize(element?.textContent ?? "", 120);

    const labelledByText = (element) => {
      const ids = normalize(element.getAttribute("aria-labelledby") ?? "", 240)
        .split(/\s+/)
        .filter(Boolean);
      return ids.map((id) => textOf(document.getElementById(id))).join(" ").trim();
    };

    const explicitLabelText = (element) => {
      if (!element.id) {
        return "";
      }
      const label = document.querySelector(`label[for="${CSS.escape(element.id)}"]`);
      return textOf(label);
    };

    const implicitLabelText = (element) => textOf(element.closest("label"));

    const accessibleName = (element) => {
      const ariaLabel = normalize(element.getAttribute("aria-label") ?? "", 120);
      if (ariaLabel) {
        return ariaLabel;
      }

      const labelledBy = labelledByText(element);
      if (labelledBy) {
        return normalize(labelledBy, 120);
      }

      if (element instanceof HTMLImageElement) {
        return normalize(element.getAttribute("alt") ?? "", 120);
      }

      if (
        element instanceof HTMLInputElement ||
        element instanceof HTMLSelectElement ||
        element instanceof HTMLTextAreaElement
      ) {
        return (
          explicitLabelText(element) ||
          implicitLabelText(element) ||
          normalize(element.getAttribute("placeholder") ?? "", 120) ||
          normalize(element.getAttribute("title") ?? "", 120)
        );
      }

      return textOf(element) || normalize(element.getAttribute("title") ?? "", 120);
    };

    const roleOf = (element) => {
      const explicitRole = normalize(element.getAttribute("role") ?? "", 80);
      if (explicitRole) {
        return explicitRole;
      }

      const tag = element.tagName.toLowerCase();
      if (tag === "a") {
        return "link";
      }
      if (tag === "button" || tag === "summary") {
        return "button";
      }
      if (tag === "textarea") {
        return "textbox";
      }
      if (tag === "select") {
        return "combobox";
      }
      if (tag === "input") {
        const type = element.getAttribute("type") || "text";
        if (["button", "submit", "reset"].includes(type)) {
          return "button";
        }
        if (["checkbox", "radio", "range"].includes(type)) {
          return type === "range" ? "slider" : type;
        }
        return "textbox";
      }
      if (tag === "main") {
        return "main";
      }
      if (tag === "nav") {
        return "navigation";
      }
      if (tag === "header") {
        return "banner";
      }
      if (tag === "footer") {
        return "contentinfo";
      }
      if (tag === "aside") {
        return "complementary";
      }
      if (tag === "form") {
        return "form";
      }
      return tag;
    };

    const allHeadings = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")];
    const allLandmarks = [...document.querySelectorAll(landmarkSelector)];
    const allControls = [...document.querySelectorAll(controlSelector)];
    const allImages = [...document.querySelectorAll("img")];

    const headings = allHeadings.slice(0, 80).map((heading) => ({
      level: Number(heading.tagName.slice(1)),
      text: textOf(heading),
      selector: selectorFor(heading),
    }));

    const landmarks = allLandmarks.slice(0, 80).map((landmark) => ({
      role: roleOf(landmark),
      label: accessibleName(landmark),
      selector: selectorFor(landmark),
    }));

    const controls = allControls.slice(0, 160).map((control) => ({
      role: roleOf(control),
      name: accessibleName(control),
      selector: selectorFor(control),
      disabled: Boolean(control.disabled || control.getAttribute("aria-disabled") === "true"),
      required: Boolean(control.required || control.getAttribute("aria-required") === "true"),
      type: normalize(control.getAttribute("type") ?? control.tagName.toLowerCase(), 40),
    }));

    const images = allImages.slice(0, 160).map((image) => {
      const hasAlt = image.hasAttribute("alt");
      const alt = image.getAttribute("alt");
      return {
        selector: selectorFor(image),
        alt_state: hasAlt ? (alt === "" ? "empty" : "present") : "missing",
        alt: hasAlt ? normalize(alt, 120) : null,
      };
    });

    return {
      title: normalize(document.title, 160) || null,
      lang: normalize(document.documentElement.getAttribute("lang") ?? "", 40) || null,
      headings,
      landmarks,
      controls,
      images,
      collection_limits: {
        max: {
          headings: 80,
          landmarks: 80,
          controls: 160,
          images: 160,
        },
        actual_counts: {
          headings: allHeadings.length,
          landmarks: allLandmarks.length,
          controls: allControls.length,
          images: allImages.length,
        },
        collected_counts: {
          headings: headings.length,
          landmarks: landmarks.length,
          controls: controls.length,
          images: images.length,
        },
        count_truncated: {
          headings: allHeadings.length > 80,
          landmarks: allLandmarks.length > 80,
          controls: allControls.length > 160,
          images: allImages.length > 160,
        },
      },
    };
  });
}

async function collectTabOrderSample(page, maxSteps) {
  const sample = [];

  for (let step = 1; step <= maxSteps; step += 1) {
    await page.keyboard.press("Tab");
    const entry = await page.evaluate((currentStep) => {
      const element = document.activeElement;
      if (!element || element === document.body || element === document.documentElement) {
        return null;
      }

      const normalize = (value, maxLength = 120) => {
        const compact = String(value ?? "")
          .replace(/[\r\n\t]+/g, " ")
          .replace(/\s{2,}/g, " ")
          .trim()
          .replace(/(token|secret|password|passwd|auth|authorization|api[-_]?key|session|cookie|jwt)=([^&\s]+)/gi, "$1=[redacted]");
        return compact.length > maxLength ? `${compact.slice(0, maxLength - 1)}...` : compact;
      };

      const selectorFor = (target) => {
        const parts = [];
        let current = target;
        while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.documentElement) {
          const tag = current.tagName.toLowerCase();
          const parent = current.parentElement;
          if (!parent) {
            parts.unshift(tag);
            break;
          }
          const siblings = [...parent.children].filter((child) => child.tagName === current.tagName);
          const index = siblings.indexOf(current) + 1;
          parts.unshift(siblings.length > 1 ? `${tag}:nth-of-type(${index})` : tag);
          if (parts.length >= 5) {
            break;
          }
          current = parent;
        }
        return parts.join(" > ");
      };

      const name =
        normalize(element.getAttribute("aria-label") ?? "") ||
        normalize(element.textContent ?? "") ||
        normalize(element.getAttribute("title") ?? "") ||
        normalize(element.getAttribute("placeholder") ?? "");

      return {
        step: currentStep,
        role: normalize(element.getAttribute("role") ?? element.tagName.toLowerCase(), 80),
        name,
        selector: selectorFor(element),
      };
    }, step);

    if (entry) {
      sample.push(entry);
    }
  }

  return sample;
}

export function normalizeAxeResults(axeRaw) {
  return {
    violations: axeRaw.violations.map((violation) => normalizeAxeIssue(violation)),
    incomplete: axeRaw.incomplete.map((issue) => normalizeAxeIssue(issue)),
  };
}

function normalizeAxeIssue(issue) {
  const rawNodes = issue.nodes ?? [];
  const nodes = rawNodes.slice(0, COLLECTION_LIMITS.axeNodesPerIssue);
  return {
    id: redactText(issue.id, 120),
    impact: issue.impact ?? "unknown",
    description: redactText(issue.description, 240),
    help: redactText(issue.help, 240),
    help_url: redactUrl(issue.helpUrl ?? ""),
    tags: issue.tags ?? [],
    node_count: rawNodes.length,
    nodes_truncated: rawNodes.length > COLLECTION_LIMITS.axeNodesPerIssue,
    nodes: nodes.map((node) => ({
      target: (node.target ?? []).map((target) => redactText(target, 200)),
      failure_summary: redactText(node.failureSummary ?? "", 360),
      checks: [...(node.any ?? []), ...(node.all ?? []), ...(node.none ?? [])].slice(0, COLLECTION_LIMITS.axeChecksPerNode).map((check) => ({
        id: redactText(check.id, 120),
        message: redactText(check.message, 240),
      })),
    })),
  };
}

function createFindingsFromAxe(pageId, violations) {
  let index = 0;
  return violations.flatMap((violation) =>
    violation.nodes.map((node) => {
      index += 1;
      const selector = node.target[0] ?? null;
      return {
        finding_id: `axe-${index}`,
        rule_id: violation.id,
        page_id: pageId,
        severity: axeImpactToSeverity(violation.impact),
        detection_type: "auto",
        review_status: "not_reviewed",
        selector,
        message: `axe-coreが「${violation.help}」を自動検出しました。`,
        user_impact: violation.description,
        remediation: node.failure_summary || "該当箇所のアクセシビリティ実装を確認してください。",
        dedupe_key: `${violation.id}:${selector ?? "page"}`,
        component_clue: inferComponentClue(selector),
        accessible_name_context: inferAccessibleNameContext(violation.id),
        source: "axe-core",
      };
    }),
  );
}

function axeImpactToSeverity(impact) {
  if (impact === "critical" || impact === "serious" || impact === "moderate" || impact === "minor") {
    return impact;
  }
  return "moderate";
}

function createScreenReaderPreview(page) {
  const outline = page.headings.map((heading) => ({
    type: "heading",
    level: heading.level,
    text: heading.text || "テキストなし",
    selector: heading.selector,
  }));
  const landmarks = page.landmarks.map((landmark) => ({
    type: "landmark",
    role: landmark.role,
    name: landmark.label || "名前なし",
    selector: landmark.selector,
  }));
  const controls = page.controls.map((control) => ({
    type: "control",
    role: control.role,
    name: control.name || "名前なし",
    selector: control.selector,
    state: control.disabled ? "disabled" : control.required ? "required" : "default",
  }));
  const forms = page.controls
    .filter((control) => ["textbox", "combobox", "checkbox", "radio", "switch", "slider"].includes(control.role))
    .map((control) => ({
      role: control.role,
      name: control.name || "ラベルなし",
      selector: control.selector,
      required: Boolean(control.required),
    }));
  const missingAccessibleNames = page.controls
    .filter((control) => !control.name)
    .map((control) => ({
      role: control.role,
      selector: control.selector,
      reason: "アクセシブルネームが空です。",
    }));
  const possibleReadingRisks = [
    ...page.images
      .filter((image) => image.alt_state === "missing")
      .map((image) => ({
        type: "image-alt",
        selector: image.selector,
        message: "画像のalt属性がないため、意味のある画像か手動確認が必要です。",
      })),
    ...page.headings
      .filter((heading, index, headings) => index > 0 && heading.level - headings[index - 1].level > 1)
      .map((heading) => ({
        type: "heading-skip",
        selector: heading.selector,
        message: `見出しが h${heading.level} へ飛んでいます。構造が意図通りか確認してください。`,
      })),
  ];

  return {
    outline,
    landmarks,
    controls,
    forms,
    alerts_and_live_regions: [],
    missing_accessible_names: missingAccessibleNames,
    possible_reading_risks: possibleReadingRisks,
  };
}

function emptyScreenReaderPreview() {
  return {
    outline: [],
    landmarks: [],
    controls: [],
    forms: [],
    alerts_and_live_regions: [],
    missing_accessible_names: [],
    possible_reading_risks: [],
  };
}

function emptyCollectionLimits() {
  return {
    max: {
      headings: COLLECTION_LIMITS.headings,
      landmarks: COLLECTION_LIMITS.landmarks,
      controls: COLLECTION_LIMITS.controls,
      images: COLLECTION_LIMITS.images,
    },
    actual_counts: { headings: 0, landmarks: 0, controls: 0, images: 0 },
    collected_counts: { headings: 0, landmarks: 0, controls: 0, images: 0 },
    count_truncated: { headings: false, landmarks: false, controls: false, images: false },
  };
}

function inferComponentClue(selector) {
  const value = String(selector || "");
  if (/header|banner|masthead/i.test(value)) return "header";
  if (/footer|contentinfo/i.test(value)) return "footer";
  if (/nav|menu|gnav|breadcrumb/i.test(value)) return "nav";
  if (/search/i.test(value)) return "search";
  if (/form|input|select|textarea|fieldset/i.test(value)) return "form";
  if (/card|item|tile|article|product/i.test(value)) return "card";
  if (/list|li|ul|ol/i.test(value)) return "list-item";
  if (/carousel|slider|swiper/i.test(value)) return "carousel";
  if (/modal|dialog|drawer/i.test(value)) return "modal";
  if (/main/i.test(value)) return "main";
  return "page";
}

function inferAccessibleNameContext(ruleId) {
  const normalized = String(ruleId || "").toLowerCase();
  if (normalized.includes("name") || normalized === "label") {
    return "missing-name";
  }
  return "not-name-related";
}

function createFailedReport({ scanRunId, requestedUrl, startedAt, errorCategory, errorMessage, viewport, finalUrl = null, redirectChain = [] }) {
  const completedAt = new Date().toISOString();
  return {
    schema_version: "0.1.0",
    scan_run: {
      scan_run_id: scanRunId,
      requested_url: requestedUrl,
      final_url: finalUrl,
      profile_ids: DEFAULT_PROFILE_IDS,
      started_at: startedAt,
      completed_at: completedAt,
      status: "failed",
      error_category: errorCategory,
      error_message: redactText(errorMessage, 240),
      standards_checked_at: STANDARDS_CHECKED_AT,
    },
    pages: [
      {
        page_id: "page-1",
        page_role: DEFAULT_PAGE_ROLE,
        page_weight: DEFAULT_PAGE_WEIGHT,
        url: finalUrl,
        http_status: null,
        redirect_chain: redirectChain,
        title: null,
        lang: null,
        viewport,
        headings: [],
        landmarks: [],
        controls: [],
        images: [],
        collection_limits: emptyCollectionLimits(),
        tab_order_sample: [],
        axe: {
          violations: [],
          incomplete: [],
        },
        screen_reader_preview: emptyScreenReaderPreview(),
      },
    ],
    findings: [],
    criteria_mappings: [],
    score_snapshot: calculateScoreSnapshot({
      findings: [],
      pages: [],
      profileIds: DEFAULT_PROFILE_IDS,
      scanStatus: "failed",
    }),
    artifacts: [],
  };
}

function normalizeScannerError(error) {
  if (error instanceof ScannerError) {
    return {
      errorCategory: error.category,
      message: error.message,
    };
  }

  return {
    errorCategory: "scanner_error",
    message: error instanceof Error ? error.message : "スキャン中に不明なエラーが発生しました。",
  };
}

class ScannerError extends Error {
  constructor(category, message) {
    super(message);
    this.category = category;
  }
}
