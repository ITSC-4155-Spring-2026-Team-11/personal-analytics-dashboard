import { useEffect, useState } from "react";

type PlanRow = { time: string; label: string; icon: string };

/** Sample plan rows — replace with API data when backend is ready. */
const SAMPLE_PLAN_ITEMS: PlanRow[] = [
  { time: "9:00 AM", label: "Class", icon: "📚" },
  { time: "11:00 AM", label: "Study Session", icon: "🧠" },
  { time: "2:00 PM", label: "Team Meeting", icon: "👥" },
  { time: "5:00 PM", label: "Review Tasks", icon: "✅" },
];

/** "9:00 AM" / "2:00 PM" → minutes from midnight; -1 if unparsable. */
function parseTimeToMinutes(t: string): number {
  const m = t.trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (!m) return -1;
  let h = Number(m[1]);
  const mins = Number(m[2]);
  const ap = m[3].toUpperCase();
  if (ap === "PM" && h !== 12) h += 12;
  if (ap === "AM" && h === 12) h = 0;
  return h * 60 + mins;
}

/** Index of the event that is happening now, or the next one (first row before the day starts). */
function indexOfCurrentOrUpcoming(items: PlanRow[]): number {
  if (items.length === 0) return 0;
  const starts = items.map((x) => parseTimeToMinutes(x.time));
  if (starts.some((s) => s < 0)) return 0;

  const now = new Date();
  const nowM = now.getHours() * 60 + now.getMinutes();

  if (nowM < starts[0]) return 0;

  for (let i = 0; i < items.length; i++) {
    const nextStart = i < items.length - 1 ? starts[i + 1] : 24 * 60;
    if (nowM >= starts[i] && nowM < nextStart) return i;
  }

  return items.length - 1;
}

/** Compact “today’s plan” block for the floating Tauri widget. */
export default function TodaysPlanWidget() {
  const count = SAMPLE_PLAN_ITEMS.length;
  const [highlightIndex, setHighlightIndex] = useState(() => indexOfCurrentOrUpcoming(SAMPLE_PLAN_ITEMS));

  useEffect(() => {
    function update() {
      setHighlightIndex(indexOfCurrentOrUpcoming(SAMPLE_PLAN_ITEMS));
    }
    update();
    const id = window.setInterval(update, 60_000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <div className="widgetPlanShell">
      <p className="widgetPlanMeta">
        {count} event{count === 1 ? "" : "s"} today
      </p>
      <div className="widgetPlanTimeline" role="list" aria-label="Scheduled items">
        {SAMPLE_PLAN_ITEMS.map((row, index) => {
          const isActive = index === highlightIndex;
          return (
            <div
              className={`widgetPlanRow${isActive ? " widgetPlanRow--active" : ""}`}
              key={row.time + row.label}
              role="listitem"
              aria-current={isActive ? "true" : undefined}
            >
              <span className="widgetPlanTime">{row.time}</span>
              <div className="widgetPlanRowBody">
                <span className="widgetPlanIcon" aria-hidden>
                  {row.icon}
                </span>
                <span className="widgetPlanLabel">{row.label}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
