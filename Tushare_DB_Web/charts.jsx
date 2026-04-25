// Lightweight SVG chart primitives — Swiss-minimal, no libraries.

function Donut({ segments, size = 200, thickness = 18, chartStyle = "filled" }) {
  // segments: [{label, value, color}]
  const total = segments.reduce((a, s) => a + s.value, 0) || 1;
  const r = size / 2 - thickness / 2;
  const c = size / 2;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  const isLine = chartStyle === "line";
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: "block" }}>
      {/* track */}
      <circle cx={c} cy={c} r={r} fill="none" stroke="var(--chart-track)" strokeWidth={thickness} />
      {segments.map((s, i) => {
        const len = (s.value / total) * circ;
        const dasharray = `${len} ${circ - len}`;
        const dashoffset = -offset;
        offset += len;
        return (
          <circle
            key={i}
            cx={c}
            cy={c}
            r={r}
            fill="none"
            stroke={s.color}
            strokeWidth={isLine ? 2 : thickness}
            strokeDasharray={dasharray}
            strokeDashoffset={dashoffset}
            transform={`rotate(-90 ${c} ${c})`}
            strokeLinecap="butt"
          />
        );
      })}
    </svg>
  );
}

function TrendLine({ data, w = 600, h = 160, chartStyle = "filled", accentKey = "rows" }) {
  if (!data || !data.length) return null;
  const pad = { t: 16, r: 8, b: 24, l: 8 };
  const values = data.map(d => d[accentKey]);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;
  const step = innerW / (data.length - 1);
  const points = data.map((d, i) => {
    const x = pad.l + i * step;
    const y = pad.t + innerH - ((d[accentKey] - min) / range) * innerH;
    return [x, y];
  });
  const linePath = points.map((p, i) => (i === 0 ? "M" : "L") + p[0] + "," + p[1]).join(" ");
  const areaPath = linePath + ` L ${points[points.length - 1][0]},${h - pad.b} L ${points[0][0]},${h - pad.b} Z`;
  const barW = Math.max(8, step * 0.55);
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ display: "block" }}>
      {/* baseline gridlines */}
      {[0, 0.5, 1].map((t, i) => (
        <line key={i} x1={pad.l} x2={w - pad.r} y1={pad.t + innerH * t} y2={pad.t + innerH * t}
          stroke="var(--line)" strokeWidth={1} strokeDasharray={i === 2 ? "0" : "2 4"} />
      ))}
      {chartStyle === "bars" ? (
        data.map((d, i) => {
          const [x, y] = points[i];
          return <rect key={i} x={x - barW / 2} y={y} width={barW} height={h - pad.b - y} fill="var(--accent)" />;
        })
      ) : chartStyle === "filled" ? (
        <>
          <path d={areaPath} fill="var(--accent)" opacity="0.12" />
          <path d={linePath} fill="none" stroke="var(--accent)" strokeWidth={1.5} />
        </>
      ) : (
        <path d={linePath} fill="none" stroke="var(--accent)" strokeWidth={1.5} />
      )}
      {/* dots */}
      {points.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={3} fill="var(--bg)" stroke="var(--accent)" strokeWidth={1.5} />
      ))}
      {/* x labels */}
      {data.map((d, i) => (
        <text key={i} x={points[i][0]} y={h - 6} textAnchor="middle"
          fontSize="10" fill="var(--mute)" fontFamily="var(--font-mono)">{d.day}</text>
      ))}
    </svg>
  );
}

function Sparkline({ data, w = 120, h = 28, chartStyle = "filled" }) {
  if (!data || !data.length) return null;
  const max = Math.max(...data), min = Math.min(...data);
  const range = max - min || 1;
  const step = w / (data.length - 1);
  const pts = data.map((v, i) => [i * step, h - 2 - ((v - min) / range) * (h - 4)]);
  const linePath = pts.map((p, i) => (i === 0 ? "M" : "L") + p[0] + "," + p[1]).join(" ");
  const areaPath = linePath + ` L ${pts[pts.length - 1][0]},${h} L ${pts[0][0]},${h} Z`;
  const barW = Math.max(2, step * 0.6);
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ display: "block" }}>
      {chartStyle === "bars" ? (
        data.map((v, i) => {
          const [x, y] = pts[i];
          return <rect key={i} x={x - barW / 2} y={y} width={barW} height={h - y} fill="var(--accent)" />;
        })
      ) : chartStyle === "filled" ? (
        <>
          <path d={areaPath} fill="var(--accent)" opacity="0.18" />
          <path d={linePath} fill="none" stroke="var(--accent)" strokeWidth={1.25} />
        </>
      ) : (
        <path d={linePath} fill="none" stroke="var(--accent)" strokeWidth={1.25} />
      )}
    </svg>
  );
}

function ProgressBar({ value, max = 100, showLabel = true, height = 6 }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div style={{ width: "100%" }}>
      <div style={{ position: "relative", height, background: "var(--chart-track)", overflow: "hidden", borderRadius: "var(--radius-sm)" }}>
        <div style={{ position: "absolute", inset: 0, width: pct + "%", background: "var(--accent)" }} />
      </div>
      {showLabel && (
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6,
          fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>
          <span>{value.toLocaleString()} / {max.toLocaleString()}</span>
          <span>{pct.toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}

function Heatmap({ rows, labels, hours = 24 }) {
  // rows: number[][]  hours columns
  const max = Math.max(...rows.flat(), 1);
  const cellW = 18, cellH = 18, gap = 2;
  const labelW = 88;
  const w = labelW + hours * (cellW + gap);
  const h = rows.length * (cellH + gap) + 20;
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} style={{ display: "block" }}>
      {Array.from({ length: hours }, (_, i) => i % 4 === 0 && (
        <text key={i} x={labelW + i * (cellW + gap) + cellW / 2} y={12}
          textAnchor="middle" fontSize="10" fill="var(--mute)"
          fontFamily="var(--font-mono)">{String(i).padStart(2, "0")}</text>
      ))}
      {rows.map((row, r) =>
        <g key={r}>
          <text x={labelW - 8} y={20 + r * (cellH + gap) + cellH * 0.7}
            textAnchor="end" fontSize="11" fill="var(--fg)"
            fontFamily="var(--font-mono)">{labels[r]}</text>
          {row.map((v, c) => {
            const op = v === 0 ? 0.04 : 0.1 + (v / max) * 0.9;
            return <rect key={c} x={labelW + c * (cellW + gap)} y={20 + r * (cellH + gap)}
              width={cellW} height={cellH} fill="var(--accent)" opacity={op} />;
          })}
        </g>
      )}
    </svg>
  );
}

Object.assign(window, { Donut, TrendLine, Sparkline, ProgressBar, Heatmap });
