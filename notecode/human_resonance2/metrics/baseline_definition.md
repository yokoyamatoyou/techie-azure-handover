# Baseline Metric Definitions

## Goal
Define measurable criteria before enabling new phases.

## Core Metrics
1. `review_points_count`
   - definition: number of review points produced per article
   - target: reduce without losing factual consistency
2. `lexical_diversity_score`
   - definition: normalized diversity index over content tokens
   - target band: avoid both repetition and unnatural synonym churn
3. `burstiness_score`
   - definition: variance pattern of sentence lengths
   - target: mid-range rhythm (not flat, not chaotic)
4. `nominalization_ratio`
   - definition: ratio of abstract/nominalized forms
   - target: decrease in explanatory/branding styles where overused
5. `layout_integrity_score`
   - definition: heading flow consistency and section order validity
   - target: intro -> core -> support -> closing consistency

## Baseline Collection Procedure
1. Sample at least 30 recent generations across article types.
2. Compute each metric from current production output.
3. Store mean, p50, p90 values.
4. Use baseline to set safe phase thresholds.

## Acceptance Gate
Enable a phase only if:
1. no regression in factual safety checks
2. no major increase in legal/editor warnings
3. readability improves or remains neutral on p50 and p90

