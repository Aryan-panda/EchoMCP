import React, { useState } from 'react';
import { Mic, Upload, Trash2, CheckCircle2, XCircle, Info } from 'lucide-react';
import { VoiceMetadata, api } from '../services/api';

interface VoicePanelProps {
  voices: VoiceMetadata[];
  onVoiceUpdated: () => void;
}

export const VoicePanel: React.FC<VoicePanelProps> = ({ voices, onVoiceUpdated }) => {
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [transcript, setTranscript] = useState('');
  const [message, setMessage] = useState<{ text: string; error?: boolean } | null>(null);

  const voice1 = voices.find((v) => v.voice_id === '1');
  const isReady = voice1?.status === 'ready';

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('voice_id', '1');
      formData.append('name', 'Voice 1');
      if (transcript.trim()) formData.append('transcript', transcript.trim());

      await api.uploadVoice(formData);
      setMessage({ text: 'Voice 1 reference audio validated and registered successfully.' });
      setSelectedFile(null);
      setTranscript('');
      onVoiceUpdated();
    } catch (err: any) {
      setMessage({ text: err.message || 'Upload failed', error: true });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Reset Voice 1 reference? Previously generated audio recordings will remain safe and playable.')) return;
    try {
      await api.deleteVoice1();
      setMessage({ text: 'Voice 1 reference sample removed.' });
      onVoiceUpdated();
    } catch (err: any) {
      setMessage({ text: err.message || 'Deletion failed', error: true });
    }
  };

  return (
    <div className="bg-slate-900/90 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-xl relative">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <Mic className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">Voice Reference Profile (Voice ID 1)</h2>
            <p className="text-xs text-slate-400">Anchor voice for all Grok conversational speech synthesis</p>
          </div>
        </div>
        <div>
          {isReady ? (
            <span className="flex items-center text-xs font-semibold px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full shadow-sm">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" /> READY
            </span>
          ) : (
            <span className="flex items-center text-xs font-semibold px-2.5 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-full shadow-sm">
              <XCircle className="w-3.5 h-3.5 mr-1 text-amber-400" /> MISSING REFERENCE
            </span>
          )}
        </div>
      </div>

      <div className="space-y-4 text-sm text-slate-300">
        {/* Profile Card */}
        <div className="p-3.5 bg-slate-950/70 rounded-xl border border-slate-800/80 space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
              <span className="text-slate-500 block mb-0.5">Voice ID</span>
              <span className="font-mono text-indigo-300 font-semibold">1</span>
            </div>
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
              <span className="text-slate-500 block mb-0.5">Duration</span>
              <span className="font-mono text-slate-200 font-medium">
                {voice1?.duration_seconds ? `${voice1.duration_seconds}s` : isReady ? '~2.5s' : 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
              <span className="text-slate-500 block mb-0.5">Sample Rate</span>
              <span className="font-mono text-slate-200 font-medium">
                {voice1?.sample_rate ? `${voice1.sample_rate} Hz` : '22050 Hz'}
              </span>
            </div>
            <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
              <span className="text-slate-500 block mb-0.5">Channels</span>
              <span className="font-mono text-slate-200 font-medium">
                {voice1?.channels === 2 ? 'Stereo' : 'Mono (1)'}
              </span>
            </div>
          </div>

          {voice1?.transcript && (
            <div className="pt-2 border-t border-slate-800/60 text-xs flex items-start space-x-1.5">
              <Info className="w-3.5 h-3.5 text-indigo-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-slate-400">Reference Transcript: </span>
                <span className="text-slate-200 italic">"{voice1.transcript}"</span>
              </div>
            </div>
          )}
        </div>

        {/* Upload Form */}
        <form onSubmit={handleUpload} className="space-y-3 pt-1">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Replace Reference Audio Sample (.wav, 0.5s–120s)
            </label>
            <input
              type="file"
              accept=".wav"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer bg-slate-950 p-1.5 rounded-lg border border-slate-800 focus:outline-none"
            />
          </div>

          <div>
            <input
              type="text"
              placeholder="Optional reference transcript text..."
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex space-x-2 pt-1">
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-all shadow-sm"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{uploading ? 'Validating Audio...' : 'Save Voice 1 Reference'}</span>
            </button>

            {isReady && (
              <button
                type="button"
                onClick={handleDelete}
                className="p-2 text-rose-400 hover:text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-lg transition-colors"
                title="Reset Voice 1 reference audio"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        {message && (
          <div
            className={`p-2.5 rounded-lg text-xs border ${
              message.error
                ? 'bg-rose-500/10 text-rose-300 border-rose-500/20'
                : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
            }`}
          >
            {message.text}
          </div>
        )}
      </div>
    </div>
  );
};
