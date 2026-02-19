import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

type Tab = "login" | "signup";

type DBUser = { password: string; name: string };
type DB = Record<string, DBUser>;

type ToastType = "success" | "error" | "warn";

type ToastState = {
  show: boolean;
  type?: ToastType;
  icon?: string;
  msg?: string;
};

type FieldErrors = Record<string, { invalid: boolean; msg: string }>;

type StrengthState = {
  show: boolean;
  width: string;
  bg: string;
  label: string;
};

function isValidEmail(email: string) {
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRe.test(email);
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

export default function Login() {
  const nav = useNavigate();

  // Simulated DB (mutable like the original HTML)
  const dbRef = useRef<DB>({
    "demo@planner.com": { password: "Demo1234!", name: "Demo User" },
    "test@planner.com": { password: "Test5678!", name: "Test User" },
  });

  const [tab, setTab] = useState<Tab>("login");

  // Login form state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPass, setLoginPass] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  // Signup form state
  const [suName, setSuName] = useState("");
  const [suEmail, setSuEmail] = useState("");
  const [suPass, setSuPass] = useState("");
  const [suConfirm, setSuConfirm] = useState("");

  // UI states
  const [loginToast, setLoginToast] = useState<ToastState>({ show: false });
  const [signupToast, setSignupToast] = useState<ToastState>({ show: false });

  const [loginLoading, setLoginLoading] = useState(false);
  const [signupLoading, setSignupLoading] = useState(false);

  const [loginSuccess, setLoginSuccess] = useState(false);
  const [signupSuccess, setSignupSuccess] = useState(false);

  // Validation
  const [loginFields, setLoginFields] = useState<FieldErrors>({
    email: { invalid: false, msg: "This field is required" },
    pass: { invalid: false, msg: "This field is required" },
  });

  const [signupFields, setSignupFields] = useState<FieldErrors>({
    name: { invalid: false, msg: "Full name is required" },
    email: { invalid: false, msg: "A valid email is required" },
    pass: { invalid: false, msg: "Password must be at least 8 characters" },
    confirm: { invalid: false, msg: "Passwords do not match" },
  });

  // Password visibility
  const [showLoginPw, setShowLoginPw] = useState(false);
  const [showSuPw, setShowSuPw] = useState(false);
  const [showSuConfirmPw, setShowSuConfirmPw] = useState(false);

  // Lockout (after 5 failures)
  const [failCount, setFailCount] = useState(0);
  const [lockUntil, setLockUntil] = useState<number>(0);
  const [lockLeft, setLockLeft] = useState<number>(30);

  // Strength meter
  const [strength, setStrength] = useState<StrengthState>({
    show: false,
    width: "20%",
    bg: "#ff6b6b",
    label: "Weak",
  });

  const isLocked = useMemo(() => Date.now() < lockUntil, [lockUntil]);

  useEffect(() => {
    // If already signed in, go to dashboard
    const raw = sessionStorage.getItem("planner_session");
    if (raw) nav("/dashboard", { replace: true });
  }, [nav]);

  useEffect(() => {
    if (!lockUntil) return;

    const id = window.setInterval(() => {
      const left = Math.ceil((lockUntil - Date.now()) / 1000);
      if (left <= 0) {
        window.clearInterval(id);
        setLockUntil(0);
        setFailCount(0);
        setLockLeft(30);
      } else {
        setLockLeft(left);
      }
    }, 1000);

    return () => window.clearInterval(id);
  }, [lockUntil]);

  function clearToasts() {
    setLoginToast({ show: false });
    setSignupToast({ show: false });
  }

  function switchTab(next: Tab) {
    setTab(next);
    clearToasts();
    setLoginSuccess(false);
    setSignupSuccess(false);

    // Optional: clear invalid styling when switching
    setLoginFields((p) => ({
      ...p,
      email: { ...p.email, invalid: false },
      pass: { ...p.pass, invalid: false },
    }));
    setSignupFields((p) => ({
      ...p,
      name: { ...p.name, invalid: false },
      email: { ...p.email, invalid: false },
      pass: { ...p.pass, invalid: false },
      confirm: { ...p.confirm, invalid: false },
    }));
  }

  function showToast(which: "login" | "signup", type: ToastType, icon: string, msg: string) {
    const toast: ToastState = { show: true, type, icon, msg };
    if (which === "login") setLoginToast(toast);
    else setSignupToast(toast);
  }

  function startLockout(seconds: number) {
    setLockLeft(seconds);
    setLockUntil(Date.now() + seconds * 1000);
  }

  function updateStrength(val: string) {
    if (!val) {
      setStrength((s) => ({ ...s, show: false }));
      return;
    }

    let score = 0;
    if (val.length >= 8) score++;
    if (/[A-Z]/.test(val)) score++;
    if (/[0-9]/.test(val)) score++;
    if (/[^A-Za-z0-9]/.test(val)) score++;

    const map = [
      { w: "20%", bg: "#ff6b6b", lbl: "Very weak" },
      { w: "40%", bg: "#ffa94d", lbl: "Weak" },
      { w: "65%", bg: "#ffd43b", lbl: "Fair" },
      { w: "85%", bg: "#69db7c", lbl: "Good" },
      { w: "100%", bg: "#38d9a9", lbl: "Strong 💪" },
    ];

    const pick = map[Math.max(0, score - 1)];
    setStrength({ show: true, width: pick.w, bg: pick.bg, label: pick.lbl });
  }

  async function onLoginSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isLocked) return;

    clearToasts();

    const email = loginEmail.trim();
    const pass = loginPass;

    // Scenario 4: missing fields
    let ok = true;

    if (!email) {
      ok = false;
      setLoginFields((p) => ({
        ...p,
        email: { invalid: true, msg: "Email or username is required" },
      }));
    } else {
      setLoginFields((p) => ({ ...p, email: { ...p.email, invalid: false } }));
    }

    if (!pass) {
      ok = false;
      setLoginFields((p) => ({
        ...p,
        pass: { invalid: true, msg: "Password is required" },
      }));
    } else {
      setLoginFields((p) => ({ ...p, pass: { ...p.pass, invalid: false } }));
    }

    if (!ok) {
      showToast("login", "error", "⚠️", "Please fill in all required fields.");
      return;
    }

    // Loading state
    setLoginLoading(true);
    await sleep(900);
    setLoginLoading(false);

    const db = dbRef.current;

    // Scenario 3: account doesn't exist
    if (!db[email]) {
      const nextFails = failCount + 1;
      setFailCount(nextFails);

      setLoginFields((p) => ({
        ...p,
        email: { invalid: true, msg: "No account found with this email" },
      }));
      showToast(
        "login",
        "error",
        "❌",
        "Account does not exist. Please check your email or sign up."
      );

      if (nextFails >= 5) startLockout(30);
      return;
    }

    // Scenario 2: wrong password
    if (db[email].password !== pass) {
      const nextFails = failCount + 1;
      setFailCount(nextFails);

      setLoginFields((p) => ({
        ...p,
        pass: { invalid: true, msg: "Incorrect password" },
      }));

      const remaining = 5 - nextFails;
      const msg =
        remaining > 0
          ? `Incorrect password. ${remaining} attempt${remaining !== 1 ? "s" : ""} remaining before lockout.`
          : "Too many failed attempts.";

      showToast("login", "error", "🔐", msg);

      if (nextFails >= 5) startLockout(30);
      return;
    }

    // Scenario 1 + 5: success
    setFailCount(0);

    const session = {
      user: db[email].name,
      email,
      loginTime: new Date().toISOString(),
    };

    // Keep original behavior (sessionStorage), but if rememberMe checked, mirror to localStorage too
    sessionStorage.setItem("planner_session", JSON.stringify(session));
    if (rememberMe) localStorage.setItem("planner_session", JSON.stringify(session));
    else localStorage.removeItem("planner_session");

    setLoginSuccess(true);

    // brief success then redirect
    setTimeout(() => {
      nav("/dashboard", { replace: true });
    }, 1800);
  }

  function onForgotPassword() {
    const email = loginEmail.trim();
    const db = dbRef.current;

    if (email && db[email]) {
      showToast("login", "success", "📧", `Password reset link sent to ${email}`);
    } else if (email) {
      showToast("login", "error", "❌", "No account found with that email address.");
    } else {
      showToast("login", "warn", "💡", 'Enter your email above, then click "Forgot password?"');
    }
  }

  async function onSignupSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearToasts();

    const name = suName.trim();
    const email = suEmail.trim();
    const pass = suPass;
    const confirm = suConfirm;

    let ok = true;

    if (!name) {
      ok = false;
      setSignupFields((p) => ({
        ...p,
        name: { invalid: true, msg: "Full name is required" },
      }));
    } else {
      setSignupFields((p) => ({ ...p, name: { ...p.name, invalid: false } }));
    }

    if (!email || !isValidEmail(email)) {
      ok = false;
      setSignupFields((p) => ({
        ...p,
        email: { invalid: true, msg: "Enter a valid email address" },
      }));
    } else {
      setSignupFields((p) => ({ ...p, email: { ...p.email, invalid: false } }));
    }

    if (pass.length < 8) {
      ok = false;
      setSignupFields((p) => ({
        ...p,
        pass: { invalid: true, msg: "Password must be at least 8 characters" },
      }));
    } else {
      setSignupFields((p) => ({ ...p, pass: { ...p.pass, invalid: false } }));
    }

    if (pass !== confirm) {
      ok = false;
      setSignupFields((p) => ({
        ...p,
        confirm: { invalid: true, msg: "Passwords do not match" },
      }));
    } else {
      setSignupFields((p) => ({ ...p, confirm: { ...p.confirm, invalid: false } }));
    }

    if (!ok) {
      showToast("signup", "error", "⚠️", "Please correct the errors above.");
      return;
    }

    const db = dbRef.current;

    // Email already exists
    if (db[email]) {
      setSignupFields((p) => ({
        ...p,
        email: { invalid: true, msg: "An account with this email already exists" },
      }));
      showToast("signup", "error", "❌", "This email is already registered. Try signing in.");
      return;
    }

    setSignupLoading(true);
    await sleep(1000);
    setSignupLoading(false);

    // Register user
    db[email] = { password: pass, name };
    setSignupSuccess(true);

    // After a moment, take them back to sign in like the original
    setTimeout(() => {
      resetSignup();
    }, 2200);
  }

  function resetSignup() {
    setSuName("");
    setSuEmail("");
    setSuPass("");
    setSuConfirm("");
    setSignupSuccess(false);
    setSignupToast({ show: false });
    updateStrength("");
    switchTab("login");
  }

  return (
    <div className="login-layout">
      {/* LEFT */}
      <div className="left-panel">
        <div className="grid-bg"></div>

        <div className="brand">
          <div className="brand-icon">📋</div>
          <span className="brand-name">PlannerHub</span>
        </div>

        <div className="hero-text">
          <h1>
            Your plans,
            <br />
            <span>beautifully organized.</span>
          </h1>
          <p>
            Stay on top of every task, deadline, and goal — all from one clean, powerful dashboard.
          </p>

          <ul className="feature-list">
            <li>
              <span className="dot"></span> Smart task boards with drag &amp; drop
            </li>
            <li>
              <span className="dot"></span> Calendar sync &amp; deadline reminders
            </li>
            <li>
              <span className="dot"></span> Team collaboration &amp; sharing
            </li>
            <li>
              <span className="dot"></span> Real-time progress analytics
            </li>
          </ul>
        </div>
      </div>

      {/* RIGHT */}
      <div className="right-panel">
        <div className="auth-box">
          {/* Tab bar */}
          <div className="tab-bar">
            <button
              className={`tab-btn ${tab === "login" ? "active" : ""}`}
              id="tab-login"
              type="button"
              onClick={() => switchTab("login")}
            >
              Sign In
            </button>
            <button
              className={`tab-btn ${tab === "signup" ? "active" : ""}`}
              id="tab-signup"
              type="button"
              onClick={() => switchTab("signup")}
            >
              Create Account
            </button>
          </div>

          {/* LOGIN */}
          {tab === "login" && !loginSuccess && (
            <div id="panel-login">
              <div className="form-title">Welcome back 👋</div>
              <div className="form-sub">Sign in to your PlannerHub dashboard</div>

              {/* Lockout bar */}
              <div className={`lockout-bar ${isLocked ? "show" : ""}`} id="lockout-bar">
                Too many failed attempts. Try again in{" "}
                <span className="lockout-timer" id="lockout-timer">
                  {lockLeft}
                </span>
                s
              </div>

              {/* Toast */}
              <div
                className={`toast ${loginToast.show ? "show" : ""} ${loginToast.type ?? ""}`}
                id="login-toast"
              >
                <span className="toast-icon" id="login-toast-icon">
                  {loginToast.icon ?? ""}
                </span>
                <span id="login-toast-msg">{loginToast.msg ?? ""}</span>
              </div>

              <form id="login-form" noValidate onSubmit={onLoginSubmit}>
                {/* Email */}
                <div className={`field ${loginFields.email.invalid ? "invalid" : ""}`} id="f-login-email">
                  <label htmlFor="login-email">Email or Username</label>
                  <div className="input-wrap">
                    <span className="icon">✉</span>
                    <input
                      autoComplete="username"
                      id="login-email"
                      type="text"
                      placeholder="you@example.com"
                      value={loginEmail}
                      onChange={(e) => setLoginEmail(e.target.value)}
                      disabled={loginLoading || isLocked}
                    />
                  </div>
                  <span className="field-error" id="err-login-email">
                    {loginFields.email.msg}
                  </span>
                </div>

                {/* Password */}
                <div className={`field ${loginFields.pass.invalid ? "invalid" : ""}`} id="f-login-pass">
                  <label htmlFor="login-password">Password</label>
                  <div className="input-wrap">
                    <span className="icon">🔑</span>
                    <input
                      autoComplete="current-password"
                      id="login-password"
                      type={showLoginPw ? "text" : "password"}
                      placeholder="••••••••"
                      value={loginPass}
                      onChange={(e) => setLoginPass(e.target.value)}
                      disabled={loginLoading || isLocked}
                    />
                    <button
                      className="icon-right"
                      type="button"
                      onClick={() => setShowLoginPw((v) => !v)}
                      disabled={loginLoading || isLocked}
                    >
                      {showLoginPw ? "🙈" : "👁"}
                    </button>
                  </div>
                  <span className="field-error" id="err-login-pass">
                    {loginFields.pass.msg}
                  </span>
                </div>

                <div className="row-between">
                  <label className="remember-wrap">
                    <input
                      id="remember-me"
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      disabled={loginLoading || isLocked}
                    />{" "}
                    Remember me
                  </label>
                  <button
                    className="link-btn"
                    type="button"
                    onClick={onForgotPassword}
                    disabled={loginLoading || isLocked}
                  >
                    Forgot password?
                  </button>
                </div>

                <button
                  className={`submit-btn ${loginLoading ? "loading" : ""}`}
                  id="login-btn"
                  type="submit"
                  disabled={loginLoading || isLocked}
                >
                  <span className="btn-text">Sign In</span>
                  <div className="spinner"></div>
                </button>
              </form>

              <div className="switch-text">
                Don't have an account?{" "}
                <button type="button" onClick={() => switchTab("signup")}>
                  Create one free
                </button>
              </div>
            </div>
          )}

          {/* LOGIN SUCCESS */}
          {tab === "login" && loginSuccess && (
            <div className="success-screen show" id="login-success">
              <div className="success-circle">✓</div>
              <h2>You're in!</h2>
              <p>Secure session created. Taking you to your dashboard…</p>
              <button className="submit-btn" type="button" onClick={() => nav("/dashboard", { replace: true })}>
                Go to Dashboard →
              </button>
            </div>
          )}

          {/* SIGNUP */}
          {tab === "signup" && !signupSuccess && (
            <div id="panel-signup">
              <div className="form-title">Create account</div>
              <div className="form-sub">Join PlannerHub — free forever</div>

              {/* Toast */}
              <div
                className={`toast ${signupToast.show ? "show" : ""} ${signupToast.type ?? ""}`}
                id="signup-toast"
              >
                <span className="toast-icon" id="signup-toast-icon">
                  {signupToast.icon ?? ""}
                </span>
                <span id="signup-toast-msg">{signupToast.msg ?? ""}</span>
              </div>

              <form id="signup-form" noValidate onSubmit={onSignupSubmit}>
                {/* Full name */}
                <div className={`field ${signupFields.name.invalid ? "invalid" : ""}`} id="f-su-name">
                  <label htmlFor="su-name">Full Name</label>
                  <div className="input-wrap">
                    <span className="icon">👤</span>
                    <input
                      autoComplete="name"
                      id="su-name"
                      type="text"
                      placeholder="Alex Johnson"
                      value={suName}
                      onChange={(e) => setSuName(e.target.value)}
                      disabled={signupLoading}
                    />
                  </div>
                  <span className="field-error" id="err-su-name">
                    {signupFields.name.msg}
                  </span>
                </div>

                {/* Email */}
                <div className={`field ${signupFields.email.invalid ? "invalid" : ""}`} id="f-su-email">
                  <label htmlFor="su-email">Email Address</label>
                  <div className="input-wrap">
                    <span className="icon">✉</span>
                    <input
                      autoComplete="email"
                      id="su-email"
                      type="email"
                      placeholder="you@example.com"
                      value={suEmail}
                      onChange={(e) => setSuEmail(e.target.value)}
                      disabled={signupLoading}
                    />
                  </div>
                  <span className="field-error" id="err-su-email">
                    {signupFields.email.msg}
                  </span>
                </div>

                {/* Password */}
                <div className={`field ${signupFields.pass.invalid ? "invalid" : ""}`} id="f-su-pass">
                  <label htmlFor="su-password">Password</label>
                  <div className="input-wrap">
                    <span className="icon">🔑</span>
                    <input
                      autoComplete="new-password"
                      id="su-password"
                      type={showSuPw ? "text" : "password"}
                      placeholder="Min. 8 characters"
                      value={suPass}
                      onChange={(e) => {
                        setSuPass(e.target.value);
                        updateStrength(e.target.value);
                      }}
                      disabled={signupLoading}
                    />
                    <button
                      className="icon-right"
                      type="button"
                      onClick={() => setShowSuPw((v) => !v)}
                      disabled={signupLoading}
                    >
                      {showSuPw ? "🙈" : "👁"}
                    </button>
                  </div>
                  <span className="field-error" id="err-su-pass">
                    {signupFields.pass.msg}
                  </span>

                  <div className={`strength-bar ${strength.show ? "show" : ""}`} id="strength-bar">
                    <div className="strength-track">
                      <div
                        className="strength-fill"
                        id="strength-fill"
                        style={{ width: strength.width, background: strength.bg }}
                      ></div>
                    </div>
                    <div className="strength-label" id="strength-label">
                      {strength.label}
                    </div>
                  </div>
                </div>

                {/* Confirm password */}
                <div className={`field ${signupFields.confirm.invalid ? "invalid" : ""}`} id="f-su-confirm">
                  <label htmlFor="su-confirm">Confirm Password</label>
                  <div className="input-wrap">
                    <span className="icon">🔒</span>
                    <input
                      autoComplete="new-password"
                      id="su-confirm"
                      type={showSuConfirmPw ? "text" : "password"}
                      placeholder="Repeat your password"
                      value={suConfirm}
                      onChange={(e) => setSuConfirm(e.target.value)}
                      disabled={signupLoading}
                    />
                    <button
                      className="icon-right"
                      type="button"
                      onClick={() => setShowSuConfirmPw((v) => !v)}
                      disabled={signupLoading}
                    >
                      {showSuConfirmPw ? "🙈" : "👁"}
                    </button>
                  </div>
                  <span className="field-error" id="err-su-confirm">
                    {signupFields.confirm.msg}
                  </span>
                </div>

                <button
                  className={`submit-btn ${signupLoading ? "loading" : ""}`}
                  id="signup-btn"
                  type="submit"
                  disabled={signupLoading}
                >
                  <span className="btn-text">Create Account</span>
                  <div className="spinner"></div>
                </button>
              </form>

              <div className="switch-text">
                Already have an account?{" "}
                <button type="button" onClick={() => switchTab("login")}>
                  Sign in
                </button>
              </div>
            </div>
          )}

          {/* SIGNUP SUCCESS */}
          {tab === "signup" && signupSuccess && (
            <div className="success-screen show" id="signup-success">
              <div className="success-circle">🎉</div>
              <h2>Account created!</h2>
              <p>Welcome to PlannerHub! Taking you to the sign in page…</p>
              <button className="submit-btn" type="button" onClick={resetSignup}>
                Sign In →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
