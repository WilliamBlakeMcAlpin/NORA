// NORA leopard: an original procedural pattern (no stock imagery).
// Broken rosettes on a jittered grid, drawn from a seeded random generator
// so the same seed always gives the same pattern.
// Usage: NORA_LEOPARD.svg({ width, height, seed, scale, colors })
(function () {
  function rng(seed) {
    let s = seed >>> 0 || 1;
    return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  }

  // An irregular closed blob around (cx, cy).
  function blob(r, cx, cy, rx, ry, rot, wob) {
    const n = 9, pts = [];
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const k = 1 + (r() - 0.5) * wob;
      const x = Math.cos(a) * rx * k, y = Math.sin(a) * ry * k;
      pts.push([cx + x * Math.cos(rot) - y * Math.sin(rot), cy + x * Math.sin(rot) + y * Math.cos(rot)]);
    }
    let d = '';
    for (let i = 0; i < n; i++) {
      const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
      if (i === 0) d += `M${p1[0].toFixed(1)} ${p1[1].toFixed(1)}`;
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += `C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
    }
    return d + 'Z';
  }

  function svg({ width = 800, height = 800, seed = 16519, scale = 1, colors } = {}) {
    const t = (window.NORA_TOKENS && window.NORA_TOKENS.leopard) || {};
    const c = Object.assign({ ground: t.ground || '#3A2617', mid: t.mid || '#6B4526', spot: t.spot || '#120C08' }, colors || {});
    const r = rng(seed);
    const cell = 64 * scale;
    let mids = '', spots = '';
    for (let gy = -1; gy < height / cell + 1; gy++) {
      for (let gx = -1; gx < width / cell + 1; gx++) {
        const cx = (gx + 0.5 + (gy % 2) * 0.5 + (r() - 0.5) * 0.5) * cell;
        const cy = (gy + 0.5 + (r() - 0.5) * 0.5) * cell;
        const R = cell * (0.26 + r() * 0.1);
        const rot = r() * Math.PI;
        mids += `<path d="${blob(r, cx, cy, R * 0.8, R * 0.65, rot, 0.3)}"/>`;
        // broken ring: 3 to 5 fragments around the center
        const n = 4 + Math.floor(r() * 3);
        const off = r() * Math.PI * 2;
        for (let i = 0; i < n; i++) {
          if (r() < 0.12) continue; // occasional gap
          const a = off + (i / n) * Math.PI * 2 + (r() - 0.5) * 0.4;
          const fx = cx + Math.cos(a) * R, fy = cy + Math.sin(a) * R * 0.85;
          const len = (Math.PI * 2 * R / n) * (0.36 + r() * 0.1);
          spots += `<path d="${blob(r, fx, fy, len, len * (0.3 + r() * 0.12), a + Math.PI / 2, 0.35)}"/>`;
        }
        if (r() < 0.35) { // loose small spot
          const sx = cx + (r() - 0.5) * cell, sy = cy + (r() - 0.5) * cell, s = cell * 0.06 * (1 + r());
          spots += `<path d="${blob(r, sx, sy, s, s * 0.8, r() * 3, 0.5)}"/>`;
        }
      }
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid slice">
<rect width="100%" height="100%" fill="${c.ground}"/>
<g fill="${c.mid}" opacity="0.7">${mids}</g>
<g fill="${c.spot}">${spots}</g></svg>`;
  }

  window.NORA_LEOPARD = { svg };
})();
