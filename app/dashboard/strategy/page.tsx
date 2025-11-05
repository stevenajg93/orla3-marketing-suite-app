'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

type Strategy = {
  brand_voice: {
    tone: string;
    personality: string[];
    key_characteristics: string[];
  };
  messaging_pillars: string[];
  language_patterns: {
    preferred_phrases: string[];
    vocabulary: string[];
    writing_style: string;
  };
  dos_and_donts: {
    dos: string[];
    donts: string[];
  };
  target_audience: {
    primary: string;
    characteristics: string[];
  };
  content_themes: string[];
  competitive_positioning?: {
    unique_value: string;
    copy_and_adapt: string[];
    gaps_to_exploit: string[];
    avoid: string[];
  };
  generated_at?: string;
  assets_analyzed?: number;
  competitors_included?: number;
  categories?: {
    guidelines: number;
    voice_samples: number;
    community: number;
  };
};

export default function StrategyPlanner() {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStrategy();
  }, []);

  const loadStrategy = async () => {
    setLoading(true);
    try {
      const data = await api.get('/strategy/current');
      
      if (data.success) {
        setStrategy(data.strategy);
        setError('');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to load strategy');
    } finally {
      setLoading(false);
    }
  };

  const analyzeStrategy = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const data = await api.post('/strategy/analyze');
      
      if (data.success) {
        setStrategy(data.strategy);
        alert('✅ Brand strategy created successfully!');
      } else {
        alert(`❌ ${data.error}`);
      }
    } catch (err) {
      alert('❌ Analysis failed. Check console for details.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <Link href="/dashboard" className="text-purple-400 hover:text-purple-300 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-purple-400 mb-2">
            🎪 Strategy Planner
          </h1>
          <p className="text-xl text-gray-300">AI-powered brand voice analysis & competitive strategy</p>
        </div>

        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Brand Voice + Competitive Analysis</h2>
              <p className="text-gray-400">
                {strategy 
                  ? `Last analyzed: ${new Date(strategy.generated_at || '').toLocaleDateString()}` + 
                    (strategy.competitors_included ? ` • ${strategy.competitors_included} competitors included` : '')
                  : 'No strategy generated yet'
                }
              </p>
            </div>
            <button
              onClick={analyzeStrategy}
              disabled={analyzing}
              className={`px-8 py-4 rounded-xl font-bold text-lg transition ${
                analyzing
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white'
              }`}
            >
              {analyzing ? '🧠 Analyzing...' : '🚀 Analyze Brand Voice'}
            </button>
          </div>

          {strategy?.assets_analyzed && (
            <div className="mt-6 grid grid-cols-5 gap-4">
              <div className="bg-violet-900/40 border border-violet-400/30 rounded-lg p-4 text-center">
                <div className="text-3xl mb-2">📁</div>
                <div className="text-2xl font-bold text-white">{strategy.assets_analyzed}</div>
                <div className="text-sm text-gray-400">Total Assets</div>
              </div>
              <div className="bg-blue-900/40 border border-blue-400/30 rounded-lg p-4 text-center">
                <div className="text-3xl mb-2">📋</div>
                <div className="text-2xl font-bold text-white">{strategy.categories?.guidelines || 0}</div>
                <div className="text-sm text-gray-400">Guidelines</div>
              </div>
              <div className="bg-green-900/40 border border-green-400/30 rounded-lg p-4 text-center">
                <div className="text-3xl mb-2">✍️</div>
                <div className="text-2xl font-bold text-white">{strategy.categories?.voice_samples || 0}</div>
                <div className="text-sm text-gray-400">Voice Samples</div>
              </div>
              <div className="bg-purple-900/40 border border-purple-400/30 rounded-lg p-4 text-center">
                <div className="text-3xl mb-2">💬</div>
                <div className="text-2xl font-bold text-white">{strategy.categories?.community || 0}</div>
                <div className="text-sm text-gray-400">Community</div>
              </div>
              <div className="bg-rose-900/40 border border-rose-400/30 rounded-lg p-4 text-center">
                <div className="text-3xl mb-2">🔍</div>
                <div className="text-2xl font-bold text-white">{strategy.competitors_included || 0}</div>
                <div className="text-sm text-gray-400">Competitors</div>
              </div>
            </div>
          )}
        </div>

        {loading ? (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-12 border border-white/10 text-center">
            <div className="text-6xl mb-4 animate-pulse">🧠</div>
            <p className="text-xl text-white">Loading strategy...</p>
          </div>
        ) : !strategy ? (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-12 border border-white/10 text-center">
            <div className="text-6xl mb-4">🎯</div>
            <h2 className="text-2xl font-bold text-white mb-2">No Strategy Yet</h2>
            <p className="text-gray-400 mb-6">
              Upload brand voice assets and add competitors, then click "Analyze Brand Voice"
            </p>
            <div className="flex gap-4 justify-center">
              <Link
                href="/dashboard/brand-voice"
                className="inline-block px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 rounded-lg text-white font-bold transition"
              >
                📤 Upload Brand Assets
              </Link>
              <Link
                href="/dashboard/competitor"
                className="inline-block px-6 py-3 bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600 rounded-lg text-white font-bold transition"
              >
                🔍 Add Competitors
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Competitive Positioning - NEW SECTION */}
            {strategy.competitive_positioning && (
              <div className="bg-gradient-to-br from-rose-900/40 to-pink-900/40 backdrop-blur-lg rounded-xl p-6 border border-rose-400/30">
                <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                  <span className="text-3xl">⚔️</span>
                  Competitive Positioning
                </h3>
                <div className="space-y-6">
                  <div>
                    <span className="text-rose-400 font-semibold text-lg">Our Unique Value:</span>
                    <p className="text-white mt-2 text-lg">{strategy.competitive_positioning.unique_value}</p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-4">
                      <h4 className="text-green-400 font-semibold mb-3 flex items-center gap-2">
                        <span>✅</span> Copy & Adapt
                      </h4>
                      <ul className="space-y-2">
                        {strategy.competitive_positioning.copy_and_adapt.map((item, i) => (
                          <li key={i} className="text-sm text-gray-200 flex items-start gap-2">
                            <span className="text-green-400">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-4">
                      <h4 className="text-yellow-400 font-semibold mb-3 flex items-center gap-2">
                        <span>🎯</span> Gaps to Exploit
                      </h4>
                      <ul className="space-y-2">
                        {strategy.competitive_positioning.gaps_to_exploit.map((item, i) => (
                          <li key={i} className="text-sm text-gray-200 flex items-start gap-2">
                            <span className="text-yellow-400">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-4">
                      <h4 className="text-red-400 font-semibold mb-3 flex items-center gap-2">
                        <span>⛔</span> Avoid
                      </h4>
                      <ul className="space-y-2">
                        {strategy.competitive_positioning.avoid.map((item, i) => (
                          <li key={i} className="text-sm text-gray-200 flex items-start gap-2">
                            <span className="text-red-400">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Brand Voice */}
            <div className="bg-gradient-to-br from-violet-900/40 to-purple-900/40 backdrop-blur-lg rounded-xl p-6 border border-violet-400/30">
              <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                <span className="text-3xl">🎤</span>
                Brand Voice Profile
              </h3>
              <div className="space-y-4">
                <div>
                  <span className="text-violet-400 font-semibold">Tone:</span>
                  <p className="text-white mt-1">{strategy.brand_voice.tone}</p>
                </div>
                <div>
                  <span className="text-violet-400 font-semibold">Personality:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {strategy.brand_voice.personality.map((trait, i) => (
                      <span key={i} className="px-3 py-1 bg-violet-500/20 border border-violet-500 rounded-full text-violet-300 text-sm font-semibold">
                        {trait}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-violet-400 font-semibold">Key Characteristics:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {strategy.brand_voice.key_characteristics.map((char, i) => (
                      <span key={i} className="px-3 py-1 bg-purple-500/20 border border-purple-500 rounded-full text-purple-300 text-sm font-semibold">
                        {char}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Messaging Pillars */}
            <div className="bg-gradient-to-br from-blue-900/40 to-cyan-900/40 backdrop-blur-lg rounded-xl p-6 border border-blue-400/30">
              <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                <span className="text-3xl">🏛️</span>
                Messaging Pillars
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {strategy.messaging_pillars.map((pillar, i) => (
                  <div key={i} className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-300">#{i + 1}</div>
                    <p className="text-white mt-2">{pillar}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Language Patterns */}
            <div className="bg-gradient-to-br from-green-900/40 to-emerald-900/40 backdrop-blur-lg rounded-xl p-6 border border-green-400/30">
              <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                <span className="text-3xl">✍️</span>
                Language Patterns
              </h3>
              <div className="space-y-4">
                <div>
                  <span className="text-green-400 font-semibold">Writing Style:</span>
                  <p className="text-white mt-1">{strategy.language_patterns.writing_style}</p>
                </div>
                <div>
                  <span className="text-green-400 font-semibold">Preferred Phrases:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {strategy.language_patterns.preferred_phrases.map((phrase, i) => (
                      <span key={i} className="px-3 py-1 bg-green-500/20 border border-green-500 rounded-full text-green-300 text-sm">
                        "{phrase}"
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-green-400 font-semibold">Key Vocabulary:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {strategy.language_patterns.vocabulary.map((word, i) => (
                      <span key={i} className="px-3 py-1 bg-emerald-500/20 border border-emerald-500 rounded-full text-emerald-300 text-sm">
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Do's and Don'ts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gradient-to-br from-green-900/40 to-teal-900/40 backdrop-blur-lg rounded-xl p-6 border border-green-400/30">
                <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                  <span className="text-3xl">✅</span>
                  Do's
                </h3>
                <ul className="space-y-2">
                  {strategy.dos_and_donts.dos.map((item, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className="text-green-400 text-xl">•</span>
                      <span className="text-white">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-gradient-to-br from-red-900/40 to-rose-900/40 backdrop-blur-lg rounded-xl p-6 border border-red-400/30">
                <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                  <span className="text-3xl">❌</span>
                  Don'ts
                </h3>
                <ul className="space-y-2">
                  {strategy.dos_and_donts.donts.map((item, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className="text-red-400 text-xl">•</span>
                      <span className="text-white">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Target Audience */}
            <div className="bg-gradient-to-br from-yellow-900/40 to-orange-900/40 backdrop-blur-lg rounded-xl p-6 border border-yellow-400/30">
              <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                <span className="text-3xl">🎯</span>
                Target Audience
              </h3>
              <div className="space-y-4">
                <div>
                  <span className="text-yellow-400 font-semibold">Primary Audience:</span>
                  <p className="text-white mt-1">{strategy.target_audience.primary}</p>
                </div>
                <div>
                  <span className="text-yellow-400 font-semibold">Characteristics:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {strategy.target_audience.characteristics.map((char, i) => (
                      <span key={i} className="px-3 py-1 bg-yellow-500/20 border border-yellow-500 rounded-full text-yellow-300 text-sm font-semibold">
                        {char}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Content Themes */}
            <div className="bg-gradient-to-br from-pink-900/40 to-rose-900/40 backdrop-blur-lg rounded-xl p-6 border border-pink-400/30">
              <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                <span className="text-3xl">📚</span>
                Content Themes
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {strategy.content_themes.map((theme, i) => (
                  <div key={i} className="bg-pink-500/10 border border-pink-500/30 rounded-lg p-4 text-center">
                    <p className="text-white font-semibold">{theme}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
