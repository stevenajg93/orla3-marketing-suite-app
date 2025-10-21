"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function DraftGeneratorPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    keyword: "corporate videography UK",
    search_intent: "informational",
    target_length_words: 800,
  });

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/content/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) throw new Error("Failed to generate draft");

      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="border-b border-white/10 backdrop-blur-xl bg-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push("/dashboard")} className="text-2xl hover:scale-110 transition">
              ←
            </button>
            <div className="text-4xl">📝</div>
            <div>
              <h1 className="text-2xl font-bold text-white">Draft Generator</h1>
              <p className="text-sm text-purple-300">AI-powered content creation</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">Generate New Draft</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-purple-300 mb-2">Keyword</label>
              <input
                type="text"
                value={formData.keyword}
                onChange={(e) => setFormData({ ...formData, keyword: e.target.value })}
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-500"
                placeholder="Enter target keyword"
              />
            </div>

            <div>
              <label className="block text-sm text-purple-300 mb-2">Search Intent</label>
              <select
                value={formData.search_intent}
                onChange={(e) => setFormData({ ...formData, search_intent: e.target.value })}
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
              >
                <option value="informational">Informational</option>
                <option value="commercial">Commercial</option>
                <option value="transactional">Transactional</option>
                <option value="navigational">Navigational</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-purple-300 mb-2">Target Length (words)</label>
              <input
                type="number"
                value={formData.target_length_words}
                onChange={(e) => setFormData({ ...formData, target_length_words: parseInt(e.target.value) })}
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold disabled:opacity-50 transition"
            >
              {loading ? "⏳ Generating..." : "✨ Generate Draft"}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 mb-6">
            <p className="text-red-200">❌ {error}</p>
          </div>
        )}

        {result && (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-8 border border-white/10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">✅ Generated Article</h2>
              <span className="px-3 py-1 bg-green-500/20 border border-green-500/50 rounded-full text-green-300 text-sm">
                {result.estimated_read_time_min} min read
              </span>
            </div>

            <article className="prose prose-invert max-w-none">
              <h1 className="text-3xl font-bold text-white mb-4">{result.title}</h1>
              
              <div className="flex flex-wrap gap-2 mb-6">
                {result.tags?.map((tag: string, i: number) => (
                  <span key={i} className="px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full text-purple-300 text-sm">
                    #{tag}
                  </span>
                ))}
              </div>

              <div className="text-purple-300 mb-6 text-sm space-y-1">
                <p><strong>Meta Description:</strong> {result.meta_description}</p>
                <p><strong>Slug:</strong> /{result.slug}</p>
                <p><strong>Category:</strong> {result.category}</p>
              </div>

              <div className="bg-black/30 rounded-lg p-6 text-white leading-relaxed whitespace-pre-wrap font-serif text-base">
                {result.body_md}
              </div>

              {result.cta && (
                <div className="mt-8 p-6 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-xl text-center">
                  <h3 className="text-xl font-bold text-white mb-3">{result.cta.headline}</h3>
                  <a 
                    href={result.cta.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg text-white font-semibold hover:shadow-lg transition"
                  >
                    {result.cta.button_label}
                  </a>
                </div>
              )}
            </article>
          </div>
        )}
      </div>
    </div>
  );
}
