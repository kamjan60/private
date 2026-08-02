# Attribution

`reference/*.md` in this directory is condensed/adapted from the skill
documentation in [`willibrandon/pixel-plugin`](https://github.com/willibrandon/pixel-plugin)
(specifically `skills/pixel-art-professional/`, `skills/pixel-art-animator/`,
and `skills/pixel-art-creator/`).

That plugin drives real Aseprite through an MCP server (`pixel-mcp`) and
requires Aseprite to be installed — the *tool* isn't usable here. Only the
tool-agnostic technique knowledge (color theory, dithering patterns,
animation timing tables, common sprite dimensions) was pulled out and
rewritten to stand alone, for use with the plain PIL helpers in
`pixel_lib.py` instead of Aseprite's MCP tools.

Original license (MIT):

```
MIT License

Copyright (c) 2025 Brandon Williams

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```


## Update, 2026-08

The technique notes in `reference/` began as a distillation of that plugin's
prose. They have since been rewritten around the pipeline actually used
here — plotting pixels with Pillow, deterministic LCG seeding, sheet index
contracts, and baked interior lighting — and the rules in the two skills
(`fantasy-pixel-art`, `spell-fx`) are now derived from mistakes made and
fixed in this repository rather than from the original text. The MIT notice
above still stands for what was borrowed.
