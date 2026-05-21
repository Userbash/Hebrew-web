import { useState } from 'react';
import { User, Lock, Eye, EyeOff, Globe, Sun, Moon, ShieldCheck, XCircle, LogIn } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function LoginForm() {
  const { theme, toggleTheme } = useTheme();
  const { language, t, setLanguage } = useLanguage();
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
    <div className={cn(
      "min-h-screen w-full flex flex-col relative overflow-hidden font-sans transition-colors duration-1000",
      theme === 'dark' ? "bg-[#0a0a0b] text-white" : "bg-[#fdfdfd] text-zinc-900"
    )}>
      
      {/* Dynamic Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className={cn(
          "absolute -top-[5%] -right-[5%] w-[60vw] h-[60vw] rounded-full blur-[140px] opacity-10 transition-colors",
          theme === 'dark' ? "bg-blue-600" : "bg-blue-200"
        )} />
        <div className={cn(
          "absolute -bottom-[5%] -left-[5%] w-[50vw] h-[50vw] rounded-full blur-[140px] opacity-10 transition-colors",
          theme === 'dark' ? "bg-purple-600" : "bg-purple-200"
        )} />
      </div>

      {/* Header Controls */}
      <nav className="relative z-30 w-full max-w-7xl mx-auto px-6 py-6 md:px-10 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-blue-500 w-8 h-8" />
          <span className="text-2xl font-black tracking-tighter italic">3X-UI</span>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={toggleTheme}
            className={cn(
              "p-3 rounded-2xl border transition-all hover:scale-110 active:scale-95",
              theme === 'dark' ? "bg-zinc-900 border-zinc-800 text-yellow-500" : "bg-white border-zinc-200 text-zinc-500 shadow-sm"
            )}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          <div className={cn(
            "flex items-center border rounded-2xl px-4 py-2 shadow-sm transition-all",
            theme === 'dark' ? "bg-zinc-900 border-zinc-800" : "bg-white border-zinc-200"
          )}>
            <Globe size={14} className="opacity-40 mr-2.5" />
            <select 
              value={language}
              onChange={(e) => setLanguage(e.target.value as any)}
              className="bg-transparent text-[11px] font-black outline-none cursor-pointer uppercase tracking-widest"
            >
              <option value="en">EN</option>
              <option value="ru">RU</option>
              <option value="he">HE</option>
            </select>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="relative z-20 flex-grow flex items-center justify-center p-6 sm:p-12">
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className={cn(
            "w-full max-w-[460px] rounded-[3.5rem] p-10 md:p-14 transition-all duration-500 shadow-2xl",
            theme === 'dark' 
              ? "bg-[#141416]/95 border border-zinc-800/50" 
              : "bg-white border border-zinc-100 shadow-[0_40px_100px_rgba(0,0,0,0.05)]"
          )}
        >
          <div className="flex flex-col gap-10">
            <div className="text-center space-y-4">
              <h2 className="text-4xl font-black tracking-tighter italic">{t.welcome}</h2>
              <div className="h-1.5 w-16 bg-blue-600 mx-auto rounded-full"></div>
            </div>

            <form onSubmit={(e) => e.preventDefault()} className="flex flex-col gap-6">
              {/* Username/Email */}
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-5">{t.username}</label>
                <div className="relative group">
                  <User className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 opacity-30 group-focus-within:text-blue-500 transition-colors" />
                  <input 
                    type="text" 
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="admin@example.com"
                    className={cn(
                      "w-full pl-16 pr-6 py-5 rounded-[2rem] transition-all outline-none font-bold text-sm border-2",
                      theme === 'dark' 
                        ? "bg-black/40 text-white border-zinc-800 focus:border-blue-500/50" 
                        : "bg-zinc-50 text-zinc-900 border-zinc-100 focus:border-blue-500/50"
                    )}
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-5">{t.password}</label>
                <div className="relative group">
                  <Lock className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 opacity-30 group-focus-within:text-blue-500 transition-colors" />
                  <input 
                    type={showPassword ? 'text' : 'password'} 
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className={cn(
                      "w-full pl-16 pr-16 py-5 rounded-[2rem] transition-all outline-none font-bold text-sm border-2",
                      theme === 'dark' 
                        ? "bg-black/40 text-white border-zinc-800 focus:border-blue-500/50" 
                        : "bg-zinc-50 text-zinc-900 border-zinc-100 focus:border-blue-500/50"
                    )}
                  />
                  <button 
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-6 top-1/2 -translate-y-1/2 p-2 rounded-full opacity-40 hover:opacity-100 transition-all hover:scale-110"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* Checkbox & Forgot */}
              <div className="flex items-center justify-between px-4">
                 <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input 
                        type="checkbox" 
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="sr-only" 
                      />
                      <div className={cn(
                        "w-5 h-5 rounded-lg border-2 transition-all",
                        rememberMe ? "bg-blue-600 border-blue-600 shadow-[0_0_15px_rgba(37,99,235,0.4)]" : "border-zinc-300"
                      )}>
                        {rememberMe && <ShieldCheck className="text-white w-full h-full p-0.5" />}
                      </div>
                    </div>
                    <span className="text-[11px] font-black uppercase tracking-widest opacity-50 group-hover:opacity-100 transition-opacity">
                      {t.rememberMe}
                    </span>
                 </label>
                 <a href="#" className="text-[11px] font-black uppercase tracking-widest text-blue-500 hover:underline">
                   {t.forgotPassword}
                 </a>
              </div>

              {/* Actions Grid */}
              <div className="grid grid-cols-2 gap-4 mt-4">
                <button 
                  type="button"
                  onClick={handleReset}
                  className={cn(
                    "flex items-center justify-center gap-2 py-5 rounded-[2rem] font-black text-[11px] uppercase tracking-widest transition-all",
                    theme === 'dark' 
                      ? "bg-zinc-900 text-zinc-400 hover:bg-zinc-800" 
                      : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200"
                  )}
                >
                  <XCircle size={16} />
                  {t.cancel}
                </button>
                <button 
                  type="submit"
                  className={cn(
                    "flex items-center justify-center gap-2 py-5 rounded-[2rem] bg-blue-600 text-white font-black text-[11px] uppercase tracking-widest transition-all shadow-xl shadow-blue-500/30 hover:scale-105 active:scale-95"
                  )}
                >
                  <LogIn size={16} />
                  {t.login}
                </button>
              </div>
            </form>
          </div>
        </motion.div>
      </main>

      {/* Stable Footer */}
      <footer className="relative z-30 w-full p-8 flex flex-col items-center gap-4 border-t border-zinc-800/10">
        <div className={cn(
          "px-6 py-2 rounded-full border text-[9px] font-black tracking-[0.5em] uppercase",
          theme === 'dark' ? "border-zinc-800 text-zinc-600" : "border-zinc-200 text-zinc-400"
        )}>
          Authentication Gateway Protocol • 2025
        </div>
      </footer>
    </div>
  );
}
