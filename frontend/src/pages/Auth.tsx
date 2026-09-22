import { useState } from 'react';
import type { FormEvent } from 'react';
import axios from 'axios';
import { ArrowRight, Check, Cpu, Eye, EyeOff, Shield, Sparkles, UserRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
type Mode = 'login' | 'register';
type Role = 'devops_engineer' | 'cloud_architect' | 'full_stack_developer' | 'enterprise_admin';
const roleOptions: Array<{ value: Role; label: string; detail: string; color: string }> = [
  { value: 'devops_engineer', label: 'DevOps Engineer', detail: 'Pipelines, runtime, automation', color: '#57d7c2' },
  { value: 'cloud_architect', label: 'Cloud Architect', detail: 'Systems, resilience, IaC', color: '#67c7ff' },
  { value: 'full_stack_developer', label: 'Full-Stack Developer', detail: 'Product, APIs, interfaces', color: '#b79cff' },
  { value: 'enterprise_admin', label: 'Enterprise Admin', detail: 'Governance, policy, teams', color: '#f0b76a' },
];

export default function Auth({ initialMode = 'login' }: { initialMode?: Mode }) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('full_stack_developer');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setLoading(true); setError('');
    try {
      if (mode === 'register') {
        await axios.post(`${API_URL}/api/auth/register`, { email, password, role });
      }
      const body = new URLSearchParams({ username: email, password });
      const response = await axios.post(`${API_URL}/api/auth/token`, body, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
      localStorage.setItem('devorbit-token', response.data.access_token);
      localStorage.setItem('devorbit-role', mode === 'register' ? role : 'full_stack_developer');
      navigate('/');
    } catch (requestError) {
      if (axios.isAxiosError(requestError) && requestError.response?.status === 409) setError('That email is already registered. Try signing in.');
      else setError('Authentication failed. Check your details and confirm the backend is running.');
    } finally { setLoading(false); }
  };

  return <main className="auth-page"><div className="auth-orbit orbit-one" /><div className="auth-orbit orbit-two" /><div className="auth-grid" />
    <section className="auth-shell">
      <div className="auth-pitch"><Link to="/" className="brand-lockup"><span className="brand-mark"><Cpu size={20} /></span> DEVORBIT AI</Link><div className="auth-pitch-copy"><p className="eyebrow">THE CLOUD OPERATING SYSTEM</p><h1>Make the complex feel <em>orbitable.</em></h1><p>One command surface for architecture, automation, security, and the teams shipping it.</p></div><div className="auth-proof"><span><Check size={14} /> Role-aware workspaces</span><span><Check size={14} /> Auditable by default</span><span><Check size={14} /> AWS-ready workflows</span></div></div>
      <div className="auth-card"><div className="auth-card-top"><div><p className="eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'CREATE YOUR ORBIT'}</p><h2>{mode === 'login' ? 'Sign in to command' : 'Start building momentum'}</h2></div><div className="auth-spark"><Sparkles size={18} /></div></div><p className="auth-subtitle">{mode === 'login' ? 'Resume your infrastructure workspace.' : 'Set up your profile for a focused workspace.'}</p>
        <form onSubmit={submit} className="auth-form"><label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required /></label><label>Password<div className="password-field"><input type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="12+ characters" minLength={12} required /><button type="button" onClick={() => setShowPassword(!showPassword)} title={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button></div></label>
          {mode === 'register' && <div className="role-picker"><div className="role-picker-label"><span>Choose your operator profile</span><UserRound size={15} /></div>{roleOptions.map((option) => <button type="button" className={`role-option ${role === option.value ? 'selected' : ''}`} key={option.value} onClick={() => setRole(option.value)}><span className="role-avatar" style={{ background: option.color }}>{option.label.slice(0, 1)}</span><span><strong>{option.label}</strong><small>{option.detail}</small></span>{role === option.value && <Check size={15} />}</button>)}</div>}
          {error && <p className="auth-error"><Shield size={15} />{error}</p>}<button className="auth-submit" disabled={loading}>{loading ? 'Securing workspace...' : mode === 'login' ? 'Enter workspace' : 'Create workspace'}<ArrowRight size={17} /></button>
        </form><p className="auth-switch">{mode === 'login' ? 'New to DevOrbit?' : 'Already have an orbit?'} <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p>
      </div>
    </section>
  </main>;
}
