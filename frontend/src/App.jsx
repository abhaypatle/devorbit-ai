import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Cpu, ArrowRight, Terminal, Server, ShieldCheck } from 'lucide-react';

function Navbar() {
  const location = useLocation();
  const links = [
    { name: 'Home', path: '/' },
    { name: 'Agent Pipeline', path: '/orchestrator' },
    { name: 'System Status', path: '/status' },
  ];

  return (
    <nav style={{ background: 'rgba(15, 23, 42, 0.9)', borderBottom: '1px solid rgba(0,240,255,0.2)', padding: '15px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 50 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Cpu style={{ color: '#00f0ff' }} />
        <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#00f0ff' }}>DevOrbit AI</span>
      </div>
      <div style={{ display: 'flex', gap: '20px' }}>
        {links.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            style={{
              color: location.pathname === link.path ? '#00f0ff' : '#94a3b8',
              textDecoration: 'none',
              fontWeight: '600',
              padding: '6px 12px',
              borderRadius: '6px',
              background: location.pathname === link.path ? 'rgba(0,240,255,0.1)' : 'transparent'
            }}
          >
            {link.name}
          </Link>
        ))}
      </div>
    </nav>
  );
}

function Home() {
  return (
    <div style={{ maxWidth: '1000px', margin: '60px auto', textAlign: 'center', padding: '0 20px', color: '#fff' }}>
      <h1 style={{ fontSize: '44px', fontWeight: '800', marginBottom: '20px' }}>
        Autonomous Cloud Infrastructure with <br />
        <span style={{ color: '#00f0ff' }}>Multi-Agent AI Orchestrator</span>
      </h1>
      <p style={{ color: '#94a3b8', fontSize: '18px', marginBottom: '30px' }}>
        Design, validate, and compile AWS Infrastructure-as-Code automatically using LangGraph & Amazon Bedrock.
      </p>
      <Link to="/orchestrator" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', background: '#00f0ff', color: '#0f172a', padding: '14px 28px', borderRadius: '8px', fontWeight: 'bold', textDecoration: 'none' }}>
        Launch Agent Workspace <ArrowRight size={18} />
      </Link>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginTop: '60px' }}>
        {[
          { icon: Terminal, title: 'Planner Agent', desc: 'Translates prompt into Multi-AZ architecture strategy.' },
          { icon: Server, title: 'Cloud Architect Agent', desc: 'Builds AWS VPC, ALB, and Multi-AZ RDS blueprints.' },
          { icon: ShieldCheck, title: 'DevOps IaC Agent', desc: 'Compiles AWS blueprints directly into Terraform code.' },
        ].map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.1)', padding: '24px', borderRadius: '12px', textAlign: 'left' }}>
              <Icon style={{ color: '#00f0ff', marginBottom: '12px' }} size={28} />
              <h3 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>{item.title}</h3>
              <p style={{ color: '#94a3b8', margin: 0, fontSize: '14px' }}>{item.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Orchestrator() {
  const [projectId, setProjectId] = useState('devorbit-prod-01');
  const [prompt, setPrompt] = useState('Design a high-availability AWS architecture for a scalable web application with auto scaling and RDS PostgreSQL.');
  const [loading, setLoading] = useState(false);
 const [messages, setMessages] = useState([]);
  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessages([]);

    try {
      const res = await axios.post('http://127.0.0.1:8000/api/v1/orchestrator/run', {
        project_id: projectId,
        prompt: prompt,
      });

      if (res.data.status === 'success') {
        setMessages(res.data.messages);
      }
    } catch (err) {
      console.error(err);
      alert('Backend Connection Error! Make sure FastAPI is running on http://127.0.0.1:8000');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '40px auto', padding: '0 20px', color: '#fff' }}>
      <div style={{ background: 'rgba(30, 41, 59, 0.6)', border: '1px solid rgba(0,240,255,0.3)', padding: '30px', borderRadius: '16px', marginBottom: '30px' }}>
        <h2 style={{ margin: '0 0 20px 0', color: '#00f0ff', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu /> Multi-Agent Execution Workspace
        </h2>
        <form onSubmit={handleRun} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: '#cbd5e1' }}>Project ID</label>
            <input
              type="text"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: '#cbd5e1' }}>Architecture Requirement</label>
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{ padding: '14px', background: loading ? '#64748b' : '#00f0ff', color: '#0f172a', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            {loading ? 'Agents Analyzing & Compiling...' : 'Execute Multi-Agent Graph'}
          </button>
        </form>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              borderLeft: msg.role === 'human' ? '4px solid #00f0ff' : '4px solid #10b981',
              padding: '20px',
              borderRadius: '8px'
            }}
          >
            <div style={{ color: msg.role === 'human' ? '#00f0ff' : '#10b981', fontWeight: 'bold', marginBottom: '8px' }}>
              {msg.role === 'human' ? '👤 User Prompt' : '🤖 AI Agent Result'}
            </div>
            <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'monospace', color: '#e2e8f0', fontSize: '14px' }}>
              {msg.content}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

function Status() {
  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 20px', color: '#fff' }}>
      <h2 style={{ color: '#00f0ff', marginBottom: '20px' }}>System Network Status</h2>
      <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '20px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.1)' }}>
        <p>🟢 <strong>FastAPI Backend Core:</strong> Port 8000 (Active)</p>
        <p>🟢 <strong>LangGraph Engine:</strong> Orchestration Enabled</p>
        <p>🟢 <strong>Bedrock Model Mode:</strong> Mocking Active</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <div style={{ background: '#0a0d14', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/orchestrator" element={<Orchestrator />} />
          <Route path="/status" element={<Status />} />
        </Routes>
      </div>
    </Router>
  );
}