'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function ArticlesPage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState<string | null>(null);
  const [publishStatus, setPublishStatus] = useState<any>({});

  useEffect(() => {
    loadExistingArticles();
  }, []);

  const loadExistingArticles = async () => {
    try {
      const response = await fetch('/api/generate', { method: 'GET' });
      const data = await response.json();
      if (data.success) {
        setArticles(data.articles);
      }
    } catch (error) {
      console.error('Error loading articles:', error);
    }
  };

  const generateNewArticles = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/generate', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        setArticles(data.articles);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const publishToWordPress = async (article: any, index: number) => {
    const articleId = `article-${index}`;
    setPublishing(articleId);
    
    try {
      // Extract title from content (usually first line)
      const lines = article.content.split('\n');
      const title = lines[0].replace(/^#+\s*/, '').replace(/[*_]/g, '');
      const content = lines.slice(1).join('\n');

      const response = await fetch('/api/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title || article.topic,
          content: content,
          status: 'draft', // Change to 'publish' to publish immediately
          action: 'create'
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setPublishStatus({
          ...publishStatus,
          [articleId]: {
            success: true,
            message: data.message,
            link: data.post.link
          }
        });
      } else {
        setPublishStatus({
          ...publishStatus,
          [articleId]: {
            success: false,
            message: data.error || 'Failed to publish'
          }
        });
      }
    } catch (error) {
      setPublishStatus({
        ...publishStatus,
        [articleId]: {
          success: false,
          message: 'Connection error'
        }
      });
    } finally {
      setPublishing(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Generated Articles</h1>
            <p className="text-gray-600">Your ORLA3 content ready to publish</p>
          </div>
          <Link 
            href="/dashboard"
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            ← Back to Dashboard
          </Link>
        </div>

        <div className="mb-6 flex gap-4">
          <button
            onClick={generateNewArticles}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg"
          >
            {loading ? '⏳ Generating...' : '📝 Generate New Articles'}
          </button>
          {articles.length > 0 && (
            <button
              onClick={loadExistingArticles}
              className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-6 rounded-lg"
            >
              🔄 Refresh
            </button>
          )}
        </div>

        {articles.length > 0 ? (
          <div className="space-y-6">
            <div className="bg-green-100 border-l-4 border-green-500 p-4 rounded">
              <p className="text-green-700">
                ✅ {articles.length} articles ready to publish to WordPress
              </p>
            </div>
            
            {articles.map((article, index) => {
              const articleId = `article-${index}`;
              const status = publishStatus[articleId];
              
              return (
                <div key={index} className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-xl font-bold text-blue-600 mb-2">{article.topic}</h2>
                  
                  {status && (
                    <div className={`mb-4 p-3 rounded-lg ${
                      status.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      <p className="font-medium">{status.message}</p>
                      {status.link && (
                        <a 
                          href={status.link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="underline text-sm"
                        >
                          View on WordPress →
                        </a>
                      )}
                    </div>
                  )}
                  
                  <div className="prose max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700 max-h-96 overflow-y-auto">
                      {article.content}
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t flex justify-between items-center">
                    <span className="text-sm text-gray-500">
                      Generated: {new Date(article.generated).toLocaleString()}
                    </span>
                    <div className="flex gap-2">
                      <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">
                        ✏️ Edit
                      </button>
                      <button 
                        onClick={() => publishToWordPress(article, index)}
                        disabled={publishing === articleId}
                        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg text-sm"
                      >
                        {publishing === articleId ? '📤 Publishing...' : '📤 Publish to WordPress'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">📝</div>
            <p className="text-gray-500 mb-4">No articles generated yet</p>
            <p className="text-gray-400">Click "Generate New Articles" to create content</p>
          </div>
        )}
      </div>
    </div>
  );
}
