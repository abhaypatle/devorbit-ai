import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Play, Cpu, CheckCircle2, Code } from 'lucide-react';

export default function Orchestrator() {
  const [projectId, setProjectId] = useState('devorbit-prod-01');
  const [prompt, setPrompt] = useState(
    'Design a high-availability AWS architecture for a scalable web application with auto scaling and RDS PostgreSQL.'
  );
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  const handleRun = async (e) => {
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
      alert('Backend connection error! Check if FastAPI server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
      <div className="glass-panel p-8 rounded-2xl border border-cyan-500/30">
        <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
          <Cpu className="text-cyan-400" /> Multi-Agent Orchestrator Workspace
        </h2>

        <form onSubmit={handleRun} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">Project Identifier</label>
            <input
              type="text"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full bg-slate-900/80 border border-gray-700 rounded-lg p-3 text-white focus:border-cyan-400 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">System Architecture Spec</label>
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full bg-slate-900/80 border border-gray-700 rounded-lg p-3 text-white focus:border-cyan-400 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 font-extrabold rounded-lg hover:brightness-110 transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <span className="animate-pulse">Agents Executing Pipeline...</span>
            ) : (
              <>
                <Play className="w-5 h-5 fill-current" /> Execute Multi-Agent Graph
              </>
            )}
          </button>
        </form>
      </div>

      {/* Output Display */}
      <div className="space-y-4">
        {messages.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.15 }}
            className={`glass-panel p-6 rounded-xl border-l-4 ${
              msg.role === 'human' ? 'border-l-cyan-400' : 'border-l-emerald-400'
            }`}
          >
            <div className="flex items-center gap-2 font-bold mb-3 text-sm text-cyan-300">
              {msg.role === 'human' ? <CheckCircle2 className="w-4 h-4" /> : <Code className="w-4 h-4 text-emerald-400" />}
              {msg.role.toUpperCase()}
            </div>
            <pre className="whitespace-pre-wrap font-mono text-sm text-gray-200 leading-relaxed">
              {msg.content}
            </pre>
          </motion.div>
        ))}
      </div>
    </div>
  );
}