# Media Library Bug Fixes

## Issues Identified

### 1. ❌ Cloud Storage Tab Missing Rendering Code
**Problem:** Button exists but clicking it shows nothing
**Location:** `app/dashboard/social/page.tsx` line 1369
**Fix:** Add rendering code for `mediaLibraryTab === 'cloud'` after Generated Content tab

### 2. ❌ Tab Navigation Hidden By Content
**Problem:** When content loads, tab buttons at top get covered/hidden
**Location:** `app/dashboard/social/page.tsx` line 1355
**Fix:** Make tabs `sticky top-0 z-10 bg-slate-900` with `flex-shrink-0`

### 3. ❌ Slow Media Loading (Minutes Wait Time)
**Problem:** Modal loads all providers synchronously on open
**Location:** `app/dashboard/social/page.tsx` lines 152-157
**Fix:** Add loading indicator, load providers lazily when tab is clicked

### 4. ❌ Content Vanishes on Navigation Return
**Problem:** JWT token expires, API returns SYSTEM_USER's empty data
**Location:** All pages using `/library/content` endpoint
**Fix:** Add token refresh logic or show explicit "session expired" message

## Critical Fixes to Apply

### Fix 1: Add Sticky Tabs with Loading State

**File:** `app/dashboard/social/page.tsx`
**Line:** 1354-1355

**Change From:**
```tsx
{/* Tabs */}
<div className="px-6 pt-4 flex gap-3 border-b border-white/10 overflow-x-auto">
```

**Change To:**
```tsx
{/* Tabs - Sticky to prevent content overlap */}
<div className="sticky top-0 z-20 bg-slate-900 px-6 pt-4 flex gap-3 border-b border-white/10 overflow-x-auto flex-shrink-0">
```

### Fix 2: Add Loading Indicator at Modal Open

**File:** `app/dashboard/social/page.tsx`
**Line:** 1400 (in Content Area div)

**Add at start of content area:**
```tsx
{/* Loading State */}
{(mediaLoading || !libraryContent) && mediaLibraryTab === 'generated' && (
  <div className="flex items-center justify-center py-12">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt mx-auto mb-4"></div>
      <p className="text-gray-400">Loading media library...</p>
    </div>
  </div>
)}
```

### Fix 3: Add Missing Cloud Storage Tab Rendering

**File:** `app/dashboard/social/page.tsx`
**Line:** After line 1446 (after Generated Content tab closes)

**Add This Entire Section:**
```tsx
{/* Cloud Storage Tab */}
{mediaLibraryTab === 'cloud' && (
  <div>
    {connectedProviders.length === 0 ? (
      <div className="text-center py-12">
        <div className="text-5xl mb-4">☁️</div>
        <h3 className="text-xl font-bold text-white mb-2">No Cloud Storage Connected</h3>
        <p className="text-gray-400 mb-4">Connect Google Drive, Dropbox, or OneDrive to access your files</p>
        <button
          onClick={() => window.open('/dashboard/settings/cloud-storage', '_blank')}
          className="px-6 py-3 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white font-semibold transition"
        >
          Connect Cloud Storage
        </button>
      </div>
    ) : (
      <div>
        {/* Provider Selector */}
        <div className="mb-6 flex gap-3">
          {connectedProviders.includes('google_drive') && (
            <button
              onClick={() => {
                setCloudStorageProvider('google_drive');
                loadDriveFiles('');
              }}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                cloudStorageProvider === 'google_drive'
                  ? 'bg-cobalt text-white'
                  : 'bg-white/10 text-gray-400 hover:bg-white/20'
              }`}
            >
              📁 Google Drive
            </button>
          )}
          {connectedProviders.includes('dropbox') && (
            <button
              onClick={() => {
                setCloudStorageProvider('dropbox');
                loadDropboxFiles('');
              }}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                cloudStorageProvider === 'dropbox'
                  ? 'bg-cobalt text-white'
                  : 'bg-white/10 text-gray-400 hover:bg-white/20'
              }`}
            >
              📦 Dropbox
            </button>
          )}
          {connectedProviders.includes('onedrive') && (
            <button
              onClick={() => {
                setCloudStorageProvider('onedrive');
                loadOnedriveFiles('');
              }}
              className={`px-4 py-2 rounded-lg font-semibold transition ${
                cloudStorageProvider === 'onedrive'
                  ? 'bg-cobalt text-white'
                  : 'bg-white/10 text-gray-400 hover:bg-white/20'
              }`}
            >
              🗂️ OneDrive
            </button>
          )}
        </div>

        {/* Loading */}
        {mediaLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt mx-auto mb-4"></div>
              <p className="text-gray-400">Loading files from {cloudStorageProvider}...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Google Drive Files */}
            {cloudStorageProvider === 'google_drive' && (
              <div>
                {(driveAssets.length === 0 && driveFolders.length === 0) ? (
                  <div className="text-center py-12">
                    <p className="text-gray-400">No files found in Google Drive</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Folders */}
                    {driveFolders.map((folder: any) => (
                      <div
                        key={folder.id}
                        onClick={() => loadDriveFiles(folder.id)}
                        className="bg-white/5 rounded-lg p-4 border border-white/10 hover:border-cobalt transition cursor-pointer"
                      >
                        <div className="text-4xl mb-2">📁</div>
                        <h4 className="text-white font-bold text-sm truncate">{folder.name}</h4>
                      </div>
                    ))}
                    {/* Files */}
                    {driveAssets.map((file: any) => (
                      <div
                        key={file.id}
                        onClick={() => handleMediaSelect(file)}
                        className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition cursor-pointer"
                      >
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
              </div>
            )}

            {/* Dropbox Files */}
            {cloudStorageProvider === 'dropbox' && (
              <div>
                {(dropboxFiles.length === 0 && dropboxFolders.length === 0) ? (
                  <div className="text-center py-12">
                    <p className="text-gray-400">No files found in Dropbox</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    {dropboxFolders.map((folder: any) => (
                      <div
                        key={folder.id}
                        onClick={() => loadDropboxFiles(folder.path)}
                        className="bg-white/5 rounded-lg p-4 border border-white/10 hover:border-royal transition cursor-pointer"
                      >
                        <div className="text-4xl mb-2">📁</div>
                        <h4 className="text-white font-bold text-sm truncate">{folder.name}</h4>
                      </div>
                    ))}
                    {dropboxFiles.map((file: any) => (
                      <div
                        key={file.id}
                        onClick={() => handleMediaSelect(file)}
                        className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-royal transition cursor-pointer"
                      >
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

            {/* OneDrive Files */}
            {cloudStorageProvider === 'onedrive' && (
              <div>
                {(onedriveFiles.length === 0 && onedriveFolders.length === 0) ? (
                  <div className="text-center py-12">
                    <p className="text-gray-400">No files found in OneDrive</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    {onedriveFolders.map((folder: any) => (
                      <div
                        key={folder.id}
                        onClick={() => loadOnedriveFiles(`items/${folder.id}`)}
                        className="bg-white/5 rounded-lg p-4 border border-white/10 hover:border-cobalt transition cursor-pointer"
                      >
                        <div className="text-4xl mb-2">📁</div>
                        <h4 className="text-white font-bold text-sm truncate">{folder.name}</h4>
                      </div>
                    ))}
                    {onedriveFiles.map((file: any) => (
                      <div
                        key={file.id}
                        onClick={() => handleMediaSelect(file)}
                        className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition cursor-pointer"
                      >
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
          </>
        )}
      </div>
    )}
  </div>
)}
```

### Fix 4: Lazy Load Cloud Storage (Performance Fix)

**File:** `app/dashboard/social/page.tsx`
**Lines:** 152-157

**Change From:**
```tsx
useEffect(() => {
  if (showMediaLibrary) {
    loadMediaLibrary();
    loadConnectedProviders();
  }
}, [showMediaLibrary]);
```

**Change To:**
```tsx
useEffect(() => {
  if (showMediaLibrary) {
    // Load generated content immediately
    loadMediaLibrary();
    // Load connected providers list (doesn't load files yet)
    loadConnectedProviders();
  }
}, [showMediaLibrary]);

// Lazy load cloud storage files only when cloud tab is clicked
useEffect(() => {
  if (showMediaLibrary && mediaLibraryTab === 'cloud' && cloudStorageProvider) {
    if (cloudStorageProvider === 'google_drive') {
      loadDriveFiles('');
    } else if (cloudStorageProvider === 'dropbox') {
      loadDropboxFiles('');
    } else if (cloudStorageProvider === 'onedrive') {
      loadOnedriveFiles('');
    }
  }
}, [mediaLibraryTab, cloudStorageProvider]);
```

## Result
After these fixes:
- ✅ Cloud storage tab will show connected drives
- ✅ Tab navigation stays visible (sticky)
- ✅ Loading indicators show progress
- ✅ Faster modal open (lazy load cloud files)
