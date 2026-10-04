# Supplied Data Bundle Inventory

This inventory describes the local capture folders supplied for the case study. The raw folders are intentionally excluded from ordinary Git commits: together they occupy 873,680,157 bytes (about 873.7 MB) and contain RGB room video.

| Local folder | Depth frames | RGB video | Files | Bytes |
|---|---:|---:|---:|---:|
| `single_room/c00a170fe1` | 1,715 | `rgb.mp4` | 3,434 | 88,503,534 |
| `single_scan_floor_only/1a8384c3f6` | 5,251 | `rgb.mp4` | 10,506 | 276,731,533 |
| `single_scan_with_ceiling/c7d28f72c6` | 9,745 | `rgb.mp4` | 19,494 | 508,445,090 |
| **Total** | **16,711** | **3 videos** | **33,434** | **873,680,157** |

Each bundle has depth and confidence PNG sequences, `odometry.csv`, `imu.csv`, `camera_matrix.csv`, and an HEVC/H.265 RGB video. The video frame counts match the odometry row counts in the supplied data. The three folders are independent single-scan exports. They do not contain separate photo files, a multi-room connector capture, repeat scans, staged-damage labels, measured room dimensions/openings, or consumer-app exports.

The RGB adapters sample up to eight still frames from the existing videos for the photo proxy and sample the RGB streams for the video proxy. Both use the paired odometry and camera intrinsics for metric camera poses and do not read the depth/confidence maps. This is a pose-assisted RGB comparison, not a strict image-only benchmark. It adds no input data beyond these folders.

## Reproduction handoff

The sample folders exist in the original working copy but are not tracked by Git. A fresh clone of the GitHub repository cannot reproduce the supplied-scan outputs until these folders are copied beside `README.md` with the same names. The repository includes the commands and current output artifacts; the raw inputs must be delivered separately with the submission if the evaluator needs to rerun them.

No upload of these raw files is implied by this inventory. The videos may show private interiors, and the dataset is too large for an accidental ordinary Git commit.
