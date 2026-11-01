#!/usr/bin/env python3
"""Self-check for the convergence gate.

Runs the acceptance criteria from .kiro/specs/convergence-gate/requirements.md
without requiring pytest, so it can be executed by a hook or in CI on a bare
Python install.

Exit 0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import convergence_gate as gate  # noqa: E402

EXAMPLES = ROOT / "examples"

checks = []


def check(label: str, condition: bool, detail: str = "") -> None:
    checks.append((label, condition, detail))


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


# AC1 - the historical artifact is refused.
r = gate.evaluate(load("z10_3_singularity.json"))
check("AC1 artifact -> INADMISSIBLE", r.verdict == gate.INADMISSIBLE, r.verdict)
check("AC1 exits 1", r.exit_code == 1, str(r.exit_code))
check("AC1 classification is SINGULARITY", r.pairs[0].kind == gate.SINGULARITY, r.pairs[0].kind)
check("AC1 refinement amplifies (~58%)", 55.0 < r.residual_pct < 62.0, "%.1f%%" % r.residual_pct)

# AC2 - a converged peak is accepted.
r2 = gate.evaluate(load("synthetic_converged.json"))
check("AC2 converged -> ADMISSIBLE", r2.verdict == gate.ADMISSIBLE, r2.verdict)
check("AC2 exits 0", r2.exit_code == 0, str(r2.exit_code))

# AC3 - falling stress larger than tolerance is under-resolved, not admissible.
under = {
    "location": "synthetic under-resolved",
    "samples": [
        {"h": 0.09, "sigma_max": 400.0, "force": 5.0},
        {"h": 0.045, "sigma_max": 340.0, "force": 5.0},
    ],
}
r3 = gate.evaluate(under)
check("AC3 under-resolved -> INSUFFICIENT", r3.verdict == gate.INSUFFICIENT, r3.verdict)
check("AC3 classification is UNDER_RESOLVED", r3.pairs[0].kind == gate.UNDER_RESOLVED, r3.pairs[0].kind)

# AC4 - one sample is a result, not an error.
r4 = gate.evaluate({"location": "single", "samples": [{"h": 0.09, "sigma_max": 100.0, "force": 5.0}]})
check("AC4 single sample -> INSUFFICIENT", r4.verdict == gate.INSUFFICIENT, r4.verdict)

# AC5 - wrong refinement order is rejected.
try:
    gate.evaluate(
        {
            "location": "wrong order",
            "samples": [
                {"h": 0.045, "sigma_max": 100.0, "force": 5.0},
                {"h": 0.09, "sigma_max": 110.0, "force": 5.0},
            ],
        }
    )
    check("AC5 ascending h rejected", False, "no exception")
except gate.GateInputError:
    check("AC5 ascending h rejected", True, "GateInputError")

# Mismatched loads are rejected: sigma_hat is only comparable within one load case.
try:
    gate.evaluate(
        {
            "location": "two loads",
            "samples": [
                {"h": 0.09, "sigma_max": 100.0, "force": 5.0},
                {"h": 0.045, "sigma_max": 100.0, "force": 10.0},
            ],
        }
    )
    check("mismatched loads rejected", False, "no exception")
except gate.GateInputError:
    check("mismatched loads rejected", True, "GateInputError")

# AC6 - tolerance is a named constant, and is actually respected.
check(
    "AC6 tol is module constant",
    abs(gate.CONVERGENCE_TOL - 0.05) < 1e-12,
    str(gate.CONVERGENCE_TOL),
)
loose = gate.evaluate(load("z10_3_singularity.json"), tol=0.60)
check("AC6 raising tol to 60% flips the verdict", loose.verdict == gate.ADMISSIBLE, loose.verdict)

# R6 - closed-form critical force.
with_uts = gate.evaluate(load("synthetic_converged.json"), uts=1150.0)
check("R6 F_crit computed", with_uts.f_crit is not None, str(with_uts.f_crit))

failed = [c for c in checks if not c[1]]
width = max(len(c[0]) for c in checks)
for label, ok, detail in checks:
    print("%-*s  %s  %s" % (width, label, "PASS" if ok else "FAIL", detail))

print()
if failed:
    print("%d/%d checks failed" % (len(failed), len(checks)))
    sys.exit(1)
print("%d/%d checks passed" % (len(checks), len(checks)))
