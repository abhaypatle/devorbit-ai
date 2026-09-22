import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { CheckCircle, Database, Gauge, HeartPulse, RefreshCw, Server, Terminal, Zap } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

type Service = { name: string; status: string; latency_ms: number };
type Telemetry = {
  timestamp: string;
  cpu_usage: number;
  memory_usage: { used_mb: number; total_mb: number; percentage: number };
  database_status: string;
  services: Service[];
  recent_logs: string[];
};

function GaugeCard({ label, value, detail, color }: { label: string; value: number; detail: string; color: string }) {
  return <article className="telemetry-gauge-card">
    <div className="gauge-ring" style={{ background: `conic-gradient(${color} ${value * 3.6}deg, rgba(255,255,255,.08) 0deg)` }}>
      <div className="gauge-center"><strong>{value.toFixed(1)}%</strong><span>utilization</span></div>
    </div>
    <div><p className="telemetry-label">{label}</p><strong className="telemetry-value">{value.toFixed(1)}%</strong><p className="telemetry-detail">{detail}</p></div>
  </article>;
}

export default function SystemStatus() {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<'diagnostics' | 'refresh' | ''>('');
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState('');

  const loadTelemetry = useCallback(async (mode: 'diagnostics' | 'refresh' | '' = '') => {
    setAction(mode);
    setLoading(true);
    setError('');
    try {
      const response = await axios.get<Telemetry>(`${API_URL}/api/v1/system/telemetry`);
      setTelemetry(response.data);
      setLogs(response.data.recent_logs);
    } catch {
      setError('Telemetry endpoint unavailable. Confirm the FastAPI server is running.');
    } finally {
      setLoading(false);
      setAction('');
    }
  }, []);

  useEffect(() => {
    void loadTelemetry();
    const interval = window.setInterval(() => void loadTelemetry(), 10000);
    return () => window.clearInterval(interval);
  }, [loadTelemetry]);

  const runDiagnostics = () => { void loadTelemetry('diagnostics'); };
  const flushAndRefresh = () => { setLogs([]); void loadTelemetry('refresh'); };
  const memory = telemetry?.memory_usage;

  return <main className="status-page">
    <header className="status-header">
      <div><p className="eyebrow">DEVORBIT / SYSTEM TELEMETRY</p><h1>Telemetry & health center</h1><p className="muted">A live pulse check across the control plane, runtime resources, and core services.</p></div>
      <div className="status-live"><span /> LIVE HEARTBEAT</div>
    </header>

    <div className="status-actions"><span className="last-sync">{telemetry ? `Last sync ${new Date(telemetry.timestamp).toLocaleTimeString()}` : 'Waiting for first heartbeat'}</span><button className="secondary-button" onClick={runDiagnostics} disabled={loading}><Gauge size={16} className={action === 'diagnostics' ? 'spin' : ''} />{action === 'diagnostics' ? 'Running diagnostics...' : 'Run System Diagnostics'}</button><button className="primary-button status-refresh" onClick={flushAndRefresh} disabled={loading}><RefreshCw size={16} className={action === 'refresh' ? 'spin' : ''} />{action === 'refresh' ? 'Refreshing...' : 'Flush & Refresh'}</button></div>
    {error && <div className="status-error">{error}</div>}

    <section className="status-gauges"><GaugeCard label="CPU usage" value={telemetry?.cpu_usage ?? 0} detail="Process host utilization" color="#00f0ff" /><GaugeCard label="Memory usage" value={memory?.percentage ?? 0} detail={memory ? `${memory.used_mb}MB of ${memory.total_mb}MB` : 'Awaiting telemetry'} color="#a78bfa" /><article className="telemetry-gauge-card database-card"><div className="database-icon"><Database size={27} /></div><div><p className="telemetry-label">Database status</p><strong className="telemetry-value database-value">{telemetry?.database_status || 'Checking'}</strong><p className="telemetry-detail">Persistence health signal</p></div></article></section>

    <section className="heartbeat-panel glass-panel"><div className="status-section-heading"><div><p className="eyebrow">01 / HEARTBEAT</p><h2>Live heartbeat & latency monitor</h2></div><HeartPulse size={22} /></div><div className="service-list">{(telemetry?.services || []).map((service) => <div className="service-row" key={service.name}><div className="service-name"><span className="service-dot" /><Server size={17} /><strong>{service.name}</strong></div><span className="service-status"><CheckCircle size={15} />{service.status}</span><span className="latency"><Zap size={14} />{service.latency_ms}ms</span></div>)}</div>{!telemetry && <p className="empty-telemetry">Waiting for service heartbeat...</p>}</section>

    <section className="terminal-panel glass-panel"><div className="status-section-heading"><div><p className="eyebrow">02 / EVENT STREAM</p><h2>Live terminal log stream</h2></div><Terminal size={21} /></div><div className="telemetry-console">{logs.length ? logs.map((log, index) => <div key={`${log}-${index}`}><span className="console-marker">›</span>{log}</div>) : <span className="console-muted">{loading ? 'Flushing event buffer...' : 'No recent events'}</span>}</div></section>
  </main>;
}
