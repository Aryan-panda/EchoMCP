import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, Download, Volume2, RotateCcw } from 'lucide-react';
import { AudioItem, api } from '../services/api';

interface AudioPlayerProps {
  currentAudio: AudioItem | null;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ currentAudio }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    if (audioRef.current && currentAudio) {
      audioRef.current.load();
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [currentAudio?.audio_id]);

  if (!currentAudio) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex items-center justify-center text-slate-500 text-sm">
        Select an audio response from history to replay.
      </div>
    );
  }

  const audioUrl = api.getAudioFileUrl(currentAudio.audio_id);

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

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-5 shadow-lg relative overflow-hidden">
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
        onLoadedMetadata={() => setDuration(audioRef.current?.duration || currentAudio.duration_seconds)}
        onEnded={() => setIsPlaying(false)}
      />

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Volume2 className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Playing: <span className="font-mono text-indigo-300">{currentAudio.audio_id}</span>
          </h3>
        </div>
        <a
          href={audioUrl}
          download={`${currentAudio.audio_id}.${currentAudio.format}`}
          className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-100 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
          title="Download audio file"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Save</span>
        </a>
      </div>

      <p className="text-xs text-slate-300 italic mb-4 line-clamp-2 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
        "{currentAudio.text}"
      </p>

      {/* Scrub Bar & Controls */}
      <div className="space-y-2">
        <input
          type="range"
          min="0"
          max={duration || 1}
          step="0.05"
          value={currentTime}
          onChange={handleSeek}
          className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
        />

        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>{formatTime(currentTime)}</span>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                if (audioRef.current) audioRef.current.currentTime = 0;
              }}
              className="p-1.5 hover:text-slate-200"
              title="Restart"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={togglePlay}
              className="p-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full transition-colors shadow-md shadow-indigo-600/30"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>
          </div>
          <span>{formatTime(duration || currentAudio.duration_seconds)}</span>
        </div>
      </div>
    </div>
  );
};
