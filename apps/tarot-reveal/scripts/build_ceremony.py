"""STUB — Phase 2. Assemble Victory Draw / Death Draw onto 'AI Jester Timeline'.

Not implemented yet. Planned shape:

    python apps/tarot-reveal/scripts/build_ceremony.py victory --numbers 3 9 13 --winner 9
    python apps/tarot-reveal/scripts/build_ceremony.py death   --number 13

victory: places 3 generated comps (fusion/generated/<n>-*.comp) as back-facing
clips on the contract timeline; the --winner card's Transform3D_Flip is what
plays (the other two stay reversed/back-up, never flipped in this ceremony);
status/text stay RELIC (as generated).

death: places 1 generated comp, but overrides at placement time:
  - Transform3D_Orient.Z = 180   (reversed)
  - Text_Status.StyledText = "CURSE"
  - Text_Effect.StyledText = card.curse_text   (not relic_text)

Both need: resolve.GetMediaPool().AppendToTimeline-equivalent for Fusion
comps (Fusion Clip import), and the timeline_read.py layout helpers from
apps/resolve-agent to find a safe record-frame insertion point — reuse those,
don't reimplement. Left unimplemented pending your OK on Phase 1
(generate_reveals.py) actually producing usable comps first.
"""

raise SystemExit(
    "build_ceremony.py: not implemented yet — Phase 2, after Phase 1 is verified."
)
