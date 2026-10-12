// Render SVG files to PNG previews with the preinstalled Chromium.
//
// Usage:
//   NODE_PATH=/opt/node22/lib/node_modules node render.js OUT_DIR file1.svg [file2.svg ...] [--sizes 1200,256,64,32] [--bg "#ffffff"]
//
// For each SVG it writes OUT_DIR/<name>@<size>.png, where <size> is the output
// width in pixels (height follows the SVG's aspect ratio). Small sizes (64, 32)
// show whether a mark still reads as a favicon or app icon. --bg sets the
// backdrop (use a dark color to check reverse/white versions).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const argv = process.argv.slice(2);
  let sizes = [1200, 256, 64, 32];
  let bg = '#ffffff';
  const files = [];
  let outDir = null;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--sizes') { sizes = argv[++i].split(',').map(Number); continue; }
    if (argv[i] === '--bg') { bg = argv[++i]; continue; }
    if (!outDir) { outDir = argv[i]; continue; }
    files.push(argv[i]);
  }
  if (!outDir || !files.length) { console.error('usage: render.js OUT_DIR file.svg ... [--sizes ..] [--bg ..]'); process.exit(1); }
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const f of files) {
    const svg = fs.readFileSync(f, 'utf8');
    const name = path.basename(f, '.svg');
    for (const w of sizes) {
      await page.setViewportSize({ width: w + 40, height: 800 });
      await page.setContent(`<!doctype html><html><body style="margin:0;padding:20px;background:${bg}"><div id="w" style="width:${w}px;line-height:0">${svg}</div></body></html>`);
      await page.evaluate(() => { const s = document.querySelector('#w svg'); s.style.width = '100%'; s.style.height = 'auto'; s.style.display = 'block'; });
      const el = await page.$('#w');
      const out = path.join(outDir, `${name}@${w}.png`);
      await el.screenshot({ path: out, omitBackground: false });
      console.log(out);
    }
  }
  await browser.close();
})();
