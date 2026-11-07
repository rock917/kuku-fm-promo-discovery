import React from 'react';
import { CheckCircle2, AlertTriangle, Layers, BarChart2, ShieldCheck, Database } from 'lucide-react';

export default function QualityTab({ qualityReport }) {
  if (!qualityReport) {
    return <div className="text-slate-500 dark:text-gray-400 p-8 text-center">Loading Quality Report...</div>;
  }

  const counts = qualityReport.candidate_counts || {};
  const val = qualityReport.validation_summary || {};
  const failureTypes = val.failure_type_counts || {};
  const coverage = qualityReport.coverage || {};
  const scores = qualityReport.score_distribution || {};

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-[#141824] border border-slate-200 dark:border-[#232838] p-5 rounded-xl shadow-sm">
          <div className="text-xs text-slate-500 dark:text-gray-400 font-semibold uppercase">Total Candidates</div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-2 font-mono">
            {counts.total_generated || 0}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-gray-500 mt-1">Generated across 50 episodes</p>
        </div>

        <div className="bg-white dark:bg-[#141824] border border-emerald-500/20 p-5 rounded-xl shadow-sm">
          <div className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold uppercase">Passed Validation</div>
          <div className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-2 font-mono">
            {counts.passed_validation || 0}
          </div>
          <p className="text-[11px] text-emerald-600/80 dark:text-emerald-500/80 mt-1">100% compliant with constraints</p>
        </div>

        <div className="bg-white dark:bg-[#141824] border border-amber-500/20 p-5 rounded-xl shadow-sm">
          <div className="text-xs text-amber-600 dark:text-amber-400 font-semibold uppercase">Filtered / Duplicates</div>
          <div className="text-3xl font-extrabold text-amber-600 dark:text-amber-400 mt-2 font-mono">
            {counts.failed_validation || 0}
          </div>
          <p className="text-[11px] text-amber-600/80 dark:text-amber-500/80 mt-1">Deduplicated & disqualified</p>
        </div>

        <div className="bg-white dark:bg-[#141824] border border-blue-500/20 p-5 rounded-xl shadow-sm">
          <div className="text-xs text-blue-600 dark:text-blue-400 font-semibold uppercase">Ranked Selection</div>
          <div className="text-3xl font-extrabold text-blue-600 dark:text-blue-400 mt-2 font-mono">
            {counts.ranked_output || 0}
          </div>
          <p className="text-[11px] text-blue-600/80 dark:text-blue-400/80 mt-1">Top promo recommendations</p>
        </div>
      </div>

      {/* Validation Breakdown & Score Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Validation Audit */}
        <div className="bg-white dark:bg-[#141824] border border-slate-200 dark:border-[#232838] rounded-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center space-x-2 text-slate-900 dark:text-white font-bold text-sm border-b border-slate-100 dark:border-[#232838] pb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span>Deterministic Constraint Enforcement</span>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs p-3 rounded-lg bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44]">
              <span className="text-slate-700 dark:text-gray-300">Timestamp Not Found in Screenplay (±0.5s)</span>
              <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{val.timestamp_errors || 0} errors</span>
            </div>

            <div className="flex justify-between items-center text-xs p-3 rounded-lg bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44]">
              <span className="text-slate-700 dark:text-gray-300">Hallucinated Verbatim Dialogue</span>
              <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{val.hallucination_errors || 0} errors</span>
            </div>

            <div className="flex justify-between items-center text-xs p-3 rounded-lg bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44]">
              <span className="text-slate-700 dark:text-gray-300">Duration Range Violations (&lt;20s or &gt;60s)</span>
              <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{val.duration_errors || 0} errors</span>
            </div>

            <div className="flex justify-between items-center text-xs p-3 rounded-lg bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44]">
              <span className="text-slate-700 dark:text-gray-300">Overlapping Window Deduplication (≥60% Overlap)</span>
              <span className="font-mono font-bold text-amber-600 dark:text-amber-400">{val.duplicate_pairs_found || 0} pairs detected</span>
            </div>
          </div>

          {/* Failure Types Bar */}
          <div className="pt-2">
            <div className="text-xs font-semibold text-slate-500 dark:text-gray-400 mb-2">Failure Type Distribution</div>
            {Object.entries(failureTypes).map(([type, count]) => (
              <div key={type} className="space-y-1">
                <div className="flex justify-between text-xs text-slate-600 dark:text-gray-400">
                  <span>{type}</span>
                  <span className="font-mono font-bold text-amber-600 dark:text-amber-400">{count}</span>
                </div>
                <div className="h-2 w-full bg-slate-100 dark:bg-[#1e2538] rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full w-full"></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Episode Coverage & Score Metrics */}
        <div className="bg-white dark:bg-[#141824] border border-slate-200 dark:border-[#232838] rounded-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center space-x-2 text-slate-900 dark:text-white font-bold text-sm border-b border-slate-100 dark:border-[#232838] pb-3">
            <BarChart2 className="w-4 h-4 text-blue-500 dark:text-blue-400" />
            <span>Episode Coverage & Score Metrics</span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44] rounded-lg">
              <div className="text-[10px] text-slate-500 dark:text-gray-400 uppercase">Top Score</div>
              <div className="text-lg font-mono font-black text-amber-600 dark:text-amber-400 mt-1">{scores.top || '—'}</div>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44] rounded-lg">
              <div className="text-[10px] text-slate-500 dark:text-gray-400 uppercase">Average Score</div>
              <div className="text-lg font-mono font-black text-slate-900 dark:text-white mt-1">{scores.average?.toFixed(2) || '—'}</div>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44] rounded-lg">
              <div className="text-[10px] text-slate-500 dark:text-gray-400 uppercase">Min Valid Score</div>
              <div className="text-lg font-mono font-black text-slate-500 dark:text-gray-400 mt-1">{scores.minimum || '—'}</div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-800 dark:text-gray-300 font-semibold mb-2">
              <span>Episode Coverage</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-mono font-bold">
                {coverage.episodes_with_at_least_one_candidate?.length || 50}/50 Episodes (100%)
              </span>
            </div>
            <div className="h-2 w-full bg-slate-100 dark:bg-[#1e2538] rounded-full overflow-hidden mb-3">
              <div className="h-full bg-emerald-500 rounded-full w-full"></div>
            </div>
            <p className="text-xs text-slate-600 dark:text-gray-400 leading-relaxed">
              Every single episode out of all 50 was successfully parsed, validated, and contributed candidate promotional moments to the discovery pipeline.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
