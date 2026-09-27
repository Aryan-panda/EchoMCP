import React, { useState } from 'react';
import { Mic, Upload, Trash2, CheckCircle2, XCircle } from 'lucide-react';
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
      if (transcript) formData.append('transcript', transcript);

      await api.uploadVoice(formData);
      setMessage({ text: 'Voice 1 reference uploaded successfully.' });
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
    if (!window.confirm('Delete Voice 1 reference profile? Previously generated audio will be retained.')) return;
    try {
      await api.deleteVoice1();
      setMessage({ text: 'Voice 1 profile deleted.' });
      onVoiceUpdated();
    } catch (err: any) {
      setMessage({ text: err.message || 'Deletion failed', error: true });
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Mic className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-slate-100">Voice Profile (Voice ID 1)</h2>
        </div>
        <div className="flex items-center space-x-2">
          {isReady ? (
            <span className="flex items-center text-xs font-semibold px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> READY
            </span>
          ) : (
            <span className="flex items-center text-xs font-semibold px-2.5 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full">
              <XCircle className="w-3.5 h-3.5 mr-1" /> MISSING REFERENCE
            </span>
          )}
        </div>
      </div>

      <div className="space-y-4 text-sm text-slate-300">
        <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 space-y-1">
          <div className="flex justify-between">
            <span className="text-slate-400">Target Voice ID:</span>
            <span className="font-mono text-indigo-300 font-semibold">1</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Reference File:</span>
            <span className="font-mono text-slate-200">{voice1?.reference_file || 'None'}</span>
          </div>
          {voice1?.transcript && (
            <div className="pt-1 border-t border-slate-800/60">
              <span className="text-xs text-slate-400">Transcript: </span>
              <span className="text-xs italic text-slate-200">"{voice1.transcript}"</span>
            </div>
          )}
        </div>

        {/* Upload Form */}
        <form onSubmit={handleUpload} className="space-y-3 pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Upload New Reference Sample (.wav)
            </label>
            <input
              type="file"
              accept=".wav"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
            />
          </div>

          <div>
            <input
              type="text"
              placeholder="Optional reference transcript..."
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex space-x-2 pt-1">
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{uploading ? 'Uploading...' : 'Save Voice 1 Reference'}</span>
            </button>

            {isReady && (
              <button
                type="button"
                onClick={handleDelete}
                className="p-2 text-rose-400 hover:text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 rounded-lg transition-colors"
                title="Delete Voice 1 reference"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>

        {message && (
          <p className={`text-xs ${message.error ? 'text-rose-400' : 'text-emerald-400'}`}>
            {message.text}
          </p>
        )}
      </div>
    </div>
  );
};
