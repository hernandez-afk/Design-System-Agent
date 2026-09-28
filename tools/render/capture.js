#!/usr/bin/env node
// Renders a page at each viewport and text scale, saves full-page screenshots,
// and measures what a screenshot alone can only estimate: sideways overflow,
// touch-target sizes, text sizes, clipped text, and the computed padding and
// type of every component. Driven by tools/screenshots.py, which passes a JSON
// config file and reads results.json back.
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

function loadPlaywright() {
  try { return require("playwright"); } catch (e) {
    const root = execSync("npm root -g").toString().trim();
    return require(path.join(root, "playwright"));
  }
}

async function measure(page, cfg, withInventory) {
  return page.evaluate(({ minTouch, minText, withInventory }) => {
    const vw = window.innerWidth;
    const kind = (el) => el.getAttribute("data-component") ||
      (el.tagName.toLowerCase() + (el.classList.length ? "." + el.classList[0] : ""));
    const label = (el) => kind(el) +
      (el.id ? `#${el.id}` : "") + (el.textContent.trim() ? ` "${el.textContent.replace(/\s+/g, " ").trim().slice(0, 40)}"` : "");
    const visible = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
      return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
    const scrollsX = (el) => { for (let p = el.parentElement; p; p = p.parentElement) {
      const o = getComputedStyle(p).overflowX; if (o === "auto" || o === "scroll") return true; } return false; };
    const all = [...document.querySelectorAll("body *")].filter(visible);

    const overflowPx = document.documentElement.scrollWidth - vw;
    // The culprit is what forces the width, not everything pushed past the edge by it: an element
    // wider than the viewport that sets a fixed width/min-width, or is intrinsically wide (tables,
    // media, code). If nothing like that is found, report the deepest over-wide elements.
    const px = (v) => (v && v.endsWith("px") ? parseFloat(v) : 0);
    const wide = all.filter((el) => el.getBoundingClientRect().width > vw + 1 && !scrollsX(el));
    let culprits = wide.filter((el) => { const s = getComputedStyle(el);
      return el.matches("table, img, video, iframe, pre, svg, canvas") || px(s.minWidth) > vw || (px(s.width) > vw && s.width === el.style.width); });
    if (!culprits.length) culprits = wide.filter((el) => ![...el.children].some((c) => wide.includes(c)));
    const offenders = overflowPx > 0 ? culprits.slice(0, 5).map((el) => ({ element: label(el),
      widthPx: Math.round(el.getBoundingClientRect().width), minWidth: getComputedStyle(el).minWidth })) : [];

    const interactive = all.filter((el) => el.matches("a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=switch], [role=tab]"));
    const smallTargets = interactive.map((el) => ({ el, r: el.getBoundingClientRect() }))
      .filter(({ r }) => r.width < minTouch || r.height < minTouch)
      .map(({ el, r }) => ({ element: label(el), widthPx: Math.round(r.width), heightPx: Math.round(r.height) }));

    const texty = all.filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
    const smallText = texty.map((el) => ({ el, fs: parseFloat(getComputedStyle(el).fontSize) }))
      .filter(({ fs }) => fs < minText).map(({ el, fs }) => ({ element: label(el), fontSizePx: fs }));
    const clipped = texty.filter((el) => { const s = getComputedStyle(el);
      const hides = [s.overflow, s.overflowX, s.overflowY].some((o) => o === "hidden" || o === "clip");
      return hides && (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1); })
      .map((el) => ({ element: label(el) }));

    let inventory = null;
    if (withInventory) {
      inventory = all.filter((el) => el.matches("[data-component], h1, h2, h3, h4, h5, h6, p, label, button, input, select"))
        .map((el) => { const s = getComputedStyle(el); const px = (v) => Math.round(parseFloat(v) || 0);
          return { key: kind(el), tag: el.tagName.toLowerCase(), where: label(el),
            padding: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft].map(px),
            gap: s.display.includes("flex") || s.display.includes("grid") ? px(s.rowGap) : null,
            fontSizePx: parseFloat(s.fontSize), fontWeight: parseInt(s.fontWeight, 10),
            fontFamily: s.fontFamily.split(",")[0].replace(/["']/g, "").trim() }; });
    }
    return { overflowPx: Math.max(0, overflowPx), offenders, smallTargets, smallText, clipped, inventory };
  }, { minTouch: cfg.minTouch, minText: cfg.minTextPx, withInventory });
}

(async () => {
  const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const results = { shots: [] };
  fs.mkdirSync(cfg.outDir, { recursive: true });
  const textSizes = (page) => page.evaluate(() => [...document.querySelectorAll("body *")]
    .filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()))
    .map((el) => ({ size: parseFloat(getComputedStyle(el).fontSize),
      element: (el.getAttribute("data-component") || el.tagName.toLowerCase() + (el.classList.length ? "." + el.classList[0] : "")) +
        ` "${el.textContent.replace(/\s+/g, " ").trim().slice(0, 40)}"` })));
  for (const vp of cfg.viewports) {
    // One page per viewport: measure at 100%, then scale text in the same page, so every
    // element can be compared with itself.
    const page = await browser.newPage({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: 1 });
    await page.goto(cfg.target, { waitUntil: "networkidle" });
    let base = null;
    for (const scale of vp.textScales) {
      if (scale !== 100) {
        // Text-only scaling: raise the root font size. Text set in rem/em grows; text set in px
        // doesn't, which is exactly what this test should expose.
        await page.addStyleTag({ content: `html { font-size: ${scale}% !important; }` });
      }
      const file = `${vp.name}-${vp.w}${scale !== 100 ? `-text${scale}` : ""}.png`;
      await page.screenshot({ path: path.join(cfg.outDir, file), fullPage: true });
      const m = await measure(page, cfg, vp.inventory && scale === 100);
      const sizes = await textSizes(page);
      if (scale === 100) base = sizes;
      const notScaling = scale !== 100 && base ? sizes.filter((s, i) => base[i] && s.size < base[i].size * (1 + (scale / 100 - 1) * 0.5))
        .map((s, i) => ({ element: s.element, fontSizePx: s.size })) : [];
      results.shots.push({ file, viewport: { name: vp.name, w: vp.w, h: vp.h }, textScalePercent: scale, notScaling, ...m });
    }
    await page.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(cfg.outDir, "results.json"), JSON.stringify(results, null, 2));
})().catch((e) => { console.error(e.message); process.exit(1); });
