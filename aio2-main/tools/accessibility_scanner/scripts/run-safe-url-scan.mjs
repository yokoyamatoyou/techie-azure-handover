#!/usr/bin/env node

import { scanUrl } from "./scanner/safeUrlScanner.mjs";
import { scanStandardPages } from "./scanner/standardPageScanner.mjs";

const args = process.argv.slice(2);
const parsed = parseArgs(args);

const report = parsed.mode === "standard" ? await scanStandardPages(parsed.pages) : await scanUrl(parsed.url);
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);

if (report.scan_run.status !== "completed") {
  process.exitCode = 1;
}

function parseArgs(args) {
  if (args.includes("--standard")) {
    const pages = {
      top: valueForFlag(args, "--top"),
      listing: valueForFlag(args, "--listing"),
      detail: valueForFlag(args, "--detail"),
      action: valueForFlag(args, "--action"),
    };
    const positional = args.filter((arg, index) => !arg.startsWith("--") && !isFlagValue(args, index));
    return {
      mode: "standard",
      pages: {
        top: pages.top || positional[0] || "",
        listing: pages.listing || positional[1] || "",
        detail: pages.detail || positional[2] || "",
        action: pages.action || positional[3] || "",
      },
    };
  }

  return {
    mode: "single",
    url: args[0] ?? "https://healthrent.duskin.jp/",
  };
}

function valueForFlag(args, flag) {
  const index = args.indexOf(flag);
  if (index < 0) {
    return "";
  }
  const value = args[index + 1] ?? "";
  return value.startsWith("--") ? "" : value;
}

function isFlagValue(args, index) {
  return index > 0 && args[index - 1].startsWith("--") && args[index - 1] !== "--standard";
}
