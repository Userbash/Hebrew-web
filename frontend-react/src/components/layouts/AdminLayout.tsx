import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { 
  Users, 
  Settings, 
  ShoppingBag, 
  BookOpen, 
  FileText,
  LogOut,
  ArrowLeft
} from 'lucide-react';

const AdminLayout = () => {
  const { logout, user } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-secondary-100 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-secondary-100">
          <Link to="/admin" className="text-xl font-bold text-primary-600 font-hebrew">
            CRM Admin
          </Link>
        </div>
        <nav className="flex-1 py-4 flex flex-col gap-2 px-4">
          <Link to="/admin/users" className="flex items-center gap-3 px-3 py-2 text-secondary-600 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors">
            <Users size={20} />
            Users
          </Link>
          <Link to="/admin/items" className="flex items-center gap-3 px-3 py-2 text-secondary-600 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors">
            <ShoppingBag size={20} />
            Store Items
          </Link>
          <Link to="/admin/lessons" className="flex items-center gap-3 px-3 py-2 text-secondary-600 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors">
            <BookOpen size={20} />
            Lessons
          </Link>
          <Link to="/admin/publications" className="flex items-center gap-3 px-3 py-2 text-secondary-600 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors">
            <FileText size={20} />
            Publications
          </Link>
          <Link to="/admin/system" className="flex items-center gap-3 px-3 py-2 text-secondary-600 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors">
            <Settings size={20} />
            System Metrics
          </Link>
        </nav>
        <div className="p-4 border-t border-secondary-100 flex flex-col gap-2">
          <Link to="/" className="flex items-center gap-3 px-3 py-2 text-secondary-600 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors">
            <ArrowLeft size={20} />
            Back to Site
          </Link>
          <button onClick={handleLogout} className="flex items-center gap-3 px-3 py-2 text-secondary-600 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors w-full text-left">
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-surface border-b border-secondary-100 flex items-center px-8 justify-between">
          <h1 className="text-xl font-semibold text-secondary-900">Dashboard</h1>
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-secondary-500">Admin: {user?.name || user?.email}</span>
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold">
              {user?.name?.charAt(0) || user?.email?.charAt(0)}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
