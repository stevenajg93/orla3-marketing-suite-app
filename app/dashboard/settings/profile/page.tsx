'use client';

import { motion } from 'framer-motion';
import { AnimatedPage } from '@/components/AnimatedPage';
import { fadeInUp } from '@/lib/motion';
import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/context/AuthContext';
import { api } from '@/lib/api-client';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function ProfileSettingsPage() {
  const { user, refreshUser, logout } = useAuth();
  const router = useRouter();

  // Profile form
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [timezone, setTimezone] = useState('');
  const [profileImageUrl, setProfileImageUrl] = useState('');
  const [loading, setLoading] = useState(false);

  // Password change
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);

  // Delete account
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setEmail(user.email || '');
      setTimezone(user.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone);
      setProfileImageUrl(user.profile_image_url || '');
    }
  }, [user]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.put('/auth/profile', {
        name,
        timezone,
        profile_image_url: profileImageUrl,
      });

      await refreshUser();
      alert('Profile updated successfully!');
    } catch (error: any) {
      alert(`Failed to update profile: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      alert('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      alert('Password must be at least 8 characters');
      return;
    }

    setPasswordLoading(true);

    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });

      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      alert('Password changed successfully!');
    } catch (error: any) {
      alert(`Failed to change password: ${error.message}`);
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== email) {
      alert('Email does not match');
      return;
    }

    const finalConfirm = confirm(
      'Are you absolutely sure? This action CANNOT be undone. All your data will be permanently deleted.'
    );

    if (!finalConfirm) return;

    try {
      await api.delete('/auth/account');
      await logout();
      router.push('/');
    } catch (error: any) {
      alert(`Failed to delete account: ${error.message}`);
    }
  };

  const timezones = [
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'America/Phoenix',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Asia/Dubai',
    'Australia/Sydney',
    'Pacific/Auckland',
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-4 sm:p-6 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-3 sm:mb-4 md:mb-6 lg:mb-8 flex items-center gap-2 sm:gap-3 md:gap-4">
          <Link
            href="/dashboard/settings"
            className="text-gray-400 hover:text-white transition"
          >
            ← Back to Settings
          </Link>
        </div>

        <h1 className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl font-bold text-white mb-2">Profile Settings</h1>
        <p className="text-gray-400 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          Manage your account details and preferences
        </p>

        {/* Profile Information */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 mb-3 sm:mb-4 md:mb-6">
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3 sm:mb-4 md:mb-6">Account Information</h2>

          <form onSubmit={handleUpdateProfile} className="space-y-2 sm:space-y-3 md:space-y-4 lg:space-y-6">
            {/* Profile Image */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Profile Image
              </label>
              <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                <div className="w-20 h-20 bg-gradient-to-br from-cobalt to-gold rounded-full flex items-center justify-center text-white text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold">
                  {name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <div className="flex-1">
                  <input
                    type="url"
                    value={profileImageUrl}
                    onChange={(e) => setProfileImageUrl(e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cobalt"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Enter a URL to your profile image
                  </p>
                </div>
              </div>
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cobalt"
              />
            </div>

            {/* Email (read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                disabled
                className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-500 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">
                Email cannot be changed. Contact support if you need to update it.
              </p>
            </div>

            {/* Timezone */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Timezone
              </label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
              >
                {timezones.map((tz) => (
                  <option key={tz} value={tz} className="bg-slate-800">
                    {tz}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white font-semibold rounded-lg transition disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>

        {/* Change Password */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 mb-3 sm:mb-4 md:mb-6">
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3 sm:mb-4 md:mb-6">Change Password</h2>

          <form onSubmit={handleChangePassword} className="space-y-2 sm:space-y-3 md:space-y-4 lg:space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Current Password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cobalt"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cobalt"
              />
              <p className="text-xs text-gray-500 mt-1">
                Must be at least 8 characters
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Confirm New Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cobalt"
              />
            </div>

            <button
              type="submit"
              disabled={passwordLoading}
              className="w-full py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white font-semibold rounded-lg transition disabled:opacity-50"
            >
              {passwordLoading ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </div>

        {/* Danger Zone */}
        <div className="bg-red-900/20 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-red-500/30">
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-red-300 mb-4">Danger Zone</h2>
          <p className="text-gray-400 mb-4">
            Once you delete your account, there is no going back. All your data will be permanently deleted.
          </p>

          <button
            onClick={() => setShowDeleteModal(true)}
            className="px-6 py-3 bg-red-900/40 hover:bg-red-900/60 text-red-200 font-semibold rounded-lg border border-red-500/30 transition"
          >
            Delete Account
          </button>
        </div>
      </div>

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 z-50">
          <div className="bg-slate-800 rounded-2xl p-4 sm:p-6 md:p-8 max-w-md w-full border border-red-500/30">
            <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-4">Delete Account</h2>

            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 sm:p-4 mb-3 sm:mb-4 md:mb-6">
              <p className="text-red-300 text-sm font-semibold mb-2">WARNING</p>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• All your content will be deleted</li>
                <li>• Your subscription will be cancelled</li>
                <li>• Your credits will be forfeited</li>
                <li>• This action cannot be undone</li>
              </ul>
            </div>

            <div className="mb-3 sm:mb-4 md:mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Type your email to confirm: <span className="text-white font-mono">{email}</span>
              </label>
              <input
                type="text"
                value={deleteConfirmation}
                onChange={(e) => setDeleteConfirmation(e.target.value)}
                placeholder={email}
                className="w-full px-3 sm:px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-red-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setDeleteConfirmation('');
                }}
                className="flex-1 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirmation !== email}
                className="flex-1 py-2 bg-red-900/60 hover:bg-red-900/80 text-red-200 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Delete Forever
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
