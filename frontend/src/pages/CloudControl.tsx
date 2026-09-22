import { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, AlertTriangle, CheckCircle, CloudCog, Copy, Download, GitBranch, Play, RefreshCw, ShieldCheck, Terminal } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

type CloudStatus = {
  status: string;
  environment: string;
  active_containers: number;
  infrastructure: { vpc: string; subnet: string; terraform_state: string };
  ai_auditor: string;
};

type Finding = { severity: string; title: string; recommendation: string };

export default function CloudControl() {
  const [cloudStatus, setCloudStatus] = useState<CloudStatus | null>(null);
  const [terraform, setTerraform] = useState('');
  const [loading, setLoading] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [logs, setLogs] = useState<string[]>(['[ready] Cloud Control initialized']);
  const [form, setForm] = useState({ project_name: 'devorbit-prod', region: 'us-east-1', ec2_instances: 2, vpc_cidr: '10.0.0.0/16', s3_buckets: 'artifacts, logs', enable_nat_gateway: false });

  const addLog = (message: string) => setLogs((current) => [`[${new Date().toLocaleTimeString()}] ${message}`, ...current].slice(0, 12));

  const loadStatus = async () => {
    try {
      const response = await axios.get<CloudStatus>(`${API_URL}/api/cloud-status`);
      setCloudStatus(response.data);
      addLog('Cloud status synchronized');
    } catch {
      addLog('Cloud status unavailable; check the FastAPI service');
    }
  };

  useEffect(() => { void loadStatus(); }, []);

  const generate = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/generate-terraform`, { ...form, s3_buckets: form.s3_buckets.split(',').map((bucket) => bucket.trim()).filter(Boolean) });
      setTerraform(response.data.terraform);
      addLog(`Generated ${response.data.filename} for ${form.project_name}`);
    } catch { addLog('Terraform generation failed'); }
    finally { setLoading(false); }
  };

  const runAudit = async () => {
    setAuditLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/ai-audit`, { configuration: { mfa_enabled: false, iam_user_access_keys: 1, s3_public_buckets: 0, security_group_open_ports: true, cloudtrail_enabled: true } });
      setFindings(response.data.findings);
      addLog(`AI audit completed: ${response.data.summary}`);
    } catch { addLog('AI audit failed'); }
    finally { setAuditLoading(false); }
  };

  const triggerDeploy = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/deploy-trigger`, { target: 'github-actions', branch: 'main' });
      addLog(`${response.data.status}: ${response.data.run_id}`);
    } catch { addLog('Deploy simulation failed'); }
  };

  const download = () => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([terraform], { type: 'text/plain' }));
    link.download = 'main.tf';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const copy = async () => { await navigator.clipboard.writeText(terraform); addLog('Terraform copied to clipboard'); };

  return <main className="control-page">
    <header className="control-header">
      <div><p className="eyebrow">DEVORBIT / CLOUD CONTROL</p><h1>Infrastructure command center</h1><p className="muted">Generate, inspect, and stage cloud changes from one operator view.</p></div>
      <button className="icon-button" onClick={() => void loadStatus()} title="Refresh cloud status"><RefreshCw size={17} /></button>
    </header>

    <section className="metric-grid">
      {[{ label: 'Cloud status', value: cloudStatus?.status || 'Checking', icon: Activity }, { label: 'Active containers', value: cloudStatus?.active_containers ?? '--', icon: CloudCog }, { label: 'Terraform state', value: cloudStatus?.infrastructure.terraform_state || '--', icon: CheckCircle }, { label: 'Auditor', value: cloudStatus?.ai_auditor || '--', icon: ShieldCheck }].map(({ label, value, icon: Icon }) => <article className="metric" key={label}><Icon size={17} /><span>{label}</span><strong>{value}</strong></article>)}
    </section>

    <section className="control-grid">
      <div className="panel requirements-panel">
        <div className="panel-heading"><div><p className="eyebrow">01 / BLUEPRINT</p><h2>Terraform generator</h2></div><GitBranch size={20} /></div>
        <div className="form-grid">
          <label>Project name<input value={form.project_name} onChange={(event) => setForm({ ...form, project_name: event.target.value })} /></label>
          <label>AWS region<select value={form.region} onChange={(event) => setForm({ ...form, region: event.target.value })}><option>us-east-1</option><option>us-west-2</option><option>eu-west-1</option></select></label>
          <label>EC2 instances<input type="number" min="1" max="20" value={form.ec2_instances} onChange={(event) => setForm({ ...form, ec2_instances: Number(event.target.value) })} /></label>
          <label>VPC CIDR<input value={form.vpc_cidr} onChange={(event) => setForm({ ...form, vpc_cidr: event.target.value })} /></label>
        </div>
        <label>S3 buckets<input value={form.s3_buckets} onChange={(event) => setForm({ ...form, s3_buckets: event.target.value })} /></label>
        <label className="toggle-label"><input type="checkbox" checked={form.enable_nat_gateway} onChange={(event) => setForm({ ...form, enable_nat_gateway: event.target.checked })} /> Include NAT gateway planning note</label>
        <button className="primary-button" onClick={() => void generate()} disabled={loading}><Play size={16} />{loading ? 'Generating...' : 'Generate Terraform'}</button>
      </div>

      <div className="panel code-panel"><div className="panel-heading"><div><p className="eyebrow">OUTPUT / MAIN.TF</p><h2>Plan preview</h2></div><div className="button-row"><button className="icon-button" onClick={() => void copy()} disabled={!terraform} title="Copy Terraform"><Copy size={16} /></button><button className="icon-button" onClick={download} disabled={!terraform} title="Download Terraform"><Download size={16} /></button></div></div><pre>{terraform || '# Your generated Terraform plan will appear here\n# Review it before running terraform apply.'}</pre></div>
    </section>

    <section className="lower-grid">
      <div className="panel audit-panel"><div className="panel-heading"><div><p className="eyebrow">02 / GUARDRAILS</p><h2>AI security audit</h2></div><ShieldCheck size={20} /></div><p className="muted">Run a simulated review against representative IAM, storage, and network controls.</p><button className="secondary-button" onClick={() => void runAudit()} disabled={auditLoading}><ShieldCheck size={16} />{auditLoading ? 'Auditing...' : 'Run security audit'}</button>{findings.length > 0 && <div className="finding-list">{findings.map((finding) => <div className="finding" key={finding.title}><AlertTriangle size={15} /><div><strong>{finding.title}</strong><p>{finding.recommendation}</p></div><span className={`severity ${finding.severity}`}>{finding.severity}</span></div>)}</div>}</div>
      <div className="panel log-panel"><div className="panel-heading"><div><p className="eyebrow">03 / OPERATIONS</p><h2>Activity console</h2></div><Terminal size={20} /></div><div className="console">{logs.map((log, index) => <div key={`${log}-${index}`}><span className="console-marker">›</span>{log}</div>)}</div><button className="secondary-button" onClick={() => void triggerDeploy()}><Play size={16} />Queue deploy simulation</button></div>
    </section>
  </main>;
}