import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { LogOut, User as UserIcon, ShoppingCart, LayoutDashboard } from 'lucide-react';

const MainLayout = () => {
  const { isAuthenticated, logout, user } = useAuthStore();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="bg-surface shadow-soft border-b border-secondary-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-bold text-primary-600 font-hebrew">
                עברית Web
              </Link>
              <nav className="ml-10 flex space-x-4">
                <Link to="/store" className="text-secondary-500 hover:text-primary-500 px-3 py-2 rounded-md font-medium">Store</Link>
                {user?.role === 'ADMIN' && (
                  <Link to="/admin" className="text-secondary-500 hover:text-primary-500 px-3 py-2 rounded-md font-medium flex items-center gap-1">
                    <LayoutDashboard size={16} /> Admin
                  </Link>
                )}
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <Link to="/profile" className="text-secondary-500 hover:text-primary-500 flex items-center gap-2">
                    <UserIcon size={20} />
                    <span className="font-medium">{user?.name || user?.email}</span>
                  </Link>
                  <button onClick={logout} className="text-secondary-500 hover:text-red-500 p-2">
                    <LogOut size={20} />
                  </button>
                </>
              ) : (
                <Link to="/login" className="bg-primary-600 text-white px-4 py-2 rounded-md font-medium hover:bg-primary-700 transition">
                  Login
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <Outlet />
      </main>

      <footer className="bg-surface border-t border-secondary-100 py-6 text-center text-secondary-500">
        <p>&copy; {new Date().getFullYear()} Hebrew Web Learning & Store. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default MainLayout;
