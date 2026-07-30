import dns from "node:dns/promises";
import net from "node:net";

const BLOCKED_PROTOCOLS = new Set(["file:", "ftp:", "data:", "javascript:"]);
const ALLOWED_PROTOCOLS = new Set(["http:", "https:"]);
const SENSITIVE_QUERY_KEYS =
  /(^|[_-])(token|secret|password|passwd|pass|auth|authorization|api[-_]?key|key|session|sid|cookie|jwt|credential|code|access[-_]?token|refresh[-_]?token)([_-]|$)/i;

export function redactText(value, maxLength = 160) {
  if (value === null || value === undefined) {
    return "";
  }

  const compact = String(value)
    .replace(/[\r\n\t]+/g, " ")
    .replace(/\s{2,}/g, " ")
    .trim()
    .replace(/(token|secret|password|passwd|auth|authorization|api[-_]?key|session|cookie|jwt)=([^&\s]+)/gi, "$1=[redacted]");

  return compact.length > maxLength ? `${compact.slice(0, maxLength - 1)}...` : compact;
}

export function redactUrl(input) {
  let parsed;
  try {
    parsed = input instanceof URL ? new URL(input.toString()) : new URL(String(input));
  } catch {
    return redactText(input, 200);
  }

  if (parsed.username) {
    parsed.username = "[redacted]";
  }
  if (parsed.password) {
    parsed.password = "[redacted]";
  }

  for (const key of [...parsed.searchParams.keys()]) {
    if (SENSITIVE_QUERY_KEYS.test(key)) {
      parsed.searchParams.set(key, "[redacted]");
    }
  }

  parsed.hash = "";
  return parsed.toString();
}

export function isPrivateOrLocalAddress(address) {
  const ipType = net.isIP(address);
  if (ipType === 4) {
    return isPrivateOrLocalIpv4(address);
  }
  if (ipType === 6) {
    return isPrivateOrLocalIpv6(address);
  }
  return false;
}

function isPrivateOrLocalIpv4(address) {
  const octets = address.split(".").map((part) => Number(part));
  if (octets.length !== 4 || octets.some((part) => Number.isNaN(part) || part < 0 || part > 255)) {
    return true;
  }

  const [a, b] = octets;
  return (
    a === 0 ||
    a === 10 ||
    a === 127 ||
    a >= 224 ||
    (a === 100 && b >= 64 && b <= 127) ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168)
  );
}

function isPrivateOrLocalIpv6(address) {
  const lower = address.toLowerCase();
  if (lower === "::" || lower === "::1") {
    return true;
  }
  if (lower.startsWith("::ffff:")) {
    return isPrivateOrLocalIpv4(lower.replace("::ffff:", ""));
  }

  const firstHextetText = lower.split(":")[0];
  const firstHextet = Number.parseInt(firstHextetText, 16);
  if (Number.isNaN(firstHextet)) {
    return true;
  }

  return (firstHextet & 0xfe00) === 0xfc00 || (firstHextet & 0xffc0) === 0xfe80;
}

export function isBlockedHostname(hostname) {
  const normalized = hostname.toLowerCase().replace(/\.$/, "");
  const ipType = net.isIP(normalized);

  if (normalized === "localhost" || normalized.endsWith(".localhost")) {
    return true;
  }
  if (ipType) {
    return isPrivateOrLocalAddress(normalized);
  }

  return !normalized.includes(".");
}

export async function validateUrlForScanning(input, options = {}) {
  const { allowLocalFixture = false } = options;
  let parsed;

  try {
    parsed = new URL(String(input).trim());
  } catch {
    return blocked("invalid_url", "URLの形式を確認してください。");
  }

  if (BLOCKED_PROTOCOLS.has(parsed.protocol) || !ALLOWED_PROTOCOLS.has(parsed.protocol)) {
    return blocked("blocked_scheme", "httpまたはhttps以外のURLは取得できません。", parsed);
  }

  if (parsed.username || parsed.password) {
    return blocked("url_credentials", "認証情報を含むURLは取得できません。", parsed);
  }

  if (!allowLocalFixture && isBlockedHostname(parsed.hostname)) {
    return blocked("blocked_local_or_private_host", "localhost、private network、内部ホスト名は取得できません。", parsed);
  }

  if (!allowLocalFixture && !net.isIP(parsed.hostname)) {
    const resolution = await resolvePublicAddresses(parsed.hostname);
    if (!resolution.ok) {
      return blocked("dns_resolution_failed", "ホスト名を解決できません。", parsed);
    }
    if (resolution.addresses.some((address) => isPrivateOrLocalAddress(address))) {
      return blocked("blocked_private_dns_result", "DNS解決結果がprivate/local networkを指しています。", parsed);
    }
  }

  return {
    ok: true,
    url: parsed.toString(),
    redactedUrl: redactUrl(parsed),
    hostname: parsed.hostname.toLowerCase(),
  };
}

async function resolvePublicAddresses(hostname) {
  try {
    const records = await dns.lookup(hostname, { all: true, verbatim: false });
    return {
      ok: records.length > 0,
      addresses: records.map((record) => record.address),
    };
  } catch {
    return { ok: false, addresses: [] };
  }
}

function blocked(errorCategory, message, parsed = null) {
  return {
    ok: false,
    errorCategory,
    message,
    redactedUrl: parsed ? redactUrl(parsed) : redactText(parsed ?? ""),
  };
}
