import React, { useState } from 'react';
import axios from 'axios';
import { Cpu, Download } from 'lucide-react';
import DiagramRenderer from './components/DiagramRenderer';

export default function App() {
  const [projectId, setProjectId] = useState('devorbit-prod-01');
  const [prompt, setPrompt] = useState('Design a high-availability AWS architecture for a scalable web application with auto scaling and RDS PostgreSQL.');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [showDiagram, setShowDiagram] = useState(false);
  const [mermaidChart, setMermaidChart] = useState<string>('');

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessages([]);
    setShowDiagram(false);

    try {
      const res = await axios.post('http://127.0.0.1:8000/api/v1/orchestrator/run', {
        project_id: projectId,
        prompt: prompt,
      });

      if (res.data.status === 'success') {
        setMessages(res.data.messages);
        setMermaidChart(res.data.diagram || prompt);
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

  return (
    <div style={{ maxWidth: '900px', margin: '40px auto', padding: '0 20px', color: '#fff', fontFamily: 'sans-serif' }}>
      
      {/* Multi-Agent Execution Workspace Form */}
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

      {/* Dynamic Key se React Component Force-Re-render Hoga */}
      {showDiagram && mermaidChart && (
        <DiagramRenderer key={mermaidChart + prompt} chart={mermaidChart} />
      )}

      {/* Execution Results */}
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