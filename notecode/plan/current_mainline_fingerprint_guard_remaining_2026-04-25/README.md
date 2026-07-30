# current_mainline_fingerprint_guard_remaining_2026-04-25 README

## Objective

- Case 1 / Case 4 の実 UI fail-closed が `fingerprint_guard_remaining` に絞れたため、runtime guard 側で品質問題か final guard 接続の false-positive かを切り分ける。
- UI package の続きではなく runtime guard package として扱い、backend / UI の final guard equivalence を先に確認する。
- 修正する場合は 1 narrow hypothesis に閉じ、threshold 緩和、repair 回数増加、target length tuning、prompt accretion はしない。

## Source Of Truth

- global current package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- predecessor evidence:
  - `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\`
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\`

## Current Finding

- UI Case 1 / Case 4 は `strict_saas_mode=medium` で fingerprint soft warnings が `SYS_QUALITY_WARNINGS_UNRESOLVED` へ昇格していた。
- predecessor の backend OK は、保存 artifact 上では non-blocking な既存 `output_guard` を保持しており、UI と同じ final guard 再評価を通した equivalence が未証明だった。
- artifact 再評価では backend OK artifact も pure final guard なら同じ `SYS_QUALITY_WARNINGS_UNRESOLVED` になる。
- product-wide final guard refresh は current-mainline public-contract success tests を壊すため、この package では product behavior change を keep しない。
- current classification は `fingerprint_false_positive_or_guard_policy_residual`。次に進めるなら threshold 緩和ではなく、別 package の realization-quality hypothesis として扱う。

## Non-Goals

- `ALGORITHM.md` の persona 主体設計を変えない。
- `single-pass + optional single repair 1回` を維持する。
- `quality_guard.py` / fingerprint threshold を緩和しない。
- repair 回数、target chars、length mode 見積もりを変えない。
- `prompt_builder.py` / `blog_image_auto.py` を肥大化させない。
- persona registry / 中央管理 module を作らない。
- runtime/internal terms を本文・UI表示に出さない。
- pre-2026-04-02 archive / frozen architecture package を reopen しない。
