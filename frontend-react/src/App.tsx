import { useState, type ReactNode } from 'react';
import {
  BarChart3,
  BookOpen,
  CheckCircle2,
  Clock3,
  Home,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
  UserRound,
} from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';
import { useLanguage } from './context/LanguageContext';
import api from './api/client';

export default function App() {
  const { user, setUser } = useAuth();
  const { theme } = useTheme();
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState('overview');

  const handleLogout = async () => {
    await api.post('/auth/logout').catch(() => undefined);
    setUser(null);
  };

  return (
    <div className={`app-shell ${theme === 'dark' ? 'app-shell-dark' : 'app-shell-light'}`}>
      <aside className="app-sidebar">
        <div className="app-brand">
          <div className="app-brand-mark">א</div>
          <div>
            <strong>Hebrew AI</strong>
            <span>Learning console</span>
          </div>
        </div>

        <nav className="app-nav" aria-label={t.dashboardNavAria}>
          <NavItem icon={<Home size={18} />} label={t.navOverview} active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <NavItem icon={<BookOpen size={18} />} label={t.navLessons} active={activeTab === 'lessons'} onClick={() => setActiveTab('lessons')} />
          <NavItem icon={<BarChart3 size={18} />} label={t.navProgress} active={activeTab === 'progress'} onClick={() => setActiveTab('progress')} />
          <NavItem icon={<Settings size={18} />} label={t.navSettings} active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
        </nav>

        <button onClick={handleLogout} className="app-logout">
          <LogOut size={18} />
          <span>{t.logout}</span>
        </button>
      </aside>

      <main className="app-main">
        <header className="app-header">
          <div>
            <p className="app-eyebrow">{t.today}</p>
            <h1>{t.hello}{user?.first_name ? `, ${user.first_name}` : ''}</h1>
            <p>{t.dashboardSubtitle}</p>
          </div>
          <div className="app-header-actions">
            <div className="app-search">
              <Search size={17} />
              <input placeholder={t.searchPlaceholder} />
            </div>
            <div className="app-user-pill">
              <UserRound size={18} />
              <span>{user?.email || 'user@example.com'}</span>
            </div>
          </div>
        </header>

        <section className="app-hero">
          <div>
            <span className="app-status"><CheckCircle2 size={16} /> {t.systemOnline}</span>
            <h2>{t.dayReadyTitle}</h2>
            <p>{t.dayReadyDesc}</p>
          </div>
          <button className="app-primary-action">{t.continueLesson}</button>
        </section>

        <section className="app-stats-grid" aria-label={t.statsAria}>
          <StatCard label={t.activeLessons} value="12" note={t.newItems} icon={<BookOpen size={19} />} />
          <StatCard label={t.weeklyProgress} value="74%" note="+8%" icon={<BarChart3 size={19} />} />
          <StatCard label={t.security} value="OK" note={t.zeroIncidents} icon={<ShieldCheck size={19} />} />
        </section>

        <section className="app-content-grid">
          <div className="app-panel">
            <div className="app-panel-header">
              <h3>{t.recentActions}</h3>
              <button>{t.all}</button>
            </div>
            <div className="activity-list">
              <ActivityItem title={t.activity1Title} time={t.twoHoursAgo} result="+250 XP" />
              <ActivityItem title={t.activity2Title} time={t.yesterday} result="+120 XP" />
              <ActivityItem title={t.activity3Title} time={t.threeDaysAgo} result="+400 XP" />
            </div>
          </div>

          <div className="app-panel health-panel">
            <div className="app-panel-header">
              <h3>{t.envStatusTitle}</h3>
              <span>{t.updatedNow}</span>
            </div>
            <div className="health-content">
              <div className="health-ring" aria-label="90 percent system health">
                <span>90%</span>
              </div>
              <div>
                <h4>{t.stable}</h4>
                <p>{t.stableDesc}</p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
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
    <button onClick={onClick} className={`app-nav-item ${active ? 'active' : ''}`}>
      {icon}
      <span>{label}</span>
    </button>
  );
}

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: string;
  note: string;
}

function StatCard({ icon, label, value, note }: StatCardProps) {
  return (
    <div className="app-stat-card">
      <div className="app-stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{note}</small>
      </div>
    </div>
  );
}

interface ActivityItemProps {
  title: string;
  time: string;
  result: string;
}

function ActivityItem({ title, time, result }: ActivityItemProps) {
  return (
    <div className="activity-item">
      <div className="activity-icon"><Clock3 size={16} /></div>
      <div>
        <strong>{title}</strong>
        <span>{time}</span>
      </div>
      <em>{result}</em>
    </div>
  );
}
