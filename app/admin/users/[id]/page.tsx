'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/context/AuthContext';
import { api } from '@/lib/api-client';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';

interface UserDetails {
  user: {
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
    admin_notes: string | null;
  };
  credit_history: Array<{
    id: string;
    amount: number;
    transaction_type: string;
    description: string;
    created_at: string;
  }>;
  content_stats: Array<{
    content_type: string;
    count: number;
    last_generated: string;
  }>;
  social_connections: Array<{
    service_type: string;
    connected_at: string;
    is_active: boolean;
  }>;
  cloud_storage: Array<{
    provider: string;
    provider_email: string;
    storage_type: string;
    connected_at: string;
    is_active: boolean;
  }>;
}

export default function UserDetailPage() {
  const { user } = useAuth();
  const router = useRouter();
  const params = useParams();
  const userId = params?.id as string;

  const [userDetails, setUserDetails] = useState<UserDetails | null>(null);
  const [loading, setLoading] = useState(true);

  // Grant Credits Modal
  const [showGrantModal, setShowGrantModal] = useState(false);
  const [grantAmount, setGrantAmount] = useState('');
  const [grantReason, setGrantReason] = useState('');
  const [grantLoading, setGrantLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    loadUserDetails();
  }, [user, userId, router]);

  const loadUserDetails = async () => {
    try {
      setLoading(true);
      const response: UserDetails = await api.get(`/admin/users/${userId}`);
      setUserDetails(response);
    } catch (error: any) {
      console.error('Failed to load user details:', error);
      if (error.status === 403) {
        router.push('/dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGrantCredits = async () => {
    if (!grantAmount || !grantReason) {
      alert('Please fill in all fields');
      return;
    }

    try {
      setGrantLoading(true);
      await api.post('/admin/credits/grant', {
        user_id: userId,
        credits: parseInt(grantAmount),
        reason: grantReason,
      });

      alert('Credits granted successfully!');
      setShowGrantModal(false);
      setGrantAmount('');
      setGrantReason('');
      loadUserDetails(); // Refresh
    } catch (error: any) {
      alert(`Failed to grant credits: ${error.message}`);
    } finally {
      setGrantLoading(false);
    }
  };

  const handleSuspendUser = async () => {
    if (!userDetails) return;

    const newStatus = userDetails.user.account_status === 'suspended' ? 'active' : 'suspended';
    const reason = prompt(`Reason for ${newStatus === 'suspended' ? 'suspending' : 'activating'} this user:`);

    if (!reason) return;

    try {
      await api.post('/admin/users/status', {
        user_id: userId,
        status: newStatus,
        reason,
      });

      alert(`User ${newStatus === 'suspended' ? 'suspended' : 'activated'} successfully!`);
      loadUserDetails();
    } catch (error: any) {
      alert(`Failed to update user status: ${error.message}`);
    }
  };

  if (loading || !userDetails) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900">
        <div className="text-white text-base sm:text-lg md:text-xl">Loading user details...</div>
      </div>
    );
  }

  const { user: u, credit_history, content_stats, social_connections, cloud_storage } = userDetails;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-4 sm:p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <Link
          href="/admin"
          className="inline-flex items-center gap-2 text-gray-300 hover:text-white mb-3 sm:mb-4 md:mb-6"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Admin Portal
        </Link>

        {/* Header */}
        <div className="mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense mb-2">
                {u.name}
              </h1>
              <p className="text-gray-300 text-lg">{u.email}</p>
              {u.is_super_admin && (
                <span className="inline-block mt-2 px-3 py-1 bg-gold/20 text-gold-400 text-sm font-semibold rounded-full">
                  SUPER ADMIN
                </span>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowGrantModal(true)}
                className="px-3 sm:px-4 py-2 bg-gradient-to-r from-cobalt to-royal rounded-lg text-white font-semibold hover:opacity-90"
              >
                Gift Credits
              </button>
              {!u.is_super_admin && (
                <button
                  onClick={handleSuspendUser}
                  className={`px-3 sm:px-4 py-2 rounded-lg text-white font-semibold ${
                    u.account_status === 'suspended'
                      ? 'bg-gold hover:bg-gold-600'
                      : 'bg-red-500 hover:bg-red-600'
                  }`}
                >
                  {u.account_status === 'suspended' ? 'Activate Account' : 'Suspend Account'}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Account Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3 md:gap-4 lg:gap-6 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <InfoCard title="Account Status" value={u.account_status} color={
            u.account_status === 'active' ? 'text-gold' :
            u.account_status === 'trial' ? 'text-blue-400' :
            u.account_status === 'suspended' ? 'text-red-400' :
            'text-gray-400'
          } />
          <InfoCard title="Plan" value={u.plan} color="text-cobalt-300" />
          <InfoCard
            title="Credit Balance"
            value={u.credits_exempt ? 'Unlimited' : u.credit_balance.toLocaleString()}
            color={u.credits_exempt ? 'text-gold' : 'text-gold-300'}
          />
          <InfoCard
            title="Email Verified"
            value={u.email_verified ? 'Yes' : 'No'}
            color={u.email_verified ? 'text-gold' : 'text-red-400'}
          />
        </div>

        {/* Organization & Stripe Info */}
        <div className="grid grid-cols-1 lg:grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 md:gap-4 lg:gap-6 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-4 sm:p-6">
            <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Organization</h2>
            <div className="space-y-3">
              <div>
                <div className="text-gray-400 text-sm">Organization Name</div>
                <div className="text-white">{u.organization_name || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Tier</div>
                <div className="text-white capitalize">{u.org_tier || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Role</div>
                <div className="text-white capitalize">{u.org_role || 'N/A'}</div>
              </div>
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-4 sm:p-6">
            <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Stripe Integration</h2>
            <div className="space-y-3">
              <div>
                <div className="text-gray-400 text-sm">Customer ID</div>
                <div className="text-white font-mono text-sm">
                  {u.stripe_customer_id || 'Not connected'}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Subscription ID</div>
                <div className="text-white font-mono text-sm">
                  {u.stripe_subscription_id || 'Not connected'}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Member Since</div>
                <div className="text-white">
                  {new Date(u.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content Generation Stats */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-4 sm:p-6 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Content Generation Stats</h2>
          {content_stats.length === 0 ? (
            <p className="text-gray-400">No content generated yet</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 sm:grid-cols-1 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
              {content_stats.map((stat) => (
                <div key={stat.content_type} className="bg-white/5 rounded-lg p-3 sm:p-4 border border-white/10">
                  <div className="text-gray-400 text-sm capitalize">{stat.content_type}</div>
                  <div className="text-white text-base sm:text-lg md:text-xl lg:text-2xl font-bold">{stat.count}</div>
                  <div className="text-gray-500 text-xs">
                    Last: {new Date(stat.last_generated).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Connections */}
        <div className="grid grid-cols-1 lg:grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 md:gap-4 lg:gap-6 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-4 sm:p-6">
            <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Social Media Connections</h2>
            {social_connections.length === 0 ? (
              <p className="text-gray-400">No social accounts connected</p>
            ) : (
              <div className="space-y-3">
                {social_connections.map((conn, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                    <div>
                      <div className="text-white capitalize">{conn.service_type}</div>
                      <div className="text-gray-400 text-sm">
                        Connected {new Date(conn.connected_at).toLocaleDateString()}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      conn.is_active ? 'bg-gold/20 text-gold' : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {conn.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-4 sm:p-6">
            <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Cloud Storage</h2>
            {cloud_storage.length === 0 ? (
              <p className="text-gray-400">No cloud storage connected</p>
            ) : (
              <div className="space-y-3">
                {cloud_storage.map((storage, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                    <div>
                      <div className="text-white capitalize">{storage.provider.replace('_', ' ')}</div>
                      <div className="text-gray-400 text-sm">{storage.provider_email}</div>
                      <div className="text-gray-500 text-xs">
                        {new Date(storage.connected_at).toLocaleDateString()}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      storage.is_active ? 'bg-gold/20 text-gold' : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {storage.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Credit History */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-4 sm:p-6">
          <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Credit Transaction History</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">Date</th>
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">Type</th>
                  <th className="text-left text-gray-400 text-sm font-semibold pb-3">Description</th>
                  <th className="text-right text-gray-400 text-sm font-semibold pb-3">Amount</th>
                </tr>
              </thead>
              <tbody>
                {credit_history.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-center py-4 sm:py-6 md:py-8 text-gray-400">
                      No credit transactions
                    </td>
                  </tr>
                ) : (
                  credit_history.map((transaction) => (
                    <tr key={transaction.id} className="border-b border-white/5">
                      <td className="py-3 text-gray-300">
                        {new Date(transaction.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3">
                        <span className="px-2 py-1 bg-white/10 rounded text-xs text-gray-300">
                          {transaction.transaction_type}
                        </span>
                      </td>
                      <td className="py-3 text-gray-300">{transaction.description}</td>
                      <td className="py-3 text-right">
                        <span className={`font-semibold ${
                          transaction.amount > 0 ? 'text-gold' : 'text-red-400'
                        }`}>
                          {transaction.amount > 0 ? '+' : ''}{transaction.amount.toLocaleString()}
                        </span>
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
            <div className="bg-slate-800 rounded-2xl border border-white/20 p-4 sm:p-6">
              <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-4">Gift Credits</h3>

              <div className="space-y-2 sm:space-y-3 md:space-y-4">
                <div>
                  <label className="block text-gray-300 text-sm mb-2">Credits Amount</label>
                  <input
                    type="number"
                    value={grantAmount}
                    onChange={(e) => setGrantAmount(e.target.value)}
                    placeholder="e.g., 1000"
                    className="w-full px-3 sm:px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-2">Reason</label>
                  <textarea
                    value={grantReason}
                    onChange={(e) => setGrantReason(e.target.value)}
                    placeholder="e.g., Promotional gift, Compensation for issue, etc."
                    rows={3}
                    className="w-full px-3 sm:px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleGrantCredits}
                    disabled={grantLoading}
                    className="flex-1 px-3 sm:px-4 py-2 bg-gradient-to-r from-cobalt to-royal rounded-lg text-white font-semibold hover:opacity-90 disabled:opacity-50"
                  >
                    {grantLoading ? 'Granting...' : 'Grant Credits'}
                  </button>
                  <button
                    onClick={() => setShowGrantModal(false)}
                    className="flex-1 px-3 sm:px-4 py-2 bg-white/10 rounded-lg text-white font-semibold hover:bg-white/20"
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

function InfoCard({ title, value, color }: { title: string; value: string | number; color: string }) {
  return (
    <div className="bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-4 sm:p-6">
      <div className="text-gray-400 text-sm mb-1">{title}</div>
      <div className={`text-base sm:text-lg md:text-xl lg:text-2xl font-bold capitalize ${color}`}>{value}</div>
    </div>
  );
}
