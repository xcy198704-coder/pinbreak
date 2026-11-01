#!/usr/bin/env python3
"""Convergence gate for linear-elastic stress peaks.

Decides whether a stress peak from a mesh-refinement study is a real stress
concentration or a contact-edge / re-entrant-corner singularity, and therefore
whether it may be reported at all.

The criterion implemented here is RULE 2 of .kiro/steering/conventions.md,
registered 2026-11-01 before the first sweep of this project ran:

    delta = |(sigma_hat(h/2) - sigma_hat(h)) / sigma_hat(h)|

    delta <= tol                      -> CONVERGED      peak admissible
    sigma_hat rises and delta > tol   -> SINGULARITY    peak inadmissible
    sigma_hat falls and delta > tol   -> UNDER_RESOLVED refine further

Because the model is linear elastic, sigma = F * sigma_hat, so sigma_hat is
independent of the applied load and is a property of mesh and geometry alone.
That is what makes it a legitimate convergence metric, and it also gives the
critical force in closed form: F_crit = sigma_uts / sigma_hat.

No third-party imports. Python 3.9+.

Exit codes:
    0  admissible, or insufficient data (a valid result, not a fault)
    1  inadmissible - the peak must not be reported
    2  invalid input (refinement order, mismatched loads, unreadable file)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Registered threshold. Do not inline this number anywhere else (RULE 1, AC6).
CONVERGENCE_TOL = 0.05

# Samples must share the applied load, because sigma_hat is only comparable
# across identical load cases.
FORCE_RTOL = 1e-9

CONVERGED = "CONVERGED"
SINGULARITY = "SINGULARITY"
UNDER_RESOLVED = "UNDER_RESOLVED"

ADMISSIBLE = "ADMISSIBLE"
INADMISSIBLE = "INADMISSIBLE"
INSUFFICIENT = "INSUFFICIENT"

EXIT_OK = 0
EXIT_INADMISSIBLE = 1
EXIT_INVALID = 2


class GateInputError(ValueError):
    """Input cannot be evaluated at all - distinct from a negative verdict."""


@dataclass(frozen=True)
class Sample:
    h: float
    sigma_max: float
    force: float

    @property
    def sigma_hat(self) -> float:
        if self.force == 0.0:
            raise GateInputError("force must be non-zero")
        return self.sigma_max / self.force


@dataclass(frozen=True)
class PairResult:
    coarse: Sample
    fine: Sample
    delta: float
    kind: str

    @property
    def delta_pct(self) -> float:
        return 100.0 * self.delta


@dataclass(frozen=True)
class GateResult:
    location: str
    verdict: str
    pairs: tuple
    residual_pct: float
    f_crit: float | None

    @property
    def exit_code(self) -> int:
        return EXIT_INADMISSIBLE if self.verdict == INADMISSIBLE else EXIT_OK


def classify_pair(coarse: Sample, fine: Sample, tol: float = CONVERGENCE_TOL) -> PairResult:
    """Classify one refinement step. Direction of the change is the whole test."""
    s_coarse = coarse.sigma_hat
    s_fine = fine.sigma_hat
    delta = abs((s_fine - s_coarse) / s_coarse)

    if delta <= tol:
        kind = CONVERGED
    elif s_fine > s_coarse:
        # Rising stress under refinement: no limit exists. Refinement is the
        # diagnostic, not the cure. Extrapolating would invent a number.
        kind = SINGULARITY
    else:
        kind = UNDER_RESOLVED

    return PairResult(coarse=coarse, fine=fine, delta=delta, kind=kind)


def evaluate(doc: dict, tol: float = CONVERGENCE_TOL, uts: float | None = None) -> GateResult:
    """Evaluate one hotspot described by a JSON document."""
    location = str(doc.get("location") or "unspecified hotspot")
    raw = doc.get("samples") or []

    samples = []
    for i, item in enumerate(raw):
        try:
            samples.append(
                Sample(
                    h=float(item["h"]),
                    sigma_max=float(item["sigma_max"]),
                    force=float(item["force"]),
                )
            )
        except KeyError as exc:
            raise GateInputError(f"sample {i} missing field {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise GateInputError(f"sample {i} is not numeric: {exc}") from exc

    if not samples:
        raise GateInputError("no samples supplied")

    # Sample i+1 must be finer than sample i.
    for prev, cur in zip(samples, samples[1:]):
        if not cur.h < prev.h:
            raise GateInputError(
                f"refinement order violated: h={cur.h} does not follow h={prev.h} "
                "(samples must be ordered coarse to fine)"
            )

    ref_force = samples[0].force
    for s in samples[1:]:
        if abs(s.force - ref_force) > FORCE_RTOL * max(abs(ref_force), 1.0):
            raise GateInputError(
                f"samples use different loads ({ref_force} vs {s.force}); "
                "normalised stress is only comparable within one load case"
            )

    if len(samples) < 2:
        return GateResult(location, INSUFFICIENT, (), 0.0, None)

    pairs = tuple(classify_pair(a, b, tol) for a, b in zip(samples, samples[1:]))

    # A singularity outranks later convergence: a peak that diverges does not
    # become physical because a coarser-to-finer step later settled down.
    if any(p.kind == SINGULARITY for p in pairs):
        verdict = INADMISSIBLE
    elif pairs[-1].kind == CONVERGED:
        verdict = ADMISSIBLE
    else:
        verdict = INSUFFICIENT

    f_crit = None
    sigma_uts = uts if uts is not None else doc.get("sigma_uts")
    if sigma_uts is not None:
        f_crit = float(sigma_uts) / samples[-1].sigma_hat

    return GateResult(
        location=location,
        verdict=verdict,
        pairs=pairs,
        residual_pct=pairs[-1].delta_pct,
        f_crit=f_crit,
    )


def format_report(result: GateResult) -> str:
    lines = []
    lines.append(f"hotspot : {result.location}")
    if not result.pairs:
        lines.append("samples : 1 - no refinement pair, nothing can be classified")
        lines.append(f"verdict : {result.verdict}")
        return "\n".join(lines)

    lines.append("")
    lines.append("  h coarse    h fine    sigma_hat c   sigma_hat f   delta      class")
    lines.append("  " + "-" * 70)
    for p in result.pairs:
        lines.append(
            "  %-11.4f %-9.4f %-13.4f %-13.4f %-10s %s"
            % (
                p.coarse.h,
                p.fine.h,
                p.coarse.sigma_hat,
                p.fine.sigma_hat,
                "%.2f%%" % p.delta_pct,
                p.kind,
            )
        )

    lines.append("")
    lines.append(f"residual mesh sensitivity : {result.residual_pct:.2f}%")
    if result.f_crit is not None:
        lines.append(f"F_crit (closed form)      : {result.f_crit:.4g} N")
    lines.append(f"verdict                   : {result.verdict}")

    if result.verdict == INADMISSIBLE:
        worst = max(result.pairs, key=lambda p: p.delta)
        lines.append("")
        lines.append(
            "REFUSED: stress rises by %.1f%% under refinement at h=%.4f -> %.4f."
            % (worst.delta_pct, worst.coarse.h, worst.fine.h)
        )
        lines.append(
            "No limit exists for this peak. Report the converged band, not this value."
        )
    elif result.verdict == ADMISSIBLE:
        lines.append("")
        lines.append("Peak accepted: converged within %.2f%%." % (100 * CONVERGENCE_TOL))

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Decide whether a stress peak is a real feature or a mesh artifact."
    )
    parser.add_argument("document", help="JSON hotspot description")
    parser.add_argument("--uts", type=float, default=None, help="override ultimate tensile strength (MPa)")
    parser.add_argument(
        "--tol",
        type=float,
        default=CONVERGENCE_TOL,
        help="override convergence tolerance (default %(default)s)",
    )
    args = parser.parse_args(argv)

    path = Path(args.document)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_INVALID
    except json.JSONDecodeError as exc:
        print(f"error: {path} is not valid JSON: {exc}", file=sys.stderr)
        return EXIT_INVALID

    try:
        result = evaluate(doc, tol=args.tol, uts=args.uts)
    except GateInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INVALID

    print(format_report(result))
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
