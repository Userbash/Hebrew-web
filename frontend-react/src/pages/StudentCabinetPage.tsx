import { Award, BookOpen, Clock3 } from 'lucide-react';
import { useState } from 'react';
import ActivityPanel from '../components/Dashboard/ActivityPanel';
import HealthPanel from '../components/Dashboard/HealthPanel';
import Hero from '../components/Dashboard/Hero';
import StatCard from '../components/Dashboard/StatCard';
import Header from '../components/Layout/Header';
import Sidebar from '../components/Layout/Sidebar';
import { useLanguage } from '../context/LanguageContext';

export default function StudentCabinetPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const { t } = useLanguage();

  return (
    <div className="app-shell">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="app-main">
        <Header />
        <Hero />
        <section className="app-stats-grid" aria-label="Student learning metrics">
          <StatCard icon={<BookOpen size={20} />} label={t.navLessons} value="18" note="4 lessons planned this week" />
          <StatCard icon={<Award size={20} />} label="XP" value="2,840" note="Level 7 learner" />
          <StatCard icon={<Clock3 size={20} />} label="Practice" value="42h" note="Fluency path in progress" />
        </section>
        <section className="app-content-grid">
          <ActivityPanel />
          <HealthPanel />
        </section>
      </main>
    </div>
  );
}
