const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options?.headers,
  };
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw { status: res.status, ...body };
  }
  return res.json();
}

export async function apiFormPost<T>(path: string, data: Record<string, string>): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
  const body = new URLSearchParams(data);
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body });
  if (!res.ok) {
    const json = await res.json().catch(() => ({}));
    throw { status: res.status, ...json };
  }
  return res.json();
}
