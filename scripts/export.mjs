// 인포그래픽 HTML → PNG(3배) + 길이 · 넘침 점검. 브라우저는 한 번만 띄우고 여러 파일을 차례로 처리.
// 사용: node export.mjs a.html [b.html ...] [--outdir png/] [--scale 3] [--check-only]
// 필요: npm i playwright (또는 NODE_PATH 로 기존 설치 지정) · 크롬 경로는 CHROME_PATH 로 바꿀 수 있음
import { createRequire } from 'module'; import path from 'path'; import fs from 'fs';
const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const args = process.argv.slice(2); const opt = (k, d) => { const i = args.indexOf(k); return i < 0 ? d : args.splice(i, 2)[1]; };
const outdir = opt('--outdir', null), scale = +opt('--scale', 3), checkOnly = args.includes('--check-only');
const files = args.filter(a => !a.startsWith('--'));
const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
const page = await (await browser.newContext({ viewport: { width: 900, height: 1200 }, deviceScaleFactor: scale })).newPage();
let fail = 0;
for (const f of files) {
  const t0 = Date.now(); await page.goto('file://' + path.resolve(f)); await page.evaluate(() => document.fonts.ready);
  const r = await page.evaluate(() => {
    addEventListener('resize', e => e.stopImmediatePropagation(), true);   // 찍는 동안 화면 맞춤 배율 끔
    const s = document.querySelector('.sheet'); s.style.zoom = 1; s.style.boxShadow = 'none';
    const issues = [];
    document.querySelectorAll('.blk').forEach(b => { const br = b.getBoundingClientRect(); const id = b.querySelector('.kn')?.textContent;
      b.querySelectorAll('.lead *, .viz *').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && (r.right > br.right + 1 || r.left < br.left - 1)) issues.push(`${id} 넘침: ${e.getAttribute('class') || e.tagName} "${e.textContent.trim().slice(0, 12)}"`); });
      b.querySelectorAll('.bl, h2').forEach(e => { const lh = parseFloat(getComputedStyle(e).lineHeight); if (e.matches('.bl') && e.getBoundingClientRect().height > lh * 1.5) issues.push(`${id} 막대 이름 두 줄: "${e.textContent}"`); }); });
    return { mm: Math.round(s.offsetHeight * 25.4 / 96), issues: [...new Set(issues)].slice(0, 8) };
  });
  if (!checkOnly) { await page.setViewportSize({ width: 900, height: Math.ceil(r.mm * 96 / 25.4) + 40 });
    const out = outdir ? path.join(outdir, path.basename(f).replace(/\.html$/, '.png')) : f.replace(/\.html$/, '.png');
    await page.evaluate(() => { document.querySelector('.sheet').style.zoom = 1; });   // 창 크기를 바꾸면 화면 맞춤 배율이 다시 걸릴 수 있어 1배로 되돌림
    fs.mkdirSync(path.dirname(out), { recursive: true }); await (await page.$('.sheet')).screenshot({ path: out }); r.png = out; }
  if (r.issues.length) fail++;
  console.log(JSON.stringify({ file: path.basename(f), length: r.mm === 297 ? 'A4' : `${r.mm}mm (A4 ${r.mm > 297 ? '+' : '−'}${Math.abs(r.mm - 297)})`, ms: Date.now() - t0, png: r.png, issues: r.issues }));
}
await browser.close(); process.exit(fail ? 1 : 0);
