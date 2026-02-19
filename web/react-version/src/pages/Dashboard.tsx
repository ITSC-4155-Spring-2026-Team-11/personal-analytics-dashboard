import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

type Session = { user: string; email?: string; loginTime?: string };

export default function Dashboard() {
  const nav = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [output, setOutput] = useState("Loading tasks...");

    useEffect(() => {
    const raw = sessionStorage.getItem("planner_session");
    if (!raw) {
        nav("/login", { replace: true });
        return;
    }

    try {
        setSession(JSON.parse(raw));
    } catch {
        sessionStorage.removeItem("planner_session");
        nav("/login", { replace: true });
    }
    }, [nav]);


  useEffect(() => {
    async function loadTasks() {
      if (!session) return;

      try {
        const res = await fetch("/tasks/");
        const data = await res.json();
        setOutput(
          data.tasks?.length
            ? JSON.stringify(data.tasks, null, 2)
            : "No tasks yet. Add some tasks to get started!"
        );
      } catch {
        setOutput("Could not load tasks. Is the backend running?");
      }
    }
    loadTasks();
  }, [session]);

  function signOut() {
    sessionStorage.removeItem("planner_session");
    nav("/login", { replace: true });
  }

  if (!session) return null;

  return (
    <>
      <header>
        <div className="brand">📋 PlannerHub</div>
        <div className="user-info">
          <span>{`👋 Welcome, ${session.user}`}</span>
          <button className="signout-btn" onClick={signOut}>
            Sign Out
          </button>
        </div>
      </header>

      <main>
        <h1>Today's Schedule</h1>
        <p>Here's what's on your plate for today.</p>
        <pre id="output">{output}</pre>
      </main>
    </>
  );
}
