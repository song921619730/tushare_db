// Mock data for Tushare DB dashboard — feels real without a backend.

const INTERFACE_CATEGORIES = ["行情", "基本面", "资金流", "财务", "指数", "公告"];

const INTERFACES = [
  ["daily", "行情", "P0", "daily", "stock_daily", "done", "2026-04-25 15:32:18", 28451209, 8200],
  ["moneyflow", "资金流", "P0", "daily", "stock_moneyflow", "done", "2026-04-25 15:33:02", 18204331, 6100],
  ["adj_factor", "行情", "P0", "daily", "adj_factor", "done", "2026-04-25 15:32:44", 28440901, 5200],
  ["weekly", "行情", "P1", "weekly", "stock_weekly", "done", "2026-04-25 15:30:55", 5820412, 1100],
  ["monthly", "行情", "P1", "monthly", "stock_monthly", "done", "2026-04-25 15:30:05", 1420055, 420],
  ["stk_limit", "行情", "P0", "daily", "stock_limit", "running", "2026-04-25 15:34:12", 28201188, 7400],
  ["income", "财务", "P1", "quarterly", "fina_income", "done", "2026-04-24 22:12:03", 442109, 180],
  ["balancesheet", "财务", "P1", "quarterly", "fina_balance", "done", "2026-04-24 22:14:41", 441102, 220],
  ["cashflow", "财务", "P1", "quarterly", "fina_cashflow", "partial", "2026-04-24 22:19:22", 428933, 240],
  ["fina_indicator", "财务", "P2", "quarterly", "fina_indicator", "done", "2026-04-24 22:22:18", 442012, 310],
  ["top_list", "资金流", "P2", "daily", "top_list", "done", "2026-04-25 15:12:04", 82104, 640],
  ["top_inst", "资金流", "P2", "daily", "top_inst", "done", "2026-04-25 15:12:44", 120409, 820],
  ["hk_hold", "资金流", "P1", "daily", "hk_hold", "done", "2026-04-25 15:22:01", 18200455, 4100],
  ["margin", "资金流", "P1", "daily", "margin", "failed", "2026-04-25 15:24:18", 2840192, 5400],
  ["margin_detail", "资金流", "P2", "daily", "margin_detail", "done", "2026-04-25 15:26:33", 14201988, 6800],
  ["index_daily", "指数", "P0", "daily", "index_daily", "done", "2026-04-25 15:28:12", 1420880, 900],
  ["index_weekly", "指数", "P2", "weekly", "index_weekly", "done", "2026-04-25 15:29:02", 284022, 210],
  ["index_classify", "指数", "P2", "static", "index_classify", "done", "2026-04-20 09:00:00", 3200, 120],
  ["stock_basic", "基本面", "P0", "static", "stock_basic", "done", "2026-04-25 06:00:00", 5203, 80],
  ["namechange", "基本面", "P2", "event", "namechange", "done", "2026-04-25 06:02:11", 18404, 110],
  ["new_share", "基本面", "P2", "daily", "new_share", "done", "2026-04-25 06:03:04", 4012, 90],
  ["dividend", "基本面", "P1", "event", "dividend", "done", "2026-04-25 06:05:18", 98211, 280],
  ["stk_holdernumber", "基本面", "P2", "quarterly", "stk_holdernumber", "done", "2026-04-24 22:30:11", 180422, 150],
  ["disclosure_date", "公告", "P2", "event", "disclosure_date", "partial", "2026-04-25 06:10:32", 41200, 320],
  ["suspend_d", "行情", "P2", "event", "suspend_d", "done", "2026-04-25 06:12:18", 18422, 140],
  ["broker_recommend", "公告", "P3", "daily", "broker_recommend", "pending", "—", 0, 0],
  ["forecast", "财务", "P2", "event", "forecast", "done", "2026-04-24 22:40:02", 204102, 520],
  ["express", "财务", "P2", "event", "express", "done", "2026-04-24 22:41:18", 80422, 310],
];

const INTERFACE_ROWS = INTERFACES.map(([name, cat, pri, mode, table, status, lastSync, rows, durMs], idx) => ({
  id: idx,
  name, cat, pri, mode, table, status, lastSync, rows, durMs,
  sparkline: Array.from({ length: 14 }, (_, i) => {
    const base = 50 + Math.sin((idx + i) * 0.7) * 15;
    return Math.max(5, Math.round(base + (Math.random() - 0.3) * 30 * (status === "failed" ? 0.3 : 1)));
  }),
}));

// Status counts
const STATUS_COUNTS = INTERFACE_ROWS.reduce((acc, r) => {
  acc[r.status] = (acc[r.status] || 0) + 1;
  return acc;
}, {});

// 7-day trend
const TREND_7D = [
  { day: "04-19", rows: 48201044, tables: 178 },
  { day: "04-20", rows: 52104812, tables: 180 },
  { day: "04-21", rows: 54208119, tables: 181 },
  { day: "04-22", rows: 58302104, tables: 181 },
  { day: "04-23", rows: 61204882, tables: 182 },
  { day: "04-24", rows: 64820412, tables: 182 },
  { day: "04-25", rows: 68420188, tables: 182 },
];

// Alerts
const ALERTS = [
  { time: "15:24", interface: "margin", level: "error", msg: "HTTP 429 — rate limit; 3 retries exhausted" },
  { time: "14:41", interface: "cashflow", level: "warn", msg: "partial: 238/240 scopes completed; 2 timeouts" },
  { time: "11:08", interface: "disclosure_date", level: "warn", msg: "partial: 41.2k of ~48k rows ingested" },
  { time: "09:02", interface: "broker_recommend", level: "info", msg: "pending — awaiting first run" },
];

// P0 last-sync timings
const P0_INTERFACES = INTERFACE_ROWS.filter(r => r.pri === "P0");

// Current run progress
const CURRENT_RUN = {
  id: "run_20260425_153412",
  startedAt: "2026-04-25 15:34:12",
  unitsTotal: 182,
  unitsDone: 164,
  runningInterface: "stk_limit",
  elapsedMs: 2814000,
  etaMs: 412000,
};

// Totals
const TOTALS = {
  tables: 182,
  tablesSynced: 178,
  totalRows: 684201880,
  storageGb: 42.8,
  todayNewRows: 3820412,
};

// Hourly heatmap data for api_calls (hours x interfaces sample — tighter subset)
const HEATMAP_INTERFACES = ["daily", "moneyflow", "adj_factor", "stk_limit", "hk_hold", "margin", "index_daily", "top_list"];
const HEATMAP = HEATMAP_INTERFACES.map((iface, i) =>
  Array.from({ length: 24 }, (_, h) => {
    if (h < 6 || h > 22) return Math.floor(Math.random() * 3);
    const base = (iface === "daily" || iface === "moneyflow") ? 40 : 20;
    return Math.floor(base + Math.sin((h + i) * 0.9) * 10 + Math.random() * 15);
  })
);

// OHLCV sample for K-line
const OHLCV_SAMPLE = (() => {
  const rows = [];
  let price = 17.82;
  const dates = [];
  const base = new Date(2026, 2, 1); // 2026-03-01
  for (let i = 0; i < 45; i++) {
    const d = new Date(base.getTime() + i * 86400000);
    const dow = d.getDay();
    if (dow === 0 || dow === 6) continue;
    dates.push(d.toISOString().slice(0, 10).replace(/-/g, ""));
  }
  dates.forEach((dt, i) => {
    const change = (Math.sin(i * 0.4) + Math.random() * 0.6 - 0.3) * 0.4;
    const open = price;
    const close = Math.max(1, price + change);
    const high = Math.max(open, close) + Math.random() * 0.3;
    const low = Math.min(open, close) - Math.random() * 0.3;
    const vol = Math.floor(8_000_000 + Math.random() * 12_000_000);
    const amount = Math.floor(vol * (open + close) / 2);
    const pct = ((close - open) / open) * 100;
    rows.push({ trade_date: dt, ts_code: "000001.SZ", open: +open.toFixed(2),
      high: +high.toFixed(2), low: +low.toFixed(2), close: +close.toFixed(2),
      pre_close: +open.toFixed(2), change: +(close - open).toFixed(2),
      pct_chg: +pct.toFixed(2), vol, amount });
    price = close;
  });
  return rows;
})();

// API call log entries
const API_CALLS = Array.from({ length: 120 }, (_, i) => {
  const hour = 6 + Math.floor(Math.random() * 18);
  const min = Math.floor(Math.random() * 60);
  const sec = Math.floor(Math.random() * 60);
  const ifaces = ["daily", "moneyflow", "adj_factor", "stk_limit", "hk_hold",
    "margin", "index_daily", "top_list", "income", "balancesheet"];
  const iface = ifaces[Math.floor(Math.random() * ifaces.length)];
  const failed = Math.random() < 0.08;
  const rate = Math.random() < 0.03;
  const status = failed ? "failed" : rate ? "rate_limited" : "success";
  return {
    started: `2026-04-25 ${String(hour).padStart(2,"0")}:${String(min).padStart(2,"0")}:${String(sec).padStart(2,"0")}`,
    interface: iface,
    params_hash: Math.random().toString(16).slice(2, 10),
    duration_ms: Math.floor(failed ? 30000 + Math.random() * 2000 : 180 + Math.random() * 2200),
    status,
    rows: status === "success" ? Math.floor(500 + Math.random() * 8000) : 0,
    error: failed ? "ConnectionTimeout after 30s" : rate ? "HTTP 429 — rate limit exceeded" : "",
  };
}).sort((a, b) => b.started.localeCompare(a.started));

// Scheduler jobs
const SCHEDULER_JOBS = [
  { id: "j1", name: "daily_eod_prices",   cn: "日线行情",   hour: 16.5, duration: 0.8, interfaces: ["daily", "adj_factor", "stk_limit", "index_daily"], last: "done",    nextIn: "23h 58m" },
  { id: "j2", name: "daily_moneyflow",    cn: "资金流",     hour: 17.5, duration: 0.6, interfaces: ["moneyflow", "hk_hold", "top_list", "top_inst"],    last: "done",    nextIn: "1d 0h" },
  { id: "j3", name: "daily_margin",       cn: "融资融券",   hour: 18,   duration: 0.4, interfaces: ["margin", "margin_detail"],                         last: "failed",  nextIn: "1d 0h" },
  { id: "j4", name: "weekly_rollup",      cn: "周线汇总",   hour: 19,   duration: 0.3, interfaces: ["weekly", "index_weekly"],                          last: "done",    nextIn: "6d 3h" },
  { id: "j5", name: "fundamentals_q",     cn: "季度财报",   hour: 22,   duration: 1.2, interfaces: ["income", "balancesheet", "cashflow", "fina_indicator"], last: "partial", nextIn: "13h 25m" },
  { id: "j6", name: "events_refresh",     cn: "事件刷新",   hour: 6,    duration: 0.3, interfaces: ["namechange", "new_share", "dividend", "suspend_d", "disclosure_date"], last: "done", nextIn: "14h 26m" },
  { id: "j7", name: "static_refresh",     cn: "静态数据",   hour: 6.5,  duration: 0.2, interfaces: ["stock_basic", "index_classify"],                   last: "done",    nextIn: "14h 56m" },
];

// Verify results
const VERIFY_RESULTS = [
  { interface: "daily",         table: "stock_daily",     expected: 28451209, actual: 28451209, diff: 0,      status: "ok" },
  { interface: "moneyflow",     table: "stock_moneyflow", expected: 18204331, actual: 18204331, diff: 0,      status: "ok" },
  { interface: "adj_factor",    table: "adj_factor",      expected: 28440901, actual: 28440901, diff: 0,      status: "ok" },
  { interface: "stk_limit",     table: "stock_limit",     expected: 28201188, actual: 28200412, diff: -776,   status: "diff" },
  { interface: "hk_hold",       table: "hk_hold",         expected: 18200455, actual: 18200455, diff: 0,      status: "ok" },
  { interface: "margin",        table: "margin",          expected: 2840192,  actual: 2829811,  diff: -10381, status: "diff" },
  { interface: "index_daily",   table: "index_daily",     expected: 1420880,  actual: 1420880,  diff: 0,      status: "ok" },
  { interface: "cashflow",      table: "fina_cashflow",   expected: 428933,   actual: 426120,   diff: -2813,  status: "diff" },
];


