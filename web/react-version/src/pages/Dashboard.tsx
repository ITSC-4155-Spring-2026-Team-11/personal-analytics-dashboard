import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API = "http://localhost:8000";

type Session = { email?: string; loginTime?: string };

export default function Dashboard() {
  const nav = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [output, setOutput] = useState("Loading tasks...");

  useEffect(() => {
    const raw = sessionStorage.getItem("planner_session");
    const token = sessionStorage.getItem("access_token");

    if (!raw || !token) {
      nav("/login", { replace: true });
      return;
    }

    try {
      setSession(JSON.parse(raw));
    } catch {
      sessionStorage.clear();
      nav("/login", { replace: true });
    }
  }, [nav]);

  useEffect(() => {
    async function loadTasks() {
      if (!session) return;

      const token = sessionStorage.getItem("access_token");
      if (!token) {
        nav("/login", { replace: true });
        return;
      }

      try {
        const res = await fetch(`${API}/tasks/`, {
          headers: {
            // Attach the JWT on every request to the backend
            Authorization: `Bearer ${token}`,
          },
        });

        if (res.status === 401) {
          // Token expired — send back to login
          sessionStorage.clear();
          nav("/login", { replace: true });
          return;
        }

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
  }, [session, nav]);

  async function signOut() {
    const refreshToken = sessionStorage.getItem("refresh_token");

    // Tell the backend to revoke the refresh token
    if (refreshToken) {
      try {
        await fetch(`${API}/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // Ignore errors — clear session locally regardless
      }
    }

    sessionStorage.clear();
    localStorage.clear();
    nav("/login", { replace: true });
  }

  if (!session) return null;

  return (
    <>
      <header>
        <div className="brand">📋 PlannerHub</div>
        <div className="user-info">
          <span>{`👋 Welcome, ${session.email ?? "User"}`}</span>
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
