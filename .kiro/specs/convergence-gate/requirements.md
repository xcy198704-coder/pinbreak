# Requirements — convergence gate

## Problem

A linear-elastic FEA of a contact pin produces stress peaks at contact edges and geometric
notches. Both look alike in a contour plot. One is a physical stress concentration, the other is a
singularity that diverges under refinement. Reporting the second as if it were the first has
already happened once on this class of part, and produced a 3274 MPa peak on a component that
fails near 21 N.

## Scope

A standalone, dependency-free evaluator that takes a set of normalised stress samples for one
hotspot and returns a verdict that downstream reporting can act on. It is deliberately separated
from the solver: it must be runnable in a hook, in CI, and by hand.

## Functional requirements

**R1 — Normalise by load.**
The gate operates on `σ̂ = σ_max / F`, never on raw stress. In linear elasticity `σ ∝ F`, so `σ̂`
is independent of the applied load and depends only on mesh and geometry. Ratios of raw stresses
at different loads would be meaningless.

**R2 — Order by refinement.**
Samples are supplied in ascending mesh refinement (descending element size `h`). The gate evaluates
each consecutive pair.

**R3 — Classify each pair.**
For each pair `(h_i, σ̂_i) → (h_{i+1}, σ̂_{i+1})` with `h_{i+1} < h_i`:

```
δ_i = |(σ̂_{i+1} − σ̂_i) / σ̂_i|

δ_i ≤ tol                          → CONVERGED
σ̂_{i+1} > σ̂_i  and δ_i > tol       → SINGULARITY
σ̂_{i+1} < σ̂_i  and δ_i > tol       → UNDER_RESOLVED
```

`tol` defaults to `0.05` and is a named constant, not a literal.

**R4 — Aggregate to a single verdict.**
`ADMISSIBLE` only if the finest pair is `CONVERGED`. If any pair is `SINGULARITY`, the hotspot is
`INADMISSIBLE` regardless of later pairs — a singularity does not become real with more elements.
Otherwise `INSUFFICIENT`.

**R5 — Report the residual sensitivity.**
The gate returns the relative change `δ` of the finest pair as a percentage, so the report can
state it next to the number (RULE 3 of the conventions).

**R6 — Critical force in closed form.**
Given `σ_uts`, return `F_crit = σ_uts / σ̂` using the finest sample. This replaces load bisection.

**R7 — Never raise on bad data, always refuse on insufficient data.**
Fewer than two samples is not an error in the input, it is a result: `INSUFFICIENT`. Non-monotonic
refinement order is an error and must be reported as such.

## Acceptance criteria

| #   | Criterion                                                                             |
| --- | ------------------------------------------------------------------------------------- |
| AC1 | The published 3274 MPa bore-edge case classifies as `SINGULARITY` / `INADMISSIBLE`     |
| AC2 | A synthetic notch with a 2% change under refinement classifies as `CONVERGED`          |
| AC3 | Decreasing stress with more than 5% change classifies as `UNDER_RESOLVED`               |
| AC4 | One sample returns `INSUFFICIENT`, exit code 0                                         |
| AC5 | Ascending `h` (wrong order) is rejected with a non-zero exit code                      |
| AC6 | `tol` is a module-level constant, not hard-coded in the comparison                     |
| AC7 | No third-party imports; runs on a bare Python 3.9 install                              |
| AC8 | Exit code is 0 for admissible/insufficient, 1 for inadmissible, 2 for invalid input    |

## Non-goals

- Not a mesher, a solver wrapper, or a reporting layer.
- Not a general-purpose statistical convergence test. It encodes one specific engineering
  judgement for one class of feature.
- No unit conversion. Inputs are MPa and N.
