import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';
import { Link } from 'react-router-dom';
import { BrainCircuit, ShieldCheck, Zap } from 'lucide-react';
import type { ReactNode } from 'react';

export default function WelcomePage() {
  const { t } = useLanguage();
  const { theme } = useTheme();
  
  return (
    <div className={`min-h-screen flex flex-col transition-all duration-1000 ${
      theme === 'dark' ? 'bg-[#050505] text-white' : 'bg-[#f8f9fa] text-zinc-900'
    } font-sans selection:bg-blue-500/30 overflow-x-hidden`}>
      
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className={`absolute top-[-10%] right-[-10%] w-[70vw] h-[70vw] rounded-full blur-[150px] opacity-10 animate-pulse ${
          theme === 'dark' ? 'bg-blue-600' : 'bg-blue-400'
        }`}></div>
      </div>

      {/* Hero Section */}
      <main className="relative z-10 flex-grow flex flex-col items-center justify-center p-6 text-center space-y-12">
        <div className="space-y-6 max-w-4xl mx-auto">
          <div className="inline-flex items-center space-x-3 px-6 py-2 rounded-full border border-blue-500/20 bg-blue-500/5 text-blue-500 text-[10px] font-black tracking-[0.4em] uppercase mb-8 animate-bounce">
            Next Generation Learning
          </div>
          <h1 className="text-6xl md:text-9xl font-black tracking-tighter leading-none italic">
            HEBREW<br/>
            <span className="bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">AI 2025</span>
          </h1>
          <p className="text-xl md:text-2xl text-zinc-500 font-medium max-w-2xl mx-auto leading-relaxed">
            Experience complete linguistic immersion powered by local environment isolation and secure neural processing.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 w-full max-w-lg mx-auto">
          <Link 
            to="/login" 
            className="group relative w-full sm:w-64 py-5 bg-blue-600 text-white font-black rounded-3xl overflow-hidden transition-all hover:scale-105 active:scale-95 shadow-2xl shadow-blue-500/20"
          >
            <span className="relative z-10 uppercase tracking-widest text-sm">{t.login}</span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </Link>
          <Link 
            to="/register" 
            className={`w-full sm:w-64 py-5 font-black rounded-3xl border transition-all hover:bg-zinc-800/10 uppercase tracking-widest text-sm ${
              theme === 'dark' ? 'border-zinc-800 text-white' : 'border-zinc-200 text-zinc-900'
            }`}
          >
            Initialize Access
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 pt-20 w-full max-w-6xl mx-auto">
           <Feature icon={<ShieldCheck className="text-blue-500" />} title="Isolated" desc="Run in completely sandboxed environments with BridgeOS." />
           <Feature icon={<BrainCircuit className="text-purple-500" />} title="Neural" desc="Advanced LLM models optimized for Hebrew grammar." />
           <Feature icon={<Zap className="text-orange-500" />} title="Fast" desc="Global edge delivery with sub-50ms interaction latency." />
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 p-12 flex flex-col items-center space-y-6 opacity-30 border-t border-zinc-800/10">
        <div className="flex items-center space-x-6 text-[10px] font-black uppercase tracking-widest">
           <a href="#" className="hover:text-blue-500">Privacy</a>
           <a href="#" className="hover:text-blue-500">Terms</a>
           <a href="#" className="hover:text-blue-500">Bridge Protocol</a>
        </div>
        <p className="text-[8px] font-black tracking-[0.8em] uppercase">SYSTEM VERSION 2.0.4-STABLE</p>
      </footer>
    </div>
  );
}

interface FeatureProps {
  icon: ReactNode;
  title: string;
  desc: string;
}

function Feature({ icon, title, desc }: FeatureProps) {
  return (
    <div className="flex flex-col items-center space-y-4 p-8 rounded-[3rem] hover:bg-zinc-500/5 transition-all cursor-default">
      <div className="p-4 rounded-2xl bg-zinc-500/5 border border-zinc-500/10">
        {icon}
      </div>
      <h4 className="font-black uppercase tracking-widest text-xs">{title}</h4>
      <p className="text-sm opacity-50 font-medium max-w-[200px] leading-relaxed">{desc}</p>
    </div>
  );
}
