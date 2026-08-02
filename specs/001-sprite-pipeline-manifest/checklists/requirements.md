# Specification Quality Checklist: Manifest sprite'ów i warstwa nieoświetlana

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-02
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

Passed on the first pass; no rewrite iterations were needed.

**The trap this feature walks into, avoided deliberately.** The request
arrived already carrying its own answer — JSON manifest, file named
`hunters.json`, the row formula, RSI. Written down as requirements, those
would be a plan wearing a spec's clothes: the solution decided before the
problem is stated. So every requirement here states an outcome and leaves
the format open — "opis maszynowo-czytelny" rather than JSON, "nazwa
stanu" rather than a filename, "zestaw testów wykrywa niezgodność" rather
than a named assertion. The SS14 / RSI lineage sits in Assumptions, where
a borrowed precedent belongs, instead of in the requirements, where it
would read as a mandate.

**Deliberately kept, despite looking like implementation detail:**

- SC-004's "trzykrotnie jaśniejszy" — a number, but a *user-observable*
  one. "Widać, że świeci" is not testable, and the whole point of the
  second story is that today the ratio is 1.0.
- SC-007's 5 KB — the single-file build is a real delivery constraint,
  because that is how the game reaches a phone.

**No [NEEDS CLARIFICATION] markers.** Three candidates were considered and
all three had a defensible default, recorded in Assumptions rather than
asked:

1. Whether department colour bands replace the per-class glow accents.
   Default: they do not — bands cover the coat only. Keeps the change
   reversible and leaves the UI legible.
2. Whether "in hand" means carrying or actively using. Default: it appears
   for the duration of a use or channel, since that is the distinction with
   evidentiary value.
3. Whether stages 3–5 ship together with 1–2. Default: no. The user said
   1 and 2 first, and stated the rest were "dalsze etapy".

**One thing the spec asserts that is worth challenging at planning time**:
FR-012 (the emissive layer must still obey invisibility). It is written as
a constraint because getting it wrong silently breaks Cień — an unshaded
layer that ignores dimming will, if implemented naively, also ignore alpha,
and the mage's own spell would give away his position in exactly the dark
where he needs it.
