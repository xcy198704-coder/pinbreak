# Design — convergence gate

## Files

```
tools/convergence_gate.py            # the evaluator, no third-party imports
examples/z10_3_singularity.json      # the historical artifact, as a regression fixture
.kiro/hooks/convergence-gate.json    # runs the fixture on every change to tools/ or examples/
.kiro/specs/convergence-gate/        # this spec
```

## Data model

One hotspot evaluation is described by a small JSON document:

```json
{
  "location": "bore mouth z=11.0 mm",
  "note": "free text, shown in output",
  "sigma_uts": 1150.0,
  "samples": [
    { "h": 0.090, "sigma_max": 156.7, "force": 5.0 },
    { "h": 0.045, "sigma_max": 248.4, "force": 5.0 }
  ]
}
```

`sigma_max` and `force` are supplied rather than the ratio, because the ratio is the thing the tool
is validating — accepting a pre-divided number would hide a load mismatch between samples. The
tool checks that all samples share the same `force` within 1e-9 and refuses otherwise.

## Algorithm

```
normalise:   σ̂_i = sigma_max_i / force_i
validate:    h strictly descending; forces equal; at least 1 sample
pairs:       for i in 1..n-1: δ_i, trend_i = sign(σ̂_i − σ̂_{i-1})
classify:    per R3
aggregate:   per R4
residual:    δ of the last pair, as percent
```

## Verdict precedence

`SINGULARITY` outranks everything. If any pair shows rising stress under refinement beyond
tolerance, the hotspot is inadmissible — later convergence would be coincidence, not evidence.

```
samples < 2                    → INSUFFICIENT
any pair SINGULARITY           → INADMISSIBLE
last pair CONVERGED            → ADMISSIBLE
otherwise                      → INSUFFICIENT
```

## Why not a p-refinement or Richardson extrapolation

Richardson extrapolation assumes a known convergence order `p`, and a singularity has no integer
`p` — it diverges. Estimating an order from two samples would produce a plausible-looking finite
number for a quantity that has no limit. Refusing to extrapolate is the correct behaviour, and it
is a requirement, not an omission.

## Failure behaviour

The tool is used as a gate in a hook and in CI, so exit codes are part of the interface:

| Code | Meaning                                        |
| ---- | ---------------------------------------------- |
| 0    | admissible, or insufficient data (not a fault) |
| 1    | inadmissible — the peak must not be reported   |
| 2    | invalid input (order, mismatched loads, parse) |

Code 1 is a *successful* evaluation with a negative verdict. It must not be conflated with 2.

## Test strategy

The historical case is the primary regression fixture: a real peak at `h = 0.09 → 0.045` that rises
by 58.5% under refinement. Any future change that makes this case pass as `CONVERGED` is a
regression against reality, regardless of how good the code looks.
