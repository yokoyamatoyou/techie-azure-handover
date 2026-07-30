import { randomUUID } from "node:crypto";
import { calculateScoreSnapshot } from "./scoring.mjs";
import { scanUrl } from "./safeUrlScanner.mjs";

export const STANDARD_PAGE_ROLES = [
  { role: "top", weight: 0.35, label: "トップ" },
  { role: "listing", weight: 0.25, label: "一覧" },
  { role: "detail", weight: 0.2, label: "詳細" },
  { role: "action", weight: 0.2, label: "行動" },
];

const DEFAULT_PROFILE_IDS = ["jis-2016-aa"];
const STANDARDS_CHECKED_AT = "2026-06-11";

export async function scanStandardPages(pageUrls, options = {}) {
  const startedAt = new Date().toISOString();
  const scanRunId = randomUUID();
  const entries = normalizeStandardPageEntries(pageUrls);
  const childReports = [];

  for (const entry of entries) {
    const report = await scanUrl(entry.url, {
      ...options,
      pageRole: entry.role,
      pageWeight: entry.weight,
    });
    childReports.push({ entry, report });
  }

  return combineStandardReports({
    scanRunId,
    startedAt,
    entries,
    childReports,
  });
}

export function normalizeStandardPageEntries(pageUrls) {
  const source = Array.isArray(pageUrls)
    ? Object.fromEntries(STANDARD_PAGE_ROLES.map((role, index) => [role.role, pageUrls[index]]))
    : pageUrls;

  return STANDARD_PAGE_ROLES.map((roleConfig) => ({
    ...roleConfig,
    url: String(source?.[roleConfig.role] ?? "").trim(),
  }));
}

function combineStandardReports({ scanRunId, startedAt, entries, childReports }) {
  const completedReports = childReports.filter(({ report }) => report.scan_run.status === "completed");
  const pageFailures = childReports
    .filter(({ report }) => report.scan_run.status !== "completed")
    .map(({ entry, report }) => ({
      page_role: entry.role,
      page_weight: entry.weight,
      requested_url: report.scan_run.requested_url || entry.url,
      final_url: report.scan_run.final_url,
      status: report.scan_run.status,
      error_category: report.scan_run.error_category,
      error_message: report.scan_run.error_message,
    }));

  const pages = completedReports.map(({ entry, report }, index) => {
    const sourcePage = report.pages[0];
    return {
      ...sourcePage,
      page_id: pageIdFor(entry.role, index),
      page_role: entry.role,
      page_weight: entry.weight,
    };
  });

  const pageIdByChildRun = new Map(
    completedReports.map(({ report }, index) => [report.scan_run.scan_run_id, pages[index].page_id]),
  );
  const findings = completedReports.flatMap(({ report }) => {
    const pageId = pageIdByChildRun.get(report.scan_run.scan_run_id);
    return report.findings.map((finding, index) => ({
      ...finding,
      finding_id: `${pageId}-${finding.finding_id || index + 1}`,
      page_id: pageId,
    }));
  });

  const status = pages.length === entries.length ? "completed" : pages.length > 0 ? "partial" : "failed";
  const completedAt = new Date().toISOString();
  const requestedUrls = Object.fromEntries(entries.map((entry) => [entry.role, entry.url]));
  const finalUrls = Object.fromEntries(
    childReports.map(({ entry, report }) => [entry.role, report.scan_run.final_url]),
  );
  const profileIds = completedReports[0]?.report.scan_run.profile_ids ?? DEFAULT_PROFILE_IDS;
  const scoreSnapshot =
    status === "failed"
      ? calculateScoreSnapshot({
          findings: [],
          pages: [],
          profileIds,
          scanStatus: "failed",
        })
      : calculateScoreSnapshot({
          findings,
          pages,
          profileIds,
          scanStatus: "completed",
        });

  return {
    schema_version: "0.1.0",
    scan_run: {
      scan_run_id: scanRunId,
      requested_url: requestedUrls.top ?? "",
      requested_urls: requestedUrls,
      final_url: finalUrls.top ?? null,
      final_urls: finalUrls,
      profile_ids: profileIds,
      started_at: startedAt,
      completed_at: completedAt,
      status,
      error_category: status === "failed" ? "all_pages_failed" : status === "partial" ? "some_pages_failed" : null,
      page_failures: pageFailures,
      standards_checked_at: STANDARDS_CHECKED_AT,
    },
    pages,
    findings,
    criteria_mappings: [],
    score_snapshot: scoreSnapshot,
    artifacts: childReports.flatMap(({ entry, report }) =>
      report.artifacts.map((artifact) => ({
        ...artifact,
        artifact_id: `${entry.role}-${artifact.artifact_id}`,
        page_role: entry.role,
      })),
    ),
  };
}

function pageIdFor(role, index) {
  return `page-${index + 1}-${role}`;
}
