"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ArticlesLibraryPage() {
  const router = useRouter();
  const [articles, setArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    try {
      const res = await fetch("/api/articles");
      const data = await res.json();
      setArticles(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filteredArticles = articles.filter(article =>
    article.topic?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="border-b border-white/10 backdrop-blur-xl bg-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push("/dashboard")} className="text-2xl hover:scale-110 transition">
              ←
            </button>
            <div className="text-4xl">📚</div>
            <div>
              <h1 className="text-2xl font-bold text-white">Articles Library</h1>
              <p className="text-sm text-purple-300">{articles.length} articles generated</p>
            </div>
          </div>
          <button
            onClick={() => router.push("/dashboard/draft")}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold transition"
          >
            + New Article
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-6">
          <input
            type="text"
            placeholder="🔍 Search articles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-500"
          />
        </div>

        {loading ? (
          <div className="text-center text-white py-12">
            <div className="text-4xl mb-4">⏳</div>
            <p>Loading articles...</p>
          </div>
        ) : filteredArticles.length === 0 ? (
          <div className="text-center text-white py-12">
            <div className="text-6xl mb-4">📝</div>
            <h2 className="text-2xl font-bold mb-2">No articles yet</h2>
            <p className="text-purple-300 mb-6">Generate your first article to get started!</p>
            <button
              onClick={() => router.push("/dashboard/draft")}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg text-white font-semibold"
            >
              Create First Article
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredArticles.map((article, idx) => (
              <div
                key={idx}
                className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 hover:border-white/30 transition group cursor-pointer"
                onClick={() => router.push(`/dashboard/articles/${article.id || idx}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="text-3xl">📄</div>
                  <span className="px-2 py-1 bg-green-500/20 border border-green-500/50 rounded text-green-300 text-xs">
                    Published
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-purple-300 transition">
                  {article.topic || "Untitled Article"}
                </h3>
                <p className="text-sm text-purple-300 mb-4 line-clamp-2">
                  {article.content?.substring(0, 100)}...
                </p>
                <div className="flex items-center justify-between text-xs text-purple-400">
                  <span>Generated {new Date(article.generated).toLocaleDateString()}</span>
                  <button className="hover:text-white transition">View →</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
