import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Cpu, Layout, Activity, Shield } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  const links = [
    { name: 'Dashboard', path: '/', icon: Layout },
    { name: 'Agent Pipeline', path: '/orchestrator', icon: Cpu },
    { name: 'System Status', path: '/status', icon: Activity },
  ];

  return (
    <nav className="glass-panel sticky top-0 z-50 px-8 py-4 flex items-center justify-between border-b border-cyan-500/20">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-cyan-500/10 rounded-lg border border-cyan-400/30">
          <Cpu className="w-6 h-6 text-cyan-400 animate-pulse" />
        </div>
        <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent glow-text">
          DevOrbit AI
        </span>
      </div>

      <div className="flex items-center gap-6">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = location.pathname === link.path;
          return (
            <Link
              key={link.path}
              to={link.path}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                isActive
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="font-medium text-sm">{link.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}