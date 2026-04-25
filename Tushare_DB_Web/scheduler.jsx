// Scheduler — 24h timeline + job cards

function Scheduler({ chartStyle }) {
  const [selected, setSelected] = React.useState(null);
  const [confirmJob, setConfirmJob] = React.useState(null);

  // 24h grid: 0-23
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const nowHour = new Date().getHours() + new Date().getMinutes() / 60;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap)",
      padding: "var(--pad-lg)", minHeight: "100%" }}>

      {/* Header */}
      <div style={{ paddingBottom: "var(--pad)", borderBottom: "1px solid var(--line)" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)",
          letterSpacing: "0.14em", textTransform: "uppercase" }}>/ scheduler — 调度任务</div>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginTop: 12 }}>
          <h1 style={{ fontSize: "clamp(28px, 3.2vw, 44px)", fontWeight: 400, letterSpacing: "-0.02em",
            fontFamily: "var(--font-display)", lineHeight: 1 }}>
            {SCHEDULER_JOBS.length} <span style={{ color: "var(--mute)" }}>active jobs</span>
          </h1>
          <div style={{ display: "flex", alignItems: "center", gap: 18, fontFamily: "var(--font-mono)", fontSize: 12 }}>
            <div><span style={{ color: "var(--mute)" }}>next run:</span> <span style={{ color: "var(--accent)" }}>13h 25m</span></div>
            <div><span style={{ color: "var(--mute)" }}>queue:</span> <span>0</span></div>
          </div>
        </div>
      </div>

      {/* 24h timeline */}
      <Panel label="24h Timeline" no="⧗" action={
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--mute)" }}>
          2026-04-25 · Asia/Shanghai
        </span>
      }>
        <div style={{ position: "relative", marginTop: 8, padding: "0 8px" }}>
          {/* Hour ticks */}
          <div style={{ position: "relative", height: 28, borderBottom: "1px solid var(--line)" }}>
            {hours.map(h => (
              <div key={h} style={{
                position: "absolute", left: `${(h / 24) * 100}%`,
                top: 0, bottom: 0, display: "flex", flexDirection: "column", alignItems: "center",
              }}>
                <div style={{ width: 1, height: h % 6 === 0 ? 12 : 6,
                  background: h % 6 === 0 ? "var(--fg)" : "var(--line)" }} />
                {h % 3 === 0 && (
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 10,
                    color: h === Math.floor(nowHour) ? "var(--accent)" : "var(--mute)",
                    marginTop: 2 }}>{String(h).padStart(2, "0")}:00</div>
                )}
              </div>
            ))}
          </div>

          {/* Now line */}
          <div style={{
            position: "absolute", left: `calc(8px + ${(nowHour / 24) * (100 - 1.5)}%)`,
            top: 28, bottom: 0, width: 1, background: "var(--accent)",
            pointerEvents: "none", zIndex: 2,
          }}>
            <div style={{ position: "absolute", top: -4, left: -4,
              width: 9, height: 9, borderRadius: "50%", background: "var(--accent)" }} />
          </div>

          {/* Job tracks */}
          <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 14 }}>
            {SCHEDULER_JOBS.map((job, i) => {
              const leftPct = (job.hour / 24) * 100;
              const widthPct = (job.duration / 24) * 100;
              const lastColor =
                job.last === "done" ? "var(--pos)" :
                job.last === "partial" ? "var(--warn)" :
                job.last === "failed" ? "var(--neg)" : "var(--mute)";
              return (
                <div key={job.id} style={{ position: "relative", height: 34,
                  display: "flex", alignItems: "center" }}>
                  <div style={{ position: "absolute", left: 0, right: 0, top: "50%",
                    height: 1, background: "var(--line)" }} />
                  <div style={{
                    position: "absolute", left: 100, fontFamily: "var(--font-mono)", fontSize: 11,
                    color: "var(--mute)", background: "var(--panel)", paddingRight: 8,
                  }}>{/* placeholder not used */}</div>
                  <button
                    onClick={() => setSelected(job)}
                    style={{
                      position: "absolute", left: `${leftPct}%`,
                      width: `max(56px, ${widthPct}%)`, height: 24, top: 5,
                      background: `color-mix(in srgb, ${lastColor} 18%, var(--panel))`,
                      border: `1px solid ${lastColor}`,
                      borderRadius: "var(--radius-sm)",
                      display: "flex", alignItems: "center", gap: 6,
                      padding: "0 8px",
                      fontFamily: "var(--font-mono)", fontSize: 11,
                      color: "var(--fg)",
                      cursor: "pointer", textAlign: "left",
                    }}>
                    <span style={{ width: 5, height: 5, borderRadius: "50%", background: lastColor, flexShrink: 0 }} />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {job.name}
                    </span>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </Panel>

      {/* Job cards grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
        gap: "var(--gap)" }}>
        {SCHEDULER_JOBS.map((job, i) => (
          <JobCard key={job.id} job={job} no={String(i+1).padStart(2,"0")}
            onTrigger={() => setConfirmJob(job)}
            onDetails={() => setSelected(job)} />
        ))}
      </div>

      {confirmJob && (
        <ConfirmModal
          job={confirmJob}
          onCancel={() => setConfirmJob(null)}
          onConfirm={() => setConfirmJob(null)}
        />
      )}

      {selected && (
        <JobDrawer job={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

function JobCard({ job, no, onTrigger, onDetails }) {
  const lastColor =
    job.last === "done" ? "var(--pos)" :
    job.last === "partial" ? "var(--warn)" :
    job.last === "failed" ? "var(--neg)" : "var(--mute)";
  const hourStr = `${String(Math.floor(job.hour)).padStart(2,"0")}:${String(Math.floor((job.hour % 1) * 60)).padStart(2,"0")}`;
  return (
    <section style={{
      background: "var(--panel)", border: "1px solid var(--line)",
      borderRadius: "var(--radius)", padding: "var(--pad)",
      display: "flex", flexDirection: "column", gap: 14,
    }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
            letterSpacing: "0.08em" }}>{no}</span>
          <div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 500 }}>{job.name}</div>
            <div style={{ fontSize: 11, color: "var(--mute)", marginTop: 2 }}>{job.cn}</div>
          </div>
        </div>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontFamily: "var(--font-mono)", fontSize: 11,
          padding: "2px 8px", border: `1px solid ${lastColor}`, color: lastColor,
          borderRadius: "var(--radius-sm)",
        }}>
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: lastColor }} />
          {job.last}
        </span>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
            letterSpacing: "0.1em", textTransform: "uppercase" }}>每日 cron</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 400,
            letterSpacing: "-0.02em", marginTop: 4, lineHeight: 1 }}>{hourStr}</div>
        </div>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
            letterSpacing: "0.1em", textTransform: "uppercase" }}>next run</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 400,
            letterSpacing: "-0.02em", marginTop: 4, lineHeight: 1, color: "var(--accent)" }}>{job.nextIn}</div>
        </div>
      </div>

      <div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
          letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>
          覆盖接口 · {job.interfaces.length}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {job.interfaces.map(i => (
            <span key={i} style={{
              fontFamily: "var(--font-mono)", fontSize: 11,
              padding: "3px 8px", border: "1px solid var(--line)",
              borderRadius: "var(--radius-sm)", color: "var(--fg)",
            }}>{i}</span>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: "auto" }}>
        <button onClick={onTrigger} style={{
          flex: 1, padding: "9px",
          fontFamily: "var(--font-mono)", fontSize: 11,
          letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 500,
          background: "var(--accent)", color: "var(--bg)",
          borderRadius: "var(--radius-sm)",
        }}>▶ 立即执行</button>
        <button onClick={onDetails} style={{
          flex: 1, padding: "9px",
          fontFamily: "var(--font-mono)", fontSize: 11,
          letterSpacing: "0.1em", textTransform: "uppercase",
          border: "1px solid var(--line)", color: "var(--fg)",
          borderRadius: "var(--radius-sm)",
        }}>历史记录</button>
      </div>
    </section>
  );
}

function ConfirmModal({ job, onCancel, onConfirm }) {
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 100,
      display: "flex", alignItems: "center", justifyContent: "center",
      backdropFilter: "blur(4px)",
      animation: "fadeIn 180ms ease-out",
    }} onClick={onCancel}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "var(--bg)", border: "1px solid var(--line)",
        padding: "32px 36px", borderRadius: "var(--radius)",
        maxWidth: 480, width: "90%",
      }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--accent)",
          letterSpacing: "0.14em", textTransform: "uppercase" }}>确认手动触发</div>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 400,
          letterSpacing: "-0.02em", marginTop: 10 }}>立即执行 <span style={{ color: "var(--accent)" }}>{job.name}</span> ?</h2>
        <p style={{ fontSize: 13, color: "var(--mute)", marginTop: 12, lineHeight: 1.6 }}>
          将立即在后台触发此调度任务，覆盖 <span style={{ color: "var(--fg)",
          fontFamily: "var(--font-mono)" }}>{job.interfaces.length}</span> 个接口。
          请确保当前没有冲突的运行 run。
        </p>
        <div style={{ display: "flex", gap: 10, marginTop: 24 }}>
          <button onClick={onCancel} style={{
            flex: 1, padding: "11px",
            fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.1em", textTransform: "uppercase",
            border: "1px solid var(--line)", color: "var(--fg)",
            borderRadius: "var(--radius-sm)",
          }}>取消</button>
          <button onClick={onConfirm} style={{
            flex: 1, padding: "11px",
            fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.1em", textTransform: "uppercase",
            fontWeight: 500,
            background: "var(--accent)", color: "var(--bg)",
            borderRadius: "var(--radius-sm)",
          }}>▶ 确认执行</button>
        </div>
      </div>
    </div>
  );
}

function JobDrawer({ job, onClose }) {
  const history = React.useMemo(() => Array.from({ length: 5 }, (_, i) => ({
    ts: `2026-04-${String(25 - i).padStart(2, "0")} ${String(Math.floor(job.hour)).padStart(2,"0")}:${String(Math.floor((job.hour % 1) * 60)).padStart(2,"0")}:00`,
    duration: Math.floor(job.duration * 3600 * (0.7 + Math.random() * 0.6)),
    units: job.interfaces.length,
    status: i === 0 ? job.last : Math.random() > 0.2 ? "done" : Math.random() > 0.5 ? "partial" : "failed",
  })), [job.id]);

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 100,
      display: "flex", justifyContent: "flex-end",
      backdropFilter: "blur(4px)",
    }} onClick={onClose}>
      <aside onClick={e => e.stopPropagation()} style={{
        width: 480, height: "100%", background: "var(--panel)",
        borderLeft: "1px solid var(--line)", overflow: "auto",
        animation: "slideInR 240ms cubic-bezier(.2,.8,.2,1)",
      }}>
        <header style={{ padding: "var(--pad)", borderBottom: "1px solid var(--line)",
          display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--mute)",
              letterSpacing: "0.14em", textTransform: "uppercase" }}>scheduled job</div>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: 30, fontWeight: 400,
              letterSpacing: "-0.02em", marginTop: 6 }}>{job.name}</h2>
            <div style={{ fontSize: 13, color: "var(--mute)", marginTop: 4 }}>{job.cn}</div>
          </div>
          <button onClick={onClose} style={{
            width: 32, height: 32, border: "1px solid var(--line)",
            borderRadius: "var(--radius-sm)", fontSize: 14,
          }}>×</button>
        </header>
        <div style={{ padding: "var(--pad)", display: "flex", flexDirection: "column", gap: 24 }}>
          <section>
            <h3 style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.14em",
              textTransform: "uppercase", color: "var(--fg)", fontWeight: 500, marginBottom: 10 }}>
              近 5 次运行 · history
            </h3>
            {history.map((h, i) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto auto",
                gap: 12, padding: "10px 0", alignItems: "center",
                borderBottom: i === history.length - 1 ? "none" : "1px solid var(--line)",
                fontFamily: "var(--font-mono)", fontSize: 11,
              }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%",
                  background: h.status === "done" ? "var(--pos)" :
                              h.status === "partial" ? "var(--warn)" :
                              h.status === "failed" ? "var(--neg)" : "var(--mute)" }} />
                <span style={{ color: "var(--mute)" }}>{h.ts}</span>
                <span>{h.units} units</span>
                <span style={{ color: "var(--mute)", minWidth: 70, textAlign: "right" }}>
                  {Math.floor(h.duration / 60)}m {h.duration % 60}s
                </span>
              </div>
            ))}
          </section>
        </div>
      </aside>
    </div>
  );
}

Object.assign(window, { Scheduler });
