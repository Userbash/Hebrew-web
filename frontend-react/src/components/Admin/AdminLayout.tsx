import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Shield, BookMarked, Activity, MessageSquareCode, LogOut } from 'lucide-react';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { id: 'dashboard', title: 'Dashboard', icon: <LayoutDashboard size={20} />, path: '/admin' },
  { id: 'users', title: 'Users', icon: <Users size={20} />, path: '/admin/users' },
  { id: 'groups', title: 'Groups', icon: <Shield size={20} />, path: '/admin/groups' },
  { id: 'content', title: 'Content', icon: <BookMarked size={20} />, path: '/admin/publications' },
  { id: 'audit', title: 'Audit', icon: <Activity size={20} />, path: '/admin/audit' },
  { id: 'ai', title: 'AI Bridge', icon: <MessageSquareCode size={20} />, path: '/admin/ai-bridge' },
];

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-[#f2f4f7]">
      {/* Sidebar */}
      <aside className="w-64 bg-[#2c3e50] text-white flex flex-col">
        <div className="p-6 text-xl font-bold border-b border-gray-700">GRAV ADMIN</div>
        <nav className="flex-grow p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.id}
              to={item.path}
              className={`flex items-center space-x-3 p-3 rounded transition ${
                location.pathname === item.path ? 'bg-gray-700' : 'hover:bg-gray-700'
              }`}
            >
              {item.icon}
              <span>{item.title}</span>
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-700">
          <button className="flex items-center space-x-2 text-gray-300 hover:text-white">
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-grow flex flex-col overflow-y-auto">
        {/* Top Header */}
        <header className="bg-[#2a816d] text-white p-4 flex justify-between items-center">
            <div className="flex items-center space-x-2">
                <span className="text-lg font-semibold">Theme: Hydrogen</span>
            </div>
            <nav className="flex space-x-4">
                <a href="#" className="hover:underline">Outlines</a>
                <a href="#" className="hover:underline">Menu</a>
                <a href="#" className="hover:underline">About</a>
                <a href="#" className="hover:underline">Extras</a>
            </nav>
        </header>
        
        {/* Children Content */}
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
};
