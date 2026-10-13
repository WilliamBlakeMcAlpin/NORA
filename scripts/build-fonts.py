#!/usr/bin/env python3
"""Static font instances from the variable OFL fonts.

Chromium embeds variable fonts in PDFs as Type 3 outlines, which some print
shops reject. Static instances embed as normal TrueType, so print PDFs stay
clean. Run once after updating the variable fonts; outputs are committed.
"""
import pathlib

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

F = pathlib.Path(__file__).resolve().parent.parent / "src/assets/fonts"
JOBS = [
    ("CormorantGaramond-VF.ttf", "CormorantGaramond", [300, 400, 500]),
    ("CormorantGaramond-Italic-VF.ttf", "CormorantGaramond-Italic", [300, 400]),
    ("Jost-VF.ttf", "Jost", [400, 500]),
]
for src, stem, weights in JOBS:
    for w in weights:
        f = instantiateVariableFont(TTFont(F / src), {"wght": w}, updateFontNames=True)
        out = F / "static" / f"{stem}-{w}.ttf"
        out.parent.mkdir(exist_ok=True)
        f.save(out)
        f.flavor = "woff2"
        f.save(out.with_suffix(".woff2"))
        print("fonts:", out.name)
