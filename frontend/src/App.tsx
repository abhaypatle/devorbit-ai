import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { jsPDF } from 'jspdf';
import { Cpu, ShieldCheck, Download, Activity, BookOpen, Rocket, RefreshCw, AlertTriangle, CheckCircle, DollarSign } from 'lucide-react';
import DiagramRenderer from './components/DiagramRenderer';
import CloudControl from './pages/CloudControl';
import EnterpriseDashboard from './pages/EnterpriseDashboard';
import SystemStatus from './pages/SystemStatus';
import HomePage from './pages/Home';
import Auth from './pages/Auth';
import { useTheme } from './context/ThemeContext';

function Navbar() {
  const location = useLocation();
  const { theme, cycleTheme } = useTheme();
  const links = [
    { name: 'Home', path: '/' },
    { name: 'Agent Pipeline', path: '/orchestrator' },
    { name: 'Digital Twin', path: '/digital-twin' },
    { name: 'Core Modules', path: '/modules' },
    { name: 'System Status', path: '/status' },
    { name: 'Cloud Control', path: '/cloud-control' },
    { name: 'Enterprise', path: '/enterprise' },
  ];

  return (
    <nav style={{ background: 'var(--surface-solid)', borderBottom: '1px solid var(--line)', padding: '15px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 50 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Cpu style={{ color: '#00f0ff' }} size={22} />
        <span style={{ fontSize: '20px', fontWeight: '800', color: '#00f0ff' }}>
          DevOrbit AI
        </span>
      </div>
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        {links.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            style={{
              color: location.pathname === link.path ? '#00f0ff' : '#94a3b8',
              textDecoration: 'none',
              fontWeight: '600',
              padding: '6px 14px',
              borderRadius: '6px',
              border: location.pathname === link.path ? '1px solid rgba(0,240,255,0.4)' : '1px solid transparent',
              background: location.pathname === link.path ? 'rgba(0,240,255,0.12)' : 'transparent',
            }}
          >
            {link.name}
          </Link>
        ))}
        <button className="theme-toggle" onClick={cycleTheme} title="Cycle visual theme">{theme === 'dark' ? '◐' : theme === 'light' ? '☼' : '✦'} <span>{theme}</span></button>
        <Link className="nav-auth-link" to="/auth/login">Sign in</Link>
      </div>
    </nav>
  );
}

function Home() {
  return <HomePage />;
  /* return (
    <div style={{ maxWidth: '1000px', margin: '60px auto', textAlign: 'center', padding: '0 20px', color: '#fff' }}>
      <h1 style={{ fontSize: '46px', fontWeight: '800', lineHeight: '1.2', marginBottom: '20px' }}>
        Autonomous Cloud Infrastructure & <br />
        <span style={{ color: '#00f0ff' }}>Project Digital Twin Engine</span>
      </h1>
      <p style={{ color: '#94a3b8', fontSize: '18px', maxWidth: '700px', margin: '0 auto 30px auto' }}>
        Transforms natural language project ideas into deployable AWS infrastructure, skill-based task divisions, live drift tracking, and automated academic/enterprise documentation.
      </p>
      <Link to="/orchestrator" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', background: '#00f0ff', color: '#070a10', padding: '14px 28px', borderRadius: '8px', fontWeight: '800', textDecoration: 'none' }}>
        Launch Agent Workspace <ArrowRight size={18} />
      </Link>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginTop: '60px' }}>
        {[
          { icon: Terminal, title: 'Lead Planner Agent', desc: 'Converts ideas into PRD blueprints and skill-matched team task matrices.' },
          { icon: Server, title: 'Cloud Architect Agent', desc: 'Designs AWS Multi-AZ VPCs, Load Balancers, and RDS PostgreSQL blueprints.' },
          { icon: ShieldCheck, title: 'DevOps IaC Agent', desc: 'Compiles architecture directly into production-ready Terraform (.tf) code.' },
        ].map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} style={{ background: 'rgba(15, 23, 42, 0.85)', border: '1px solid rgba(0,240,255,0.2)', padding: '24px', borderRadius: '12px', textAlign: 'left' }}>
              <Icon style={{ color: '#00f0ff', marginBottom: '12px' }} size={28} />
              <h3 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>{item.title}</h3>
              <p style={{ color: '#94a3b8', margin: 0, fontSize: '14px', lineHeight: '1.5' }}>{item.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  ); */
}

function Orchestrator() {
  const [projectId, setProjectId] = useState('devorbit-prod-01');
  const [prompt, setPrompt] = useState('Design a high-availability AWS architecture for a scalable web application with auto scaling and RDS PostgreSQL.');
  const [cloudProvider, setCloudProvider] = useState<'aws' | 'azure' | 'gcp'>('aws');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [showDiagram, setShowDiagram] = useState(false);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessages([]);
    setShowDiagram(false);

    try {
      const res = await axios.post('http://127.0.0.1:8000/api/v1/orchestrator/run', {
        project_id: projectId,
        prompt: prompt,
        cloud_provider: cloudProvider,
      });

      if (res.data.status === 'success') {
        setMessages(res.data.messages);
        setShowDiagram(true);
      }
    } catch (err) {
      console.error(err);
      alert('Backend Connection Error! Make sure FastAPI is running on http://127.0.0.1:8000');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTerraform = (content: string) => {
    const element = document.createElement('a');
    const file = new Blob([content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = 'main.tf';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

 const mermaidChart = `graph TD
    Users[👤 Users] --> Route53[🌐 Route 53]
    Route53 --> IGW[🚪 Internet Gateway]
    IGW --> ALB[⚖️ Application Load Balancer]
    
    subgraph Multi_AZ_VPC [AWS Multi-AZ VPC]
      subgraph AZ1 [AZ 1: us-east-1a]
        EC2_1[💻 EC2 WebServer 1]
        RDS_1[(🗄️ RDS Standby DB)]
      end
      subgraph AZ2 [AZ 2: us-east-1b]
        EC2_2[💻 EC2 WebServer 2]
        RDS_2[(🗄️ RDS Master DB)]
      end
    end
    
    ALB --> EC2_1
    ALB --> EC2_2
    EC2_1 --> RDS_2
    EC2_2 --> RDS_2
    RDS_2 -. Sync .- RDS_1`;

  return (
    <div style={{ maxWidth: '900px', margin: '40px auto', padding: '0 20px', color: '#fff' }}>
      <div style={{ background: 'rgba(15, 23, 42, 0.85)', border: '1px solid rgba(0,240,255,0.3)', padding: '30px', borderRadius: '16px', marginBottom: '30px' }}>
        <h2 style={{ margin: '0 0 20px 0', color: '#00f0ff', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu /> Multi-Agent Execution Workspace
        </h2>
        <form onSubmit={handleRun} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: '#cbd5e1' }}>Cloud provider</label>
            <select value={cloudProvider} onChange={(e) => setCloudProvider(e.target.value as 'aws' | 'azure' | 'gcp')} style={{ width: '100%', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}>
              <option value="aws">AWS</option><option value="azure">Microsoft Azure</option><option value="gcp">Google Cloud</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: '#cbd5e1' }}>Project ID</label>
            <input
              type="text"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: '#cbd5e1' }}>Architecture Specs & Requirements</label>
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{ padding: '14px', background: loading ? '#64748b' : '#00f0ff', color: '#070a10', border: 'none', borderRadius: '6px', fontWeight: '800', cursor: loading ? 'not-allowed' : 'pointer' }}
          >
            {loading ? 'Agents Analyzing & Compiling...' : 'Execute Multi-Agent Graph'}
          </button>
        </form>
      </div>

 {/* Force Re-render using prompt/chart string as key */}
{showDiagram && (
  <DiagramRenderer 
    key={mermaidChart + prompt} 
    chart={mermaidChart + " " + prompt} 
  />
)}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(10, 15, 26, 0.85)',
              borderLeft: msg.role === 'human' ? '4px solid #00f0ff' : '4px solid #10b981',
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.05)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ color: msg.role === 'human' ? '#00f0ff' : '#10b981', fontWeight: 'bold' }}>
                {msg.role === 'human' ? '👤 User Prompt' : '🤖 AI Agent Result'}
              </div>
              {msg.content && msg.content.includes('resource "aws_') && (
                <button
                  onClick={() => handleDownloadTerraform(msg.content)}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(16,185,129,0.2)', color: '#10b981', border: '1px solid #10b981', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                >
                  <Download size={14} /> Download main.tf
                </button>
              )}
            </div>
            <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'monospace', color: '#e2e8f0', fontSize: '14px', lineHeight: '1.5' }}>
              {msg.content}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

function DigitalTwin() {
  const [driftState, setDriftState] = useState({
    driftDetected: true,
    progress: 72,
    invalidatedDocs: ['Architecture_Diagram.png', 'SRS_Document.pdf', 'Viva_Presentation.pptx'],
    tasks: [
      { id: 'TSK-101', name: 'Multi-AZ VPC Terraform Build', assignee: 'Abhay', status: 'Completed' },
      { id: 'TSK-102', name: 'FastAPI Digital Twin API Sync', assignee: 'Amit', status: 'In Progress' },
      { id: 'TSK-103', name: 'React 3D UI Mesh Connection', assignee: 'Rahul', status: 'Completed' },
      { id: 'TSK-104', name: 'Auto Thesis & SRS Re-Gen', assignee: 'Sneha', status: 'Pending Sync' },
    ]
  });

  return (
    <div style={{ maxWidth: '950px', margin: '40px auto', padding: '0 20px', color: '#fff' }}>
      <header style={{ borderBottom: '1px solid rgba(0,240,255,0.2)', paddingBottom: '15px', marginBottom: '25px' }}>
        <h1 style={{ color: '#00f0ff', margin: 0, fontSize: '28px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Activity /> Project Digital Twin Engine
        </h1>
        <p style={{ color: '#94a3b8', margin: '4px 0 0 0', fontSize: '14px' }}>
          Continuous Live Sync between Code Repository, AWS Infrastructure, Tasks & Auto-Documentation.
        </p>
      </header>

      {driftState.driftDetected ? (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', padding: '18px', borderRadius: '10px', marginBottom: '25px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <AlertTriangle style={{ color: '#ef4444' }} size={24} />
            <div>
              <strong style={{ color: '#ef4444', fontSize: '15px', display: 'block' }}>Architecture Drift Detected!</strong>
              <span style={{ fontSize: '13px', color: '#cbd5e1' }}>
                Outdated Artifacts: {driftState.invalidatedDocs.join(', ')}
              </span>
            </div>
          </div>
          <button onClick={() => setDriftState(prev => ({ ...prev, driftDetected: false, invalidatedDocs: [], progress: 90 }))} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={14} /> Auto-Sync Docs
          </button>
        </div>
      ) : (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', padding: '14px 18px', borderRadius: '10px', marginBottom: '25px', color: '#10b981', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={18} /> Project Digital Twin in 100% Sync with AWS Cloud & Docs
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px', marginBottom: '30px' }}>
        <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.1)', padding: '18px', borderRadius: '10px' }}>
          <span style={{ color: '#94a3b8', fontSize: '13px' }}>Overall Progress</span>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#00f0ff', margin: '6px 0' }}>{driftState.progress}%</div>
          <div style={{ background: '#1e293b', height: '5px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${driftState.progress}%`, background: '#00f0ff', height: '100%' }} />
          </div>
        </div>
        <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.1)', padding: '18px', borderRadius: '10px' }}>
          <span style={{ color: '#94a3b8', fontSize: '13px' }}>AWS Infrastructure Status</span>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#10b981', margin: '10px 0 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle size={16} /> Multi-AZ Active (us-east-1)
          </div>
        </div>
      </div>

      <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.1)', padding: '20px', borderRadius: '10px' }}>
        <h3 style={{ margin: '0 0 14px 0', color: '#00f0ff', fontSize: '18px' }}>Skill-Matched Team Work Division</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
              <th style={{ paddingBottom: '8px' }}>Task ID</th>
              <th style={{ paddingBottom: '8px' }}>Task Description</th>
              <th style={{ paddingBottom: '8px' }}>Assignee</th>
              <th style={{ paddingBottom: '8px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {driftState.tasks.map((t) => (
              <tr key={t.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '10px 0', color: '#64748b' }}>{t.id}</td>
                <td style={{ padding: '10px 0', color: '#f8fafc' }}>{t.name}</td>
                <td style={{ padding: '10px 0', color: '#00f0ff', fontWeight: 'bold' }}>{t.assignee}</td>
                <td style={{ padding: '10px 0', color: t.status === 'Completed' ? '#10b981' : t.status === 'In Progress' ? '#f59e0b' : '#ef4444' }}>
                  {t.status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ModulesView() {
  const [activeTab, setActiveTab] = useState<'capstone' | 'startup' | 'enterprise'>('capstone');
  const [capstoneSpecs, setCapstoneSpecs] = useState({
    title: 'DevOrbit AI: Autonomous Cloud Infrastructure Platform',
    problem_statement: 'Cloud architecture, infrastructure automation, security review, and project documentation are often fragmented across disconnected tools, making delivery slower and difficult to audit.',
    objectives: 'Generate cloud infrastructure from architecture requirements\nProvide automated security and cost recommendations\nKeep project documentation synchronized with implementation',
    technologies: 'React, FastAPI, PostgreSQL, AWS, Terraform',
    methodology: 'Agile iterative development',
    authors: 'DevOrbit AI Research Team',
    generation_mode: 'auto' as 'auto' | 'user_based',
    custom_outline: '',
  });
  const [capstoneLoading, setCapstoneLoading] = useState(false);
  const [capstoneDocuments, setCapstoneDocuments] = useState<{ srs_markdown: string; research_paper_markdown: string; slides_markdown: string; project_report_markdown: string } | null>(null);
  const [activeDocument, setActiveDocument] = useState<'srs_markdown' | 'research_paper_markdown' | 'slides_markdown' | 'project_report_markdown'>('srs_markdown');
  const [capstoneError, setCapstoneError] = useState('');
  const [startupLoading, setStartupLoading] = useState(false);
  const [startupNotice, setStartupNotice] = useState('');
  const [startupTasks, setStartupTasks] = useState<Array<{ task_id: string; description: string; details: string; assignee: string; status: string }>>([]);
  const [enterpriseAuditLoading, setEnterpriseAuditLoading] = useState(false);
  const [enterpriseAuditNotice, setEnterpriseAuditNotice] = useState('');
  const [enterpriseAudit, setEnterpriseAudit] = useState<{ monthly_cost: number; currency: string; security_errors: number; cis_status: string; scanned_at: string; cis_checks: Array<{ control: string; passed: boolean; recommendation: string }> } | null>(null);

  const generateCapstone = async (event: React.FormEvent) => {
    event.preventDefault();
    setCapstoneLoading(true);
    setCapstoneError('');
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/modules/capstone/generate', {
        ...capstoneSpecs,
        objectives: capstoneSpecs.objectives.split('\n').map((item) => item.trim()).filter(Boolean),
        technologies: capstoneSpecs.technologies.split(',').map((item) => item.trim()).filter(Boolean),
        generation_mode: capstoneSpecs.generation_mode,
        custom_outline: capstoneSpecs.custom_outline,
      });
      setCapstoneDocuments(response.data.documents);
      setActiveDocument('srs_markdown');
    } catch {
      setCapstoneError('Unable to generate the academic documents. Confirm that the FastAPI server is running.');
    } finally {
      setCapstoneLoading(false);
    }
  };

  const downloadCapstone = () => {
    if (!capstoneDocuments) return;
    const content = `# DevOrbit AI Capstone Package\n\n${capstoneDocuments.srs_markdown}\n\n---\n\n${capstoneDocuments.research_paper_markdown}\n\n---\n\n${capstoneDocuments.project_report_markdown}\n\n---\n\n${capstoneDocuments.slides_markdown}`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([content], { type: 'text/markdown' }));
    link.download = 'devorbit-capstone-package.md';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const downloadCapstonePdf = () => {
    if (!capstoneDocuments) return;
    const pdf = new jsPDF({ unit: 'pt', format: 'a4' });
    const content = [capstoneDocuments.project_report_markdown, capstoneDocuments.srs_markdown, capstoneDocuments.research_paper_markdown, capstoneDocuments.slides_markdown].join('\n\n---\n\n');
    const lines = pdf.splitTextToSize(content.replace(/^#{1,6}\s?/gm, ''), 515);
    let y = 42;
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(16);
    pdf.text('DevOrbit AI Capstone Package', 40, y);
    y += 28;
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(9);
    lines.forEach((line: string) => { if (y > 800) { pdf.addPage(); y = 42; } pdf.text(line, 40, y); y += 13; });
    pdf.save('devorbit-capstone-package.pdf');
  };

  const syncStartupBacklog = async () => {
    setStartupLoading(true);
    setStartupNotice('');
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/modules/startup/sync-backlog', { repository: 'devorbit-ai/platform' });
      setStartupTasks(response.data.tasks);
      setStartupNotice(`GitHub backlog synchronized: ${response.data.summary.total} tasks allocated across the team.`);
    } catch {
      setStartupNotice('Unable to sync the GitHub backlog. Confirm that the FastAPI server is running.');
    } finally {
      setStartupLoading(false);
    }
  };

  const runEnterpriseAudit = async () => {
    setEnterpriseAuditLoading(true);
    setEnterpriseAuditNotice('');
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/modules/enterprise/audit', {});
      setEnterpriseAudit(response.data);
      setEnterpriseAuditNotice(`Audit completed at ${new Date(response.data.scanned_at).toLocaleTimeString()}.`);
    } catch {
      setEnterpriseAuditNotice('Unable to complete the FinOps and CIS audit. Confirm that the FastAPI server is running.');
    } finally {
      setEnterpriseAuditLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '950px', margin: '40px auto', padding: '0 20px', color: '#fff' }}>
      <header style={{ marginBottom: '25px' }}>
        <h1 style={{ color: '#00f0ff', margin: 0, fontSize: '28px' }}>⚡ Core Operating Modules</h1>
        <p style={{ color: '#94a3b8', margin: '4px 0 0 0', fontSize: '14px' }}>Switch between Academic Defense, Startup Operations, and Enterprise IDP Governance.</p>
      </header>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '25px' }}>
        {[
          { id: 'capstone', name: 'Module A: Capstone', icon: BookOpen },
          { id: 'startup', name: 'Module B: Startup MVP', icon: Rocket },
          { id: 'enterprise', name: 'Module C: Enterprise IDP', icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                flex: 1,
                padding: '12px 16px',
                background: isSelected ? 'rgba(0, 240, 255, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                border: isSelected ? '1px solid #00f0ff' : '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                color: isSelected ? '#00f0ff' : '#94a3b8',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <Icon size={16} /> {tab.name}
            </button>
          );
        })}
      </div>

      {activeTab === 'capstone' && (
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(0,240,255,0.3)', padding: '24px', borderRadius: '12px' }}>
          <h3 style={{ color: '#00f0ff', margin: '0 0 12px 0' }}>🎓 Auto Academic Research & Viva Defense Suite</h3>
          <p style={{ color: '#cbd5e1', fontSize: '14px' }}>Generate IEEE-compliant SRS documents, research paper drafts, and presentation slide decks.</p>
          <form onSubmit={generateCapstone} style={{ display: 'grid', gap: '12px', marginTop: '20px' }}>
            <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Project title
              <input value={capstoneSpecs.title} onChange={(event) => setCapstoneSpecs({ ...capstoneSpecs, title: event.target.value })} style={{ display: 'block', width: '100%', marginTop: '6px', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }} />
            </label>
            <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Problem statement
              <textarea rows={3} value={capstoneSpecs.problem_statement} onChange={(event) => setCapstoneSpecs({ ...capstoneSpecs, problem_statement: event.target.value })} style={{ display: 'block', width: '100%', marginTop: '6px', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff', resize: 'vertical' }} />
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Objectives, one per line
                <textarea rows={4} value={capstoneSpecs.objectives} onChange={(event) => setCapstoneSpecs({ ...capstoneSpecs, objectives: event.target.value })} style={{ display: 'block', width: '100%', marginTop: '6px', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff', resize: 'vertical' }} />
              </label>
              <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Technologies, comma-separated
                <textarea rows={4} value={capstoneSpecs.technologies} onChange={(event) => setCapstoneSpecs({ ...capstoneSpecs, technologies: event.target.value })} style={{ display: 'block', width: '100%', marginTop: '6px', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff', resize: 'vertical' }} />
              </label>
            </div>
            <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Methodology
              <input value={capstoneSpecs.methodology} onChange={(event) => setCapstoneSpecs({ ...capstoneSpecs, methodology: event.target.value })} style={{ display: 'block', width: '100%', marginTop: '6px', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }} />
            </label>
            <fieldset style={{ border: '1px solid #334155', borderRadius: '6px', padding: '12px', margin: 0 }}>
              <legend style={{ color: '#cbd5e1', fontSize: '13px', padding: '0 6px' }}>Generation Mode</legend>
              <div style={{ display: 'flex', gap: '18px', flexWrap: 'wrap' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '7px', color: '#cbd5e1', fontSize: '13px', cursor: 'pointer' }}>
                  <input type="radio" name="generation-mode" value="auto" checked={capstoneSpecs.generation_mode === 'auto'} onChange={() => setCapstoneSpecs({ ...capstoneSpecs, generation_mode: 'auto' })} />
                  Automatic (AI Structured)
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '7px', color: '#cbd5e1', fontSize: '13px', cursor: 'pointer' }}>
                  <input type="radio" name="generation-mode" value="user_based" checked={capstoneSpecs.generation_mode === 'user_based'} onChange={() => setCapstoneSpecs({ ...capstoneSpecs, generation_mode: 'user_based' })} />
                  User-Based (Custom Outline / Chapters)
                </label>
              </div>
            </fieldset>
            {capstoneSpecs.generation_mode === 'user_based' && <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Custom chapter structure or focus areas, one per line
              <textarea rows={5} placeholder={'Chapter 1: Introduction\nLiterature Review\nCloud Security Evaluation'} value={capstoneSpecs.custom_outline} onChange={(event) => setCapstoneSpecs({ ...capstoneSpecs, custom_outline: event.target.value })} required style={{ display: 'block', width: '100%', marginTop: '6px', padding: '10px', background: '#0a0d14', border: '1px solid #334155', borderRadius: '6px', color: '#fff', resize: 'vertical' }} />
            </label>}
            <button type="submit" disabled={capstoneLoading} style={{ display: 'inline-flex', justifyContent: 'center', alignItems: 'center', gap: '8px', padding: '12px 16px', background: capstoneLoading ? '#64748b' : '#00f0ff', color: '#070a10', border: 0, borderRadius: '6px', fontWeight: 800, cursor: capstoneLoading ? 'wait' : 'pointer' }}>
              {capstoneLoading ? 'Generating academic package...' : 'Generate Report, SRS & Slides'}
            </button>
          </form>
          {capstoneError && <p style={{ color: '#f87171', margin: '14px 0 0', fontSize: '13px' }}>{capstoneError}</p>}
          {capstoneDocuments && <div style={{ marginTop: '24px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '18px' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[['project_report_markdown', 'Project Report / Thesis'], ['srs_markdown', 'IEEE SRS'], ['research_paper_markdown', 'Research Draft'], ['slides_markdown', 'Slide Outline']].map(([key, label]) => <button key={key} onClick={() => setActiveDocument(key as typeof activeDocument)} style={{ padding: '8px 10px', background: activeDocument === key ? 'rgba(0,240,255,0.15)' : '#0a0d14', border: activeDocument === key ? '1px solid #00f0ff' : '1px solid #334155', borderRadius: '5px', color: activeDocument === key ? '#00f0ff' : '#94a3b8', cursor: 'pointer' }}>{label}</button>)}
              </div>
              <div style={{ display: 'flex', gap: '8px' }}><button onClick={downloadCapstone} style={{ padding: '8px 12px', background: 'rgba(16,185,129,0.15)', border: '1px solid #10b981', borderRadius: '5px', color: '#10b981', cursor: 'pointer', fontWeight: 700 }}>Download Markdown</button><button onClick={downloadCapstonePdf} style={{ padding: '8px 12px', background: 'rgba(112,0,255,0.2)', border: '1px solid #a78bfa', borderRadius: '5px', color: '#c4b5fd', cursor: 'pointer', fontWeight: 700 }}>Download PDF</button></div>
            </div>
            <pre style={{ maxHeight: '520px', overflow: 'auto', whiteSpace: 'pre-wrap', margin: 0, padding: '18px', background: '#0a0d14', border: '1px solid #1e293b', borderRadius: '6px', color: '#dbeafe', font: '13px/1.6 Consolas, monospace' }}>{capstoneDocuments[activeDocument]}</pre>
          </div>}
        </div>
      )}

      {activeTab === 'startup' && (
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(0,240,255,0.3)', padding: '24px', borderRadius: '12px' }}>
          <h3 style={{ color: '#00f0ff', margin: '0 0 12px 0' }}>🚀 Startup Task Allocation & GitHub Live Sync</h3>
          <p style={{ color: '#cbd5e1', fontSize: '14px' }}>Automatically maps incoming backlog tasks to developer skill sets.</p>
          <button onClick={() => void syncStartupBacklog()} disabled={startupLoading} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginTop: '16px', padding: '11px 16px', background: startupLoading ? '#64748b' : '#00f0ff', color: '#070a10', border: 0, borderRadius: '6px', fontWeight: 800, cursor: startupLoading ? 'wait' : 'pointer' }}>
            <RefreshCw size={16} className={startupLoading ? 'spin' : ''} />
            {startupLoading ? 'Syncing GitHub Backlog...' : 'Sync GitHub Backlog'}
          </button>
          {startupNotice && <p style={{ color: startupNotice.startsWith('Unable') ? '#f87171' : '#10b981', fontSize: '13px', margin: '14px 0 0' }}>{startupNotice}</p>}
          {startupTasks.length > 0 && <div style={{ overflowX: 'auto', marginTop: '20px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead><tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}><th style={{ padding: '10px 8px' }}>Task ID</th><th style={{ padding: '10px 8px' }}>Task Description</th><th style={{ padding: '10px 8px' }}>Assignee</th><th style={{ padding: '10px 8px' }}>Status</th></tr></thead>
              <tbody>{startupTasks.map((task) => <tr key={task.task_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}><td style={{ padding: '12px 8px', color: '#64748b', fontFamily: 'monospace' }}>{task.task_id}</td><td style={{ padding: '12px 8px', color: '#f8fafc' }}><strong>{task.description}</strong><small style={{ display: 'block', color: '#94a3b8', marginTop: '4px' }}>{task.details}</small></td><td style={{ padding: '12px 8px', color: '#00f0ff', fontWeight: 700 }}>{task.assignee}</td><td style={{ padding: '12px 8px', color: '#10b981' }}>{task.status}</td></tr>)}</tbody>
            </table>
          </div>}
        </div>
      )}

      {activeTab === 'enterprise' && (
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(0,240,255,0.3)', padding: '24px', borderRadius: '12px' }}>
          <h3 style={{ color: '#00f0ff', margin: '0 0 12px 0' }}>🏢 Enterprise FinOps & CIS Security Audit</h3>
          <p style={{ color: '#cbd5e1', fontSize: '14px' }}>Scan the current resource baseline for monthly cost and CIS control posture.</p>
          <button onClick={() => void runEnterpriseAudit()} disabled={enterpriseAuditLoading} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', marginTop: '10px', padding: '11px 16px', background: enterpriseAuditLoading ? '#64748b' : '#00f0ff', color: '#070a10', border: 0, borderRadius: '6px', fontWeight: 800, cursor: enterpriseAuditLoading ? 'wait' : 'pointer' }}>
            <RefreshCw size={16} className={enterpriseAuditLoading ? 'spin' : ''} />
            {enterpriseAuditLoading ? 'Scanning FinOps & CIS Controls...' : 'Run FinOps & CIS Audit'}
          </button>
          {enterpriseAuditNotice && <p style={{ color: enterpriseAuditNotice.startsWith('Unable') ? '#f87171' : '#10b981', fontSize: '13px', margin: '12px 0 0' }}>{enterpriseAuditNotice}</p>}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '15px' }}>
            <div style={{ background: '#0a0d14', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
              <h4 style={{ color: '#10b981', margin: '0 0 6px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <DollarSign size={16} /> FinOps Cost Estimator
              </h4>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{enterpriseAudit ? `$${enterpriseAudit.monthly_cost.toFixed(2)} / month` : 'Not scanned'}</div>
            </div>
            <div style={{ background: '#0a0d14', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
              <h4 style={{ color: '#00f0ff', margin: '0 0 6px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={16} /> CIS Security Status
              </h4>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: enterpriseAudit?.security_errors ? '#f87171' : '#10b981' }}>{enterpriseAudit ? `${enterpriseAudit.security_errors} Security Errors · ${enterpriseAudit.cis_status}` : 'Not scanned'}</div>
            </div>
          </div>
          {enterpriseAudit && <div style={{ marginTop: '18px', display: 'grid', gap: '8px' }}>{enterpriseAudit.cis_checks.map((check) => <div key={check.control} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', padding: '10px 12px', background: '#0a0d14', border: '1px solid #1e293b', borderRadius: '6px', fontSize: '13px' }}><span style={{ color: '#cbd5e1' }}>{check.control}</span><span style={{ color: check.passed ? '#10b981' : '#f87171', fontWeight: 700 }}>{check.passed ? 'PASS' : 'FAIL'}</span></div>)}</div>}
        </div>
      )}
    </div>
  );
}

function Status() {
  return <SystemStatus />;
}

export default function App() {
  return (
    <Router>
      <div className="app-shell" style={{ minHeight: '100vh', background: 'var(--page-bg)', color: 'var(--text-main)', fontFamily: 'system-ui, sans-serif' }}>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/auth/login" element={<Auth initialMode="login" />} />
          <Route path="/auth/register" element={<Auth initialMode="register" />} />
          <Route path="/orchestrator" element={<Orchestrator />} />
          <Route path="/digital-twin" element={<DigitalTwin />} />
          <Route path="/modules" element={<ModulesView />} />
          <Route path="/status" element={<Status />} />
          <Route path="/cloud-control" element={<CloudControl />} />
          <Route path="/enterprise" element={<EnterpriseDashboard />} />
        </Routes>
      </div>
    </Router>
  );
}