import React from 'react';
import { 
  Sparkles, 
  BarChart3, 
  ShieldAlert, 
  FileCode2, 
  Cpu, 
  Radio, 
  ExternalLink 
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'studio', label: 'Promo Studio', icon: Sparkles, badge: 'Live' },
    { id: 'quality', label: 'Quality & Telemetry', icon: BarChart3 },
    { id: 'diagnostics', label: 'Failure Audit', icon: ShieldAlert },
    { id: 'screenplay', label: 'Script Teleprompter', icon: FileCode2 },
    { id: 'pipeline', label: 'OpenAI Pipeline', icon: Cpu },
  ];

  return (
    <aside className="w-16 flex-shrink-0 bg-slate-100 dark:bg-[#090a0f] border-r border-slate-200 dark:border-[#1a1d29] flex flex-col items-center py-4 justify-between z-30 select-none transition-colors">
      {/* Brand Icon */}
      <div className="flex flex-col items-center space-y-6">
        <div 
          onClick={() => setActiveTab('studio')}
          className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 to-red-500 flex items-center justify-center shadow-lg shadow-rose-600/25 cursor-pointer hover:scale-105 transition-transform"
          title="Kuku FM Promo Studio"
        >
          <Radio className="w-5 h-5 text-white" />
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-col space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                title={item.label}
                className={`relative group w-11 h-11 rounded-xl flex items-center justify-center transition-all ${
                  isActive
                    ? 'bg-rose-500/15 text-rose-500 dark:text-rose-400 border border-rose-500/30 shadow-sm'
                    : 'text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-slate-200/60 dark:hover:bg-[#141724]'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-rose-500 dark:text-rose-400' : 'text-slate-500 dark:text-gray-400 group-hover:text-slate-800 dark:group-hover:text-gray-200'}`} />

                {/* Tooltip on hover */}
                <div className="absolute left-14 ml-2 px-2.5 py-1 bg-slate-900 dark:bg-[#161a26] border border-slate-700 dark:border-[#272e42] text-xs text-white font-medium rounded-md whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity shadow-xl z-50">
                  {item.label}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Profile / Info */}
      <div className="flex flex-col items-center space-y-3">
        <a
          href="https://github.com/rock917/kuku-fm-promo-discovery"
          target="_blank"
          rel="noreferrer"
          title="View GitHub Repository"
          className="w-9 h-9 rounded-lg flex items-center justify-center text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-[#151926] transition"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
        <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" title="System Operational" />
      </div>
    </aside>
  );
}

