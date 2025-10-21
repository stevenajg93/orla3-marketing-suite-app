'use client';

import { useState } from 'react';
import Link from 'next/link';

const TEXT_PLATFORMS = [
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: 'from-blue-600 to-blue-700', limit: '1300 chars' },
  { id: 'twitter', name: 'X (Twitter)', icon: '🐦', color: 'from-sky-500 to-sky-600', limit: '280 chars' },
  { id: 'facebook', name: 'Facebook', icon: '👥', color: 'from-blue-500 to-blue-600', limit: '400 chars optimal' },
  { id: 'reddit', name: 'Reddit', icon: '🤖', color: 'from-orange-500 to-orange-600', limit: 'No hashtags' },
  { id: 'tumblr', name: 'Tumblr', icon: '📝', color: 'from-indigo-600 to-indigo-700', limit: '500 chars' }
];

export default function TextPublisher() {
  const [generating, setGenerating] = useState(false);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [publishing, setPublishing] = useState(false);
  const [blogData, setBlogData] = useState<any>(null);
  const [marketResearch, setMarketResearch] = useState<any>(null);
  const [atomizedPosts, setAtomizedPosts] = useState<any>(null);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState('');

  const togglePlatform = (platformId: string) => {
    if (selectedPlatforms.includes(platformId)) {
      setSelectedPlatforms(selectedPlatforms.filter(p => p !== platformId));
    } else {
      setSelectedPlatforms([...selectedPlatforms, platformId]);
    }
  };

  const selectAll = () => setSelectedPlatforms(TEXT_PLATFORMS.map(p => p.id));
  const deselectAll = () => setSelectedPlatforms([]);

  const autoGenerateEverything = async () => {
    setGenerating(true);
    setError('');
    setBlogData(null);
    setMarketResearch(null);
    setAtomizedPosts(null);

    try {
      const strategyRes = await fetch('http://localhost:8000/strategy/next-keyword');
      const strategy = await strategyRes.json();
      const nextKw = strategy.recommended_next;

      const researchRes = await fetch('http://localhost:8000/strategy/market-research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: nextKw.keyword })
      });
      const research = await researchRes.json();
      setMarketResearch(research);

      const blogRes = await fetch('http://localhost:8000/content/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword: nextKw.keyword,
          search_intent: nextKw.search_intent,
          target_length_words: 1500
        })
      });
      const blog = await blogRes.json();
      setBlogData({ ...blog, keyword: nextKw.keyword });

      const atomizeRes = await fetch('http://localhost:8000/atomize/blog-to-social', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          blog_title: blog.title,
          blog_content: blog.body_md,
          blog_url: 'https://orla3.com/blog',
          keyword: nextKw.keyword
        })
      });
      const atomized = await atomizeRes.json();
      
      const textPosts = {
        posts: atomized.posts.filter((p: any) => TEXT_PLATFORMS.some(tp => tp.id === p.platform)),
        hero_image_url: atomized.hero_image_url
      };
      
      setAtomizedPosts(textPosts);
      setSelectedPlatforms(textPosts.posts.map((p: any) => p.platform));

    } catch (err) {
      setError('Failed to auto-generate. Make sure backend is running.');
    } finally {
      setGenerating(false);
    }
  };

  const publishToAll = async () => {
    if (!atomizedPosts || selectedPlatforms.length === 0) {
      setError('Please generate content first');
      return;
    }

    setPublishing(true);
    setError('');
    setResults([]);

    try {
      const response = await fetch('http://localhost:8000/publisher/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: atomizedPosts.posts[0]?.content || '',
          platforms: selectedPlatforms,
          media_url: atomizedPosts.hero_image_url
        })
      });

      if (!response.ok) throw new Error('Failed to publish');

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError('Failed to publish. Check backend connection.');
    } finally {
      setPublishing(false);
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
              📝 Text Publisher
            </h1>
            <p className="text-gray-400 mt-2">Automated content for LinkedIn, Twitter, Facebook, Reddit & Tumblr</p>
            <Link href="/dashboard/video-publisher" className="inline-block mt-2 text-blue-400 hover:text-blue-300">
              → Switch to Video Publisher (TikTok, Instagram, YouTube)
            </Link>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-6 border border-green-400/30 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-white mb-2">🤖 Full Automation Mode</h3>
              <p className="text-green-100">Strategy → Market Research → Blog → 5 Text Platform Posts</p>
            </div>
            <button
              onClick={autoGenerateEverything}
              disabled={generating}
              className="bg-white hover:bg-green-50 text-green-700 font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50 whitespace-nowrap"
            >
              {generating ? '⚡ Generating...' : '🚀 Auto-Generate All'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-200 mb-6">
            {error}
          </div>
        )}

        {marketResearch && (
          <div className="bg-gradient-to-br from-blue-900/40 to-purple-900/40 backdrop-blur-lg rounded-2xl p-8 border border-blue-400/30 mb-6">
            <h3 className="text-2xl font-bold text-white mb-6">🔍 Market Intelligence</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-bold text-blue-300 mb-3">Competitor Angles</h4>
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
                <h4 className="text-lg font-bold text-green-300 mb-3">Our Advantage</h4>
                <ul className="space-y-2">
                  {marketResearch.orla3_unique_angles?.map((angle: string, i: number) => (
                    <li key={i} className="text-white flex items-start">
                      <span className="text-yellow-400 mr-2">⭐</span>
                      {angle}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {blogData && (
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-6">
            <h3 className="text-2xl font-bold text-white mb-4">📝 Generated Blog Post</h3>
            <h2 className="text-3xl font-bold text-yellow-400 mb-2">{blogData.title}</h2>
            <p className="text-gray-400 mb-4">{blogData.estimated_read_time_min} min read • Keyword: {blogData.keyword}</p>
            <div className="text-gray-300 leading-relaxed line-clamp-6">
              {blogData.body_md?.substring(0, 500)}...
            </div>
          </div>
        )}

        {atomizedPosts && (
          <>
            <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Generated Platform Posts</h2>
                <div className="flex gap-3">
                  <button onClick={selectAll} className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg text-sm">
                    Select All
                  </button>
                  <button onClick={deselectAll} className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg text-sm">
                    Deselect All
                  </button>
                </div>
              </div>

              <div className="mb-6">
                <img src={atomizedPosts.hero_image_url} alt="Hero" className="w-full h-64 object-cover rounded-lg" />
                <p className="text-gray-400 text-sm mt-2">Hero image for all platforms</p>
              </div>

              <div className="space-y-4">
                {atomizedPosts.posts.map((post: any) => {
                  const platform = TEXT_PLATFORMS.find(p => p.id === post.platform);
                  return (
                    <div
                      key={post.platform}
                      onClick={() => togglePlatform(post.platform)}
                      className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${
                        selectedPlatforms.includes(post.platform)
                          ? `bg-gradient-to-br ${platform?.color} border-white/40`
                          : 'bg-white/5 border-white/10 hover:border-white/30'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <span className="text-3xl">{platform?.icon}</span>
                          <div>
                            <h3 className="text-white font-bold">{platform?.name}</h3>
                            <p className="text-gray-400 text-sm">{platform?.limit}</p>
                          </div>
                        </div>
                        <span className="text-gray-400 text-sm">{post.character_count} chars</span>
                      </div>

                      <p className="text-white mb-3">{post.content}</p>

                      {post.hashtags && post.hashtags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {post.hashtags.map((tag: string, i: number) => (
                            <span key={i} className="bg-white/10 px-3 py-1 rounded-full text-sm text-blue-300">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <button
                onClick={publishToAll}
                disabled={publishing || selectedPlatforms.length === 0}
                className="w-full mt-6 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-black font-bold py-4 px-8 rounded-lg transition-all disabled:opacity-50"
              >
                {publishing ? '📤 Publishing...' : `🚀 Publish to ${selectedPlatforms.length} Platforms`}
              </button>
            </div>
          </>
        )}

        {results.length > 0 && (
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10">
            <h2 className="text-2xl font-bold text-white mb-6">Publishing Results</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.map((result, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-lg border ${
                    result.status === 'success' ? 'bg-green-900/30 border-green-500' :
                    result.status === 'ready' ? 'bg-blue-900/30 border-blue-500' :
                    'bg-red-900/30 border-red-500'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white capitalize">{result.platform}</span>
                    <span className={`text-sm px-2 py-1 rounded ${
                      result.status === 'success' ? 'bg-green-500' :
                      result.status === 'ready' ? 'bg-blue-500' : 'bg-red-500'
                    }`}>
                      {result.status}
                    </span>
                  </div>
                  {result.message && <p className="text-gray-300 text-sm">{result.message}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
