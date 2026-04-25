import { useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { hideWidgetRobust } from "./widgetInvoke";
import "./App.css";
import LoginView from "./views/LoginView";
import DashboardView from "./views/DashboardView";
import TodaysPlanWidget from "./components/TodaysPlanWidget";

function formatWidgetDateShort(d: Date) {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${days[d.getDay()]}, ${months[d.getMonth()]} ${d.getDate()}`;
}

function WidgetContent() {
  const today = new Date();

  return (
    <div className="widget-wrap">
      <main className="widget">
        <div className="widgetHeader">
          <div className="widgetHeaderDrag" data-tauri-drag-region>
            <span className="widgetDragHandle" aria-hidden>⋮⋮</span>
            <div className="widgetHeaderTitles">
              <span className="widgetTitle">Today&apos;s Plan</span>
              <span className="widgetDate">{formatWidgetDateShort(today)}</span>
            </div>
          </div>
          <button
            type="button"
            className="widgetHideBtn"
            onClick={() => {
              hideWidgetRobust().catch(() => {});
            }}
            aria-label="Close widget"
            title="Close widget"
          >
            <span className="widgetHideBtnIcon" aria-hidden>
              ×
            </span>
          </button>
        </div>

        <div className="widgetBody">
          <TodaysPlanWidget />
        </div>
      </main>
    </div>
  );
}

function App() {
  const isWidget = new URLSearchParams(window.location.search).get("widget") === "1";

  if (isWidget) {
    return <WidgetContent />;
  }

  const accessToken =
    sessionStorage.getItem("access_token") || localStorage.getItem("access_token") || "";

  // Sync token to Rust so the widget window can get it (widget has separate storage).
  useEffect(() => {
    if (!accessToken) return;
    invoke("set_widget_token", { token: accessToken }).catch(() => {});
  }, [accessToken]);

  if (!accessToken) {
    return (
      <LoginView
        onAuthed={() => {
          // Simple "route": re-render will show the main app once token exists.
          window.location.reload();
        }}
      />
    );
  }

  function handleSignOut() {
    invoke("set_widget_token", { token: null }).catch(() => {});
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
    sessionStorage.removeItem("planner_session");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("planner_session");
    window.location.reload();
  }

  return (
    <DashboardView onSignOut={handleSignOut} />
  );
}

export default App;
