import React, { useState } from 'react';
import axios from 'axios';
import { Cpu, Download } from 'lucide-react';

export default function AgentPipeline() {
  const [projectId, setProjectId] = useState('devorbit-prod-01');
  const [prompt, setPrompt] = useState('Design a serverless API using AWS Lambda and DynamoDB');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);

  // Diagram mode strictly tracking user active selection
  const [activeLayout, setActiveLayout] = useState<'serverless' | 'container' | 'multiaz'>('serverless');

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Immediate diagram layout state update based on prompt keyword
    const pLower = prompt.toLowerCase();
    if (pLower.includes('lambda') || pLower.includes('serverless') || pLower.includes('dynamodb')) {
      setActiveLayout('serverless');
    } else if (pLower.includes('container') || pLower.includes('fargate') || pLower.includes('ecs')) {
      setActiveLayout('container');
    } else {
      setActiveLayout('multiaz');
    }

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
      alert('Backend Connection Error! Verify FastAPI on http://127.0.0.1:8000');
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

  return (
    <div style={{ maxWidth: '900px', margin: '40px auto', padding: '0 20px', color: '#fff', fontFamily: 'sans-serif' }}>
      
      {/* Workspace Form */}
      <div style={{ background: 'rgba(15, 23, 42, 0.85)', border: '1px solid rgba(0,240,255,0.3)', padding: '30px', borderRadius: '16px', marginBottom: '30px' }}>
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

      {/* Direct SVG Render Box */}
      <div style={{
        background: 'rgba(10, 15, 26, 0.9)',
        border: '1px solid rgba(0, 240, 255, 0.4)',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '20px',
        boxShadow: '0 0 20px rgba(0, 240, 255, 0.15)',
        overflowX: 'auto'
      }}>
        <h4 style={{ color: '#00f0ff', margin: '0 0 16px 0', fontSize: '15px' }}>
          📐 Live Target Infrastructure Diagram
        </h4>

        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
          {activeLayout === 'serverless' && (
            <svg width="600" height="120" viewBox="0 0 600 120" xmlns="http://www.w3.org/2000/svg">
              <rect x="20" y="35" width="110" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
              <text x="75" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">👤 User</text>
              <path d="M 130 60 L 170 60" stroke="#00f0ff" strokeWidth="2"/>
              <rect x="175" y="35" width="120" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
              <text x="235" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">🚪 API Gateway</text>
              <path d="M 295 60 L 335 60" stroke="#00f0ff" strokeWidth="2"/>
              <rect x="340" y="35" width="120" height="50" rx="8" fill="#1e293b" stroke="#10b981" strokeWidth="2"/>
              <text x="400" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">⚡ AWS Lambda</text>
              <path d="M 460 60 L 495 60" stroke="#10b981" strokeWidth="2"/>
              <rect x="500" y="35" width="110" height="50" rx="8" fill="#1e293b" stroke="#f59e0b" strokeWidth="2"/>
              <text x="555" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">🗄️ DynamoDB</text>
            </svg>
          )}

          {activeLayout === 'container' && (
            <svg width="600" height="120" viewBox="0 0 600 120" xmlns="http://www.w3.org/2000/svg">
              <rect x="20" y="35" width="100" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
              <text x="70" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">👤 User</text>
              <path d="M 120 60 L 160 60" stroke="#00f0ff" strokeWidth="2"/>
              <rect x="165" y="35" width="130" height="50" rx="8" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
              <text x="230" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">⚖️ Load Balancer</text>
              <path d="M 295 60 L 335 60" stroke="#00f0ff" strokeWidth="2"/>
              <rect x="340" y="35" width="130" height="50" rx="8" fill="#1e293b" stroke="#3b82f6" strokeWidth="2"/>
              <text x="400" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">🐳 ECS Fargate</text>
              <path d="M 470 60 L 505 60" stroke="#3b82f6" strokeWidth="2"/>
              <rect x="510" y="35" width="110" height="50" rx="8" fill="#1e293b" stroke="#ef4444" strokeWidth="2"/>
              <text x="565" y="65" fill="#fff" fontSize="14" textAnchor="middle" fontWeight="bold">⚡ Redis Cache</text>
            </svg>
          )}

          {activeLayout === 'multiaz' && (
            <svg width="600" height="180" viewBox="0 0 600 180" xmlns="http://www.w3.org/2000/svg">
              <rect x="240" y="10" width="120" height="35" rx="6" fill="#1e293b" stroke="#00f0ff" strokeWidth="2"/>
              <text x="300" y="32" fill="#fff" fontSize="13" textAnchor="middle" fontWeight="bold">🌐 Route 53 / ALB</text>
              <path d="M 270 45 L 200 80" stroke="#00f0ff" strokeWidth="2"/>
              <path d="M 330 45 L 400 80" stroke="#00f0ff" strokeWidth="2"/>
              <rect x="130" y="80" width="140" height="40" rx="6" fill="#1e293b" stroke="#3b82f6" strokeWidth="2"/>
              <text x="200" y="105" fill="#fff" fontSize="12" textAnchor="middle">AZ 1: EC2 Server</text>
              <rect x="330" y="80" width="140" height="40" rx="6" fill="#1e293b" stroke="#3b82f6" strokeWidth="2"/>
              <text x="400" y="105" fill="#fff" fontSize="12" textAnchor="middle">AZ 2: EC2 Server</text>
              <path d="M 200 120 L 200 145" stroke="#10b981" strokeWidth="2"/>
              <path d="M 400 120 L 400 145" stroke="#10b981" strokeWidth="2"/>
              <rect x="130" y="145" width="140" height="30" rx="6" fill="#1e293b" stroke="#10b981" strokeWidth="2"/>
              <text x="200" y="165" fill="#fff" fontSize="12" textAnchor="middle">RDS Master DB</text>
              <rect x="330" y="145" width="140" height="30" rx="6" fill="#1e293b" stroke="#f59e0b" strokeWidth="2"/>
              <text x="400" y="165" fill="#fff" fontSize="12" textAnchor="middle">RDS Standby DB</text>
            </svg>
          )}
        </div>
      </div>

      {/* Output Feed */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
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