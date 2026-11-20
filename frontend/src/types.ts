export type Role = "admin" | "engineer" | "client";
export type User = {
  id: string;
  org_id: string;
  client_id: string | null;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
};

export type Order = {
  id: string;
  project_key: string;
  name: string;
  description: string | null;
  status: string;
  budget: string;
  currency: string;
  client_id: string;
};
export type Subscription = {
  id: string;
  project_id: string;
  name: string;
  amount: string;
  currency: string;
  interval: string;
  status: string;
};
export type Approval = {
  id: string;
  project_id: string;
  action: string;
  status: string;
  idempotency_key: string;
  action_payload: Record<string, unknown>;
  created_at: string;
};
export type Citation = {
  doc_id: string;
  doc_title: string;
  chunk_index: number;
  snippet: string;
  section: string | null;
  score: number;
};
export type Document = {
  id: string;
  project_id: string;
  title: string;
  filename: string;
  is_approved: boolean;
  status: string;
  created_at: string;
  download_reference: string;
};
export type Invoice = {
  id: string;
  invoice_number: string;
  project_id: string;
  status: string;
  amount_cents: number;
  currency: string;
  due_date: string;
  pdf_storage_key: string | null;
};
export type Metrics = {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_llm_cost_usd: number;
  average_latency_ms: number;
  p95_latency_ms: number;
  contract_budget_cents: number;
  issued_revenue_cents: number;
  paid_revenue_cents: number;
  active_subscription_mrr_cents: number;
  estimated_margin_cents: number;
  estimated_margin_percent: number | null;
};
export type AgentRun = {
  status: string;
  mode: string;
  scope_decision: string | null;
  risk_score: number | null;
  output_text: string | null;
  generated_srs: string | null;
  milestones: { name: string; sequence: string }[] | null;
  citations: Citation[];
  approval_id: string | null;
};
export type RAGResult = {
  status: string;
  answer: string;
  citations: Citation[];
};
export type TokenResponse = { access_token: string; user: User };
