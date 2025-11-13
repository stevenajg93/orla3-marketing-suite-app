'use client';

import { useState } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
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

  const stripMarkdown = (markdown: string): string => {
    // Remove markdown syntax for clean text storage
    return markdown
      .replace(/^#{1,6}\s+/gm, '')  // Remove headers
      .replace(/\*\*(.+?)\*\*/g, '$1')  // Remove bold
      .replace(/\*(.+?)\*/g, '$1')  // Remove italic
      .replace(/\[(.+?)\]\(.+?\)/g, '$1')  // Remove links, keep text
      .replace(/`(.+?)`/g, '$1')  // Remove code blocks
      .replace(/^\s*[-*+]\s+/gm, '')  // Remove list markers
      .replace(/^\s*\d+\.\s+/gm, '')  // Remove numbered list markers
      .trim();
  };

  const saveToLibrary = async () => {
    if (!blog) return;

    setSaveMessage('');

    try {
      // Clean the full content - remove markdown syntax
      const cleanFullContent = stripMarkdown(blog.body_md);

      // Store both markdown and metadata for flexible use
      const response = await fetch(`${config.apiUrl}/library/content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: Date.now().toString(),
          title: blog.title,
          content_type: 'blog',
          content: cleanFullContent,  // Clean content without markdown
          metadata: JSON.stringify({
            title: blog.title,
            slug: blog.slug,
            meta_description: blog.meta_description,
            full_markdown: blog.body_md,  // Store markdown for WordPress publishing
            full_clean: cleanFullContent   // Full clean text for social posting
          }),
          created_at: new Date().toISOString(),
          status: 'draft',
          tags: [keyword, searchIntent]
        })
      });


      setSaveMessage('Saved to Media Library!');
      setTimeout(() => setSaveMessage(''), 3000);
      return true;
    } catch (err) {
      setSaveMessage('Failed to save');
      return false;
    }
  };

  const saveAndOpenSocialManager = async () => {
    if (!blog) return;

    setSaveMessage('Saving to library...');

    const saved = await saveToLibrary();

    if (saved) {
      // Store blog data in localStorage for social manager to pick up
      localStorage.setItem('pendingBlogPost', JSON.stringify({
        title: blog.title,
        content: stripMarkdown(blog.body_md),
        metadata: {
          title: blog.title,
          slug: blog.slug,
          meta_description: blog.meta_description,
          full_markdown: blog.body_md,
          full_clean: stripMarkdown(blog.body_md)
        }
      }));

      // Navigate to social manager
      router.push('/dashboard/social');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-gray-400 hover:text-white mb-2 inline-block">
              ← Back to Dashboard
            </Link>
            <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-gold-200">
              Blog Writer
            </h1>
            <p className="text-gray-400 mt-2">AI-powered SEO content engine with live market research</p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-6 border border-green-400/30 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">Autonomous Mode</h3>
              <p className="text-green-100">Strategic keyword + market research + blog generation</p>
            </div>
            <button
              onClick={autoGenerate}
              disabled={loading}
              className="bg-white hover:bg-green-50 text-green-700 font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {researching ? 'Researching Market...' : loading ? 'Generating...' : 'Auto-Generate'}
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
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gold"
              />
            </div>

            <div>
              <label className="block text-white font-bold mb-2">Search Intent</label>
              <input
                type="text"
                value={searchIntent}
                onChange={(e) => setSearchIntent(e.target.value)}
                placeholder="e.g., Find best corporate videographers"
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gold"
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
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-gold"
              />
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={doMarketResearch}
              disabled={researching}
              className="flex-1 bg-gradient-to-r from-cobalt to-cobalt-700 hover:from-blue-700 hover:to-blue-800 text-white font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {researching ? 'Researching...' : 'Research Market First'}
            </button>
            
            <button
              onClick={generateBlog}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-gold to-gold-600 hover:from-gold-600 hover:to-gold-700 text-black font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Generating Blog...' : 'Generate Blog Post'}
            </button>
          </div>

          {error && (
            <div className="mt-4 bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-200">
              {error}
            </div>
          )}
        </div>

        {marketResearch && (
          <div className="bg-gradient-to-br from-royal-900/40 to-cobalt-900/40 backdrop-blur-lg rounded-2xl p-8 border border-cobalt-400/30 mb-6">
            <h3 className="text-2xl font-bold text-white mb-6">Market Intelligence</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-bold text-cobalt-300 mb-3">What Competitors Cover</h4>
                <ul className="space-y-2">
                  {marketResearch.competitor_angles?.map((angle: string, i: number) => (
                    <li key={i} className="text-gray-300 flex items-start">
                      <span className="text-cobalt-300 mr-2">•</span>
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
                      <span className="text-green-400 mr-2"></span>
                      {gap}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {marketResearch.orla3_unique_angles && (
              <div className="mt-6 pt-6 border-t border-white/10">
                <h4 className="text-lg font-bold text-gold-300 mb-3">ORLA³ Unique Angles</h4>
                <ul className="space-y-2">
                  {marketResearch.orla3_unique_angles.map((angle: string, i: number) => (
                    <li key={i} className="text-white flex items-start">
                      <span className="text-gold-400 mr-2"></span>
                      {angle}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {marketResearch.market_gap && (
              <div className="mt-4 bg-gold/10 border border-gold/30 rounded-lg p-4">
                <p className="text-gold-200"><strong>Market Gap:</strong> {marketResearch.market_gap}</p>
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

            <div className="prose prose-invert prose-lg max-w-none mb-6">
              <ReactMarkdown
                className="text-gray-300 leading-relaxed"
                components={{
                  h2: ({node, ...props}) => <h2 className="text-2xl font-bold text-white mt-8 mb-4" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-xl font-bold text-white mt-6 mb-3" {...props} />,
                  p: ({node, ...props}) => <p className="mb-4 text-gray-300" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc list-inside mb-4 space-y-2" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-4 space-y-2" {...props} />,
                  li: ({node, ...props}) => <li className="text-gray-300" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold text-white" {...props} />,
                  table: ({node, ...props}) => <table className="w-full border-collapse border border-gray-700 my-6" {...props} />,
                  thead: ({node, ...props}) => <thead className="bg-gray-800" {...props} />,
                  th: ({node, ...props}) => <th className="border border-gray-700 px-4 py-2 text-white font-bold" {...props} />,
                  td: ({node, ...props}) => <td className="border border-gray-700 px-4 py-2 text-gray-300" {...props} />,
                }}
              >
                {blog.body_md}
              </ReactMarkdown>
            </div>

            {saveMessage && (
              <div className="mb-4 bg-green-500/20 border border-green-500 rounded-lg p-4 text-green-200 text-center font-bold">
                {saveMessage}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-white/10">
              <button
                onClick={saveToLibrary}
                className="bg-gradient-to-r from-gold to-gold-600 hover:from-gold-600 hover:to-gold-700 text-black font-bold py-3 px-6 rounded-lg transition-all"
              >
                Save to Library
              </button>
              <Link href="/dashboard/carousel" className="bg-cobalt hover:bg-cobalt-700 text-white font-bold py-3 px-6 rounded-lg transition-all text-center">
                🎠 Atomize to Carousel
              </Link>
              <button
                onClick={saveAndOpenSocialManager}
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-all text-center"
              >
                Open in Social Manager
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
