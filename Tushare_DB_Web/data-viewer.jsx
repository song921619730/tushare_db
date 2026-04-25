// Data Viewer — SQL editor + result table + K-line chart

const PRESET_QUERIES = [
  {
    id: "ohlcv",
    label: "OHLCV K 线",
    cn: "日线行情",
    sql: `SELECT trade_date, ts_code, open, high, low, close, pre_close,
       change, pct_chg, vol, amount
FROM tushare.stock_daily
WHERE ts_code = '000001.SZ'
  AND trade_date >= '20260301' AND trade_date <= '20260425'
ORDER BY trade_date
LIMIT 5000;`,
    kind: "kline",
  },
  {
    id: "fina",
    label: "财务数据",
    cn: "三大报表",
    sql: `SELECT end_date, ts_code, revenue, operate_profit, n_income,
       total_assets, total_liab
FROM tushare.fina_income
WHERE ts_code = '000001.SZ'
ORDER BY end_date DESC
LIMIT 100;`,
    kind: "table",
  },
  {
    id: "moneyflow",
    label: "资金流向 Top30",
    cn: "净流入排行",
    sql: `SELECT ts_code, name, close, pct_chg, net_mf_amount, buy_lg_amount
FROM tushare.stock_moneyflow
WHERE trade_date = '20260425'
ORDER BY net_mf_amount DESC
LIMIT 30;`,
    kind: "table",
  },
  {
    id: "limit",
    label: "涨停板",
    cn: "Limit-up list",
    sql: `SELECT ts_code, name, close, pct_chg, fc_ratio, fl_ratio, fd_amount
FROM tushare.stock_limit
WHERE trade_date = '20260425' AND limit = 'U'
ORDER BY fd_amount DESC
LIMIT 5000;`,
    kind: "table",
  },
];

function DataViewer({ chartStyle }) {
  const [preset, setPreset] = React.useState(PRESET_QUERIES[0]);
  const [sql, setSql] = React.useState(PRESET_QUERIES[0].sql);
  const [running, setRunning] = React.useState(false);
  const [results, setResults] = React.useState({
    rows: OHLCV_SAMPLE, cols: Object.keys(OHLCV_SAMPLE[0]),
    durationMs: 142, totalRows: OHLCV_SAMPLE.length, kind: "kline",
  });

  const runQuery = () => {
    setRunning(true);
    setTimeout(() => {
      setRunning(false);
      const rows = preset.kind === "kline" ? OHLCV_SAMPLE : generateMockRows(preset.id);
      setResults({
        rows, cols: Object.keys(rows[0] || {}),
        durationMs: Math.floor(80 + Math.random() * 280),
        totalRows: rows.length,
        kind: preset.kind,
      });
    }, 600);
  };

  const selectPreset = (p) => { setPreset(p); setSql(p.sql); };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap)",
      padding: "var(--pad-lg)", minHeight: "100%" }}>

      {/* Header */}
      <div style={{ paddingBottom: "var(--pad)", borderBottom: "1px solid var(--line)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
          letterSpacing: "0.14em", textTransform: "uppercase" }}>/ data — 数据查询与浏览</div>
        <h1 style={{ fontSize: "clamp(28px, 3.2vw, 44px)", fontWeight: 400, letterSpacing: "-0.02em",
          fontFamily: "var(--font-display)", lineHeight: 1, marginTop: 12 }}>
          SQL <span style={{ color: "var(--mute)" }}>/</span> query explorer
        </h1>
        <p style={{ fontSize: 13, color: "var(--mute)", marginTop: 8 }}>
          只读模式 · 自动注入 <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg)" }}>LIMIT 5000</span>
          · max_execution_time <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg)" }}>30s</span>
        </p>
      </div>

      {/* Presets */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {PRESET_QUERIES.map(p => {
          const active = p.id === preset.id;
          return (
            <button key={p.id} onClick={() => selectPreset(p)}
              style={{
                padding: "10px 16px",
                border: `1px solid ${active ? "var(--accent)" : "var(--line)"}`,
                background: active ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "var(--panel)",
                color: active ? "var(--accent)" : "var(--fg)",
                borderRadius: "var(--radius-sm)",
                display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 2,
                minWidth: 140,
              }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500 }}>{p.label}</span>
              <span style={{ fontSize: 11, color: "var(--mute)" }}>{p.cn}</span>
            </button>
          );
        })}
      </div>

      {/* Editor + run */}
      <Panel label="SQL editor — read-only" no="·" action={
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={runQuery} disabled={running}
            style={{
              padding: "6px 16px", fontFamily: "var(--font-mono)", fontSize: 11,
              letterSpacing: "0.14em", textTransform: "uppercase", fontWeight: 500,
              background: "var(--accent)", color: "var(--bg)",
              borderRadius: "var(--radius-sm)",
              opacity: running ? 0.6 : 1,
            }}>{running ? "⋯ running" : "▶ run"}</button>
          <button style={{
            padding: "6px 12px", fontFamily: "var(--font-mono)", fontSize: 11,
            letterSpacing: "0.12em", textTransform: "uppercase",
            border: "1px solid var(--line)", color: "var(--fg)",
            borderRadius: "var(--radius-sm)",
          }}>⤓ export CSV</button>
        </div>
      } style={{ padding: 0 }}>
        <div style={{ padding: "var(--pad)", paddingTop: 12 }}>
          <pre style={{
            margin: 0, padding: 16,
            background: "var(--panel-soft)", border: "1px solid var(--line)",
            fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--fg)",
            borderRadius: "var(--radius-sm)", lineHeight: 1.6,
            whiteSpace: "pre-wrap", overflow: "auto", maxHeight: 180,
          }}>
            <textarea
              value={sql}
              onChange={e => setSql(e.target.value)}
              spellCheck={false}
              style={{
                width: "100%", minHeight: 140, border: "none", background: "transparent",
                fontFamily: "inherit", fontSize: "inherit", color: "inherit", resize: "vertical",
                outline: "none", lineHeight: 1.6,
              }}
            />
          </pre>
        </div>
      </Panel>

      {/* K-line chart if preset */}
      {results.kind === "kline" && (
        <Panel label="K 线图 · 000001.SZ" no="♫" action={
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>
            {results.rows.length} bars · 2026-03 → 2026-04
          </span>
        }>
          <KLineChart data={results.rows} />
        </Panel>
      )}

      {/* Result stats */}
      <div style={{ display: "flex", gap: 24, padding: "12px 16px",
        border: "1px solid var(--line)", borderRadius: "var(--radius-sm)",
        background: "var(--panel-soft)", fontFamily: "var(--font-mono)", fontSize: 12 }}>
        <div>
          <span style={{ color: "var(--mute)", marginRight: 8 }}>rows:</span>
          <span style={{ fontWeight: 500 }}>{results.totalRows.toLocaleString()}</span>
        </div>
        <div>
          <span style={{ color: "var(--mute)", marginRight: 8 }}>cols:</span>
          <span style={{ fontWeight: 500 }}>{results.cols.length}</span>
        </div>
        <div>
          <span style={{ color: "var(--mute)", marginRight: 8 }}>duration:</span>
          <span style={{ fontWeight: 500, color: "var(--pos)" }}>{results.durationMs}ms</span>
        </div>
        <div style={{ marginLeft: "auto", color: "var(--mute)" }}>LIMIT 5000 · ai_reader@clickhouse:8123</div>
      </div>

      {/* Results table */}
      <Panel label="Results" no="◫" style={{ padding: 0 }}>
        <div style={{ overflow: "auto", maxHeight: 520 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {results.cols.map(c => (
                  <th key={c} style={{
                    textAlign: typeof results.rows[0][c] === "number" ? "right" : "left",
                    padding: "12px 14px",
                    fontFamily: "var(--font-mono)", fontSize: 10,
                    letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--mute)",
                    fontWeight: 500, background: "var(--panel)",
                    borderBottom: "1px solid var(--line)",
                    position: "sticky", top: 0, zIndex: 1,
                  }}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results.rows.slice(0, 100).map((r, i) => (
                <tr key={i} style={{
                  borderBottom: i === Math.min(99, results.rows.length - 1) ? "none" : "1px solid var(--line)",
                }}>
                  {results.cols.map(c => {
                    const v = r[c];
                    const isNum = typeof v === "number";
                    const isPct = c === "pct_chg";
                    const color = isPct ? (v > 0 ? "var(--neg)" : v < 0 ? "var(--pos)" : "var(--mute)") :
                                  "var(--fg)"; // Chinese convention: 红涨绿跌
                    return (
                      <td key={c} style={{
                        textAlign: isNum ? "right" : "left",
                        padding: "10px 14px",
                        fontFamily: "var(--font-mono)", fontSize: 12,
                        color, fontVariantNumeric: "tabular-nums",
                      }}>{isPct && v > 0 ? "+" : ""}{isNum ? v.toLocaleString() : v}</td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* pagination footer */}
        <div style={{
          padding: "12px 16px", borderTop: "1px solid var(--line)",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
        }}>
          <span>showing 1–{Math.min(100, results.rows.length)} of {results.rows.length}</span>
          <div style={{ display: "flex", gap: 4 }}>
            {["‹‹", "‹", "1", "2", "3", "›", "››"].map((b, i) => (
              <button key={i} style={{
                minWidth: 28, height: 26, padding: "0 8px",
                border: "1px solid var(--line)",
                background: b === "1" ? "var(--fg)" : "transparent",
                color: b === "1" ? "var(--bg)" : "var(--fg)",
                borderRadius: "var(--radius-sm)",
              }}>{b}</button>
            ))}
          </div>
        </div>
      </Panel>
    </div>
  );
}

function KLineChart({ data, w = 1200, h = 340 }) {
  if (!data || !data.length) return null;
  const pad = { t: 20, r: 20, b: 60, l: 50 };
  const priceAreaH = (h - pad.t - pad.b) * 0.72;
  const volAreaTop = pad.t + priceAreaH + 10;
  const volAreaH = (h - pad.t - pad.b) * 0.28 - 10;

  const highs = data.map(d => d.high);
  const lows = data.map(d => d.low);
  const max = Math.max(...highs);
  const min = Math.min(...lows);
  const range = max - min;
  const maxVol = Math.max(...data.map(d => d.vol));

  const n = data.length;
  const innerW = w - pad.l - pad.r;
  const step = innerW / n;
  const bw = Math.max(3, step * 0.7);

  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} style={{ display: "block" }}>
      {/* price gridlines */}
      {[0, 0.25, 0.5, 0.75, 1].map((t, i) => {
        const y = pad.t + priceAreaH * t;
        const price = (max - range * t).toFixed(2);
        return (
          <g key={i}>
            <line x1={pad.l} x2={w - pad.r} y1={y} y2={y}
              stroke="var(--line)" strokeWidth={1} strokeDasharray="2 4" />
            <text x={pad.l - 6} y={y + 4} textAnchor="end" fontSize="10"
              fill="var(--mute)" fontFamily="var(--font-mono)">{price}</text>
          </g>
        );
      })}
      {/* volume gridline */}
      <line x1={pad.l} x2={w - pad.r} y1={volAreaTop + volAreaH} y2={volAreaTop + volAreaH}
        stroke="var(--line)" strokeWidth={1} />

      {/* candlesticks */}
      {data.map((d, i) => {
        const x = pad.l + i * step + step / 2;
        const yHigh = pad.t + ((max - d.high) / range) * priceAreaH;
        const yLow  = pad.t + ((max - d.low) / range) * priceAreaH;
        const yOpen = pad.t + ((max - d.open) / range) * priceAreaH;
        const yClose = pad.t + ((max - d.close) / range) * priceAreaH;
        const up = d.close >= d.open;
        // Chinese convention: 红涨 (red up), 绿跌 (green down) — map to neg/pos vars
        const color = up ? "var(--neg)" : "var(--pos)";
        const bodyTop = Math.min(yOpen, yClose);
        const bodyH = Math.max(1, Math.abs(yClose - yOpen));

        const volY = volAreaTop + volAreaH - (d.vol / maxVol) * volAreaH;
        const volH = volAreaTop + volAreaH - volY;

        return (
          <g key={i}>
            <line x1={x} x2={x} y1={yHigh} y2={yLow} stroke={color} strokeWidth={1} />
            <rect x={x - bw/2} y={bodyTop} width={bw} height={bodyH}
              fill={up ? color : color} stroke={color} strokeWidth={1}
              fillOpacity={up ? 0.9 : 0.9} />
            <rect x={x - bw/2} y={volY} width={bw} height={volH}
              fill={color} fillOpacity={0.6} />
          </g>
        );
      })}

      {/* x labels every ~7 */}
      {data.map((d, i) => i % 7 === 0 && (
        <text key={i} x={pad.l + i * step + step/2} y={h - pad.b + 20}
          textAnchor="middle" fontSize="10" fill="var(--mute)"
          fontFamily="var(--font-mono)">
          {d.trade_date.slice(4, 6)}-{d.trade_date.slice(6, 8)}
        </text>
      ))}
    </svg>
  );
}

function generateMockRows(presetId) {
  const codes = ["000001.SZ", "000002.SZ", "000858.SZ", "600000.SH", "600036.SH",
    "600519.SH", "600887.SH", "601318.SH", "601398.SH", "601857.SH",
    "300015.SZ", "300059.SZ", "300750.SZ", "300760.SZ", "688981.SH",
    "002415.SZ", "002594.SZ", "000651.SZ", "601888.SH", "600276.SH",
    "600030.SH", "601688.SH", "600309.SH", "002230.SZ", "000776.SZ",
    "300253.SZ", "600031.SH", "600104.SH", "601166.SH", "000333.SZ"];
  const names = ["平安银行","万科A","五粮液","浦发银行","招商银行","贵州茅台","伊利股份","中国平安","工商银行","中国石油","爱尔眼科","东方财富","宁德时代","迈瑞医疗","中芯国际","海康威视","比亚迪","格力电器","中国中免","恒瑞医药","中信证券","华泰证券","万华化学","科大讯飞","广发证券","卫宁健康","三一重工","上汽集团","兴业银行","美的集团"];
  if (presetId === "fina") {
    return codes.slice(0, 12).map((c, i) => ({
      end_date: ["20251231", "20250930", "20250630", "20250331"][i % 4],
      ts_code: c,
      revenue: Math.floor(Math.random() * 50_000_000_000 + 10_000_000_000),
      operate_profit: Math.floor(Math.random() * 12_000_000_000 + 1_000_000_000),
      n_income: Math.floor(Math.random() * 8_000_000_000 + 500_000_000),
      total_assets: Math.floor(Math.random() * 300_000_000_000 + 50_000_000_000),
      total_liab: Math.floor(Math.random() * 200_000_000_000 + 20_000_000_000),
    }));
  }
  if (presetId === "moneyflow") {
    return codes.map((c, i) => ({
      ts_code: c,
      name: names[i],
      close: +(10 + Math.random() * 200).toFixed(2),
      pct_chg: +((Math.random() - 0.3) * 10).toFixed(2),
      net_mf_amount: +(Math.random() * 800 + 80).toFixed(2),
      buy_lg_amount: +(Math.random() * 1200 + 100).toFixed(2),
    })).sort((a, b) => b.net_mf_amount - a.net_mf_amount);
  }
  if (presetId === "limit") {
    return codes.slice(0, 18).map((c, i) => ({
      ts_code: c,
      name: names[i],
      close: +(10 + Math.random() * 80).toFixed(2),
      pct_chg: +(9.9 + Math.random() * 0.1).toFixed(2),
      fc_ratio: +(Math.random() * 20).toFixed(2),
      fl_ratio: +(Math.random() * 10).toFixed(2),
      fd_amount: Math.floor(Math.random() * 5_000_000_000 + 100_000_000),
    }));
  }
  return [];
}

Object.assign(window, { DataViewer });
