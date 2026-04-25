import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Legend,
} from "recharts";
import { API_BASE } from "../apiBase.ts";

type Task = {
  id: number; title: string; category: string; duration_minutes: number;
  completed: boolean; task_type: string | null; fixed_start: string | null;
  fixed_end: string | null; importance: number; deadline: string | null; created_at: string;
};

type DailySummaryTask = {
  id: number; title: string; category: string; duration_minutes: number;
  duration_label: string; completed: boolean; task_type: string | null;
  fixed_start: string | null; fixed_end: string | null; importance: number;
};

type DailySummary = {
  date: string; tasks: DailySummaryTask[]; total_minutes: number;
  total_formatted: string; by_category: Record<string, number>; task_count: number;
};

const CATEGORY_COLORS: Record<string, string> = {
  Work: "#6c63ff", Study: "#74c0fc", Exercise: "#69db7c", Rest: "#ffd43b",
};

const CATEGORY_BG: Record<string, string> = {
  Work: "rgba(108,99,255,.15)", Study: "rgba(116,192,252,.15)",
  Exercise: "rgba(105,219,124,.15)", Rest: "rgba(255,212,59,.15)",
};

const ALL_CATEGORIES = ["Work", "Study", "Exercise", "Rest"];

function toDateStr(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}

function formatDuration(minutes: number): string {
  if (minutes === 0) return "0m";
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60), m = minutes % 60;
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

function formatDateLabel(ds: string) {
  const [y, m, d] = ds.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const today = new Date(); const todayStr = toDateStr(today);
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  if (ds === todayStr) return "Today";
  if (ds === toDateStr(yesterday)) return "Yesterday";
  return date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
}

function importanceColor(n: number) {
  if (n >= 5) return "#ff6b6b"; if (n === 4) return "#ffa94d";
  if (n === 3) return "#ffd43b"; if (n === 2) return "#74c0fc"; return "#9099b0";
}

function PieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }: {
  cx: number; cy: number; midAngle: number; innerRadius: number;
  outerRadius: number; percent: number; name: string;
}) {
  if (percent < 0.06) return null;
  const R = Math.PI / 180;
  const r = innerRadius + (outerRadius - innerRadius) * 0.55;
  return (
    <text x={cx + r * Math.cos(-midAngle * R)} y={cy + r * Math.sin(-midAngle * R)}
      fill="#fff" textAnchor="middle" dominantBaseline="central"
      style={{ fontSize: "0.72rem", fontWeight: 700, pointerEvents: "none" }}>
      {name}
    </text>
  );
}

export default function Analytics() {
  const nav = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [pieFilter, setPieFilter] = useState<"day"|"week"|"month"|"all">("day");
  const [selectedDate, setSelectedDate] = useState(toDateStr(new Date()));
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [dailyLoading, setDailyLoading] = useState(false);
  const [dailyErr, setDailyErr] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionStorage.getItem("access_token")) nav("/login", { replace: true });
  }, [nav]);

  useEffect(() => {
    const token = sessionStorage.getItem("access_token"); if (!token) return;
    setTasksLoading(true);
    fetch(`${API_BASE}/tasks/`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => setTasks(Array.isArray(data.tasks) ? data.tasks : []))
      .catch(() => {}).finally(() => setTasksLoading(false));
  }, []);

  useEffect(() => {
    const token = sessionStorage.getItem("access_token"); if (!token) return;
    setDailyLoading(true); setDailyErr(null);
    fetch(`${API_BASE}/analytics/daily?date=${selectedDate}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => setDailySummary(data))
      .catch(() => setDailyErr("Could not load daily summary."))
      .finally(() => setDailyLoading(false));
  }, [selectedDate]);

  const todayStr = toDateStr(new Date());
  const weekStart = (() => { const d = new Date(); d.setDate(d.getDate() - d.getDay()); return toDateStr(d); })();
  const monthStart = todayStr.slice(0, 7);

  const filteredTasks = tasks.filter(t => {
    if (pieFilter === "all") return true;
    if (!t.deadline) return false;
    if (pieFilter === "day")   return t.deadline === todayStr;
    if (pieFilter === "week")  return t.deadline >= weekStart && t.deadline <= todayStr;
    if (pieFilter === "month") return t.deadline.startsWith(monthStart);
    return true;
  });

  const categoryMinutes: Record<string, number> = {};
  for (const t of filteredTasks) categoryMinutes[t.category] = (categoryMinutes[t.category] ?? 0) + t.duration_minutes;

  const pieData = Object.entries(categoryMinutes).map(([name, value]) => ({ name, value })).sort((a,b) => b.value - a.value);
  const totalMinutes = Object.values(categoryMinutes).reduce((s, v) => s + v, 0);

  const last7 = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (6 - i)); const ds = toDateStr(d);
    return { date: ds, label: i === 6 ? "Today" : d.toLocaleDateString("en-US", { weekday: "short" }), count: tasks.filter(t => t.deadline === ds).length };
  });

  const stackedData = last7.map(day => {
    const entry: Record<string, string|number> = { label: day.label };
    for (const cat of ALL_CATEGORIES)
      entry[cat] = tasks.filter(t => t.deadline === day.date && t.category === cat).reduce((sum, t) => sum + t.duration_minutes, 0);
    return entry;
  });

  const filterBtn = (f: "day"|"week"|"month"|"all", label: string) => (
    <button key={f} type="button" onClick={() => setPieFilter(f)} style={{
      padding: "4px 10px", borderRadius: 99, fontSize: "0.75rem", fontWeight: 600,
      cursor: "pointer", border: "1px solid",
      background: pieFilter === f ? "rgba(108,99,255,.2)" : "transparent",
      borderColor: pieFilter === f ? "#6c63ff" : "var(--border)",
      color: pieFilter === f ? "#6c63ff" : "var(--muted)", transition: "all 0.15s",
    }}>{label}</button>
  );

  const tooltipStyle = { background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: "0.82rem" };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text)" }}>
      <header className="header-shell">
        <div className="header-row-1">
          <div className="brand">📋 PlannerHub</div>
          <div className="user-info user-info--compact">
            <button className="ghost-btn" type="button" onClick={() => nav("/dashboard")}>← Dashboard</button>
            <button className="signout-btn" onClick={() => { sessionStorage.clear(); nav("/login", { replace: true }); }}>Sign Out</button>
          </div>
        </div>
      </header>

      <main className="dash" style={{ display: "block", padding: "28px 24px", maxWidth: "none" }}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 800, margin: 0 }}>Analytics</h1>
          <p style={{ color: "var(--muted)", marginTop: 4, fontSize: "0.9rem" }}>Track how your time is spent across categories.</p>
        </div>

        {/* Row 1: Pie + Task count bar */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
          <div className="panel" style={{ padding: 24 }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 10 }}>
              <div>
                <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 4px" }}>Time by Category</h2>
                <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: 0 }}>
                  {pieFilter === "day" ? "Today" : pieFilter === "week" ? "This week" : pieFilter === "month" ? "This month" : "All time"} · {formatDuration(totalMinutes)} total
                </p>
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                {filterBtn("day","Day")}{filterBtn("week","Week")}{filterBtn("month","Month")}{filterBtn("all","All time")}
              </div>
            </div>
            {tasksLoading ? <div className="empty">Loading…</div> : pieData.length === 0 ? (
              <div className="empty" style={{ padding: "60px 0" }}>
                <div style={{ fontSize: "2rem", marginBottom: 8 }}>📭</div>No tasks for this period.
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={120} dataKey="value" labelLine={false} label={(p) => <PieLabel {...p} />}>
                      {pieData.map(e => <Cell key={e.name} fill={CATEGORY_COLORS[e.name] ?? "#888"} />)}
                    </Pie>
                    <Tooltip formatter={(v: number) => [formatDuration(v), "Time"]} contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 12, justifyContent: "center" }}>
                  {pieData.map(e => (
                    <div key={e.name} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.8rem" }}>
                      <span style={{ width: 10, height: 10, borderRadius: "50%", background: CATEGORY_COLORS[e.name] ?? "#888", display: "inline-block" }} />
                      <span style={{ color: "var(--muted)" }}>{e.name}</span>
                      <span style={{ fontWeight: 700 }}>{formatDuration(e.value)}</span>
                      <span style={{ color: "var(--muted)" }}>({Math.round(e.value / totalMinutes * 100)}%)</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="panel" style={{ padding: 24 }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 4px" }}>Last 7 Days</h2>
            <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0 0 20px" }}>Tasks scheduled per day</p>
            {tasksLoading ? <div className="empty">Loading…</div> : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={last7} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip formatter={(v: number) => [v, "Tasks"]} contentStyle={tooltipStyle} />
                  <Bar dataKey="count" name="Tasks" fill="#6c63ff" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Row 2: Category stat cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 20 }}>
          {ALL_CATEGORIES.map(cat => {
            const mins = categoryMinutes[cat] ?? 0;
            const count = filteredTasks.filter(t => t.category === cat).length;
            const pct = totalMinutes > 0 ? Math.round(mins / totalMinutes * 100) : 0;
            return (
              <div key={cat} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, padding: "16px 18px", borderTop: `3px solid ${CATEGORY_COLORS[cat]}` }}>
                <div style={{ fontSize: "0.75rem", fontWeight: 700, color: CATEGORY_COLORS[cat], textTransform: "uppercase", letterSpacing: "0.06em" }}>{cat}</div>
                <div style={{ fontSize: "1.5rem", fontWeight: 800, marginTop: 6 }}>{formatDuration(mins)}</div>
                <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: 2 }}>{count} task{count !== 1 ? "s" : ""} · {pct}%</div>
                <div style={{ marginTop: 10, height: 4, borderRadius: 99, background: "var(--border)" }}>
                  <div style={{ height: "100%", borderRadius: 99, background: CATEGORY_COLORS[cat], width: `${pct}%`, transition: "width 0.4s ease" }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Row 3: Stacked category breakdown */}
        <div className="panel" style={{ padding: 24, marginBottom: 20 }}>
          <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 4px" }}>Category Breakdown — Last 7 Days</h2>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0 0 20px" }}>Minutes per category per day</p>
          {tasksLoading ? <div className="empty">Loading…</div> : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={stackedData} margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} allowDecimals={false}
                  tickFormatter={(v: number) => v >= 60 ? `${Math.floor(v/60)}h` : `${v}m`} />
                <Tooltip formatter={(v: number, name: string) => [formatDuration(v), name]} contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: "0.8rem", paddingTop: 12 }} />
                {ALL_CATEGORIES.map((cat, i) => (
                  <Bar key={cat} dataKey={cat} stackId="a" fill={CATEGORY_COLORS[cat]}
                    radius={i === ALL_CATEGORIES.length - 1 ? [4,4,0,0] : [0,0,0,0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Row 4: Daily Summary */}
        <div className="panel" style={{ padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap", marginBottom: 20 }}>
            <div>
              <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: 0 }}>Daily Summary</h2>
              <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "2px 0 0" }}>Activities logged for a specific day</p>
            </div>
            <input type="date" className="input" value={selectedDate} onChange={e => setSelectedDate(e.target.value)}
              style={{ marginLeft: "auto", width: "auto", fontSize: "0.88rem" }} />
          </div>

          {dailyLoading ? <div className="empty">Loading…</div>
          : dailyErr ? <div className="error">{dailyErr}</div>
          : !dailySummary || dailySummary.task_count === 0 ? (
            <div className="empty" style={{ padding: "32px 0" }}>
              <div style={{ fontSize: "2rem", marginBottom: 8 }}>📭</div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>No activities for {formatDateLabel(selectedDate)}</div>
              <div style={{ fontSize: "0.83rem", color: "var(--muted)" }}>Tasks with a deadline on this date, or completed this day, will appear here.</div>
            </div>
          ) : (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 20, padding: "12px 16px", background: "rgba(108,99,255,.08)", borderRadius: 10, border: "1px solid rgba(108,99,255,.2)", marginBottom: 16, flexWrap: "wrap" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>{formatDateLabel(selectedDate)}</span>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, marginTop: 2 }}>Total: {dailySummary.total_formatted}</div>
                </div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginLeft: "auto" }}>
                  {Object.entries(dailySummary.by_category).map(([cat, mins]) => (
                    <div key={cat} style={{ padding: "4px 12px", borderRadius: 99, background: CATEGORY_BG[cat] ?? "rgba(255,255,255,.07)", border: `1px solid ${CATEGORY_COLORS[cat] ?? "#888"}40`, fontSize: "0.78rem", fontWeight: 600, color: CATEGORY_COLORS[cat] ?? "var(--text)" }}>
                      {cat}: {formatDuration(mins)}
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {dailySummary.tasks.map(t => (
                  <div key={t.id} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 14px", background: "var(--surface)", borderRadius: 10, border: "1px solid var(--border)", opacity: t.completed ? 0.7 : 1 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: "0.9rem", textDecoration: t.completed ? "line-through" : "none", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.title}</div>
                      <div style={{ display: "flex", gap: 8, marginTop: 4, alignItems: "center" }}>
                        <span style={{ width: 6, height: 6, borderRadius: "50%", background: importanceColor(t.importance), display: "inline-block", flexShrink: 0 }} />
                        {t.fixed_start && t.fixed_end && <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>🕐 {t.fixed_start}–{t.fixed_end}</span>}
                      </div>
                    </div>
                    <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent2)", flexShrink: 0 }}>{t.duration_label}</span>
                    <span style={{ padding: "3px 10px", borderRadius: 99, background: CATEGORY_BG[t.category] ?? "rgba(255,255,255,.07)", border: `1px solid ${CATEGORY_COLORS[t.category] ?? "#888"}40`, fontSize: "0.75rem", fontWeight: 600, color: CATEGORY_COLORS[t.category] ?? "var(--text)", flexShrink: 0 }}>
                      {t.category}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}