const SCORE_MAX = 100;
const SCORING_MODEL = "seo_accessibility_ux_v1";
const SCORE_LABEL = "アクセシビリティUXスコア";
const TARGET_STANDARD = "JIS X 8341-3:2016 A/AA と WCAG 2.0 A/AA を根拠辞書として参照";
const CLAIM_LEVEL = "quality_signal";

const PAGE_ROLE_WEIGHTS = {
  top: 0.35,
  listing: 0.25,
  detail: 0.2,
  action: 0.2,
  single: 1,
  other: 0.05,
};

const SEVERITY_WEIGHTS = {
  critical: 22,
  serious: 10,
  moderate: 3,
  minor: 1,
};

const RULE_WEIGHT_OVERRIDES = {
  "button-name": 12,
  "link-name": 7,
  label: 16,
  "color-contrast": 8,
  "image-alt": 6,
  "aria-allowed-attr": 8,
  "aria-required-attr": 8,
  "aria-valid-attr": 8,
  "aria-valid-attr-value": 8,
  "aria-roles": 8,
  "meta-viewport": 10,
  "list": 2.5,
  "definition-list": 2.5,
  "dlitem": 2.5,
  region: 2.5,
  "landmark-one-main": 4,
  "landmark-unique": 4,
  "heading-order": 3,
  "page-has-heading-one": 3,
};

const EVIDENCE_CAPS = {
  standard: 100,
  limited: 75,
  insufficient: 60,
};

const BLOCKER_CAPS = {
  critical: 59,
  repeatedSerious: 79,
};

export function calculateScoreSnapshot({ findings, pages, profileIds, scanStatus }) {
  const normalizedPages = normalizePages(pages);
  const scannedPageCount = normalizedPages.length;
  const sampleConfidence = sampleConfidenceFor(scannedPageCount);
  const evidence = calculateEvidence(normalizedPages);

  if (scanStatus !== "completed") {
    return {
      scoring_status: "not_available",
      scoring_model: SCORING_MODEL,
      score_label: SCORE_LABEL,
      target_standard: TARGET_STANDARD,
      claim_level: CLAIM_LEVEL,
      score: null,
      max_score: SCORE_MAX,
      auto_score: null,
      raw_score: null,
      total_penalty: 0,
      risk_penalty: 0,
      cap_penalty: 0,
      score_cap: SCORE_MAX,
      score_cap_reason: null,
      evidence_level: evidence.level,
      evidence_score: evidence.score,
      sample_confidence: sampleConfidence,
      testable_unit_count: evidence.total,
      testable_unit_counts: evidence.counts,
      grouped_issue_count: 0,
      automated_grouped_issue_count: 0,
      manual_review_pending_count: 0,
      manual_risk_count: 0,
      not_scored_risks: [],
      high_risk_manual_review_pending_count: 0,
      critical_issue_count: 0,
      serious_issue_count: 0,
      affected_page_count: 0,
      scanned_page_count: scannedPageCount,
      page_role_weights: pageRoleWeights(normalizedPages),
      selected_profiles: profileIds,
      severity_counts: emptySeverityCounts(),
      weights: scoreWeights(),
      scored_groups: [],
      note: scoreNote(),
    };
  }

  const groupedFindings = groupFindings(findings);
  const notScoredRisks = Array.from(groupIncompleteIssues(normalizedPages).values()).map(toNotScoredRisk);
  const severityCounts = emptySeverityCounts();
  const affectedPages = new Set();
  const scoredGroups = [];

  const pagePenalties = new Map(normalizedPages.map((page) => [page.page_id, 0]));
  for (const group of groupedFindings.values()) {
    const scoredGroup = scoreAutomatedGroup(group, normalizedPages, scannedPageCount);
    severityCounts[scoredGroup.severity] += 1;
    distributeGroupPenaltyToPages(scoredGroup, group.pageIds, normalizedPages, pagePenalties);
    scoredGroups.push(scoredGroup);
    for (const pageId of group.pageIds) {
      affectedPages.add(pageId);
    }
  }

  const pageWeightedPenalty = calculatePageWeightedPenalty(normalizedPages, pagePenalties);
  const riskPenalty = roundPenalty(pageWeightedPenalty);
  const rawScore = roundPenalty(clampScore(SCORE_MAX - riskPenalty));
  const cap = determineScoreCap({ evidence, severityCounts, sampleConfidence });
  const score = Math.round(clampScore(Math.min(rawScore, cap.value)));
  const totalPenalty = roundPenalty(SCORE_MAX - score);
  const capPenalty = roundPenalty(Math.max(0, totalPenalty - riskPenalty));
  const manualRiskCount = notScoredRisks.length;

  return {
    scoring_status: "calculated",
    scoring_model: SCORING_MODEL,
    score_label: SCORE_LABEL,
    target_standard: TARGET_STANDARD,
    claim_level: CLAIM_LEVEL,
    score,
    max_score: SCORE_MAX,
    auto_score: score,
    raw_score: rawScore,
    total_penalty: totalPenalty,
    risk_penalty: riskPenalty,
    cap_penalty: capPenalty,
    score_cap: cap.value,
    score_cap_reason: cap.reason,
    evidence_level: evidence.level,
    evidence_score: evidence.score,
    sample_confidence: sampleConfidence,
    testable_unit_count: evidence.total,
    testable_unit_counts: evidence.counts,
    grouped_issue_count: groupedFindings.size,
    automated_grouped_issue_count: groupedFindings.size,
    manual_review_pending_count: manualRiskCount,
    manual_risk_count: manualRiskCount,
    not_scored_risks: notScoredRisks,
    high_risk_manual_review_pending_count: 0,
    critical_issue_count: severityCounts.critical,
    serious_issue_count: severityCounts.serious,
    affected_page_count: affectedPages.size,
    scanned_page_count: scannedPageCount,
    page_role_weights: pageRoleWeights(normalizedPages),
    selected_profiles: profileIds,
    severity_counts: severityCounts,
    weights: scoreWeights(),
    scored_groups: scoredGroups.sort((a, b) => b.penalty - a.penalty),
    page_scores: normalizedPages.map((page) => ({
      page_id: page.page_id,
      page_role: page.page_role,
      page_weight: page.page_weight,
      risk_penalty: roundPenalty(pagePenalties.get(page.page_id) ?? 0),
      score: Math.round(clampScore(SCORE_MAX - (pagePenalties.get(page.page_id) ?? 0))),
    })),
    note: scoreNote(),
  };
}

function normalizePages(pages) {
  const useStandardRoles = pages.length >= 4;
  const withRoles = pages.map((page, index) => {
    const pageRole = page.page_role ?? (useStandardRoles ? ["top", "listing", "detail", "action"][index] ?? "other" : "single");
    const pageWeight = Number.isFinite(page.page_weight) ? page.page_weight : PAGE_ROLE_WEIGHTS[pageRole] ?? PAGE_ROLE_WEIGHTS.other;
    return {
      ...page,
      page_role: pageRole,
      page_weight: pageWeight,
    };
  });

  const totalWeight = withRoles.reduce((total, page) => total + Math.max(page.page_weight, 0), 0) || 1;
  return withRoles.map((page) => ({
    ...page,
    page_weight: roundMetric(Math.max(page.page_weight, 0) / totalWeight),
  }));
}

function groupFindings(findings) {
  const groups = new Map();
  for (const finding of findings) {
    if (finding.review_status === "reviewed_pass" || finding.review_status === "not_applicable") {
      continue;
    }

    const ruleId = finding.rule_id || "unknown";
    const groupKey = automatedGroupKey(finding);
    const severity = adjustedSeverity(finding);
    const pageId = finding.page_id || "page";
    const current = groups.get(groupKey);

    if (!current) {
      groups.set(groupKey, {
        groupKey,
        ruleId,
        severity,
        componentClue: componentClueFor(finding),
        accessibleNameContext: accessibleNameContextFor(finding),
        selectors: new Set([finding.selector || "page"]),
        pageIds: new Set([pageId]),
        instanceCount: 1,
      });
      continue;
    }

    current.instanceCount += 1;
    current.selectors.add(finding.selector || "page");
    current.pageIds.add(pageId);
    if (severityRank(severity) > severityRank(current.severity)) {
      current.severity = severity;
    }
  }
  return groups;
}

function adjustedSeverity(finding) {
  const ruleId = String(finding.rule_id || "").toLowerCase();
  const selector = String(finding.selector || "");
  const base = normalizeSeverity(finding.severity);

  if (ruleId === "meta-viewport" && isZoomBlockingFinding(finding)) {
    return "serious";
  }

  if (isTaskBlockingRule(ruleId) && isPrimaryTaskContext(finding, selector)) {
    return "critical";
  }

  if (isHeavyUxRule(ruleId)) {
    if (base === "critical") {
      return "serious";
    }
    return severityRank(base) >= severityRank("serious") ? base : "serious";
  }

  if (isStructuralRule(ruleId)) {
    return severityRank(base) > severityRank("moderate") ? "moderate" : base;
  }

  return base === "critical" ? "serious" : base;
}

function isTaskBlockingRule(ruleId) {
  return ruleId === "button-name" || ruleId === "label" || ruleId.includes("control-name");
}

function isPrimaryTaskContext(finding, selector) {
  const context = [
    selector,
    finding.message,
    finding.user_impact,
    finding.remediation,
    finding.dedupe_key,
    finding.component_clue,
    finding.accessible_name_context,
  ]
    .filter(Boolean)
    .join(" ");
  return /(form|submit|search|login|reserve|reservation|booking|contact|cart|checkout|apply|required|primary action|purchase|order|entry)/i.test(
    context,
  );
}

function isZoomBlockingFinding(finding) {
  const context = [finding.rule_id, finding.selector, finding.message, finding.user_impact, finding.remediation]
    .filter(Boolean)
    .join(" ");
  return /meta-viewport|viewport|user-scalable|maximum-scale|zoom/i.test(context);
}

function isHeavyUxRule(ruleId) {
  return (
    ruleId === "button-name" ||
    ruleId === "link-name" ||
    ruleId === "label" ||
    ruleId === "color-contrast" ||
    ruleId === "image-alt" ||
    ruleId === "meta-viewport" ||
    ruleId.startsWith("aria-")
  );
}

function isStructuralRule(ruleId) {
  return (
    ruleId === "list" ||
    ruleId === "definition-list" ||
    ruleId === "dlitem" ||
    ruleId === "region" ||
    ruleId.startsWith("landmark") ||
    ruleId.includes("heading")
  );
}

function groupIncompleteIssues(pages) {
  const groups = new Map();
  for (const page of pages) {
    for (const issue of page.axe?.incomplete ?? []) {
      for (const node of issue.nodes.length > 0 ? issue.nodes : [{ target: ["page"] }]) {
        const target = node.target?.[0] ?? "page";
        const ruleId = issue.id || "unknown";
        const groupKey = `risk:${ruleId}:${normalizeSelectorPattern(target)}`;
        const impact = normalizeSeverity(issue.impact);
        const current = groups.get(groupKey);

        if (!current) {
          groups.set(groupKey, {
            group_key: groupKey,
            rule_id: ruleId,
            source: "axe-incomplete",
            risk_label: "自動判定外リスク",
            severity: impact,
            pageIds: new Set([page.page_id]),
            instance_count: 1,
          });
          continue;
        }

        current.instance_count += 1;
        current.pageIds.add(page.page_id);
        if (severityRank(impact) > severityRank(current.severity)) {
          current.severity = impact;
        }
      }
    }
  }
  return groups;
}

function toNotScoredRisk(group) {
  return {
    group_key: group.group_key,
    rule_id: group.rule_id,
    source: group.source,
    risk_label: group.risk_label,
    severity: group.severity,
    instance_count: group.instance_count,
    affected_page_count: group.pageIds.size,
    scored: false,
    reason: "axe incomplete は自動検出で明確な失敗とは扱わず、点数とは別に確認します。",
  };
}

function scoreAutomatedGroup(group, pages, scannedPageCount) {
  const relevantUnits = relevantUnitCount(group.ruleId, pages);
  const denominator = Math.max(relevantUnits, group.instanceCount, 1);
  const failureRate = clampUnit(group.instanceCount / denominator);
  const recurrence = recurrenceFactor(group.instanceCount);
  const density = densityFactor(failureRate);
  const scope = affectedPageFactor(group.pageIds.size, scannedPageCount);
  const pageWeight = pageWeightFactor(group.pageIds, pages);
  const ruleWeight = ruleWeightFor(group.ruleId, group.severity);
  const countTruncated = countMayBeTruncated(group.ruleId, pages);
  const penalty = roundPenalty(ruleWeight * recurrence * density * scope);

  return {
    group_key: group.groupKey,
    rule_id: group.ruleId,
    source: "automated",
    severity: group.severity,
    instance_count: group.instanceCount,
    affected_page_count: group.pageIds.size,
    relevant_unit_count: relevantUnits,
    failure_rate: roundMetric(failureRate),
    recurrence_factor: roundMetric(recurrence),
    density_factor: roundMetric(density),
    affected_page_factor: roundMetric(scope),
    page_weight_factor: roundMetric(pageWeight),
    component_clue: group.componentClue,
    accessible_name_context: group.accessibleNameContext,
    blocker_type: null,
    count_truncated: countTruncated,
    failure_rate_confidence: countTruncated ? "capped_collection" : "normal",
    penalty,
  };
}

function ruleWeightFor(ruleId, severity) {
  const normalizedRuleId = String(ruleId || "").toLowerCase();
  return RULE_WEIGHT_OVERRIDES[normalizedRuleId] ?? SEVERITY_WEIGHTS[severity] ?? SEVERITY_WEIGHTS.moderate;
}

function pageWeightFactor(pageIds, pages) {
  if (pages.length <= 1) {
    return 1;
  }

  const affectedWeight = pages
    .filter((page) => pageIds.has(page.page_id))
    .reduce((total, page) => total + page.page_weight, 0);

  return Math.max(0.05, affectedWeight);
}

function automatedGroupKey(finding) {
  const ruleId = finding.rule_id || "unknown";
  const groupSource = finding.dedupe_key ? selectorFromDedupeKey(finding.dedupe_key) : finding.selector || "page";
  const component = componentClueFor(finding);
  const nameContext = accessibleNameContextFor(finding);
  return `auto:${ruleId}:${component}:${normalizeSelectorPattern(groupSource)}:${nameContext}`;
}

function selectorFromDedupeKey(dedupeKey) {
  if (!dedupeKey || typeof dedupeKey !== "string") {
    return "";
  }
  const separatorIndex = dedupeKey.indexOf(":");
  return separatorIndex >= 0 ? dedupeKey.slice(separatorIndex + 1) : dedupeKey;
}

function normalizeSelectorPattern(selector) {
  return String(selector || "page")
    .toLowerCase()
    .replace(/:nth-of-type\(\d+\)/g, ":nth-of-type(*)")
    .replace(/:nth-child\(\d+\)/g, ":nth-child(*)")
    .replace(/([.#][a-z_-]+)\d+/gi, "$1*")
    .replace(/\[[^\]=]+=(["'])?[^"'\]]+\1\]/g, "[attr]")
    .replace(/\s+/g, " ")
    .trim();
}

function relevantUnitCount(ruleId, pages) {
  const normalizedRuleId = String(ruleId || "").toLowerCase();
  const counts = calculateEvidence(pages).counts;
  const controls = pages.flatMap((page) => page.controls ?? []);

  if (normalizedRuleId.includes("image") || normalizedRuleId.includes("alt")) {
    return counts.images;
  }

  if (normalizedRuleId.includes("link")) {
    return controls.filter((control) => control.role === "link" || control.type === "a").length;
  }

  if (normalizedRuleId.includes("button")) {
    return controls.filter((control) => control.role === "button" || control.type === "button").length;
  }

  if (
    normalizedRuleId.includes("label") ||
    normalizedRuleId.includes("input") ||
    normalizedRuleId.includes("select") ||
    normalizedRuleId.includes("form")
  ) {
    return controls.filter((control) =>
      ["textbox", "combobox", "checkbox", "radio", "switch", "slider", "button"].includes(control.role),
    ).length;
  }

  if (normalizedRuleId.includes("heading")) {
    return counts.headings;
  }

  if (normalizedRuleId.includes("landmark") || normalizedRuleId === "region") {
    return counts.landmarks + counts.pages;
  }

  if (
    normalizedRuleId.includes("title") ||
    normalizedRuleId.includes("lang") ||
    normalizedRuleId.includes("viewport")
  ) {
    return counts.pages;
  }

  if (normalizedRuleId.includes("contrast")) {
    return counts.headings + counts.controls + counts.landmarks + counts.pages;
  }

  if (normalizedRuleId.includes("aria")) {
    return counts.controls + counts.landmarks + counts.pages;
  }

  return Math.max(counts.testable_content_units, counts.total);
}

function countMayBeTruncated(ruleId, pages) {
  const normalizedRuleId = String(ruleId || "").toLowerCase();
  const keys =
    normalizedRuleId.includes("image") || normalizedRuleId.includes("alt")
      ? ["images"]
      : normalizedRuleId.includes("link") || normalizedRuleId.includes("button") || normalizedRuleId.includes("label")
        ? ["controls"]
        : normalizedRuleId.includes("heading")
          ? ["headings"]
          : normalizedRuleId.includes("landmark") || normalizedRuleId === "region"
            ? ["landmarks"]
            : [];

  return pages.some((page) => keys.some((key) => page.collection_limits?.count_truncated?.[key] === true));
}

function distributeGroupPenaltyToPages(scoredGroup, pageIds, pages, pagePenalties) {
  const affectedPages = pages.filter((page) => pageIds.has(page.page_id));

  for (const page of affectedPages) {
    pagePenalties.set(page.page_id, (pagePenalties.get(page.page_id) ?? 0) + scoredGroup.penalty);
  }
}

function calculatePageWeightedPenalty(pages, pagePenalties) {
  return pages.reduce((total, page) => {
    const pagePenalty = Math.min(SCORE_MAX, pagePenalties.get(page.page_id) ?? 0);
    return total + pagePenalty * page.page_weight;
  }, 0);
}

function componentClueFor(finding) {
  if (finding.component_clue) {
    return normalizeContextToken(finding.component_clue);
  }

  const selector = String(finding.selector || finding.dedupe_key || "");
  if (/header|banner|masthead/i.test(selector)) return "header";
  if (/footer|contentinfo/i.test(selector)) return "footer";
  if (/nav|menu|gnav|breadcrumb/i.test(selector)) return "nav";
  if (/search/i.test(selector)) return "search";
  if (/form|input|select|textarea|fieldset/i.test(selector)) return "form";
  if (/card|item|tile|article|product/i.test(selector)) return "card";
  if (/list|li|ul|ol/i.test(selector)) return "list-item";
  if (/carousel|slider|swiper/i.test(selector)) return "carousel";
  if (/modal|dialog|drawer/i.test(selector)) return "modal";
  if (/main/i.test(selector)) return "main";
  return "page";
}

function accessibleNameContextFor(finding) {
  if (finding.accessible_name_context) {
    return normalizeContextToken(finding.accessible_name_context);
  }

  const ruleId = String(finding.rule_id || "").toLowerCase();
  if (ruleId.includes("name") || ruleId === "label") {
    return "missing-name";
  }
  return "not-name-related";
}

function normalizeContextToken(value) {
  return String(value || "unknown")
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
}

function calculateEvidence(pages) {
  const counts = {
    pages: pages.length,
    titles: pages.filter((page) => page.title).length,
    languages: pages.filter((page) => page.lang).length,
    headings: sumBy(pages, (page) => page.headings?.length ?? 0),
    landmarks: sumBy(pages, (page) => page.landmarks?.length ?? 0),
    controls: sumBy(pages, (page) => page.controls?.length ?? 0),
    images: sumBy(pages, (page) => page.images?.length ?? 0),
    tab_order_entries: sumBy(pages, (page) => page.tab_order_sample?.length ?? 0),
    axe_issue_nodes: sumBy(pages, (page) =>
      [...(page.axe?.violations ?? [])].reduce((total, issue) => total + Math.max(issue.nodes?.length ?? 0, 1), 0),
    ),
    axe_incomplete_nodes: sumBy(pages, (page) =>
      [...(page.axe?.incomplete ?? [])].reduce((total, issue) => total + Math.max(issue.nodes?.length ?? 0, 1), 0),
    ),
  };
  counts.testable_content_units =
    counts.headings + counts.landmarks + counts.controls + counts.images + counts.tab_order_entries;
  counts.total =
    counts.pages +
    counts.titles +
    counts.languages +
    counts.testable_content_units +
    counts.axe_issue_nodes +
    counts.axe_incomplete_nodes;

  if (counts.testable_content_units < 2) {
    return { level: "insufficient", score: 40, total: counts.total, counts };
  }

  if (counts.total < 8 || counts.testable_content_units < 5) {
    return { level: "limited", score: 70, total: counts.total, counts };
  }

  return { level: "standard", score: 100, total: counts.total, counts };
}

function determineScoreCap({ evidence, severityCounts, sampleConfidence }) {
  const candidates = [];
  const evidenceCap = EVIDENCE_CAPS[evidence.level];
  if (evidenceCap < SCORE_MAX) {
    candidates.push({
      value: evidenceCap,
      reason:
        evidence.level === "insufficient"
          ? "評価対象が少ないため、品質スコアの上限を60点にしました。"
          : "評価対象が限られるため、品質スコアの上限を75点にしました。",
    });
  }

  if (severityCounts.critical > 0) {
    candidates.push({
      value: BLOCKER_CAPS.critical,
      reason: "問い合わせ、申込、検索などの主要操作を妨げ得る自動検出があるため、上限を59点にしました。",
    });
  } else if (severityCounts.serious >= 5) {
    candidates.push({
      value: BLOCKER_CAPS.repeatedSerious,
      reason: "Seriousの自動検出が複数あるため、上限を79点にしました。",
    });
  }

  if (sampleConfidence === "low") {
    const scannedPages = evidence.counts.pages;
    const capValue = scannedPages === 1 ? 90 : 95;
    candidates.push({
      value: capValue,
      reason:
        scannedPages === 1
          ? "1ページのみの評価でサンプル信頼度がlowのため、品質スコアの上限を90点にしました。"
          : "2-3ページの評価でサンプル信頼度がlowのため、品質スコアの上限を95点にしました。",
    });
  }

  if (candidates.length === 0) {
    return { value: SCORE_MAX, reason: null };
  }

  const limiting = candidates.reduce((lowest, candidate) => (candidate.value < lowest.value ? candidate : lowest));
  return {
    value: limiting.value,
    reason: limiting.reason,
  };
}

function recurrenceFactor(instanceCount) {
  return 1 + Math.min(Math.log2(Math.max(instanceCount, 1)), 4) * 0.22;
}

function densityFactor(failureRate) {
  return 0.65 + clampUnit(failureRate) * 0.55;
}

function affectedPageFactor(affectedPageCount, scannedPageCount) {
  if (scannedPageCount <= 1) {
    return 1;
  }
  return 1 + Math.sqrt(affectedPageCount / scannedPageCount) * 0.2;
}

function sampleConfidenceFor(scannedPageCount) {
  if (scannedPageCount >= 10) {
    return "high";
  }
  if (scannedPageCount >= 4) {
    return "standard";
  }
  return "low";
}

function pageRoleWeights(pages) {
  return pages.map((page) => ({
    page_id: page.page_id,
    page_role: page.page_role,
    page_weight: page.page_weight,
  }));
}

function normalizeSeverity(severity) {
  if (severity === "critical" || severity === "serious" || severity === "moderate" || severity === "minor") {
    return severity;
  }
  return "moderate";
}

function severityRank(severity) {
  const ranks = {
    minor: 1,
    moderate: 2,
    serious: 3,
    critical: 4,
  };
  return ranks[severity] ?? 2;
}

function emptySeverityCounts() {
  return {
    critical: 0,
    serious: 0,
    moderate: 0,
    minor: 0,
  };
}

function scoreWeights() {
  return {
    ...SEVERITY_WEIGHTS,
    rule_overrides: RULE_WEIGHT_OVERRIDES,
    page_role_weights: PAGE_ROLE_WEIGHTS,
    recurrence_log_base: 2,
    recurrence_step: 0.22,
    max_recurrence_steps: 4,
    density_min: 0.65,
    density_max: 1.2,
    limited_evidence_score_cap: EVIDENCE_CAPS.limited,
    insufficient_evidence_score_cap: EVIDENCE_CAPS.insufficient,
    low_sample_confidence_score_cap: { one_page: 90, two_or_three_pages: 95 },
    critical_blocker_score_cap: BLOCKER_CAPS.critical,
    repeated_serious_score_cap: BLOCKER_CAPS.repeatedSerious,
  };
}

function sumBy(values, callback) {
  return values.reduce((total, value) => total + callback(value), 0);
}

function roundPenalty(value) {
  return Math.round(value * 100) / 100;
}

function roundMetric(value) {
  return Math.round(value * 1000) / 1000;
}

function clampUnit(value) {
  return Math.max(0, Math.min(1, value));
}

function clampScore(value) {
  return Math.max(0, Math.min(SCORE_MAX, value));
}

function scoreNote() {
  return "アクセシビリティUXスコアはSEO/UX前提の品質指標です。JIS X 8341-3:2016 A/AAとWCAG 2.0 A/AAは自動検出ルールの根拠辞書として参照し、正式な適合判定ではありません。axe incomplete は自動判定外リスクとして別枠表示し、点数には混ぜません。";
}

export function compareScoreSnapshots(beforeReport, afterReport) {
  const beforeScore = beforeReport?.score_snapshot?.score ?? null;
  const afterScore = afterReport?.score_snapshot?.score ?? null;
  const beforeGroups = new Map((beforeReport?.score_snapshot?.scored_groups ?? []).map((group) => [group.group_key, group]));
  const afterGroups = new Map((afterReport?.score_snapshot?.scored_groups ?? []).map((group) => [group.group_key, group]));
  const allKeys = new Set([...beforeGroups.keys(), ...afterGroups.keys()]);
  const issueDeltas = Array.from(allKeys).map((key) => {
    const before = beforeGroups.get(key);
    const after = afterGroups.get(key);
    return {
      group_key: key,
      rule_id: after?.rule_id ?? before?.rule_id ?? "unknown",
      before_penalty: before?.penalty ?? 0,
      after_penalty: after?.penalty ?? 0,
      penalty_delta: roundPenalty((after?.penalty ?? 0) - (before?.penalty ?? 0)),
      status: !before && after ? "new" : before && !after ? "resolved" : "changed",
    };
  });

  const scoreDelta =
    typeof beforeScore === "number" && typeof afterScore === "number" ? Math.round((afterScore - beforeScore) * 100) / 100 : null;

  return {
    comparison_model: "before_after_score_delta_v1",
    stable_keys: ["group_key", "rule_id", "page_role", "component_clue", "accessible_name_context"],
    before_score: beforeScore,
    after_score: afterScore,
    score_delta: scoreDelta,
    improved: typeof scoreDelta === "number" ? scoreDelta > 0 : null,
    resolved_group_count: issueDeltas.filter((delta) => delta.status === "resolved").length,
    new_group_count: issueDeltas.filter((delta) => delta.status === "new").length,
    issue_deltas: issueDeltas.sort((a, b) => Math.abs(b.penalty_delta) - Math.abs(a.penalty_delta)),
    note: "before/after比較は同じURL、テンプレート、または同等ページロールの安定キーで差分を見るための改善指標です。正式な適合判定ではありません。",
  };
}
