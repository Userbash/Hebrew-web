import { useState } from 'react';
import { User, Lock, Eye, EyeOff, Sun, Moon, RotateCcw, LogIn } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';

export default function LoginForm() {
  const { theme, toggleTheme } = useTheme();
  const { t, language, setLanguage } = useLanguage();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  const handleReset = () => {
    setUsername('');
    setPassword('');
    setRememberMe(false);
  };

  return (
    <div className={theme === 'dark' ? 'dark' : ''}>
      <div className="auth-container">
        
        {/* Settings Bar */}
        <div style={{ position: 'absolute', top: '2rem', right: '2rem', display: 'flex', gap: '1rem' }}>
          <button 
            onClick={toggleTheme} 
            style={{ padding: '0.75rem', borderRadius: '0.75rem', border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer' }}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value as any)}
            style={{ padding: '0.5rem 1rem', borderRadius: '0.75rem', border: '1px solid #e5e7eb', fontWeight: 'bold' }}
          >
            <option value="en">EN</option>
            <option value="ru">RU</option>
            <option value="he">HE</option>
          </select>
        </div>

        <div className="auth-card">
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 900, letterSpacing: '-0.05em', fontStyle: 'italic', color: '#2563eb' }}>
              3X-UI
            </h1>
            <p style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.2em', opacity: 0.5, marginTop: '0.5rem' }}>
              {t.welcome}
            </p>
          </div>

          <form onSubmit={(e) => e.preventDefault()}>
            <div className="input-group">
              <label className="input-label">{t.username}</label>
              <div className="input-wrapper">
                <User style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', opacity: 0.3, width: '1.2rem' }} />
                <input 
                  type="text" 
                  className="input-field" 
                  style={{ paddingLeft: '3rem' }}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Username" 
                />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">{t.password}</label>
              <div className="input-wrapper">
                <Lock style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', opacity: 0.3, width: '1.2rem' }} />
                <input 
                  type={showPassword ? 'text' : 'password'} 
                  className="input-field" 
                  style={{ paddingLeft: '3rem', paddingRight: '3.5rem' }}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password" 
                />
                <button 
                  type="button" 
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', border: 'none', background: 'none', cursor: 'pointer', opacity: 0.3 }}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, color: '#6b7280' }}>
                <input 
                  type="checkbox" 
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                {t.rememberMe}
              </label>
              <a href="#" style={{ fontSize: '0.8rem', fontWeight: 800, color: '#2563eb', textDecoration: 'none', textTransform: 'uppercase' }}>
                {t.forgotPassword}
              </a>
            </div>

            <div className="btn-row">
              <button type="button" onClick={handleReset} className="btn-base btn-cancel">
                <RotateCcw size={14} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
                {t.cancel}
              </button>
              <button type="submit" className="btn-base btn-submit">
                <LogIn size={14} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />
                {t.login}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
