#!/usr/bin/env python3
"""NORA logo system: faithful trace of the master logo, then assembly.

Source: refs/logo/nora-logo-black.jpg (white mark on black, supplied by Blake).
The mark is NOT redrawn. Each component is cropped from the source, upscaled,
thresholded at the midpoint between background and ink, and traced with
potrace. The hairline rule is a measured straight line, centred on the
wordmark axis (the only cleanup: it sat 5px right of centre in the source).

"SABAE · JAPAN" is the one piece that is set, not traced: its letters do not
exist in the source. It is set in Jost (OFL), converted to outlines, with
tracking solved so it matches the original descriptor's letter spacing.

Outputs
  src/assets/logo/parts/*.svg, manifest.json   traced components (source px)
  src/assets/logo/<application>-<ink>.svg      assembled logo files
  output/D2/svg/                               copies for delivery

Replace this trace with a designer's master file the moment one exists.
"""
import json
import pathlib
import shutil

import numpy as np
import potrace
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "refs/logo/nora-logo-black.jpg"
PARTS = ROOT / "src/assets/logo/parts"
LOGO = ROOT / "src/assets/logo"
DELIVER = ROOT / "output/D2/svg"
TOKENS = json.loads((ROOT / "src/tokens/tokens.json").read_text())
SCALE = 8  # upscale factor before tracing
BG = 10    # measured background value inside the logo panel

# Component boxes in source pixels (x0, y0, x1, y1), measured from the source.
BOXES = {
    "monogram": (300, 200, 535, 478),
    "wordmark": (305, 542, 529, 614),
    "descriptor": (312, 682, 522, 703),          # LUXURY EYEWEAR
    "descriptor_eyewear": (410, 682, 522, 703),  # EYEWEAR only (same pixels)
}
# Measured ink extents (source px).
MONO = dict(x0=307, x1=527, y0=208, y1=469)
WORD = dict(x0=313, x1=521, y0=549, y1=605)
DESC = dict(x0=319, x1=515, y0=687, y1=696)
EYEWEAR_X = (417, 516)
AXIS = (WORD["x0"] + WORD["x1"]) / 2          # 417, shared centre line
RULE_W = 229                                 # source rule spans x 308-536
RULE_Y = 509
RULE_H = 1.0
CAP_X = WORD["y1"] - WORD["y0"]              # X unit = wordmark cap height (56)


def trace(box, ink_max):
    img = Image.open(SRC).convert("L").crop(box)
    w, h = img.size
    big = img.resize((w * SCALE, h * SCALE), Image.LANCZOS)
    a = np.asarray(big, dtype=np.float32)
    threshold = BG + (ink_max - BG) / 2.0
    # potracer treats False as ink, so pass the inverted mask.
    bm = potrace.Bitmap(a <= threshold)
    plist = bm.trace(turdsize=4 * SCALE, alphamax=1.0, opticurve=True, opttolerance=0.2)
    s = 1.0 / SCALE
    ox, oy = box[0], box[1]

    def p(pt):
        return f"{ox + pt.x * s:.3f} {oy + pt.y * s:.3f}"

    d = []
    for curve in plist:
        d.append("M" + p(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner:
                d.append("L" + p(seg.c) + "L" + p(seg.end_point))
            else:
                d.append("C" + p(seg.c1) + " " + p(seg.c2) + " " + p(seg.end_point))
        d.append("Z")
    return "".join(d)


def set_text_outline(text, cap_px, target_width=None, ref_text=None, weight=350):
    """Set text in Jost as outlines. Tracking is solved so that ref_text,
    at the same cap height, spans target_width (matching the source)."""
    font = TTFont(ROOT / "src/assets/fonts/Jost-VF.ttf")
    font = instantiateVariableFont(font, {"wght": weight})
    upm = font["head"].unitsPerEm
    cap = font["OS/2"].sCapHeight
    scale = cap_px / cap
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    hmtx = font["hmtx"]

    def ink_width(s, track):
        # Left edge of first glyph's ink to right edge of last glyph's ink.
        names = [cmap[ord(c)] for c in s]
        x = sum(hmtx[n][0] + track for n in names[:-1])
        last = names[-1]
        right = x + hmtx[last][1] + _glyph_w(font, last)
        return (right - hmtx[names[0]][1]) * scale

    track = 0.0
    if target_width and ref_text:
        lo, hi = 0.0, upm * 2.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if ink_width(ref_text, mid) < target_width:
                lo = mid
            else:
                hi = mid
        track = lo
    names = [cmap[ord(c)] for c in text]
    pen = SVGPathPen(gs)
    x = -hmtx[names[0]][1]
    for n in names:
        tp = TransformPen(pen, (scale, 0, 0, -scale, x * scale, 0))
        gs[n].draw(tp)
        x += hmtx[n][0] + track
    width = ink_width(text, track)
    return pen.getCommands(), width, track / upm


def _glyph_w(font, name):
    g = font["glyf"][name]
    g.recalcBounds(font["glyf"])
    return (g.xMax - g.xMin) if g.numberOfContours else 0


def build_parts():
    PARTS.mkdir(parents=True, exist_ok=True)
    gray = np.asarray(Image.open(SRC).convert("L"), dtype=np.float32)
    parts = {}
    for name, box in BOXES.items():
        x0, y0, x1, y1 = box
        # EYEWEAR is cut from the same descriptor, so it shares its threshold.
        bx = BOXES["descriptor"] if name == "descriptor_eyewear" else box
        ink_max = float(gray[bx[1]:bx[3], bx[0]:bx[2]].max())
        d = trace(box, ink_max)
        parts[name] = {"box": box, "d": d, "source_ink_max": ink_max}
        (PARTS / f"{name}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1-x0} {y1-y0}">'
            f'<path fill="#fff" fill-rule="evenodd" d="{d}"/></svg>\n'
        )
        print(f"  traced {name}: source ink max {ink_max:.0f}")
    # SABAE · JAPAN, set to match the original descriptor.
    cap = DESC["y1"] - DESC["y0"] + 1
    d, w, track_em = set_text_outline(
        "SABAE · JAPAN", cap, target_width=DESC["x1"] - DESC["x0"] + 1,
        ref_text="LUXURY EYEWEAR")
    parts["descriptor_sabae"] = {"d": d, "width": w, "cap": cap, "tracking_em": track_em}
    print(f"  set SABAE · JAPAN in Jost 350, tracking {track_em:.3f}em, width {w:.1f}px")
    (PARTS / "manifest.json").write_text(json.dumps(parts, indent=1))
    return parts


# ---------- assembly ----------

def rule(y, ink, solid):
    op = "" if solid else f' fill-opacity="{TOKENS["logo"]["rule_opacity_on_screen"]}"'
    return (f'<rect x="{AXIS - RULE_W / 2:.2f}" y="{y - RULE_H / 2:.2f}" '
            f'width="{RULE_W}" height="{RULE_H}" fill="{ink}"{op}/>')


def path(d, ink, transform=None):
    t = f' transform="{transform}"' if transform else ""
    return f'<path fill="{ink}" fill-rule="evenodd" d="{d}"{t}/>'


def svg(view, body, title):
    x, y, w, h = view
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.2f} {y:.2f} {w:.2f} {h:.2f}" '
            f'width="{w:.2f}" height="{h:.2f}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{body}</svg>\n')


def applications(parts, ink, solid):
    P = parts
    mono = path(P["monogram"]["d"], ink)
    word = path(P["wordmark"]["d"], ink)
    left = AXIS - RULE_W / 2
    apps = {}
    # 1. Full lockups
    apps["lockup-luxury-eyewear"] = (
        (left, MONO["y0"], RULE_W, DESC["y1"] + 1 - MONO["y0"]),
        mono + rule(RULE_Y, ink, solid) + word + path(P["descriptor"]["d"], ink),
        "NORA lockup, descriptor LUXURY EYEWEAR (original)")
    apps["lockup-no-descriptor"] = (
        (left, MONO["y0"], RULE_W, WORD["y1"] + 1 - MONO["y0"]),
        mono + rule(RULE_Y, ink, solid) + word,
        "NORA lockup, no descriptor")
    dx = AXIS - (EYEWEAR_X[0] + EYEWEAR_X[1]) / 2
    apps["lockup-eyewear"] = (
        (left, MONO["y0"], RULE_W, DESC["y1"] + 1 - MONO["y0"]),
        mono + rule(RULE_Y, ink, solid) + word
        + path(P["descriptor_eyewear"]["d"], ink, f"translate({dx:.2f} 0)"),
        "NORA lockup, descriptor EYEWEAR")
    sab = P["descriptor_sabae"]
    sx = AXIS - sab["width"] / 2
    sy = DESC["y1"] + 1  # baseline
    apps["lockup-sabae-japan"] = (
        (left, MONO["y0"], RULE_W, DESC["y1"] + 1 - MONO["y0"]),
        mono + rule(RULE_Y, ink, solid) + word
        + path(sab["d"], ink, f"translate({sx:.2f} {sy:.2f})"),
        "NORA lockup, descriptor SABAE · JAPAN")
    # 2. Wordmark only
    apps["wordmark"] = ((WORD["x0"], WORD["y0"], WORD["x1"] + 1 - WORD["x0"], CAP_X + 1), word, "NORA wordmark")
    # 3. Monogram only
    apps["monogram"] = ((MONO["x0"], MONO["y0"], MONO["x1"] + 1 - MONO["x0"], MONO["y1"] + 1 - MONO["y0"]),
                        mono, "NORA monogram")
    # 4. Interior temple stamp: monogram | rule | wordmark on one line.
    mh = MONO["y1"] + 1 - MONO["y0"]
    mw = MONO["x1"] + 1 - MONO["x0"]
    k = (CAP_X * 1.6) / mh                     # monogram height = 1.6X
    gap = CAP_X * 0.9
    ww = WORD["x1"] + 1 - WORD["x0"]
    total_w = mw * k + gap * 2 + RULE_H + ww
    h = mh * k
    word_y = (h - (CAP_X + 1)) / 2
    op = "" if solid else f' fill-opacity="{TOKENS["logo"]["rule_opacity_on_screen"]}"'
    body = (f'<g transform="translate(0 0) scale({k:.5f}) translate({-MONO["x0"]} {-MONO["y0"]})">{mono}</g>'
            f'<rect x="{mw * k + gap:.2f}" y="{h * 0.15:.2f}" width="{RULE_H}" height="{h * 0.7:.2f}" fill="{ink}"{op}/>'
            f'<g transform="translate({mw * k + gap * 2 + RULE_H:.2f} {word_y:.2f}) translate({-WORD["x0"]} {-WORD["y0"]})">{word}</g>')
    apps["temple-stamp"] = ((0, 0, total_w, h), body, "NORA interior temple stamp")
    return apps


def main():
    print("logo: tracing master")
    parts = build_parts()
    c = TOKENS["color"]
    inks = {
        "white": (c["white"]["hex"], False),     # white on black
        "black": (c["black"]["hex"], False),     # black on white
        "violet": (c["violet"]["hex"], False),   # violet on black, limited use
        "single": (c["black"]["hex"], True),     # one flat colour: deboss, engrave, foil
    }
    DELIVER.mkdir(parents=True, exist_ok=True)
    index = []
    for ink_name, (hexv, solid) in inks.items():
        for app, (view, body, title) in applications(parts, hexv, solid).items():
            name = f"{app}-{ink_name}"
            (LOGO / f"{name}.svg").write_text(svg(view, body, f"{title} ({ink_name})"))
            shutil.copy(LOGO / f"{name}.svg", DELIVER / f"{name}.svg")
            index.append({"file": name, "app": app, "ink": ink_name, "w": view[2], "h": view[3]})
    (LOGO / "index.json").write_text(json.dumps(index, indent=1))
    print(f"logo: wrote {len(index)} SVGs")


if __name__ == "__main__":
    main()
