# pinbreak

**At what force does this contact pin break — and am I allowed to believe the answer?**

`pinbreak` is an automated strength-analysis harness for connector contact pins, built for
[Kiroween 2026](https://kiroween.devpost.com/). It drives a parametric finite element study
end to end, and — more importantly — it refuses to report a stress peak it cannot defend.

```
parameters.yaml
   │
   ├── geometry  →  parametric pin profile, revolved mesh (no CAD clicking)
   ├── deck      →  CalculiX .inp  (contact pairs, steps, output requests)
   ├── sweep     →  N cases: element size × fillet radius × load direction
   ├── solve     →  ccx + Pardiso
   ├── gate      →  convergence + singularity verdict per hotspot   ← the point
   └── report    →  self-contained HTML: F–u curve, σ–F thresholds, 3D frame playback
```

## Why the gate exists

In linear elasticity the stress field scales exactly with load, so the normalised field is
independent of the applied force:

```
σ_ij(x; F) = F · σ̂_ij(x)
```

`σ̂` is therefore a property of the **mesh and geometry alone**, which makes it a legitimate
convergence metric — and the fracture force falls out in closed form instead of by bisection:

```
F_crit = σ_uts / max(σ̂_vm)
```

But a contact edge is a singularity: `σ ~ K·r^(-λ)` with `λ ∈ (0, 0.5)`, so refining the mesh
does not converge it, it *amplifies* it. Mesh refinement is not the fix. It is the diagnostic.

The gate encodes that diagnostic as arithmetic rather than taste:

| Observed as `h → h/2`        | Verdict          | Meaning                                  |
| ---------------------------- | ---------------- | ---------------------------------------- |
| `\|Δσ̂/σ̂\| ≤ 5%`              | `CONVERGED`      | real feature, peak admissible            |
| `σ̂` rises, `\|Δσ̂/σ̂\| > 5%`    | `SINGULARITY`    | mesh artifact, peak **inadmissible**     |
| `σ̂` falls, `\|Δσ̂/σ̂\| > 5%`    | `UNDER_RESOLVED` | needs refinement, not yet admissible     |

The 5% threshold and the direction of the inequality are **committed to
`.kiro/steering/conventions.md` before a sweep runs**. That is the whole design: a criterion in
a note file is a suggestion; a criterion in the repository, checked by a hook, is a fact.

## Status

**In development** — built during the Kiroween 2026 submission window (30 Oct – 4 Dec 2026).
The engineering question is inherited from earlier manual FEA work; the code here is new.

- [x] Convergence gate logic (`tools/convergence_gate.py`)
- [ ] Geometry → deck generator
- [ ] Case sweep + manifest
- [ ] FRD post-processor
- [ ] Self-contained interactive report
- [ ] Kiro hooks wired to the gate

## Quick start

```bash
python tools/convergence_gate.py examples/z10_3_singularity.json
python tools/convergence_gate.py examples/z10_3_singularity.json --uts 1150
```

Requires Python 3.9+. No third-party dependencies for the gate itself.

## License

MIT — see [LICENSE](LICENSE).
