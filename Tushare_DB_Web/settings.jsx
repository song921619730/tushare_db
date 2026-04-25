// Settings — ClickHouse connection, Tushare token, scheduler config

function Settings({ chartStyle }) {
  const [form, setForm] = React.useState({
    ch_host: "clickhouse.internal.lan",
    ch_port: "8123",
    ch_user: "ai_reader",
    ch_pass: "••••••••••••",
    ch_db: "tushare",
    ts_token: "e3f1••••••••••••••••••••••••••••4a2b",
    tz: "Asia/Shanghai",
    lookback: "30",
    max_retry: "3",
    rate_limit: "500",
    retention: "90",
  });
  const [testing, setTesting] = React.useState(false);
  const [testResult, setTestResult] = React.useState({ ch: "ok", ts: "ok" });

  const upd = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const doTest = () => {
    setTesting(true);
    setTimeout(() => { setTesting(false); setTestResult({ ch: "ok", ts: "ok" }); }, 900);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap)",
      padding: "var(--pad-lg)", minHeight: "100%", maxWidth: 1100 }}>
      <div style={{ paddingBottom: "var(--pad)", borderBottom: "1px solid var(--line)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
          letterSpacing: "0.14em", textTransform: "uppercase" }}>/ settings — 连接与系统设置</div>
        <h1 style={{ fontSize: "clamp(28px, 3.2vw, 44px)", fontWeight: 400, letterSpacing: "-0.02em",
          fontFamily: "var(--font-display)", lineHeight: 1, marginTop: 12 }}>
          系统配置 <span style={{ color: "var(--mute)" }}>/ configuration</span>
        </h1>
      </div>

      {/* ClickHouse */}
      <Panel label="ClickHouse 连接" no="01" action={
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontFamily: "var(--font-mono)", fontSize: 11,
          padding: "3px 8px", border: "1px solid var(--pos)", color: "var(--pos)",
          borderRadius: "var(--radius-sm)",
        }}>
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--pos)" }} />
          connected
        </span>
      }>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 14, marginTop: 8 }}>
          <Field label="host" value={form.ch_host} onChange={v => upd("ch_host", v)} />
          <Field label="port" value={form.ch_port} onChange={v => upd("ch_port", v)} />
          <Field label="username" value={form.ch_user} onChange={v => upd("ch_user", v)} />
          <Field label="password" value={form.ch_pass} onChange={v => upd("ch_pass", v)} type="password" />
          <Field label="database" value={form.ch_db} onChange={v => upd("ch_db", v)} />
          <Field label="dsn preview" value={`clickhouse://${form.ch_user}@${form.ch_host}:${form.ch_port}/${form.ch_db}`} readonly />
        </div>
      </Panel>

      {/* Tushare */}
      <Panel label="Tushare 凭据" no="02" action={
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontFamily: "var(--font-mono)", fontSize: 11,
          padding: "3px 8px", border: "1px solid var(--pos)", color: "var(--pos)",
          borderRadius: "var(--radius-sm)",
        }}>
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--pos)" }} />
          valid · L3 quota
        </span>
      }>
        <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: 14, marginTop: 8 }}>
          <Field label="token" value={form.ts_token} onChange={v => upd("ts_token", v)} type="password" />
          <Field label="rate limit (req/min)" value={form.rate_limit} onChange={v => upd("rate_limit", v)} />
        </div>
      </Panel>

      {/* Scheduler defaults */}
      <Panel label="调度默认参数" no="03">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginTop: 8 }}>
          <Field label="timezone" value={form.tz} onChange={v => upd("tz", v)} />
          <Field label="回溯窗口 (天)" value={form.lookback} onChange={v => upd("lookback", v)} />
          <Field label="最大重试" value={form.max_retry} onChange={v => upd("max_retry", v)} />
          <Field label="审计保留 (天)" value={form.retention} onChange={v => upd("retention", v)} />
        </div>
      </Panel>

      {/* Actions */}
      <div style={{ display: "flex", gap: 10, paddingTop: 8 }}>
        <button onClick={doTest} disabled={testing} style={{
          padding: "12px 22px", fontFamily: "var(--font-mono)", fontSize: 12,
          letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 500,
          border: "1px solid var(--line)", color: "var(--fg)",
          borderRadius: "var(--radius-sm)",
        }}>{testing ? "⋯ 测试中" : "◉ 测试连接"}</button>
        <button style={{
          padding: "12px 26px", fontFamily: "var(--font-mono)", fontSize: 12,
          letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 500,
          background: "var(--accent)", color: "var(--bg)",
          borderRadius: "var(--radius-sm)",
        }}>✓ 保存配置</button>
        <button style={{
          padding: "12px 22px", fontFamily: "var(--font-mono)", fontSize: 12,
          letterSpacing: "0.12em", textTransform: "uppercase",
          border: "1px solid var(--line)", color: "var(--mute)",
          borderRadius: "var(--radius-sm)", marginLeft: "auto",
        }}>↺ 重置为默认</button>
      </div>

      {/* system info footer */}
      <Panel label="系统信息" no="04">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20, marginTop: 8 }}>
          {[
            ["version", "v1.0.0-alpha"],
            ["runtime", "Node 20.11 · python 3.11"],
            ["deploy", "LAN · docker-compose"],
            ["uptime", "11d 4h 12m"],
            ["CH server", "24.3.2.23"],
            ["disk", "482 GB / 2 TB"],
            ["last backup", "2026-04-25 03:00"],
            ["license", "MIT · 开源"],
          ].map(([k, v]) => (
            <div key={k}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
                letterSpacing: "0.12em", textTransform: "uppercase" }}>{k}</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, marginTop: 4 }}>{v}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", readonly = false }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
        letterSpacing: "0.12em", textTransform: "uppercase" }}>{label}</span>
      <input
        type={type}
        value={value}
        readOnly={readonly}
        onChange={e => onChange && onChange(e.target.value)}
        style={{
          padding: "10px 12px",
          fontFamily: "var(--font-mono)", fontSize: 13,
          background: readonly ? "var(--panel-soft)" : "var(--bg)",
          color: readonly ? "var(--mute)" : "var(--fg)",
          border: "1px solid var(--line)",
          borderRadius: "var(--radius-sm)",
          outline: "none",
        }}
      />
    </label>
  );
}

Object.assign(window, { Settings });
