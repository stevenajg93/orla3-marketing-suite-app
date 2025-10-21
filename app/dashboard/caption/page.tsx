"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function CaptionGeneratorPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    topic: "Finding quality videographers in the UK marketplace",
    platform: "instagram",
    tone: "professional",
    include_hashtags: true,
    include_emojis: true,
    variations: 3,
  });

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/social/caption", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) throw new Error("Failed to generate captions");

      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopied(index);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="border-b border-white/10 backdrop-blur-xl bg-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push("/dashboard")} className="text-2xl hover:scale-110 transition">
              ←
            </button>
            <div className="text-4xl">✍️</div>
            <div>
              <h1 className="text-2xl font-bold text-white">Caption Generator</h1>
              <p className="text-sm text-purple-300">AI-powered captions for every platform</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-6">
          <h2 className="text-xl font-bold text-white mb-4">Generate Captions</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-purple-300 mb-2">What's your post about?</label>
              <textarea
                value={formData.topic}
                onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-500"
                placeholder="Describe your post topic..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-purple-300 mb-2">Platform</label>
                <select
                  value={formData.platform}
                  onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                  className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="instagram">Instagram</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="twitter">Twitter</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-purple-300 mb-2">Tone</label>
                <select
                  value={formData.tone}
                  onChange={(e) => setFormData({ ...formData, tone: e.target.value })}
                  className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="professional">Professional</option>
                  <option value="casual">Casual</option>
                  <option value="inspirational">Inspirational</option>
                  <option value="humorous">Humorous</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-purple-300 mb-2">Variations</label>
                <select
                  value={formData.variations}
                  onChange={(e) => setFormData({ ...formData, variations: Number(e.target.value) })}
                  className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="3">3 options</option>
                  <option value="5">5 options</option>
                  <option value="10">10 options</option>
                </select>
              </div>

              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.include_emojis}
                    onChange={(e) => setFormData({ ...formData, include_emojis: e.target.checked })}
                    className="w-5 h-5 rounded border-white/20 bg-white/10 text-purple-500 focus:ring-purple-500"
                  />
                  <span className="text-sm text-white">Include Emojis</span>
                </label>
              </div>

              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.include_hashtags}
                    onChange={(e) => setFormData({ ...formData, include_hashtags: e.target.checked })}
                    className="w-5 h-5 rounded border-white/20 bg-white/10 text-purple-500 focus:ring-purple-500"
                  />
                  <span className="text-sm text-white">Include Hashtags</span>
                </label>
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold disabled:opacity-50 transition"
            >
              {loading ? "⏳ Generating..." : "✨ Generate Captions"}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 mb-6">
            <p className="text-red-200">❌ {error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-white">Your Captions</h2>
              <span className="px-3 py-1 bg-blue-500/20 border border-blue-500/50 rounded-full text-blue-300 text-sm capitalize">
                {result.platform}
              </span>
            </div>

            {result.captions?.map((caption: string, idx: number) => (
              <div
                key={idx}
                className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 hover:border-purple-500/50 transition group"
              >
                <div className="flex items-start justify-between mb-4">
                  <span className="px-3 py-1 bg-purple-500/20 rounded-full text-purple-300 text-xs font-semibold">
                    Option {idx + 1}
                  </span>
                  <button
                    onClick={() => copyToClipboard(caption, idx)}
                    className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm font-semibold transition"
                  >
                    {copied === idx ? "✅ Copied!" : "📋 Copy"}
                  </button>
                </div>
                <p className="text-white leading-relaxed whitespace-pre-wrap">{caption}</p>
              </div>
            ))}

            {result.hashtags && result.hashtags.length > 0 && (
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h3 className="text-lg font-bold text-white mb-3">📌 Suggested Hashtags</h3>
                <div className="flex flex-wrap gap-2">
                  {result.hashtags.map((tag: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full text-blue-300 text-sm"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
                <button
                  onClick={() => copyToClipboard(result.hashtags.map((t: string) => `#${t}`).join(' '), -1)}
                  className="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm font-semibold transition"
                >
                  {copied === -1 ? "✅ Copied!" : "📋 Copy All Hashtags"}
                </button>
              </div>
            )}

            <button
              onClick={() => setResult(null)}
              className="w-full py-3 bg-white/10 hover:bg-white/20 rounded-lg text-white font-semibold transition"
            >
              ← Generate New Captions
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
