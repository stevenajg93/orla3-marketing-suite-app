'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

export default function BlogWriter() {
  const [keyword, setKeyword] = useState('');
  const [searchIntent, setSearchIntent] = useState('');
  const [wordCount, setWordCount] = useState(1500);
  const [loading, setLoading] = useState(false);
  const [researching, setResearching] = useState(false);
  const [marketResearch, setMarketResearch] = useState<{ keyword: string; intent: string; insights: string[] } | null>(null);
  const [blog, setBlog] = useState<{ title: string; content: string; slug: string } | null>(null);
  const [error, setError] = useState('');
  const [saveMessage, setSaveMessage] = useState('');

  const autoGenerate = async () => {
    setLoading(true);
    setResearching(true);
    setError('');
    setMarketResearch(null);
    
    try {
      const strategyRes = await api.get('/strategy/next-keyword');
      const strategy = strategyRes;
      const nextKw = strategy.recommended_next;
      
      setKeyword(nextKw.keyword);
      setSearchIntent(nextKw.search_intent);
      
      const researchRes = await api.post(`/strategy/market-research`, { keyword: nextKw.keyword });
      const research = researchRes;
      setMarketResearch({
        ...research,
        market_gap: nextKw.market_gap
      });
      
      setResearching(false);
      
      const response = await api.post(`/draft/content/draft`, {
          keyword: nextKw.keyword,
          search_intent: nextKw.search_intent,
          target_length_words: wordCount
        });

      
      const data = response;
      setBlog(data);
    } catch (err: unknown) {
      console.error('Auto-generate error:', err);
      setError('Failed to auto-generate. Make sure backend is running.');
    } finally {
      setLoading(false);
      setResearching(false);
    }
  };

  const doMarketResearch = async () => {
    if (!keyword.trim()) {
      setError('Please enter a keyword first');
      return;
    }

    setResearching(true);
    setError('');
    
    try {
      const researchRes = await api.post(`/strategy/market-research`, { keyword });
      const research = researchRes;
      setMarketResearch(research);
    } catch (err) {
      setError('Failed to fetch market research.');
    } finally {
      setResearching(false);
    }
  };

  const generateBlog = async () => {
    if (!keyword.trim() || !searchIntent.trim()) {
      setError('Please enter both keyword and search intent');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await api.post(`/draft/content/draft`, {
          keyword,
          search_intent: searchIntent,
          target_length_words: wordCount
        });

      
      const data = response;
      setBlog(data);
    } catch (err) {
      setError('Failed to generate blog. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const saveToLibrary = async () => {
    if (!blog) return;
    
    setSaveMessage('');
    
    try {
      const response = await fetch(`${config.apiUrl}/library/content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: Date.now().toString(),
          title: blog.title,
          content_type: 'blog',
          content: blog.body_md,
          created_at: new Date().toISOString(),
          status: 'draft',
          tags: [keyword, searchIntent]
        })
      });

      
      setSaveMessage('✅ Saved to Media Library!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (err) {
      setSaveMessage('❌ Failed to save');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-gray-400 hover:text-white mb-2 inline-block">
              ← Back to Dashboard
            </Link>
            <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-yellow-200">
              ✍️ Blog Writer
            </h1>
            <p className="text-gray-400 mt-2">AI-powered SEO content engine with live market research</p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-6 border border-green-400/30 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">🤖 Autonomous Mode</h3>
              <p className="text-green-100">Strategic keyword + market research + blog generation</p>
            </div>
            <button
              onClick={autoGenerate}
              disabled={loading}
              className="bg-white hover:bg-green-50 text-green-700 font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {researching ? '🔍 Researching Market...' : loading ? '✨ Generating...' : '⚡ Auto-Generate'}
            </button>
          </div>
        </div>

        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-6">
          <h3 className="text-xl font-bold text-white mb-4">Manual Mode (Optional)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <label className="block text-white font-bold mb-2">Keyword/Topic</label>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="e.g., Corporate Video Production"
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
            </div>

            <div>
              <label className="block text-white font-bold mb-2">Search Intent</label>
              <input
                type="text"
                value={searchIntent}
                onChange={(e) => setSearchIntent(e.target.value)}
                placeholder="e.g., Find best corporate videographers"
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
            </div>

            <div>
              <label className="block text-white font-bold mb-2">Word Count</label>
              <input
                type="number"
                value={wordCount}
                onChange={(e) => setWordCount(Number(e.target.value))}
                min="500"
                max="3000"
                step="100"
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={doMarketResearch}
              disabled={researching}
              className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {researching ? '🔍 Researching...' : '🔍 Research Market First'}
            </button>
            
            <button
              onClick={generateBlog}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-black font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '✨ Generating Blog...' : '🚀 Generate Blog Post'}
            </button>
          </div>

          {error && (
            <div className="mt-4 bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-200">
              {error}
            </div>
          )}
        </div>

        {marketResearch && (
          <div className="bg-gradient-to-br from-blue-900/40 to-purple-900/40 backdrop-blur-lg rounded-2xl p-8 border border-blue-400/30 mb-6">
            <h3 className="text-2xl font-bold text-white mb-6">🔍 Market Intelligence</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-bold text-blue-300 mb-3">What Competitors Cover</h4>
                <ul className="space-y-2">
                  {marketResearch.competitor_angles?.map((angle: string, i: number) => (
                    <li key={i} className="text-gray-300 flex items-start">
                      <span className="text-blue-400 mr-2">•</span>
                      {angle}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="text-lg font-bold text-green-300 mb-3">Content Gaps (Our Advantage)</h4>
                <ul className="space-y-2">
                  {marketResearch.content_gaps?.map((gap: string, i: number) => (
                    <li key={i} className="text-gray-300 flex items-start">
                      <span className="text-green-400 mr-2">✓</span>
                      {gap}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {marketResearch.orla3_unique_angles && (
              <div className="mt-6 pt-6 border-t border-white/10">
                <h4 className="text-lg font-bold text-yellow-300 mb-3">🎯 ORLA³ Unique Angles</h4>
                <ul className="space-y-2">
                  {marketResearch.orla3_unique_angles.map((angle: string, i: number) => (
                    <li key={i} className="text-white flex items-start">
                      <span className="text-yellow-400 mr-2">⭐</span>
                      {angle}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {marketResearch.market_gap && (
              <div className="mt-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <p className="text-yellow-200"><strong>Market Gap:</strong> {marketResearch.market_gap}</p>
              </div>
            )}
          </div>
        )}

        {blog && (
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-white">{blog.title}</h2>
              <span className="text-gray-400">{blog.estimated_read_time_min} min read</span>
            </div>

            <div className="prose prose-invert max-w-none mb-6">
              <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {blog.body_md}
              </div>
            </div>

            {saveMessage && (
              <div className="mb-4 bg-green-500/20 border border-green-500 rounded-lg p-4 text-green-200 text-center font-bold">
                {saveMessage}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-white/10">
              <button 
                onClick={saveToLibrary}
                className="bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-black font-bold py-3 px-6 rounded-lg transition-all"
              >
                💾 Save to Library
              </button>
              <Link href="/dashboard/carousel" className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all text-center">
                🎠 Atomize to Carousel
              </Link>
              <Link href="/dashboard/social" className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-all text-center">
                📱 Open Social Manager
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
