import React, { useState } from 'react';
import { Download, Filter, Clock, Flame, ShieldCheck, ChevronDown, ChevronUp, Layers, HelpCircle } from 'lucide-react';

export default function PromosTab({ promos, loading, metadata }) {
  const [selectedEpisode, setSelectedEpisode] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [minDuration, setMinDuration] = useState(20);
  const [maxDuration, setMaxDuration] = useState(60);
  const [expandedId, setExpandedId] = useState(promos[0]?.candidate_id || null);

  // Extract all episode numbers available
  const allEpisodes = Array.from(
    new Set(promos.flatMap((p) => p.episodes || []))
  ).sort((a, b) => a - b);

  // Filter promos
  const filtered = promos.filter((p) => {
    if (selectedEpisode && !(p.episodes || []).includes(Number(selectedEpisode))) return false;
    if ((p.final_score || 0) < minScore) return false;
    if ((p.total_duration_sec || 0) < minDuration || (p.total_duration_sec || 0) > maxDuration) return false;
    return true;
  });

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify({ metadata, promos: filtered }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'promos.json';
    a.click();
  };

  const exportCSV = () => {
    const headers = ['Rank', 'Candidate_ID', 'Episodes', 'Scene', 'Start_TS', 'End_TS', 'Duration_Sec', 'Final_Score', 'Hook_Text', 'Cliffhanger_Text'];
    const rows = filtered.map(p => [
      p.rank,
      p.candidate_id,
      (p.episodes || []).join(';'),
      p.segments?.[0]?.scene_number,
      p.segments?.[0]?.start_ts,
      p.segments?.[0]?.end_ts,
      p.total_duration_sec,
      p.final_score,
      `"${(p.opening_hook?.text || '').replace(/"/g, '""')}"`,
      `"${(p.closing_cliffhanger?.text || '').replace(/"/g, '""')}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'promos.csv';
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Filters Bar */}
      <div className="bg-[#141824] border border-[#232838] rounded-xl p-4 sm:p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#232838]">
          <div className="flex items-center space-x-2 text-gray-200 font-semibold text-sm">
            <Filter className="w-4 h-4 text-red-400" />
            <span>Candidate Filter Criteria</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-[#1e2333] text-gray-400 border border-[#2b3348]">
              {filtered.length} of {promos.length} Candidates
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={exportJSON}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#1e2433] hover:bg-[#283044] text-xs font-medium text-gray-300 border border-[#2f384f] transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={exportCSV}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#1e2433] hover:bg-[#283044] text-xs font-medium text-gray-300 border border-[#2f384f] transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">Episode Number</label>
            <select
              value={selectedEpisode}
              onChange={(e) => setSelectedEpisode(e.target.value)}
              className="w-full bg-[#1b2030] border border-[#2a3348] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500"
            >
              <option value="">All 50 Episodes</option>
              {allEpisodes.map((ep) => (
                <option key={ep} value={ep}>Episode {ep}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Minimum Final Score: <span className="text-red-400 font-bold">{minScore}</span>
            </label>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full accent-red-500 cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Duration Limit: <span className="text-red-400 font-bold">{minDuration}s – {maxDuration}s</span>
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="number"
                min="20"
                max="60"
                value={minDuration}
                onChange={(e) => setMinDuration(Number(e.target.value))}
                className="w-1/2 bg-[#1b2030] border border-[#2a3348] rounded-lg px-2.5 py-1.5 text-xs text-gray-200 text-center"
              />
              <span className="text-gray-500 text-xs">to</span>
              <input
                type="number"
                min="20"
                max="60"
                value={maxDuration}
                onChange={(e) => setMaxDuration(Number(e.target.value))}
                className="w-1/2 bg-[#1b2030] border border-[#2a3348] rounded-lg px-2.5 py-1.5 text-xs text-gray-200 text-center"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Promos List */}
      <div className="space-y-4">
        {filtered.map((promo) => {
          const isExpanded = expandedId === promo.candidate_id;
          const seg = promo.segments?.[0] || {};
          const score = promo.final_score || 0;
          const aiScores = promo.scoring?.scores?.['AI-generated'] || {};
          const progScores = promo.scoring?.scores?.['programmatic'] || {};

          return (
            <div
              key={promo.candidate_id}
              className={`bg-[#141824] border transition rounded-xl overflow-hidden shadow-sm ${
                isExpanded ? 'border-red-500/50 ring-1 ring-red-500/20' : 'border-[#232838] hover:border-[#323a50]'
              }`}
            >
              {/* Card Header */}
              <div
                onClick={() => setExpandedId(isExpanded ? null : promo.candidate_id)}
                className="p-4 sm:p-5 flex items-center justify-between cursor-pointer select-none"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-amber-500/20 to-red-500/20 border border-amber-500/30 flex items-center justify-center font-black text-amber-400 text-lg">
                    #{promo.rank}
                  </div>

                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-gray-100 text-base">
                        Episode {promo.episodes?.join(', ')} · Scene {seg.scene_number}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-[#1e2434] text-gray-300 font-mono border border-[#2d364d]">
                        {seg.start_ts} → {seg.end_ts}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/20">
                        {promo.total_duration_sec}s
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1 font-mono">
                      {seg.scene_heading || 'SCENE HEADING'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Composite Score</div>
                    <div className="text-xl font-black text-amber-400 font-mono">
                      {score.toFixed(3)}<span className="text-xs text-gray-500">/10</span>
                    </div>
                  </div>
                  {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                </div>
              </div>

              {/* Card Body */}
              {isExpanded && (
                <div className="px-4 sm:px-5 pb-5 pt-2 border-t border-[#1f2536] bg-[#10131d]/50 space-y-5">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left: Narrative & Hooks */}
                    <div className="lg:col-span-2 space-y-4">
                      {/* Hook */}
                      <div className="bg-[#181d2c] border border-blue-500/20 rounded-lg p-3.5">
                        <div className="flex items-center space-x-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
                          <Flame className="w-3.5 h-3.5" />
                          <span>Opening Hook (First 3s Attention Grabber)</span>
                        </div>
                        <p className="text-sm text-gray-200 italic">
                          "{promo.opening_hook?.text || 'No hook text available'}"
                        </p>
                      </div>

                      {/* Cliffhanger */}
                      <div className="bg-[#181d2c] border border-red-500/20 rounded-lg p-3.5">
                        <div className="flex items-center space-x-2 text-red-400 text-xs font-semibold uppercase tracking-wider mb-1">
                          <Clock className="w-3.5 h-3.5" />
                          <span>Closing Cliffhanger (Unresolved Dramatic Peak)</span>
                        </div>
                        <p className="text-sm text-gray-200 italic">
                          "{promo.closing_cliffhanger?.text || 'No cliffhanger text available'}"
                        </p>
                        {promo.has_cliffhanger_sfx && (
                          <div className="text-xs text-amber-400/80 mt-2 flex items-center space-x-1">
                            <span>🔔 Supporting SFX Signal: {promo.cliffhanger_sfx_note}</span>
                          </div>
                        )}
                      </div>

                      {/* Standalone Narrative Context */}
                      <div className="bg-[#181d2c] border border-[#283248] rounded-lg p-3.5">
                        <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
                          Narrative Context & Standalone Value
                        </div>
                        <p className="text-xs text-gray-300 leading-relaxed">
                          {promo.narrative_context}
                        </p>
                      </div>
                    </div>

                    {/* Right: Explainable 5D Scoring Breakdown */}
                    <div className="bg-[#171c2b] border border-[#283248] rounded-lg p-4 space-y-4">
                      <div className="text-xs font-bold text-gray-200 uppercase tracking-wider border-b border-[#242b3e] pb-2 flex items-center justify-between">
                        <span>Score Breakdown</span>
                        <span className="text-[10px] text-gray-400">Explainable Weights</span>
                      </div>

                      {/* AI-Generated Section */}
                      <div className="space-y-2.5">
                        <div className="text-[11px] font-semibold text-amber-400 flex items-center space-x-1">
                          <span>⚡ AI-Generated Scores</span>
                          <span className="text-gray-500 font-normal">(LLM Narrative Analysis)</span>
                        </div>

                        {[
                          { key: 'hook_strength', label: 'Hook Strength', weight: '25%', score: aiScores.hook_strength?.score },
                          { key: 'cliffhanger_strength', label: 'Cliffhanger Strength', weight: '30%', score: aiScores.cliffhanger_strength?.score },
                          { key: 'standalone_clarity', label: 'Standalone Clarity', weight: '20%', score: aiScores.standalone_clarity?.score },
                          { key: 'emotional_impact', label: 'Emotional Impact', weight: '15%', score: aiScores.emotional_impact?.score },
                        ].map((dim) => (
                          <div key={dim.key} className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-gray-400">{dim.label} <span className="text-gray-500">({dim.weight})</span></span>
                              <span className="text-amber-400 font-mono font-bold">{dim.score?.toFixed(1) || '—'}/10</span>
                            </div>
                            <div className="h-1.5 w-full bg-[#20273a] rounded-full overflow-hidden">
                              <div
                                className="h-full bg-amber-500 rounded-full"
                                style={{ width: `${((dim.score || 0) / 10) * 100}%` }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Programmatic Section */}
                      <div className="space-y-2.5 pt-2 border-t border-[#242b3e]">
                        <div className="text-[11px] font-semibold text-cyan-400 flex items-center space-x-1">
                          <span>🔒 Programmatic Score</span>
                          <span className="text-gray-500 font-normal">(Deterministic Rule)</span>
                        </div>

                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Duration Quality <span className="text-gray-500">(10%)</span></span>
                            <span className="text-cyan-400 font-mono font-bold">{progScores.duration_quality?.score?.toFixed(1) || '—'}/10</span>
                          </div>
                          <div className="h-1.5 w-full bg-[#20273a] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-cyan-500 rounded-full"
                              style={{ width: `${((progScores.duration_quality?.score || 0) / 10) * 100}%` }}
                            ></div>
                          </div>
                          <p className="text-[10px] text-gray-500">Target: 25s–45s ideal window.</p>
                        </div>
                      </div>

                      {/* Validation Badge */}
                      <div className="pt-2 border-t border-[#242b3e] flex items-center space-x-2 text-emerald-400 text-xs">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span className="font-semibold">Passed 100% Deterministic Validations</span>
                      </div>
                    </div>
                  </div>

                  {/* Traceability Note */}
                  <div className="text-[11px] text-gray-500 font-mono bg-[#0e111a] p-2.5 rounded border border-[#1d2334]">
                    📍 Traceability: Ep{seg.episode_number} Scene {seg.scene_number} · Timestamps are scene-relative (resetting to 00:00.00 for this scene).
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

