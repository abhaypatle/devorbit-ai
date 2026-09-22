import React from 'react';
import { Activity, CheckCircle, Server } from 'lucide-react';

export default function Status() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12 space-y-6">
      <h2 className="text-3xl font-bold text-white flex items-center gap-3">
        <Activity className="text-cyan-400" /> Agent Network Status
      </h2>

      <div className="grid gap-4">
        {[
          { name: 'FastAPI Backend Core', status: 'Online', port: '8000' },
          { name: 'LangGraph Orchestrator Engine', status: 'Operational', port: 'Internal' },
          { name: 'Amazon Bedrock Client / Mock Engine', status: 'Active', port: 'AWS US-East-1' },
        ].map((item, idx) => (
          <div key={idx} className="glass-panel p-5 rounded-xl flex items-center justify-between border border-white/5">
            <div className="flex items-center gap-3">
              <Server className="text-gray-400" />
              <div>
                <h4 className="font-semibold text-white">{item.name}</h4>
                <span className="text-xs text-gray-400">Endpoint/Region: {item.port}</span>
              </div>
            </div>
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
              <CheckCircle className="w-4 h-4" /> {item.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}