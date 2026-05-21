import { useState } from 'react';
import { User, Lock, Eye, EyeOff, Sun, Moon } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';

export default function LoginForm() {
  const { theme, toggleTheme } = useTheme();
  const { language, t, setLanguage } = useLanguage();
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-6 dark-gradient-bg relative overflow-hidden">
      
      {/* Background Glows */}
      <div className="absolute top-[-10%] right-[-10%] w-[60vw] h-[60vw] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Settings Bar */}
      <div className="absolute top-8 right-8 flex items-center gap-4 z-50">
        <button 
          onClick={toggleTheme}
          className="p-3 rounded-2xl bg-zinc-900/50 border border-zinc-800 text-zinc-400 hover:text-white transition-all"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <select 
          value={language}
          onChange={(e) => setLanguage(e.target.value as any)}
          className="px-4 py-2 rounded-2xl bg-zinc-900/50 border border-zinc-800 text-xs font-black text-zinc-400 outline-none cursor-pointer hover:text-white"
        >
          <option value="en">EN</option>
          <option value="ru">RU</option>
          <option value="he">HE</option>
        </select>
      </div>

      {/* Main Login Card */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-[420px] premium-card p-10 md:p-14 z-10"
      >
        <div className="text-center mb-10">
          <h1 className="text-4xl font-black tracking-tighter mb-2 italic">3X-UI</h1>
          <div className="h-1 w-12 bg-blue-600 mx-auto rounded-full mb-6"></div>
          <h2 className="text-5xl font-black tracking-tight">{t.welcome}</h2>
        </div>

        <form onSubmit={(e) => e.preventDefault()} className="flex flex-col gap-6">
          {/* Field: Username */}
          <div className="flex flex-col gap-2">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-4">
              {t.username}
            </label>
            <div className="relative group">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-blue-500 transition-colors" />
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                className="auth-input"
              />
            </div>
          </div>

          {/* Field: Password */}
          <div className="flex flex-col gap-2">
            <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-4">
              {t.password}
            </label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-blue-500 transition-colors" />
              <input 
                type={showPassword ? 'text' : 'password'} 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="auth-input pr-12"
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-zinc-600 hover:text-white transition-colors"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button type="submit" className="btn-blue">
              {t.login}
            </button>
          </div>
        </form>

        <div className="mt-10 text-center">
          <a href="#" className="text-[10px] font-black uppercase tracking-widest text-zinc-600 hover:text-blue-500 transition-colors">
            Security Control Protocol • 2025
          </a>
        </div>
      </motion.div>

      {/* Footer Branding */}
      <div className="absolute bottom-10 opacity-5 text-[8px] font-black tracking-[1em] uppercase pointer-events-none">
        Hebrew AI Environment Isolation
      </div>
    </div>
  );
}
