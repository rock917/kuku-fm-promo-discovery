import React, { useState, useEffect, useMemo } from 'react';
import { FileText, Search, Copy, Check, ChevronDown, BookOpen, Clock, AlertTriangle } from 'lucide-react';
import { fetchEpisodeContent } from '../api';

export default function SourceViewerTab() {
  const [episodeNum, setEpisodeNum] = useState(1);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchEpisodeContent(episodeNum).then((data) => {
      if (active) {
        setContent(data.screenplay_text || 'No screenplay content available.');
        setLoading(false);
      }
    });
    return () => { active = false; };
  }, [episodeNum]);

  const copyScript = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Stats
  const stats = useMemo(() => {
    if (!content) return { lines: 0, scenes: 0, chars: 0 };
    const lines = content.split('\n');
    const scenes = lines.filter(l => /^(INT\.|EXT\.)/i.test(l.trim())).length;
    return {
      lines: lines.length,
      scenes: Math.max(1, scenes),
      chars: content.length,
    };
  }, [content]);

  // Highlighted search matches
  const formattedContent = useMemo(() => {
    if (!searchQuery.trim() || !content) return content;
    // Simple line-based filtering or highlight
    return content;
  }, [content, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Control Bar */}
      <div className="bg-white dark:bg-[#121624] border border-slate-200 dark:border-[#20273a] rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <FileText className="w-4 h-4 text-rose-500 dark:text-rose-400" />
              <span>Screenplay Source Verification & Traceability Viewer</span>
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-gray-400 mt-1">
            Deterministic source ground truth: Every promo candidate links directly to an episode, scene, and scene-relative timestamp.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Episode Selector */}
          <div className="flex items-center space-x-2 bg-slate-50 dark:bg-[#181d2c] border border-slate-200 dark:border-[#2b354c] rounded-lg px-3 py-1.5 shadow-sm">
            <BookOpen className="w-3.5 h-3.5 text-slate-400 dark:text-gray-400" />
            <label className="text-xs font-semibold text-slate-700 dark:text-gray-300">Episode:</label>
            <select
              value={episodeNum}
              onChange={(e) => setEpisodeNum(Number(e.target.value))}
              className="bg-transparent text-sm text-slate-900 dark:text-gray-200 font-bold focus:outline-none cursor-pointer"
            >
              {Array.from({ length: 50 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n} className="dark:bg-[#181d2c] dark:text-gray-200">
                  Episode {n}
                </option>
              ))}
            </select>
          </div>

          {/* Copy Button */}
          <button
            onClick={copyScript}
            disabled={loading || !content}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-[#181d2c] hover:bg-slate-100 dark:hover:bg-[#202638] text-xs font-medium text-slate-700 dark:text-gray-300 border border-slate-200 dark:border-[#2b354c] transition shadow-sm disabled:opacity-50"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5 text-slate-400 dark:text-gray-400" />}
            <span>{copied ? 'Copied' : 'Copy Full Script'}</span>
          </button>
        </div>
      </div>

      {/* Screenplay Content Card */}
      <div className="bg-white dark:bg-[#121624] border border-slate-200 dark:border-[#20273a] rounded-xl overflow-hidden shadow-sm">
        {/* Header Strip with Metadata */}
        <div className="bg-slate-50 dark:bg-[#181d2c] px-4 py-3 border-b border-slate-200 dark:border-[#20273a] flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center space-x-3">
            <span className="font-mono text-slate-900 dark:text-gray-200 font-bold">
              Episode {episodeNum} — Original Script
            </span>
            <span className="text-[11px] text-slate-500 dark:text-gray-400 font-mono">
              {stats.scenes} scenes · {stats.lines} lines · {stats.chars.toLocaleString()} chars
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center space-x-1 text-amber-600 dark:text-amber-400 font-mono text-[11px] bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              <Clock className="w-3 h-3 mr-1" />
              <span>Scene-Relative Timestamps (Resets to 00:00.00 each scene)</span>
            </span>
          </div>
        </div>

        {/* Script Viewer Body */}
        <div className="p-4 bg-slate-100/60 dark:bg-[#0c0e17]">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <div className="w-6 h-6 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
              <div className="text-slate-400 dark:text-gray-500 text-xs font-mono">Streaming Episode {episodeNum} screenplay...</div>
            </div>
          ) : (
            <div className="relative">
              <pre className="font-mono text-xs text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed max-h-[640px] overflow-y-auto selection:bg-rose-500/30 p-2">
                {formattedContent}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
