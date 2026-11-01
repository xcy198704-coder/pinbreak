---
inclusion: always
---

# Working conventions — read before changing anything numeric

## RULE 1 — Criteria are pre-registered

Any acceptance criterion that will be used to judge a result **must be committed to this file
before the first solve of the sweep it governs**. Not after the plots are drawn. Any commit that
adds or changes a criterion must be dated and must not be amended after results exist.

Rationale: a peak that looks like a finding and is actually an artifact is the single most
expensive failure mode in this domain. Pre-registration is the only defence, because it removes
the analyst's discretion over whether the data passed.

## RULE 2 — The convergence criterion (v1, registered 2026-11-01)

For a hotspot with normalised stress `σ̂ = σ/F`, sampled at element sizes `h` and `h/2`:

```
δ = |(σ̂(h/2) − σ̂(h)) / σ̂(h)|

δ ≤ 5%                     → CONVERGED      peak admissible
σ̂(h/2) > σ̂(h) and δ > 5%  → SINGULARITY    peak INADMISSIBLE, report the band instead
σ̂(h/2) < σ̂(h) and δ > 5%  → UNDER_RESOLVED refine further, nothing admissible yet
```

**The direction matters.** Increasing stress under refinement means a singularity; decreasing
means insufficient resolution. A previous handwritten note recorded this inequality backwards,
which would have classified every genuine notch as an artifact. It was caught only by recomputing
from raw solver output rather than trusting the note — the reason RULE 1 exists.

## RULE 3 — No single-number fracture force without a converged band

If any hotspot in the failure path fails the gate, the deliverable reports a **band**, not a
point value. State the residual mesh sensitivity as a percentage next to it.

## RULE 4 — Negative results are results

An artifact that was disqualified belongs in the report with its evidence, in the same visual
weight as the accepted result. It is the strongest evidence that the method works.

## RULE 5 — Measured data is never simulated

If a test record exists, it is plotted as measured. If it does not exist, the field is empty and
labelled as such. No synthetic stand-ins, no "typical value" dressed as a measurement.

## RULE 6 — Units and precision

mm, N, MPa. Forces to 3 significant figures, displacements to 3 decimals, stresses to 4 significant
figures. Never round a threshold to a round number — 21.4 N is information, 21 N is a guess.
