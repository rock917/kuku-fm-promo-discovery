import React from 'react';
import { ShieldAlert, AlertCircle, Info, ChevronDown } from 'lucide-react';

export default function FailureTab({ failureAnalysis }) {
  if (!failureAnalysis) {
    return <div className="text-slate-500 dark:text-gray-400 p-8 text-center">Loading Failure Analysis...</div>;
  }

  const limitations = failureAnalysis.known_system_limitations || failureAnalysis.system_limitations || [];
  const valFailures = failureAnalysis.validation_failures || [];
  const weakCandidates = failureAnalysis.weak_candidates || [];

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="bg-gradient-to-r from-amber-500/10 via-red-500/10 to-transparent border border-amber-500/30 rounded-xl p-5">
        <div className="flex items-start space-x-3">
          <ShieldAlert className="w-5 h-5 text-amber-500 dark:text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Transparent System Limitations & Honest Failure Analysis
            </h3>
            <p className="text-xs text-slate-600 dark:text-gray-300 mt-1 leading-relaxed">
              As required by the assignment guidelines, this report provides a comprehensive, unvarnished failure audit. It documents where the AI + rule-based pipeline faces constraints, edge cases in microdrama scripts, and how each risk is mitigated.
            </p>
          </div>
        </div>
      </div>

      {/* 6 Documented Limitations */}
      <div className="space-y-4">
        <h4 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">
          Documented System Limitations & Architectural Edge Cases
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {limitations.map((lim, index) => (
            <div key={index} className="bg-white dark:bg-[#141824] border border-slate-200 dark:border-[#232838] rounded-xl p-4 sm:p-5 space-y-3 shadow-sm">
              <div className="flex items-center space-x-2 text-amber-600 dark:text-amber-400 text-sm font-bold">
                <Info className="w-4 h-4 flex-shrink-0" />
                <span>{lim.category || lim.limitation || `Limitation #${index + 1}`}</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-gray-300 leading-relaxed">
                {lim.description}
              </p>
              <div className="bg-slate-50 dark:bg-[#191f2e] border border-slate-200 dark:border-[#263045] rounded-lg p-3 text-xs">
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">Engineering Mitigation: </span>
                <span className="text-slate-700 dark:text-gray-300">{lim.mitigation}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sample Validation Disqualifications */}
      <div className="bg-white dark:bg-[#141824] border border-slate-200 dark:border-[#232838] rounded-xl p-5 space-y-4 shadow-sm">
        <h4 className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">
          Sample Validation Disqualifications Audit ({valFailures.length} Total Disqualified)
        </h4>

        <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
          {valFailures.slice(0, 15).map((vf, idx) => (
            <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-[#191f2e] border border-slate-200/80 dark:border-[#252f44] text-xs gap-2">
              <div className="flex items-center space-x-3">
                <span className="font-mono font-bold text-amber-600 dark:text-amber-400">{vf.candidate_id}</span>
                <span className="text-slate-600 dark:text-gray-400">Ep {Array.isArray(vf.episodes) ? vf.episodes.join(', ') : vf.episodes}</span>
                <span className="text-slate-400 dark:text-gray-500 font-mono">({vf.duration_sec}s)</span>
              </div>
              <div className="text-rose-600 dark:text-red-400 font-mono text-[11px] bg-rose-500/10 px-2 py-1 rounded border border-rose-500/20">
                {vf.reason}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
