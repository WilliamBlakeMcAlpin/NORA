// Export everything with Chromium (Playwright):
//  - logo SVGs  -> transparent PNG @1x/@2x/@4x + vector PDF   (output/D2/png, output/D2/pdf)
//  - pages      -> one PDF per page file + a PNG per .page section (output/<D>/, output/previews/)
// A page file declares:  <meta name="nora-page" content="1600x1000">  (CSS px per page)
//                        <meta name="nora-output" content="D2">
// Usage: node scripts/export.mjs [filter]   (filter matches page file names)
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const filter = process.argv[2] || '';
const exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const browser = await chromium.launch(fs.existsSync(exe) ? { executablePath: exe } : {});
const mk = (p) => fs.mkdirSync(p, { recursive: true });

// ---------- logo files ----------
const BASE_1X = { 'temple-stamp': ['w', 400], monogram: ['h', 256], wordmark: ['w', 400] };
async function exportLogos() {
  const index = JSON.parse(fs.readFileSync(path.join(root, 'src/assets/logo/index.json'), 'utf8'));
  const png = path.join(root, 'output/D2/png'); const pdf = path.join(root, 'output/D2/pdf');
  mk(png); mk(pdf);
  const page = await browser.newPage();
  for (const item of index) {
    const [axis, size] = BASE_1X[item.app] || ['w', 400];
    const k = axis === 'w' ? size / item.w : size / item.h;
    const w = Math.round(item.w * k), h = Math.round(item.h * k);
    const svgUrl = 'file://' + path.join(root, 'src/assets/logo', item.file + '.svg');
    const html = `<html><body style="margin:0;background:transparent">
      <img src="${svgUrl}" style="display:block;width:${w}px;height:${h}px"></body></html>`;
    for (const scale of [1, 2, 4]) {
      await page.setViewportSize({ width: w, height: h });
      const ctx = await browser.newContext({ deviceScaleFactor: scale, viewport: { width: w, height: h } });
      const p = await ctx.newPage();
      await p.setContent(html); await p.waitForLoadState('load');
      await p.screenshot({ path: path.join(png, `${item.file}@${scale}x.png`), omitBackground: true });
      await ctx.close();
    }
    await page.setContent(html); await page.waitForLoadState('load');
    await page.pdf({ path: path.join(pdf, `${item.file}.pdf`), width: `${w}px`, height: `${h}px`,
      printBackground: false, pageRanges: '1' });
  }
  await page.close();
  console.log(`export: ${index.length} logo files -> PNG @1x/@2x/@4x + PDF`);
}

// ---------- pages ----------
async function exportPages() {
  const dir = path.join(root, 'src/pages');
  const files = fs.readdirSync(dir).filter((f) => f.endsWith('.html') && f.includes(filter) && !f.startsWith('_'));
  for (const f of files) {
    const src = fs.readFileSync(path.join(dir, f), 'utf8');
    const size = (src.match(/name="nora-page" content="(\d+)x(\d+)"/) || []).slice(1).map(Number);
    const out = (src.match(/name="nora-output" content="([^"]+)"/) || [])[1];
    if (!size.length || !out) { console.log(`export: skip ${f} (no nora-page/nora-output meta)`); continue; }
    const [w, h] = size;
    const name = f.replace(/\.html$/, '');
    const outDir = path.join(root, 'output', out); mk(path.join(outDir, 'png')); mk(path.join(root, 'output/previews'));
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    await page.goto('file://' + path.join(dir, f));
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    const sections = await page.$$('.page');
    for (let i = 0; i < sections.length; i++) {
      const n = String(i + 1).padStart(2, '0');
      const file = `${name}-p${n}.png`;
      await sections[i].screenshot({ path: path.join(outDir, 'png', file) });
      fs.copyFileSync(path.join(outDir, 'png', file), path.join(root, 'output/previews', file));
    }
    await page.emulateMedia({ media: 'print' });
    await page.pdf({ path: path.join(outDir, `${name}.pdf`), width: `${w}px`, height: `${h}px`, printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 } });
    await ctx.close();
    console.log(`export: ${f} -> output/${out}/${name}.pdf + ${sections.length} PNG`);
  }
}

if (!filter) await exportLogos();
await exportPages();
await browser.close();
