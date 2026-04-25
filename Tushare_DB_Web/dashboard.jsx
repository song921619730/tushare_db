// Dashboard view — Swiss-minimal, asymmetric grid

const { useMemo } = React;

function formatRows(n) {
  if (n >= 1e8) return (n / 1e8).toFixed(2) + "亿";
  if (n >= 1e4) return (n / 1e4).toFixed(1) + "万";
  return n.toLocaleString();
}

function Panel({ children, style, label, no = null, action = null }) {
  return (
    <section style={{
      background: "var(--panel)",
      border: "1px solid var(--line)",
      borderRadius: "var(--radius)",
      padding: "var(--pad)",
      display: "flex",
      flexDirection: "column",
      minWidth: 0,
      ...style,
    }}>
      {(label || no || action) && (
        <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: "calc(var(--gap) * 1.1)" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            {no && <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
              letterSpacing: "0.08em" }}>{no}</span>}
            {label && <h3 style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.12em",
              textTransform: "uppercase", color: "var(--fg)", whiteSpace: "nowrap" }}>{label}</h3>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

function StatusBadge({ status, size = "sm" }) {
  const map = {
    done:    { cn: "已完成", color: "var(--pos)",  fill: false },
    running: { cn: "运行中", color: "var(--accent)", fill: true, pulse: true },
    partial: { cn: "部分",   color: "var(--warn)", fill: false },
    failed:  { cn: "失败",   color: "var(--neg)",  fill: true },
    pending: { cn: "待执行", color: "var(--mute)", fill: false },
  };
  const m = map[status] || map.pending;
  const s = size === "lg";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      fontFamily: "var(--font-mono)",
      fontSize: s ? 12 : 11,
      padding: s ? "4px 8px" : "2px 6px",
      border: `1px solid ${m.color}`,
      color: m.color,
      background: m.fill ? `color-mix(in srgb, ${m.color} 12%, transparent)` : "transparent",
      borderRadius: "var(--radius-sm)",
      letterSpacing: "0.04em",
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: "50%",
        background: m.color,
        animation: m.pulse ? "pulse 1.6s ease-in-out infinite" : "none",
      }} />
      {status}
    </span>
  );
}

function Dashboard({ chartStyle }) {
  const totals = TOTALS;

  const donutSegments = [
    { label: "done",    value: STATUS_COUNTS.done || 0,    color: "var(--pos)" },
    { label: "running", value: STATUS_COUNTS.running || 0, color: "var(--accent)" },
    { label: "partial", value: STATUS_COUNTS.partial || 0, color: "var(--warn)" },
    { label: "failed",  value: STATUS_COUNTS.failed || 0,  color: "var(--neg)" },
    { label: "pending", value: STATUS_COUNTS.pending || 0, color: "var(--mute)" },
  ];
  const total = donutSegments.reduce((a, s) => a + s.value, 0);
  const donePct = Math.round(((STATUS_COUNTS.done || 0) / total) * 100);

  const run = CURRENT_RUN;
  const runPct = (run.unitsDone / run.unitsTotal) * 100;

  const statTiles = [
    { no: "01", label: "接口总数", key: "tables", val: totals.tables, sub: "interfaces" },
    { no: "02", label: "已同步", key: "tablesSynced", val: totals.tablesSynced, sub: `${Math.round(totals.tablesSynced/totals.tables*100)}% coverage` },
    { no: "03", label: "总行数", key: "totalRows", val: formatRows(totals.totalRows), sub: "rows across tables" },
    { no: "04", label: "存储占用", key: "storage", val: totals.storageGb, unit: "GB", sub: "compressed on disk" },
    { no: "05", label: "今日新增", key: "today", val: formatRows(totals.todayNewRows), sub: "rows today" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap)", padding: "var(--pad-lg)",
      minHeight: "100%" }}>

      {/* Hero row */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between",
        paddingBottom: "var(--pad)", borderBottom: "1px solid var(--line)" }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
            letterSpacing: "0.14em", textTransform: "uppercase" }}>/ dashboard — 总览</div>
          <h1 style={{ fontSize: "clamp(32px, 4vw, 56px)", fontWeight: 400, letterSpacing: "-0.02em",
            marginTop: 12, fontFamily: "var(--font-display)", lineHeight: 1 }}>
            A 股数据仓库 <span style={{ color: "var(--mute)" }}>/</span> <span style={{ color: "var(--accent)" }}>ai_reader</span>
          </h1>
          <p style={{ fontSize: 14, color: "var(--mute)", marginTop: 10, maxWidth: 560 }}>
            ClickHouse HTTP 8123 · 只读连接 · 最后刷新 <span style={{
              fontFamily: "var(--font-mono)", color: "var(--fg)" }}>2026-04-25 15:34:42</span>
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--gap)" }}>
          <LiveClock />
          <button style={{
            fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
            padding: "10px 18px", border: "1px solid var(--fg)", color: "var(--fg)",
            borderRadius: "var(--radius-sm)",
          }}>↻ refresh</button>
        </div>
      </div>

      {/* 5 stat tiles */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "var(--gap)" }}>
        {statTiles.map((t, i) => (
          <Panel key={i} label={t.label} no={t.no}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginTop: 6 }}>
              <div style={{
                fontFamily: "var(--font-display)", fontSize: "clamp(30px, 3vw, 44px)",
                fontWeight: 400, letterSpacing: "-0.03em", lineHeight: 1,
                whiteSpace: "nowrap",
              }}>{t.val}</div>
              {t.unit && <span style={{ fontFamily: "var(--font-mono)", fontSize: 14, color: "var(--mute)" }}>{t.unit}</span>}
            </div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
              marginTop: 10, letterSpacing: "0.08em" }}>{t.sub}</div>
          </Panel>
        ))}
      </div>

      {/* Second row — asymmetric: 2fr (health) + 3fr (trend) */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 3fr", gap: "var(--gap)" }}>
        <Panel label="同步健康度" no="06" action={
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>n = {total}</span>
        }>
          <div style={{ display: "flex", alignItems: "center", gap: 24, marginTop: 8, flex: 1 }}>
            <div style={{ position: "relative", flexShrink: 0 }}>
              <Donut segments={donutSegments} size={180} thickness={14} chartStyle={chartStyle} />
              <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center" }}>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 40, fontWeight: 400,
                  letterSpacing: "-0.03em", lineHeight: 1 }}>{donePct}%</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
                  marginTop: 4, letterSpacing: "0.1em" }}>HEALTHY</div>
              </div>
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
              {donutSegments.map((s, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10,
                  paddingBottom: 8, borderBottom: i === donutSegments.length - 1 ? "none" : "1px solid var(--line)" }}>
                  <span style={{ width: 10, height: 10, background: s.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", textTransform: "uppercase",
                    letterSpacing: "0.08em", flex: 1 }}>{s.label}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500 }}>{s.value}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
                    width: 42, textAlign: "right" }}>{total ? Math.round(s.value/total*100) : 0}%</span>
                </div>
              ))}
            </div>
          </div>
        </Panel>

        <Panel label="存储增长 — 近 7 日" no="07" action={
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--pos)" }}>+41.9% ↗</span>
        }>
          <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 8 }}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 400,
              letterSpacing: "-0.02em", lineHeight: 1 }}>{formatRows(TREND_7D[6].rows)}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>
              rows (cumulative) · 182 tables
            </div>
          </div>
          <div style={{ flex: 1, minHeight: 180 }}>
            <TrendLine data={TREND_7D} h={200} chartStyle={chartStyle} />
          </div>
        </Panel>
      </div>

      {/* Third row — current run + P0 + alerts */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.5fr 1.3fr", gap: "var(--gap)" }}>
        {/* Current run */}
        <Panel label="今日运行" no="08" action={<StatusBadge status="running" />}>
          <div style={{ marginTop: 4 }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>run_id</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, marginTop: 2,
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{run.id}</div>
          </div>
          <div style={{ marginTop: 20, display: "flex", gap: 16 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
                letterSpacing: "0.1em" }}>ELAPSED</div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 24, marginTop: 4,
                fontWeight: 400 }}>{Math.floor(run.elapsedMs/60000)}m {Math.floor((run.elapsedMs%60000)/1000)}s</div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
                letterSpacing: "0.1em" }}>ETA</div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 24, marginTop: 4,
                fontWeight: 400, color: "var(--accent)" }}>~{Math.floor(run.etaMs/60000)}m {Math.floor((run.etaMs%60000)/1000)}s</div>
            </div>
          </div>
          <div style={{ marginTop: "auto", paddingTop: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)",
              fontSize: 11, color: "var(--mute)", marginBottom: 8 }}>
              <span>→ {run.runningInterface}</span>
              <span>{run.unitsDone}/{run.unitsTotal} units</span>
            </div>
            <ProgressBar value={run.unitsDone} max={run.unitsTotal} showLabel={false} height={4} />
            <div style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: 11,
              marginTop: 6, color: "var(--fg)" }}>{runPct.toFixed(1)}%</div>
          </div>
        </Panel>

        {/* P0 priority */}
        <Panel label="P0 核心接口" no="09" action={
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>
            SLA · 4h
          </span>
        }>
          <div style={{ display: "flex", flexDirection: "column", gap: 0, marginTop: 4, flex: 1 }}>
            {P0_INTERFACES.map((p, i) => {
              const stale = p.status !== "done" && p.status !== "running";
              return (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "1fr auto auto", gap: 10,
                  padding: "10px 0",
                  borderBottom: i === P0_INTERFACES.length - 1 ? "none" : "1px solid var(--line)",
                  alignItems: "center",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%",
                      background: stale ? "var(--neg)" : p.status === "running" ? "var(--accent)" : "var(--pos)",
                      flexShrink: 0 }} />
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500 }}>{p.name}</span>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)" }}>{p.cat}</span>
                  </div>
                  <Sparkline data={p.sparkline} w={70} h={20} chartStyle={chartStyle} />
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
                    textAlign: "right", minWidth: 90 }}>{p.lastSync.slice(-8)}</span>
                </div>
              );
            })}
          </div>
        </Panel>

        {/* Alerts */}
        <Panel label="告警 — 近 24h" no="10" action={
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--neg)" }}>{ALERTS.length} events</span>
        }>
          <div style={{ display: "flex", flexDirection: "column", gap: 0, marginTop: 4, flex: 1 }}>
            {ALERTS.map((a, i) => {
              const col = a.level === "error" ? "var(--neg)" : a.level === "warn" ? "var(--warn)" : "var(--mute)";
              return (
                <div key={i} style={{
                  padding: "12px 0",
                  borderBottom: i === ALERTS.length - 1 ? "none" : "1px solid var(--line)",
                  display: "grid", gridTemplateColumns: "auto 1fr", gap: 14, alignItems: "start",
                }}>
                  <div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>{a.time}</div>
                    <div style={{ width: 4, height: 4, background: col, marginTop: 6 }} />
                  </div>
                  <div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: col,
                      fontWeight: 500, letterSpacing: "0.02em" }}>{a.interface}</div>
                    <div style={{ fontSize: 12, color: "var(--fg)", marginTop: 3, lineHeight: 1.45,
                      textWrap: "pretty" }}>{a.msg}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function LiveClock() {
  const [t, setT] = React.useState(new Date());
  React.useEffect(() => {
    const id = setInterval(() => setT(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const pad = n => String(n).padStart(2, "0");
  return (
    <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--fg)",
      letterSpacing: "0.06em", display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--pos)",
        animation: "pulse 2s ease-in-out infinite" }} />
      {pad(t.getHours())}:{pad(t.getMinutes())}:{pad(t.getSeconds())}
    </div>
  );
}

Object.assign(window, { Dashboard, Panel, StatusBadge, formatRows });
