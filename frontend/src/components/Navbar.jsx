import React from 'react';
import { Radio, Sparkles, CheckCircle2, AlertCircle, ShieldAlert, FileText, Play } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, backendStatus }) {
  const tabs = [
    { id: 'promos', label: 'Ranked Promos', icon: Sparkles },
    { id: 'quality', label: 'Quality & Validation', icon: CheckCircle2 },
    { id: 'failure', label: 'Failure Analysis', icon: ShieldAlert },
    { id: 'source', label: 'Source Screenplay', icon: FileText },
    { id: 'run', label: 'Pipeline Controls', icon: Play },
  ];

  return (
    <header className="border-b border-[#232838] bg-[#12151e]/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center shadow-lg shadow-red-500/20">
              <Radio className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-white">Kuku FM</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 font-semibold border border-red-500/20">
                  Promo Discovery
                </span>
              </div>
              <p className="text-xs text-gray-400 hidden sm:block">
                AI Generalist Assignment · Problem 1 (50 Episodes Microdrama)
              </p>
            </div>
          </div>

          {/* Backend Status Pill */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-[#1a1f2c] border border-[#2b3348] text-xs">
              <span className={`w-2 h-2 rounded-full ${backendStatus === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
              <span className="text-gray-300 font-medium">
                {backendStatus === 'online' ? 'Azure Backend Connected' : 'Vercel Mode (Bundled Data)'}
              </span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 sm:space-x-4 overflow-x-auto py-2 -mb-px">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-lg transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-red-500/15 text-red-400 border border-red-500/30 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#1a1f2c]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-red-400' : 'text-gray-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}

