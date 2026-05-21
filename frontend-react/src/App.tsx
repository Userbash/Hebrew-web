import { useState } from 'react';
import { 
  BookOpen, 
  LayoutDashboard, 
  Search, 
  LogOut, 
  Trophy, 
  Flame, 
  BrainCircuit
} from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';

export default function App() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className={theme === 'dark' ? 'dark' : ''}>
      <div className="min-h-screen flex bg-zinc-50 dark:bg-[#09090b] text-zinc-900 dark:text-zinc-100">
        
        {/* Sidebar */}
        <aside className="w-20 lg:w-64 flex flex-col border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
          <div className="p-6 flex items-center gap-3">
            <BrainCircuit className="text-blue-600 w-8 h-8" />
            <span className="hidden lg:block text-xl font-black italic">3X-UI</span>
          </div>

          <nav className="flex-grow p-4 space-y-2">
            <NavItem icon={<LayoutDashboard size={20} />} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
            <NavItem icon={<BookOpen size={20} />} label="Lessons" active={activeTab === 'lessons'} onClick={() => setActiveTab('lessons')} />
            <NavItem icon={<Trophy size={20} />} label="Stats" active={activeTab === 'leaderboard'} onClick={() => setActiveTab('leaderboard')} />
          </nav>

          <div className="p-4 border-t border-zinc-100 dark:border-zinc-800">
            <button className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/10 text-red-500 transition-all">
              <LogOut size={20} />
              <span className="hidden lg:block font-bold text-xs uppercase tracking-widest">Logout</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex-grow flex flex-col overflow-hidden">
          <header className="h-20 flex items-center justify-between px-8 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
            <div className="flex items-center gap-4 px-4 py-2 bg-zinc-100 dark:bg-black rounded-full border border-zinc-200 dark:border-zinc-800 lg:w-96">
              <Search size={16} className="opacity-30" />
              <input type="text" placeholder="Search system..." className="bg-transparent border-none outline-none text-sm w-full" />
            </div>

            <div className="flex items-center gap-4">
               <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-50 dark:bg-orange-900/10 text-orange-500 rounded-full border border-orange-100 dark:border-orange-900/20 text-xs font-black">
                  <Flame size={14} fill="currentColor" /> 12 DAY STREAK
               </div>
               <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-black text-white">
                  {user?.email?.[0].toUpperCase()}
               </div>
            </div>
          </header>

          <main className="flex-grow overflow-y-auto p-8">
            <div className="max-w-5xl mx-auto space-y-8">
              <section className="p-10 rounded-[2rem] bg-blue-600 text-white shadow-xl relative overflow-hidden">
                 <div className="relative z-10 space-y-4">
                   <h2 className="text-4xl font-black">System Ready.</h2>
                   <p className="opacity-80 max-w-sm font-medium">Welcome back, Admin. Environment isolation is active and monitored.</p>
                 </div>
                 <div className="absolute right-[-10%] bottom-[-20%] w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
              </section>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                 <div className="p-6 rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
                    <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Active Nodes</span>
                    <div className="text-2xl font-black mt-1 text-blue-600">1,284</div>
                 </div>
                 <div className="p-6 rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
                    <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Security Status</span>
                    <div className="text-2xl font-black mt-1 text-green-500">Verified</div>
                 </div>
                 <div className="p-6 rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
                    <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Alerts</span>
                    <div className="text-2xl font-black mt-1">0</div>
                 </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }: any) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all ${
        active 
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' 
          : 'hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-500'
      }`}
    >
      {icon}
      <span className="hidden lg:block font-bold text-sm">{label}</span>
    </button>
  );
}
