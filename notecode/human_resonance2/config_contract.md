# Config Contract (human_resonance2)

## Objective
Define config keys for phased rollout and safe fallback.

## Top-level Proposal
```json
{
  "quality_pipeline": {
    "enabled": false,
    "mode": "off",
    "rollout_percent": 100,
    "fail_open": true,
    "phase01_lexical_enabled": false,
    "phase01_tokenizer": "auto",
    "phase02_burstiness_enabled": false,
    "phase03_nominalization_enabled": false,
    "phase04_style_drift_enabled": false,
    "phase05_layout_guard_enabled": false,
    "phase06_orchestrator_enabled": false,
    "phase07_rollout_enabled": false,
    "lexical_threshold": 0.32,
    "burstiness_target_min": 0.18,
    "burstiness_target_max": 0.52,
    "nominalization_alert_threshold": 0.18,
    "style_alignment_min_score": 0.72,
    "domain_guard_strictness": "normal",
    "supplement_min_position_ratio": 0.45,
    "intro_max_length_ratio": 0.35,
    "section_coherence_min_score": 0.40,
    "global_rewrite_ratio_cap": 0.20,
    "conflict_resolution_policy": "safe_first",
    "quality_gate_min_score": 0.55,
    "max_rewrite_ratio": 0.15,
    "max_sentence_split_ratio": 0.12,
    "max_nominalization_rewrite_ratio": 0.12
  }
}
```

## Key Rules
1. `enabled=false` must guarantee no behavior change from current production.
2. Every phase key must be independently togglable.
3. `fail_open=true` means any phase error returns original text unchanged.
4. `max_rewrite_ratio` caps rewrite aggressiveness.
5. `phase01_tokenizer` supports `auto|regex|sudachi` (auto fallback to regex when Sudachi is unavailable).
6. `burstiness_target_min` and `burstiness_target_max` define the acceptable burstiness band.
7. `max_sentence_split_ratio` caps Phase02 split/merge count by sentence count ratio.
8. `nominalization_alert_threshold` sets the minimum sentence-level alert trigger for Phase03.
9. `max_nominalization_rewrite_ratio` caps Phase03 rewrite count by sentence count ratio.
10. `style_alignment_min_score` sets the minimum acceptable alignment score for Phase04.
11. `domain_guard_strictness` controls drift sensitivity (`relaxed|normal|strict`).
12. `supplement_min_position_ratio` sets the earliest allowed section ratio for supplement blocks in Phase05.
13. `intro_max_length_ratio` caps intro section token share in Phase05.
14. `section_coherence_min_score` sets the minimum adjacent-section coherence score in Phase05.
15. `global_rewrite_ratio_cap` sets Phase06 global change cap across Phase01-05 outputs.
16. `conflict_resolution_policy` chooses conflict winner policy (`safe_first|readability_first|diversity_first`).
17. `quality_gate_min_score` sets the minimum overall quality score for gate pass.
18. `phase07_rollout_enabled` enables rollout routing and integration telemetry reporting.
19. `rollout_percent` controls enforce traffic share when Phase07 is enabled.

## Validation Rules
1. `mode`: `off|shadow|enforce`
2. `phase01_tokenizer`: `auto|regex|sudachi`
3. Numeric values must be clamped to safe ranges.
4. `burstiness_target_min <= burstiness_target_max`
5. `nominalization_alert_threshold`: `0.0 <= x <= 1.0`
6. `max_nominalization_rewrite_ratio`: `0.0 <= x <= 1.0`
7. `style_alignment_min_score`: `0.0 <= x <= 1.0`
8. `domain_guard_strictness`: `relaxed|normal|strict`
9. `supplement_min_position_ratio`: `0.2 <= x <= 0.9`
10. `intro_max_length_ratio`: `0.1 <= x <= 0.8`
11. `section_coherence_min_score`: `0.0 <= x <= 1.0`
12. `global_rewrite_ratio_cap`: `0.0 <= x <= 1.0`
13. `conflict_resolution_policy`: `safe_first|readability_first|diversity_first`
14. `quality_gate_min_score`: `0.0 <= x <= 1.0`
15. `rollout_percent`: `0 <= x <= 100`
