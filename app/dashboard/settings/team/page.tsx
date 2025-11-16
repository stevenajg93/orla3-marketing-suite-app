'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/context/AuthContext';
import { api } from '@/lib/api-client';
import Link from 'next/link';

interface TeamMember {
  user_id: string;
  email: string;
  name: string;
  role: string;
  joined_at: string;
  last_login_at: string | null;
  is_active: boolean;
}

interface Organization {
  id: string;
  name: string;
  subscription_tier: string;
  max_users: number;
  current_user_count: number;
}

export default function TeamSettingsPage() {
  const { user } = useAuth();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);

  // Invite member
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'member' | 'admin'>('member');
  const [inviteLoading, setInviteLoading] = useState(false);

  // Change role
  const [changingRole, setChangingRole] = useState<string | null>(null);

  useEffect(() => {
    loadTeamData();
  }, []);

  const loadTeamData = async () => {
    try {
      setLoading(true);

      // Get organization info
      const orgResponse = await api.get('/organization/info');
      setOrganization(orgResponse);

      // Get team members
      const membersResponse = await api.get('/organization/members');
      setMembers(membersResponse);
    } catch (error: any) {
      console.error('Failed to load team data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteLoading(true);

    try {
      await api.post('/organization/invite', {
        email: inviteEmail,
        role: inviteRole,
      });

      alert(`Invitation sent to ${inviteEmail}!`);
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('member');
      loadTeamData();
    } catch (error: any) {
      alert(`Failed to send invitation: ${error.message}`);
    } finally {
      setInviteLoading(false);
    }
  };

  const handleChangeRole = async (userId: string, newRole: string) => {
    const confirm = window.confirm(
      `Are you sure you want to change this member's role to ${newRole}?`
    );

    if (!confirm) return;

    setChangingRole(userId);

    try {
      await api.put('/organization/member/role', {
        user_id: userId,
        role: newRole,
      });

      alert('Role updated successfully!');
      loadTeamData();
    } catch (error: any) {
      alert(`Failed to update role: ${error.message}`);
    } finally {
      setChangingRole(null);
    }
  };

  const handleRemoveMember = async (userId: string, memberEmail: string) => {
    const confirm = window.confirm(
      `Are you sure you want to remove ${memberEmail} from the team? They will lose access to all shared resources.`
    );

    if (!confirm) return;

    try {
      await api.delete(`/organization/member/${userId}`);
      alert('Member removed successfully!');
      loadTeamData();
    } catch (error: any) {
      alert(`Failed to remove member: ${error.message}`);
    }
  };

  const canInvite = organization && organization.current_user_count < organization.max_users;
  const isOwnerOrAdmin = user?.role === 'owner' || user?.role === 'admin';

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-gold-500/20 text-gold-300 border-gold-400/30';
      case 'admin':
        return 'bg-purple-500/20 text-purple-300 border-purple-400/30';
      case 'member':
        return 'bg-cobalt-500/20 text-cobalt-300 border-cobalt-400/30';
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-400/30';
    }
  };

  const getTierName = (tier: string) => {
    return tier.charAt(0).toUpperCase() + tier.slice(1);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-8 flex items-center justify-center">
        <div className="text-white text-xl">Loading team data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link
            href="/dashboard/settings"
            className="text-gray-400 hover:text-white transition"
          >
            ← Back to Settings
          </Link>
        </div>

        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">Team Settings</h1>
            <p className="text-gray-400">
              Manage your team members and permissions
            </p>
          </div>

          {isOwnerOrAdmin && canInvite && (
            <button
              onClick={() => setShowInviteModal(true)}
              className="px-6 py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white font-semibold rounded-lg transition"
            >
              Invite Member
            </button>
          )}
        </div>

        {/* Organization Overview */}
        {organization && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 mb-6">
            <h2 className="text-2xl font-bold text-white mb-4">Organization</h2>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <p className="text-gray-400 text-sm">Name</p>
                <p className="text-white font-semibold text-lg">{organization.name}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Plan</p>
                <p className="text-white font-semibold text-lg">
                  {getTierName(organization.subscription_tier)}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Team Size</p>
                <p className="text-white font-semibold text-lg">
                  {organization.current_user_count} / {organization.max_users} seats
                </p>
                {organization.current_user_count >= organization.max_users && (
                  <p className="text-orange-300 text-xs mt-1">
                    At capacity - upgrade to add more members
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Team Members */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
          <h2 className="text-2xl font-bold text-white mb-6">Team Members</h2>

          {members.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400">No team members yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-4 text-gray-400 font-semibold">Member</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-semibold">Role</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-semibold">Joined</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-semibold">Last Active</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-semibold">Status</th>
                    {isOwnerOrAdmin && (
                      <th className="text-right py-3 px-4 text-gray-400 font-semibold">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {members.map((member) => (
                    <tr key={member.user_id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-4 px-4">
                        <div>
                          <p className="text-white font-semibold">{member.name}</p>
                          <p className="text-gray-400 text-sm">{member.email}</p>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-sm font-semibold border ${getRoleBadgeColor(
                            member.role
                          )}`}
                        >
                          {member.role}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-gray-300">
                        {new Date(member.joined_at).toLocaleDateString()}
                      </td>
                      <td className="py-4 px-4 text-gray-300">
                        {member.last_login_at
                          ? new Date(member.last_login_at).toLocaleDateString()
                          : 'Never'}
                      </td>
                      <td className="py-4 px-4">
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                            member.is_active
                              ? 'bg-green-500/20 text-green-300'
                              : 'bg-gray-500/20 text-gray-300'
                          }`}
                        >
                          {member.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      {isOwnerOrAdmin && (
                        <td className="py-4 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {member.role !== 'owner' && member.user_id !== user?.id && (
                              <>
                                <select
                                  value={member.role}
                                  onChange={(e) => handleChangeRole(member.user_id, e.target.value)}
                                  disabled={changingRole === member.user_id}
                                  className="px-3 py-1 bg-white/5 border border-white/20 rounded text-sm text-white focus:outline-none focus:border-cobalt"
                                >
                                  <option value="viewer" className="bg-slate-800">Viewer</option>
                                  <option value="member" className="bg-slate-800">Member</option>
                                  <option value="admin" className="bg-slate-800">Admin</option>
                                </select>
                                <button
                                  onClick={() => handleRemoveMember(member.user_id, member.email)}
                                  className="px-3 py-1 bg-red-900/40 hover:bg-red-900/60 text-red-200 rounded text-sm transition"
                                >
                                  Remove
                                </button>
                              </>
                            )}
                            {member.user_id === user?.id && (
                              <span className="text-gray-500 text-sm">You</span>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-2xl p-8 max-w-md w-full border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6">Invite Team Member</h2>

            <form onSubmit={handleInviteMember} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                  placeholder="colleague@company.com"
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cobalt"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Role
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as 'member' | 'admin')}
                  className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
                >
                  <option value="viewer" className="bg-slate-800">Viewer - Can view only</option>
                  <option value="member" className="bg-slate-800">Member - Can create & edit</option>
                  <option value="admin" className="bg-slate-800">Admin - Full access except billing</option>
                </select>
              </div>

              <div className="bg-cobalt-500/10 border border-cobalt-400/30 rounded-lg p-4">
                <p className="text-cobalt-300 text-sm">
                  An invitation email will be sent to this address with a link to join your team.
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowInviteModal(false);
                    setInviteEmail('');
                    setInviteRole('member');
                  }}
                  className="flex-1 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviteLoading}
                  className="flex-1 py-2 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white rounded-lg transition disabled:opacity-50"
                >
                  {inviteLoading ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
