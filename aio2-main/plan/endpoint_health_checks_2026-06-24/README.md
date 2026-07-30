# Endpoint Health Checks Slice - 2026-06-24

## Owner

- Current owner: `core/site_health/endpoint_health_checker.py`
- Aggregation owner: `core/site_health/security_checker.py`
- Classification/score owner: `core/site_health/maintenance_risk.py`
- Handoff owner: `core/application/technical_summary_builder.py`

## Scope

This slice adds passive public endpoint health checks to the existing
`public_technology_risks -> site_health_checks -> engineer_tasks` flow.

Checks are generic and must not be tuned for a specific validation site.

## Non-Invasive Boundary

Allowed:

- Fetch the analyzed page already in scope.
- Fetch `/robots.txt`.
- Fetch a small fixed set of known sitemap endpoints:
  `/sitemap.xml`, `/wp-sitemap.xml`, `/sitemap_index.xml`.
- Fetch `/wp-json/` only as an unused endpoint/fake-200 check when the page
  does not look like WordPress.
- Fetch exactly one generated nonexistent URL to detect soft 404 behavior.
- Read public HTTP headers such as `X-Powered-By` and `Server`.

Not allowed:

- Directory discovery.
- Backup file discovery.
- `.git` or admin endpoint probing.
- Brute force or credential checks.
- Vulnerability exploitation.
- Multiple random missing URL probes.
- EC transaction safety or product data audit.

## Output Contract

- Non-engineer output must describe the public sign, what to ask the maintenance
  vendor, and whether it is urgent or can wait for a renewal.
- Engineer tasks must include confirmation URL, HTTP status, Content-Type,
  short evidence excerpt, recommended fix, command, and pass condition.
- Wording must avoid compromise/vulnerability assertions. Use "確認候補" and
  "保守会社に確認してください".
