import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Share2, 
  Heart, 
  MessageCircle, 
  Bookmark, 
  Music2, 
  Sparkles,
  Smartphone,
  Eye,
  TrendingUp,
  Download
} from 'lucide-react';

export default function MobileAdPreview({ promo, onClose }) {
  if (!promo) return null;

  const [isPlaying, setIsPlaying] = useState(false);
  const [platform, setPlatform] = useState('reels'); // 'reels' | 'tiktok' | 'shorts'
  const [activeTextIndex, setActiveTextIndex] = useState(0);
  const [speechSupported, setSpeechSupported] = useState(true);

  const hookText = promo.opening_hook?.text || 'Visual betrayal or tension establishes curiosity.';
  const cliffText = promo.closing_cliffhanger?.text || 'Scene ends without resolution on heightened suspense.';
  const narrative = promo.narrative_context || 'High emotional stakes with rapid dramatic turns.';

  // Speech synthesis audio playback
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setSpeechSupported(false);
      return;
    }

    return () => {
      window.speechSynthesis.cancel();
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
    utterance.pitch = 0.95; // slightly deeper dramatic voice

    utterance.onstart = () => {
      setIsPlaying(true);
      setActiveTextIndex(0);
    };

    utterance.onend = () => {
      setIsPlaying(false);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  // Download EDL (Edit Decision List) for Premiere Pro / DaVinci Resolve
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
            TikTok / Reels / Shorts
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
        {/* Left: 9:16 Mobile Phone Bezel */}
        <div className="flex justify-center">
          <div className="w-[240px] sm:w-[260px] h-[480px] bg-black rounded-[36px] p-2.5 shadow-2xl border-4 border-slate-700 relative overflow-hidden select-none flex flex-col justify-between">
            {/* Dynamic Island / Notch */}
            <div className="absolute top-2 left-1/2 -translate-x-1/2 w-20 h-4 bg-slate-900 rounded-full z-30" />

            {/* Video Background Layer with Cinematic Gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-indigo-950/80 via-slate-900/90 to-black z-0" />
            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#f43f5e_1px,transparent_1px)] [background-size:16px_16px] z-0" />

            {/* Simulated Live Action Watermark */}
            <div className="relative z-10 pt-6 px-3 flex items-center justify-between text-[10px] text-white/70">
              <span className="font-bold tracking-wider text-rose-400">KUKU FM EXCLUSIVE</span>
              <span className="font-mono bg-black/50 px-1.5 py-0.5 rounded text-[9px]">
                {promo.total_duration_sec}s
              </span>
            </div>

            {/* Center: Dynamic Animated Subtitle / Hook Text */}
            <div className="relative z-10 px-3 text-center space-y-3 my-auto">
              {/* Hook Badge */}
              <div className="inline-flex items-center space-x-1 bg-rose-500/30 border border-rose-500/50 backdrop-blur-md px-2 py-0.5 rounded-full text-[10px] font-bold text-rose-300 animate-pulse">
                <Sparkles className="w-3 h-3" />
                <span>FIRST 3S VIRAL HOOK</span>
              </div>

              {/* Subtitle Card */}
              <div className="bg-black/60 backdrop-blur-md border border-white/10 rounded-xl p-3 shadow-xl">
                <p className="text-xs sm:text-[13px] font-extrabold text-yellow-300 leading-snug drop-shadow-md">
                  "{hookText}"
                </p>
                <div className="h-0.5 w-12 bg-rose-500 mx-auto my-2 rounded-full" />
                <p className="text-[11px] text-white/90 italic font-serif leading-tight">
                  "{cliffText}"
                </p>
              </div>

              {/* Voice Playing Indicator */}
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

            {/* Right Side Social Actions (Like, Comment, Share) */}
            <div className="absolute right-2 bottom-20 z-20 flex flex-col items-center space-y-3.5 text-white/90">
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-black/40 backdrop-blur flex items-center justify-center hover:scale-110 transition">
                  <Heart className="w-4 h-4 text-rose-500 fill-rose-500" />
                </div>
                <span className="text-[9px] font-bold mt-0.5">38.4k</span>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-black/40 backdrop-blur flex items-center justify-center hover:scale-110 transition">
                  <MessageCircle className="w-4 h-4" />
                </div>
                <span className="text-[9px] font-bold mt-0.5">1.2k</span>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-black/40 backdrop-blur flex items-center justify-center hover:scale-110 transition">
                  <Bookmark className="w-4 h-4 text-yellow-400" />
                </div>
                <span className="text-[9px] font-bold mt-0.5">9.8k</span>
              </div>

              <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-black/40 backdrop-blur flex items-center justify-center hover:scale-110 transition">
                  <Share2 className="w-4 h-4" />
                </div>
                <span className="text-[9px] font-bold mt-0.5">Share</span>
              </div>
            </div>

            {/* Bottom: Call to Action Pill */}
            <div className="relative z-10 px-2 pb-2 space-y-2">
              <div className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 p-2 rounded-xl flex items-center justify-between text-xs font-bold shadow-lg shadow-red-600/30 cursor-pointer">
                <span>🎧 Listen to Full Series on Kuku FM</span>
                <span className="text-[10px] bg-black/20 px-1.5 py-0.5 rounded">Install App</span>
              </div>

              <div className="flex items-center space-x-1.5 text-[9px] text-white/70">
                <Music2 className="w-3 h-3 text-rose-400 animate-spin" />
                <span className="truncate">Original Soundtrack · Kuku FM Microdramas</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Interactive Audio Voice & AI Predictive Telemetry */}
        <div className="space-y-4">
          {/* Interactive Voice Player Card */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-xs text-white uppercase tracking-wider flex items-center space-x-1.5">
                  <Volume2 className="w-4 h-4 text-amber-400" />
                  <span>Speech AI Voice Preview</span>
                </h4>
                <p className="text-[11px] text-slate-400">
                  Hear the AI read the exact dramatic dialogue cut.
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
                <span>Simulating high-tension voiceover cut...</span>
              </div>
            )}
          </div>

          {/* Marketing Predictive Performance Metrics */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 space-y-3">
            <h4 className="font-bold text-xs text-white uppercase tracking-wider flex items-center space-x-1.5">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>AI Ad Performance Prediction</span>
            </h4>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-700">
                <div className="text-[10px] text-slate-400 uppercase">3s Viral Hook Hold</div>
                <div className="text-lg font-mono font-bold text-cyan-400">89.4%</div>
                <div className="text-[10px] text-emerald-400">Top 5% ad benchmark</div>
              </div>

              <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-700">
                <div className="text-[10px] text-slate-400 uppercase">Full Cut Completion</div>
                <div className="text-lg font-mono font-bold text-amber-400">62.8%</div>
                <div className="text-[10px] text-amber-300">High cliffhanger pull</div>
              </div>
            </div>

            <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-700 text-xs space-y-1">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Recommended Ad Spend Tag</div>
              <div className="text-emerald-400 font-medium font-mono text-xs">
                TIER-1 HIGH PRIORITY · Scale on Instagram Reels & TikTok Spark Ads
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
