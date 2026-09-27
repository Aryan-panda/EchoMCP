import React, { useState } from 'react';
import { Volume2, Play, Sparkles, Sliders, Zap, CheckCircle2 } from 'lucide-react';
import { api, SpeakResponse } from '../services/api';

interface SpeechTesterProps {
  onSpeechGenerated: (res: SpeakResponse) => void;
}

const TAG_DEFINITIONS = [
  { tag: '[happy]', color: 'text-amber-300 bg-amber-500/10 border-amber-500/20 hover:bg-amber-500/20' },
  { tag: '[amused]', color: 'text-cyan-300 bg-cyan-500/10 border-cyan-500/20 hover:bg-cyan-500/20' },
  { tag: '[excited]', color: 'text-violet-300 bg-violet-500/10 border-violet-500/20 hover:bg-violet-500/20' },
  { tag: '[sad]', color: 'text-blue-300 bg-blue-500/10 border-blue-500/20 hover:bg-blue-500/20' },
  { tag: '[angry]', color: 'text-rose-300 bg-rose-500/10 border-rose-500/20 hover:bg-rose-500/20' },
  { tag: '[whisper]', color: 'text-purple-300 bg-purple-500/10 border-purple-500/20 hover:bg-purple-500/20' },
  { tag: '[laughing]', color: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20 hover:bg-emerald-500/20' },
  { tag: '[pause]', color: 'text-orange-300 bg-orange-500/10 border-orange-500/20 hover:bg-orange-500/20' },
];

const PRESETS = [
  {
    label: '🚀 Sci-Fi Mission',
    text: '[excited] We just breached light speed! [pause] [whisper] Engines are holding steady.',
  },
  {
    label: '😄 Witty & Amused',
    text: '[amused] You actually tried that? [laughing] That is genuinely brilliant.',
  },
  {
    label: '🌧️ Somber Story',
    text: '[sad] It was the last transmission from the surface. [pause:750] Silence followed.',
  },
  {
    label: '🤫 Stealth Whisper',
    text: '[whisper] Keep completely still. [pause] They are walking right past us.',
  },
];

export const SpeechTester: React.FC<SpeechTesterProps> = ({ onSpeechGenerated }) => {
  const [text, setText] = useState(PRESETS[0].text);
  const [speed, setSpeed] = useState(1.0);
  const [format, setFormat] = useState<'wav' | 'mp3'>('wav');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSuccess, setLastSuccess] = useState<SpeakResponse | null>(null);

  const insertTag = (tag: string) => {
    setText((prev) => `${prev.trim()} ${tag} `);
  };

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await api.speak({
        text,
        voice_id: '1',
        speed,
        format,
      });
      setLastSuccess(res);
      onSpeechGenerated(res);
    } catch (err: any) {
      setError(err.message || 'Speech generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="bg-slate-900/90 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-xl relative">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <Volume2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">Speech Sandbox & Emotion Tester</h2>
            <p className="text-xs text-slate-400">Test emotion tags and acoustic prosody directly via local synthesis</p>
          </div>
        </div>
        <span className="text-[11px] font-mono text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-md">
          Voice: ID 1
        </span>
      </div>

      <div className="space-y-4">
        {/* Sample Presets */}
        <div>
          <span className="text-xs text-slate-400 block mb-1.5 flex items-center">
            <Sparkles className="w-3 h-3 text-indigo-400 mr-1" />
            Quick Test Presets:
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => setText(p.text)}
                className="text-left p-1.5 px-2.5 bg-slate-950/70 hover:bg-slate-800/80 border border-slate-800 rounded-lg text-xs text-slate-300 hover:text-slate-100 transition-colors truncate"
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Text Area */}
        <div>
          <div className="flex items-center justify-between mb-1.5 text-xs">
            <label className="font-medium text-slate-300">Input Text with Emotion Tags</label>
            <span className="text-slate-500 font-mono">{text.length}/5000</span>
          </div>
          <textarea
            rows={3}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors resize-none leading-relaxed"
            placeholder="Type your response with tags (e.g. [excited], [whisper], [pause])..."
          />
        </div>

        {/* Quick Tag Insert Chips */}
        <div>
          <span className="text-xs text-slate-400 block mb-1.5">Insert Emotion / Prosody Tag:</span>
          <div className="flex flex-wrap gap-1.5">
            {TAG_DEFINITIONS.map((def) => (
              <button
                key={def.tag}
                type="button"
                onClick={() => insertTag(def.tag)}
                className={`px-2.5 py-1 text-xs rounded-lg border font-mono transition-all font-medium ${def.color}`}
              >
                {def.tag}
              </button>
            ))}
          </div>
        </div>

        {/* Controls: Speed & Format */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
          <div>
            <div className="flex justify-between items-center mb-1 text-xs text-slate-400">
              <span className="flex items-center">
                <Sliders className="w-3 h-3 mr-1 text-indigo-400" />
                Playback Speed:
              </span>
              <span className="text-indigo-400 font-mono font-semibold">{speed.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
          </div>

          <div>
            <span className="text-xs text-slate-400 block mb-1">Audio Container Format:</span>
            <div className="flex space-x-2">
              {(['wav', 'mp3'] as const).map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => setFormat(fmt)}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-lg uppercase transition-colors border ${
                    format === fmt
                      ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                  }`}
                >
                  {fmt}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Generate Button */}
        <button
          type="button"
          onClick={handleGenerate}
          disabled={!text.trim() || generating}
          className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-sm font-semibold flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
        >
          {generating ? (
            <>
              <Zap className="w-4 h-4 animate-spin text-white" />
              <span>Synthesizing Speech...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Synthesize & Play Audio</span>
            </>
          )}
        </button>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-300">
            {error}
          </div>
        )}

        {lastSuccess && !generating && (
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-300 flex items-center justify-between">
            <span className="flex items-center">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
              Generated {lastSuccess.audio_id} ({lastSuccess.duration_seconds}s, {lastSuccess.format.toUpperCase()})
            </span>
            <span className="text-[10px] text-emerald-400 font-mono">READY IN STORE</span>
          </div>
        )}
      </div>
    </div>
  );
};
