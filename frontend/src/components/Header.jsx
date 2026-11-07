import React from 'react';
import { 
  Bot, 
  Search, 
  Download, 
  Layers, 
  Sparkles,
  SlidersHorizontal 
} from 'lucide-react';

export default function Header({ 
  searchQuery, 
  setSearchQuery, 
  backendStatus, 
  totalPromos, 
  onExportJSON, 
  onExportCSV 
}) {
  return (
    <header className="h-14 border-b border-[#181b26] bg-[#0c0d14]/90 backdrop-blur px-6 flex items-center justify-between z-20 select-none">
      {/* Breadcrumb & Project Name */}
      <div className="flex items-center space-x-3 text-xs">
        <span className="font-semibold text-gray-400">Kuku FM Studio</span>
        <span className="text-gray-600">/</span>
        <span className="font-bold text-gray-200">I Married a Broken Soldier</span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#171b26] text-gray-400 border border-[#232a3d] font-mono">
          50 Eps
        </span>

        {/* OpenAI GPT Badge */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[11px]">
          <Bot className="w-3.5 h-3.5" />
          <span className="font-semibold">OpenAI GPT-4o Mini</span>
        </div>
      </div>

      {/* Center Search Input */}
      <div className="hidden md:flex items-center w-80 relative">
        <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter candidate text, scene, speaker... (⌘K)"
          className="w-full bg-[#121520] border border-[#202638] rounded-lg pl-9 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-rose-500/50 focus:ring-1 focus:ring-rose-500/20 transition"
        />
      </div>

      {/* Right Controls: Backend pill & Export actions */}
      <div className="flex items-center space-x-2.5">
        <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#131722] border border-[#212738] text-[11px] text-gray-400">
          <span className={`w-1.5 h-1.5 rounded-full ${backendStatus === 'online' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
          <span>{backendStatus === 'online' ? 'Azure API' : 'Vercel Edge'}</span>
        </div>

        <button
          onClick={onExportJSON}
          className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md bg-[#161a26] hover:bg-[#202638] text-xs font-medium text-gray-300 border border-[#262f44] transition"
          title="Export promos.json"
        >
          <Download className="w-3.5 h-3.5 text-gray-400" />
          <span className="hidden sm:inline">JSON</span>
        </button>

        <button
          onClick={onExportCSV}
          className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md bg-[#161a26] hover:bg-[#202638] text-xs font-medium text-gray-300 border border-[#262f44] transition"
          title="Export promos.csv"
        >
          <Download className="w-3.5 h-3.5 text-gray-400" />
          <span className="hidden sm:inline">CSV</span>
        </button>
      </div>
    </header>
  );
}
