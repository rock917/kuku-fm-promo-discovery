import React, { useState } from 'react';
import { Play, Cpu, Check, AlertCircle, RefreshCw } from 'lucide-react';
import { triggerPipelineRun } from '../api';

export default function PipelineRunTab({ onPipelineSuccess }) {
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4o-mini');
  const [topN, setTopN] = useState(20);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleProviderChange = (e) => {
    const val = e.target.value;
    setProvider(val);
    if (val === 'groq') setModel('llama-3.3-70b-versatile');
    else if (val === 'gemini') setModel('gemini-1.5-flash');
    else if (val === 'openai') setModel('gpt-4o-mini');
    else if (val === 'mock') setModel('mock');
  };

  const handleRun = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const res = await triggerPipelineRun({ provider, model, top_n: topN });
      setResult(res);
      if (onPipelineSuccess) onPipelineSuccess();
    } catch (err) {
      setError(err.message || 'Failed to trigger pipeline run');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-[#141824] border border-[#232838] rounded-xl p-6 shadow-sm">
        <div className="flex items-center space-x-3 pb-4 border-b border-[#232838]">
          <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Pipeline Execution Controls</h3>
            <p className="text-xs text-gray-400">
              Run an analysis job across the 50 microdrama episodes with swappable LLM reasoning.
            </p>
          </div>
        </div>

        <form onSubmit={handleRun} className="space-y-5 pt-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5 uppercase">
                LLM Provider
              </label>
              <select
                value={provider}
                onChange={handleProviderChange}
                className="w-full bg-[#1b2030] border border-[#2a3449] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500"
              >
                <option value="groq">Groq (Ultra-Fast Inference)</option>
                <option value="gemini">Google Gemini</option>
                <option value="openai">OpenAI</option>
                <option value="mock">Mock (Zero API Calls — Fast Verification)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5 uppercase">
                Model Identifier
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-[#1b2030] border border-[#2a3449] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1.5 uppercase">
              Top Promos to Rank
            </label>
            <input
              type="number"
              min="5"
              max="100"
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              className="w-full bg-[#1b2030] border border-[#2a3449] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500"
            />
            <p className="text-[11px] text-gray-500 mt-1">
              Extracts and scores candidate windows across all 50 episodes and ranks the top N candidates.
            </p>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 font-bold text-white text-sm shadow-lg shadow-red-500/20 transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Triggering Pipeline Analysis...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Execute Promo Discovery Pipeline</span>
              </>
            )}
          </button>
        </form>

        {result && (
          <div className="mt-5 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs space-y-1">
            <div className="font-bold flex items-center space-x-1">
              <Check className="w-4 h-4" />
              <span>Pipeline Job Queued Successfully</span>
            </div>
            <p className="text-gray-300">{result.message}</p>
          </div>
        )}

        {error && (
          <div className="mt-5 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs space-y-1">
            <div className="font-bold flex items-center space-x-1">
              <AlertCircle className="w-4 h-4" />
              <span>Pipeline Execution Failed</span>
            </div>
            <p className="text-gray-300">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

