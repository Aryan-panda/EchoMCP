import React, { useState } from 'react';
import { History, Play, Trash2, Clock, Search, ShieldAlert } from 'lucide-react';
import { AudioItem, api } from '../services/api';

interface AudioHistoryProps {
  history: AudioItem[];
  currentAudio: AudioItem | null;
  onSelectAudio: (item: AudioItem) => void;
  onItemDeleted: () => void;
  onCleanupTriggered: () => void;
}

export const AudioHistory: React.FC<AudioHistoryProps> = ({
  history,
  currentAudio,
  onSelectAudio,
  onItemDeleted,
  onCleanupTriggered,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [cleaningUp, setCleaningUp] = useState(false);
  const [cleanupMessage, setCleanupMessage] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, audioId: string) => {
    e.stopPropagation();
    if (!window.confirm(`Delete audio record ${audioId} from persistent storage?`)) return;
    try {
      await api.deleteAudio(audioId);
      onItemDeleted();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleCleanup = async () => {
    const daysStr = prompt('Enter retention cutoff in days (records older than this will be deleted):', '7');
    if (daysStr === null) return;
    const days = parseInt(daysStr, 10);
    if (isNaN(days) || days < 0) {
      alert('Please enter a valid positive number of days.');
      return;
    }

    setCleaningUp(true);
    setCleanupMessage(null);
    try {
      const res = await api.cleanupAudio(days);
      setCleanupMessage(`Retention cleanup complete: ${res.deleted_count} expired records removed.`);
      onCleanupTriggered();
    } catch (err: any) {
      setCleanupMessage(`Cleanup failed: ${err.message}`);
    } finally {
      setCleaningUp(false);
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

  const filteredHistory = history.filter((item) =>
    item.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.audio_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-slate-900/90 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-xl relative">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">Conversation Audio Store & History</h2>
            <p className="text-xs text-slate-400">Sequential multi-turn speech recordings indexed by timestamp</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleCleanup}
            disabled={cleaningUp}
            className="flex items-center space-x-1.5 px-2.5 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700/60 rounded-lg transition-colors shadow-sm disabled:opacity-50"
            title="Purge expired recordings by retention days"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            <span>{cleaningUp ? 'Pruning...' : 'Retention Cleanup'}</span>
          </button>
          <span className="text-xs font-mono px-2 py-1 bg-slate-950 border border-slate-800 rounded-lg text-slate-400">
            {history.length} records
          </span>
        </div>
      </div>

      {cleanupMessage && (
        <div className="mb-3 p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-xs text-indigo-300">
          {cleanupMessage}
        </div>
      )}

      {/* Search Filter */}
      <div className="mb-3 relative">
        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Filter speech history by text or ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
        />
      </div>

      {/* History List */}
      {filteredHistory.length === 0 ? (
        <div className="py-10 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
          {history.length === 0
            ? 'No generated speech records in persistent store yet. Test in the sandbox or trigger via Grok MCP!'
            : 'No records matching your search query.'}
        </div>
      ) : (
        <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
          {filteredHistory.map((item) => {
            const isSelected = currentAudio?.audio_id === item.audio_id;
            return (
              <div
                key={item.audio_id}
                onClick={() => onSelectAudio(item)}
                className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500/60 shadow-md shadow-indigo-950/20'
                    : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex-1 min-w-0 mr-3">
                  <div className="flex items-center space-x-2 text-xs mb-1">
                    <span className="font-mono text-indigo-300 font-semibold">{item.audio_id}</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400 flex items-center">
                      <Clock className="w-3 h-3 mr-0.5" />
                      {formatDate(item.created_at)}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-emerald-400 font-medium">{item.duration_seconds}s</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-[10px] text-slate-400 uppercase font-mono">{item.format}</span>
                  </div>
                  <p className="text-xs text-slate-200 truncate leading-relaxed">"{item.text}"</p>
                </div>

                <div className="flex items-center space-x-1.5 flex-shrink-0">
                  <button
                    onClick={() => onSelectAudio(item)}
                    className="p-1.5 text-indigo-400 hover:text-white hover:bg-indigo-600 rounded-lg transition-colors"
                    title="Play turn"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, item.audio_id)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
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
