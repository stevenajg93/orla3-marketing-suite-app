'use client';

import Link from 'next/link';
import { useAuth } from '@/lib/context/AuthContext';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { useCredits } from '@/lib/hooks/useCredits';
import CreditPurchaseModal from '@/components/CreditPurchaseModal';
import PageTransition from '@/components/PageTransition';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const pathname = usePathname();
  const { credits, loading: creditsLoading } = useCredits();

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900">
      {/* Top Navigation Bar */}
      <nav className="border-b border-white/10 backdrop-blur-lg bg-white/5 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 text-gray-300 hover:text-white transition"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>

            {/* Logo */}
            <Link href="/dashboard" className="flex items-center">
              <h1 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
                ORLA³
              </h1>
            </Link>

            {/* Right Side - User Account */}
            <div className="flex items-center gap-2 sm:gap-4">
              {/* Super Admin Link */}
              {user?.is_super_admin && (
                <Link
                  href="/admin"
                  className={`hidden md:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-gold/20 to-gold-intense/20 hover:from-gold/30 hover:to-gold-intense/30 rounded-lg border border-gold-400/30 transition group ${
                    pathname?.startsWith('/admin') ? 'ring-2 ring-gold-400/50' : ''
                  }`}
                >
                  <svg className="w-5 h-5 text-gold-300 group-hover:text-gold-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="text-gold-300 font-semibold group-hover:text-gold-200">
                    Admin
                  </span>
                </Link>
              )}

              {/* Find Creators Link */}
              <a
                href="https://orla3.com/browse"
                target="_blank"
                rel="noopener noreferrer"
                className="hidden md:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-royal/20 to-cobalt/20 hover:from-cobalt/30 hover:to-gold/30 rounded-lg border border-cobalt-400/30 transition group"
              >
                <span className="text-2xl"></span>
                <span className="text-cobalt-300 font-semibold group-hover:text-cobalt-200">
                  Find Creators
                </span>
              </a>

              {/* Buy More Credits Button - Hidden for system admin */}
              {user?.email !== 's.gillespie@gecslabs.com' && (
                <button
                  onClick={() => setShowCreditModal(true)}
                  className="hidden sm:flex items-center gap-2 px-3 sm:px-4 py-2 bg-gradient-to-r from-cobalt/20 to-royal/20 hover:from-cobalt/30 hover:to-royal/30 rounded-lg border border-cobalt-400/30 hover:border-cobalt-400/50 transition group"
                >
                  {creditsLoading ? (
                    <span className="text-gray-400 text-xs sm:text-sm">Loading...</span>
                  ) : credits ? (
                    <>
                      <span className={`text-sm sm:text-base font-bold group-hover:text-cobalt-200 ${
                        credits.warning_threshold ? 'text-gold-400' : 'text-cobalt-300'
                      }`}>
                        {credits.balance.toLocaleString()}
                      </span>
                      <span className="hidden md:inline text-gray-400 text-sm group-hover:text-gray-300">credits</span>
                      <span className="hidden lg:inline text-cobalt-300 text-xs font-semibold group-hover:text-cobalt-200">• Buy More</span>
                    </>
                  ) : (
                    <span className="text-gray-400 text-xs sm:text-sm">--</span>
                  )}
                </button>
              )}

              {/* Account Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setIsAccountMenuOpen(!isAccountMenuOpen)}
                  className="flex items-center gap-2 sm:gap-3 px-2 sm:px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg border border-white/20 transition"
                >
                  <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-br from-cobalt to-gold rounded-full flex items-center justify-center text-white text-sm sm:text-base font-bold">
                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div className="hidden lg:block text-left">
                    <div className="text-white text-sm font-semibold">
                      {user?.name || 'User'}
                    </div>
                    <div className="text-gray-400 text-xs capitalize">
                      {user?.role || 'user'}
                    </div>
                  </div>
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform hidden sm:block ${
                      isAccountMenuOpen ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {/* Dropdown Menu */}
                {isAccountMenuOpen && (
                  <>
                    {/* Backdrop */}
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setIsAccountMenuOpen(false)}
                    />

                    {/* Menu */}
                    <div className="absolute right-0 mt-2 w-56 sm:w-64 bg-slate-800/95 backdrop-blur-lg rounded-lg border border-white/20 shadow-2xl z-50 overflow-hidden">
                      {/* User Info */}
                      <div className="px-4 py-3 border-b border-white/10">
                        <div className="text-white font-semibold">
                          {user?.name}
                        </div>
                        <div className="text-gray-400 text-sm">
                          {user?.email}
                        </div>
                        {user?.organization_name && (
                          <div className="text-gray-500 text-xs mt-1">
                            {user.organization_name}
                          </div>
                        )}
                      </div>

                      {/* Menu Items */}
                      <div className="py-2">
                        <Link
                          href="/dashboard/settings"
                          className={`flex items-center gap-3 px-4 py-2 text-gray-300 hover:bg-white/10 hover:text-white transition ${
                            pathname === '/dashboard/settings'
                              ? 'bg-white/10 text-white'
                              : ''
                          }`}
                          onClick={() => setIsAccountMenuOpen(false)}
                        >
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                          </svg>
                          Account Settings
                        </Link>

                        {/* Billing & Credits - Hidden for system admin */}
                        {user?.email !== 's.gillespie@gecslabs.com' && (
                          <Link
                            href="/dashboard/billing"
                            className="flex items-center gap-3 px-4 py-2 text-gray-300 hover:bg-white/10 hover:text-white transition"
                            onClick={() => setIsAccountMenuOpen(false)}
                          >
                            <svg
                              className="w-5 h-5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
                              />
                            </svg>
                            Billing & Credits
                          </Link>
                        )}

                        <Link
                          href="/"
                          className="flex items-center gap-3 px-4 py-2 text-gray-300 hover:bg-white/10 hover:text-white transition"
                          onClick={() => setIsAccountMenuOpen(false)}
                        >
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                            />
                          </svg>
                          Home
                        </Link>
                      </div>

                      {/* Logout */}
                      <div className="border-t border-white/10 py-2">
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-3 px-4 py-2 text-red-400 hover:bg-red-900/20 hover:text-red-300 transition w-full"
                        >
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                            />
                          </svg>
                          Log Out
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Menu Drawer */}
      {isMobileMenuOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 z-40 md:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />

          {/* Drawer */}
          <div className="fixed inset-y-0 left-0 w-72 bg-slate-900/95 backdrop-blur-lg border-r border-white/10 z-50 md:hidden overflow-y-auto">
            <div className="p-4">
              {/* Close Button */}
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-white">Menu</h2>
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 text-gray-400 hover:text-white transition"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* User Info */}
              <div className="mb-6 p-4 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-cobalt to-gold rounded-full flex items-center justify-center text-white font-bold">
                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div>
                    <div className="text-white font-semibold">{user?.name || 'User'}</div>
                    <div className="text-gray-400 text-xs capitalize">{user?.role || 'user'}</div>
                  </div>
                </div>
              </div>

              {/* Credits Display - Hidden for system admin */}
              {user?.email !== 's.gillespie@gecslabs.com' && (
                <button
                  onClick={() => {
                    setShowCreditModal(true);
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full mb-4 p-4 bg-gradient-to-r from-cobalt/20 to-royal/20 hover:from-cobalt/30 hover:to-royal/30 rounded-lg border border-cobalt-400/30 transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300 text-sm">Credits</span>
                    {creditsLoading ? (
                      <span className="text-gray-400 text-sm">Loading...</span>
                    ) : credits ? (
                      <div className="flex items-center gap-2">
                        <span className={`font-bold ${
                          credits.warning_threshold ? 'text-gold-400' : 'text-cobalt-300'
                        }`}>
                          {credits.balance.toLocaleString()}
                        </span>
                        <span className="text-cobalt-300 text-xs">Buy More →</span>
                      </div>
                    ) : (
                      <span className="text-gray-400">--</span>
                    )}
                  </div>
                </button>
              )}

              {/* Navigation Links */}
              <nav className="space-y-1">
                <Link
                  href="/dashboard"
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                    pathname === '/dashboard' ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <span className="text-xl"></span>
                  <span>Dashboard</span>
                </Link>

                <Link
                  href="/dashboard/settings"
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                    pathname?.startsWith('/dashboard/settings') ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>Settings</span>
                </Link>

                {user?.email !== 's.gillespie@gecslabs.com' && (
                  <Link
                    href="/dashboard/billing"
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                      pathname === '/dashboard/billing' ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                    <span>Billing</span>
                  </Link>
                )}

                {user?.is_super_admin && (
                  <Link
                    href="/admin"
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                      pathname?.startsWith('/admin') ? 'bg-gold/20 text-gold-300 border border-gold-400/30' : 'text-gold-300 hover:bg-gold/10 border border-transparent'
                    }`}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span>Admin</span>
                  </Link>
                )}

                <a
                  href="https://orla3.com/browse"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-white/5 hover:text-white rounded-lg transition"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <span className="text-xl"></span>
                  <span>Find Creators</span>
                  <span className="ml-auto text-xs">↗</span>
                </a>

                <Link
                  href="/"
                  className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-white/5 hover:text-white rounded-lg transition"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  <span>Home</span>
                </Link>
              </nav>

              {/* Logout Button */}
              <div className="mt-6 pt-6 border-t border-white/10">
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false);
                    handleLogout();
                  }}
                  className="flex items-center gap-3 w-full px-4 py-3 text-red-400 hover:bg-red-900/20 rounded-lg transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span>Log Out</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6 md:py-8">
        <PageTransition>
          {children}
        </PageTransition>
      </main>

      {/* Credit Purchase Modal */}
      <CreditPurchaseModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        onSuccess={() => {
          setShowCreditModal(false);
          // Credits will auto-refresh via webhook
        }}
      />
    </div>
  );
}
