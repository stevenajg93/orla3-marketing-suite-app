"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import html2canvas from "html2canvas";
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

interface BrandAssets {
  brand_colors: string[];
  brand_fonts: string[];
  logo_url: string | null;
  primary_color: string | null;
  secondary_color: string | null;
}

export default function CarouselMakerPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [result, setResult] = useState<{ slides: Array<{ slide_number: number; hook: string; body: string; image_url?: string }> } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [caption, setCaption] = useState("");
  const exportRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [saveMessage, setSaveMessage] = useState("");
  const [brandAssets, setBrandAssets] = useState<BrandAssets>({
    brand_colors: ['#C8A530', '#3D2B63'], // Default fallback colors
    brand_fonts: [],
    logo_url: null,
    primary_color: '#C8A530',
    secondary_color: '#3D2B63'
  });

  const [formData, setFormData] = useState({
    post_summary: "Learn how to hire the perfect corporate videographer in the UK. Discover pricing factors, quality indicators, and expert tips.",
    target_platform: "instagram",
    angle: "problem-solution",
  });

  // Fetch brand assets on mount
  useEffect(() => {
    const fetchBrandAssets = async () => {
      try {
        const res = await fetch(`${config.apiUrl}/brand-assets`);
        if (res.ok) {
          const data = await res.json();
          if (data.success && data.brand_colors && data.brand_colors.length > 0) {
            setBrandAssets({
              brand_colors: data.brand_colors,
              brand_fonts: data.brand_fonts || [],
              logo_url: data.logo_url,
              primary_color: data.primary_color || data.brand_colors[0],
              secondary_color: data.secondary_color || data.brand_colors[1]
            });
            console.log('Loaded brand assets:', data);
          }
        }
      } catch (err) {
        console.error('Failed to fetch brand assets:', err);
      }
    };

    fetchBrandAssets();
  }, []);

  // Helper to get font family string with brand fonts
  const getBrandFontFamily = () => {
    if (brandAssets.brand_fonts && brandAssets.brand_fonts.length > 0) {
      return `${brandAssets.brand_fonts.map(f => `"${f}"`).join(', ')}, system-ui, -apple-system, sans-serif`;
    }
    return 'system-ui, -apple-system, sans-serif';
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setEditMode(false);

    try {
      const res = await fetch(`${config.apiUrl}/carousel/social/carousel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) throw new Error("Failed to generate carousel");

      const data = await res.json();
      setResult(data);
      setCaption(`${formData.post_summary.split('.')[0]}.\n\nSwipe through to learn more! 👉\n\nWhich tip resonates most with you? Comment below! 👇`);
      setEditMode(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };


  const saveToLibrary = async () => {
    if (!result) return;
    setSaveMessage("Exporting slides...");
    
    try {
      const brandedSlides = [];
      
      for (let i = 0; i < exportRefs.current.length; i++) {
        const slideElement = exportRefs.current[i];
        if (!slideElement) continue;

        slideElement.style.display = "block";
        const canvas = await html2canvas(slideElement, {
          backgroundColor: "#ffffff",
          scale: 1,
          width: 1080,
          height: 1080,
          logging: false,
          useCORS: true,
          allowTaint: true,
        });
        slideElement.style.display = "none";

        const imageData = canvas.toDataURL("image/png");
        brandedSlides.push({
          ...result.slides[i],
          branded_image: imageData
        });

        await new Promise(resolve => setTimeout(resolve, 100));
      }

      await fetch(`${config.apiUrl}/library/content`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: Date.now().toString(),
          title: result.slides?.[0]?.title || "Carousel Post",
          content_type: "carousel",
          content: JSON.stringify(brandedSlides),
          created_at: new Date().toISOString(),
          status: "draft",
          platform: formData.target_platform,
          tags: [formData.target_platform, formData.angle],
          metadata: {
            caption: caption,
            slideCount: result.slides?.length || 0
          }
        })
      });

      setSaveMessage("Saved!");
      setTimeout(() => setSaveMessage(""), 2000);
    } catch (err) {
      console.error(err);
      setSaveMessage("Failed");
    }
  };
  const handleExport = async () => {
    if (!result?.slides) return;
    
    setExporting(true);
    
    try {
      for (let i = 0; i < exportRefs.current.length; i++) {
        const slideElement = exportRefs.current[i];
        if (!slideElement) continue;

        // Make visible temporarily
        slideElement.style.display = 'block';

        const canvas = await html2canvas(slideElement, {
          backgroundColor: '#ffffff',
          scale: 1,
          width: 1080,
          height: 1080,
          logging: false,
          useCORS: true,
          allowTaint: true,
        });

        // Hide again
        slideElement.style.display = 'none';

        // Download
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `carousel-slide-${i + 1}.png`;
            link.click();
            URL.revokeObjectURL(url);
          }
        }, 'image/png');

        await new Promise(resolve => setTimeout(resolve, 800));
      }

      alert('All slides exported successfully! Check your downloads folder.');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  const updateSlide = (index: number, field: string, value: string) => {
    const updated = { ...result };
    updated.slides[index][field] = value;
    setResult(updated);
  };

  const regenerateImage = async (index: number) => {
    const query = prompt("Enter new search term for image:", result.slides[index].alt_hint);
    if (!query) return;

    try {
      const res = await fetch(`https://api.unsplash.com/search/photos?query=${query}&per_page=1&orientation=landscape`, {
        headers: { Authorization: `Client-ID ${process.env.NEXT_PUBLIC_UNSPLASH_KEY}` }
      });
      const data = await res.json();
      if (data.results?.[0]) {
        updateSlide(index, 'image_url', data.results[0].urls.regular);
      }
    } catch (e) {
      alert("Failed to fetch new image");
    }
  };

  const renderSlideContent = (slide: { slide_number: number; hook: string; body: string; image_url?: string }, idx: number, isExport: boolean = false) => {
    const isFirstSlide = idx === 0;
    const isLastSlide = idx === result.slides.length - 1;
    const totalSlides = result.slides.length;
    const scale = isExport ? 2 : 1;

    if (isFirstSlide) {
      return (
        <>
          <img
            src={slide.image_url}
            alt={slide.alt_hint}
            className="w-full h-full object-cover"
            crossOrigin="anonymous"
          />
          <div className="absolute inset-0 bg-black/40" />
          
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center" style={{ padding: `${50 * scale}px` }}>
            <div
              style={{
                fontSize: `${120 * scale}px`,
                lineHeight: 0.95,
                fontWeight: 900,
                color: 'white',
                textShadow: '0 4px 30px rgba(0,0,0,1)',
                fontFamily: getBrandFontFamily(),
                marginBottom: `${20 * scale}px`,
                width: '100%',
                whiteSpace: 'pre-wrap',
              }}
            >
              {slide.title}
            </div>
            <div 
              style={{ 
                fontSize: `${36 * scale}px`,
                lineHeight: 1.4,
                color: 'rgba(255,255,255,0.95)',
                textShadow: '0 2px 15px rgba(0,0,0,1)',
                maxWidth: `${500 * scale}px`,
                marginBottom: `${20 * scale}px`,
              }}
            >
              {slide.body.split('.')[0]}.
            </div>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: `${10 * scale}px`,
              fontSize: `${28 * scale}px`,
              fontWeight: 600,
              color: 'rgba(255,255,255,0.9)',
              textShadow: '0 2px 10px rgba(0,0,0,1)',
            }}>
              <span>Swipe for more</span>
              <span style={{ fontSize: `${40 * scale}px` }}>→</span>
            </div>
          </div>
        </>
      );
    }

    return (
      <div className="h-full flex flex-col justify-center items-center text-center relative" style={{ padding: `${50 * scale}px` }}>
        <div className="absolute" style={{ top: `${30 * scale}px`, left: `${30 * scale}px` }}>
          <div style={{
            width: `${60 * scale}px`,
            height: `${60 * scale}px`,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: `${36 * scale}px`,
            fontWeight: 700,
            backgroundColor: brandAssets.primary_color || '#C8A530',
            color: 'white',
          }}>
            {idx}
          </div>
        </div>

        <div className="absolute" style={{ top: `${30 * scale}px`, right: `${30 * scale}px` }}>
          <div style={{
            padding: `${6 * scale}px ${15 * scale}px`,
            borderRadius: `${20 * scale}px`,
            fontSize: `${24 * scale}px`,
            fontWeight: 600,
            backgroundColor: brandAssets.secondary_color || '#3D2B63',
            color: 'white',
          }}>
            {idx + 1}/{totalSlides}
          </div>
        </div>

        <div style={{
          fontSize: `${60 * scale}px`,
          fontWeight: 700,
          color: 'black',
          fontFamily: getBrandFontFamily(),
          marginBottom: `${30 * scale}px`,
          textAlign: 'center',
        }}>
          {slide.title}
        </div>

        <div style={{
          fontSize: `${32 * scale}px`,
          lineHeight: 1.6,
          color: '#374151',
          fontFamily: getBrandFontFamily(),
          textAlign: 'center',
        }}>
          {slide.body}
        </div>

        {isLastSlide && (
          <div style={{
            marginTop: `${30 * scale}px`,
            paddingTop: `${30 * scale}px`,
            borderTop: `${4 * scale}px solid ${brandAssets.primary_color || '#C8A530'}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: `${10 * scale}px`,
          }}>
            {brandAssets.logo_url && (
              <img
                src={brandAssets.logo_url.startsWith('http') ? brandAssets.logo_url : `${config.apiUrl}/${brandAssets.logo_url}`}
                alt="Brand Logo"
                style={{
                  maxHeight: `${40 * scale}px`,
                  maxWidth: `${200 * scale}px`,
                  objectFit: 'contain',
                }}
                crossOrigin="anonymous"
              />
            )}
            {!brandAssets.logo_url && (
              <div style={{
                fontSize: `${28 * scale}px`,
                fontWeight: 600,
                color: brandAssets.primary_color || '#C8A530',
              }}>
                ORLA³
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900">
      {/* Hidden export versions - 1080x1080 */}
      <div style={{ position: 'absolute', left: '-9999px', top: 0 }}>
        {result?.slides?.map((slide, idx: number) => (
          <div
            key={`export-${idx}`}
            ref={(el) => {
              exportRefs.current[idx] = el;
            }}
            style={{
              width: '1080px',
              height: '1080px',
              position: 'relative',
              backgroundColor: 'white',
              display: 'none',
            }}
          >
            {renderSlideContent(slide, idx, true)}
          </div>
        ))}
      </div>

      <div className="border-b border-white/10 backdrop-blur-xl bg-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push("/dashboard")} className="text-2xl hover:scale-110 transition">
              ←
            </button>
            <div className="text-4xl">🎠</div>
            <div>
              <h1 className="text-2xl font-bold text-white">Carousel Maker</h1>
              <p className="text-sm text-cobalt-300">
                Instagram-ready carousels with your brand colors, fonts & logo
                {brandAssets.brand_colors.length > 2 && <span className="ml-2 text-green-400">Branded</span>}
              </p>
            </div>
          </div>
          {result && editMode && (
            <button
              onClick={handleExport}
              disabled={exporting}
              className="px-6 py-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold transition disabled:opacity-50"
            >
              {exporting ? "⏳ Exporting..." : "📥 Export Carousel"}
            </button>
          )}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {!result && (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-6">
            <h2 className="text-xl font-bold text-white mb-4">Generate Carousel</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-cobalt-300 mb-2">Post Summary</label>
                <textarea
                  value={formData.post_summary}
                  onChange={(e) => setFormData({ ...formData, post_summary: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt"
                  placeholder="Summarize your content..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-cobalt-300 mb-2">Platform</label>
                  <select
                    value={formData.target_platform}
                    onChange={(e) => setFormData({ ...formData, target_platform: e.target.value })}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
                  >
                    <option value="instagram">Instagram</option>
                    <option value="linkedin">LinkedIn</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-cobalt-300 mb-2">Angle</label>
                  <select
                    value={formData.angle}
                    onChange={(e) => setFormData({ ...formData, angle: e.target.value })}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
                  >
                    <option value="problem-solution">Problem-Solution</option>
                    <option value="myth-busting">Myth-Busting</option>
                    <option value="checklist">Checklist</option>
                    <option value="case-study">Case Study</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleGenerate}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold disabled:opacity-50 transition"
              >
                {loading ? "⏳ Generating..." : "Generate Professional Carousel"}
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 mb-6">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {result && editMode && (
          <div className="space-y-6">
            <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <h3 className="text-lg font-bold text-white mb-3">Post Caption</h3>
              <textarea
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                rows={4}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt resize-none font-mono text-sm"
              />
              <p className="text-xs text-gold mt-2">Optimized for Instagram engagement</p>
            </div>

            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white">Edit Your Carousel</h2>
              <span className="px-3 py-1 bg-cobalt/20 border border-cobalt/50 rounded-full text-cobalt-300 text-sm">
                {result.platform} • {result.slides?.length || 0} slides
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {result.slides?.map((slide, idx: number) => {
                const isFirstSlide = idx === 0;
                const isLastSlide = idx === result.slides.length - 1;
                const totalSlides = result.slides.length;
                
                return (
                  <div
                    key={idx}
                    className="bg-white rounded-xl overflow-hidden shadow-2xl hover:shadow-3xl transition"
                    style={{ width: '540px', height: '540px' }}
                  >
                    <div className="relative w-full h-full group bg-white">
                      {isFirstSlide && (
                        <>
                          <img
                            src={slide.image_url}
                            alt={slide.alt_hint}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-black/40" />
                          
                          <button
                            onClick={() => regenerateImage(idx)}
                            className="absolute top-3 right-3 p-2 bg-white/90 hover:bg-white rounded-lg text-black opacity-0 group-hover:opacity-100 transition z-10 text-sm font-semibold"
                            title="Change image"
                          >
                            🔄
                          </button>

                          <div className="absolute inset-0 flex flex-col items-center justify-center p-10 text-center">
                            <textarea
                              value={slide.title}
                              onChange={(e) => updateSlide(idx, 'title', e.target.value)}
                              rows={2}
                              className="text-6xl font-black text-white bg-transparent border-2 border-transparent hover:border-white/30 focus:border-white/50 focus:outline-none px-2 py-2 rounded w-full mb-4 text-center resize-none leading-none"
                              style={{
                                textShadow: '0 4px 30px rgba(0,0,0,1)',
                                fontFamily: getBrandFontFamily(),
                                fontWeight: 900,
                              }}
                            />
                            <textarea
                              value={slide.body}
                              onChange={(e) => updateSlide(idx, 'body', e.target.value)}
                              rows={2}
                              className="text-lg text-white/95 bg-transparent border-2 border-transparent hover:border-white/30 focus:border-white/50 focus:outline-none px-2 py-1 rounded w-full max-w-lg leading-snug resize-none mb-4"
                              style={{ textShadow: '0 2px 15px rgba(0,0,0,1)' }}
                            />
                            <div className="flex items-center gap-2 text-white/90 text-sm font-semibold" style={{ textShadow: '0 2px 10px rgba(0,0,0,1)' }}>
                              <span>Swipe for more</span>
                              <span className="text-xl">→</span>
                            </div>
                          </div>
                        </>
                      )}

                      {!isFirstSlide && (
                        <div className="h-full flex flex-col justify-center items-center p-10 text-center relative">
                          <div className="absolute top-6 left-6">
                            <div className="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold" style={{ backgroundColor: brandAssets.primary_color || '#C8A530', color: 'white' }}>
                              {idx}
                            </div>
                          </div>

                          <div className="absolute top-6 right-6">
                            <div className="px-3 py-1 rounded-full text-xs font-semibold" style={{ backgroundColor: brandAssets.secondary_color || '#3D2B63', color: 'white' }}>
                              {idx + 1}/{totalSlides}
                            </div>
                          </div>

                          <input
                            type="text"
                            value={slide.title}
                            onChange={(e) => updateSlide(idx, 'title', e.target.value)}
                            className="text-3xl font-bold text-black bg-transparent border-2 border-transparent hover:border-gray-300 focus:border-gray-400 focus:outline-none px-3 py-2 rounded w-full mb-6 text-center"
                            style={{ fontFamily: getBrandFontFamily(), fontWeight: 700 }}
                          />

                          <textarea
                            value={slide.body}
                            onChange={(e) => updateSlide(idx, 'body', e.target.value)}
                            rows={isLastSlide ? 4 : 6}
                            className="text-base leading-relaxed text-gray-700 bg-transparent border-2 border-transparent hover:border-gray-300 focus:border-gray-400 focus:outline-none px-4 py-2 rounded w-full resize-none"
                            style={{ fontFamily: getBrandFontFamily() }}
                          />

                          {isLastSlide && (
                            <div className="mt-6 pt-6 border-t-2 flex flex-col items-center gap-2" style={{ borderColor: brandAssets.primary_color || '#C8A530' }}>
                              {brandAssets.logo_url && (
                                <img
                                  src={brandAssets.logo_url.startsWith('http') ? brandAssets.logo_url : `${config.apiUrl}/${brandAssets.logo_url}`}
                                  alt="Brand Logo"
                                  style={{
                                    maxHeight: '20px',
                                    maxWidth: '100px',
                                    objectFit: 'contain',
                                  }}
                                />
                              )}
                              {!brandAssets.logo_url && (
                                <p className="text-sm font-semibold" style={{ color: brandAssets.primary_color || '#C8A530' }}>ORLA³</p>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {saveMessage && <div className="mb-3 text-center bg-green-500/20 border border-green-500 rounded px-3 py-1 text-green-200 text-sm font-bold">{saveMessage}</div>}
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setResult(null);
                  setEditMode(false);
                }}
                className="flex-1 py-3 bg-white/10 hover:bg-white/20 rounded-lg text-white font-semibold transition"
              >
                ← Start Over
              </button>
              <button onClick={saveToLibrary} className="flex-1 py-3 bg-gradient-to-r from-gold to-gold-600 hover:from-gold-600 hover:to-gold-700 rounded-lg text-black font-semibold transition">
                Save
              </button>
              <button
                onClick={handleExport}
                disabled={exporting}
                className="flex-1 py-3 rounded-lg text-white font-semibold transition disabled:opacity-50"
                style={{ background: 'linear-gradient(135deg, #C8A530 0%, #E8C14D 100%)' }}
              >
                {exporting ? "⏳ Exporting..." : "📥 Export All Slides"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
