"""Connect to Resolve's Fusion object and the active comp.

Reuses grimcader.resolve_conn.connect() (apps/resolve-agent) for the Resolve
handshake — same Studio-only External Scripting requirement, same env vars.

Fusion page must be open in Resolve with a comp active (e.g. a Fusion Clip or
Fusion Title dropped on a timeline) before GetCurrentComp() returns anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

_RESOLVE_AGENT = Path(__file__).resolve().parents[3] / "resolve-agent"
if str(_RESOLVE_AGENT) not in sys.path:
    sys.path.insert(0, str(_RESOLVE_AGENT))

from grimcader.resolve_conn import connect  # noqa: E402


def get_fusion():
    resolve = connect()
    fusion = resolve.Fusion()
    if fusion is None:
        raise RuntimeError("resolve.Fusion() returned None — is Resolve running?")
    return fusion


def get_current_comp():
    """Return the comp active in the Fusion page, or raise a clear error."""
    fusion = get_fusion()
    comp = fusion.GetCurrentComp()
    if comp is None:
        raise RuntimeError(
            "No active comp. Open the Fusion page on a Fusion Clip/Title "
            "(e.g. a placeholder dropped on 'AI Jester Timeline') first."
        )
    return comp


def dump_inputs(tool) -> None:
    """Debug helper: print a tool's input IDs. Use this to confirm exact input
    names in your Resolve/Fusion version before trusting the guessed IDs in
    template_build.py (Transform3D/ImagePlane3D input names vary by version).
    """
    for name in tool.GetInputList():
        inp = tool.GetInputList()[name]
        print(f"  {inp.GetAttrs('INPS_ID')!r}  ({inp.GetAttrs('INPS_Name')!r})")
