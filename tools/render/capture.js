#!/usr/bin/env node
// Renders a page at each viewport and text scale, saves full-page screenshots,
// and measures what a screenshot alone can only estimate: sideways overflow,
// touch-target sizes, text sizes, clipped text, and the computed padding and
// type of every component. On the inventory shots it also reads what an AI-made
// page tends to get wrong: the same sentence or figure shown twice on one
// screen, fonts that don't actually load, and (for brand checks) the colors,
// fonts, text and logos in use. Driven by tools/screenshots.py, which passes a JSON
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

// Anti-AI-design and brand measurements, on the inventory shots only.
async function antiAi(page, cfg) {
  await page.evaluate(() => document.fonts.ready);
  return page.evaluate(({ rep, logoSelectors, primaryHexes }) => {
    const kind = (el) => el.getAttribute("data-component") ||
      (el.tagName.toLowerCase() + (el.classList.length ? "." + el.classList[0] : ""));
    const label = (el) => kind(el) + ` "${el.textContent.replace(/\s+/g, " ").trim().slice(0, 40)}"`;
    const visible = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
      return r.width > 1 && r.height > 1 && s.visibility !== "hidden" && s.display !== "none" && s.clipPath === "none" && s.clip === "auto"; };
    const texty = [...document.querySelectorAll("body *")].filter((el) => visible(el) &&
      [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
    // Each screen is compared with itself: a design file showing several screens or states side by
    // side marks them with data-screen, data-artboard or data-state.
    const screen = (el) => el.closest("[data-screen], [data-artboard], [data-state]") || document.body;
    const skipped = (el) => el.closest("nav, [aria-current], [aria-hidden=true], title, script, style, noscript, template");
    // Items of a repeated list (rows, list items, repeated component instances) may share text:
    // "Vote" on every card is structure, not repetition.
    const item = (el) => { for (let p = el; p && p !== document.body; p = p.parentElement) {
      if (p.matches("li, tr, [role=listitem], [role=row], option")) return p;
      const c = p.getAttribute("data-component");
      if (c && p.parentElement && [...p.parentElement.children].some((x) => x !== p && x.getAttribute("data-component") === c)) return p;
    } return null; };
    const structural = (a, b) => { const ia = item(a), ib = item(b); return ia && ib && ia !== ib && ia.parentElement === ib.parentElement; };
    const norm = (t) => t.toLowerCase().replace(/\s+/g, " ").replace(/[.,:;!?…"'“”‘’()\[\]]/g, "").trim();
    const groups = (entries) => { const g = new Map();
      for (const [key, el] of entries) { const k = key + "\u0000" + [...document.querySelectorAll("[data-screen], [data-artboard], [data-state]")].indexOf(screen(el));
        g.set(k, [...(g.get(k) || []), el]); }
      const out = [];
      for (const [k, els] of g) {
        const leaves = els.filter((a) => !els.some((b) => b !== a && a.contains(b)));
        const kept = leaves.filter((a) => leaves.some((b) => b !== a && !structural(a, b)));
        if (kept.length > 1) out.push({ value: k.split("\u0000")[0], where: kept.slice(0, 4).map(label) });
      }
      return out; };
    const blocks = texty.filter((el) => !skipped(el)).map((el) => [el.textContent.replace(/\s+/g, " ").trim(), el]);
    // Compared sentence by sentence, so a sentence repeated inside a longer paragraph still counts.
    const sentences = blocks.flatMap(([t, el]) => t.split(/(?<=[.!?])\s+/).map((x) => [norm(x), el]))
      .filter(([x]) => x.split(" ").length >= (rep.minWords || 3));
    const repeatedText = rep.enabled === false ? [] : groups(sentences);
    // A figure counts when it can't be a coincidence: a separator, decimal, %, currency or 3+ digits.
    const FIG = /(?:[$€£¥]\s?)?\d[\d,.]*\d(?:\s?(?:%|k|m|bn))?|(?:[$€£¥]\s?)?\d(?:\s?%)/gi;
    const figs = [];
    if (rep.enabled !== false && rep.figures !== false) {
      for (const [t, el] of blocks) for (const f of t.match(FIG) || []) {
        const v = f.replace(/\s/g, "").toLowerCase();
        if (/^(19|20)\d\d$/.test(v) || !/[,.%$€£¥km]|\d{3}/.test(v)) continue;
        figs.push([v, el]);
      }
    }
    const repeatedFigures = groups(figs);

    // Fonts: which families the text asks for, and whether each actually renders (a family that
    // isn't installed or loaded measures the same as the fallback).
    const ctx = document.createElement("canvas").getContext("2d");
    const width = (font) => { ctx.font = font; return ctx.measureText("mmmmmmmmmwwwwwwwiiiiilll 0123456789").width; };
    const fonts = {};
    for (const el of texty) {
      const fam = getComputedStyle(el).fontFamily.split(",")[0].replace(/["']/g, "").trim();
      if (!(fam in fonts)) {
        const generic = ["serif", "sans-serif", "monospace", "system-ui", "cursive", "fantasy"].includes(fam);
        const renders = generic || ["monospace", "serif"].some((fb) => width(`40px "${fam}", ${fb}`) !== width(`40px ${fb}`));
        fonts[fam] = { where: label(el), renders };
      }
    }
    // Brand data: the text (with alt text and a brand-guidelines declaration), colors in use, logos.
    const hex = (c) => { const m = c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/);
      if (!m || (m[4] !== undefined && parseFloat(m[4]) === 0)) return null;
      return "#" + [m[1], m[2], m[3]].map((x) => (+x).toString(16).padStart(2, "0")).join(""); };
    const colors = {};
    for (const el of [...document.querySelectorAll("body, body *")].filter(visible)) {
      const s = getComputedStyle(el);
      const used = [texty.includes(el) ? s.color : null, s.backgroundColor,
        parseFloat(s.borderTopWidth) > 0 ? s.borderTopColor : null];
      for (const c of used.map((c) => c && hex(c)).filter(Boolean)) if (!(c in colors)) colors[c] = label(el);
    }
    const meta = document.querySelector('meta[name="brand-guidelines"]');
    const text = [document.body.innerText, ...[...document.querySelectorAll("img[alt], [aria-label]")]
      .map((e) => e.getAttribute("alt") || e.getAttribute("aria-label")), meta ? `<meta name="brand-guidelines" content="${meta.content}">` : ""].join("\n");
    const others = [...document.querySelectorAll("body *")].filter((o) => visible(o) &&
      ([...o.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) || o.matches("img, svg, button, input, a")));
    const logos = logoSelectors.flatMap((selector) => [...document.querySelectorAll(selector)].filter(visible).map((el) => {
      const r = el.getBoundingClientRect();
      const gap = (o) => { const q = o.getBoundingClientRect();
        return Math.max(q.left - r.right, r.left - q.right, q.top - r.bottom, r.top - q.bottom); };
      const near = others.filter((o) => !o.contains(el) && !el.contains(o));
      // Colors an inline SVG logo is drawn in; an <img> logo's colors can't be read.
      const fills = [...new Set([...el.querySelectorAll("path, rect, circle, ellipse, polygon, polyline, text, use")]
        .flatMap((sh) => { const cs = getComputedStyle(sh); return [cs.fill, cs.stroke]; })
        .map((c) => c && c.startsWith("rgb") ? hex(c) : null).filter(Boolean))];
      const t = getComputedStyle(el).transform;
      const mtx = t && t !== "none" ? t.match(/matrix\(([^)]+)\)/) : null;
      return { selector, where: kind(el) + (el.getAttribute("alt") ? ` "${el.getAttribute("alt")}"` : ""),
        w: Math.round(r.width), h: Math.round(r.height), naturalW: el.naturalWidth || null, naturalH: el.naturalHeight || null,
        clearPx: near.length ? Math.round(Math.min(...near.map(gap))) : null, fills,
        rotated: mtx ? Math.abs(parseFloat(mtx[1].split(",")[1])) > 1e-3 : false };
    }));
    // The type each kind of text is set in, for a brand's type roles.
    const seenType = new Set(), type = [];
    for (const el of texty.filter((e) => e.matches("h1, h2, h3, h4, h5, h6, p, label, button, a, li, td, th, figcaption, small"))) {
      const cs = getComputedStyle(el);
      const t = { tag: el.tagName.toLowerCase(), family: cs.fontFamily.split(",")[0].replace(/["']/g, "").trim(),
        weight: parseInt(cs.fontWeight, 10), transform: cs.textTransform, where: label(el),
        caps: el.textContent === el.textContent.toUpperCase() };
      const k = [t.tag, t.family, t.weight, t.transform].join("|");
      if (!seenType.has(k)) { seenType.add(k); type.push(t); }
    }
    // Content: how much text there is, where, and information in prose that has a better form.
    const vh = window.innerHeight;
    const words = (t) => (t.match(/[\p{L}\p{N}][\p{L}\p{N}'’.-]*/gu) || []).length;
    const longform = (el) => el.closest("[data-longform], nav, footer");
    const own = (el) => [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(" ");
    const textBlocks = texty.filter((el) => !longform(el) && el.matches("p, li, dd, figcaption, label, small, span, div, td"))
      .filter((el) => !el.closest("button, a, label") || el.matches("label"))
      .map((el) => ({ el, text: el.textContent.replace(/\s+/g, " ").trim() }))
      .filter((b) => !texty.some((o) => o !== b.el && b.el.contains(o) && o.matches("p, li")));
    const sentenceCount = (t) => t.split(/(?<=[.!?])\s+/).filter((x) => words(x) > 0).length;
    const contentBlocks = textBlocks.map((b) => ({ where: label(b.el), words: words(b.text), sentences: sentenceCount(b.text),
      intro: !!(b.el.previousElementSibling && b.el.previousElementSibling.matches("h1, h2")), text: b.text.slice(0, 400) }));
    const firstScreenWords = texty.filter((el) => !el.closest("nav") && el.getBoundingClientRect().top < vh)
      .reduce((n, el) => n + words(own(el)), 0);
    const screensWords = [...document.querySelectorAll("[data-screen], [data-artboard], [data-state]")];
    const totalWords = screensWords.length ? Math.max(...screensWords.map((sc) => words(sc.innerText || "")))
      : words(document.body.innerText.replace(/\n+/g, " "));
    // The 3-second glance: the purpose (h1) and the primary action in the first screen.
    const h1 = [...document.querySelectorAll("h1")].find(visible);
    const isPrimary = (el) => el.matches("[data-variant=primary], [data-primary], .primary, .btn-primary, .button-primary, button[type=submit]") ||
      (primaryHexes || []).includes(hex(getComputedStyle(el).backgroundColor) || "");
    const actions = [...document.querySelectorAll("button, a[href], input[type=submit], [role=button]")].filter((el) => visible(el) && !el.closest("nav"));
    const primaries = actions.filter(isPrimary).map((el) => ({ where: label(el), top: Math.round(el.getBoundingClientRect().top) }));
    // For the 3-minute estimate: what a person has to read and fill in on this screen.
    const fields = [...document.querySelectorAll("input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=submit]):not([type=button]), textarea, select")].filter(visible).length;
    const choices = new Set([...document.querySelectorAll("input[type=checkbox], input[type=radio], [role=switch]")].filter(visible)
      .map((el) => el.name || el.id || Math.random())).size;
    const tables = [...document.querySelectorAll("table")].filter(visible).map((t) => ({ where: label(t),
      rows: [...t.querySelectorAll("tr")].filter((r) => r.querySelector("td")).length,
      cols: Math.max(0, ...[...t.querySelectorAll("tr")].map((r) => r.children.length)) }));
    // Cards: how many separate pieces of information each one shows (actions aren't counted).
    const cardSel = "[data-component*='Card'], [data-component*='Tile'], .card, article";
    const cards = [...document.querySelectorAll(cardSel)].filter((c) => visible(c) && !c.querySelector(cardSel)).map((c) => {
      // A table or list inside a card is one area; its cells and items aren't counted one by one.
      const units = [...c.querySelectorAll("*")].filter((el) => visible(el) && !el.closest("button, a, [role=button], input, select, textarea") && (
        el.matches("table, ul, ol, dl") && !el.parentElement.closest("table, ul, ol, dl") ||
        !el.closest("table, ul, ol, dl") && [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()) ||
        (el.matches("img, svg, video, canvas, picture") && el.getBoundingClientRect().width > 24 && !el.parentElement.closest("img, svg, picture"))));
      return { where: label(c), areas: units.length, parts: units.slice(0, 8).map((u) => u.tagName.toLowerCase() +
        (u.textContent.trim() ? ` "${u.textContent.replace(/\s+/g, " ").trim().slice(0, 20)}"` : "")) };
    });
    // Navigation: items per level, clicks to reach each option, search, and how hidden options open.
    const navs = [...document.querySelectorAll("nav, [role=navigation], [role=menubar]")].filter((n) => !n.parentElement.closest("nav, [role=navigation], [role=menubar]"));
    const opener = (el) => { const id = el.id; const byId = id && document.querySelector(`[aria-controls="${id}"]`);
      if (byId && visible(byId)) return byId;
      const li = el.closest("li, details"); if (!li) return null;
      return [...li.querySelectorAll(":scope > button[aria-expanded], :scope > [role=button][aria-expanded], :scope > summary, :scope > a[aria-expanded]")].find(visible) || null; };
    const nav = navs.map((n) => {
      const links = [...n.querySelectorAll("a[href], button:not([aria-expanded]), [role=menuitem], [role=tab]")];
      const hiddenLists = [...n.querySelectorAll("ul, ol, [role=menu], [id]")].filter((l) => !visible(l) && l.querySelector("a, button, [role=menuitem]"));
      const unlabelled = hiddenLists.filter((l) => { const o = opener(l); return !o || !(o.getAttribute("aria-label") || o.textContent.trim()); });
      const depthOf = (a) => { let d = 1; for (let p = a.parentElement; p && p !== n.parentElement; p = p.parentElement)
        if (p.matches("ul ul, ol ol, ul ol, ol ul, [role=menu], details > ul, details > ol") ) d++;
        return d + (visible(n) ? 0 : 1); };
      const levels = new Map();  // items per list: its entries, whether links, buttons or submenu headings
      for (const l of n.querySelectorAll("ul, ol, [role=menu], [role=menubar], [role=tablist]"))
        levels.set(l, l.matches("ul, ol") ? [...l.children].filter((c) => c.matches("li")).length : l.querySelectorAll(":scope > *").length);
      if (!levels.size) levels.set(n, links.length);
      const toggle = !visible(n) && (opener(n) || [...document.querySelectorAll("[aria-controls], button[aria-expanded]")].find((b) => visible(b) && !b.closest("nav")));
      return { where: label(n), visible: visible(n), hasOpener: !!toggle, options: links.length,
        maxClicks: links.length ? Math.max(...links.map(depthOf)) : 0,
        levels: [...levels.entries()].map(([l, k]) => ({ where: label(l), items: k })),
        unlabelledHidden: unlabelled.map(label) };
    });
    const search = !!document.querySelector("input[type=search], [role=search], [data-command-palette], input[aria-label*='search' i], input[placeholder*='search' i]");
    const onScreen = [...document.querySelectorAll("a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=switch], [role=tab], summary")]
      .filter((el) => visible(el) && el.getBoundingClientRect().top < vh && el.getBoundingClientRect().bottom > 0).length;
    const structure = { cards, nav, search, controlsOnFirstScreen: onScreen };
    const content = { viewportH: vh, blocks: contentBlocks, firstScreenWords, totalWords,
      glance: { h1: h1 ? { where: label(h1), top: Math.round(h1.getBoundingClientRect().top) } : null, primaries },
      effort: { words: totalWords, fields, choices, actions: actions.length }, tables };
    return { repeatedText, repeatedFigures, fonts, brand: { text, colors, logos, type }, content, structure };
  }, { rep: cfg.repetition || {}, logoSelectors: cfg.logoSelectors || [], primaryHexes: cfg.primaryHexes || [] });
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
      if (vp.inventory && scale === 100) m.antiAi = await antiAi(page, cfg);
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
