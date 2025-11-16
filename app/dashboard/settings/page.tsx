'use client';

import Link from 'next/link';

export default function SettingsPage() {
  const tabs = [
    {
      id: 'cloud-storage',
      name: 'Cloud Storage',
      icon: '',
      description: 'Connect Google Drive, OneDrive, and Dropbox',
      href: '/dashboard/settings/cloud-storage',
      badge: 'Active'
    },
    {
      id: 'social-accounts',
      name: 'Social Accounts',
      icon: '',
      description: 'Connect Instagram, LinkedIn, Twitter, and more',
      href: '/dashboard/settings/social-accounts',
      badge: 'Active'
    },
    {
      id: 'profile',
      name: 'Profile',
      icon: '',
      description: 'Manage your account details',
      href: '/dashboard/settings/profile',
      badge: 'Active'
    },
    {
      id: 'billing',
      name: 'Billing',
      icon: '',
      description: 'Manage subscription and payment methods',
      href: '/dashboard/billing',
      badge: 'Active'
    },
    {
      id: 'team',
      name: 'Team',
      icon: '',
      description: 'Invite team members and manage permissions',
      href: '/dashboard/settings/team',
      badge: 'Active'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-4 sm:p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <h1 className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-400">
            Manage your account, connections, and preferences
          </p>
        </div>

        {/* Settings Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 md:gap-6">
          {tabs.map((tab) => (
            <Link
              key={tab.id}
              href={tab.comingSoon ? '#' : tab.href}
              className={`
                relative bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20
                transition-all duration-300
                ${tab.comingSoon
                  ? 'opacity-60 cursor-not-allowed'
                  : 'hover:border-white/40 hover:bg-white/15 hover:scale-105 cursor-pointer'
                }
              `}
              onClick={(e) => tab.comingSoon && e.preventDefault()}
            >
              {/* Badge */}
              {tab.comingSoon ? (
                <div className="absolute top-4 right-4 bg-cobalt/20 border border-cobalt text-cobalt-300 text-xs px-2 py-1 rounded-full font-semibold">
                  Coming Soon
                </div>
              ) : tab.badge && (
                <div className="absolute top-4 right-4 bg-green-500/20 border border-green-500 text-green-300 text-xs px-2 py-1 rounded-full font-semibold">
                  {tab.badge}
                </div>
              )}

              {/* Icon */}
              <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl mb-4">
                {tab.icon}
              </div>

              {/* Content */}
              <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">
                {tab.name}
              </h3>
              <p className="text-gray-400 text-sm">
                {tab.description}
              </p>

              {/* Arrow Icon (only for active tabs) */}
              {!tab.comingSoon && (
                <div className="mt-4 text-cobalt-300 flex items-center gap-2 text-sm font-semibold">
                  Manage
                  <span className="text-lg">→</span>
                </div>
              )}
            </Link>
          ))}
        </div>

        {/* Help Section */}
        <div className="mt-4 sm:mt-6 md:mt-8 bg-cobalt/10 border border-cobalt/30 rounded-xl p-4 sm:p-6">
          <div className="flex items-start gap-2 sm:gap-3 md:gap-4">
            <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl"></div>
            <div>
              <h4 className="text-lg font-semibold text-cobalt-300 mb-2">
                Need Help?
              </h4>
              <p className="text-gray-300 text-sm mb-3">
                Check our documentation or contact support if you need assistance with any settings.
              </p>
              <div className="flex gap-3">
                <a
                  href="https://docs.orla3.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 sm:px-4 py-2 bg-cobalt/20 hover:bg-cobalt/30 text-cobalt-300 rounded-lg text-sm font-semibold transition"
                >
                  Documentation
                </a>
                <a
                  href="mailto:support@orla3.ai"
                  className="px-3 sm:px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm font-semibold transition"
                >
                  Contact Support
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
