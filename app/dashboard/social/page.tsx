"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

type PostType = "text" | "video" | "carousel";
type Platform = "instagram" | "linkedin" | "facebook" | "x" | "tiktok" | "youtube" | "reddit" | "tumblr";

export default function SocialManagerPage() {
  const router = useRouter();
  const [postType, setPostType] = useState<PostType>("text");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>(["instagram"]);
  const [caption, setCaption] = useState("");
  const [generatingCaption, setGeneratingCaption] = useState(false);
  const [scheduleDate, setScheduleDate] = useState("");

  const platforms = [
    { id: "instagram" as Platform, name: "Instagram", icon: "📷", color: "from-pink-500 to-purple-500" },
    { id: "linkedin" as Platform, name: "LinkedIn", icon: "💼", color: "from-blue-600 to-blue-700" },
    { id: "facebook" as Platform, name: "Facebook", icon: "👍", color: "from-blue-500 to-blue-600" },
    { id: "x" as Platform, name: "X", icon: "❌", color: "from-slate-800 to-slate-900" },
    { id: "tiktok" as Platform, name: "TikTok", icon: "🎵", color: "from-black to-pink-500" },
    { id: "youtube" as Platform, name: "YouTube", icon: "▶️", color: "from-red-600 to-red-700" },
    { id: "reddit" as Platform, name: "Reddit", icon: "🤖", color: "from-orange-500 to-red-500" },
    { id: "tumblr" as Platform, name: "Tumblr", icon: "🔷", color: "from-indigo-500 to-blue-600" },
  ];

  const togglePlatform = (platform: Platform) => {
    if (selectedPlatforms.includes(platform)) {
      setSelectedPlatforms(selectedPlatforms.filter(p => p !== platform));
    } else {
      setSelectedPlatforms([...selectedPlatforms, platform]);
    }
  };

  const generateCaption = async () => {
    setGeneratingCaption(true);
    // TODO: Call caption API
    setTimeout(() => {
      setCaption("🎬 Finding the perfect videographer for your brand? Here's what you need to know!\n\nSwipe through to learn the key factors that separate great from mediocre. 👉\n\n#VideoMarketing #ContentCreation #UKBusiness");
      setGeneratingCaption(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="bg-white/5 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-purple-400 hover:text-purple-300 mb-2 flex items-center gap-2 text-sm"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">
            📱 Social Manager
          </h1>
          <p className="text-purple-300 mt-1">Create, schedule, and manage all your social content</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* LEFT COLUMN - Post Creation */}
          <div className="lg:col-span-2 space-y-6">
            {/* Post Type Selector */}
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <h2 className="text-xl font-bold text-white mb-4">Post Type</h2>
              <div className="flex gap-3">
                <button
                  onClick={() => setPostType("text")}
                  className={`flex-1 py-3 rounded-lg font-semibold transition ${
                    postType === "text"
                      ? "bg-gradient-to-r from-green-500 to-emerald-500 text-white"
                      : "bg-white/10 text-gray-400 hover:bg-white/20"
                  }`}
                >
                  📝 Text Post
                </button>
                <button
                  onClick={() => setPostType("video")}
                  className={`flex-1 py-3 rounded-lg font-semibold transition ${
                    postType === "video"
                      ? "bg-gradient-to-r from-red-500 to-pink-500 text-white"
                      : "bg-white/10 text-gray-400 hover:bg-white/20"
                  }`}
                >
                  🎬 Video Post
                </button>
                <button
                  onClick={() => setPostType("carousel")}
                  className={`flex-1 py-3 rounded-lg font-semibold transition ${
                    postType === "carousel"
                      ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                      : "bg-white/10 text-gray-400 hover:bg-white/20"
                  }`}
                >
                  🎨 Carousel
                </button>
              </div>
            </div>

            {/* Caption Editor */}
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">Caption</h2>
                <button
                  onClick={generateCaption}
                  disabled={generatingCaption}
                  className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold transition disabled:opacity-50"
                >
                  {generatingCaption ? "✨ Generating..." : "✨ Generate Caption"}
                </button>
              </div>
              <textarea
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Write your caption here or generate one with AI..."
                rows={8}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-500 resize-none"
              />
              <div className="flex items-center justify-between mt-3">
                <span className="text-sm text-gray-400">{caption.length} characters</span>
                {selectedPlatforms.includes("x") && caption.length > 280 && (
                  <span className="text-sm text-red-400 font-semibold">⚠️ Too long for X (280 char limit)</span>
                )}
              </div>
            </div>

            {/* Media Selection */}
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <h2 className="text-xl font-bold text-white mb-4">Media</h2>
              <div className="border-2 border-dashed border-white/20 rounded-lg p-12 text-center hover:border-purple-500/50 transition cursor-pointer">
                <div className="text-6xl mb-4">📁</div>
                <p className="text-gray-400 mb-2">Click to browse Media Library</p>
                <p className="text-sm text-gray-500">or drag and drop files here</p>
              </div>
            </div>

            {/* Schedule */}
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <h2 className="text-xl font-bold text-white mb-4">Schedule</h2>
              <div className="flex gap-4">
                <input
                  type="datetime-local"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
                <button className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-lg text-white font-semibold transition">
                  Post Now
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN - Platform Selection & Preview */}
          <div className="space-y-6">
            {/* Platform Selector */}
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <h2 className="text-xl font-bold text-white mb-4">Platforms</h2>
              <div className="space-y-3">
                {platforms.map((platform) => (
                  <button
                    key={platform.id}
                    onClick={() => togglePlatform(platform.id)}
                    className={`w-full p-4 rounded-lg border-2 transition ${
                      selectedPlatforms.includes(platform.id)
                        ? `border-transparent bg-gradient-to-r ${platform.color} text-white`
                        : "border-white/20 bg-white/5 text-gray-400 hover:border-white/40"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{platform.icon}</span>
                        <span className="font-semibold">{platform.name}</span>
                      </div>
                      {selectedPlatforms.includes(platform.id) && (
                        <span className="text-xl">✓</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Preview */}
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <h2 className="text-xl font-bold text-white mb-4">Preview</h2>
              <div className="bg-white rounded-lg p-4 aspect-square flex items-center justify-center">
                <p className="text-gray-400 text-center">
                  Select platforms to see preview
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
