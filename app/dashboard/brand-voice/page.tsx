'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

type Asset = {
  id: string;
  filename: string;
  category: string;
  size: number;
  text_preview: string;
  uploaded_at: string;
};

type DriveFolder = {
  id: string;
  name: string;
};

type DriveFile = {
  id: string;
  name: string;
  mimeType: string;
};

const CATEGORIES = [
  { id: 'guidelines', name: 'Brand Guidelines', icon: '📋', description: 'Official brand docs, style guides' },
  { id: 'voice_samples', name: 'Voice Samples', icon: '✍️', description: 'Your emails, blogs, copy' },
  { id: 'community_videographer', name: 'Videographer Community', icon: '🎥', description: 'Discord chats, forums' },
  { id: 'community_client', name: 'Client Community', icon: '💼', description: 'Client conversations' },
  { id: 'logos', name: 'Logos & Assets', icon: '🎨', description: 'Visual brand assets' }
];

export default function BrandVoice() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [uploading, setUploading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('guidelines');
  const [dragActive, setDragActive] = useState(false);
  
  // Drive integration
  const [showDriveModal, setShowDriveModal] = useState(false);
  const [driveFolders, setDriveFolders] = useState<DriveFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [driveFiles, setDriveFiles] = useState<DriveFile[]>([]);
  const [loadingDrive, setLoadingDrive] = useState(false);

  useEffect(() => {
    loadAssets();
  }, []);

  const loadAssets = async () => {
    try {
      const res = await fetch('http://localhost:8000/brand-voice/assets');
      const data = await res.json();
      setAssets(data.assets || []);
    } catch (err) {
      console.error('Failed to load assets');
    }
  };

  const loadDriveFolders = async () => {
    try {
      const res = await fetch('http://localhost:8000/drive/folders');
      const data = await res.json();
      setDriveFolders(data.folders || []);
    } catch (err) {
      console.error('Failed to load Drive folders');
    }
  };

  const loadDriveFiles = async (folderId: string = '') => {
    setLoadingDrive(true);
    try {
      // If no folderId, load the Marketing root folder
      if (!folderId && driveFolders.length > 0) {
        // Use the first folder (Marketing Root)
        folderId = driveFolders[0].id;
      }
      
      const endpoint = `http://localhost:8000/drive/folder/${folderId}/files`;
      const res = await fetch(endpoint);
      const data = await res.json();
      setDriveFiles(data.files || []);
      setSelectedFolder(folderId);
    } catch (err) {
      console.error('Failed to load Drive files');
    } finally {
      setLoadingDrive(false);
    }
  };

  const importFromDrive = async (fileId: string, fileName: string) => {
    try {
      setUploading(true);
      const res = await fetch(`http://localhost:8000/brand-voice/import-from-drive?file_id=${fileId}&filename=${fileName}&category=${selectedCategory}`, {
        method: 'POST'
      });
      
      if (res.ok) {
        loadAssets();
        alert('✅ File imported successfully!');
      } else {
        alert('❌ Import failed');
      }
    } catch (err) {
      console.error('Import failed');
      alert('❌ Import failed');
    } finally {
      setUploading(false);
    }
  };

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    const formData = new FormData();
    
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const res = await fetch(`http://localhost:8000/brand-voice/upload?category=${selectedCategory}`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        loadAssets();
      }
    } catch (err) {
      console.error('Upload failed');
      alert('Upload failed. Check console for details.');
    } finally {
      setUploading(false);
    }
  };

  const deleteAsset = async (assetId: string) => {
    if (!confirm('Delete this asset?')) return;

    try {
      await fetch(`http://localhost:8000/brand-voice/assets/${assetId}`, {
        method: 'DELETE'
      });
      loadAssets();
    } catch (err) {
      console.error('Delete failed');
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const getCategoryAssets = (categoryId: string) => {
    return assets.filter(a => a.category === categoryId);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <Link href="/dashboard" className="text-purple-400 hover:text-purple-300 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 mb-2">
            🎯 Brand Voice
          </h1>
          <p className="text-xl text-gray-300">Train AI with your authentic voice and brand assets</p>
        </div>

        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Upload Training Assets</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`p-4 rounded-lg border-2 transition ${
                  selectedCategory === cat.id
                    ? 'border-cyan-500 bg-cyan-500/20'
                    : 'border-white/20 bg-white/5 hover:border-white/40'
                }`}
              >
                <div className="text-3xl mb-2">{cat.icon}</div>
                <div className="text-sm font-semibold text-white">{cat.name}</div>
                <div className="text-xs text-gray-400 mt-1">{cat.description}</div>
              </button>
            ))}
          </div>

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition ${
              dragActive
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-white/20 hover:border-cyan-500/50'
            }`}
          >
            <div className="text-6xl mb-4">📤</div>
            <p className="text-xl text-white mb-2">
              {uploading ? 'Uploading...' : 'Drag & drop files here'}
            </p>
            <p className="text-gray-400 mb-4">
              Supported: TXT, DOCX, PDF, JSON (Discord exports), MD
            </p>
            <div className="flex gap-4 justify-center">
              <label className="inline-block px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 rounded-lg text-white font-bold cursor-pointer transition">
                <input
                  type="file"
                  multiple
                  onChange={(e) => handleFiles(e.target.files)}
                  className="hidden"
                  accept=".txt,.docx,.pdf,.json,.md,.png,.jpg,.jpeg,.gif,.svg,.mp4,.mov,.avi,.zip,.csv,.xlsx"
                />
                📁 Browse Files
              </label>
              <button
                onClick={() => {
                  loadDriveFolders();
                  loadDriveFiles();
                  setShowDriveModal(true);
                }}
                className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-bold transition"
              >
                🔗 Import from Google Drive
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {CATEGORIES.map(category => {
            const categoryAssets = getCategoryAssets(category.id);
            if (categoryAssets.length === 0) return null;

            return (
              <div key={category.id} className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">{category.icon}</span>
                  <h3 className="text-xl font-bold text-white">{category.name}</h3>
                  <span className="px-3 py-1 bg-cyan-500/20 border border-cyan-500 rounded-full text-cyan-300 text-sm font-bold">
                    {categoryAssets.length} files
                  </span>
                </div>

                <div className="space-y-3">
                  {categoryAssets.map(asset => (
                    <div key={asset.id} className="bg-white/5 rounded-lg p-4 flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <p className="font-semibold text-white">{asset.filename}</p>
                          <span className="text-xs text-gray-500">{formatFileSize(asset.size)}</span>
                        </div>
                        <p className="text-sm text-gray-400 line-clamp-2">{asset.text_preview}</p>
                        <p className="text-xs text-gray-600 mt-2">
                          {new Date(asset.uploaded_at).toLocaleDateString()}
                        </p>
                      </div>
                      <button
                        onClick={() => deleteAsset(asset.id)}
                        className="ml-4 text-red-400 hover:text-red-300 text-xl"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {assets.length === 0 && (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-12 border border-white/10 text-center">
            <div className="text-6xl mb-4">🎯</div>
            <h2 className="text-2xl font-bold text-white mb-2">No Training Assets Yet</h2>
            <p className="text-gray-400 mb-6">
              Upload your brand guidelines, writing samples, and community chats to train the AI
            </p>
          </div>
        )}

        {/* Google Drive Modal */}
        {showDriveModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-gradient-to-br from-slate-900 to-purple-900 rounded-2xl border border-white/20 max-w-6xl w-full max-h-[80vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">🔗 Import from Google Drive</h2>
                <button onClick={() => setShowDriveModal(false)} className="text-gray-400 hover:text-white text-2xl">×</button>
              </div>

              <div className="flex-1 overflow-hidden flex">
                {/* Sidebar */}
                <div className="w-64 border-r border-white/10 p-4 overflow-y-auto">
                  <h3 className="text-sm font-bold text-white mb-3">Folders</h3>
                  <button
                    onClick={() => loadDriveFiles('')}
                    className={`w-full text-left p-3 rounded-lg mb-2 transition ${
                      selectedFolder === ''
                        ? 'bg-green-600 text-white'
                        : 'bg-white/10 text-gray-300 hover:bg-white/20'
                    }`}
                  >
                    📁 All Files
                  </button>
                  {driveFolders.map(folder => (
                    <button
                      key={folder.id}
                      onClick={() => loadDriveFiles(folder.id)}
                      className={`w-full text-left p-3 rounded-lg mb-2 transition truncate ${
                        selectedFolder === folder.id
                          ? 'bg-green-600 text-white'
                          : 'bg-white/10 text-gray-300 hover:bg-white/20'
                      }`}
                    >
                      📁 {folder.name}
                    </button>
                  ))}
                </div>

                {/* Files */}
                <div className="flex-1 p-6 overflow-y-auto">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    {loadingDrive ? 'Loading...' : `Select Files to Import`}
                  </h3>
                  <div className="space-y-2">
                    {driveFiles.map(file => {
                      const isFolder = file.mimeType === 'application/vnd.google-apps.folder';
                      return (
                        <div key={file.id} className="p-4 bg-white/5 border border-white/10 rounded-lg flex items-center justify-between">
                          <div className="flex items-center gap-3 flex-1">
                            <span className="text-2xl">{isFolder ? '📁' : '📄'}</span>
                            <span className="text-white truncate">{file.name}</span>
                          </div>
                          {isFolder ? (
                            <button
                              onClick={() => loadDriveFiles(file.id)}
                              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white font-semibold transition"
                            >
                              Browse →
                            </button>
                          ) : (
                            <button
                              onClick={() => importFromDrive(file.id, file.name)}
                              disabled={uploading}
                              className="px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg text-white font-semibold transition disabled:opacity-50"
                            >
                              {uploading ? '...' : 'Import'}
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  {driveFiles.length === 0 && !loadingDrive && (
                    <p className="text-gray-400 text-center py-12">No files in this folder</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
