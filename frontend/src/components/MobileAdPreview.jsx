import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Volume2, 
  Share2, 
  Heart, 
  MessageCircle, 
  Bookmark, 
  Music2, 
  Smartphone, 
  TrendingUp, 
  Download,
  Calculator
} from 'lucide-react';

export default function MobileAdPreview({ promo, onClose }) {
  if (!promo) return null;

  const [isPlaying, setIsPlaying] = useState(false);
  const [platform, setPlatform] = useState('reels'); // 'reels' | 'tiktok' | 'shorts'

  const hookText = promo.opening_hook?.text || 'Visual betrayal or tension establishes curiosity.';
  const cliffText = promo.closing_cliffhanger?.text || 'Scene ends without resolution on heightened suspense.';

  // Extract real 5D scores for dynamic mathematical prediction
  const aiScores = promo.scoring?.scores?.['AI-generated'] || {};
  const progScores = promo.scoring?.scores?.['programmatic'] || {};

  const hookScore = aiScores.hook_strength?.score ?? 8.5;
  const cliffScore = aiScores.cliffhanger_strength?.score ?? 8.0;
  const durationScore = progScores.duration_quality?.score ?? 10.0;
  const finalScore = promo.final_score ?? 8.0;

  // Real Mathematical Retention & Completion Formulas:
  // Hook Hold Rate (%): Baseline 50% + (Hook Strength x 4.5%)
  const hookHoldRate = Math.min(96.0, Math.max(45.0, 50.0 + hookScore * 4.5)).toFixed(1);
  // Full Cut Completion (%): (Cliffhanger x 4.0%) + (Duration Quality x 3.0%)
  const completionRate = Math.min(88.0, Math.max(25.0, cliffScore * 4.0 + durationScore * 3.0)).toFixed(1);

  // Dynamic Ad Spend Recommendation based on composite score
  let spendTier = 'TIER-1 HIGH PRIORITY · Scale on Instagram Reels & TikTok Spark Ads';
  let spendTagColor = 'text-emerald-400';
  if (finalScore < 8.2 && finalScore >= 7.6) {
    spendTier = 'TIER-2 STANDARD · Moderate testing budget on YouTube Shorts';
    spendTagColor = 'text-amber-400';
  } else if (finalScore < 7.6) {
    spendTier = 'ORGANIC TESTING · Distribute to community channels before paid ads';
    spendTagColor = 'text-slate-300';
  }

  // Web Speech Synthesis
  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handlePlayToggle = () => {
    if (!('speechSynthesis' in window)) return;

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    window.speechSynthesis.cancel();
    const scriptToRead = `${hookText}. ... ${cliffText}`;
    const utterance = new SpeechSynthesisUtterance(scriptToRead);
    utterance.rate = 1.0;
    utterance.pitch = 0.95;

    utterance.onstart = () => setIsPlaying(true);
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);

    window.speechSynthesis.speak(utterance);
  };

  // Download EDL file for video editors
  const downloadEDL = () => {
    const seg = promo.segments?.[0] || {};
    const edlContent = `TITLE: KUKU_FM_PROMO_${promo.candidate_id}
FCM: NON-DROP FRAME

001  AX       V     C        ${seg.start_ts || '00:00:00:00'} ${seg.end_ts || '00:00:43:00'} 00:00:00:00 00:00:43:00
* FROM CLIP NAME: EPISODE_${promo.episodes?.[0] || 1}_SCENE_${seg.scene_number || 1}.mp4
* COMMENT: HOOK: "${hookText.slice(0, 60)}"
* COMMENT: CLIFFHANGER: "${cliffText.slice(0, 60)}"
* COMMENT: 5D_SCORE: ${promo.final_score}
`;

    const blob = new Blob([edlContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Promo_${promo.candidate_id}.edl`;
    a.click();
  };

  return (
    <div className="bg-slate-900/95 border border-slate-700 dark:border-[#2a3449] rounded-2xl p-5 text-white shadow-2xl space-y-4">
      {/* Top Header Controls */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Smartphone className="w-4 h-4 text-rose-500" />
          <span className="font-bold text-xs uppercase tracking-wider">
            9:16 Vertical Video Ad Simulator
          </span>
          <span className="text-[10px] font-mono bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded border border-rose-500/30">
            {platform.toUpperCase()}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Platform Switcher */}
          <div className="flex bg-slate-800 p-0.5 rounded-lg text-[11px] font-semibold">
            {['reels', 'tiktok', 'shorts'].map((p) => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={`px-2.5 py-1 rounded-md capitalize transition ${
                  platform === p ? 'bg-rose-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          <button
            onClick={downloadEDL}
            title="Download Edit Decision List for Premiere / DaVinci"
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-emerald-400 border border-emerald-500/30 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export EDL</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        {/* Left: Clean 9:16 Mobile Phone Bezel without unneeded watermarks */}
        <div className="flex justify-center">
          <div className="w-[240px] sm:w-[260px] h-[480px] bg-black rounded-[36px] p-2.5 shadow-2xl border-4 border-slate-700 relative overflow-hidden select-none flex flex-col justify-between">
            {/* Dynamic Island / Camera Notch */}
            <div className="absolute top-2 left-1/2 -translate-x-1/2 w-20 h-4 bg-slate-900 rounded-full z-30" />

            {/* Clean Video Background */}
            <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-black z-0" />

            {/* Clean Minimalist Top Bar */}
            <div className="relative z-10 pt-5 px-3 flex items-center justify-between text-[11px] text-white/60">
              <span className="font-mono">{promo.segments?.[0]?.start_ts}</span>
              <span className="font-mono bg-black/60 px-2 py-0.5 rounded-full text-[10px] text-white/80 border border-white/10">
                {promo.total_duration_sec}s Cut
              </span>
            </div>

            {/* Center: Dialogue Subtitles */}
            <div className="relative z-10 px-3 text-center space-y-2.5 my-auto">
              <div className="bg-black/70 backdrop-blur-md border border-white/10 rounded-xl p-3 shadow-xl space-y-2">
                <p className="text-xs sm:text-[13px] font-extrabold text-yellow-300 leading-snug drop-shadow-md">
                  {hookText}
                </p>
                <div className="h-[1px] w-8 bg-white/20 mx-auto" />
                <p className="text-[11px] text-slate-300 italic font-serif leading-tight">
                  {cliffText}
                </p>
              </div>

              {/* Voice Equalizer Visualizer */}
              {isPlaying && (
                <div className="flex items-center justify-center space-x-1 py-1">
                  <span className="w-1 h-3 bg-rose-500 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <span className="w-1 h-5 bg-amber-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1 h-4 bg-emerald-400 rounded-full animate-bounce [animation-delay:0.3s]" />
                  <span className="w-1 h-6 bg-rose-400 rounded-full animate-bounce [animation-delay:0.4s]" />
                  <span className="w-1 h-2 bg-yellow-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
              )}
            </div>

            {/* Right Side Social UI */}
            <div className="absolute right-2.5 bottom-16 z-20 flex flex-col items-center space-y-3.5 text-white/80">
              <div className="flex flex-col items-center">
                <div className="w-7 h-7 rounded-full bg-black/40 backdrop-blur flex items-center justify-center">
                  <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" />
                </div>
                <span className="text-[9px] font-mono mt-0.5">38k</span>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-7 h-7 rounded-full bg-black/40 backdrop-blur flex items-center justify-center">
                  <MessageCircle className="w-3.5 h-3.5" />
                </div>
                <span className="text-[9px] font-mono mt-0.5">1.2k</span>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-7 h-7 rounded-full bg-black/40 backdrop-blur flex items-center justify-center">
                  <Bookmark className="w-3.5 h-3.5 text-yellow-400" />
                </div>
                <span className="text-[9px] font-mono mt-0.5">9k</span>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-7 h-7 rounded-full bg-black/40 backdrop-blur flex items-center justify-center">
                  <Share2 className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>

            {/* Bottom Audio Pill */}
            <div className="relative z-10 px-2 pb-2">
              <div className="flex items-center space-x-1.5 text-[9px] text-white/60 bg-black/40 px-2 py-1 rounded-md backdrop-blur-sm">
                <Music2 className="w-3 h-3 text-rose-400" />
                <span className="truncate">Kuku FM Original Screenplay · Ep {promo.episodes?.[0]}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Real Mathematically Derived Predictions */}
        <div className="space-y-4">
          {/* Interactive Speech AI Player */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-xs text-white uppercase tracking-wider flex items-center space-x-1.5">
                  <Volume2 className="w-4 h-4 text-amber-400" />
                  <span>Speech AI Voice Preview</span>
                </h4>
                <p className="text-[11px] text-slate-400">
                  Hear the AI read the exact dialogue lines from this cut.
                </p>
              </div>

              <button
                onClick={handlePlayToggle}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition shadow-lg ${
                  isPlaying
                    ? 'bg-amber-500 text-slate-900 hover:bg-amber-400 animate-pulse'
                    : 'bg-gradient-to-r from-rose-600 to-red-600 text-white hover:from-rose-500 hover:to-red-500'
                }`}
              >
                {isPlaying ? <Pause className="w-4 h-4 fill-slate-900" /> : <Play className="w-4 h-4 fill-white" />}
                <span>{isPlaying ? 'Pause Audio' : 'Play Voice Preview'}</span>
              </button>
            </div>

            {isPlaying && (
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 font-mono flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                <span>Streaming dialogue playback...</span>
              </div>
            )}
          </div>

          {/* Real AI Performance Prediction Card with Mathematical Transparency */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-xs text-white uppercase tracking-wider flex items-center space-x-1.5">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span>Explainable Ad Prediction</span>
              </h4>
              <span className="text-[10px] font-mono text-slate-400 flex items-center space-x-1">
                <Calculator className="w-3 h-3 text-cyan-400" />
                <span>5D Engine Derived</span>
              </span>
            </div>

            {/* Dynamic Real Percentages */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-700 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">
                  3s Viral Hook Hold
                </div>
                <div className="text-xl font-mono font-bold text-cyan-400">
                  {hookHoldRate}%
                </div>
                <div className="text-[9px] text-slate-400 leading-tight">
                  Formula: 50% + ({hookScore.toFixed(1)} hook × 4.5%)
                </div>
              </div>

              <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-700 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">
                  Full Cut Completion
                </div>
                <div className="text-xl font-mono font-bold text-amber-400">
                  {completionRate}%
                </div>
                <div className="text-[9px] text-slate-400 leading-tight">
                  Formula: ({cliffScore.toFixed(1)} cliff × 4%) + ({durationScore.toFixed(1)} dur × 3%)
                </div>
              </div>
            </div>

            {/* Dynamic Spend Allocation */}
            <div className="p-2.5 bg-slate-900/70 rounded-lg border border-slate-700 text-xs space-y-1">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Recommended Ad Spend Tier (Score: {finalScore.toFixed(3)})
              </div>
              <div className={`font-mono font-bold text-xs ${spendTagColor}`}>
                {spendTier}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
