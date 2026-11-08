import React, { useState } from 'react';
import { 
  Play, 
  Cpu, 
  Check, 
  AlertCircle, 
  RefreshCw, 
  Link as LinkIcon, 
  FileText, 
  Layers, 
  Sparkles,
  Flame,
  Clock,
  ExternalLink
} from 'lucide-react';
import { triggerPipelineRun, analyzeCustomScript } from '../api';

const SAMPLE_SCRIPT_TEMPLATE = `EPISODE NUMBER: Episode 51
EPISODE LOGLINE: The Duke faces an unexpected betrayal in the royal courtyard.
CONTINUITY NOTES: Takes place immediately following the wedding banquet.

--- SCRIPT START ---
SCENE 1
Scene heading: EXT. ROYAL COURTYARD – NIGHT
Scene start: 00:00.00
Scene end: 00:55.00

**ACTION:**
Start: (00:00.00) | End: (00:04.50)
Heavy rain lashes against stone arches. Lady Juliana clutches her veil as guards surround the pavilion.

**DUKE ALEXANDER (Cold, Command):**
Start: (00:04.50) | End: (00:18.20)
"You thought I died on the northern front. Look at my face, Lord Cassian... Do you truly believe I came back to surrender?"

**LORD CASSIAN (Trembling, Defiant):**
Start: (00:18.20) | End: (00:32.40)
"You cannot protect her! By dawn, every soldier in this garrison answers to the King's seal!"

**JULIANA (Desperate):**
Start: (00:32.40) | End: (00:43.00)
"Alexander, no! He has the imperial seal hidden beneath the altar!"

**SOUND FX:**
Start: (00:43.00) | End: (00:55.00)
Thunder cracks violently. Alexander draws his blade. Ominous cliffhanger strings rise to an abrupt silence.
--- SCRIPT END ---`;

export default function PipelineRunTab({ onPipelineSuccess }) {
  // Input mode: 'url' | 'text' | 'archive'
  const [inputMode, setInputMode] = useState('url');
  const [episodeUrl, setEpisodeUrl] = useState('');
  const [scriptText, setScriptText] = useState('');
  const [provider, setProvider] = useState('groq');
  const [model, setModel] = useState('openai/gpt-oss-120b');
  const [topN, setTopN] = useState(5);
  const [submitting, setSubmitting] = useState(false);
  const [customResults, setCustomResults] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleProviderChange = (e) => {
    const val = e.target.value;
    setProvider(val);
    if (val === 'groq') setModel('openai/gpt-oss-120b');
    else if (val === 'openai') setModel('gpt-4o-mini');
    else if (val === 'gemini') setModel('gemini-1.5-flash');
    else if (val === 'mock') setModel('mock');
  };

  const handleRun = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);
    setCustomResults(null);

    try {
      if (inputMode === 'archive') {
        // Run full archive pipeline
        const res = await triggerPipelineRun({ provider, model, top_n: topN });
        setResult(res);
        if (onPipelineSuccess) onPipelineSuccess();
      } else {
        // Run on-demand custom episode analysis (URL or Text)
        const payload = {
          sourceType: inputMode,
          url: episodeUrl,
          scriptText: scriptText,
          provider,
          model,
          topN,
        };
        const res = await analyzeCustomScript(payload);
        setCustomResults(res);
      }
    } catch (err) {
      setError(err.message || 'Failed to process episode analysis.');
    } finally {
      setSubmitting(false);
    }
  };

  const loadTemplate = () => {
    setInputMode('text');
    setScriptText(SAMPLE_SCRIPT_TEMPLATE);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white dark:bg-[#121624] border border-slate-200/90 dark:border-[#20273a] rounded-2xl p-6 sm:p-7 shadow-sm transition-colors">
        {/* Header */}
        <div className="flex items-center space-x-3 pb-5 border-b border-slate-100 dark:border-[#1c2235]">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 to-red-500 flex items-center justify-center text-white shadow-md shadow-rose-600/20">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              AI Promo Discovery Pipeline & Ingestion
            </h3>
            <p className="text-xs text-slate-500 dark:text-gray-400">
              Analyze new episodes via public link, raw script text, or process the existing 50-episode library.
            </p>
          </div>
        </div>

        <form onSubmit={handleRun} className="space-y-6 pt-5">
          {/* Source Mode Selector (Tabs) */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-2 uppercase tracking-wider">
              1. Choose Screenplay Input Source
            </label>
            <div className="grid grid-cols-3 gap-2 p-1 bg-slate-100 dark:bg-[#161a29] rounded-xl border border-slate-200 dark:border-[#242d42]">
              <button
                type="button"
                onClick={() => setInputMode('url')}
                className={`flex items-center justify-center space-x-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition ${
                  inputMode === 'url'
                    ? 'bg-white dark:bg-[#20273a] text-rose-600 dark:text-rose-400 shadow-sm'
                    : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <LinkIcon className="w-3.5 h-3.5" />
                <span>Episode Link / URL</span>
              </button>

              <button
                type="button"
                onClick={() => setInputMode('text')}
                className={`flex items-center justify-center space-x-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition ${
                  inputMode === 'text'
                    ? 'bg-white dark:bg-[#20273a] text-rose-600 dark:text-rose-400 shadow-sm'
                    : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Paste Script Text</span>
              </button>

              <button
                type="button"
                onClick={() => setInputMode('archive')}
                className={`flex items-center justify-center space-x-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition ${
                  inputMode === 'archive'
                    ? 'bg-white dark:bg-[#20273a] text-rose-600 dark:text-rose-400 shadow-sm'
                    : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>50-Episode Library</span>
              </button>
            </div>
          </div>

          {/* Mode 1: Episode Link Input */}
          {inputMode === 'url' && (
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300">
                Public Episode Link (Google Drive, Dropbox, AWS S3, or Raw URL)
              </label>
              <div className="relative">
                <input
                  type="url"
                  required={inputMode === 'url'}
                  value={episodeUrl}
                  onChange={(e) => setEpisodeUrl(e.target.value)}
                  placeholder="https://drive.google.com/file/d/... or https://dropbox.com/... or raw text URL"
                  className="w-full bg-slate-50 dark:bg-[#161a29] border border-slate-200 dark:border-[#252e44] rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-900 dark:text-gray-100 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none focus:border-rose-500 transition shadow-sm"
                />
              </div>
              <p className="text-[11px] text-slate-500 dark:text-gray-400">
                Supports direct .txt files, Google Drive share links, and Dropbox links. The Azure backend downloads and analyzes it in seconds.
              </p>
            </div>
          )}

          {/* Mode 2: Paste Script Text Input */}
          {inputMode === 'text' && (
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300">
                  Raw Screenplay Text (with scene headings & timestamps)
                </label>
                <button
                  type="button"
                  onClick={loadTemplate}
                  className="text-[11px] text-rose-600 dark:text-rose-400 hover:underline font-medium flex items-center space-x-1"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>Load Sample Episode 51</span>
                </button>
              </div>
              <textarea
                rows={8}
                required={inputMode === 'text'}
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder="Paste the episode script here (e.g. SCENE 1, Scene heading, Dialogue, and SFX with timestamps)..."
                className="w-full font-mono text-xs bg-slate-50 dark:bg-[#161a29] border border-slate-200 dark:border-[#252e44] rounded-xl p-3.5 text-slate-900 dark:text-gray-100 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none focus:border-rose-500 transition shadow-sm"
              />
            </div>
          )}

          {/* Mode 3: Archive Info */}
          {inputMode === 'archive' && (
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#161a29] border border-slate-200 dark:border-[#252e44] text-xs text-slate-600 dark:text-gray-300 space-y-1">
              <div className="font-semibold text-slate-900 dark:text-gray-100 flex items-center space-x-1.5">
                <Layers className="w-4 h-4 text-rose-500" />
                <span>Archive Batch Run (50 Episodes)</span>
              </div>
              <p>
                Runs the full discovery algorithm across all 50 episodes of <em>"I Married a Broken Soldier. He was a Duke"</em> located on the Azure backend.
              </p>
            </div>
          )}

          {/* LLM & Model Settings */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300 mb-1.5 uppercase">
                LLM Provider
              </label>
              <select
                value={provider}
                onChange={handleProviderChange}
                className="w-full bg-slate-50 dark:bg-[#161a29] border border-slate-200 dark:border-[#252e44] rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-900 dark:text-gray-200 focus:outline-none focus:border-rose-500 shadow-sm"
              >
                <option value="groq">Groq (GPT-OSS 120B / LPU)</option>
                <option value="openai">OpenAI (GPT-4o Mini)</option>
                <option value="gemini">Google Gemini 1.5</option>
                <option value="mock">Offline Testing (Deterministic)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300 mb-1.5 uppercase">
                Model Identifier
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-slate-50 dark:bg-[#161a29] border border-slate-200 dark:border-[#252e44] rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-900 dark:text-gray-200 focus:outline-none focus:border-rose-500 shadow-sm font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300 mb-1.5 uppercase">
                Top Promos to Rank
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value))}
                className="w-full bg-slate-50 dark:bg-[#161a29] border border-slate-200 dark:border-[#252e44] rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-900 dark:text-gray-200 focus:outline-none focus:border-rose-500 shadow-sm font-mono"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-rose-600 via-red-600 to-amber-600 hover:from-rose-500 hover:to-red-500 font-bold text-white text-sm shadow-lg shadow-rose-600/25 transition flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Analyzing Screenplay with {provider.toUpperCase()}...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>
                  {inputMode === 'url' ? 'Download & Discover Promos from Link' : inputMode === 'text' ? 'Discover Promos from Screenplay Text' : 'Execute Full Archive Pipeline'}
                </span>
              </>
            )}
          </button>
        </form>

        {/* Status Alerts */}
        {error && (
          <div className="mt-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-red-400 text-xs space-y-1">
            <div className="font-bold flex items-center space-x-1.5">
              <AlertCircle className="w-4 h-4" />
              <span>Analysis Failed</span>
            </div>
            <p className="text-slate-600 dark:text-gray-300">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-5 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs space-y-1">
            <div className="font-bold flex items-center space-x-1.5">
              <Check className="w-4 h-4" />
              <span>Archive Pipeline Queued Successfully</span>
            </div>
            <p className="text-slate-600 dark:text-gray-300">{result.message}</p>
          </div>
        )}

        {/* On-Demand Analysis Results Display */}
        {customResults && (
          <div className="mt-6 pt-6 border-t border-slate-200 dark:border-[#20273a] space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                  Analysis Complete: {customResults.top_promos?.length || 0} Promos Found
                </span>
                <span className="text-xs text-slate-500 dark:text-gray-400 ml-2">
                  (Detected {customResults.scenes_detected} scene(s), {customResults.total_candidates_generated} candidate windows)
                </span>
              </div>
            </div>

            <div className="space-y-3">
              {customResults.top_promos?.map((promo, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-50 dark:bg-[#161a29] border border-slate-200 dark:border-[#252e44] space-y-2 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                        RANK #{promo.rank || idx + 1}
                      </span>
                      <span className="text-xs font-bold text-slate-800 dark:text-gray-200">
                        Episode {promo.episodes?.join(', ')} · Scene {promo.segments?.[0]?.scene_number}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {promo.segments?.[0]?.start_ts} – {promo.segments?.[0]?.end_ts} ({promo.total_duration_sec}s)
                      </span>
                    </div>

                    <div className="font-mono text-xs font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">
                      Score: {promo.final_score?.toFixed(3)}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div className="text-xs p-2.5 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
                      <span className="text-[10px] uppercase font-bold text-cyan-600 dark:text-cyan-400 block mb-0.5">
                        Opening Hook (First 3s)
                      </span>
                      <p className="italic text-slate-700 dark:text-gray-300 font-serif">
                        "{promo.opening_hook?.text}"
                      </p>
                    </div>

                    <div className="text-xs p-2.5 rounded-lg bg-rose-500/5 border border-rose-500/20">
                      <span className="text-[10px] uppercase font-bold text-rose-600 dark:text-rose-400 block mb-0.5">
                        Closing Cliffhanger (Cut Point)
                      </span>
                      <p className="italic text-slate-700 dark:text-gray-300 font-serif">
                        "{promo.closing_cliffhanger?.text}"
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
