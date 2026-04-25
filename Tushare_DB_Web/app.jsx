// App shell — sidebar + main content + tweaks panel

const { useState, useEffect } = React;

const DEFAULTS = /*EDITMODE-BEGIN*/{
  "palette": "paper",
  "fontBody": "sans",
  "radius": 4,
  "density": "medium",
  "saturation": 1,
  "chartStyle": "filled",
  "sidebarExpanded": true,
  "page": "dashboard"
}/*EDITMODE-END*/;

const PAGES = [
  { id: "dashboard",  label: "Dashboard",   cn: "总览",     num: "01", icon: "◎" },
  { id: "interfaces", label: "Interfaces",  cn: "接口状态", num: "02", icon: "≡" },
  { id: "data",       label: "Data Viewer", cn: "数据浏览", num: "03", icon: "▦" },
  { id: "scheduler",  label: "Scheduler",   cn: "调度任务", num: "04", icon: "⧗" },
  { id: "audit",      label: "Audit",       cn: "审计日志", num: "05", icon: "⎔" },
  { id: "verify",     label: "Verify",      cn: "验证诊断", num: "06", icon: "✓" },
  { id: "settings",   label: "Settings",    cn: "连接设置", num: "07", icon: "⚙" },
];

function App() {
  const [tweaks, setTweak] = useTweaks(DEFAULTS);
  const [page, setPage] = useState(tweaks.page || "dashboard");

  useEffect(() => {
    applyTheme(tweaks.palette, tweaks.saturation, tweaks.radius, tweaks.density, tweaks.fontBody);
  }, [tweaks.palette, tweaks.saturation, tweaks.radius, tweaks.density, tweaks.fontBody]);

  return (
    <div style={{ display: "flex", height: "100vh", width: "100vw", background: "var(--bg)", color: "var(--fg)" }}>
      <Sidebar expanded={tweaks.sidebarExpanded} page={page} setPage={setPage}
        onToggle={() => setTweak("sidebarExpanded", !tweaks.sidebarExpanded)} />

      <main style={{ flex: 1, minWidth: 0, overflow: "auto", position: "relative" }}>
        {page === "dashboard" && <Dashboard chartStyle={tweaks.chartStyle} />}
        {page === "interfaces" && <Interfaces chartStyle={tweaks.chartStyle} />}
        {page === "data" && <DataViewer chartStyle={tweaks.chartStyle} />}
        {page === "scheduler" && <Scheduler chartStyle={tweaks.chartStyle} />}
        {page === "audit" && <Audit chartStyle={tweaks.chartStyle} />}
        {page === "verify" && <Verify chartStyle={tweaks.chartStyle} />}
        {page === "settings" && <Settings chartStyle={tweaks.chartStyle} />}
      </main>

      <TweaksPanelContent tweaks={tweaks} setTweak={setTweak} />
    </div>
  );
}

function Sidebar({ expanded, page, setPage, onToggle }) {
  const w = expanded ? 220 : 64;
  return (
    <aside style={{
      width: w, flexShrink: 0, transition: "width 240ms cubic-bezier(.2,.8,.2,1)",
      borderRight: "1px solid var(--line)", background: "var(--panel)",
      display: "flex", flexDirection: "column",
      position: "relative", overflow: "hidden",
    }}>
      {/* Brand */}
      <div style={{
        padding: expanded ? "22px 20px" : "22px 12px",
        borderBottom: "1px solid var(--line)",
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <div style={{
          width: 28, height: 28, flexShrink: 0,
          background: "var(--accent)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: "var(--font-mono)", fontSize: 14, fontWeight: 700,
          color: "var(--bg)", borderRadius: "var(--radius-sm)",
        }}>T</div>
        {expanded && (
          <div style={{ minWidth: 0 }}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 16, fontWeight: 500,
              letterSpacing: "-0.01em", lineHeight: 1.1 }}>Tushare DB</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--mute)",
              letterSpacing: "0.14em", textTransform: "uppercase", marginTop: 2 }}>v1.0 · LAN</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "20px 8px", display: "flex", flexDirection: "column", gap: 2 }}>
        {expanded && (
          <div style={{ padding: "0 12px 12px", fontFamily: "var(--font-mono)", fontSize: 9,
            color: "var(--mute)", letterSpacing: "0.18em", textTransform: "uppercase" }}>Navigation</div>
        )}
        {PAGES.map(p => {
          const active = p.id === page;
          return (
            <button
              key={p.id}
              onClick={() => !p.disabled && setPage(p.id)}
              disabled={p.disabled}
              style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: expanded ? "10px 12px" : "10px",
                justifyContent: expanded ? "flex-start" : "center",
                background: active ? "var(--panel-soft)" : "transparent",
                borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
                color: active ? "var(--fg)" : p.disabled ? "var(--mute)" : "var(--fg)",
                opacity: p.disabled ? 0.4 : 1,
                cursor: p.disabled ? "not-allowed" : "pointer",
                borderRadius: 0,
                transition: "background 120ms",
                fontSize: 13,
                position: "relative",
              }}
              onMouseEnter={e => { if (!p.disabled && !active) e.currentTarget.style.background = "var(--panel-soft)"; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
            >
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--mute)",
                width: expanded ? 14 : 0, textAlign: "right", opacity: expanded ? 1 : 0,
                transition: "opacity 180ms",
              }}>{expanded && p.num}</span>
              <span style={{ fontSize: 16, width: 18, textAlign: "center", color: active ? "var(--accent)" : "var(--mute)" }}>{p.icon}</span>
              {expanded && (
                <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.02em",
                    fontWeight: active ? 500 : 400 }}>{p.label}</span>
                  <span style={{ fontSize: 10, color: "var(--mute)" }}>{p.cn}</span>
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Connection status */}
      <div style={{ borderTop: "1px solid var(--line)", padding: expanded ? 16 : 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: expanded ? "flex-start" : "center" }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--pos)",
            animation: "pulse 2s ease-in-out infinite", flexShrink: 0 }} />
          {expanded && (
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--fg)" }}>ClickHouse ▸ 8123</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--mute)", marginTop: 2 }}>ai_reader · read-only</div>
            </div>
          )}
        </div>
        <button onClick={onToggle} style={{
          marginTop: 14, width: "100%", padding: "6px",
          border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
          color: "var(--mute)", fontFamily: "var(--font-mono)", fontSize: 10,
          letterSpacing: "0.12em", textTransform: "uppercase",
        }}>{expanded ? "◂ collapse" : "▸"}</button>
      </div>
    </aside>
  );
}

function ComingSoon({ page }) {
  return (
    <div style={{ padding: "var(--pad-lg)", height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
        letterSpacing: "0.14em", textTransform: "uppercase" }}>/ {page.id}</div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", gap: 20 }}>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 120, fontWeight: 300,
          letterSpacing: "-0.04em", color: "var(--mute)", lineHeight: 1 }}>{page.num}</div>
        <div style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 400 }}>{page.label}</div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--mute)",
          letterSpacing: "0.14em", textTransform: "uppercase" }}>{page.cn} · coming in v2</div>
      </div>
    </div>
  );
}

// === Tweaks Panel ===
function TweaksPanelContent({ tweaks, setTweak }) {
  return (
    <TweaksPanel title="Tweaks">
      <TweakSection label="配色 · Palette" />
      <PaletteGrid value={tweaks.palette} onChange={v => setTweak("palette", v)} />

      <TweakSection label="字体 · Typography" />
      <TweakRadio label="Font" value={tweaks.fontBody} onChange={v => setTweak("fontBody", v)}
        options={[
          { value: "sans",  label: "Sans" },
          { value: "mono",  label: "Mono" },
          { value: "serif", label: "Serif" },
        ]} />

      <TweakSection label="外观 · Appearance" />
      <TweakSlider label="圆角 Radius" value={tweaks.radius} onChange={v => setTweak("radius", v)}
        min={0} max={20} step={1} unit="px" />
      <TweakRadio label="密度 Density" value={tweaks.density} onChange={v => setTweak("density", v)}
        options={[
          { value: "compact",     label: "Compact" },
          { value: "medium",      label: "Medium" },
          { value: "comfortable", label: "Comfort" },
        ]} />
      <TweakSlider label="饱和度 Saturation" value={tweaks.saturation} onChange={v => setTweak("saturation", v)}
        min={0} max={1.5} step={0.05} unit="×" />

      <TweakSection label="图表 · Charts" />
      <TweakRadio label="Chart style" value={tweaks.chartStyle} onChange={v => setTweak("chartStyle", v)}
        options={[
          { value: "filled", label: "Filled" },
          { value: "line",   label: "Line" },
          { value: "bars",   label: "Bars" },
        ]} />

      <TweakSection label="布局 · Layout" />
      <TweakToggle value={tweaks.sidebarExpanded} onChange={v => setTweak("sidebarExpanded", v)}
        label="侧边栏展开" />
    </TweaksPanel>
  );
}

function PaletteGrid({ value, onChange }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
      {Object.entries(PALETTES).map(([key, p]) => {
        const active = key === value;
        return (
          <button key={key} onClick={() => onChange(key)}
            style={{
              display: "flex", alignItems: "center", gap: 10, padding: 8,
              border: `1px solid ${active ? p.accent : "rgba(255,255,255,0.12)"}`,
              background: active ? `color-mix(in srgb, ${p.accent} 8%, transparent)` : "transparent",
              borderRadius: 4, cursor: "pointer", textAlign: "left",
            }}>
            {/* Swatch */}
            <div style={{ display: "flex", width: 46, height: 28, flexShrink: 0,
              border: "1px solid rgba(255,255,255,0.08)", overflow: "hidden", borderRadius: 2 }}>
              <div style={{ flex: 1, background: p.bg }} />
              <div style={{ flex: 1, background: p.panel }} />
              <div style={{ flex: 1, background: p.fg }} />
              <div style={{ width: 8, background: p.accent }} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, color: "#fff", fontWeight: 500 }}>
                {p.name} <span style={{ color: "rgba(255,255,255,0.5)", fontWeight: 400 }}>· {p.cn}</span>
              </div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.45)", marginTop: 2,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.desc}</div>
            </div>
            {active && <span style={{ color: p.accent, fontSize: 14 }}>●</span>}
          </button>
        );
      })}
    </div>
  );
}

// Inject global animations
const styleEl = document.createElement("style");
styleEl.textContent = `
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
  }
  @keyframes slideInR {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  main { animation: fadeIn 300ms ease-out; }
`;
document.head.appendChild(styleEl);

// Mount
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
