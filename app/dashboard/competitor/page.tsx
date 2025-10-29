'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

type Competitor = {
  id: string;
  name: string;
  handles: {
    instagram?: string;
    linkedin?: string;
    x?: string;
    tiktok?: string;
    youtube?: string;
  };
  industry?: string;
  location?: string;
  analysis?: any;
  last_analyzed?: string;
  added_at: string;
};

export default function CompetitorAnalysis() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState<string | null>(null);
  const [insights, setInsights] = useState<string>('');
  const [loadingInsights, setLoadingInsights] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    industry: '',
    location: '',
    instagram: '',
    linkedin: '',
    x: '',
    tiktok: '',
    youtube: ''
  });

  useEffect(() => {
    loadCompetitors();
  }, []);

  const loadCompetitors = async () => {
    try {
      const res = await fetch('http://localhost:8000/competitor/list');
      const data = await res.json();
      setCompetitors(data.competitors || []);
    } catch (err) {
      console.error('Failed to load competitors');
    }
  };

  const loadInsights = async () => {
    setLoadingInsights(true);
    try {
      const res = await fetch('http://localhost:8000/competitor/insights');
      const data = await res.json();
      setInsights(data.insights);
    } catch (err) {
      console.error('Failed to load insights');
    } finally {
      setLoadingInsights(false);
    }
  };

  const addCompetitor = async () => {
    if (!formData.name) {
      alert('Please enter competitor name');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/competitor/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          industry: formData.industry || null,
          location: formData.location || null,
          handles: {
            instagram: formData.instagram || null,
            linkedin: formData.linkedin || null,
            x: formData.x || null,
            tiktok: formData.tiktok || null,
            youtube: formData.youtube || null
          }
        })
      });

      if (res.ok) {
        setFormData({ name: '', industry: '', location: '', instagram: '', linkedin: '', x: '', tiktok: '', youtube: '' });
        setShowAddForm(false);
        loadCompetitors();
      }
    } catch (err) {
      console.error('Failed to add competitor');
    } finally {
      setLoading(false);
    }
  };

  const analyzeCompetitor = async (competitorId: string) => {
    setAnalyzing(competitorId);
    try {
      await fetch(`http://localhost:8000/competitor/${competitorId}/analyze`, { method: 'POST' });
      loadCompetitors();
    } catch (err) {
      console.error('Failed to analyze');
    } finally {
      setAnalyzing(null);
    }
  };

  const deleteCompetitor = async (competitorId: string) => {
    if (!confirm('Remove this competitor?')) return;
    try {
      await fetch(`http://localhost:8000/competitor/${competitorId}`, { method: 'DELETE' });
      loadCompetitors();
    } catch (err) {
      console.error('Failed to delete');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <Link href="/dashboard" className="text-purple-400 hover:text-purple-300 mb-4 inline-block">← Back to Dashboard</Link>
          <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-rose-400 to-pink-400 mb-2">🔍 Competitor Analysis</h1>
          <p className="text-xl text-gray-300">Track competitors and discover content opportunities</p>
        </div>

        <div className="flex gap-4 mb-8">
          <button onClick={() => setShowAddForm(!showAddForm)} className="px-6 py-3 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600 rounded-lg text-white font-bold transition">
            {showAddForm ? '✕ Cancel' : '+ Add Competitor'}
          </button>
          {competitors.length > 0 && (
            <button onClick={loadInsights} disabled={loadingInsights} className="px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 rounded-lg text-white font-bold transition disabled:opacity-50">
              {loadingInsights ? '✨ Analyzing...' : '💡 Get Strategic Insights'}
            </button>
          )}
        </div>

        {showAddForm && (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">Add Competitor</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <input type="text" placeholder="Competitor Name *" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500" />
              <input type="text" placeholder="Industry (optional)" value={formData.industry} onChange={(e) => setFormData({...formData, industry: e.target.value})} className="px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500" />
            </div>
            <input type="text" placeholder="Location (optional)" value={formData.location} onChange={(e) => setFormData({...formData, location: e.target.value})} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500 mb-4" />
            <h3 className="text-lg font-semibold text-white mb-3">Social Media Handles</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              <input type="text" placeholder="📷 Instagram: @handle" value={formData.instagram} onChange={(e) => setFormData({...formData, instagram: e.target.value})} className="px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500" />
              <input type="text" placeholder="💼 LinkedIn: company-name" value={formData.linkedin} onChange={(e) => setFormData({...formData, linkedin: e.target.value})} className="px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500" />
              <input type="text" placeholder="𝕏 X/Twitter: @handle" value={formData.x} onChange={(e) => setFormData({...formData, x: e.target.value})} className="px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500" />
              <input type="text" placeholder="🎵 TikTok: @handle" value={formData.tiktok} onChange={(e) => setFormData({...formData, tiktok: e.target.value})} className="px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500" />
              <input type="text" placeholder="📺 YouTube: channel-name" value={formData.youtube} onChange={(e) => setFormData({...formData, youtube: e.target.value})} className="px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-rose-500" />
            </div>
            <button onClick={addCompetitor} disabled={loading} className="w-full py-4 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600 rounded-lg text-white font-bold transition disabled:opacity-50">
              {loading ? 'Adding...' : '✓ Add Competitor'}
            </button>
          </div>
        )}

        {insights && (
          <div className="bg-gradient-to-br from-purple-900/50 to-indigo-900/50 backdrop-blur-lg rounded-xl p-6 border border-purple-500/30 mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">💡 Strategic Insights</h2>
            <p className="text-gray-200 whitespace-pre-wrap leading-relaxed">{insights}</p>
          </div>
        )}

        {competitors.length === 0 ? (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-12 border border-white/10 text-center">
            <div className="text-6xl mb-4">🔍</div>
            <h2 className="text-2xl font-bold text-white mb-2">No Competitors Yet</h2>
            <p className="text-gray-400 mb-6">Add competitors to start analyzing their content strategy</p>
            <button onClick={() => setShowAddForm(true)} className="px-6 py-3 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600 rounded-lg text-white font-bold transition">+ Add Your First Competitor</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {competitors.map((comp) => (
              <div key={comp.id} className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">{comp.name}</h3>
                    {comp.industry && <p className="text-sm text-gray-400">{comp.industry}</p>}
                    {comp.location && <p className="text-sm text-gray-500">📍 {comp.location}</p>}
                  </div>
                  <button onClick={() => deleteCompetitor(comp.id)} className="text-red-400 hover:text-red-300 text-xl">×</button>
                </div>
                <div className="flex flex-wrap gap-2 mb-4">
                  {comp.handles.instagram && <span className="px-3 py-1 bg-gradient-to-r from-pink-500/20 to-purple-500/20 border border-pink-500/30 rounded-full text-xs text-pink-300">📷 {comp.handles.instagram}</span>}
                  {comp.handles.linkedin && <span className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full text-xs text-blue-300">💼 {comp.handles.linkedin}</span>}
                  {comp.handles.x && <span className="px-3 py-1 bg-gray-500/20 border border-gray-500/30 rounded-full text-xs text-gray-300">𝕏 {comp.handles.x}</span>}
                  {comp.handles.tiktok && <span className="px-3 py-1 bg-cyan-500/20 border border-cyan-500/30 rounded-full text-xs text-cyan-300">🎵 {comp.handles.tiktok}</span>}
                  {comp.handles.youtube && <span className="px-3 py-1 bg-red-500/20 border border-red-500/30 rounded-full text-xs text-red-300">📺 {comp.handles.youtube}</span>}
                </div>
                {comp.analysis ? (
                  <div className="bg-white/5 rounded-lg p-4 mb-4">
                    <h4 className="text-sm font-semibold text-purple-300 mb-2">AI Analysis:</h4>
                    <div className="text-sm text-gray-300 space-y-2">
                      {comp.analysis.content_themes && <div><span className="font-semibold text-white">Content Themes:</span><p className="text-xs">{comp.analysis.content_themes.join(', ')}</p></div>}
                      {comp.analysis.insights && <p className="text-xs">{comp.analysis.insights.substring(0, 200)}...</p>}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Last analyzed: {new Date(comp.last_analyzed || '').toLocaleDateString()}</p>
                  </div>
                ) : (
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mb-4"><p className="text-sm text-yellow-300">No analysis yet</p></div>
                )}
                <button onClick={() => analyzeCompetitor(comp.id)} disabled={analyzing === comp.id} className="w-full py-3 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 rounded-lg text-white font-semibold transition disabled:opacity-50">
                  {analyzing === comp.id ? '🔄 Analyzing...' : comp.analysis ? '🔄 Re-Analyze' : '🔍 Analyze Competitor'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
