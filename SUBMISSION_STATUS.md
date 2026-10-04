# Submission Readiness

**Status: partial LiDAR baseline; not a complete implementation of the case study.** This review is based on the full case-study brief, the checked-in source and reports, the three local capture folders, and a fresh local run of each supplied LiDAR command.

## Verified locally

All three LiDAR commands completed successfully and generated a JSON plan, SVG plan, raw-pose result, and drift ablation. The default run processed 58, 176, and 325 sampled frames respectively. These are pipeline smoke results, not measurement-accuracy results.

| Capture | Estimated hull area | Ceiling value | Status |
|---|---:|---:|---|
| `single_room` | 33.725 m² | Not reported | Outline estimated |
| `single_scan_floor_only` | 92.541 m² | Not reported | Outline estimated |
| `single_scan_with_ceiling` | 176.161 m² | 4.035 m observed vertical span* | Outline estimated |

`*` The 4.035 m value is the observed point-cloud vertical span after operator confirmation, not a tape-measured ceiling height. All intervals are explicitly uncalibrated.

## Requirement status

| Brief requirement | Current evidence | Status |
|---|---|---|
| Photo, video, and LiDAR tiers | Only the supplied LiDAR export path runs; the CLI rejects photo/video tiers | **Incomplete** |
| Named installable capture route and device matrix | Export layout and walking guidance are documented, but no app/version or device run is identified | **Incomplete** |
| Per-room plans, openings, full-property adjacency, damage, concealed-damage rules, and scope items | Single-scan convex-hull outline; other fields are absent or explicitly `not_assessed` | **Partial** |
| Benchmark set: 3+ rooms with connector, staged damage, all tiers, repeated scan, ground truth | Three independent LiDAR exports; no connector, repeat, staged labels, or laser/tape truth | **Incomplete** |
| Accuracy, calibration, opening, ceiling, and repeatability gates | No independent references or repeated captures | **Not evaluated** |
| Consumer scanning app comparison on two rooms | No app name/version or exports | **Missing** |
| Fix loop for the worst gate | Before/after translation-drift outputs exist; the declared photo-stitch failure remains unfixed | **Incomplete** |
| Published output schema | A local draft schema is checked in; the brief's published schema was not supplied | **Unverified** |
| Reproduction from a clean clone | Source and results are in Git; the 873.7 MB raw bundles are ignored and absent from GitHub | **Incomplete** |
| Technical report and compliance record | Markdown report, compliance matrix, capture-route note, fix-loop note, and benchmark summary exist | **Present with open gaps** |

## Submission guidance

Present this work as an exploratory LiDAR baseline. Do not claim that it passes dimensional accuracy, ceiling-height, opening, repeatability, photo/video, multi-room, damage, or head-to-head gates. The detailed status is in [COMPLIANCE.md](COMPLIANCE.md); current numbers and caveats are in [outputs/benchmark_summary.md](outputs/benchmark_summary.md).

## Evidence still needed for a complete submission

1. Implement and run photo-only and video-only pipelines on the required iPhone 15+ inputs, and name/version the installable capture route.
2. Capture at least three connected rooms, staged examples from two damage classes, a repeat scan, and matching laser/tape measurements and opening inventory.
3. Run a named consumer scanning app on two of those rooms and include its exports and dimension-by-dimension comparison.
4. Ship the fix for the measured worst-performing gate and regenerate before/after outputs against ground truth.
5. Include the published output schema and deliver the raw capture bundle separately so a clean clone can reproduce the reported results.
