import React, { useState, useEffect } from 'react';
import { FileText, Search, AlertCircle } from 'lucide-react';
import { fetchEpisodeContent } from '../api';

export default function SourceViewerTab() {
  const [episodeNum, setEpisodeNum] = useState(1);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="space-y-6">
      <div className="bg-[#141824] border border-[#232838] rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <FileText className="w-4 h-4 text-red-400" />
            <span>Screenplay Source Verification & Traceability Viewer</span>
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Every promo recommendation links directly to an episode, scene, and scene-relative timestamp.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <label className="text-xs font-medium text-gray-300">Select Episode:</label>
          <select
            value={episodeNum}
            onChange={(e) => setEpisodeNum(Number(e.target.value))}
            className="bg-[#1b2030] border border-[#2b354c] rounded-lg px-3 py-1.5 text-sm text-gray-200 font-bold focus:outline-none focus:border-red-500"
          >
            {Array.from({ length: 50 }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>Episode {n}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Screenplay Content Card */}
      <div className="bg-[#141824] border border-[#232838] rounded-xl overflow-hidden shadow-sm">
        <div className="bg-[#181d2c] px-4 py-3 border-b border-[#232838] flex items-center justify-between text-xs">
          <span className="font-mono text-gray-300 font-bold">
            Episode {episodeNum} — Raw Screenplay
          </span>
          <span className="text-amber-400 font-mono text-[11px] bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
            ⚠️ Scene-Relative Timestamps (resets to 00:00.00 each scene)
          </span>
        </div>

        <div className="p-4 bg-[#0d0f17]">
          {loading ? (
            <div className="text-center py-16 text-gray-500 text-xs">Loading screenplay...</div>
          ) : (
            <pre className="font-mono text-xs text-gray-300 whitespace-pre-wrap leading-relaxed max-h-[600px] overflow-y-auto">
              {content}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

