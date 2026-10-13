# NORA Eyewear: brand system

The brand package is built as code: HTML, CSS and SVG are the source, and Chromium exports them to PDF and PNG. The rules the package follows are in `CLAUDE.md`.

## Rebuild everything

```
npm install
pip install potracer fonttools brotli numpy pillow
npm run build
```

`npm run build` runs four steps in order:

1. **tokens** (`scripts/build-tokens.mjs`): turns `src/tokens/tokens.json` into `tokens.css` and `tokens.js`, and computes the contrast ratios.
2. **logo** (`scripts/build-logo.py`): traces the master logo from `refs/logo/nora-logo-black.jpg`, then assembles every lockup in every color.
3. **check** (`scripts/check-trace.mjs`): compares the trace with the source pixel by pixel.
4. **export** (`scripts/export.mjs`): writes logo PNGs (@1x/@2x/@4x) and PDFs, plus one PDF and per-page PNGs for each page in `src/pages`.

To export a single page file, run `node scripts/export.mjs D4`.

## Where things are

| Path | What |
|---|---|
| `refs/` | Inputs from Blake. Never edited. |
| `src/tokens/tokens.json` | The single source of truth for colors, type and spacing. Edit here only. |
| `src/assets/logo/` | Assembled logo SVGs, the traced parts, and the trace check |
| `src/assets/fonts/` | Cormorant Garamond and Jost (OFL), as TTF and WOFF2 |
| `src/assets/patterns/leopard.js` | The original procedural leopard pattern |
| `src/pages/` | One HTML file per deliverable |
| `output/D2`, `D4`, `D5` | Final logo files and documents |
| `output/checkpoint-1/` | Graphic-device proposals, pending approval |
| `output/previews/` | PNG previews for checkpoint review |

## Status

- **Phase 1 (logo, color, type, devices):** built. Waiting at Checkpoint 1.
- **Logo:** traced from a roughly 220 px source. A designer's master file should replace the trace when one exists.
