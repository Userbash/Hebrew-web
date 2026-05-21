import { Search, UserRound } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Header() {
  const { user } = useAuth();

  return (
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
  );
}
