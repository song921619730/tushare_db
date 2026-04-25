// Interfaces page — table with filters, sorting, detail drawer

const { useState: useStateIf, useMemo: useMemoIf } = React;

function Interfaces({ chartStyle }) {
  const [query, setQuery] = useStateIf("");
  const [catFilter, setCatFilter] = useStateIf("ALL");
  const [statusFilter, setStatusFilter] = useStateIf("ALL");
  const [sort, setSort] = useStateIf({ key: "rows", dir: "desc" });
  const [selected, setSelected] = useStateIf(null);
  const [checked, setChecked] = useStateIf(new Set());

  const filtered = useMemoIf(() => {
    let rows = INTERFACE_ROWS;
    if (query) {
      const q = query.toLowerCase();
      rows = rows.filter(r => r.name.toLowerCase().includes(q) || r.table.toLowerCase().includes(q) || r.cat.includes(q));
    }
    if (catFilter !== "ALL") rows = rows.filter(r => r.cat === catFilter);
    if (statusFilter !== "ALL") rows = rows.filter(r => r.status === statusFilter);
    rows = [...rows].sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key];
      if (typeof av === "number") return sort.dir === "asc" ? av - bv : bv - av;
      return sort.dir === "asc" ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
    return rows;
  }, [query, catFilter, statusFilter, sort]);

  const toggleSort = (key) => {
    setSort(s => s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "desc" });
  };

  const toggleCheck = (id) => {
    setChecked(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const cols = [
    { key: "name",     label: "接口 / interface", w: "minmax(160px, 1.4fr)", sort: true, align: "left" },
    { key: "cat",      label: "分类",            w: "90px",                   sort: true, align: "left" },
    { key: "pri",      label: "优先",            w: "60px",                   sort: true, align: "left" },
    { key: "mode",     label: "模式",            w: "90px",                   sort: true, align: "left" },
    { key: "table",    label: "表名",            w: "minmax(140px, 1fr)",     sort: true, align: "left" },
    { key: "status",   label: "状态",            w: "110px",                  sort: true, align: "left" },
    { key: "lastSync", label: "最后同步",        w: "160px",                  sort: true, align: "left" },
    { key: "rows",     label: "总行数",          w: "120px",                  sort: true, align: "right" },
    { key: "spark",    label: "近 14d",          w: "110px",                  sort: false, align: "right" },
    { key: "durMs",    label: "耗时",            w: "90px",                   sort: true, align: "right" },
  ];
  const gridTemplate = cols.map(c => c.w).join(" ");

  return (
    <div style={{ display: "flex", height: "100%", minHeight: 0 }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0,
        padding: "var(--pad-lg)", gap: "var(--gap)", overflow: "hidden" }}>

        {/* Header */}
        <div style={{ paddingBottom: "var(--pad)", borderBottom: "1px solid var(--line)" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
            letterSpacing: "0.14em", textTransform: "uppercase" }}>/ interfaces — 接口同步状态</div>
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: 12 }}>
            <h1 style={{ fontSize: "clamp(28px, 3.2vw, 44px)", fontWeight: 400, letterSpacing: "-0.02em",
              fontFamily: "var(--font-display)", lineHeight: 1 }}>
              {filtered.length} <span style={{ color: "var(--mute)" }}>of {INTERFACE_ROWS.length}</span> interfaces
            </h1>
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              {checked.size > 0 && (
                <>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--accent)" }}>
                    {checked.size} selected
                  </span>
                  <button style={{
                    fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
                    padding: "8px 14px", border: "1px solid var(--accent)", color: "var(--accent)",
                    borderRadius: "var(--radius-sm)" }}>↻ 回补</button>
                  <button style={{
                    fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
                    padding: "8px 14px", border: "1px solid var(--fg)", color: "var(--fg)",
                    borderRadius: "var(--radius-sm)" }}>✓ 验证</button>
                </>
              )}
              <button style={{
                fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase",
                padding: "8px 14px", background: "var(--fg)", color: "var(--bg)",
                borderRadius: "var(--radius-sm)" }}>+ 新增</button>
            </div>
          </div>
        </div>

        {/* Filters row */}
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 280px", minWidth: 220, maxWidth: 360, position: "relative" }}>
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="搜索接口名 / 表名 / 分类…"
              style={{
                width: "100%", padding: "10px 14px 10px 36px",
                background: "var(--panel)", border: "1px solid var(--line)",
                borderRadius: "var(--radius-sm)", color: "var(--fg)",
                fontFamily: "var(--font-mono)", fontSize: 12, outline: "none",
              }}
              onFocus={e => e.target.style.borderColor = "var(--accent)"}
              onBlur={e => e.target.style.borderColor = "var(--line)"}
            />
            <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)",
              color: "var(--mute)", fontSize: 14 }}>⌕</span>
          </div>

          <FilterChips
            label="分类"
            value={catFilter}
            onChange={setCatFilter}
            options={[["ALL", "全部"], ...INTERFACE_CATEGORIES.map(c => [c, c])]}
          />
          <FilterChips
            label="状态"
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              ["ALL", "全部"], ["done", "done"], ["running", "running"],
              ["partial", "partial"], ["failed", "failed"], ["pending", "pending"],
            ]}
          />
        </div>

        {/* Table */}
        <div style={{
          flex: 1, minHeight: 0, overflow: "auto",
          border: "1px solid var(--line)",
          borderRadius: "var(--radius)",
          background: "var(--panel)",
        }}>
          {/* header */}
          <div style={{
            display: "grid", gridTemplateColumns: `44px ${gridTemplate}`,
            padding: "14px 16px", gap: 12,
            borderBottom: "1px solid var(--line)",
            position: "sticky", top: 0, background: "var(--panel)", zIndex: 2,
          }}>
            <input type="checkbox"
              checked={checked.size > 0 && checked.size === filtered.length}
              onChange={e => setChecked(e.target.checked ? new Set(filtered.map(r => r.id)) : new Set())}
              style={{ accentColor: "var(--accent)" }}
            />
            {cols.map(c => (
              <button key={c.key}
                disabled={!c.sort}
                onClick={() => c.sort && toggleSort(c.key)}
                style={{
                  textAlign: c.align, fontFamily: "var(--font-mono)", fontSize: 10,
                  letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--mute)",
                  cursor: c.sort ? "pointer" : "default",
                  display: "flex", alignItems: "center", gap: 4,
                  justifyContent: c.align === "right" ? "flex-end" : "flex-start",
                }}>
                {c.label}
                {sort.key === c.key && <span style={{ color: "var(--accent)" }}>{sort.dir === "asc" ? "↑" : "↓"}</span>}
              </button>
            ))}
          </div>
          {/* rows */}
          {filtered.map((r, i) => (
            <div key={r.id}
              onClick={() => setSelected(r)}
              style={{
                display: "grid", gridTemplateColumns: `44px ${gridTemplate}`,
                padding: "12px 16px", gap: 12, alignItems: "center",
                borderBottom: i === filtered.length - 1 ? "none" : "1px solid var(--line)",
                cursor: "pointer",
                background: selected && selected.id === r.id ? "var(--panel-soft)" : "transparent",
                transition: "background 120ms",
              }}
              onMouseEnter={e => { if (!selected || selected.id !== r.id) e.currentTarget.style.background = "var(--panel-soft)"; }}
              onMouseLeave={e => { if (!selected || selected.id !== r.id) e.currentTarget.style.background = "transparent"; }}
            >
              <input type="checkbox"
                checked={checked.has(r.id)}
                onClick={e => e.stopPropagation()}
                onChange={() => toggleCheck(r.id)}
                style={{ accentColor: "var(--accent)" }}
              />
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.name}</span>
              <span style={{ fontSize: 12, color: "var(--mute)" }}>{r.cat}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11,
                color: r.pri === "P0" ? "var(--accent)" : "var(--mute)",
                fontWeight: r.pri === "P0" ? 600 : 400 }}>{r.pri}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>{r.mode}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--mute)",
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.table}</span>
              <StatusBadge status={r.status} />
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>{r.lastSync}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, textAlign: "right",
                fontVariantNumeric: "tabular-nums" }}>{r.rows.toLocaleString()}</span>
              <span style={{ display: "flex", justifyContent: "flex-end" }}>
                <Sparkline data={r.sparkline} w={100} h={22} chartStyle={chartStyle} />
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, textAlign: "right",
                color: "var(--mute)" }}>{r.durMs ? (r.durMs/1000).toFixed(1) + "s" : "—"}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Detail drawer */}
      {selected && <InterfaceDrawer row={selected} onClose={() => setSelected(null)} chartStyle={chartStyle} />}
    </div>
  );
}

function FilterChips({ label, value, onChange, options }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
        letterSpacing: "0.12em", textTransform: "uppercase", whiteSpace: "nowrap" }}>{label}</span>
      <div style={{ display: "flex", gap: 0, border: "1px solid var(--line)",
        borderRadius: "var(--radius-sm)", overflow: "hidden" }}>
        {options.map(([k, l], i) => (
          <button key={k}
            onClick={() => onChange(k)}
            style={{
              padding: "6px 10px", fontFamily: "var(--font-mono)", fontSize: 11,
              background: value === k ? "var(--fg)" : "transparent",
              color: value === k ? "var(--bg)" : "var(--mute)",
              borderRight: i < options.length - 1 ? "1px solid var(--line)" : "none",
              letterSpacing: "0.04em", whiteSpace: "nowrap",
            }}>{l}</button>
        ))}
      </div>
    </div>
  );
}

function InterfaceDrawer({ row, onClose, chartStyle }) {
  // Mock last 10 runs
  const runs = React.useMemo(() => Array.from({ length: 10 }, (_, i) => ({
    ts: `2026-04-${String(25 - i).padStart(2, "0")} ${String(14 + (i%4)).padStart(2,"0")}:${String((i*7)%60).padStart(2,"0")}:${String((i*11)%60).padStart(2,"0")}`,
    rows: Math.floor(row.rows / 200 + (Math.random() - 0.3) * 20000),
    dur: Math.floor(row.durMs * (0.8 + Math.random() * 0.4)),
    status: i === 0 ? row.status : (Math.random() > 0.15 ? "done" : Math.random() > 0.5 ? "partial" : "failed"),
  })), [row.id]);

  const scopes = React.useMemo(() => {
    const codes = ["000001.SZ", "000002.SZ", "000858.SZ", "600000.SH", "600036.SH",
      "600519.SH", "600887.SH", "601318.SH", "601398.SH", "601857.SH",
      "300015.SZ", "300059.SZ", "300750.SZ", "300760.SZ"];
    return codes.map(c => ({
      scope: c,
      status: Math.random() > 0.12 ? "done" : Math.random() > 0.5 ? "partial" : "failed",
      rows: Math.floor(Math.random() * 8000 + 1000),
      last: `2026-04-25 ${String(14 + Math.floor(Math.random()*2)).padStart(2,"0")}:${String(Math.floor(Math.random()*60)).padStart(2,"0")}`,
    }));
  }, [row.id]);

  return (
    <aside style={{
      width: 460, flexShrink: 0, height: "100%",
      borderLeft: "1px solid var(--line)",
      background: "var(--panel)", overflow: "auto",
      display: "flex", flexDirection: "column",
      animation: "slideInR 240ms cubic-bezier(.2,.8,.2,1)",
    }}>
      <header style={{
        padding: "var(--pad)", borderBottom: "1px solid var(--line)",
        display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 14,
        position: "sticky", top: 0, background: "var(--panel)", zIndex: 1,
      }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
            letterSpacing: "0.12em", textTransform: "uppercase" }}>interface · {row.cat}</div>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 400,
            letterSpacing: "-0.02em", marginTop: 6, lineHeight: 1.05 }}>{row.name}</h2>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--mute)", marginTop: 6 }}>
            tushare.{row.table}
          </div>
        </div>
        <button onClick={onClose} style={{
          width: 32, height: 32, border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
          color: "var(--fg)", fontFamily: "var(--font-mono)", fontSize: 14,
          display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
        }}>×</button>
      </header>

      <div style={{ padding: "var(--pad)", display: "flex", flexDirection: "column", gap: 20 }}>
        {/* quick stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          {[
            ["状态", <StatusBadge status={row.status} />],
            ["优先", <span style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 500,
              color: row.pri === "P0" ? "var(--accent)" : "var(--fg)" }}>{row.pri}</span>],
            ["模式", <span style={{ fontFamily: "var(--font-mono)", fontSize: 14 }}>{row.mode}</span>],
          ].map(([k, v], i) => (
            <div key={i} style={{ padding: "10px 0", borderTop: "1px solid var(--line)" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
                letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>{k}</div>
              {v}
            </div>
          ))}
        </div>

        {/* Big row number */}
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
            letterSpacing: "0.12em", textTransform: "uppercase" }}>总行数 · rows</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 48, fontWeight: 400,
            letterSpacing: "-0.03em", marginTop: 4, lineHeight: 1 }}>{row.rows.toLocaleString()}</div>
          <div style={{ marginTop: 10 }}>
            <Sparkline data={row.sparkline} w={420} h={40} chartStyle={chartStyle} />
          </div>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button style={{
            flex: 1, padding: "10px", fontFamily: "var(--font-mono)", fontSize: 11,
            letterSpacing: "0.1em", textTransform: "uppercase",
            background: "var(--accent)", color: "var(--bg)",
            borderRadius: "var(--radius-sm)", fontWeight: 500,
          }}>↻ 回补此接口</button>
          <button style={{
            flex: 1, padding: "10px", fontFamily: "var(--font-mono)", fontSize: 11,
            letterSpacing: "0.1em", textTransform: "uppercase",
            border: "1px solid var(--fg)", color: "var(--fg)",
            borderRadius: "var(--radius-sm)",
          }}>✓ 行数验证</button>
        </div>

        {/* recent runs */}
        <section>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 10 }}>
            <h3 style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em",
              textTransform: "uppercase", color: "var(--fg)", fontWeight: 500 }}>近 10 次运行 · recent runs</h3>
          </div>
          <div style={{ display: "flex", flexDirection: "column", border: "1px solid var(--line)",
            borderRadius: "var(--radius-sm)" }}>
            {runs.map((r, i) => (
              <div key={i} style={{
                padding: "9px 12px",
                display: "grid", gridTemplateColumns: "auto 1fr auto auto",
                gap: 10, alignItems: "center",
                borderBottom: i === runs.length - 1 ? "none" : "1px solid var(--line)",
                fontFamily: "var(--font-mono)", fontSize: 11,
              }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%",
                  background: r.status === "done" ? "var(--pos)" :
                              r.status === "running" ? "var(--accent)" :
                              r.status === "partial" ? "var(--warn)" :
                              r.status === "failed" ? "var(--neg)" : "var(--mute)" }} />
                <span style={{ color: "var(--mute)" }}>{r.ts}</span>
                <span style={{ color: "var(--fg)" }}>{r.rows.toLocaleString()}</span>
                <span style={{ color: "var(--mute)", minWidth: 56, textAlign: "right" }}>{(r.dur/1000).toFixed(1)}s</span>
              </div>
            ))}
          </div>
        </section>

        {/* Scope keys */}
        <section>
          <h3 style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em",
            textTransform: "uppercase", color: "var(--fg)", fontWeight: 500, marginBottom: 10 }}>
            scope_key · top 14
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            {scopes.map((s, i) => (
              <div key={i} style={{
                padding: "7px 10px",
                border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
                display: "flex", alignItems: "center", gap: 8,
                fontFamily: "var(--font-mono)", fontSize: 11,
              }}>
                <span style={{ width: 5, height: 5,
                  background: s.status === "done" ? "var(--pos)" : s.status === "partial" ? "var(--warn)" : "var(--neg)" }} />
                <span style={{ flex: 1, color: "var(--fg)" }}>{s.scope}</span>
                <span style={{ color: "var(--mute)" }}>{(s.rows/1000).toFixed(1)}k</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </aside>
  );
}

Object.assign(window, { Interfaces });
