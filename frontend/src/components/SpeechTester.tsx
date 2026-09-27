import React, { useState } from 'react';
import { Volume2, Play, Sparkles } from 'lucide-react';
import { api, SpeakResponse } from '../services/api';

interface SpeechTesterProps {
  onSpeechGenerated: (res: SpeakResponse) => void;
}

const TAGS = ['[amused]', '[excited]', '[happy]', '[whisper]', '[laughing]', '[sad]', '[angry]', '[pause]'];

export const SpeechTester: React.FC<SpeechTesterProps> = ({ onSpeechGenerated }) => {
  const [text, setText] = useState('[amused] Oh, come on. Did you really think that would work? [laughing] That is actually brilliant.');
  const [speed, setSpeed] = useState(1.0);
  const [format, setFormat] = useState<'wav' | 'mp3'>('wav');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const insertTag = (tag: string) => {
    setText((prev) => `${prev} ${tag} `);
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
      onSpeechGenerated(res);
    } catch (err: any) {
      setError(err.message || 'Speech generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Volume2 className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-slate-100">Speech Sandbox</h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">Targets Voice ID 1</span>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
            <span>Input Text with Emotion Tags</span>
            <span className="text-slate-500">{text.length}/5000</span>
          </label>
          <textarea
            rows={3}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
            placeholder="Type response text or click emotion tags below..."
          />
        </div>

        {/* Emotion Tag Quick-Insert Chips */}
        <div>
          <span className="text-xs text-slate-400 block mb-1.5">Quick Insert Emotion Tags:</span>
          <div className="flex flex-wrap gap-1.5">
            {TAGS.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => insertTag(tag)}
                className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-indigo-300 text-xs rounded-md border border-slate-700/60 transition-colors font-mono"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        {/* Controls */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              Speech Speed: <span className="text-indigo-400 font-semibold">{speed.toFixed(1)}x</span>
            </label>
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
            <label className="block text-xs text-slate-400 mb-1">Audio Format</label>
            <div className="flex space-x-2">
              {(['wav', 'mp3'] as const).map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => setFormat(fmt)}
                  className={`flex-1 py-1.5 text-xs font-semibold rounded-lg uppercase transition-colors ${
                    format === fmt
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}
                >
                  {fmt}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating || !text.trim()}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm rounded-lg transition-colors shadow-md shadow-indigo-600/20"
        >
          {generating ? (
            <Sparkles className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          <span>{generating ? 'Synthesizing Audio...' : 'Generate Speech'}</span>
        </button>

        {error && <p className="text-xs text-rose-400 mt-2">{error}</p>}
      </div>
    </div>
  );
};
