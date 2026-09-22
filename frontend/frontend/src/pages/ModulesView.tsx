import React, { useState } from 'react';
import { BookOpen, Rocket, ShieldCheck, Download, DollarSign, CheckCircle2 } from 'lucide-react';

export default function ModulesView() {
  const [activeTab, setActiveTab] = useState<'capstone' | 'startup' | 'enterprise'>('capstone');

  return (
    <div style={{ maxWidth: '1100px', margin: '40px auto', padding: '0 24px', color: '#fff' }}>
      <header style={{ marginBottom: '30px' }}>
        <h1 style={{ color: '#00f0ff', margin: 0, fontSize: '30px' }}>⚡ Core Operating Modules</h1>
        <p style={{ color: '#94a3b8', margin: '6px 0 0 0' }}>Switch between Academic Defense, Startup Operations, and Enterprise IDP Governance.</p>
      </header>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '30px' }}>
        {[
          { id: 'capstone', name: 'Module A: Academic Capstone', icon: BookOpen },
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
                padding: '14px 20px',
                background: isSelected ? 'rgba(0, 240, 255, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                border: isSelected ? '1px solid #00f0ff' : '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '10px',
                color: isSelected ? '#00f0ff' : '#94a3b8',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                transition: 'all 0.3s ease'
              }}
            >
              <Icon size={18} /> {tab.name}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Academic Capstone */}
      {activeTab === 'capstone' && (
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(0,240,255,0.3)', padding: '28px', borderRadius: '16px' }}>
          <h3 style={{ color: '#00f0ff', margin: '0 0 16px 0' }}>🎓 Auto Academic Research & Viva Defense Suite</h3>
          <p style={{ color: '#cbd5e1', fontSize: '15px' }}>Generate IEEE-compliant SRS documents, research papers, and slide decks in 1-click.</p>
          <div style={{ display: 'flex', gap: '16px', marginTop: '24px' }}>
            <button style={{ padding: '12px 20px', background: '#00f0ff', color: '#070a10', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Download size={16} /> Download IEEE SRS (.md)
            </button>
            <button style={{ padding: '12px 20px', background: 'rgba(112, 0, 255, 0.3)', color: '#fff', border: '1px solid #7000ff', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Download size={16} /> Export Presentation PPT Outline
            </button>
          </div>
        </div>
      )}

      {/* Tab 2: Startup MVP */}
      {activeTab === 'startup' && (
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(0,240,255,0.3)', padding: '28px', borderRadius: '16px' }}>
          <h3 style={{ color: '#00f0ff', margin: '0 0 16px 0' }}>🚀 Startup Task Allocation & GitHub Live Sync</h3>
          <p style={{ color: '#cbd5e1', fontSize: '15px' }}>Automatically maps incoming backlog tasks to developer skill sets.</p>
          <div style={{ background: '#0a0d14', padding: '16px', borderRadius: '10px', marginTop: '16px', border: '1px solid #1e293b' }}>
            <div style={{ color: '#10b981', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={16} /> Task Engine Synced with GitHub Repository
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Enterprise IDP */}
      {activeTab === 'enterprise' && (
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(0,240,255,0.3)', padding: '28px', borderRadius: '16px' }}>
          <h3 style={{ color: '#00f0ff', margin: '0 0 16px 0' }}>🏢 Enterprise FinOps & CIS Security Audit</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
            <div style={{ background: '#0a0d14', padding: '20px', borderRadius: '12px', border: '1px solid #1e293b' }}>
              <h4 style={{ color: '#10b981', margin: '0 0 10px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <DollarSign /> FinOps Cost Estimator
              </h4>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>$195 / month</div>
              <p style={{ color: '#64748b', fontSize: '13px', margin: '6px 0 0 0' }}>AWS Multi-AZ VPC + ALB + RDS + EFS</p>
            </div>
            <div style={{ background: '#0a0d14', padding: '20px', borderRadius: '12px', border: '1px solid #1e293b' }}>
              <h4 style={{ color: '#00f0ff', margin: '0 0 10px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck /> CIS Compliance Status
              </h4>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#10b981' }}>0 Critical Security Errors</div>
              <p style={{ color: '#64748b', fontSize: '13px', margin: '6px 0 0 0' }}>Terraform HCL Audit Passed</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}