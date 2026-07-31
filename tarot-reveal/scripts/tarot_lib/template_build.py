"""Build the CardReveal node graph in a Fusion comp.

Rig (single rigid "card" flips as one body, front+back glued back-to-back —
only one face is ever pointed at the camera):

    Loader_Front -> ImagePlane3D_Front --\\
                                           Merge3D1 -> Transform3D_Flip -> Transform3D_Orient -> Renderer3D1 --\\
    Loader_Back  -> ImagePlane3D_Back  --/                                   Camera3D1 --------------------/     \\
                                                                                                                    Merge2D chain
    TextPlus_Name -> TextPlus_Status -> TextPlus_Effect  (2D overlays, composited after the 3D render)  ----------/ -> MediaOut1

Transform3D_Flip's Y rotation is the only keyframed value: 180 (back facing
camera) -> 0 (front facing camera). Transform3D_Orient's Z rotation is a
STATIC per-ceremony value set after building: 0 = Upright/relic, 180 =
Reversed/curse. generate_reveals.py only ever touches Loader_Front's Clip
and the 3 TextPlus StyledText fields — it never re-keyframes the flip.

Tool/input IDs below were confirmed live against Resolve/Fusion (2026-07-26)
via tarot_lib.fusion_conn.dump_inputs — notably ImagePlane3D has no plain
"Image" input; the 2D source connects into "MaterialInput" and Fusion
auto-wraps it. Camera connects into Renderer3D's "CameraSelector", not
"ActiveCamera3D". Rotation fields are flat dotted IDs
("Transform3DOp.Rotate.Y"), not a nested attribute object with .X/.Y/.Z.

Node x/y in AddTool are Fusion flow-grid units (~1 = one node width/height),
not pixels — the first pass used pixel-scale offsets (200-400 apart) and
produced a wildly spread-out graph; confirmed live that small integers give
a normal, tight layout.
"""

from __future__ import annotations

FLIP_START_FRAME = 0
FLIP_END_FRAME = 24  # 24 frames @ default fps; adjust to taste
TEXT_SIZE = 0.035  # confirmed live: TextPlus default (0.08) reads oversized in this comp

TOOL = {
    "loader": "Loader",
    "image_plane_3d": "ImagePlane3D",
    "merge_3d": "Merge3D",
    "transform_3d": "Transform3D",
    "camera_3d": "Camera3D",
    "renderer_3d": "Renderer3D",
    "text_plus": "TextPlus",
    "merge_2d": "Merge",
}

INPUT = {
    "loader_clip": "Clip",
    "image_plane_material": "MaterialInput",
    "merge3d_scene_a": "SceneInput1",
    "merge3d_scene_b": "SceneInput2",
    "transform_scene_input": "SceneInput",
    "transform_rotate_x": "Transform3DOp.Rotate.X",
    "transform_rotate_y": "Transform3DOp.Rotate.Y",
    "transform_rotate_z": "Transform3DOp.Rotate.Z",
    "renderer_scene_input": "SceneInput",
    "renderer_camera": "CameraSelector",
    "text_styled_text": "StyledText",
    "merge2d_background": "Background",
    "merge2d_foreground": "Foreground",
}


def build_card_reveal_comp(comp, front_image_path: str, back_image_path: str):
    """Construct the rig described above in `comp` (a fresh or current Fusion
    comp). Returns a dict of named tool handles the caller needs to touch
    per-card (front loader + the 3 text tools) or per-ceremony (orient
    transform).
    """
    comp.Lock()
    try:
        loader_front = comp.AddTool(TOOL["loader"], 0, 0)
        loader_front.SetAttrs({"TOOLS_Name": "Loader_Front"})
        loader_front[INPUT["loader_clip"]] = front_image_path

        loader_back = comp.AddTool(TOOL["loader"], 0, 1)
        loader_back.SetAttrs({"TOOLS_Name": "Loader_Back"})
        loader_back[INPUT["loader_clip"]] = back_image_path

        plane_front = comp.AddTool(TOOL["image_plane_3d"], 1, 0)
        plane_front.SetAttrs({"TOOLS_Name": "Plane_Front"})
        plane_front[INPUT["image_plane_material"]] = loader_front

        plane_back = comp.AddTool(TOOL["image_plane_3d"], 1, 1)
        plane_back.SetAttrs({"TOOLS_Name": "Plane_Back"})
        plane_back[INPUT["image_plane_material"]] = loader_back
        # Back plane faces away by default; rotate 180 on Y so it's glued
        # back-to-back with the front plane rather than overlapping it.
        plane_back[INPUT["transform_rotate_y"]] = 180

        merge3d = comp.AddTool(TOOL["merge_3d"], 2, 0.5)
        merge3d.SetAttrs({"TOOLS_Name": "Merge3D_Card"})
        merge3d[INPUT["merge3d_scene_a"]] = plane_front
        merge3d[INPUT["merge3d_scene_b"]] = plane_back

        flip = comp.AddTool(TOOL["transform_3d"], 3, 0.5)
        flip.SetAttrs({"TOOLS_Name": "Transform3D_Flip"})
        flip[INPUT["transform_scene_input"]] = merge3d
        # Static rest value only — NOT animated here. comp.BezierSpline() /
        # SetInput(value, time) do not reliably attach a keyframed spline to
        # a nested dotted input from script (confirmed live: creates an
        # orphan disconnected BezierSpline tool instead). Keyframe this by
        # hand in the Fusion UI (select the tool, right-click the Y
        # Rotation field -> Animate, set 180 at frame 0 and 0 at frame 24).
        # generate_reveals.py's real batch strategy is to DUPLICATE a
        # verified hand-keyframed template comp per card rather than
        # rebuild the animation from script each time.
        flip[INPUT["transform_rotate_y"]] = 180

        orient = comp.AddTool(TOOL["transform_3d"], 4, 0.5)
        orient.SetAttrs({"TOOLS_Name": "Transform3D_Orient"})
        orient[INPUT["transform_scene_input"]] = flip
        orient[INPUT["transform_rotate_z"]] = 0  # Upright default; ceremony sets 180 for Reversed

        camera = comp.AddTool(TOOL["camera_3d"], 4, 2)
        camera.SetAttrs({"TOOLS_Name": "Camera3D_Card"})

        renderer = comp.AddTool(TOOL["renderer_3d"], 5, 1)
        renderer.SetAttrs({"TOOLS_Name": "Renderer3D_Card"})
        renderer[INPUT["renderer_scene_input"]] = orient
        renderer[INPUT["renderer_camera"]] = camera

        text_name = comp.AddTool(TOOL["text_plus"], 5, 2)
        text_name.SetAttrs({"TOOLS_Name": "Text_CardName"})
        text_name["Size"] = TEXT_SIZE

        text_status = comp.AddTool(TOOL["text_plus"], 6, 2.3)
        text_status.SetAttrs({"TOOLS_Name": "Text_Status"})
        text_status["Size"] = TEXT_SIZE

        text_effect = comp.AddTool(TOOL["text_plus"], 7, 2.6)
        text_effect.SetAttrs({"TOOLS_Name": "Text_Effect"})
        text_effect["Size"] = TEXT_SIZE

        # Merge's own Center repositions its Foreground within the frame —
        # without this all 3 text layers default-stack at dead center.
        merge_a = comp.AddTool(TOOL["merge_2d"], 6, 1.3)
        merge_a.SetAttrs({"TOOLS_Name": "Merge_CardName"})
        merge_a[INPUT["merge2d_background"]] = renderer
        merge_a[INPUT["merge2d_foreground"]] = text_name
        merge_a["Center"] = {1: 0.5, 2: 0.85}

        merge_b = comp.AddTool(TOOL["merge_2d"], 7, 1.6)
        merge_b.SetAttrs({"TOOLS_Name": "Merge_Status"})
        merge_b[INPUT["merge2d_background"]] = merge_a
        merge_b[INPUT["merge2d_foreground"]] = text_status
        merge_b["Center"] = {1: 0.5, 2: 0.75}

        merge_c = comp.AddTool(TOOL["merge_2d"], 8, 1.9)
        merge_c.SetAttrs({"TOOLS_Name": "Merge_Effect"})
        merge_c[INPUT["merge2d_background"]] = merge_b
        merge_c[INPUT["merge2d_foreground"]] = text_effect
        merge_c["Center"] = {1: 0.5, 2: 0.15}

        media_out = comp.FindTool("MediaOut1") or comp.AddTool("MediaOut", 9, 1.9)
        media_out.SetAttrs({"TOOLS_Name": "MediaOut1"})
        media_out.Input = merge_c
    finally:
        comp.Unlock()

    return {
        "loader_front": loader_front,
        "loader_back": loader_back,
        "transform_orient": orient,
        "text_name": text_name,
        "text_status": text_status,
        "text_effect": text_effect,
        "media_out": media_out,
    }
