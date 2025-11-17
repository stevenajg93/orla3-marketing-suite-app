#!/bin/bash
#
# Script to apply media library fixes
# Run from project root

set -e

echo "🔧 Applying media library fixes..."

# Backup original file
cp app/dashboard/social/page.tsx app/dashboard/social/page.tsx.backup
echo "✅ Created backup: app/dashboard/social/page.tsx.backup"

# Fix already applied: Sticky tabs (done via Edit tool)
echo "✅ Sticky tabs fix already applied"

# Now let's add loading state and create a patch file for the cloud storage tab
cat > /tmp/cloud-storage-tab.txt << 'EOFCLOUD'

                {/* Cloud Storage Tab */}
                {mediaLibraryTab === 'cloud' && (
                  <div>
                    {mediaLoading ? (
                      <div className="flex items-center justify-center py-12">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt mx-auto mb-4"></div>
                          <p className="text-gray-400">Loading cloud storage...</p>
                        </div>
                      </div>
                    ) : connectedProviders.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-5xl mb-4">☁️</div>
                        <h3 className="text-xl font-bold text-white mb-2">No Cloud Storage Connected</h3>
                        <p className="text-gray-400 mb-4">Connect Google Drive, Dropbox, or OneDrive</p>
                        <button
                          onClick={() => window.open('/dashboard/settings/cloud-storage', '_blank')}
                          className="px-6 py-3 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white font-semibold transition"
                        >
                          Connect Cloud Storage
                        </button>
                      </div>
                    ) : (
                      <div>
                        <div className="mb-6 flex gap-3 flex-wrap">
                          {connectedProviders.includes('google_drive') && (
                            <button
                              onClick={() => { setCloudStorageProvider('google_drive'); loadDriveFiles(''); }}
                              className={\`px-4 py-2 rounded-lg font-semibold transition \${cloudStorageProvider === 'google_drive' ? 'bg-cobalt text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20'}\`}
                            >
                              📁 Google Drive
                            </button>
                          )}
                          {connectedProviders.includes('dropbox') && (
                            <button
                              onClick={() => { setCloudStorageProvider('dropbox'); loadDropboxFiles(''); }}
                              className={\`px-4 py-2 rounded-lg font-semibold transition \${cloudStorageProvider === 'dropbox' ? 'bg-cobalt text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20'}\`}
                            >
                              📦 Dropbox
                            </button>
                          )}
                          {connectedProviders.includes('onedrive') && (
                            <button
                              onClick={() => { setCloudStorageProvider('onedrive'); loadOnedriveFiles(''); }}
                              className={\`px-4 py-2 rounded-lg font-semibold transition \${cloudStorageProvider === 'onedrive' ? 'bg-cobalt text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20'}\`}
                            >
                              🗂️ OneDrive
                            </button>
                          )}
                        </div>

                        {cloudStorageProvider === 'google_drive' && driveAssets && (
                          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                            {driveAssets.map((file: any) => (
                              <div key={file.id} onClick={() => handleMediaSelect(file)} className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition cursor-pointer">
                                {file.thumbnail ? (
                                  <img src={file.thumbnail} alt={file.name} className="w-full aspect-square object-cover" />
                                ) : (
                                  <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                                    <span className="text-4xl">📄</span>
                                  </div>
                                )}
                                <div className="p-3">
                                  <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {cloudStorageProvider === 'dropbox' && dropboxFiles && (
                          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                            {dropboxFiles.map((file: any) => (
                              <div key={file.id} onClick={() => handleMediaSelect(file)} className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-royal transition cursor-pointer">
                                <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                                  <span className="text-4xl">📄</span>
                                </div>
                                <div className="p-3">
                                  <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {cloudStorageProvider === 'onedrive' && onedriveFiles && (
                          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                            {onedriveFiles.map((file: any) => (
                              <div key={file.id} onClick={() => handleMediaSelect(file)} className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition cursor-pointer">
                                <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                                  <span className="text-4xl">📄</span>
                                </div>
                                <div className="p-3">
                                  <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

EOFCLOUD

echo "✅ Created cloud storage tab template"
echo ""
echo "📋 Next Steps:"
echo "1. Insert cloud storage tab code after line 1446 in app/dashboard/social/page.tsx"
echo "2. The code is saved in: /tmp/cloud-storage-tab.txt"
echo "3. Build and test: npm run build"
echo "4. Commit changes"
echo ""
echo "To restore backup if needed: cp app/dashboard/social/page.tsx.backup app/dashboard/social/page.tsx"
