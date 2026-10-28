/**
 * @design-fidelity/react — render design layers exactly, in plain DOM/CSS/SVG.
 *
 * The same semantics as the Flutter `design_fidelity` package, so a page
 * generated for the web is judged by the same contract:
 *  - inside / center / outside borders keep the fill geometry unchanged;
 *  - outer shadows are knocked out under the shape (CSS box-shadow already is);
 *  - Sketch/Figma blur radius r becomes a Gaussian sigma of 0.5 r
 *    (CSS box-shadow blur = 2 sigma = r; filter blur() takes sigma);
 *  - text uses an absolute line height with even leading (CSS half-leading)
 *    and rem units, so the browser's font-size setting scales it;
 *  - every source layer carries `data-node-id` for the geometry probe.
 */
import * as React from 'react';

export type Vec = readonly [number, number];
export type Color = string;

export type SourceShape =
  | { kind: 'rect'; radii?: number | readonly [number, number, number, number] }
  | { kind: 'oval' }
  | { kind: 'path'; points: readonly SourcePathPoint[]; closed?: boolean; evenOdd?: boolean };

export interface SourcePathPoint {
  point: Vec;
  curveFrom?: Vec;
  curveTo?: Vec;
}

export interface SourceLinearGradient {
  /** Unit coordinates relative to the layer box. */
  from: Vec;
  to: Vec;
  stops: readonly (readonly [number, Color])[];
}

export type SourceFill =
  | { color: Color; opacity?: number }
  | { linear: SourceLinearGradient; opacity?: number };

export interface SourceBorder {
  thickness: number;
  fill: SourceFill;
  position?: 'inside' | 'center' | 'outside';
  cap?: 'butt' | 'round' | 'square';
  join?: 'miter' | 'round' | 'bevel';
  dash?: readonly number[];
}

export interface SourceShadow {
  color: Color;
  offset?: Vec;
  /** Source blur radius (sigma = 0.5 * blur). */
  blur?: number;
  spread?: number;
  inner?: boolean;
}

export interface TextSpec {
  /** Design (fidelity) font family, loaded from disk during fidelity renders. */
  family: string;
  /** Production family per platform; null = system font, absent = `family`. */
  platforms?: { web?: string | null };
  size: number;
  weight: number;
  /** Absolute line height in design units; null = font default. */
  lineHeight?: number | null;
  letterSpacing?: number;
  color: Color;
  decoration?: 'underline' | 'lineThrough' | null;
}

/** Sketch/Figma effect radius -> Gaussian sigma. Change only with a recalibration. */
export const FidelityEffectMapping = {
  shadowSigmaPerRadius: 0.5,
  layerBlurSigmaPerRadius: 0.5,
  backgroundBlurSigmaPerRadius: 0.5,
} as const;

export const SourceFonts = {
  /** Set by the fidelity harness: render with the design fonts. */
  useDesignFonts: false,
  systemStack: 'system-ui, -apple-system, "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", sans-serif',
};

export function sourceFontFamily(spec: Pick<TextSpec, 'family' | 'platforms'>): string {
  if (SourceFonts.useDesignFonts) return `"${spec.family}", ${SourceFonts.systemStack}`;
  const web = spec.platforms && 'web' in spec.platforms ? spec.platforms.web : spec.family;
  return web ? `"${web}", ${SourceFonts.systemStack}` : SourceFonts.systemStack;
}

// ---------------------------------------------------------------------------
// colours and gradients

function parseColor(color: Color): [number, number, number, number] {
  const text = color.trim();
  let m = /^rgba?\(([^)]*)\)$/.exec(text);
  if (m) {
    const p = m[1].split(',').map((v) => parseFloat(v));
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  }
  m = /^#([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(text);
  if (m) {
    const v = parseInt(m[1], 16);
    return [(v >> 16) & 255, (v >> 8) & 255, v & 255, m[2] ? parseInt(m[2], 16) / 255 : 1];
  }
  throw new Error(`Unsupported colour ${color}`);
}

export function withOpacity(color: Color, opacity = 1): string {
  const [r, g, b, a] = parseColor(color);
  return `rgba(${r}, ${g}, ${b}, ${+(a * opacity).toFixed(4)})`;
}

const fmt = (v: number) => +v.toFixed(4);
const px = (v: number) => `${fmt(v)}px`;

/**
 * CSS linear-gradient reproducing a gradient defined by two unit points.
 * CSS gradients are specified by angle; the stop positions are projected so
 * that the colour at every pixel equals the source gradient. Axis-aligned
 * gradients are size independent; diagonal ones are exact at `size`.
 */
export function linearGradientCss(g: SourceLinearGradient, opacity = 1, size: Vec = [1, 1]): string {
  const [w, h] = size;
  const p0 = [g.from[0] * w, g.from[1] * h];
  const d = [(g.to[0] - g.from[0]) * w, (g.to[1] - g.from[1]) * h];
  const len = Math.hypot(d[0], d[1]);
  const stops = g.stops.length ? g.stops : [[0, 'rgba(0,0,0,0)'] as const];
  if (len < 1e-9) return `linear-gradient(${withOpacity(stops[0][1], opacity)}, ${withOpacity(stops[0][1], opacity)})`;
  const dir = [d[0] / len, d[1] / len];
  const angle = (Math.atan2(dir[0], -dir[1]) * 180) / Math.PI;
  const L = Math.abs(w * dir[0]) + Math.abs(h * dir[1]);
  const start = [w / 2 - (dir[0] * L) / 2, h / 2 - (dir[1] * L) / 2];
  const base = (p0[0] - start[0]) * dir[0] + (p0[1] - start[1]) * dir[1];
  const parts = stops.map(([t, c]) => `${withOpacity(c, opacity)} ${fmt(((base + t * len) / L) * 100)}%`);
  return `linear-gradient(${fmt(angle)}deg, ${parts.join(', ')})`;
}

function fillCss(fill: SourceFill, size?: Vec): string {
  if ('linear' in fill) return linearGradientCss(fill.linear, fill.opacity ?? 1, size);
  const c = withOpacity(fill.color, fill.opacity ?? 1);
  return `linear-gradient(${c}, ${c})`;
}

// ---------------------------------------------------------------------------
// shapes

function radiiOf(shape: SourceShape): [number, number, number, number] | null {
  if (shape.kind !== 'rect') return null;
  const r = shape.radii ?? 0;
  return typeof r === 'number' ? [r, r, r, r] : [r[0], r[1], r[2], r[3]];
}

function radiusCss(shape: SourceShape, grow = 0): string {
  if (shape.kind === 'oval') return '50%';
  const r = radiiOf(shape) ?? [0, 0, 0, 0];
  return r.map((v) => px(v > 0 ? Math.max(0, v + grow) : 0)).join(' ');
}

export function pathData(points: readonly SourcePathPoint[], closed = true): string {
  if (!points.length) return '';
  const n = (v: number) => fmt(v);
  let d = `M${n(points[0].point[0])} ${n(points[0].point[1])}`;
  const count = closed ? points.length + 1 : points.length;
  for (let i = 1; i < count; i++) {
    const prev = points[(i - 1) % points.length];
    const cur = points[i % points.length];
    if (prev.curveFrom || cur.curveTo) {
      const c1 = prev.curveFrom ?? prev.point;
      const c2 = cur.curveTo ?? cur.point;
      d += ` C${n(c1[0])} ${n(c1[1])} ${n(c2[0])} ${n(c2[1])} ${n(cur.point[0])} ${n(cur.point[1])}`;
    } else {
      d += ` L${n(cur.point[0])} ${n(cur.point[1])}`;
    }
  }
  return closed ? d + ' Z' : d;
}

/** Unit-space outline of any shape, for objectBoundingBox clip paths. */
function unitOutline(shape: SourceShape): string {
  if (shape.kind === 'path') return pathData(shape.points, shape.closed ?? true);
  if (shape.kind === 'oval') return 'M0 0.5 A0.5 0.5 0 1 0 1 0.5 A0.5 0.5 0 1 0 0 0.5 Z';
  return 'M0 0 H1 V1 H0 Z';
}

const FILL: React.CSSProperties = { position: 'absolute', inset: 0 };

function ClipDefs({ id, shape }: { id: string; shape: SourceShape }) {
  return (
    <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden>
      <clipPath id={id} clipPathUnits="objectBoundingBox">
        <path d={unitOutline(shape)} clipRule={shape.kind === 'path' && shape.evenOdd ? 'evenodd' : 'nonzero'} />
      </clipPath>
    </svg>
  );
}

/** CSS that clips an element to `shape` (rect/oval via border-radius). */
function useShapeClip(shape: SourceShape | undefined): [React.CSSProperties, React.ReactNode] {
  const id = 'df' + React.useId().replace(/[^a-zA-Z0-9]/g, '');
  if (!shape) return [{}, null];
  if (shape.kind !== 'path') return [{ borderRadius: radiusCss(shape), overflow: 'hidden' }, null];
  return [{ clipPath: `url(#${id})` }, <ClipDefs key="clip" id={id} shape={shape} />];
}

// ---------------------------------------------------------------------------
// SourceBox

export interface SourceBoxProps {
  shape?: SourceShape;
  fills?: readonly SourceFill[];
  borders?: readonly SourceBorder[];
  shadows?: readonly SourceShadow[];
  opacity?: number;
  /** Design size; makes diagonal gradients exact. */
  size?: Vec;
  clipChild?: boolean;
  children?: React.ReactNode;
}

function shadowCss(s: SourceShadow): string {
  const [dx, dy] = s.offset ?? [0, 0];
  // CSS blur length is 2 sigma; sigma = 0.5 * source blur, so CSS blur = source blur.
  const blur = (s.blur ?? 0) * 2 * FidelityEffectMapping.shadowSigmaPerRadius;
  return `${s.inner ? 'inset ' : ''}${px(dx)} ${px(dy)} ${px(blur)} ${px(s.spread ?? 0)} ${withOpacity(s.color)}`;
}

function BorderOverlay({ shape, border, size }: { shape: SourceShape; border: SourceBorder; size?: Vec }) {
  const uid = 'df' + React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const t = border.thickness;
  if (t <= 0) return null;
  const position = border.position ?? 'center';
  const out = position === 'inside' ? 0 : position === 'center' ? t / 2 : t;
  const marker = { 'data-df-border': position, 'data-df-thickness': t } as const;
  const radii = radiiOf(shape);
  const uniform = shape.kind === 'oval' || (radii !== null && radii.every((r) => r === radii[0]));
  const dashed = !!(border.dash && border.dash.length);
  if (!dashed && !('linear' in border.fill)) {
    // Solid stroke: box-shadow rings follow the radius and are not pixel-snapped
    // like masked layers, so half-pixel (center) strokes stay exact.
    const c = withOpacity(border.fill.color, border.fill.opacity ?? 1);
    const ring = position === 'inside' ? `inset 0 0 0 ${px(t)} ${c}`
      : position === 'outside' ? `0 0 0 ${px(t)} ${c}`
      : `inset 0 0 0 ${px(t / 2)} ${c}, 0 0 0 ${px(t / 2)} ${c}`;
    return <span aria-hidden {...marker} style={{ ...FILL, borderRadius: radiusCss(shape), boxShadow: ring, pointerEvents: 'none' }} />;
  }
  if (uniform) {
    // Gradient or dashed stroke: an SVG rect/ellipse that follows the box size.
    const inset = t / 2 - out;
    const stroke = 'linear' in border.fill ? `url(#${uid})` : withOpacity(border.fill.color, border.fill.opacity ?? 1);
    const common = {
      fill: 'none', stroke, strokeWidth: t, strokeDasharray: dashed ? border.dash!.join(' ') : undefined,
      strokeLinecap: border.cap ?? 'butt', strokeLinejoin: border.join ?? 'miter',
    } as const;
    const r = radii ? radii[0] : 0;
    return (
      <svg aria-hidden {...marker} style={{ ...FILL, overflow: 'visible', pointerEvents: 'none' }} width="100%" height="100%">
        {'linear' in border.fill && (
          <defs>
            <linearGradient id={uid} x1={border.fill.linear.from[0]} y1={border.fill.linear.from[1]}
              x2={border.fill.linear.to[0]} y2={border.fill.linear.to[1]}>
              {border.fill.linear.stops.map(([o, c], i) => <stop key={i} offset={o} stopColor={withOpacity(c, (border.fill as { opacity?: number }).opacity ?? 1)} />)}
            </linearGradient>
          </defs>
        )}
        {shape.kind === 'oval' ? (
          <ellipse {...common} style={{ cx: '50%', cy: '50%', rx: `calc(50% - ${px(inset)})`, ry: `calc(50% - ${px(inset)})` } as React.CSSProperties} />
        ) : (
          <rect {...common} x={inset} y={inset} rx={Math.max(0, r - inset)}
            style={{ width: `calc(100% - ${px(2 * inset)})`, height: `calc(100% - ${px(2 * inset)})` }} />
        )}
      </svg>
    );
  }
  // Gradient stroke with mixed corner radii: a masked ring (may snap to whole CSS px).
  return (
    <span aria-hidden {...marker} style={{
      position: 'absolute', inset: -out, padding: t, borderRadius: radiusCss(shape, out),
      background: fillCss(border.fill, size), backgroundOrigin: 'border-box', pointerEvents: 'none',
      WebkitMask: 'linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)',
      WebkitMaskComposite: 'xor', maskComposite: 'exclude',
    } as React.CSSProperties} />
  );
}

function PathBox(props: SourceBoxProps & { shape: Extract<SourceShape, { kind: 'path' }> }) {
  const { shape, fills = [], borders = [], shadows = [], opacity = 1, children } = props;
  const uid = 'df' + React.useId().replace(/[^a-zA-Z0-9]/g, '');
  const d = pathData(shape.points, shape.closed ?? true);
  const rule = shape.evenOdd ? 'evenodd' : 'nonzero';
  const paint = (fill: SourceFill, key: string) =>
    'linear' in fill ? `url(#${uid}${key})` : withOpacity(fill.color, fill.opacity ?? 1);
  const gradient = (fill: SourceFill, key: string) =>
    'linear' in fill ? (
      <linearGradient key={key} id={uid + key} gradientUnits="userSpaceOnUse"
        x1={fill.linear.from[0]} y1={fill.linear.from[1]} x2={fill.linear.to[0]} y2={fill.linear.to[1]}>
        {fill.linear.stops.map(([t, c], i) => <stop key={i} offset={t} stopColor={withOpacity(c, fill.opacity ?? 1)} />)}
      </linearGradient>
    ) : null;
  // Outer shadows only (approximation: drop-shadow has no spread and is not knocked out).
  const filter = shadows.filter((s) => !s.inner).map((s) =>
    `drop-shadow(${px(s.offset?.[0] ?? 0)} ${px(s.offset?.[1] ?? 0)} ${px((s.blur ?? 0) * FidelityEffectMapping.shadowSigmaPerRadius)} ${withOpacity(s.color)})`).join(' ');
  const closed = shape.closed ?? true;
  return (
    <div data-df-box="path" data-df-fills={fills.length} data-df-shadows={shadows.length} data-df-borders={borders.map((b) => `${b.thickness}:${closed ? b.position ?? 'center' : 'center'}`).join(' ')}
      style={{ ...FILL, opacity: opacity < 1 ? opacity : undefined }}>
      <svg aria-hidden viewBox="0 0 1 1" preserveAspectRatio="none" width="100%" height="100%"
        style={{ ...FILL, overflow: 'visible', filter: filter || undefined }}>
        <defs>
          {fills.map((f, i) => gradient(f, `f${i}`))}
          {borders.map((b, i) => gradient(b.fill, `b${i}`))}
          <clipPath id={`${uid}in`}><path d={d} clipRule={rule} /></clipPath>
          <mask id={`${uid}out`} maskUnits="userSpaceOnUse" x={-10} y={-10} width={21} height={21}>
            <rect x={-10} y={-10} width={21} height={21} fill="#fff" />
            <path d={d} fill="#000" fillRule={rule} />
          </mask>
        </defs>
        {fills.map((f, i) => <path key={`f${i}`} d={d} fill={paint(f, `f${i}`)} fillRule={rule} />)}
        {borders.map((b, i) => {
          const position = closed ? b.position ?? 'center' : 'center';
          return (
            <path key={`b${i}`} d={d} fill="none" stroke={paint(b.fill, `b${i}`)} vectorEffect="non-scaling-stroke"
              strokeWidth={position === 'center' ? b.thickness : b.thickness * 2}
              strokeLinecap={b.cap ?? 'butt'} strokeLinejoin={b.join ?? 'miter'}
              strokeDasharray={b.dash?.length ? b.dash.join(' ') : undefined}
              clipPath={position === 'inside' ? `url(#${uid}in)` : undefined}
              mask={position === 'outside' ? `url(#${uid}out)` : undefined} />
          );
        })}
      </svg>
      {children}
    </div>
  );
}

/** A source shape layer: outer shadows, fills, inner shadows, borders. Fills its container. */
export function SourceBox(props: SourceBoxProps) {
  const shape = props.shape ?? { kind: 'rect' };
  if (shape.kind === 'path') return <PathBox {...props} shape={shape} />;
  const { fills = [], borders = [], shadows = [], opacity = 1, size, clipChild, children } = props;
  // CSS paints the first background/shadow on top; source order is bottom-up.
  const style: React.CSSProperties = {
    ...FILL,
    borderRadius: radiusCss(shape),
    background: fills.length ? [...fills].reverse().map((f) => fillCss(f, size)).join(', ') : undefined,
    boxShadow: shadows.length ? [...shadows].reverse().map(shadowCss).join(', ') : undefined,
    opacity: opacity < 1 ? opacity : undefined,
  };
  return (
    <div data-df-box={shape.kind} data-df-fills={fills.length} data-df-shadows={shadows.length}
      data-df-borders={borders.map((b) => `${b.thickness}:${b.position ?? 'center'}`).join(' ')} style={style}>
      {children != null && (
        <div style={{ ...FILL, borderRadius: clipChild ? radiusCss(shape) : undefined, overflow: clipChild ? 'hidden' : undefined }}>
          {children}
        </div>
      )}
      {borders.map((b, i) => <BorderOverlay key={i} shape={shape} border={b} size={size} />)}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Text

const rem = (v: number) => `${fmt(v / 16)}rem`;

export function sourceTextStyle(spec: TextSpec, strut?: TextSpec): React.CSSProperties {
  const line = (strut ?? spec).lineHeight;
  return {
    fontFamily: sourceFontFamily(spec),
    fontSize: rem(spec.size),
    fontWeight: spec.weight,
    lineHeight: line ? rem(line) : 'normal',
    letterSpacing: spec.letterSpacing ? rem(spec.letterSpacing) : 0,
    color: withOpacity(spec.color),
    textDecoration: spec.decoration === 'underline' ? 'underline' : spec.decoration === 'lineThrough' ? 'line-through' : 'none',
    fontStyle: 'normal',
    fontKerning: 'normal',
  };
}

export interface SourceTextProps {
  text?: string;
  /** Mixed-style runs; each run's spec is complete, the base spec sets the line box. */
  runs?: readonly (readonly [string, TextSpec])[];
  style: TextSpec;
  align?: 'left' | 'right' | 'center' | 'justify';
  /** Fixed-width source text box wraps; auto-width stays on one line. */
  wrap?: boolean;
}

export function SourceText({ text, runs, style, align = 'left', wrap = false }: SourceTextProps) {
  return (
    <div data-df-text="" style={{
      ...sourceTextStyle(style), margin: 0, textAlign: align,
      whiteSpace: wrap ? 'pre-wrap' : 'pre', overflowWrap: wrap ? 'break-word' : 'normal',
      WebkitFontSmoothing: 'antialiased',
    } as React.CSSProperties}>
      {runs ? runs.map(([t, s], i) => (
        // Forced strut (as Sketch/Figma and the Flutter primitive): a run never
        // grows the line box set by the base style; zero line-height spans
        // still paint their glyphs on the shared baseline.
        <span key={i} style={{ ...sourceTextStyle(s, style), lineHeight: style.lineHeight ? 0 : 'normal' }}>{t}</span>
      )) : text}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Assets, placeholders, effects

/** Normalises bundler image imports (string or `{ src }`). */
export function assetUrl(value: string | { src: string } | { default: string }): string {
  if (typeof value === 'string') return value;
  return 'src' in value ? value.src : value.default;
}

export function SourceAsset({ src, exportRect, alt = '' }: { src: string; exportRect?: readonly [number, number, number, number]; alt?: string }) {
  const style: React.CSSProperties = exportRect
    ? { position: 'absolute', left: exportRect[0], top: exportRect[1], width: exportRect[2], height: exportRect[3] }
    : { ...FILL, width: '100%', height: '100%' };
  return (
    <div style={{ ...FILL, overflow: 'visible' }}>
      <img src={src} alt={alt} draggable={false} data-df-asset={exportRect ? exportRect.join(' ') : ''} style={{ ...style, display: 'block', objectFit: 'fill', maxWidth: 'none' }} />
    </div>
  );
}

export function SourcePlaceholder({ nodeId, label = '设计素材未切图' }: { nodeId: string; label?: string }) {
  return (
    <div role="img" data-df-placeholder={nodeId} aria-label={`${label} (${nodeId})`} style={{
      ...FILL, background: '#FFE5EA', boxShadow: 'inset 0 0 0 1px #FF4D6D', overflow: 'hidden',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <span style={{ fontSize: 10, lineHeight: 1.2, color: '#C52245', padding: 2, whiteSpace: 'nowrap', fontFamily: SourceFonts.systemStack }}>{label}</span>
    </div>
  );
}

type WrapProps = { fill?: boolean; children?: React.ReactNode };
const box = (fill?: boolean, extra?: React.CSSProperties): React.CSSProperties =>
  fill ? { ...FILL, ...extra } : { position: 'relative', ...extra };

export function SourceOpacity({ value, fill, children }: WrapProps & { value: number }) {
  return <div data-df-opacity={value} style={box(fill, { opacity: value })}>{children}</div>;
}

export function SourceFlip({ x, y, fill, children }: WrapProps & { x?: boolean; y?: boolean }) {
  return <div style={box(fill, { transform: `scale(${x ? -1 : 1}, ${y ? -1 : 1})` })}>{children}</div>;
}

export function SourceLayerBlur({ radius, fill, children }: WrapProps & { radius: number }) {
  const sigma = radius * FidelityEffectMapping.layerBlurSigmaPerRadius;
  return <div data-df-layer-blur={radius} style={box(fill, sigma > 0 ? { filter: `blur(${px(sigma)})` } : undefined)}>{children}</div>;
}

export function SourceBackdropBlur({ radius, shape, saturation = 1, fill = true, children }: WrapProps & {
  radius: number; shape?: SourceShape; saturation?: number;
}) {
  const sigma = radius * FidelityEffectMapping.backgroundBlurSigmaPerRadius;
  const [clip, defs] = useShapeClip(shape ?? { kind: 'rect' });
  const filter = `blur(${px(sigma)})${Math.abs(saturation - 1) > 1e-6 ? ` saturate(${fmt(saturation)})` : ''}`;
  // Only the backdrop sample is clipped to the shape; the layer itself (its
  // fills and outer shadows) paints unclipped on top.
  return (
    <div data-df-backdrop={radius} data-df-saturation={saturation} style={box(fill)}>
      {defs}
      <div aria-hidden style={{ ...FILL, ...clip, backdropFilter: filter, WebkitBackdropFilter: filter } as React.CSSProperties} />
      {children}
    </div>
  );
}

/** Clips children to a mask layer's shape (mask groups). */
export function SourceClip({ shape, children }: { shape: SourceShape; children?: React.ReactNode }) {
  const [clip, defs] = useShapeClip(shape);
  return <div data-df-clip={shape.kind} style={{ ...FILL, ...clip }}>{defs}{children}</div>;
}

// ---------------------------------------------------------------------------
// Layout

type Len = number | string | null | undefined;
const len = (v: Len) => (typeof v === 'number' ? px(v) : v ?? undefined);

/** Design value plus the top safe-area change (root `top`, or the height of a
 *  background drawn under the status bar); `floor` clamps it from below. */
export const dy = (v: number, floor?: number) => clampCalc(`calc(var(--df-dy, 0px) + ${px(v)})`, floor);
/** Design value plus the bottom safe-area change (footer `bottom` / height). */
export const dyBottom = (v: number, floor?: number) => clampCalc(`calc(var(--df-dy-bottom, 0px) + ${px(v)})`, floor);
const clampCalc = (value: string, floor?: number) => (floor == null ? value : `max(${px(floor)}, ${value})`);

export function Placed(props: { left?: Len; top?: Len; right?: Len; bottom?: Len; width?: Len; height?: Len; children?: React.ReactNode }) {
  const { children, ...edges } = props;
  const style: React.CSSProperties = { position: 'absolute' };
  for (const [k, v] of Object.entries(edges)) (style as Record<string, unknown>)[k] = len(v as Len);
  return <div style={style}>{children}</div>;
}

export function Fill({ children }: { children?: React.ReactNode }) {
  return <div style={FILL}>{children}</div>;
}

/** Horizontally centred child at the top (Align.topCenter). */
export function AlignTopCenter({ children }: { children?: React.ReactNode }) {
  return <div style={{ display: 'flex', justifyContent: 'center', height: '100%' }}>{children}</div>;
}

export function Sized({ width, children }: { width: number; children?: React.ReactNode }) {
  return <div style={{ position: 'relative', width: px(width), flexShrink: 0 }}>{children}</div>;
}

export interface SceneOverrides {
  /** Replacement content keyed by source node id; drawn in the node frame. */
  overrides?: Readonly<Record<string, () => React.ReactNode>>;
  /** Click handlers keyed by source node id. */
  onTap?: Readonly<Record<string, () => void>>;
}

const OverridesContext = React.createContext<SceneOverrides>({});

/**
 * One source layer. `fill` boxes fill the placed frame; text keeps its
 * intrinsic size. Scene overrides replace the content inside the same frame.
 */
export function SourceNode({ id, fill, children }: { id: string; fill?: boolean; children?: React.ReactNode }) {
  const { overrides, onTap } = React.useContext(OverridesContext);
  const override = overrides?.[id];
  const tap = onTap?.[id];
  return (
    <div data-node-id={id} onClick={tap} style={box(fill, tap ? { cursor: 'pointer' } : undefined)}>
      {override ? override() : children}
    </div>
  );
}

export interface SceneProps extends SceneOverrides {
  designSize: Vec;
  /** Safe-area insets drawn in the design (status bar / home indicator). */
  designPadding: { top: number; bottom: number };
  /** Follow the device safe area (default); false keeps design coordinates. */
  adaptSafeArea?: boolean;
  footer?: React.ReactNode;
  children?: React.ReactNode;
}

/**
 * Full-screen page frame. Root layers move with the safe area
 * (`--df-safe-top` / `--df-safe-bottom`, default `env(safe-area-inset-*)`),
 * the body scrolls when the viewport is shorter than the design, and
 * footers stay pinned above the bottom inset. Give it a full-height parent.
 */
export function SourceScene({ designSize, designPadding, adaptSafeArea = true, footer, children, overrides, onTap }: SceneProps) {
  const top = adaptSafeArea ? `calc(var(--df-safe-top, env(safe-area-inset-top, 0px)) - ${px(designPadding.top)})` : '0px';
  const bottom = adaptSafeArea ? `calc(var(--df-safe-bottom, env(safe-area-inset-bottom, 0px)) - ${px(designPadding.bottom)})` : '0px';
  const natural = `calc(${px(designSize[1])} + var(--df-dy) + var(--df-dy-bottom))`;
  const value = React.useMemo(() => ({ overrides, onTap }), [overrides, onTap]);
  return (
    <OverridesContext.Provider value={value}>
    <div data-df-scene="" style={{
      position: 'relative', width: '100%', height: '100%', overflow: 'hidden',
      '--df-dy': top, '--df-dy-bottom': bottom,
    } as React.CSSProperties}>
      <div data-df-scroll="" style={{ ...FILL, overflowX: 'hidden', overflowY: 'auto', scrollbarWidth: 'none' } as React.CSSProperties}>
        <div style={{ position: 'relative', height: `max(100%, ${natural})` }}>{children}</div>
      </div>
      {footer}
    </div>
    </OverridesContext.Provider>
  );
}
