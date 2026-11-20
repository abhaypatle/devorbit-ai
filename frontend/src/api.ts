import type {
  AgentRun,
  Approval,
  Document,
  Invoice,
  Metrics,
  Order,
  RAGResult,
  Subscription,
  TokenResponse,
  User,
} from "./types";

const API = "/api/v1";
const TOKEN_KEY = "devorbit_access_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function saveSession(token: string, user: User): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem("devorbit_user", JSON.stringify(user));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem("devorbit_user");
}

export function getSavedUser(): User | null {
  const raw = localStorage.getItem("devorbit_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    clearSession();
    return null;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown } | null;
    const message = typeof body?.detail === "string"
      ? body.detail
      : body?.detail
        ? JSON.stringify(body.detail)
        : `${response.status} ${response.statusText}`;
    if (response.status === 401) clearSession();
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  login: (payload: { organization_slug: string; email: string; password: string }) =>
    request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  register: (payload: {
    organization_name: string;
    organization_slug: string;
    full_name: string;
    email: string;
    password: string;
  }) => request<TokenResponse>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request<User>("/auth/me"),
  orders: () => request<Order[]>("/orders"),
  subscriptions: () => request<Subscription[]>("/subscriptions"),
  approvals: () => request<Approval[]>("/approvals"),
  invoices: () => request<Invoice[]>("/invoices"),
  metrics: (projectId: string) => request<Metrics>(`/projects/${projectId}/metrics`),
  documents: (projectId: string) => request<Document[]>(`/projects/${projectId}/documents`),
  uploadDocument: (projectId: string, file: File, approved: boolean) => {
    const form = new FormData();
    form.set("file", file);
    if (approved) form.set("approved", "true");
    return request<Document>(`/projects/${projectId}/documents`, { method: "POST", body: form });
  },
  query: (projectId: string, query: string) =>
    request<RAGResult>(`/projects/${projectId}/rag/query`, {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
  runAgent: (projectId: string, input_text: string, mode: string, action: string | null) =>
    request<AgentRun>(`/projects/${projectId}/agent/run`, {
      method: "POST",
      body: JSON.stringify({ input_text, mode, action }),
    }),
  resolveApproval: (approval: Approval, decision: "APPROVED" | "REJECTED") =>
    request<Approval>(`/approvals/${approval.id}/resolve`, {
      method: "POST",
      headers: { "Idempotency-Key": approval.idempotency_key },
      body: JSON.stringify({ decision }),
    }),
  runDueBilling: () => request<{ created: number }>("/billing/run-due", { method: "POST" }),
  downloadInvoice: async (invoiceId: string, invoiceNumber: string) => {
    const token = getToken();
    const response = await fetch(`${API}/invoices/${invoiceId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) throw new Error("Invoice download failed");
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${invoiceNumber}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
  },
};
