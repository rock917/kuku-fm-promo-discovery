import React from 'react';
import { Scissors, Clock, Volume2, Play } from 'lucide-react';

export default function TimelineScrubber({ segment, durationSec }) {
  if (!segment) return null;

  const startSec = segment.start_sec || 0;
  const endSec = segment.end_sec || durationSec || 40;
  // Scene estimate (at least endSec + 15s to show surrounding context)
  const sceneEstimatedEnd = Math.max(endSec + 20, 90);

  const startPercent = Math.min(100, Math.max(0, (startSec / sceneEstimatedEnd) * 100));
  const widthPercent = Math.min(100 - startPercent, Math.max(5, ((endSec - startSec) / sceneEstimatedEnd) * 100));

  return (
    <div className="bg-slate-100 dark:bg-[#0e1018] border-t border-slate-200 dark:border-[#1a1d29] px-6 py-3 select-none transition-colors">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Left Track Info */}
        <div className="flex items-center space-x-3 text-xs flex-shrink-0">
          <div className="flex items-center space-x-1.5 text-rose-500 dark:text-rose-400 font-mono font-semibold">
            <Scissors className="w-3.5 h-3.5" />
            <span>Clip Window:</span>
          </div>
          <span className="font-mono bg-white dark:bg-[#181c2b] px-2 py-0.5 rounded text-slate-700 dark:text-gray-200 border border-slate-200 dark:border-[#262f44] shadow-sm">
            {segment.start_ts || '00:00.00'} → {segment.end_ts || '00:43.90'}
          </span>
          <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-mono font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {durationSec ? durationSec.toFixed(1) : (endSec - startSec).toFixed(1)}s
          </span>
        </div>

        {/* Center Interactive Timeline Bar */}
        <div className="flex-1 w-full max-w-2xl px-2">
          <div className="relative h-7 bg-slate-200/80 dark:bg-[#141724] rounded-lg border border-slate-300 dark:border-[#23293c] overflow-hidden flex items-center">
            {/* Waveform graphic pattern in background */}
            <div className="absolute inset-0 opacity-20 flex items-center justify-around pointer-events-none">
              {Array.from({ length: 48 }).map((_, i) => (
                <div 
                  key={i} 
                  className="w-0.5 bg-slate-600 dark:bg-gray-400 rounded-full"
                  style={{ height: `${20 + (Math.sin(i * 0.8) * 40 + (i % 3) * 15)}%` }}
                />
              ))}
            </div>

            {/* Glowing Active Cut Block */}
            <div 
              className="absolute h-full bg-gradient-to-r from-rose-500/30 via-amber-500/30 to-rose-500/30 border-x-2 border-rose-500 flex items-center justify-between px-1"
              style={{
                left: `${startPercent}%`,
                width: `${widthPercent}%`,
              }}
            >
              <div className="w-1.5 h-3.5 bg-rose-500 rounded-sm shadow-sm" />
              <span className="text-[10px] font-mono font-extrabold text-amber-700 dark:text-amber-300 drop-shadow hidden md:inline">
                ACTIVE CUT
              </span>
              <div className="w-1.5 h-3.5 bg-rose-500 rounded-sm shadow-sm" />
            </div>
          </div>

          {/* Time markers */}
          <div className="flex justify-between text-[10px] font-mono text-slate-500 dark:text-gray-500 mt-1 px-1">
            <span>00:00.00 (Scene Start)</span>
            <span className="text-slate-500 dark:text-gray-400">Target Range: 20s–60s (Peak 25s–45s)</span>
            <span>{Math.floor(sceneEstimatedEnd / 60)}:{(sceneEstimatedEnd % 60).toFixed(0).padStart(2, '0')}.00</span>
          </div>
        </div>

        {/* Right Scene Context */}
        <div className="text-right text-[11px] text-slate-500 dark:text-gray-400 hidden xl:block flex-shrink-0">
          <span className="font-semibold text-slate-700 dark:text-gray-300">Ep {segment.episode_number} Scene {segment.scene_number}</span>
          <p className="text-[10px] text-slate-400 dark:text-gray-500 truncate max-w-[200px]">{segment.scene_heading}</p>
        </div>
      </div>
    </div>
  );
}
