import { Search, UserRound } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

export default function Header() {
  const { user } = useAuth();
  const { t } = useLanguage();

  return (
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
  );
}
