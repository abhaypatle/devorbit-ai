import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Bot,
  BriefcaseBusiness,
  Check,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  FileText,
  FolderKanban,
  LogOut,
  MessageSquareText,
  Plus,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
  Zap,
} from "lucide-react";
import { api, clearSession, getSavedUser, saveSession } from "./api";
import type {
  AgentRun,
  Approval,
  Citation,
  Document as ProjectDocument,
  Invoice,
  Metrics,
  Order,
  RAGResult,
  Role,
  Subscription,
  User,
} from "./types";

type Tab = "overview" | "workspace" | "billing";
type Notice = { kind: "success" | "error"; message: string } | null;

const money = (amount: number, currency = "USD", cents = false) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency }).format(
    cents ? amount / 100 : amount,
  );
const dateLabel = (value: string) =>
  new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value));
const isStaff = (role: Role) => role === "admin" || role === "engineer";

export default function App() {
  const [user, setUser] = useState<User | null>(getSavedUser());
  const [tab, setTab] = useState<Tab>("overview");
  const [orders, setOrders] = useState<Order[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [ragResult, setRagResult] = useState<RAGResult | null>(null);
  const [agentResult, setAgentResult] = useState<AgentRun | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const [busy, setBusy] = useState(false);

  const selectedOrder = useMemo(
    () => orders.find((order) => order.id === selectedProject) ?? null,
    [orders, selectedProject],
  );

  const refresh = useCallback(async (activeUser: User) => {
    const [orderRows, subscriptionRows, invoiceRows] = await Promise.all([
      api.orders(),
      api.subscriptions(),
      api.invoices(),
    ]);
    setOrders(orderRows);
    setSubscriptions(subscriptionRows);
    setInvoices(invoiceRows);
    if (isStaff(activeUser.role)) setApprovals(await api.approvals());
    else setApprovals([]);
    setSelectedProject((current) =>
      orderRows.some((order) => order.id === current) ? current : orderRows[0]?.id ?? "",
    );
  }, []);

  useEffect(() => {
    if (!user) return;
    let active = true;
    void api.me().then(async (identity) => {
      if (!active) return;
      setUser(identity);
      saveSession(localStorage.getItem("devorbit_access_token") ?? "", identity);
      await refresh(identity);
    }).catch((error: unknown) => {
      if (!active) return;
      setNotice({ kind: "error", message: error instanceof Error ? error.message : "Session expired" });
      setUser(null);
    });
    return () => { active = false; };
  }, [user?.id, refresh]);

  useEffect(() => {
    if (!user || !isStaff(user.role) || !selectedProject) {
      setMetrics(null);
      return;
    }
    let active = true;
    void api.metrics(selectedProject).then((value) => {
      if (active) setMetrics(value);
    }).catch((error: unknown) => {
      if (active) setNotice({ kind: "error", message: error instanceof Error ? error.message : "Metrics unavailable" });
    });
    return () => { active = false; };
  }, [user, selectedProject]);

  useEffect(() => {
    if (!user || !selectedProject) {
      setDocuments([]);
      return;
    }
    let active = true;
    void api.documents(selectedProject).then((rows) => {
      if (active) setDocuments(rows);
    }).catch((error: unknown) => {
      if (active) setNotice({ kind: "error", message: error instanceof Error ? error.message : "Documents unavailable" });
    });
    return () => { active = false; };
  }, [user, selectedProject]);

  async function handleLogin(token: string, identity: User): Promise<void> {
    saveSession(token, identity);
    setUser(identity);
    setNotice({ kind: "success", message: `Welcome back, ${identity.full_name}.` });
  }

  function signOut(): void {
    clearSession();
    setUser(null);
    setOrders([]);
    setSubscriptions([]);
    setApprovals([]);
    setInvoices([]);
    setNotice(null);
  }

  async function perform<T>(operation: () => Promise<T>, success?: (value: T) => string): Promise<T | undefined> {
    setBusy(true);
    setNotice(null);
    try {
      const value = await operation();
      if (success) setNotice({ kind: "success", message: success(value) });
      if (user) await refresh(user);
      return value;
    } catch (error) {
      setNotice({ kind: "error", message: error instanceof Error ? error.message : "Request failed" });
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return <LoginScreen notice={notice} onLogin={handleLogin} />;
  }

  const firstName = user.full_name.split(" ")[0] || user.full_name;
  const navItems: { key: Tab; label: string; icon: typeof FolderKanban }[] = [
    { key: "overview", label: "Command center", icon: FolderKanban },
    { key: "workspace", label: "Project workspace", icon: BriefcaseBusiness },
    { key: "billing", label: "Billing & invoices", icon: CircleDollarSign },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="DevOrbit home">
          <span className="brand-mark"><Zap size={19} fill="currentColor" /></span>
          <span>devorbit<span className="brand-ai">.ai</span></span>
        </a>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="nav-list" aria-label="Main navigation">
          {navItems.map(({ key, label, icon: Icon }) => (
            <button key={key} className={`nav-item ${tab === key ? "active" : ""}`} onClick={() => setTab(key)}>
              <Icon size={18} /><span>{label}</span>
              {key === "overview" && approvals.length > 0 && isStaff(user.role) &&
                <span className="nav-count">{approvals.length}</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="secure-note"><ShieldCheck size={16} /><span>Tenant isolated<br /><small>Workspace data is private</small></span></div>
          <button className="profile" onClick={signOut}>
            <span className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</span>
            <span className="profile-copy"><strong>{user.full_name}</strong><small>{user.role}</small></span>
            <LogOut size={16} className="logout-icon" />
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><ArrowRight size={14} /><strong>{navItems.find((item) => item.key === tab)?.label}</strong></div>
          <div className="topbar-right">
            <span className="live-indicator"><i /> All systems operational</span>
            <span className="role-pill">{user.role}</span>
          </div>
        </header>
        <div className="page-content">
          {notice && <div className={`notice ${notice.kind}`} role="status">
            {notice.kind === "success" ? <CheckCircle2 size={17} /> : <X size={17} />}
            <span>{notice.message}</span><button aria-label="Dismiss" onClick={() => setNotice(null)}><X size={15} /></button>
          </div>}

          {tab === "overview" && (
            <Overview
              user={user}
              firstName={firstName}
              orders={orders}
              subscriptions={subscriptions}
              approvals={approvals}
              metrics={metrics}
              selectedProject={selectedProject}
              setSelectedProject={setSelectedProject}
              busy={busy}
              onRunBilling={() => void perform(api.runDueBilling, (result) => `Billing run complete — ${result.created} invoice(s) created.`)}
              onResolve={(approval, decision) => void perform(
                () => api.resolveApproval(approval, decision),
                () => `Approval ${decision.toLowerCase()}.`,
              )}
              onOpenWorkspace={() => setTab("workspace")}
            />
          )}
          {tab === "workspace" && (
            <Workspace
              user={user}
              orders={orders}
              selectedProject={selectedProject}
              selectedOrder={selectedOrder}
              setSelectedProject={setSelectedProject}
              documents={documents}
              setDocuments={setDocuments}
              ragResult={ragResult}
              setRagResult={setRagResult}
              agentResult={agentResult}
              setAgentResult={setAgentResult}
              busy={busy}
              perform={perform}
            />
          )}
          {tab === "billing" && (
            <Billing
              invoices={invoices}
              subscriptions={subscriptions}
              orders={orders}
              user={user}
              busy={busy}
              onRunBilling={() => void perform(api.runDueBilling, (result) => `Billing run complete — ${result.created} invoice(s) created.`)}
              onDownload={(invoice) => void perform(
                () => api.downloadInvoice(invoice.id, invoice.invoice_number),
                () => `Downloading ${invoice.invoice_number}.pdf`,
              )}
            />
          )}
        </div>
      </main>
    </div>
  );
}

function LoginScreen({ notice, onLogin }: { notice: Notice; onLogin: (token: string, user: User) => Promise<void> }) {
  const [registering, setRegistering] = useState(false);
  const [organizationName, setOrganizationName] = useState("");
  const [organizationSlug, setOrganizationSlug] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setLoading(true);
    setLocalError("");
    try {
      const result = registering
        ? await api.register({
          organization_name: organizationName,
          organization_slug: organizationSlug.toLowerCase().trim(),
          full_name: fullName,
          email,
          password,
        })
        : await api.login({ organization_slug: organizationSlug.toLowerCase().trim(), email, password });
      await onLogin(result.access_token, result.user);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Could not authenticate");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-orbit orbit-one" /><div className="login-orbit orbit-two" />
      <header className="login-brand brand"><span className="brand-mark"><Zap size={19} fill="currentColor" /></span><span>devorbit<span className="brand-ai">.ai</span></span></header>
      <section className="login-card">
        <div className="eyebrow"><Sparkles size={14} /> DELIVERY OPERATING SYSTEM</div>
        <h1>{registering ? "Create your workspace" : "Welcome back"}</h1>
        <p className="muted">{registering ? "Start managing delivery with AI-powered project operations." : "Sign in to your organization's secure workspace."}</p>
        {(localError || (notice?.kind === "error" ? notice.message : "")) &&
          <div className="notice error login-notice">{localError || notice?.message}</div>}
        <form className="login-form" onSubmit={(event) => void submit(event)}>
          {registering && <>
            <label>Organization name<input required minLength={2} value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} placeholder="Acme Studio" /></label>
            <label>Workspace slug<input required minLength={3} value={organizationSlug} onChange={(event) => setOrganizationSlug(event.target.value.replace(/[^a-zA-Z0-9-]/g, ""))} placeholder="acme-studio" /></label>
            <label>Your name<input required value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Alex Morgan" /></label>
          </>}
          {!registering && <label>Workspace slug<input required value={organizationSlug} onChange={(event) => setOrganizationSlug(event.target.value)} placeholder="acme-studio" /></label>}
          <label>Email address<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" /></label>
          <label>Password<input required type="password" minLength={registering ? 12 : 1} autoComplete={registering ? "new-password" : "current-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••••••" /></label>
          <button className="button primary full-width" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : <>{registering ? "Create workspace" : "Sign in"} <ArrowRight size={16} /></>}
          </button>
        </form>
        <div className="login-switch">{registering ? "Already have a workspace?" : "New to DevOrbit?"}
          <button onClick={() => { setRegistering(!registering); setLocalError(""); }}> {registering ? "Sign in" : "Create one"}</button>
        </div>
        <div className="login-foot"><ShieldCheck size={14} /> Secure, organization-scoped access</div>
      </section>
    </div>
  );
}

function Overview(props: {
  user: User; firstName: string; orders: Order[]; subscriptions: Subscription[];
  approvals: Approval[]; metrics: Metrics | null; selectedProject: string;
  setSelectedProject: (id: string) => void; busy: boolean;
  onRunBilling: () => void; onResolve: (approval: Approval, decision: "APPROVED" | "REJECTED") => void;
  onOpenWorkspace: () => void;
}) {
  const project = props.orders.find((order) => order.id === props.selectedProject);
  const isAgency = isStaff(props.user.role);
  return (
    <>
      <div className="page-heading">
        <div><div className="eyebrow">OVERVIEW <span className="eyebrow-line" /></div><h1>Good to see you, {props.firstName}<span className="heading-dot">.</span></h1>
          <p className="muted">{isAgency ? "Your delivery operations, at a glance." : "Your projects and delivery progress, all in one place."}</p></div>
        <button className="button primary" onClick={props.onOpenWorkspace}><Plus size={16} /> Open workspace</button>
      </div>
      <section className="stats-grid">
        <StatCard label={isAgency ? "Active projects" : "Your projects"} value={String(props.orders.filter((order) => order.status === "active").length).padStart(2, "0")} caption={`${props.orders.length} total orders`} icon={FolderKanban} accent="blue" />
        <StatCard label="Subscriptions" value={String(props.subscriptions.filter((item) => item.status === "active").length).padStart(2, "0")} caption="Active recurring services" icon={RefreshCw} accent="cyan" />
        <StatCard label={isAgency ? "Pending approvals" : "Invoices"} value={isAgency ? String(props.approvals.length).padStart(2, "0") : String(props.orders.length).padStart(2, "0")} caption={isAgency ? "Waiting for your review" : "Project billing and status"} icon={isAgency ? ShieldCheck : FileText} accent="amber" />
        <StatCard label="LLM usage cost" value={props.metrics ? money(props.metrics.estimated_llm_cost_usd) : "—"} caption={props.metrics ? `${props.metrics.total_tokens.toLocaleString()} tokens · ${props.metrics.average_latency_ms} ms avg` : "Select a project to view metrics"} icon={Activity} accent="green" />
      </section>
      {isAgency && <section className="section-grid">
        <div className="panel approvals-panel">
          <div className="panel-heading"><div><div className="eyebrow">HUMAN IN THE LOOP</div><h2>Approval queue <span className="count-bubble">{props.approvals.length}</span></h2></div><span className="status-dot amber-dot">Needs review</span></div>
          {props.approvals.length === 0 ? <EmptyState title="Queue is clear" text="Approval requests will appear here when an agent or billing action needs review." icon={CheckCircle2} /> :
            <div className="approval-list">{props.approvals.slice(0, 5).map((approval) => (
              <div className="approval-row" key={approval.id}>
                <div className="approval-icon"><ShieldCheck size={17} /></div>
                <div className="approval-info"><strong>{approval.action.replaceAll("_", " ")}</strong><span>{props.orders.find((order) => order.id === approval.project_id)?.name ?? "Project"} · {dateLabel(approval.created_at)}</span>
                  {typeof approval.action_payload.amount_cents === "number" && <span className="approval-value">{money(approval.action_payload.amount_cents, String(approval.action_payload.currency ?? "USD"), true)}</span>}
                </div>
                <div className="approval-actions">
                  <button className="icon-action reject" aria-label="Reject approval" disabled={props.busy} onClick={() => props.onResolve(approval, "REJECTED")}><X size={16} /></button>
                  <button className="icon-action accept" aria-label="Approve request" disabled={props.busy} onClick={() => props.onResolve(approval, "APPROVED")}><Check size={16} /></button>
                </div>
              </div>
            ))}</div>}
        </div>
        <div className="panel metrics-panel">
          <div className="panel-heading"><div><div className="eyebrow">FINOPS TELEMETRY</div><h2>Project margin</h2></div><Activity className="panel-icon" size={18} /></div>
          <label className="select-label">Project
            <select value={props.selectedProject} onChange={(event) => props.setSelectedProject(event.target.value)}>
              {props.orders.map((order) => <option key={order.id} value={order.id}>{order.name}</option>)}
              {props.orders.length === 0 && <option value="">No projects yet</option>}
            </select>
          </label>
          {props.metrics ? <>
            <div className="margin-value">{props.metrics.estimated_margin_percent?.toFixed(1) ?? "—"}<span>%</span></div>
            <div className="margin-bar"><i style={{ width: `${Math.min(100, Math.max(0, props.metrics.estimated_margin_percent ?? 0))}%` }} /></div>
            <div className="metric-lines"><span>Contract budget <strong>{money(props.metrics.contract_budget_cents, project?.currency ?? "USD", true)}</strong></span>
              <span>Paid invoices <strong>{money(props.metrics.paid_revenue_cents, project?.currency ?? "USD", true)}</strong></span>
              <span>Subscription MRR <strong>{money(props.metrics.active_subscription_mrr_cents, project?.currency ?? "USD", true)}</strong></span>
              <span>LLM p95 latency <strong>{props.metrics.p95_latency_ms} ms</strong></span></div>
          </> : <EmptyState title="No telemetry yet" text="Choose a project with recorded usage to see its cost and margin." icon={Activity} />}
        </div>
      </section>}
      <section className="panel orders-panel">
        <div className="panel-heading"><div><div className="eyebrow">DELIVERY PIPELINE</div><h2>{isAgency ? "Project orders" : "Your projects"}</h2></div><button className="text-button" onClick={props.onOpenWorkspace}>View project workspace <ArrowRight size={15} /></button></div>
        {props.orders.length === 0 ? <EmptyState title="No project orders yet" text="Projects created by your organization will show up here." icon={FolderKanban} /> :
          <div className="table-scroll"><table><thead><tr><th>PROJECT</th><th>STATUS</th><th>CONTRACT</th><th>SUBSCRIPTION</th><th>DELIVERY</th></tr></thead>
            <tbody>{props.orders.map((order) => {
              const services = props.subscriptions.filter((item) => item.project_id === order.id && item.status === "active");
              return <tr key={order.id} onClick={() => props.setSelectedProject(order.id)} className={props.selectedProject === order.id ? "selected-row" : ""}>
                <td><div className="project-cell"><span className="project-mark">{order.project_key.slice(0, 1).toUpperCase()}</span><span><strong>{order.name}</strong><small>{order.project_key}</small></span></div></td>
                <td><StatusBadge status={order.status} /></td>
                <td className="table-money">{money(Number(order.budget), order.currency)}</td>
                <td>{services.length ? <span className="subscription-label"><i />{services.length} active</span> : <span className="muted">—</span>}</td>
                <td><button className="row-arrow" aria-label={`Open ${order.name}`} onClick={(event) => { event.stopPropagation(); props.setSelectedProject(order.id); props.onOpenWorkspace(); }}><ArrowRight size={17} /></button></td>
              </tr>;
            })}</tbody></table></div>}
      </section>
    </>
  );
}

function Workspace(props: {
  user: User; orders: Order[]; selectedProject: string; selectedOrder: Order | null;
  setSelectedProject: (id: string) => void; documents: ProjectDocument[];
  setDocuments: (value: ProjectDocument[]) => void; ragResult: RAGResult | null;
  setRagResult: (value: RAGResult | null) => void; agentResult: AgentRun | null;
  setAgentResult: (value: AgentRun | null) => void; busy: boolean;
  perform: <T>(operation: () => Promise<T>, success?: (value: T) => string) => Promise<T | undefined>;
}) {
  const [query, setQuery] = useState("");
  const [agentInput, setAgentInput] = useState("");
  const [agentMode, setAgentMode] = useState("scope");
  const [agentAction, setAgentAction] = useState("");
  const [approved, setApproved] = useState(false);
  async function upload(file: File | undefined): Promise<void> {
    if (!file || !props.selectedProject) return;
    const result = await props.perform(
      () => api.uploadDocument(props.selectedProject, file, approved),
      (document) => `Indexed ${document.filename} and added it to this project's RAG library.`,
    );
    if (result) props.setDocuments([result, ...props.documents.filter((item) => item.id !== result.id)]);
  }
  return <>
    <div className="page-heading">
      <div><div className="eyebrow">PROJECT OPERATIONS <span className="eyebrow-line" /></div><h1>Project workspace<span className="heading-dot">.</span></h1><p className="muted">Documents, AI workflows and scoped project intelligence.</p></div>
      <label className="project-select"><FolderKanban size={16} /><select value={props.selectedProject} onChange={(event) => props.setSelectedProject(event.target.value)}>
        {props.orders.map((order) => <option key={order.id} value={order.id}>{order.name}</option>)}
        {props.orders.length === 0 && <option value="">No projects available</option>}
      </select></label>
    </div>
    {!props.selectedOrder ? <div className="panel"><EmptyState title="No project selected" text="A project order must be available to access documents and AI workflows." icon={FolderKanban} /></div> : <>
      <div className="workspace-project-banner"><div className="project-mark large">{props.selectedOrder.project_key.slice(0, 1).toUpperCase()}</div><div><span className="eyebrow">{props.selectedOrder.project_key}</span><h2>{props.selectedOrder.name}</h2><p>{props.selectedOrder.description || "Project documentation and scoped AI workbench"}</p></div><StatusBadge status={props.selectedOrder.status} /></div>
      <div className="workspace-grid">
        <section className="panel document-panel">
          <div className="panel-heading"><div><div className="eyebrow">KNOWLEDGE BASE</div><h2>Project documents</h2></div><span className="count-bubble">{props.documents.length}</span></div>
          <label className="upload-zone">
            <input type="file" accept=".txt,.md,.markdown,.json,.pdf,text/plain,text/markdown,application/json,application/pdf" onChange={(event) => { void upload(event.target.files?.[0]); event.currentTarget.value = ""; }} />
            <span className="upload-icon"><Upload size={19} /></span><strong>Drop a brief or browse files</strong><small>PDF, Markdown, JSON or text · up to 10 MB</small>
          </label>
          {isStaff(props.user.role) && <label className="checkbox-line"><input type="checkbox" checked={approved} onChange={(event) => setApproved(event.target.checked)} /> Mark document as approved for scope analysis</label>}
          <div className="document-list">{props.documents.map((doc) => <div className="document-row" key={doc.id}>
            <span className="file-icon"><FileText size={17} /></span><span className="document-copy"><strong>{doc.title}</strong><small>{doc.filename} · {dateLabel(doc.created_at)}</small></span>
            {doc.is_approved && <span className="approved-tag"><Check size={12} /> Approved</span>}
            <span className="indexed-dot" title={doc.status} />
          </div>)}
            {props.documents.length === 0 && <EmptyState title="Your knowledge base is empty" text="Upload project briefs, SRS documents or runbooks to make them searchable." icon={FileText} />}
          </div>
        </section>
        <section className="panel ai-panel">
          <div className="panel-heading"><div><div className="eyebrow">PROJECT-SCOPED RAG</div><h2>Ask your documents</h2></div><span className="ai-chip"><Sparkles size={13} /> AI</span></div>
          <form onSubmit={(event) => { event.preventDefault(); if (query.trim()) void props.perform(() => api.query(props.selectedProject, query), (result) => result.status === "COMPLETED" ? "Project answer generated with scoped citations." : "Query blocked by safety guardrail.").then((result) => { if (result) props.setRagResult(result); }); }}>
            <label className="sr-only" htmlFor="rag-query">Ask a question about this project</label>
            <textarea id="rag-query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask a question about this project's docs..." rows={3} />
            <button className="button primary" type="submit" disabled={props.busy || !query.trim()}><MessageSquareText size={15} /> Ask project docs</button>
          </form>
          {props.ragResult && <div className="answer-block"><div className="answer-label"><Sparkles size={14} /> ANSWER</div><p>{props.ragResult.answer}</p>
            <CitationList citations={props.ragResult.citations} /></div>}
          <div className="agent-divider" />
          <div className="panel-heading compact-heading"><div><div className="eyebrow">LANGGRAPH WORKFLOW</div><h2>Run a project agent</h2></div><Bot size={19} className="panel-icon" /></div>
          <form onSubmit={(event) => { event.preventDefault(); if (agentInput.trim()) void props.perform(() => api.runAgent(props.selectedProject, agentInput, agentMode, agentAction || null), (result) => `Agent run ${result.status.toLowerCase().replaceAll("_", " ")}.`).then((result) => { if (result) props.setAgentResult(result); }); }}>
            <div className="form-row"><label>Workflow<select value={agentMode} onChange={(event) => setAgentMode(event.target.value)}><option value="scope">Scope check</option><option value="srs">SRS architect</option></select></label>
              <label>Action gate<select value={agentAction} onChange={(event) => setAgentAction(event.target.value)}><option value="">No external action</option><option value="change_request_quote">Change request quote</option><option value="invoice_dispatch">Invoice dispatch</option></select></label></div>
            <textarea value={agentInput} onChange={(event) => setAgentInput(event.target.value)} placeholder={agentMode === "srs" ? "Describe the project brief to turn into a structured SRS..." : "Describe a new client request to compare against approved scope..."} rows={3} />
            <button className="button secondary" type="submit" disabled={props.busy || !agentInput.trim()}><Zap size={15} /> Run workflow</button>
          </form>
          {props.agentResult && <div className="agent-result"><div className="agent-result-head"><span className="answer-label"><Bot size={14} /> WORKFLOW RESULT</span><StatusBadge status={props.agentResult.status} /></div>
            {props.agentResult.scope_decision && <p className="scope-decision">Decision: <strong>{props.agentResult.scope_decision}</strong>{props.agentResult.risk_score !== null && <span> · Risk score {props.agentResult.risk_score}/100</span>}</p>}
            <p>{props.agentResult.output_text || props.agentResult.generated_srs || "Workflow completed."}</p>
            {props.agentResult.approval_id && <div className="pending-inline"><Clock3 size={14} /> Waiting for staff approval · {props.agentResult.approval_id.slice(0, 8)}</div>}
            {props.agentResult.milestones && <ul className="milestone-list">{props.agentResult.milestones.map((item) => <li key={`${item.sequence}-${item.name}`}><span>{item.sequence}</span>{item.name}</li>)}</ul>}
            <CitationList citations={props.agentResult.citations} />
          </div>}
        </section>
      </div>
    </>}
  </>;
}

function Billing(props: {
  invoices: Invoice[]; subscriptions: Subscription[]; orders: Order[]; user: User; busy: boolean;
  onRunBilling: () => void; onDownload: (invoice: Invoice) => void;
}) {
  const canRunBilling = props.user.role === "admin";
  return <>
    <div className="page-heading">
      <div><div className="eyebrow">REVENUE OPERATIONS <span className="eyebrow-line" /></div><h1>Billing & invoices<span className="heading-dot">.</span></h1><p className="muted">Subscription cycles, invoice status and payment records.</p></div>
      {canRunBilling && <button className="button primary" onClick={props.onRunBilling} disabled={props.busy}><RefreshCw size={15} /> Run due billing</button>}
    </div>
    <section className="stats-grid billing-stats">
      <StatCard label="Invoices" value={String(props.invoices.length).padStart(2, "0")} caption="Visible to your account" icon={FileText} accent="blue" />
      <StatCard label="Outstanding" value={String(props.invoices.filter((invoice) => ["ISSUED", "PENDING_APPROVAL"].includes(invoice.status.toUpperCase())).length).padStart(2, "0")} caption="Issued or awaiting approval" icon={Clock3} accent="amber" />
      <StatCard label="Paid" value={String(props.invoices.filter((invoice) => invoice.status.toUpperCase() === "PAID").length).padStart(2, "0")} caption="Successfully settled" icon={CheckCircle2} accent="green" />
      <StatCard label="Subscriptions" value={String(props.subscriptions.filter((item) => item.status === "active").length).padStart(2, "0")} caption="Active billing schedules" icon={RefreshCw} accent="cyan" />
    </section>
    <section className="panel orders-panel invoice-panel">
      <div className="panel-heading"><div><div className="eyebrow">BILLING HISTORY</div><h2>Invoices</h2></div><span className="count-bubble">{props.invoices.length}</span></div>
      {props.invoices.length === 0 ? <EmptyState title="No invoices yet" text={canRunBilling ? "Run due billing when an active subscription reaches its billing date." : "Invoices for your projects will appear here."} icon={FileText} /> :
        <div className="table-scroll"><table><thead><tr><th>INVOICE</th><th>PROJECT</th><th>STATUS</th><th>DUE DATE</th><th>AMOUNT</th><th>PDF</th></tr></thead>
          <tbody>{props.invoices.map((invoice) => <tr key={invoice.id}>
            <td><strong className="invoice-number">{invoice.invoice_number}</strong></td>
            <td>{props.orders.find((order) => order.id === invoice.project_id)?.name ?? "Project"}</td>
            <td><StatusBadge status={invoice.status} /></td>
            <td>{dateLabel(invoice.due_date)}</td>
            <td className="table-money">{money(invoice.amount_cents, invoice.currency, true)}</td>
            <td><button className="download-button" disabled={props.busy || !invoice.pdf_storage_key} title={!invoice.pdf_storage_key ? "PDF not available" : "Download PDF"} onClick={() => props.onDownload(invoice)}><ArrowDownToLine size={16} /> PDF</button></td>
          </tr>)}</tbody></table></div>}
    </section>
    <section className="panel orders-panel subscriptions-panel">
      <div className="panel-heading"><div><div className="eyebrow">RECURRING REVENUE</div><h2>Subscriptions</h2></div><span className="count-bubble">{props.subscriptions.length}</span></div>
      {props.subscriptions.length === 0 ? <p className="muted empty-copy">No subscription schedules are linked to your projects.</p> :
        <div className="subscription-grid">{props.subscriptions.map((sub) => <article className="subscription-card" key={sub.id}>
          <span className="subscription-icon"><RefreshCw size={17} /></span><div className="subscription-body"><strong>{sub.name}</strong><span>{props.orders.find((order) => order.id === sub.project_id)?.name ?? "Project"}</span></div>
          <div className="subscription-price"><strong>{money(Number(sub.amount), sub.currency)}</strong><small>/ {sub.interval}</small></div>
          <StatusBadge status={sub.status} />
        </article>)}</div>}
    </section>
  </>;
}

function StatCard({ label, value, caption, icon: Icon, accent }: {
  label: string; value: string; caption: string; icon: typeof FolderKanban;
  accent: "blue" | "cyan" | "amber" | "green";
}) {
  return <article className={`stat-card accent-${accent}`}>
    <div className="stat-top"><span>{label}</span><span className="stat-icon"><Icon size={17} /></span></div>
    <strong className="stat-value">{value}</strong><span className="stat-caption">{caption}</span>
  </article>;
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const tone = ["active", "completed", "paid", "approved", "completed"].includes(normalized) ? "green"
    : ["pending", "pending_approval", "awaiting_approval", "on_hold", "draft"].includes(normalized) ? "amber"
      : ["cancelled", "rejected", "void", "blocked", "failed"].includes(normalized) ? "rose" : "blue";
  return <span className={`status-badge ${tone}`}><i />{status.replaceAll("_", " ")}</span>;
}

function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return <div className="citation-list"><div className="citation-heading"><FileText size={13} /> SOURCES</div>
    {citations.map((citation) => <article className="citation" key={`${citation.doc_id}-${citation.chunk_index}`}>
      <div><strong>{citation.doc_title}</strong><span>{citation.section || "General"} · chunk {citation.chunk_index + 1} · {Math.round(citation.score * 100)}% match</span></div>
      <p>{citation.snippet}</p>
    </article>)}
  </div>;
}

function EmptyState({ title, text, icon: Icon }: { title: string; text: string; icon: typeof FileText }) {
  return <div className="empty-state"><span className="empty-icon"><Icon size={20} /></span><strong>{title}</strong><p>{text}</p></div>;
}
