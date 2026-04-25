// Verify — data validation/repair operations

function Verify({ chartStyle }) {
  const [running, setRunning] = React.useState(null);
  const [results, setResults] = React.useState(VERIFY_RESULTS);
  const [selected, setSelected] = React.useState(null);

  const runCheck = (op) => {
    setRunning(op);
    setTimeout(() => setRunning(null), 1600);
  };

  const ops = [
    { id: "count",    no: "01", name: "行数对账",    en: "Row-count verify",   desc: "按接口维度对比本地表行数与 API 返回的总数，识别缺失数据。", action: "运行对账" },
    { id: "dedup",    no: "02", name: "去重检查",    en: "Dedup check",        desc: "基于主键扫描本地 ClickHouse 表，发现重复键并列出样本。",  action: "扫描去重" },
    { id: "gap",      no: "03", name: "日期缺口",    en: "Trading-day gaps",   desc: "对交易日序列逐日校验，高亮缺失的 trade_date。",            action: "扫描缺口" },
    { id: "checksum", no: "04", name: "Checksum",   en: "Integrity checksum", desc: "抽取样本比对 Tushare 返回与本地 close/vol 等字段值。",     action: "对比校验" },
    { id: "repair",   no: "05", name: "一键回补",    en: "Auto-repair",        desc: "对行数差异的接口，按缺失日期自动触发回补任务。",            action: "确认回补" },
    { id: "freshness",no: "06", name: "新鲜度",      en: "Freshness check",    desc: "检查每个 P0 接口最近一次同步时间是否在期望窗口内。",        action: "检查新鲜度" },
  ];

  const nOk = results.filter(r => r.status === "ok").length;
  const nDiff = results.filter(r => r.status === "diff").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap)",
      padding: "var(--pad-lg)", minHeight: "100%" }}>
      <div style={{ paddingBottom: "var(--pad)", borderBottom: "1px solid var(--line)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
          letterSpacing: "0.14em", textTransform: "uppercase" }}>/ verify — 验证与诊断</div>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: 12 }}>
          <h1 style={{ fontSize: "clamp(28px, 3.2vw, 44px)", fontWeight: 400, letterSpacing: "-0.02em",
            fontFamily: "var(--font-display)", lineHeight: 1 }}>
            {nDiff} <span style={{ color: "var(--mute)" }}>discrepancies</span>
            <span style={{ color: "var(--mute)" }}> / </span>
            <span style={{ color: "var(--pos)" }}>{nOk}</span>
            <span style={{ fontSize: "0.42em", color: "var(--mute)", marginLeft: 8 }}>OK</span>
          </h1>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--mute)" }}>
            last scan · 2026-04-25 18:02
          </div>
        </div>
      </div>

      {/* op cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
        gap: "var(--gap)" }}>
        {ops.map(op => (
          <section key={op.id} style={{
            background: "var(--panel)", border: "1px solid var(--line)",
            borderRadius: "var(--radius)", padding: "var(--pad)",
            display: "flex", flexDirection: "column", gap: 12,
          }}>
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
                letterSpacing: "0.08em" }}>{op.no}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
                letterSpacing: "0.12em", textTransform: "uppercase" }}>{op.en}</span>
            </header>
            <div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 400,
                letterSpacing: "-0.02em", lineHeight: 1.1 }}>{op.name}</div>
              <p style={{ fontSize: 13, color: "var(--mute)", marginTop: 8, lineHeight: 1.55,
                textWrap: "pretty" }}>{op.desc}</p>
            </div>
            <button onClick={() => runCheck(op.id)} disabled={running === op.id}
              style={{
                padding: "10px", marginTop: "auto",
                fontFamily: "var(--font-mono)", fontSize: 11,
                letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 500,
                background: running === op.id ? "var(--mute)" : "var(--accent)",
                color: "var(--bg)",
                borderRadius: "var(--radius-sm)",
              }}>{running === op.id ? "⋯ 运行中" : `▶ ${op.action}`}</button>
          </section>
        ))}
      </div>

      {/* results */}
      <Panel label="行数对账结果 · row-count diff" no="07" style={{ padding: 0 }}>
        <div style={{ overflow: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["接口", "本地表名", "API 期望", "本地行数", "差异", "状态", ""].map((h, i) => (
                  <th key={h} style={{
                    textAlign: i >= 2 && i <= 4 ? "right" : "left",
                    padding: "12px 14px",
                    fontFamily: "var(--font-mono)", fontSize: 10,
                    letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--mute)",
                    fontWeight: 500, background: "var(--panel)",
                    borderBottom: "1px solid var(--line)",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => {
                const sc = r.status === "ok" ? "var(--pos)" : "var(--warn)";
                return (
                  <tr key={i} style={{
                    borderBottom: i === results.length - 1 ? "none" : "1px solid var(--line)",
                  }}>
                    <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, fontWeight: 500 }}>{r.interface}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, color: "var(--mute)" }}>{r.table}</td>
                    <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {r.expected.toLocaleString()}
                    </td>
                    <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                      {r.actual.toLocaleString()}
                    </td>
                    <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono)",
                      fontSize: 12, textAlign: "right", fontVariantNumeric: "tabular-nums",
                      color: r.diff === 0 ? "var(--mute)" : "var(--warn)", fontWeight: 500 }}>
                      {r.diff === 0 ? "—" : r.diff.toLocaleString()}
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 5,
                        fontFamily: "var(--font-mono)", fontSize: 11,
                        padding: "2px 7px", border: `1px solid ${sc}`, color: sc,
                        borderRadius: "var(--radius-sm)",
                      }}>
                        <span style={{ width: 5, height: 5, borderRadius: "50%", background: sc }} />
                        {r.status === "ok" ? "ok" : "diff"}
                      </span>
                    </td>
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      {r.status === "diff" && (
                        <button style={{
                          padding: "4px 10px", fontFamily: "var(--font-mono)", fontSize: 11,
                          letterSpacing: "0.1em", textTransform: "uppercase",
                          border: "1px solid var(--accent)", color: "var(--accent)",
                          borderRadius: "var(--radius-sm)",
                        }}>回补 →</button>
                      )}
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

Object.assign(window, { Verify });
