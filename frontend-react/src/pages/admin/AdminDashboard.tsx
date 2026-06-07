import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../../store/authStore';
import { Users, Server, AlertTriangle } from 'lucide-react';

const AdminDashboard = () => {
  const { token } = useAuthStore();
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('/api/admin/system/health', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setMetrics(response.data);
      } catch (error) {
        console.error('Failed to fetch metrics', error);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, [token]);

  if (loading) {
    return <div className="text-secondary-500">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-secondary-900 mb-6">System Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-surface p-6 rounded-lg shadow-soft border border-secondary-100 flex items-start gap-4">
          <div className="p-3 bg-primary-100 text-primary-600 rounded-md">
            <Server size={24} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-secondary-500">System Status</h3>
            <p className="text-2xl font-bold text-secondary-900 mt-1">
              {metrics?.status || 'Active'}
            </p>
          </div>
        </div>

        <div className="bg-surface p-6 rounded-lg shadow-soft border border-secondary-100 flex items-start gap-4">
          <div className="p-3 bg-green-100 text-green-600 rounded-md">
            <Users size={24} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-secondary-500">Active Users</h3>
            <p className="text-2xl font-bold text-secondary-900 mt-1">
              {metrics?.activeUsers || 0}
            </p>
          </div>
        </div>

        <div className="bg-surface p-6 rounded-lg shadow-soft border border-secondary-100 flex items-start gap-4">
          <div className="p-3 bg-amber-100 text-amber-600 rounded-md">
            <AlertTriangle size={24} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-secondary-500">Warnings</h3>
            <p className="text-2xl font-bold text-secondary-900 mt-1">
              {metrics?.warnings || 0}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-8 bg-surface p-6 rounded-lg shadow-soft border border-secondary-100">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Quick Actions</h3>
        <div className="flex gap-4">
          <button className="bg-primary-50 text-primary-600 px-4 py-2 rounded-md font-medium hover:bg-primary-100 transition-colors">
            Manage Users
          </button>
          <button className="bg-secondary-50 text-secondary-600 px-4 py-2 rounded-md font-medium hover:bg-secondary-100 transition-colors">
            View Audit Logs
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
