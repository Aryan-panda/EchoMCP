import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, Download, Volume2, RotateCcw, FastForward } from 'lucide-react';
import { AudioItem, api } from '../services/api';

interface AudioPlayerProps {
  currentAudio: AudioItem | null;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ currentAudio }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);

  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    if (audioRef.current && currentAudio) {
      audioRef.current.playbackRate = playbackRate;
      audioRef.current.load();
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [currentAudio?.audio_id]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleRestart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleRateChange = (rate: number) => {
    setPlaybackRate(rate);
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  if (!currentAudio) {
    return (
      <div className="bg-slate-900/90 backdrop-blur border border-slate-800 rounded-xl p-8 shadow-xl flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-500 mb-3">
          <Volume2 className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-300 mb-1">No Active Audio Turn Selected</h3>
        <p className="text-xs text-slate-500 max-w-xs">
          Select any conversation turn from history below or synthesize a new phrase in the sandbox.
        </p>
      </div>
    );
  }

  const audioUrl = api.getAudioFileUrl(currentAudio.audio_id);

  return (
    <div className="bg-slate-900/90 backdrop-blur border border-indigo-500/30 rounded-xl p-5 shadow-2xl relative overflow-hidden">
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
        onLoadedMetadata={() => setDuration(audioRef.current?.duration || currentAudio.duration_seconds)}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Header Info */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <Volume2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-200">
              Playing Turn: <span className="font-mono text-indigo-300">{currentAudio.audio_id}</span>
            </h3>
            <span className="text-[11px] text-slate-400">
              Format: {currentAudio.format.toUpperCase()} • {currentAudio.sample_rate}Hz • {currentAudio.duration_seconds}s
            </span>
          </div>
        </div>
        <a
          href={audioUrl}
          download={`${currentAudio.audio_id}.${currentAudio.format}`}
          className="flex items-center space-x-1 text-xs text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700/60 transition-colors shadow-sm"
          title="Download audio file"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Save File</span>
        </a>
      </div>

      {/* Spoken Text Quote */}
      <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800/80 mb-4">
        <p className="text-xs text-slate-200 italic leading-relaxed line-clamp-3">
          "{currentAudio.text}"
        </p>
      </div>

      {/* Animated Waveform Simulation */}
      <div className="flex items-center justify-center space-x-1 h-8 mb-3 bg-slate-950/40 rounded-lg py-1">
        {[40, 70, 30, 90, 60, 100, 50, 80, 45, 95, 65, 85, 35, 75, 55, 90, 40, 60].map((height, i) => (
          <div
            key={i}
            className={`w-1 rounded-full transition-all duration-150 ${
              isPlaying
                ? 'bg-indigo-400 animate-pulse'
                : 'bg-slate-700'
            }`}
            style={{
              height: isPlaying ? `${Math.max(15, (height * (i % 2 === 0 ? 1 : 0.7)))}%` : '20%',
              animationDelay: `${i * 60}ms`,
            }}
          />
        ))}
      </div>

      {/* Scrub Bar & Time Counters */}
      <div className="space-y-1.5 mb-4">
        <input
          type="range"
          min="0"
          max={duration || 1}
          step="0.05"
          value={currentTime}
          onChange={handleSeek}
          className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
        />
        <div className="flex justify-between text-[11px] font-mono text-slate-400">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Playback Controls & Rate */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center space-x-2">
          <button
            onClick={togglePlay}
            className="p-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full shadow-lg shadow-indigo-600/30 transition-transform active:scale-95 cursor-pointer"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="w-5 h-5 fill-white" /> : <Play className="w-5 h-5 fill-white translate-x-0.5" />}
          </button>
          <button
            onClick={handleRestart}
            className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
            title="Replay from start"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Speed Multiplier Pill */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[11px]">
          <span className="text-slate-500 px-1.5 flex items-center">
            <FastForward className="w-3 h-3 mr-0.5" /> Rate:
          </span>
          {[0.75, 1.0, 1.25, 1.5].map((rate) => (
            <button
              key={rate}
              onClick={() => handleRateChange(rate)}
              className={`px-2 py-0.5 rounded font-mono font-medium transition-colors ${
                playbackRate === rate
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {rate}x
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
