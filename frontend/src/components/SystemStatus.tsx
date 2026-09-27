import React from 'react';
import { Activity, CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { ReadinessResponse } from '../services/api';

interface SystemStatusProps {
  status: ReadinessResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({ status, loading, onRefresh }) => {
  const items = [
    { label: 'MCP Server', ready: status?.mcp ?? false },
    { label: 'TTS Engine', ready: status?.tts ?? false },
    { label: 'Voice ID 1', ready: status?.voice_1 ?? false },
    { label: 'Audio Store', ready: status?.audio_store ?? false },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-slate-100">System Diagnostics</h2>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-1.5 text-slate-400 hover:text-slate-100 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          title="Refresh status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {items.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between p-3 bg-slate-950/60 rounded-lg border border-slate-800/80"
          >
            <span className="text-xs font-medium text-slate-300">{item.label}</span>
            {item.ready ? (
              <span className="flex items-center text-xs font-semibold text-emerald-400">
                <CheckCircle className="w-3.5 h-3.5 mr-1" /> ONLINE
              </span>
            ) : (
              <span className="flex items-center text-xs font-semibold text-amber-400">
                <AlertTriangle className="w-3.5 h-3.5 mr-1" /> OFFLINE
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
