// Every call goes to the FastAPI backend from Problem 7. The dashboard never
// touches the database or the MCP server directly.
import type { CashResponse, EventsResponse, PaymentRequest, RunStatus, TicketBoard } from "./types";

export const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const TOKEN_KEY = "campus-customs-david-token";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const session = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, init: RequestInit = {}, withAuth = false): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = session.get();
  if (withAuth && token) headers.Authorization = `Bearer ${token}`;
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Can't reach the backend at " + API_URL + ". Is uvicorn running?");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, (body as { detail?: string }).detail ?? `Request failed (${res.status})`);
  return body as T;
}

export const api = {
  tickets: () => request<TicketBoard>("/api/tickets"),
  runTicket: (id: number) => request<{ run_id: string }>(`/api/tickets/${id}/run`, { method: "POST" }),
  currentRun: () => request<RunStatus>("/api/runs/current"),
  events: (ticketId: number, after = -1) =>
    request<EventsResponse>(`/api/events?ticket_id=${ticketId}&after=${after}&limit=500&since_reset=true`),
  cash: () => request<CashResponse>("/api/cash"),
  paymentRequests: (status = "pending") =>
    request<{ requests: PaymentRequest[] }>(`/api/payment-requests?status=${status}`),
  login: (password: string) =>
    request<{ token: string; approver: string; expires_in_minutes: number }>("/api/login", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),
  logout: () => request<{ logged_out: boolean }>("/api/logout", { method: "POST" }, true),
  session: () => request<{ logged_in: boolean; approver?: string; message?: string; password_set?: boolean }>(
    "/api/session", {}, true),
  approve: (id: number, reason: string, acknowledgeRisk = false) =>
    request<{ paid: boolean; amount: number; balance_before: number; balance_after: number }>(
      `/api/payment-requests/${id}/approve`,
      { method: "POST", body: JSON.stringify({ reason, acknowledge_risk: acknowledgeRisk }) }, true),
  decline: (id: number, reason: string) =>
    request<{ declined: boolean }>(`/api/payment-requests/${id}/decline`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }, true),
  reset: () => request<{ reset: boolean }>("/api/reset", { method: "POST" }, true),
};
