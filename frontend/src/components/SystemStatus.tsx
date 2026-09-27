import React from 'react';
import { Activity, AlertTriangle, RefreshCw, Server, Cpu, Mic, HardDrive } from 'lucide-react';
import { ReadinessResponse } from '../services/api';

interface SystemStatusProps {
  status: ReadinessResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({ status, loading, onRefresh }) => {
  const items = [
    { label: 'MCP Server', icon: Server, ready: status?.mcp ?? false, desc: 'Port 3001 JSON-RPC' },
    { label: 'TTS Engine', icon: Cpu, ready: status?.tts ?? false, desc: 'CosyVoice Synthesizer' },
    { label: 'Voice ID 1', icon: Mic, ready: status?.voice_1 ?? false, desc: 'Reference Profile' },
    { label: 'Audio Store', icon: HardDrive, ready: status?.audio_store ?? false, desc: 'Dated Storage & Metadata' },
  ];

  return (
    <div className="bg-slate-900/90 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">System Diagnostics & Readiness</h2>
            <p className="text-xs text-slate-400">Autonomous health monitoring for MCP and local speech subsystem</p>
          </div>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs text-slate-300 hover:text-slate-100 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 rounded-lg transition-colors shadow-sm disabled:opacity-50"
          title="Poll system health"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className={`p-3.5 rounded-xl border transition-all ${
                item.ready
                  ? 'bg-slate-950/70 border-emerald-500/20 shadow-sm'
                  : 'bg-slate-950/70 border-amber-500/20'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Icon className={`w-4 h-4 ${item.ready ? 'text-indigo-400' : 'text-slate-500'}`} />
                  <span className="text-xs font-semibold text-slate-200">{item.label}</span>
                </div>
                {item.ready ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
                    ONLINE
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    OFFLINE
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400">{item.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
