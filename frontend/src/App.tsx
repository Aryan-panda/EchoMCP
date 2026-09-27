import React, { useState, useEffect } from 'react';
import { Radio } from 'lucide-react';
import { api, ReadinessResponse, VoiceMetadata, AudioItem, SpeakResponse } from './services/api';
import { SystemStatus } from './components/SystemStatus';
import { VoicePanel } from './components/VoicePanel';
import { SpeechTester } from './components/SpeechTester';
import { AudioPlayer } from './components/AudioPlayer';
import { AudioHistory } from './components/AudioHistory';

export const App: React.FC = () => {
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [voices, setVoices] = useState<VoiceMetadata[]>([]);
  const [audioHistory, setAudioHistory] = useState<AudioItem[]>([]);
  const [currentAudio, setCurrentAudio] = useState<AudioItem | null>(null);

  const fetchStatus = async () => {
    setLoadingStatus(true);
    try {
      const data = await api.getReadiness();
      setReadiness(data);
    } catch {
      setReadiness(null);
    } finally {
      setLoadingStatus(false);
    }
  };

  const fetchVoices = async () => {
    try {
      const data = await api.listVoices();
      setVoices(data);
    } catch {
      setVoices([]);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await api.listAudio(1, 50);
      setAudioHistory(res.items);
      if (res.items.length > 0 && !currentAudio) {
        setCurrentAudio(res.items[0]);
      }
    } catch {
      setAudioHistory([]);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchVoices();
    fetchHistory();

    // Polling interval every 5 seconds for status & new audio
    const interval = setInterval(() => {
      fetchStatus();
      fetchHistory();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSpeechGenerated = (res: SpeakResponse) => {
    fetchHistory();
    const newItem: AudioItem = {
      audio_id: res.audio_id,
      text: 'Newly generated speech',
      voice_id: '1',
      format: (res.format as 'wav' | 'mp3') || 'wav',
      duration_seconds: res.duration_seconds,
      sample_rate: 22050,
      channels: 1,
      created_at: res.created_at,
      audio_url: res.audio_url,
      file_url: `${res.audio_url}/file`,
    };
    setCurrentAudio(newItem);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">EchoMCP</h1>
              <p className="text-xs text-slate-400">Grok MCP Bridge for Custom Voice</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 font-mono text-slate-300">
              MCP Port: 3001
            </span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <SystemStatus
          status={readiness}
          loading={loadingStatus}
          onRefresh={fetchStatus}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Voice 1 & Speech Sandbox */}
          <div className="space-y-6">
            <VoicePanel
              voices={voices}
              onVoiceUpdated={() => {
                fetchVoices();
                fetchStatus();
              }}
            />
            <SpeechTester onSpeechGenerated={handleSpeechGenerated} />
          </div>

          {/* Right Column: Audio Player & Replay History */}
          <div className="space-y-6">
            <AudioPlayer currentAudio={currentAudio} />
            <AudioHistory
              history={audioHistory}
              currentAudio={currentAudio}
              onSelectAudio={(item) => setCurrentAudio(item)}
              onItemDeleted={fetchHistory}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-4 px-6 text-center text-xs text-slate-500">
        EchoMCP System Architecture — Grok remains the brain. EchoMCP provides the voice.
      </footer>
    </div>
  );
};
export default App;
