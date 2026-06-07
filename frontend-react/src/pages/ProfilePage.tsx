import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { User as UserIcon, BookOpen, Star } from 'lucide-react';

const ProfilePage = () => {
  const { user, token } = useAuthStore();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get('/api/users/me', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setProfile(response.data);
      } catch (error) {
        console.error('Failed to fetch profile', error);
      } finally {
        setLoading(false);
      }
    };
    if (token) fetchProfile();
  }, [token]);

  if (loading) {
    return <div className="text-secondary-500 p-8">Loading profile...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="bg-surface rounded-lg border border-secondary-100 shadow-soft p-8 flex items-center gap-8">
        <div className="w-24 h-24 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-4xl font-bold">
          {profile?.name?.charAt(0) || user?.email?.charAt(0)}
        </div>
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">{profile?.name || 'User'}</h1>
          <p className="text-secondary-500 mt-1">{user?.email}</p>
          <div className="mt-4 flex gap-2">
            <span className="bg-secondary-100 text-secondary-700 px-2 py-1 rounded text-xs font-medium uppercase tracking-wider">
              {user?.role || 'USER'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-surface rounded-lg border border-secondary-100 shadow-soft p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-accent-100 text-accent-600 rounded-md">
              <BookOpen size={20} />
            </div>
            <h2 className="text-xl font-bold text-secondary-900">Learning Progress</h2>
          </div>
          <p className="text-secondary-500">Your progress in Hebrew lessons will appear here.</p>
          {/* Progress bar placeholder */}
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-secondary-700">Course Completion</span>
              <span className="text-secondary-500">0%</span>
            </div>
            <div className="w-full bg-secondary-100 rounded-full h-2">
              <div className="bg-accent-500 h-2 rounded-full" style={{ width: '0%' }}></div>
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-lg border border-secondary-100 shadow-soft p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-yellow-100 text-yellow-600 rounded-md">
              <Star size={20} />
            </div>
            <h2 className="text-xl font-bold text-secondary-900">Achievements</h2>
          </div>
          <p className="text-secondary-500">Complete lessons and quizzes to earn badges.</p>
          <div className="mt-4 flex gap-3">
            <div className="w-12 h-12 rounded-full border-2 border-dashed border-secondary-200 flex items-center justify-center text-secondary-300">
              <Star size={24} />
            </div>
            <div className="w-12 h-12 rounded-full border-2 border-dashed border-secondary-200 flex items-center justify-center text-secondary-300">
              <Star size={24} />
            </div>
            <div className="w-12 h-12 rounded-full border-2 border-dashed border-secondary-200 flex items-center justify-center text-secondary-300">
              <Star size={24} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
