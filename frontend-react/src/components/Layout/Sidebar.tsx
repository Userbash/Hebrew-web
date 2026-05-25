import { Home, BookOpen, BarChart3, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import api from '../../api/client';
import type { ReactNode } from 'react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export default function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const { setUser } = useAuth();
  const { t } = useLanguage();

  const handleLogout = async () => {
    await api.post('/auth/logout').catch(() => undefined);
    setUser(null);
  };

  return (
    <aside className="app-sidebar">
      <div className="app-brand">
        <div className="app-brand-mark">LS</div>
        <div>
          <strong>Language School</strong>
          <span>Learning console</span>
        </div>
      </div>

      <nav className="app-nav" aria-label={t.dashboardNavAria}>
        <NavItem 
          icon={<Home size={18} />} 
          label={t.navOverview} 
          active={activeTab === 'overview'} 
          onClick={() => onTabChange('overview')} 
        />
        <NavItem 
          icon={<BookOpen size={18} />} 
          label={t.navLessons} 
          active={activeTab === 'lessons'} 
          onClick={() => onTabChange('lessons')} 
        />
        <NavItem 
          icon={<BarChart3 size={18} />} 
          label={t.navProgress} 
          active={activeTab === 'progress'} 
          onClick={() => onTabChange('progress')} 
        />
        <NavItem 
          icon={<Settings size={18} />} 
          label={t.navSettings} 
          active={activeTab === 'settings'} 
          onClick={() => onTabChange('settings')} 
        />
      </nav>

      <button onClick={handleLogout} className="app-logout">
        <LogOut size={18} />
        <span>{t.logout}</span>
      </button>
    </aside>
  );
}

interface NavItemProps {
  icon: ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
}

function NavItem({ icon, label, active = false, onClick }: NavItemProps) {
  return (
    <button 
      onClick={onClick} 
      className={`app-nav-item ${active ? 'active' : ''}`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
