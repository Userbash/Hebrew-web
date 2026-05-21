import { useState } from 'react';
import { 
  BookOpen, 
  LayoutDashboard, 
  Settings, 
  Search, 
  Bell, 
  LogOut, 
  Trophy, 
  Flame, 
  BrainCircuit,
  ChevronRight
} from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';

export default function App() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className={`min-h-screen flex transition-all duration-700 ${
      theme === 'dark' ? 'bg-[#050505] text-white' : 'bg-[#f8f9fa] text-zinc-900'
    }`}>
      
      {/* 1. SIDEBAR (Fixed & Adaptive) */}
      <aside className={`w-20 lg:w-72 flex flex-col border-r transition-all duration-500 ${
        theme === 'dark' ? 'bg-[#0a0a0b] border-zinc-800/50' : 'bg-white border-zinc-200'
      }`}>
        {/* Sidebar Header */}
        <div className="p-6 flex items-center space-x-3 mb-10">
          <div className="w-10 h-10 bg-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-600/40">
            <BrainCircuit className="text-white w-6 h-6" />
          </div>
          <span className="hidden lg:block text-2xl font-black tracking-tighter italic">3X-UI</span>
        </div>

        {/* Navigation Items */}
        <nav className="flex-grow px-4 space-y-2">
          <NavItem 
            icon={<LayoutDashboard size={20} />} 
            label="Dashboard" 
            active={activeTab === 'dashboard'} 
            onClick={() => setActiveTab('dashboard')} 
          />
          <NavItem 
            icon={<BookOpen size={20} />} 
            label="Lessons" 
            active={activeTab === 'lessons'} 
            onClick={() => setActiveTab('lessons')} 
          />
          <NavItem 
            icon={<Trophy size={20} />} 
            label="Leaderboard" 
            active={activeTab === 'leaderboard'} 
            onClick={() => setActiveTab('leaderboard')} 
          />
        </nav>

        {/* Sidebar Footer */}
        <div className="p-6 mt-auto border-t border-zinc-800/10 space-y-4">
           <NavItem icon={<Settings size={20} />} label="Settings" />
           <div className="p-4 rounded-3xl bg-red-500/10 text-red-500 flex items-center justify-center lg:justify-start cursor-pointer hover:bg-red-500/20 transition-all">
             <LogOut size={20} />
             <span className="hidden lg:block ml-3 font-bold text-xs uppercase tracking-widest">Terminate Session</span>
           </div>
        </div>
      </aside>

      {/* 2. MAIN CONTENT AREA */}
      <main className="flex-grow flex flex-col overflow-y-auto">
        
        {/* Top Header / Search */}
        <header className="p-6 md:p-8 flex justify-between items-center max-w-[1200px] w-full mx-auto">
          <div className="relative flex-grow max-w-md hidden md:block">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 opacity-30" />
            <input 
              type="text" 
              placeholder="Search assets, tools or documentation..." 
              className={`w-full pl-12 pr-4 py-3 rounded-2xl outline-none text-sm transition-all ${
                theme === 'dark' ? 'bg-zinc-900 focus:bg-black border border-zinc-800' : 'bg-zinc-100 focus:bg-white border border-zinc-200'
              }`}
            />
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-4 py-2 bg-orange-500/10 text-orange-500 rounded-full border border-orange-500/20">
              <Flame size={16} fill="currentColor" />
              <span className="font-black text-xs">12 DAY STREAK</span>
            </div>
            <button className={`p-3 rounded-2xl relative ${theme === 'dark' ? 'bg-zinc-900' : 'bg-white shadow-md'}`}>
              <Bell size={20} className="opacity-50" />
              <div className="absolute top-2.5 right-2.5 w-2 h-2 bg-blue-600 rounded-full border-2 border-zinc-900"></div>
            </button>
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 p-[2px]">
              <div className={`w-full h-full rounded-[14px] flex items-center justify-center font-black ${theme === 'dark' ? 'bg-black' : 'bg-white'}`}>
                {user?.email?.[0].toUpperCase()}
              </div>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <div className="p-6 md:p-8 max-w-[1200px] w-full mx-auto space-y-10">
          
          {/* Hero Welcome */}
          <section className="relative overflow-hidden rounded-[3rem] p-8 md:p-14 bg-gradient-to-br from-blue-600 to-blue-800 text-white shadow-2xl shadow-blue-900/20">
             <div className="relative z-10 space-y-4">
               <h1 className="text-4xl md:text-6xl font-black tracking-tighter">Welcome back,<br/>System Admin</h1>
               <p className="max-w-md text-blue-100 font-medium opacity-80">
                 You are currently managing the Hebrew AI environment. 4 tasks require your immediate attention in the security log.
               </p>
               <button className="mt-8 px-8 py-4 bg-white text-blue-700 font-black rounded-2xl hover:scale-105 transition-transform">
                 View Critical Alerts
               </button>
             </div>
             <div className="absolute -right-20 -top-20 w-80 h-80 bg-white/10 rounded-full blur-[100px]"></div>
          </section>

          {/* Quick Stats Grid */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCard label="Active Users" value="1,284" trend="+12%" />
            <StatCard label="Memory Usage" value="4.2 GB" trend="Optimal" />
            <StatCard label="Security Events" value="0 Alerts" trend="Secure" green />
          </section>

          {/* Activity Section */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className={`p-8 rounded-[2.5rem] ${theme === 'dark' ? 'bg-zinc-900/40 border border-zinc-800' : 'bg-white border border-zinc-100 shadow-xl'}`}>
              <h4 className="text-xl font-black mb-6 flex justify-between items-center">
                Latest Acquisitions
                <span className="text-[10px] text-blue-500 uppercase tracking-widest cursor-pointer hover:underline">See All</span>
              </h4>
              <div className="space-y-4">
                 <ActivityItem title="Advanced Hebrew Grammar" time="2 hours ago" xp={250} />
                 <ActivityItem title="Modern Slang Vocabulary" time="Yesterday" xp={120} />
                 <ActivityItem title="Tech Terms Hebrew" time="3 days ago" xp={400} />
              </div>
            </div>
            
            <div className={`p-8 rounded-[2.5rem] ${theme === 'dark' ? 'bg-zinc-900/40 border border-zinc-800' : 'bg-white border border-zinc-100 shadow-xl'}`}>
              <h4 className="text-xl font-black mb-6">Environment Health</h4>
              <div className="flex flex-col items-center justify-center py-10 space-y-6">
                 <div className="relative w-40 h-40">
                   <svg className="w-full h-full transform -rotate-90">
                     <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-zinc-800" />
                     <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" strokeDasharray={440} strokeDashoffset={440 * 0.1} className="text-blue-500 stroke-linecap-round" />
                   </svg>
                   <div className="absolute inset-0 flex flex-col items-center justify-center">
                     <span className="text-4xl font-black">90%</span>
                     <span className="text-[9px] uppercase tracking-widest opacity-40">Healthy</span>
                   </div>
                 </div>
                 <p className="text-center text-xs opacity-50 font-medium">All bridge connections are functioning within normal parameters.</p>
              </div>
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, active = false, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      className={`flex items-center justify-center lg:justify-start p-4 rounded-2xl cursor-pointer transition-all ${
        active 
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' 
          : 'hover:bg-zinc-800/10 opacity-50 hover:opacity-100'
      }`}
    >
      {icon}
      <span className="hidden lg:block ml-4 font-bold text-xs uppercase tracking-widest">{label}</span>
    </div>
  );
}

function StatCard({ label, value, trend, green = false }: any) {
  return (
    <div className={`p-8 rounded-[2.5rem] border bg-zinc-900/20 border-zinc-800/50 backdrop-blur-md`}>
      <span className="text-[10px] font-black uppercase tracking-widest opacity-40">{label}</span>
      <div className="flex items-end justify-between mt-2">
        <h5 className="text-3xl font-black tracking-tighter">{value}</h5>
        <span className={`text-[10px] font-bold px-2 py-1 rounded-lg ${green ? 'bg-green-500/10 text-green-500' : 'bg-blue-500/10 text-blue-500'}`}>
          {trend}
        </span>
      </div>
    </div>
  );
}

function ActivityItem({ title, time, xp }: any) {
  return (
    <div className="flex items-center justify-between p-4 rounded-3xl bg-zinc-800/10 border border-zinc-800/5 hover:border-zinc-800/20 transition-all group">
      <div className="flex items-center space-x-4">
        <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500">
           <BookOpen size={18} />
        </div>
        <div>
          <h6 className="font-bold text-sm">{title}</h6>
          <p className="text-[10px] opacity-40 font-bold uppercase tracking-widest">{time}</p>
        </div>
      </div>
      <div className="flex items-center space-x-4">
         <span className="text-xs font-black text-blue-500">+{xp} XP</span>
         <ChevronRight size={16} className="opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </div>
  );
}
