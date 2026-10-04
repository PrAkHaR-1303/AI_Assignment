# Case Study Compliance Matrix

Statuses refer to artifacts in this workspace. `Partial` means a reproducible baseline exists but the acceptance gate cannot be claimed. `Blocked by inputs/device` means required evidence or hardware is absent.

| Requirement | File path | Artifact | Status |
|---|---|---|---|
| Dimensioned per-room plan, floor area, ceiling height, openings | `roomscan/pipeline.py`, `outputs/*/plan.json`, `outputs/*/plan.svg` | LiDAR hull plan and measurement fields; ceiling evidence heuristic | Partial; opening detector absent and dimensions uncalibrated |
| Stitched whole-property plan with correct adjacency | `roomscan/pipeline.py` | Single-capture output contract and explicit adjacency status | Blocked by missing multi-room capture and registration |
| Damage classes and metric extents | `roomscan/pipeline.py` | `damage_regions` output field | Blocked by missing labeled/staged damage data and classifier |
| Concealed-damage rules | `roomscan/pipeline.py` | `concealed_damage` output field | Blocked by absent moisture/thermal/material data and rule validation |
| Scope line items keyed to surfaces | `roomscan/pipeline.py` | `scope_line_items` output field | Blocked by unmeasured damage regions and pricing schedule |
| Confidence interval on every measurement | `roomscan/pipeline.py` | Interval for each emitted measurement | Partial; intervals are conservative assumptions, not calibrated against ground truth |
| One command per capture; JSON to a schema; rendered plan | `roomscan/cli.py`, `roomscan/pipeline.py`, `schemas/case-study-output.schema.json`, `outputs/*` | `python -m roomscan <capture>` writes JSON and SVG against a local draft schema | Partial; the referenced published schema was not supplied |
| Photo tier from 2-8 stills, including whole-property stitching | `roomscan/cli.py`, `README.md` | Tier selector rejects unsupported adapter clearly | Blocked; no photo captures or monocular reconstruction backend |
| Video tier on iPhone 15+ | `roomscan/cli.py`, `README.md` | Video input is recorded in metadata | Blocked; no video-only reconstruction adapter or iPhone capture route |
| LiDAR tier and device matrix | `roomscan/pipeline.py`, `TECHNICAL_REPORT.md` | LiDAR reader for supplied export format | Partial; device compatibility and accuracy need device runs and GT |
| Stock capture protocol or installable iOS build | `CAPTURE_PROTOCOL.md` | Capture handoff requirements | Blocked by absent iPhone/Xcode/TestFlight and unspecified capture app |
| Benchmark composition, including multi-room and staged damage | `COMPLIANCE.md` | Missing-input register | Blocked; supplied examples are independent single-scan bundles |
| Opening-width gate | `outputs/*/plan.json` | Opening detection status | Not evaluated |
| Ceiling-height and repeatability gates | `outputs/*/plan.json`, `TECHNICAL_REPORT.md` | Heuristic height evidence and repeatability protocol | Not evaluated; no ground truth or repeated same-room capture |
| Drift accountability and on/off ablation | `roomscan/geometry.py`, `outputs/*/drift_ablation.json` | Revisit-based translation correction with raw/corrected runs | Partial; no rotation graph or GT-based footprint score |
| Photo/video accuracy gates and calibrated intervals | `TECHNICAL_REPORT.md` | Error-budget statement | Not evaluated |
| LiDAR head-to-head against a consumer app | `COMPLIANCE.md` | Comparison table placeholder in report | Blocked; app export/version and shared-room GT absent |
| Shipped fix, regenerable before/after, readable diff | `roomscan/pipeline.py`, `outputs/*/before_fix.json`, `outputs/*/plan.json`, `outputs/*/drift_ablation.json` | Drift correction ablation | Partial; improvement is geometric only and cannot be scored against truth |
| Fresh-machine reproduction bundle | `README.md`, `roomscan/`, `DATA_BUNDLE.md` | Standard-library Python package and CLI; raw-input inventory | Partial; raw capture folders are excluded from Git, so a clean clone cannot regenerate the sample outputs |
| Commit history/process evidence | `.git` | Git was initialized after intake; staging required a one-command safe-directory override because the sandbox owns `.git` | Available for continued candidate commits |
| Technical report (maximum six pages) | `TECHNICAL_REPORT.md` | Concise architecture, tiers, drift, calibration, and gaps | Partial |
| Raw sensor logs, GT, app exports | `single_room/`, `single_scan_floor_only/`, `single_scan_with_ceiling/` | Supplied raw scan bundles exist in the original working copy | Partial; raw inputs are excluded from Git; no ground truth or app exports |
