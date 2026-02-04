const API_BASE = "http://127.0.0.1:8000";

async function apiGet(path) {
  const res = await fetch(API_BASE + path);
  return await res.json();
}

async function apiPost(path, bodyObj) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyObj),
  });
  return await res.json();
}
