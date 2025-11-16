'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/context/AuthContext';
import { api } from '@/lib/api-client';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface PlatformStats {
  overview: {
    total_users: number;
    total_organizations: number;
    verified_users: number;
    active_users: number;
    trial_users: number;
    suspended_users: number;
  };
  subscriptions: Array<{
    subscription_tier: string;
    count: number;
    total_seats: number;
    used_seats: number;
  }>;
  credits: {
    total_credits_balance: number;
    avg_credits_per_user: number;
    total_credits_used: number;
    total_credits_purchased: number;
    total_credits_granted: number;
  };
  content_generation: Array<{
    content_type: string;
    count: number;
    avg_content_length: number;
  }>;
  activity_trend: Array<{
    date: string;
    active_users: number;
    actions_count: number;
  }>;
  revenue: {
    paying_customers: number;
    active_subscriptions: number;
  };
  last_updated: string;
}

interface User {
  id: string;
  email: string;
  name: string;
  plan: string;
  credit_balance: number;
  credits_exempt: boolean;
  is_super_admin: boolean;
  account_status: string;
  email_verified: boolean;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  created_at: string;
  last_login_at: string | null;
  organization_name: string | null;
  org_tier: string | null;
  org_role: string | null;
  total_content: number;
  total_credits_used: number;
}

interface UsersResponse {
  users: User[];
  total: number;
  limit: number;
  offset: number;
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [planFilter, setPlanFilter] = useState<string>('');

  // Grant Credits Modal
  const [showGrantModal, setShowGrantModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [grantAmount, setGrantAmount] = useState('');
  const [grantReason, setGrantReason] = useState('');
  const [grantLoading, setGrantLoading] = useState(false);

  // Grant Super Admin Modal
  const [showSuperAdminModal, setShowSuperAdminModal] = useState(false);
  const [superAdminAction, setSuperAdminAction] = useState<'grant' | 'revoke'>('grant');
  const [superAdminReason, setSuperAdminReason] = useState('');
  const [superAdminLoading, setSuperAdminLoading] = useState(false);

  // Check if user is super admin
  useEffect(() => {
    if (!user) {
      router.push('/login?redirect=/admin');
      return;
    }

    // Check if user is super admin directly from user object
    if (!user.is_super_admin) {
      console.error('User is not a super admin:', user);
      router.push('/dashboard');
      return;
    }

    // Load platform stats
    const loadStats = async () => {
      try {
        const response = await api.get('/admin/stats/overview');
        setStats(response);
      } catch (error: any) {
        console.error('Failed to load admin stats:', error);
        if (error.status === 403) {
          // Not authorized
          alert('Access denied: You are not a super admin. Please contact support if this is an error.');
          router.push('/dashboard');
        }
      }
    };

    loadStats();
  }, [user, router]);

  // Load users
  useEffect(() => {
    loadUsers();
  }, [searchQuery, statusFilter, planFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      let endpoint = '/admin/users?limit=50';

      if (searchQuery) endpoint += `&search=${encodeURIComponent(searchQuery)}`;
      if (statusFilter) endpoint += `&status=${statusFilter}`;
      if (planFilter) endpoint += `&plan=${planFilter}`;

      const response: UsersResponse = await api.get(endpoint);
      setUsers(response.users);
      setUsersTotal(response.total);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGrantCredits = async () => {
    if (!selectedUserId || !grantAmount || !grantReason) {
      alert('Please fill in all fields');
      return;
    }

    try {
      setGrantLoading(true);
      await api.post('/admin/credits/grant', {
        user_id: selectedUserId,
        credits: parseInt(grantAmount),
        reason: grantReason,
      });

      alert('Credits granted successfully!');
      setShowGrantModal(false);
      setSelectedUserId('');
      setGrantAmount('');
      setGrantReason('');
      loadUsers(); // Refresh user list
    } catch (error: any) {
      alert(`Failed to grant credits: ${error.message}`);
    } finally {
      setGrantLoading(false);
    }
  };

  const handleSuspendUser = async (userId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'suspended' ? 'active' : 'suspended';
    const reason = prompt(`Reason for ${newStatus === 'suspended' ? 'suspending' : 'activating'} this user:`);

    if (!reason) return;

    try {
      await api.post('/admin/users/status', {
        user_id: userId,
        status: newStatus,
        reason,
      });

      alert(`User ${newStatus === 'suspended' ? 'suspended' : 'activated'} successfully!`);
      loadUsers();
    } catch (error: any) {
      alert(`Failed to update user status: ${error.message}`);
    }
  };

  const handleDeleteUser = async (userId: string, userEmail: string) => {
    const confirmed = window.confirm(
      `⚠️ WARNING: Permanently delete ${userEmail}?\n\n` +
      `This will delete:\n` +
      `- User account\n` +
      `- All content library items\n` +
      `- All credit transactions\n` +
      `- All social connections\n` +
      `- All cloud storage tokens\n\n` +
      `This action CANNOT be undone!`
    );

    if (!confirmed) {
      return;
    }

    try {
      await api.delete(`/admin/users/${userId}`);
      alert(`User ${userEmail} permanently deleted`);
      loadUsers();
    } catch (error: any) {
      alert(`Failed to delete user: ${error.message}`);
    }
  };

  const handleSuperAdmin = async () => {
    if (!superAdminReason) {
      alert('Please provide a reason');
      return;
    }

    try {
      setSuperAdminLoading(true);
      const endpoint = superAdminAction === 'grant'
        ? '/admin/super-admin/grant'
        : '/admin/super-admin/revoke';

      await api.post(endpoint, {
        user_id: selectedUserId,
        reason: superAdminReason,
      });

      alert(`Super admin ${superAdminAction === 'grant' ? 'granted' : 'revoked'} successfully!`);
      setShowSuperAdminModal(false);
      setSelectedUserId('');
      setSuperAdminReason('');
      loadUsers(); // Refresh
    } catch (error: any) {
      alert(`Failed to ${superAdminAction} super admin: ${error.message}`);
    } finally {
      setSuperAdminLoading(false);
    }
  };

  if (!stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white text-xl">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense mb-2">
            Super Admin Portal
          </h1>
          <p className="text-gray-300 text-lg">
            Platform management and analytics
          </p>
        </div>

        {/* Platform Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Users"
            value={stats.overview.total_users}
            subtitle={`${stats.overview.verified_users} verified`}
            color="from-cobalt to-cobalt-600"
          />
          <StatCard
            title="Organizations"
            value={stats.overview.total_organizations}
            subtitle={`${stats.overview.active_users} active users`}
            color="from-royal to-royal-600"
          />
          <StatCard
            title="Credits Used"
            value={stats.credits.total_credits_used?.toLocaleString() || '0'}
            subtitle={`${Math.round(stats.credits.avg_credits_per_user || 0)} avg per user`}
            color="from-gold to-gold-600"
          />
          <StatCard
            title="Paying Customers"
            value={stats.revenue.paying_customers}
            subtitle={`${stats.revenue.active_subscriptions} subscriptions`}
            color="from-green-500 to-emerald-500"
          />
        </div>

        {/* Subscription Breakdown */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-6 mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Subscription Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.subscriptions.map((sub) => (
              <div key={sub.subscription_tier} className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="text-gray-400 text-sm capitalize">{sub.subscription_tier}</div>
                <div className="text-white text-2xl font-bold">{sub.count}</div>
                <div className="text-gray-500 text-xs">
                  {sub.used_seats || 0}/{sub.total_seats || 0} seats
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* User Management */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">User Management</h2>
            <div className="text-gray-400 text-sm">
              {usersTotal} total users
            </div>
          </div>

          {/* Filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <input
              type="text"
              placeholder="Search by email or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="trial">Trial</option>
              <option value="suspended">Suspended</option>
              <option value="banned">Banned</option>
            </select>
            <select
              value={planFilter}
              onChange={(e) => setPlanFilter(e.target.value)}
              className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
            >
              <option value="">All Plans</option>
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="pro">Professional</option>
              <option value="business">Business</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          {/* Users Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">User</th>
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">Plan</th>
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">Credits</th>
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">Status</th>
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">Organization</th>
                  <th className="text-right text-gray-400 text-sm font-semibold pb-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-400">
                      Loading users...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-400">
                      No users found
                    </td>
                  </tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-4">
                        <div className="flex flex-col">
                          <div className="text-white font-semibold">{u.name}</div>
                          <div className="text-gray-400 text-sm">{u.email}</div>
                          {u.is_super_admin && (
                            <span className="inline-block mt-1 px-2 py-0.5 bg-gold/20 text-gold-400 text-xs rounded">
                              SUPER ADMIN
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4">
                        <span className="text-white capitalize">{u.plan}</span>
                      </td>
                      <td className="py-4">
                        <div className="flex flex-col">
                          <span className="text-white font-semibold">
                            {u.credit_balance.toLocaleString()}
                          </span>
                          {u.credits_exempt && (
                            <span className="text-green-400 text-xs">Unlimited</span>
                          )}
                        </div>
                      </td>
                      <td className="py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          u.account_status === 'active' ? 'bg-green-500/20 text-green-400' :
                          u.account_status === 'trial' ? 'bg-blue-500/20 text-blue-400' :
                          u.account_status === 'suspended' ? 'bg-red-500/20 text-red-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {u.account_status}
                        </span>
                      </td>
                      <td className="py-4">
                        <div className="flex flex-col">
                          <span className="text-white text-sm">{u.organization_name || 'N/A'}</span>
                          {u.org_role && (
                            <span className="text-gray-400 text-xs capitalize">{u.org_role}</span>
                          )}
                        </div>
                      </td>
                      <td className="py-4">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/admin/users/${u.id}`}
                            className="px-3 py-1 bg-cobalt/20 hover:bg-cobalt/30 text-cobalt-300 rounded text-sm"
                          >
                            View
                          </Link>
                          <button
                            onClick={() => {
                              setSelectedUserId(u.id);
                              setShowGrantModal(true);
                            }}
                            className="px-3 py-1 bg-gold/20 hover:bg-gold/30 text-gold-300 rounded text-sm"
                          >
                            Gift Credits
                          </button>
                          <button
                            onClick={() => {
                              setSelectedUserId(u.id);
                              setSuperAdminAction(u.is_super_admin ? 'revoke' : 'grant');
                              setShowSuperAdminModal(true);
                            }}
                            className={`px-3 py-1 rounded text-sm ${
                              u.is_super_admin
                                ? 'bg-orange-500/20 hover:bg-orange-500/30 text-orange-300'
                                : 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-300'
                            }`}
                          >
                            {u.is_super_admin ? 'Revoke Admin' : 'Make Admin'}
                          </button>
                          {!u.is_super_admin && (
                            <>
                              <button
                                onClick={() => handleSuspendUser(u.id, u.account_status)}
                                className={`px-3 py-1 rounded text-sm ${
                                  u.account_status === 'suspended'
                                    ? 'bg-green-500/20 hover:bg-green-500/30 text-green-300'
                                    : 'bg-red-500/20 hover:bg-red-500/30 text-red-300'
                                }`}
                              >
                                {u.account_status === 'suspended' ? 'Activate' : 'Suspend'}
                              </button>
                              <button
                                onClick={() => handleDeleteUser(u.id, u.email)}
                                className="px-3 py-1 rounded text-sm bg-red-900/40 hover:bg-red-900/60 text-red-200 border border-red-500/30"
                                title="Permanently delete this user and all their data"
                              >
                                Delete
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Grant Credits Modal */}
      {showGrantModal && (
        <>
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" onClick={() => setShowGrantModal(false)} />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md">
            <div className="bg-slate-800 rounded-2xl border border-white/20 p-6">
              <h3 className="text-2xl font-bold text-white mb-4">Gift Credits</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Credits Amount</label>
                  <input
                    type="number"
                    value={grantAmount}
                    onChange={(e) => setGrantAmount(e.target.value)}
                    placeholder="e.g., 1000"
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-2">Reason</label>
                  <textarea
                    value={grantReason}
                    onChange={(e) => setGrantReason(e.target.value)}
                    placeholder="e.g., Promotional gift, Compensation for issue, etc."
                    rows={3}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleGrantCredits}
                    disabled={grantLoading}
                    className="flex-1 px-4 py-2 bg-gradient-to-r from-cobalt to-royal rounded-lg text-white font-semibold hover:opacity-90 disabled:opacity-50"
                  >
                    {grantLoading ? 'Granting...' : 'Grant Credits'}
                  </button>
                  <button
                    onClick={() => setShowGrantModal(false)}
                    className="flex-1 px-4 py-2 bg-white/10 rounded-lg text-white font-semibold hover:bg-white/20"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Super Admin Modal */}
      {showSuperAdminModal && (
        <>
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" onClick={() => setShowSuperAdminModal(false)} />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md">
            <div className="bg-slate-800 rounded-2xl border border-white/20 p-6">
              <h3 className="text-2xl font-bold text-white mb-4">
                {superAdminAction === 'grant' ? 'Grant Super Admin' : 'Revoke Super Admin'}
              </h3>

              <div className="space-y-4">
                <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                  <p className="text-yellow-300 text-sm">
                    {superAdminAction === 'grant'
                      ? '⚠️ This will grant full platform access and unlimited credits to this user.'
                      : '⚠️ This will remove super admin privileges from this user.'}
                  </p>
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-2">Reason</label>
                  <textarea
                    value={superAdminReason}
                    onChange={(e) => setSuperAdminReason(e.target.value)}
                    placeholder="e.g., Platform co-administrator, Temporary access for support, etc."
                    rows={3}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleSuperAdmin}
                    disabled={superAdminLoading}
                    className={`flex-1 px-4 py-2 rounded-lg text-white font-semibold hover:opacity-90 disabled:opacity-50 ${
                      superAdminAction === 'grant'
                        ? 'bg-gradient-to-r from-purple-500 to-purple-700'
                        : 'bg-gradient-to-r from-orange-500 to-red-600'
                    }`}
                  >
                    {superAdminLoading
                      ? (superAdminAction === 'grant' ? 'Granting...' : 'Revoking...')
                      : (superAdminAction === 'grant' ? 'Grant Super Admin' : 'Revoke Super Admin')}
                  </button>
                  <button
                    onClick={() => setShowSuperAdminModal(false)}
                    className="flex-1 px-4 py-2 bg-white/10 rounded-lg text-white font-semibold hover:bg-white/20"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ title, value, subtitle, color }: { title: string; value: number | string; subtitle: string; color: string }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-lg">
      <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-10`}></div>
      <div className="relative p-6">
        <div className="text-gray-400 text-sm mb-1">{title}</div>
        <div className="text-white text-3xl font-bold mb-1">{value}</div>
        <div className="text-gray-500 text-xs">{subtitle}</div>
      </div>
    </div>
  );
}
