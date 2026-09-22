import React, { useState } from 'react';
import { AlertTriangle, RefreshCw, CheckCircle, FileText, Activity } from 'lucide-react';

export default function DigitalTwin() {
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

  const handleAutoSync = () => {
    setDriftState((prev) => ({
      ...prev,
      driftDetected: false,
      invalidatedDocs: [],
      progress: 90,
    }));
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '40px auto', padding: '0 24px', color: '#fff' }}>
      <header style={{ borderBottom: '1px solid rgba(0,240,255,0.2)', paddingBottom: '20px', marginBottom: '30px' }}>
        <h1 style={{ color: '#00f0ff', margin: 0, fontSize: '30px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Activity /> Project Digital Twin Engine
        </h1>
        <p style={{ color: '#94a3b8', margin: '6px 0 0 0' }}>
          Continuous Live Sync between Code Repository, AWS Infrastructure, Tasks & Auto-Documentation.
        </p>
      </header>

      {/* Drift Warning Banner */}
      {driftState.driftDetected ? (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', padding: '20px', borderRadius: '12px', marginBottom: '30px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <AlertTriangle style={{ color: '#ef4444' }} size={28} />
            <div>
              <strong style={{ color: '#ef4444', fontSize: '16px', display: 'block' }}>Architecture Drift Detected!</strong>
              <span style={{ fontSize: '14px', color: '#cbd5e1' }}>
                Outdated Artifacts: {driftState.invalidatedDocs.join(', ')}
              </span>
            </div>
          </div>
          <button onClick={handleAutoSync} style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RefreshCw size={16} /> Auto-Sync Docs
          </button>
        </div>
      ) : (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', padding: '16px 20px', borderRadius: '12px', marginBottom: '30px', color: '#10b981', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <CheckCircle size={20} /> Project Digital Twin in 100% Sync with AWS Cloud & Docs
        </div>
      )}

      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '35px' }}>
        <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.1)', padding: '20px', borderRadius: '12px' }}>
          <span style={{ color: '#94a3b8', fontSize: '14px' }}>Overall Completion</span>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#00f0ff', margin: '8px 0' }}>{driftState.progress}%</div>
          <div style={{ background: '#1e293b', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${driftState.progress}%`, background: '#00f0ff', height: '100%' }} />
          </div>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.1)', padding: '20px', borderRadius: '12px' }}>
          <span style={{ color: '#94a3b8', fontSize: '14px' }}>AWS Cloud Infrastructure Status</span>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#10b981', margin: '12px 0 0 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={18} /> Multi-AZ HA Active (us-east-1)
          </div>
        </div>
      </div>

      {/* Task Assignment Table */}
      <div style={{ background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255,255,255,0.1)', padding: '24px', borderRadius: '12px' }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#00f0ff' }}>Skill-Matched Team Work Division</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
              <th style={{ paddingBottom: '10px' }}>Task ID</th>
              <th style={{ paddingBottom: '10px' }}>Task Description</th>
              <th style={{ paddingBottom: '10px' }}>Assignee</th>
              <th style={{ paddingBottom: '10px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {driftState.tasks.map((t) => (
              <tr key={t.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '12px 0', color: '#64748b' }}>{t.id}</td>
                <td style={{ padding: '12px 0', color: '#f8fafc' }}>{t.name}</td>
                <td style={{ padding: '12px 0', color: '#00f0ff', fontWeight: 'bold' }}>{t.assignee}</td>
                <td style={{ padding: '12px 0', color: t.status === 'Completed' ? '#10b981' : t.status === 'In Progress' ? '#f59e0b' : '#ef4444' }}>
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