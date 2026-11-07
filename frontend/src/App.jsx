import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import PromosTab from './components/PromosTab';
import QualityTab from './components/QualityTab';
import FailureTab from './components/FailureTab';
import SourceViewerTab from './components/SourceViewerTab';
import PipelineRunTab from './components/PipelineRunTab';
import { fetchHealth, fetchPromos, fetchQualityReport, fetchFailureAnalysis } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('promos');
  const [backendStatus, setBackendStatus] = useState('checking');
  const [promos, setPromos] = useState([]);
  const [qualityReport, setQualityReport] = useState(null);
  const [failureAnalysis, setFailureAnalysis] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0d13] text-gray-100">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} backendStatus={backendStatus} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="w-10 h-10 border-4 border-red-500/20 border-t-red-500 rounded-full animate-spin"></div>
            <p className="text-sm text-gray-400 font-medium">Loading Promo Discovery System...</p>
          </div>
        ) : (
          <>
            {activeTab === 'promos' && (
              <PromosTab promos={promos} loading={loading} metadata={metadata} />
            )}
            {activeTab === 'quality' && (
              <QualityTab qualityReport={qualityReport} />
            )}
            {activeTab === 'failure' && (
              <FailureTab failureAnalysis={failureAnalysis} />
            )}
            {activeTab === 'source' && (
              <SourceViewerTab />
            )}
            {activeTab === 'run' && (
              <PipelineRunTab onPipelineSuccess={loadData} />
            )}
          </>
        )}
      </main>

      <footer className="border-t border-[#1b2030] py-6 text-center text-xs text-gray-500">
        <p>Kuku FM AI Generalist Assignment · Problem 1: Find the Promos</p>
        <p className="mt-1">Architected for Vercel Frontend + Azure App Service Backend + Supabase PostgreSQL</p>
      </footer>
    </div>
  );
}
