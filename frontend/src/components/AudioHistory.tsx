import React from 'react';
import { History, Play, Trash2, Clock } from 'lucide-react';
import { AudioItem, api } from '../services/api';

interface AudioHistoryProps {
  history: AudioItem[];
  currentAudio: AudioItem | null;
  onSelectAudio: (item: AudioItem) => void;
  onItemDeleted: () => void;
}

export const AudioHistory: React.FC<AudioHistoryProps> = ({
  history,
  currentAudio,
  onSelectAudio,
  onItemDeleted,
}) => {
  const handleDelete = async (e: React.MouseEvent, audioId: string) => {
    e.stopPropagation();
    if (!window.confirm(`Delete audio record ${audioId}?`)) return;
    try {
      await api.deleteAudio(audioId);
      onItemDeleted();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <History className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-slate-100">Persistent Audio History</h2>
        </div>
        <span className="text-xs text-slate-400">{history.length} records</span>
      </div>

      {history.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
          No generated speech records yet. Synthesize speech in the sandbox or trigger via Grok!
        </div>
      ) : (
        <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
          {history.map((item) => {
            const isSelected = currentAudio?.audio_id === item.audio_id;
            return (
              <div
                key={item.audio_id}
                onClick={() => onSelectAudio(item)}
                className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500/50 shadow-sm'
                    : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex-1 min-w-0 mr-3">
                  <div className="flex items-center space-x-2 text-xs mb-1">
                    <span className="font-mono text-indigo-300 font-medium">{item.audio_id}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400 flex items-center">
                      <Clock className="w-3 h-3 mr-0.5" />
                      {formatDate(item.created_at)}
                    </span>
                    <span className="text-slate-500">•</span>
                    <span className="text-indigo-400 font-medium">{item.duration_seconds}s</span>
                  </div>
                  <p className="text-xs text-slate-200 truncate">{item.text}</p>
                </div>

                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={() => onSelectAudio(item)}
                    className="p-1.5 text-indigo-400 hover:text-white hover:bg-indigo-600 rounded-md transition-colors"
                    title="Play audio"
                  >
                    <Play className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, item.audio_id)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-colors"
                    title="Delete record"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
