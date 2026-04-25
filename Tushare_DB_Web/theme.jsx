// 5 palettes — each is a committed aesthetic direction, not just recolored pixels.
// Every palette defines: bg, panel, fg, mute, line, accent, accent2 (tension), pos, neg, warn
const PALETTES = {
  paper: {
    name: "Paper",
    cn: "素白",
    desc: "Warm off-white. Ink black. One drop of crimson.",
    bg: "#f3f0e8",
    panel: "#ebe7dc",
    panelSoft: "#f8f5ee",
    fg: "#0e0e0e",
    mute: "#6b665a",
    line: "#c9c3b4",
    accent: "#d94326",
    accent2: "#0e0e0e",
    pos: "#2b6b3f",
    neg: "#d94326",
    warn: "#b8860b",
    chartTrack: "#d8d3c4",
  },
  graphite: {
    name: "Graphite",
    cn: "石墨",
    desc: "Deep charcoal. Bone type. Electric green pulse.",
    bg: "#0f0f10",
    panel: "#161617",
    panelSoft: "#1c1c1e",
    fg: "#ebe7df",
    mute: "#7a7670",
    line: "#262627",
    accent: "#b4f23a",
    accent2: "#ebe7df",
    pos: "#b4f23a",
    neg: "#ff5a4d",
    warn: "#f2b33a",
    chartTrack: "#222223",
  },
  bone: {
    name: "Bone",
    cn: "骨色",
    desc: "Cream paper. Ink lines. Burnt orange warmth.",
    bg: "#efe9dd",
    panel: "#e5dfd1",
    panelSoft: "#f4efe4",
    fg: "#161413",
    mute: "#7a6f5f",
    line: "#c5bca8",
    accent: "#c7501f",
    accent2: "#3a3228",
    pos: "#5a6f2d",
    neg: "#c7501f",
    warn: "#a57c15",
    chartTrack: "#d6cfbe",
  },
  midnight: {
    name: "Midnight",
    cn: "子夜",
    desc: "Deep navy. Ivory text. Cyan signal.",
    bg: "#0a0e14",
    panel: "#10151c",
    panelSoft: "#151b23",
    fg: "#e8e6df",
    mute: "#6b7280",
    line: "#1c2430",
    accent: "#4ad8e6",
    accent2: "#e8e6df",
    pos: "#4ad88a",
    neg: "#ff6b6b",
    warn: "#ffcf4a",
    chartTrack: "#1a222e",
  },
  editorial: {
    name: "Editorial",
    cn: "编辑",
    desc: "Pure white. Near-black. Magenta shock.",
    bg: "#ffffff",
    panel: "#fafafa",
    panelSoft: "#ffffff",
    fg: "#0a0a0a",
    mute: "#8a8a8a",
    line: "#e5e5e5",
    accent: "#e6007e",
    accent2: "#0a0a0a",
    pos: "#007e3a",
    neg: "#e6007e",
    warn: "#d97706",
    chartTrack: "#ededed",
  },
};

const FONTS = {
  sans: "'Inter', 'Noto Sans SC', system-ui, sans-serif",
  mono: "'JetBrains Mono', 'IBM Plex Mono', 'Noto Sans SC', monospace",
  serif: "'Fraunces', 'Noto Serif SC', Georgia, serif",
};

// Apply theme CSS variables to document root
function applyTheme(palette, saturation, radius, density, fontBody) {
  const p = PALETTES[palette] || PALETTES.paper;
  const root = document.documentElement;
  // Saturation adjustment on accent
  const accent = adjustSaturation(p.accent, saturation);
  root.style.setProperty("--bg", p.bg);
  root.style.setProperty("--panel", p.panel);
  root.style.setProperty("--panel-soft", p.panelSoft);
  root.style.setProperty("--fg", p.fg);
  root.style.setProperty("--mute", p.mute);
  root.style.setProperty("--line", p.line);
  root.style.setProperty("--accent", accent);
  root.style.setProperty("--accent-2", p.accent2);
  root.style.setProperty("--pos", p.pos);
  root.style.setProperty("--neg", p.neg);
  root.style.setProperty("--warn", p.warn);
  root.style.setProperty("--chart-track", p.chartTrack);
  root.style.setProperty("--radius", radius + "px");
  root.style.setProperty("--radius-sm", Math.max(0, radius * 0.5) + "px");
  // density
  const d = density === "compact" ? 0.85 : density === "comfortable" ? 1.15 : 1;
  root.style.setProperty("--d", d);
  root.style.setProperty("--pad", (20 * d) + "px");
  root.style.setProperty("--pad-lg", (32 * d) + "px");
  root.style.setProperty("--gap", (16 * d) + "px");
  root.style.setProperty("--row-h", (40 * d) + "px");
  // fonts
  root.style.setProperty("--font-body", FONTS[fontBody] || FONTS.sans);
  root.style.setProperty("--font-mono", FONTS.mono);
  root.style.setProperty("--font-display", fontBody === "serif" ? FONTS.serif : FONTS[fontBody] || FONTS.sans);
}

// hex -> hsl -> adjust sat -> hex
function adjustSaturation(hex, mul) {
  if (mul === 1) return hex;
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) { h = s = 0; }
  else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  s = Math.max(0, Math.min(1, s * mul));
  // hsl->rgb
  const hue2rgb = (p, q, t) => {
    if (t < 0) t += 1; if (t > 1) t -= 1;
    if (t < 1/6) return p + (q - p) * 6 * t;
    if (t < 1/2) return q;
    if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
    return p;
  };
  let r2, g2, b2;
  if (s === 0) { r2 = g2 = b2 = l; }
  else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r2 = hue2rgb(p, q, h + 1/3);
    g2 = hue2rgb(p, q, h);
    b2 = hue2rgb(p, q, h - 1/3);
  }
  const toHex = x => Math.round(x * 255).toString(16).padStart(2, "0");
  return "#" + toHex(r2) + toHex(g2) + toHex(b2);
}

Object.assign(window, { PALETTES, FONTS, applyTheme });
