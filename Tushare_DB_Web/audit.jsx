// Audit — API call log with date filter, heatmap, and detail table

function Audit({ chartStyle }) {
  const [range, setRange] = React.useState("today");
  const [filter, setFilter] = React.useState("all");
  const calls = API_CALLS;
  const stats = React.useMemo(() => {
    const total = calls.length;
    const success = calls.filter(c => c.status === "success").length;
    const failed = calls.filter(c => c.status === "failed").length;
    const rateLtd = calls.filter(c => c.status === "rate_limited").length;
    const totalMs = calls.reduce((a, c) => a + c.duration_ms, 0);
    const totalRows = calls.reduce((a, c) => a + c.rows, 0);
    return { total, success, failed, rateLtd, totalMs, totalRows, okRate: (success / total * 100).toFixed(1) };
  }, [calls]);

  const filtered = React.useMemo(() =>
    filter === "all" ? calls :
    filter === "failed" ? calls.filter(c => c.status === "failed" || c.status === "rate_limited") :
    calls.filter(c => c.status === filter),
  [calls, filter]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap)",
      padding: "var(--pad-lg)", minHeight: "100%" }}>
      <div style={{ paddingBottom: "var(--pad)", borderBottom: "1px solid var(--line)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
          letterSpacing: "0.14em", textTransform: "uppercase" }}>/ audit — API 调用审计</div>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: 12 }}>
          <h1 style={{ fontSize: "clamp(28px, 3.2vw, 44px)", fontWeight: 400, letterSpacing: "-0.02em",
            fontFamily: "var(--font-display)", lineHeight: 1 }}>
            {stats.total.toLocaleString()} <span style={{ color: "var(--mute)" }}>API calls</span>
          </h1>
          <DateRangeChips value={range} onChange={setRange} />
        </div>
      </div>

      {/* stat row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "var(--gap)" }}>
        {[
          ["01", "成功率", stats.okRate + "%", stats.success + " ok"],
          ["02", "失败", stats.failed, "HTTP err + timeout"],
          ["03", "限流", stats.rateLtd, "HTTP 429"],
          ["04", "累计耗时", (stats.totalMs / 1000).toFixed(1) + "s", "wall-clock"],
          ["05", "返回行数", formatRows(stats.totalRows), "rows ingested"],
        ].map(([n, l, v, s]) => (
          <Panel key={n} no={n} label={l}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: "clamp(28px, 2.8vw, 40px)",
              fontWeight: 400, letterSpacing: "-0.02em", lineHeight: 1, marginTop: 4,
              whiteSpace: "nowrap" }}>{v}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
              marginTop: 10, letterSpacing: "0.08em" }}>{s}</div>
          </Panel>
        ))}
      </div>

      {/* heatmap */}
      <Panel label="调用热力图 · interface × hour" no="06" action={
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>
          深色 = 调用频次
        </span>
      }>
        <div style={{ marginTop: 8 }}>
          <Heatmap rows={HEATMAP} labels={HEATMAP_INTERFACES} />
        </div>
      </Panel>

      {/* call log */}
      <Panel label="调用明细 · call log" no="07" action={
        <div style={{ display: "flex", gap: 6 }}>
          {[["all","全部"],["success","success"],["failed","failed"],["rate_limited","429"]].map(([k, l]) => (
            <button key={k} onClick={() => setFilter(k)} style={{
              padding: "5px 10px", fontFamily: "var(--font-mono)", fontSize: 11,
              border: `1px solid ${filter === k ? "var(--accent)" : "var(--line)"}`,
              background: filter === k ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
              color: filter === k ? "var(--accent)" : "var(--mute)",
              borderRadius: "var(--radius-sm)",
            }}>{l}</button>
          ))}
        </div>
      } style={{ padding: 0 }}>
        <div style={{ overflow: "auto", maxHeight: 420 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["调用时间", "接口", "参数哈希", "耗时", "状态", "行数", "错误信息"].map((h, i) => (
                  <th key={h} style={{
                    textAlign: i === 3 || i === 5 ? "right" : "left",
                    padding: "12px 14px",
                    fontFamily: "var(--font-mono)", fontSize: 10,
                    letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--mute)",
                    fontWeight: 500, background: "var(--panel)",
                    borderBottom: "1px solid var(--line)",
                    position: "sticky", top: 0, zIndex: 1,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 80).map((c, i) => {
                const sc = c.status === "success" ? "var(--pos)" :
                           c.status === "failed" ? "var(--neg)" : "var(--warn)";
                return (
                  <tr key={i} style={{
                    borderBottom: i === Math.min(79, filtered.length - 1) ? "none" : "1px solid var(--line)",
                  }}>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, color: "var(--mute)" }}>{c.started}</td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, fontWeight: 500 }}>{c.interface}</td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 11, color: "var(--mute)" }}>{c.params_hash}</td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, textAlign: "right", fontVariantNumeric: "tabular-nums",
                      color: c.duration_ms > 10000 ? "var(--warn)" : "var(--fg)" }}>
                      {c.duration_ms.toLocaleString()}ms
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 5,
                        fontFamily: "var(--font-mono)", fontSize: 11,
                        padding: "2px 7px", border: `1px solid ${sc}`, color: sc,
                        borderRadius: "var(--radius-sm)",
                      }}>
                        <span style={{ width: 5, height: 5, borderRadius: "50%", background: sc }} />
                        {c.status}
                      </span>
                    </td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {c.rows ? c.rows.toLocaleString() : "—"}
                    </td>
                    <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 11, color: "var(--neg)",
                      maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.error || "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function DateRangeChips({ value, onChange }) {
  const opts = [["today", "今日"], ["24h", "近 24h"], ["7d", "近 7 日"], ["30d", "近 30 日"], ["custom", "自定义"]];
  return (
    <div style={{ display: "flex", border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
      overflow: "hidden" }}>
      {opts.map(([k, l], i) => (
        <button key={k} onClick={() => onChange(k)} style={{
          padding: "8px 12px", fontFamily: "var(--font-mono)", fontSize: 11,
          background: value === k ? "var(--fg)" : "transparent",
          color: value === k ? "var(--bg)" : "var(--mute)",
          borderRight: i < opts.length - 1 ? "1px solid var(--line)" : "none",
          whiteSpace: "nowrap",
        }}>{l}</button>
      ))}
    </div>
  );
}

Object.assign(window, { Audit });
