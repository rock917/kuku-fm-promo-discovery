import React from 'react';
import { 
  Bot, 
  Search, 
  Download, 
  Layers, 
  Sparkles,
  SlidersHorizontal,
  Sun,
  Moon
} from 'lucide-react';

export default function Header({ 
  searchQuery, 
  setSearchQuery, 
  backendStatus, 
  totalPromos, 
  onExportJSON, 
  onExportCSV,
  theme,
  toggleTheme
}) {
  return (
    <header className="h-14 border-b border-slate-200 dark:border-[#181b26] bg-white/90 dark:bg-[#0c0d14]/90 backdrop-blur px-6 flex items-center justify-between z-20 select-none transition-colors">
      {/* Breadcrumb & Project Name */}
      <div className="flex items-center space-x-3 text-xs">
        <span className="font-semibold text-slate-500 dark:text-gray-400">Kuku FM Studio</span>
        <span className="text-slate-300 dark:text-gray-600">/</span>
        <span className="font-bold text-slate-900 dark:text-gray-200">I Married a Broken Soldier</span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-[#171b26] text-slate-600 dark:text-gray-400 border border-slate-200 dark:border-[#232a3d] font-mono">
          50 Eps
        </span>

        {/* OpenAI GPT Badge */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-mono text-[11px]">
          <Bot className="w-3.5 h-3.5" />
          <span className="font-semibold">OpenAI GPT-4o Mini</span>
        </div>
      </div>

      {/* Center Search Input */}
      <div className="hidden md:flex items-center w-80 relative">
        <Search className="w-3.5 h-3.5 text-slate-400 dark:text-gray-500 absolute left-3 pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter candidate text, scene, speaker... (⌘K)"
          className="w-full bg-slate-100 dark:bg-[#121520] border border-slate-200 dark:border-[#202638] rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-800 dark:text-gray-200 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none focus:border-rose-500/50 focus:ring-1 focus:ring-rose-500/20 transition"
        />
      </div>

      {/* Right Controls: Theme Toggle + Backend pill & Export actions */}
      <div className="flex items-center space-x-2">
        {/* Theme Switcher Button */}
        <button
          onClick={toggleTheme}
          className="p-1.5 rounded-lg bg-slate-100 dark:bg-[#161a26] hover:bg-slate-200 dark:hover:bg-[#202638] text-slate-600 dark:text-gray-300 border border-slate-200 dark:border-[#262f44] transition flex items-center justify-center"
          title={`Switch to ${theme === 'dark' ? 'Bright / Light' : 'Dark'} Theme`}
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400 hover:rotate-45 transition-transform" />
          ) : (
            <Moon className="w-4 h-4 text-slate-700 hover:-rotate-12 transition-transform" />
          )}
        </button>

        <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-[#131722] border border-slate-200 dark:border-[#212738] text-[11px] text-slate-600 dark:text-gray-400">
          <span className={`w-1.5 h-1.5 rounded-full ${backendStatus === 'online' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          <span>{backendStatus === 'online' ? 'Azure API' : 'Vercel Edge'}</span>
        </div>

        <button
          onClick={onExportJSON}
          className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md bg-slate-100 dark:bg-[#161a26] hover:bg-slate-200 dark:hover:bg-[#202638] text-xs font-medium text-slate-700 dark:text-gray-300 border border-slate-200 dark:border-[#262f44] transition"
          title="Export promos.json"
        >
          <Download className="w-3.5 h-3.5 text-slate-500 dark:text-gray-400" />
          <span className="hidden sm:inline">JSON</span>
        </button>

        <button
          onClick={onExportCSV}
          className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md bg-slate-100 dark:bg-[#161a26] hover:bg-slate-200 dark:hover:bg-[#202638] text-xs font-medium text-slate-700 dark:text-gray-300 border border-slate-200 dark:border-[#262f44] transition"
          title="Export promos.csv"
        >
          <Download className="w-3.5 h-3.5 text-slate-500 dark:text-gray-400" />
          <span className="hidden sm:inline">CSV</span>
        </button>
      </div>
    </header>
  );
}

