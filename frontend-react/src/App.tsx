import { useState } from 'react';
import { 
  BookOpen, 
  LayoutDashboard, 
  Search, 
  LogOut, 
  Trophy, 
  Flame, 
  BrainCircuit,
  Settings,
  Bell
} from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';

export default function App() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className={`min-h-screen w-full flex ${theme === 'dark' ? 'bg-[#0a0a0b]' : 'bg-[#f8f9fa]'} text-white`}>
      
      {/* SIDEBAR */}
      <aside className="w-20 lg:w-72 flex flex-col border-r border-zinc-800 bg-black/20 backdrop-blur-md">
        <div className="p-8 flex items-center gap-4">
          <div className="w-10 h-10 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-600/20">
            <BrainCircuit className="text-white w-6 h-6" />
          </div>
          <span className="hidden lg:block text-2xl font-black italic tracking-tighter">3X-UI</span>
        </div>

        <nav className="flex-grow px-4 space-y-2 mt-8">
          <NavItem 
            icon={<LayoutDashboard size={20} />} 
            label="Overview" 
            active={activeTab === 'dashboard'} 
            onClick={() => setActiveTab('dashboard')} 
          />
          <NavItem 
            icon={<BookOpen size={20} />} 
            label="Environment" 
            active={activeTab === 'lessons'} 
            onClick={() => setActiveTab('lessons')} 
          />
          <NavItem 
            icon={<Trophy size={20} />} 
            label="Infrastructure" 
            active={activeTab === 'leaderboard'} 
            onClick={() => setActiveTab('leaderboard')} 
          />
        </nav>

        <div className="p-6 mt-auto border-t border-zinc-800/50">
           <button className="w-full flex items-center gap-4 p-4 rounded-2xl hover:bg-red-500/10 text-red-500 transition-all group">
             <LogOut size={20} className="group-hover:scale-110 transition-transform" />
             <span className="hidden lg:block font-black text-[10px] uppercase tracking-widest">Terminate Session</span>
           </button>
        </div>
      </aside>

      {/* MAIN VIEW */}
      <div className="flex-grow flex flex-col min-w-0">
        
        {/* HEADER */}
        <header className="h-24 flex items-center justify-between px-8 md:px-12 border-b border-zinc-800">
          <div className="flex items-center gap-4 flex-grow max-w-xl">
             <div className="relative w-full group">
               <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600 group-focus-within:text-blue-500 transition-colors" />
               <input 
                type="text" 
                placeholder="Audit logs, users or system nodes..." 
                className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-zinc-900 border border-zinc-800 outline-none focus:border-blue-500 transition-all text-sm font-medium"
               />
             </div>
          </div>

          <div className="flex items-center gap-6 ml-8">
            <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-orange-500/10 text-orange-500 rounded-full border border-orange-500/20 text-[10px] font-black tracking-widest">
              <Flame size={14} fill="currentColor" /> SYSTEM UP: 12D
            </div>
            <button className="p-3 rounded-2xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition-colors relative">
               <Bell size={20} />
               <div className="absolute top-3 right-3 w-2 h-2 bg-blue-600 rounded-full ring-4 ring-black"></div>
            </button>
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 p-[2px] cursor-pointer hover:rotate-6 transition-transform">
               <div className="w-full h-full rounded-[14px] bg-black flex items-center justify-center font-black text-blue-500">
                 {user?.email?.[0].toUpperCase()}
               </div>
            </div>
          </div>
        </header>

        {/* CONTENT */}
        <main className="flex-grow p-8 md:p-12 overflow-y-auto">
          <div className="max-w-6xl mx-auto space-y-10">
            
            {/* HERO CARD */}
            <section className="p-10 md:p-16 rounded-[3rem] bg-gradient-to-br from-blue-600 to-blue-800 relative overflow-hidden shadow-2xl shadow-blue-900/20">
               <div className="relative z-10 space-y-4">
                 <div className="inline-block px-4 py-1.5 rounded-full bg-white/10 border border-white/20 text-[10px] font-black uppercase tracking-widest text-blue-100">
                    Host Integrity Verified
                 </div>
                 <h2 className="text-5xl md:text-7xl font-black tracking-tighter leading-[0.9]">Secure Layer<br/>is Active.</h2>
                 <p className="max-w-md text-blue-100 font-medium text-lg opacity-80 pt-4">
                    Environment isolation protocol is running at 100% capacity. No bridge violations detected.
                 </p>
               </div>
               <div className="absolute -right-20 -top-20 w-[400px] h-[400px] bg-white/10 rounded-full blur-[100px]"></div>
            </section>

            {/* STATS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard icon={<LayoutDashboard size={18} />} label="Encapsulated Nodes" value="1,284" status="+12.5%" />
              <StatCard icon={<Settings size={18} />} label="Bridge Latency" value="0.4ms" status="Optimal" green />
              <StatCard icon={<ShieldCheck size={18} />} label="Security Events" value="0" status="Secure" green />
            </div>

            {/* LOWER CONTENT SECTION */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
               <div className="p-8 rounded-[2.5rem] bg-zinc-900/50 border border-zinc-800">
                  <h4 className="text-lg font-black uppercase tracking-widest mb-8 flex justify-between items-center">
                    Audit Log
                    <span className="text-[10px] text-blue-500 cursor-pointer hover:underline">Full Report</span>
                  </h4>
                  <div className="space-y-4">
                     <LogItem title="Host command: podman ps" time="2m ago" ok />
                     <LogItem title="Identity check: user login" time="15m ago" ok />
                     <LogItem title="Bridge sync: schema update" time="1h ago" ok />
                  </div>
               </div>

               <div className="p-8 rounded-[2.5rem] bg-zinc-900/50 border border-zinc-800 flex flex-col items-center justify-center text-center space-y-6">
                  <h4 className="text-lg font-black uppercase tracking-widest w-full text-left mb-4">Environment Health</h4>
                  <div className="relative w-48 h-48">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-zinc-800" />
                      <circle cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="12" fill="transparent" strokeDasharray={500} strokeDashoffset={500 * 0.1} className="text-blue-500 stroke-linecap-round shadow-xl" />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-5xl font-black italic">90%</span>
                      <span className="text-[10px] font-black uppercase tracking-widest opacity-40">Healthy</span>
                    </div>
                  </div>
                  <p className="text-xs text-zinc-500 font-medium max-w-xs">
                    All bridge connections are functioning within normal hardware parameters.
                  </p>
               </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}

function NavItem({ icon, label, active = false, onClick }: any) {
  return (
    <div 
      onClick={onClick}
      className={`flex items-center gap-4 p-4 rounded-2xl cursor-pointer transition-all ${
        active 
          ? 'bg-blue-600 text-white shadow-xl shadow-blue-600/30' 
          : 'text-zinc-500 hover:bg-zinc-800/50 hover:text-white'
      }`}
    >
      {icon}
      <span className="hidden lg:block font-black text-[11px] uppercase tracking-widest">{label}</span>
    </div>
  );
}

function StatCard({ icon, label, value, status, green = false }: any) {
  return (
    <div className="p-8 rounded-[2.5rem] bg-zinc-900/50 border border-zinc-800 space-y-4">
      <div className="flex items-center justify-between">
        <div className="p-2.5 rounded-xl bg-zinc-800 text-zinc-400">{icon}</div>
        <span className={`text-[10px] font-black px-2 py-1 rounded-lg ${green ? 'bg-green-500/10 text-green-500' : 'bg-blue-500/10 text-blue-500'}`}>
          {status}
        </span>
      </div>
      <div>
        <h5 className="text-3xl font-black tracking-tighter">{value}</h5>
        <span className="text-[10px] font-black uppercase tracking-widest text-zinc-600">{label}</span>
      </div>
    </div>
  );
}

function LogItem({ title, time, ok }: any) {
  return (
    <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-800/20 border border-transparent hover:border-zinc-800 transition-all group">
      <div className="flex items-center gap-4">
        <div className={`w-2 h-2 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'} shadow-[0_0_10px_rgba(34,197,94,0.3)]`}></div>
        <span className="text-sm font-bold text-zinc-300 group-hover:text-white transition-colors">{title}</span>
      </div>
      <span className="text-[10px] font-black text-zinc-600 uppercase">{time}</span>
    </div>
  );
}

function ShieldCheck(props: any) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
      <path d="m9 12 2 2 4-4"/>
    </svg>
  );
}
