# Tasks — convergence gate

Legend: `[x]` done · `[ ]` pending

## Phase 1 — the gate itself

- [x] Register the criterion in `.kiro/steering/conventions.md` **before** any code (RULE 1)
- [x] Define input schema (`sigma_max` + `force` per sample, not a pre-divided ratio)
- [x] Implement pair classification with the direction test
- [x] Implement verdict precedence (`SINGULARITY` outranks later convergence)
- [x] Closed-form critical force `F_crit = σ_uts / σ̂`
- [x] Exit-code contract (0 admissible/insufficient, 1 inadmissible, 2 invalid)
- [x] Regression fixture from the historical 3274 MPa artifact
- [x] Self-check harness covering AC1–AC6 and R6 (`tools/selfcheck.py`, 14/14 passing)
- [ ] pytest suite around AC1–AC8
- [ ] CI workflow running the fixture on push

## Phase 2 — wire the gate into the pipeline

- [ ] `build_deck.py` emits the hotspot sample list alongside each solve
- [ ] `parse_frd.py` extracts per-increment surface displacement and von Mises stress
- [ ] Sweep runner refuses to promote a case whose gate verdict is not `ADMISSIBLE`
- [ ] Hook: re-run the fixture whenever `tools/` or `examples/` changes

## Phase 3 — report

- [ ] Self-contained HTML with base64 assets
- [ ] `F–u` curve, `σ–F` thresholds, band-limited axial profile
- [ ] Disqualified artifacts shown at equal visual weight to accepted results (RULE 4)
- [ ] Residual mesh sensitivity stated as a percentage next to every force (RULE 3)

## Phase 4 — Kiro leverage (documented for the submission write-up)

- [ ] Spec-driven build of the sweep runner from this spec directory
- [ ] Steering carries the material allowables and the standing rules
- [ ] Hook gates merges on the verdict
- [ ] MCP reads real test records for the measured overlay

## Open questions

- Should the gate own the band computation, or leave that to the reporting layer? Currently
  excluded, because the band is a presentation decision and the gate should stay a pure predicate.
- Two-sample evaluation is the minimum. Three or more samples would allow checking that `δ`
  itself is shrinking, which distinguishes "nearly converged" from "converging slowly". Not
  implemented; noted because it changes the verdict logic, not just the loop.
