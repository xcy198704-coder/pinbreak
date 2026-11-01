---
inclusion: always
---

# Technical context

## Stack

| Layer        | Choice                                      | Why                                              |
| ------------ | ------------------------------------------- | ------------------------------------------------ |
| Language     | Python 3.9+                                 | geometry generation, post-processing, reporting   |
| Solver       | CalculiX `ccx` + Pardiso                    | scriptable, no license server, batch-native       |
| Elements     | C3D10 quadratic tets                        | bending-dominated thin features need mid-nodes    |
| Numerics     | NumPy (`.npz` frame cache)                  | compact per-increment surface data                |
| Rendering    | matplotlib (static), PyVista/VTK (volume)   | figures for the report                            |
| Front end    | three.js, ES modules, plain HTML/CSS        | the report must be one file, offline, double-click |

## Hard constraints learned the hard way

- **matplotlib and VTK cannot share a process.** Importing matplotlib before an offscreen PyVista
  render segfaults with no traceback. The animation renderer must never import matplotlib; the jet
  colormap is hand-rolled.
- **Do not run two `ccx` jobs concurrently** on the same host — memory and thread contention. Runs
  are serialised through a queue and resume from the last completed increment.
- **Force control has no solution before contact closure.** Before the push head closes the gap the
  pin is a free body with no static equilibrium. Loading is displacement-controlled, which is also
  what the physical test rig does.
- **`OMP_NUM_THREADS` must be pinned** (10 on the reference machine) or timings and residual paths
  drift between runs.
- **HTML report assets are base64-embedded.** An external reference breaks the "opens by double
  click on a machine with no Python" promise.
- **Windows paths in templates need raw strings.** `D:\fea2` contains `\f`, a form feed.

## Data flow

```
parameters.yaml → build_deck.py → cases/<id>/job.inp
                                      ↓ ccx
                                 job.frd  (text, fixed-width)
                                      ↓ parse_frd.py
                                 frames.json  (per increment)
                                      ↓ extract_surface.py
                                 surf_<id>.npz  (nodes, faces, disp, vm per frame)
                                      ↓
                    figures + animation data + report.html
```

Frames are ordered by increment, displacement first. `frd` parsing is fixed-width column slicing;
do not "improve" it with regex splitting, which breaks on exponent fields.

## Conventions

- Element size is always reported in millimetres alongside every stress result.
- Every numeric result carries its case id so it can be reproduced from the manifest.
- Units are mm, N, MPa, and nothing else. No unit conversion layer.
