import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import StudioView from './components/StudioView';
import QualityTab from './components/QualityTab';
import FailureTab from './components/FailureTab';
import SourceViewerTab from './components/SourceViewerTab';
import PipelineRunTab from './components/PipelineRunTab';
import { fetchHealth, fetchPromos, fetchQualityReport, fetchFailureAnalysis } from './api';

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('kuku_theme') || 'dark';
  });
  const [activeTab, setActiveTab] = useState('studio');
  const [backendStatus, setBackendStatus] = useState('checking');
  const [promos, setPromos] = useState([]);
  const [qualityReport, setQualityReport] = useState(null);
  const [failureAnalysis, setFailureAnalysis] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.classList.remove('dark');
      root.classList.add('light');
    } else {
      root.classList.remove('light');
      root.classList.add('dark');
    }
    localStorage.setItem('kuku_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const health = await fetchHealth();
      setBackendStatus(health.status === 'healthy' ? 'online' : 'offline');

      const promosRes = await fetchPromos();
      setPromos(promosRes.promos || []);
      setMetadata(promosRes.metadata || {});

      const qual = await fetchQualityReport();
      setQualityReport(qual);

      const fail = await fetchFailureAnalysis();
      setFailureAnalysis(fail);
    } catch (err) {
      console.error('Data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify({ metadata, promos }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'promos.json';
    a.click();
  };

  const exportCSV = () => {
    const headers = ['Rank', 'Candidate_ID', 'Episodes', 'Scene', 'Start_TS', 'End_TS', 'Duration_Sec', 'Final_Score', 'Hook_Text', 'Cliffhanger_Text'];
    const rows = promos.map(p => [
      p.rank,
      p.candidate_id,
      (p.episodes || []).join(';'),
      p.segments?.[0]?.scene_number,
      p.segments?.[0]?.start_ts,
      p.segments?.[0]?.end_ts,
      p.total_duration_sec,
      p.final_score,
      `"${(p.opening_hook?.text || '').replace(/"/g, '""')}"`,
      `"${(p.closing_cliffhanger?.text || '').replace(/"/g, '""')}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'promos.csv';
    a.click();
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 dark:bg-[#090a0f] dark:text-gray-100 font-sans antialiased transition-colors duration-200">
      {/* Linear-Style Left Navigation Dock */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} theme={theme} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header 
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          backendStatus={backendStatus}
          totalPromos={promos.length}
          onExportJSON={exportJSON}
          onExportCSV={exportCSV}
          theme={theme}
          toggleTheme={toggleTheme}
        />

        {/* Dynamic Tab Views */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center space-y-4">
              <div className="w-10 h-10 border-4 border-rose-500/20 border-t-rose-500 rounded-full animate-spin"></div>
              <p className="text-xs text-slate-500 dark:text-gray-400 font-mono tracking-wider uppercase">
                Loading Kuku FM Promo Studio...
              </p>
            </div>
          ) : (
            <>
              {activeTab === 'studio' && (
                <StudioView promos={promos} searchQuery={searchQuery} theme={theme} />
              )}
              {activeTab === 'quality' && (
                <div className="flex-1 overflow-y-auto p-6 max-w-7xl mx-auto w-full">
                  <QualityTab qualityReport={qualityReport} />
                </div>
              )}
              {activeTab === 'diagnostics' && (
                <div className="flex-1 overflow-y-auto p-6 max-w-7xl mx-auto w-full">
                  <FailureTab failureAnalysis={failureAnalysis} />
                </div>
              )}
              {activeTab === 'screenplay' && (
                <div className="flex-1 overflow-y-auto p-6 max-w-7xl mx-auto w-full">
                  <SourceViewerTab />
                </div>
              )}
              {activeTab === 'pipeline' && (
                <div className="flex-1 overflow-y-auto p-6 max-w-7xl mx-auto w-full">
                  <PipelineRunTab onPipelineSuccess={loadData} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
