---
inclusion: always
---

# Product context

`pinbreak` answers one question for a hardware engineer: **at what force does this contact pin
break, and is that number defensible?**

## Who it is for

An engineer preparing a design review, not a simulation specialist. They have a parametric part
(tip radius, head radius, waist fillet, bore depth, wall thickness), a material certificate, and
a test bench that gives a force range rather than a precise fracture load. They need to know
whether a design change is required, and they need to be able to defend the answer when
challenged.

## What it must do

1. Turn a parameter set into solver decks without hand editing.
2. Sweep element size, geometry, and load direction across cases, tracked in a manifest.
3. Extract per-increment surface displacement and von Mises stress from solver output.
4. **Refuse to report a peak that fails the convergence gate.**
5. Emit a single self-contained HTML report a reviewer can open with no tooling.

## What it must not do

- It must not report a stress peak without a stated mesh-convergence status.
- It must not silently substitute a mock or synthetic value for a measured one.
- It must not present a conclusion that the pre-registered criteria do not support.

## The precedent this project is built on

A bore-edge peak of 3274 MPa was reported by a fine mesh on a pin that in reality fractures near
21 N. The peak was a contact-edge singularity. It was caught only because a falsification rule
had been written down before the sweep ran. Everything in this repository exists so that rule is
executed by code rather than remembered by a person.
