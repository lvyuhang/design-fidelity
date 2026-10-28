#!/usr/bin/env node
/*
 * Fidelity render harness for React pages (tool code; copied next to the
 * page's render entry and kept in sync by `page generate`).
 *
 *   node fidelity/<page>/support/fidelity_render_harness.cjs fidelity/<page>/render.tsx \
 *        --output-env PAGE_RENDER_OUTPUT
 *
 * Bundles the entry with esbuild, renders it in headless Chromium (Playwright)
 * at the design size and the design safe area, and writes:
 *   <output>                 PNG at `fidelity.scale` device pixels per design unit
 *   <output>.geometry.json   layout rects of every [data-node-id] (schema 1)
 *   <output>.variants.json   the same on five devices x text scales 1.0 / 1.3 (schema 2)
 * The schema matches the Flutter harness, so the same gate checks both.
 *
 *   node .../fidelity_render_harness.cjs fidelity/<page>/render.tsx --scene fidelity/<page>/scene.g.json
 *
 * Scene-obligation mode: renders the generated scene and checks that every
 * source effect is bound to the verified primitive (data-df-* attributes) and,
 * where listed, the border band / composited fill pixels. Exit 1 on failure.
 *
 * Needs `esbuild`, `playwright`, `react`, `react-dom` resolvable from the app
 * (devDependencies) or NODE_PATH, and `@design-fidelity/react` (installed or at
 * packages/design-fidelity-react).
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const DEVICES = [
  { name: 'iphone_se', width: 375, height: 667, top: 20, bottom: 0 },
  { name: 'iphone_15', width: 393, height: 852, top: 59, bottom: 34 },
  { name: 'iphone_15_pro_max', width: 430, height: 932, top: 59, bottom: 34 },
  { name: 'android_compact', width: 360, height: 800, top: 24, bottom: 0 },
  { name: 'android_large', width: 412, height: 915, top: 24, bottom: 24 },
];
const TEXT_SCALES = [1.0, 1.3];
const ORIGIN = 'http://fidelity.local';
const WEIGHTS = { thin: 100, ultralight: 200, extralight: 200, light: 300, regular: 400, normal: 400,
  medium: 500, semibold: 600, demibold: 600, bold: 700, heavy: 800, extrabold: 800, black: 900 };

function load(name) {
  for (const base of [process.cwd(), __dirname]) {
    try { return require(require.resolve(name, { paths: [base] })); } catch (_) { /* next */ }
  }
  return require(name); // NODE_PATH
}

function parseArgs(argv) {
  const args = { entry: null, outputEnv: 'PAGE_RENDER_OUTPUT', variants: true, scene: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--output-env') args.outputEnv = argv[++i];
    else if (argv[i] === '--scene') args.scene = argv[++i];
    else if (argv[i] === '--no-variants') args.variants = false;
    else if (!args.entry) args.entry = argv[i];
    else throw new Error(`Unexpected argument ${argv[i]}`);
  }
  if (!args.entry) throw new Error('usage: fidelity_render_harness.cjs <render.tsx> [--output-env NAME]');
  return args;
}

function weightOf(label) {
  const value = String(label).split('@').pop().trim();
  const n = Number(value);
  if (Number.isFinite(n)) return Math.min(900, Math.max(100, Math.round(n / 100) * 100));
  return WEIGHTS[value.toLowerCase().replace(/[-\s]/g, '')] || 400;
}

function fontFaces(fontMapPath, files) {
  if (!fontMapPath) return '';
  const resolvedMap = path.resolve(fontMapPath);
  const map = JSON.parse(fs.readFileSync(resolvedMap, 'utf8'));
  const css = [];
  for (const [label, entry] of Object.entries(map.fonts || {})) {
    if (!entry || !entry.runtime_family || !entry.path) continue;
    let file = entry.path.startsWith('~/') ? path.join(os.homedir(), entry.path.slice(2)) : entry.path;
    if (!path.isAbsolute(file)) file = path.join(path.dirname(resolvedMap), file);
    if (!fs.existsSync(file)) throw new Error(`Design font missing for ${label}: ${file}`);
    const key = `/font/${files.size}${path.extname(file)}`;
    files.set(key, file);
    css.push(`@font-face{font-family:"${entry.runtime_family}";src:url("${ORIGIN}${key}");` +
      `font-weight:${weightOf(label)};font-style:normal;font-display:block}`);
  }
  return css.join('\n');
}

async function bundle(entry, outdir, scene) {
  const esbuild = load('esbuild');
  const mount = path.join(outdir, 'mount.tsx');
  const sceneImport = scene
    ? `import { ${scene.scene} as Scene } from ${JSON.stringify(path.resolve(path.dirname(scene.file), scene.module))};\nconst Page = () => <Scene />;`
    : '';
  fs.writeFileSync(mount, `
import * as React from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import { SourceFonts } from '@design-fidelity/react';
import ${scene ? 'EntryPage' : 'Page'}, { fidelity } from ${JSON.stringify(entry)};
${sceneImport}
SourceFonts.useDesignFonts = true;
let root: any = null;
(window as any).__fidelity = {
  config: fidelity,
  mount() {
    const el = document.getElementById('root')!;
    if (root) root.unmount();
    root = createRoot(el, { onUncaughtError: (e: any) => (window as any).__errors.push(String(e && e.stack || e)),
                            onCaughtError: (e: any) => (window as any).__errors.push(String(e && e.stack || e)) });
    flushSync(() => root.render(<Page />));
  },
};
`);
  const nodePaths = [path.join(process.cwd(), 'node_modules'),
    ...(process.env.NODE_PATH || '').split(path.delimiter).filter(Boolean)];
  const alias = {};
  try {
    require.resolve('@design-fidelity/react', { paths: [process.cwd()] });
  } catch (_) {
    const local = path.join(process.cwd(), 'packages', 'design-fidelity-react', 'src', 'index.tsx');
    const fallback = process.env.DESIGN_FIDELITY_REACT || local;
    if (!fs.existsSync(fallback)) throw new Error('@design-fidelity/react not found; run install_app.py init --target react');
    alias['@design-fidelity/react'] = fallback;
  }
  await esbuild.build({
    entryPoints: [mount], bundle: true, outdir, format: 'iife', platform: 'browser', jsx: 'automatic',
    loader: { '.png': 'file', '.jpg': 'file', '.jpeg': 'file', '.webp': 'file', '.gif': 'file', '.svg': 'file' },
    assetNames: 'assets/[name]-[hash]', publicPath: ORIGIN, nodePaths, alias, logLevel: 'error',
    define: { 'process.env.NODE_ENV': '"production"' },
  });
}

function html(faces) {
  return `<!doctype html><html><head><meta charset="utf-8">
<style>${faces}
html{font-size:16px;-webkit-text-size-adjust:100%;text-size-adjust:100%;font-synthesis:none}
html,body{margin:0;padding:0;background:transparent}
#root{position:relative;overflow:hidden}
</style></head><body><div id="root"></div><script>window.__errors=[];
window.addEventListener('error',e=>window.__errors.push(String(e.error&&e.error.stack||e.message)));
</script><script src="${ORIGIN}/mount.js"></script></body></html>`;
}

async function settle(page) {
  return page.evaluate(async () => {
    await document.fonts.ready;
    const images = [...document.querySelectorAll('img')];
    const failed = [];
    await Promise.all(images.map(async (img) => {
      try { await img.decode(); } catch (_) { failed.push(img.getAttribute('src')); }
    }));
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    return failed;
  });
}

function measure() {
  const root = document.getElementById('root');
  const o = root.getBoundingClientRect();
  const nodes = {};
  const text = {};
  for (const el of root.querySelectorAll('[data-node-id]')) {
    const r = el.getBoundingClientRect();
    const id = el.getAttribute('data-node-id');
    nodes[id] = [r.left - o.left, r.top - o.top, r.width, r.height];
    let u = null;
    const add = (q) => {
      if (q.width <= 0 && q.height <= 0) return;
      u = u ? [Math.min(u[0], q.left), Math.min(u[1], q.top), Math.max(u[2], q.right), Math.max(u[3], q.bottom)]
        : [q.left, q.top, q.right, q.bottom];
    };
    const paragraphs = el.querySelectorAll('[data-df-text]');
    if (paragraphs.length) {
      paragraphs.forEach((p) => add(p.getBoundingClientRect()));
    } else {
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let t = walker.nextNode(); t; t = walker.nextNode()) {
        if (!t.textContent.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(t);
        add(range.getBoundingClientRect());
      }
    }
    if (u) text[id] = [u[0] - o.left, u[1] - o.top, u[2] - u[0], u[3] - u[1]];
  }
  const scroller = root.querySelector('[data-df-scroll]');
  const scrollable = [...root.querySelectorAll('*')].some((el) => {
    const style = getComputedStyle(el);
    return /(auto|scroll)/.test(style.overflowY) && el.scrollHeight > el.clientHeight + 0.5;
  }) || !!(scroller && scroller.scrollHeight > scroller.clientHeight + 0.5);
  return { nodes, text, scrollable };
}

async function frame(page, { width, height, top, bottom, textScale }) {
  await page.setViewportSize({ width: Math.ceil(width), height: Math.ceil(height) });
  await page.evaluate(({ width, height, top, bottom, textScale }) => {
    document.documentElement.style.fontSize = `${16 * textScale}px`;
    const root = document.getElementById('root');
    Object.assign(root.style, { width: `${width}px`, height: `${height}px` });
    root.style.setProperty('--df-safe-top', `${top}px`);
    root.style.setProperty('--df-safe-bottom', `${bottom}px`);
    window.__errors = [];
    window.__fidelity.mount();
  }, { width, height, top, bottom, textScale });
  const failed = await settle(page);
  const errors = await page.evaluate(() => window.__errors);
  return { failed, errors };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const entry = path.resolve(args.entry);
  if (args.scene) return sceneChecks(args, entry);
  const output = process.env[args.outputEnv];
  if (!output) throw new Error(`Set ${args.outputEnv} to the PNG output path`);
  const outdir = fs.mkdtempSync(path.join(os.tmpdir(), 'design-fidelity-web-'));
  try {
    await bundle(entry, outdir);
    const { chromium } = load('playwright');
    const browser = await chromium.launch();
    try {
      const files = new Map();
      // Config is read from the bundle before the real viewport is known.
      const config = await readConfig(browser, outdir, files);
      const faces = fontFaces(config.fontMap, files);
      const [width, height] = config.designSize;
      const scale = config.scale || 4;
      const context = await browser.newContext({ deviceScaleFactor: scale, viewport: { width, height } });
      const page = await context.newPage();
      const consoleErrors = [];
      page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
      page.on('pageerror', (e) => consoleErrors.push(String(e.stack || e)));
      await page.route(`${ORIGIN}/**`, (route) => serve(route, outdir, files, faces));
      await page.goto(`${ORIGIN}/index.html`);
      const main = await frame(page, { width, height, top: config.designPadding.top,
        bottom: config.designPadding.bottom, textScale: 1 });
      if (main.failed.length) throw new Error(`Image failed to load: ${main.failed.join(', ')}`);
      if (main.errors.length || consoleErrors.length) throw new Error(`Render error: ${[...main.errors, ...consoleErrors][0]}`);
      const geometry = await page.evaluate(measure);
      fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
      if (Object.keys(geometry.nodes).length) {
        fs.writeFileSync(`${output}.geometry.json`, JSON.stringify({ schema: 1, canvas: [width, height],
          nodes: geometry.nodes, text_nodes: geometry.text }, null, 1));
      }
      await page.locator('#root').screenshot({ path: output, omitBackground: true, animations: 'disabled' });
      if (args.variants) {
        const variants = [];
        await context.close();
        const vcontext = await browser.newContext({ deviceScaleFactor: 1 });
        const vpage = await vcontext.newPage();
        await vpage.route(`${ORIGIN}/**`, (route) => serve(route, outdir, files, faces));
        await vpage.goto(`${ORIGIN}/index.html`);
        for (const device of DEVICES) {
          for (const textScale of TEXT_SCALES) {
            const result = await frame(vpage, { ...device, textScale });
            const g = await vpage.evaluate(measure);
            variants.push({ device: device.name, width: device.width, height: device.height,
              padding: { top: device.top, bottom: device.bottom }, text_scale: textScale,
              exception: result.errors[0] || (result.failed.length ? `Image failed: ${result.failed[0]}` : null),
              scrollable: g.scrollable, nodes: g.nodes, text_nodes: g.text });
          }
        }
        fs.writeFileSync(`${output}.variants.json`, JSON.stringify({ schema: 2, variants }, null, 1));
        await vcontext.close();
      }
    } finally {
      await browser.close();
    }
  } finally {
    fs.rmSync(outdir, { recursive: true, force: true });
  }
}

async function readConfig(browser, outdir, files) {
  const probe = await browser.newPage();
  await probe.route(`${ORIGIN}/**`, (route) => serve(route, outdir, files, ''));
  await probe.goto(`${ORIGIN}/index.html`);
  const config = await probe.evaluate(() => window.__fidelity.config);
  await probe.close();
  return config;
}

/** Pixel helpers evaluated in the page: decode PNG screenshots via canvas. */
async function pixels(page, buffer) {
  return page.evaluate(async (b64) => {
    const img = new Image();
    img.src = `data:image/png;base64,${b64}`;
    await img.decode();
    const canvas = document.createElement('canvas');
    canvas.width = img.width;
    canvas.height = img.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const data = ctx.getImageData(0, 0, img.width, img.height).data;
    window.__px = window.__px || [];
    window.__px.push({ w: img.width, data });
    return window.__px.length - 1;
  }, buffer.toString('base64'));
}

async function rgb(page, handle, x, y) {
  return page.evaluate(({ handle, x, y }) => {
    const { w, data } = window.__px[handle];
    const o = (y * w + x) * 4;
    return [data[o], data[o + 1], data[o + 2]];
  }, { handle, x, y });
}

const diff = (a, b) => Math.max(...a.map((v, i) => Math.abs(v - b[i])));

async function sceneChecks(args, entry) {
  const specFile = path.resolve(args.scene);
  const spec = JSON.parse(fs.readFileSync(specFile, 'utf8'));
  const outdir = fs.mkdtempSync(path.join(os.tmpdir(), 'design-fidelity-scene-'));
  const failures = [];
  let passed = 0;
  try {
    await bundle(entry, outdir, { ...spec, file: specFile });
    const { chromium } = load('playwright');
    const browser = await chromium.launch();
    try {
      const files = new Map();
      const config = await readConfig(browser, outdir, files);
      const faces = fontFaces(config.fontMap, files);
      const [width, height] = spec.canvas;
      const context = await browser.newContext({ deviceScaleFactor: 1, viewport: { width, height } });
      const page = await context.newPage();
      await page.route(`${ORIGIN}/**`, (route) => serve(route, outdir, files, faces));
      await page.goto(`${ORIGIN}/index.html`);
      const result = await frame(page, { width, height, top: spec.design_padding.top,
        bottom: spec.design_padding.bottom, textScale: 1 });
      if (result.errors.length) throw new Error(`Scene render error: ${result.errors[0]}`);
      let scene = null;
      for (const check of spec.checks) {
        const fail = (message) => failures.push(`${check.kind}: ${check.id}: ${message}`);
        const before = failures.length;
        for (const bound of check.bound || []) {
          const found = await page.evaluate(({ node, attr, equals }) => {
            const el = document.querySelector(`[data-node-id="${CSS.escape(node)}"]`);
            if (!el) return 'node not rendered';
            const candidates = [el, ...el.querySelectorAll(`[${attr}]`)].filter((c) => c.hasAttribute(attr));
            if (!candidates.length) return `does not render through ${attr}`;
            const wanted = Object.entries(equals || {});
            if (candidates.some((c) => wanted.every(([k, v]) => c.getAttribute(k) === v))) return null;
            return `expected ${JSON.stringify(equals)}, found ${JSON.stringify(candidates.map((c) =>
              Object.fromEntries(wanted.map(([k]) => [k, c.getAttribute(k)]))))}`;
          }, bound);
          if (found) fail(`${bound.node}: ${found}`);
        }
        for (const member of check.clipped || []) {
          const ok = await page.evaluate((id) => {
            const el = document.querySelector(`[data-node-id="${CSS.escape(id)}"]`);
            return !!(el && el.closest('[data-df-clip]'));
          }, member);
          if (!ok) fail(`${member} is not clipped by its mask shape`);
        }
        if (check.pixel) {
          if (scene === null) scene = await pixels(page, await page.locator('#root').screenshot());
          const got = await rgb(page, scene, check.pixel.at[0], check.pixel.at[1]);
          if (diff(got, check.pixel.rgb) > check.pixel.tolerance) {
            fail(`composited fills at (${check.pixel.at}) are ${got}, source ${check.pixel.rgb}`);
          }
        }
        if (check.band) {
          const message = await borderBand(page, check.band);
          if (message) fail(message);
        }
        if (failures.length === before) passed++;
      }
      await context.close();
    } finally {
      await browser.close();
    }
  } finally {
    fs.rmSync(outdir, { recursive: true, force: true });
  }
  console.log(JSON.stringify({ status: failures.length ? 'FAIL' : 'PASS', checks: spec.checks.length, passed, failures }, null, 1));
  if (failures.length) process.exitCode = 1;
}

/**
 * Renders a copy of the node's SourceBox on mid-grey with and without its
 * border and checks the band position plus the absence of leaks either side
 * (same probe as the Flutter scene test).
 */
async function borderBand(page, band) {
  const ratio = 4;
  const margin = band.thickness * 2 + 4;
  const [w, h] = band.size;
  const ok = await page.evaluate(({ node, margin, w, h }) => {
    const el = document.querySelector(`[data-node-id="${CSS.escape(node)}"]`);
    const box = el && (el.matches('[data-df-box]') ? el : el.querySelector('[data-df-box]'));
    if (!box) return false;
    document.getElementById('df-band')?.remove();
    const host = document.createElement('div');
    host.id = 'df-band';
    Object.assign(host.style, { position: 'fixed', left: '0', top: '0', zIndex: '2147483647',
      background: '#808080', padding: `${margin}px`, width: `${w}px`, height: `${h}px`, boxSizing: 'content-box' });
    const inner = document.createElement('div');
    Object.assign(inner.style, { position: 'relative', width: `${w}px`, height: `${h}px` });
    inner.appendChild(box.cloneNode(true));
    host.appendChild(inner);
    document.body.appendChild(host);
    return true;
  }, { node: band.node, margin, w, h });
  if (!ok) return `${band.node}: no SourceBox to probe`;
  const context = await page.context().browser().newContext({ deviceScaleFactor: ratio,
    viewport: { width: Math.ceil(w + margin * 2), height: Math.ceil(h + margin * 2) } });
  const html = await page.evaluate(() => document.getElementById('df-band').outerHTML);
  const probe = await context.newPage();
  await probe.setContent(`<!doctype html><html><body style="margin:0">${html}</body></html>`);
  const bordered = await pixels(page, await probe.locator('#df-band').screenshot());
  await probe.evaluate(() => document.querySelectorAll('#df-band [data-df-border]').forEach((b) => b.remove()));
  const plain = await pixels(page, await probe.locator('#df-band').screenshot());
  await context.close();
  await page.evaluate(() => document.getElementById('df-band')?.remove());
  const y = Math.floor((margin + h / 2) * ratio);
  const px = (x) => Math.floor(x * ratio);
  const t = band.thickness;
  const at = { inside: margin + t / 2, center: margin, outside: margin - t / 2 }[band.position];
  if (diff(await rgb(page, bordered, px(at), y), await rgb(page, plain, px(at), y)) <= 2) {
    return `${band.node}: border band must be painted at ${at}`;
  }
  const outsideEdge = { inside: margin - 1.5, center: margin - t / 2 - 1.5, outside: margin - t - 1.5 }[band.position];
  const insideEdge = { inside: margin + t + 1.5, center: margin + t / 2 + 1.5, outside: margin + 1.5 }[band.position];
  for (const x of [outsideEdge, insideEdge]) {
    if (diff(await rgb(page, bordered, px(x), y), await rgb(page, plain, px(x), y)) > 2) {
      return `${band.node}: border must not leak to ${x}`;
    }
  }
  return null;
}

function serve(route, outdir, files, faces) {
  const url = new URL(route.request().url());
  if (url.pathname === '/index.html') return route.fulfill({ contentType: 'text/html', body: html(faces) });
  const mapped = files.get(url.pathname) || path.join(outdir, decodeURIComponent(url.pathname));
  if (!mapped.startsWith(outdir) && !files.has(url.pathname)) return route.fulfill({ status: 404 });
  if (!fs.existsSync(mapped)) return route.fulfill({ status: 404, body: `missing ${url.pathname}` });
  const types = { '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.webp': 'image/webp', '.gif': 'image/gif', '.svg': 'image/svg+xml', '.ttf': 'font/ttf', '.otf': 'font/otf',
    '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttc': 'font/collection' };
  return route.fulfill({ body: fs.readFileSync(mapped), contentType: types[path.extname(mapped)] || 'application/octet-stream' });
}

main().catch((error) => {
  console.error(error && error.stack || error);
  process.exit(1);
});
