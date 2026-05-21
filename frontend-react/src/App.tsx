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
import api from './api/client';

export default function App() {
  const { user, setUser } = useAuth();
  const { theme } = useTheme();
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

        <nav className="app-nav" aria-label="Главная навигация">
          <NavItem icon={<Home size={18} />} label="Обзор" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <NavItem icon={<BookOpen size={18} />} label="Уроки" active={activeTab === 'lessons'} onClick={() => setActiveTab('lessons')} />
          <NavItem icon={<BarChart3 size={18} />} label="Прогресс" active={activeTab === 'progress'} onClick={() => setActiveTab('progress')} />
          <NavItem icon={<Settings size={18} />} label="Настройки" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
        </nav>

        <button onClick={handleLogout} className="app-logout">
          <LogOut size={18} />
          <span>Выйти</span>
        </button>
      </aside>

      <main className="app-main">
        <header className="app-header">
          <div>
            <p className="app-eyebrow">Сегодня</p>
            <h1>Здравствуйте{user?.first_name ? `, ${user.first_name}` : ''}</h1>
            <p>Продолжайте обучение и следите за состоянием платформы.</p>
          </div>
          <div className="app-header-actions">
            <div className="app-search">
              <Search size={17} />
              <input placeholder="Найти урок, слово или отчёт" />
            </div>
            <div className="app-user-pill">
              <UserRound size={18} />
              <span>{user?.email || 'user@example.com'}</span>
            </div>
          </div>
        </header>

        <section className="app-hero">
          <div>
            <span className="app-status"><CheckCircle2 size={16} /> Система работает</span>
            <h2>Ваш учебный день готов</h2>
            <p>3 коротких упражнения и один словарный повтор помогут сохранить темп без перегрузки.</p>
          </div>
          <button className="app-primary-action">Продолжить урок</button>
        </section>

        <section className="app-stats-grid" aria-label="Ключевые показатели">
          <StatCard label="Активные уроки" value="12" note="2 новых" icon={<BookOpen size={19} />} />
          <StatCard label="Прогресс недели" value="74%" note="+8%" icon={<BarChart3 size={19} />} />
          <StatCard label="Безопасность" value="OK" note="0 событий" icon={<ShieldCheck size={19} />} />
        </section>

        <section className="app-content-grid">
          <div className="app-panel">
            <div className="app-panel-header">
              <h3>Последние действия</h3>
              <button>Все</button>
            </div>
            <div className="activity-list">
              <ActivityItem title="Урок: базовая грамматика" time="2 часа назад" result="+250 XP" />
              <ActivityItem title="Повтор: современная лексика" time="Вчера" result="+120 XP" />
              <ActivityItem title="Тест: технические термины" time="3 дня назад" result="+400 XP" />
            </div>
          </div>

          <div className="app-panel health-panel">
            <div className="app-panel-header">
              <h3>Состояние среды</h3>
              <span>Обновлено сейчас</span>
            </div>
            <div className="health-content">
              <div className="health-ring" aria-label="90 процентов здоровья системы">
                <span>90%</span>
              </div>
              <div>
                <h4>Стабильно</h4>
                <p>API, база данных и учебные сервисы отвечают в пределах нормы.</p>
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
