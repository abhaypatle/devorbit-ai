import { useState } from 'react';
import { Activity, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';

interface ResourceDrift {
  id: string;
  resource_type: string;
  resource_name: string;
  expected_state: string;
  actual_state: string;
  status: 'IN_SYNC' | 'DRIFTED' | 'MISSING';
  last_checked: string;
}

export default function DigitalTwin() {
  const [syncing, setSyncing] = useState(false);
  const [resources, setResources] = useState<ResourceDrift[]>([
    {
      id: 'res-1',
      resource_type: 'aws_db_instance',
      resource_name: 'devorbit-prod-db',
      expected_state: 'Multi-AZ: True, Instance: db.t4g.micro',
      actual_state: 'Multi-AZ: True, Instance: db.t4g.micro',
      status: 'IN_SYNC',
      last_checked: '2 mins ago'
    },
    {
      id: 'res-2',
      resource_type: 'aws_security_group',
      resource_name: 'web-sg',
      expected_state: 'Ports: 80, 443 (Allowed)',
      actual_state: 'Ports: 80, 443, 22 (Allowed)',
      status: 'DRIFTED',
      last_checked: 'Just now'
    },
    {
      id: 'res-3',
      resource_type: 'aws_lambda_function',
      resource_name: 'api-auth-handler',
      expected_state: 'Runtime: nodejs18.x, Memory: 512MB',
      actual_state: 'Runtime: nodejs18.x, Memory: 512MB',
      status: 'IN_SYNC',
      last_checked: '5 mins ago'
    },
    {
      id: 'res-4',
      resource_type: 'aws_s3_bucket',
      resource_name: 'devorbit-media-assets',
      expected_state: 'Public Access Block: Enabled',
      actual_state: 'Public Access Block: Disabled',
      status: 'DRIFTED',
      last_checked: '1 min ago'
    }
  ]);

  const handleSyncScan = () => {
    setSyncing(true);
    setTimeout(() => {
      setResources((prev) =>
        prev.map((r) => ({
          ...r,
          last_checked: 'Just now'
        }))
      );
      setSyncing(false);
    }, 1500);
  };

  const driftedCount = resources.filter((r) => r.status === 'DRIFTED').length;
  const inSyncCount = resources.filter((r) => r.status === 'IN_SYNC').length;

  return (
    <div style={{ maxWidth: '1100px', margin: '40px auto', padding: '0 20px', color: '#fff', fontFamily: 'sans-serif' }}>
      
      {/* Header Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <div>
          <h2 style={{ margin: 0, color: '#00f0ff', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity /> Digital Twin: Cloud Infrastructure Drift Monitor
          </h2>
          <p style={{ margin: '6px 0 0 0', color: '#94a3b8', fontSize: '14px' }}>
            Real-time synchronization engine between Terraform IaC code and deployed AWS environment.
          </p>
        </div>

        <button
          onClick={handleSyncScan}
          disabled={syncing}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: syncing ? '#334155' : '#00f0ff',
            color: '#070a10',
            border: 'none',
            padding: '12px 20px',
            borderRadius: '8px',
            fontWeight: 'bold',
            cursor: syncing ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s'
          }}
        >
          <RefreshCw className={syncing ? 'spin' : ''} size={18} />
          {syncing ? 'Scanning AWS Environment...' : 'Re-Scan AWS Drift'}
        </button>
      </div>

      <style>{`
        @keyframes spinAnimation {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .spin {
          animation: spinAnimation 1s linear infinite;
        }
      `}</style>

      {/* Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '30px' }}>
        <div style={{ background: 'rgba(15, 23, 42, 0.85)', border: '1px solid rgba(0, 240, 255, 0.3)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px' }}>Total Tracked Resources</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#00f0ff' }}>{resources.length}</div>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.85)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px' }}>In-Sync Resources</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={24} /> {inSyncCount}
          </div>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.85)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px' }}>Drift Detected</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={24} /> {driftedCount}
          </div>
        </div>
      </div>

      {/* Resource Drift Table */}
      <div style={{ background: 'rgba(10, 15, 26, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: 'rgba(15, 23, 42, 0.95)', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
              <th style={{ padding: '16px 20px' }}>Resource Type</th>
              <th style={{ padding: '16px 20px' }}>Resource Name</th>
              <th style={{ padding: '16px 20px' }}>Expected (Terraform State)</th>
              <th style={{ padding: '16px 20px' }}>Actual (AWS Live)</th>
              <th style={{ padding: '16px 20px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {resources.map((item) => (
              <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: item.status === 'DRIFTED' ? 'rgba(239, 68, 68, 0.05)' : 'transparent' }}>
                <td style={{ padding: '16px 20px', fontFamily: 'monospace', color: '#00f0ff' }}>{item.resource_type}</td>
                <td style={{ padding: '16px 20px', fontWeight: 'bold' }}>{item.resource_name}</td>
                <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{item.expected_state}</td>
                <td style={{ padding: '16px 20px', color: item.status === 'DRIFTED' ? '#f87171' : '#cbd5e1' }}>{item.actual_state}</td>
                <td style={{ padding: '16px 20px' }}>
                  {item.status === 'IN_SYNC' ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold' }}>
                      <CheckCircle size={14} /> IN SYNC
                    </span>
                  ) : (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold' }}>
                      <AlertTriangle size={14} /> DRIFTED
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}