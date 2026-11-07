import React, { useState } from 'react';
import { ChevronDown, ChevronUp, MoreHorizontal, Sparkles } from 'lucide-react';

export default function RadarScoreCard({ selectedPromo }) {
  if (!selectedPromo) return null;

  const [isAnalysisOpen, setIsAnalysisOpen] = useState(true);

  const aiScores = selectedPromo.scoring?.scores?.['AI-generated'] || {};
  const progScores = selectedPromo.scoring?.scores?.['programmatic'] || {};

  // Extract the 5 dimensions on 0-10 scale
  const hookScore = aiScores.hook_strength?.score ?? 8.5;
  const cliffScore = aiScores.cliffhanger_strength?.score ?? 8.0;
  const standScore = aiScores.standalone_clarity?.score ?? 7.5;
  const emotScore = aiScores.emotional_impact?.score ?? 8.0;
  const durScore = progScores.duration_quality?.score ?? 10.0;

  // Radar chart dimensions & geometry
  const size = 200;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = 64;

  // 5 dimensions arranged in clockwise pentagon:
  // Top (Hook) -> Top-Right (Sense / Standalone) -> Bottom-Right (Body / Duration) -> Bottom-Left (Pacing / Cliffhanger) -> Top-Left (Tone / Emotion)
  const dimensions = [
    { label: 'Hook', fullLabel: 'Hook Strength', weight: '25%', score: hookScore, color: '#38bdf8' },
    { label: 'Sense', fullLabel: 'Narrative Sense', weight: '20%', score: standScore, color: '#fbbf24' },
    { label: 'Body', fullLabel: 'Duration & Body', weight: '10%', score: durScore, color: '#34d399' },
    { label: 'Pacing', fullLabel: 'Cliffhanger Pacing', weight: '30%', score: cliffScore, color: '#f43f5e' },
    { label: 'Tone', fullLabel: 'Emotional Tone', weight: '15%', score: emotScore, color: '#c084fc' },
  ];

  // Angles for pentagon vertices (-90 is top)
  const angles = [-90, -18, 54, 126, 198];

  const getPoint = (angleDeg, radius) => {
    const rad = (angleDeg * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    };
  };

  // 5 concentric polygon grid rings
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];
  const gridPolygons = gridLevels.map((lvl) => {
    return angles.map((ang) => {
      const pt = getPoint(ang, maxR * lvl);
      return `${pt.x},${pt.y}`;
    }).join(' ');
  });

  // Active data polygon points
  const dataPoints = dimensions.map((dim, idx) => {
    const fraction = Math.max(0.18, Math.min(1.0, dim.score / 10));
    return getPoint(angles[idx], maxR * fraction);
  });
  const dataPolygon = dataPoints.map((pt) => `${pt.x},${pt.y}`).join(' ');

  // Cliffhanger scaled to 100
  const cliffScaled = Math.round(cliffScore * 10);

  // Transcript text from hook or opening line
  const hookText = selectedPromo.opening_hook?.text || 
    (selectedPromo.segments && selectedPromo.segments[0]?.events?.find(e => e.type === 'dialogue')?.text) ||
    'I Married a Broken Soldier. He was a Duke who returned with scars, but an unbreakable resolve...';

  return (
    <div className="bg-white dark:bg-[#121624] border border-slate-200/90 dark:border-[#20273a] rounded-2xl p-4 sm:p-5 space-y-4 shadow-sm transition-colors">
      {/* Top Header matching user screenshot */}
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-[#1c2235] pb-3">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
          <h3 className="font-bold text-sm text-slate-900 dark:text-gray-100 tracking-tight">
            AI Promo Inspector
          </h3>
        </div>
        <div className="flex items-center space-x-1.5 text-slate-400 hover:text-slate-600 dark:text-gray-500 dark:hover:text-gray-300">
          <span className="text-[11px] font-mono font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 mr-1">
            GPT-4o Scored
          </span>
          <button className="p-1 rounded hover:bg-slate-100 dark:hover:bg-[#1a2030] transition">
            <MoreHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Hook Transcript Box matching user screenshot */}
      <div className="bg-slate-50/80 dark:bg-[#161b2c] border border-slate-200/70 dark:border-[#252f47] rounded-xl p-3.5 space-y-1.5">
        <div className="text-[11px] font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider flex items-center justify-between">
          <span>Hook Transcript</span>
          <span className="text-[10px] font-mono text-cyan-600 dark:text-cyan-400">00:00 - 00:03 Cut</span>
        </div>
        <p className="text-xs sm:text-[13px] text-slate-800 dark:text-gray-200 leading-relaxed font-serif italic">
          "{hookText}"
        </p>
      </div>

      {/* Split Cards: Left Meter & Breakdown + Right Pentagon Radar Chart */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-stretch">
        {/* Left Column Card: Cliffhanger Score + Emotional Analysis */}
        <div className="bg-slate-50/90 dark:bg-[#161b2c] border border-slate-200/80 dark:border-[#252f47] rounded-xl p-4 flex flex-col justify-between space-y-3.5">
          {/* Cliffhanger Score Headline */}
          <div>
            <div className="flex justify-between items-baseline mb-1.5">
              <span className="text-xs font-bold text-slate-800 dark:text-gray-200 tracking-tight">
                Cliffhanger Score:
              </span>
              <span className="font-mono text-base font-black text-amber-500 dark:text-amber-400">
                {cliffScaled}<span className="text-xs text-slate-400 dark:text-gray-500 font-normal">/100</span>
              </span>
            </div>

            {/* Glowing Gradient Bar: Red -> Amber -> Yellow */}
            <div className="h-2 w-full bg-slate-200 dark:bg-[#0d101a] rounded-full overflow-hidden p-[1px] shadow-inner">
              <div
                className="h-full rounded-full bg-gradient-to-r from-red-600 via-amber-500 to-yellow-400 shadow-sm transition-all duration-700 ease-out"
                style={{ width: `${Math.min(100, Math.max(8, cliffScaled))}%` }}
              />
            </div>
          </div>

          {/* Emotional Analysis Collapsible Section */}
          <div className="pt-2 border-t border-slate-200/60 dark:border-[#222b40] space-y-2.5">
            <button
              onClick={() => setIsAnalysisOpen(!isAnalysisOpen)}
              className="w-full flex items-center justify-between text-xs font-bold text-slate-700 dark:text-gray-300 hover:text-slate-900 dark:hover:text-white transition"
            >
              <span>Emotional Analysis</span>
              {isAnalysisOpen ? (
                <ChevronUp className="w-3.5 h-3.5 text-slate-400 dark:text-gray-500" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-gray-500" />
              )}
            </button>

            {isAnalysisOpen && (
              <div className="space-y-2 pt-1 transition-all">
                {dimensions.map((dim, i) => {
                  const pct = Math.round(dim.score * 10);
                  return (
                    <div key={i} className="flex justify-between items-center text-xs">
                      <span className="text-slate-600 dark:text-gray-400 flex items-center space-x-1.5">
                        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dim.color }} />
                        <span>{dim.fullLabel}</span>
                      </span>
                      <span className="font-mono font-bold text-slate-800 dark:text-gray-200">
                        {pct}%
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column Card: Glowing Amber Pentagon Radar Chart */}
        <div className="bg-slate-50/90 dark:bg-[#161b2c] border border-slate-200/80 dark:border-[#252f47] rounded-xl p-3 flex flex-col items-center justify-center relative select-none">
          <svg width={size} height={size} className="overflow-visible">
            <defs>
              {/* Radial Glowing Amber Gradient for Polygon */}
              <radialGradient id="radarGoldGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.5" />
                <stop offset="70%" stopColor="#d97706" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#b45309" stopOpacity="0.1" />
              </radialGradient>
              <filter id="neonRadarGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3.5" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Pentagon Grid Concentric Rings */}
            {gridPolygons.map((pts, i) => (
              <polygon
                key={i}
                points={pts}
                fill="none"
                stroke={i === gridPolygons.length - 1 ? '#64748b' : '#334155'}
                strokeWidth={i === gridPolygons.length - 1 ? 1 : 0.6}
                strokeDasharray={i === gridPolygons.length - 1 ? 'none' : '2 2'}
                opacity={0.4}
              />
            ))}

            {/* Radial Spoke Lines */}
            {angles.map((ang, i) => {
              const pt = getPoint(ang, maxR);
              return (
                <line
                  key={i}
                  x1={cx}
                  y1={cy}
                  x2={pt.x}
                  y2={pt.y}
                  stroke="#475569"
                  strokeWidth="0.8"
                  opacity={0.35}
                />
              );
            })}

            {/* Active Data Filled Polygon with Glow */}
            <polygon
              points={dataPolygon}
              fill="url(#radarGoldGlow)"
              stroke="#fbbf24"
              strokeWidth="2"
              filter="url(#neonRadarGlow)"
              className="transition-all duration-500 ease-out"
            />

            {/* Vertex Glowing Dots */}
            {dataPoints.map((pt, i) => (
              <circle
                key={i}
                cx={pt.x}
                cy={pt.y}
                r="3.5"
                fill="#fef08a"
                stroke="#d97706"
                strokeWidth="1.5"
                className="transition-all duration-500 ease-out"
              />
            ))}

            {/* Vertex Axis Labels matching screenshot */}
            {dimensions.map((dim, i) => {
              const labelPt = getPoint(angles[i], maxR + 16);
              return (
                <text
                  key={i}
                  x={labelPt.x}
                  y={labelPt.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="text-[10px] font-mono fill-slate-500 dark:fill-gray-400 font-semibold"
                >
                  {dim.label}
                </text>
              );
            })}
          </svg>

          <span className="text-[10px] text-slate-400 dark:text-gray-500 font-mono mt-1">
            5D Harmonic Resonance
          </span>
        </div>
      </div>
    </div>
  );
}
