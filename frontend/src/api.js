// =============================================================================
// api.js — Data Client for Azure FastAPI Backend & Local Fallback
// =============================================================================

const API_BASE = import.meta.env.VITE_API_URL || 'https://kuku-fm-rg-f4bsfnb0ejcbdkeb.centralindia-01.azurewebsites.net';

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) return await res.json();
  } catch (e) {
    // Backend offline
  }
  return { status: 'offline', local_fallback: true };
}

export async function fetchPromos(filters = {}) {
  // Try live Azure API first
  try {
    const params = new URLSearchParams();
    if (filters.episode) params.append('episode', filters.episode);
    if (filters.minScore) params.append('min_score', filters.minScore);
    if (filters.minDuration) params.append('min_duration', filters.minDuration);
    if (filters.maxDuration) params.append('max_duration', filters.maxDuration);

    const res = await fetch(`${API_BASE}/api/promos?${params.toString()}`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      const data = await res.json();
      return { promos: data.results, total: data.total_matching, source: 'azure-api' };
    }
  } catch (e) {
    // Fall back to local bundled JSON
  }

  // Fallback to static bundled data
  try {
    const res = await fetch('/data/promos.json');
    const data = await res.json();
    let promos = data.ranked_promos || [];

    if (filters.episode) {
      promos = promos.filter(p => (p.episodes || []).includes(Number(filters.episode)));
    }
    if (filters.minScore) {
      promos = promos.filter(p => (p.final_score || 0) >= Number(filters.minScore));
    }
    if (filters.minDuration) {
      promos = promos.filter(p => (p.total_duration_sec || 0) >= Number(filters.minDuration));
    }
    if (filters.maxDuration) {
      promos = promos.filter(p => (p.total_duration_sec || 0) <= Number(filters.maxDuration));
    }

    return {
      promos,
      total: promos.length,
      metadata: data.metadata,
      source: 'bundled-json'
    };
  } catch (err) {
    console.error('Failed to load promos:', err);
    return { promos: [], total: 0, error: err.message };
  }
}

export async function fetchQualityReport() {
  try {
    const res = await fetch(`${API_BASE}/api/quality-report`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) return await res.json();
  } catch (e) {}

  const res = await fetch('/data/quality_report.json');
  return await res.json();
}

export async function fetchFailureAnalysis() {
  try {
    const res = await fetch(`${API_BASE}/api/failure-analysis`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) return await res.json();
  } catch (e) {}

  const res = await fetch('/data/failure_analysis.json');
  return await res.json();
}

export async function fetchEpisodeContent(episodeNumber) {
  try {
    const res = await fetch(`${API_BASE}/api/episodes/${episodeNumber}`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) return await res.json();
  } catch (e) {}

  return {
    episode_number: episodeNumber,
    screenplay_text: `Screenplay viewer is connected to the backend. Start the backend with 'uvicorn src.api:app' to stream Episode ${episodeNumber} screenplay text directly.`
  };
}

export async function triggerPipelineRun(params) {
  const res = await fetch(`${API_BASE}/api/pipeline/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`API error: ${res.statusText}`);
  return await res.json();
}

