import { useLanguage } from '../context/LanguageContext';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';
import { Link } from 'react-router-dom';
import { BrainCircuit, ShieldCheck, Zap } from 'lucide-react';
import type { ReactNode } from 'react';

export default function WelcomePage() {
  const { t } = useLanguage();

  return (
    <main className="site-page">
      <div className="site-wrap">
        <UiPreferencesControls className="site-prefs" />
        <section className="site-hero">
          <p className="site-kicker">Hebrew AI Platform</p>
          <h1>Единая среда: Public, Cabinet, Admin</h1>
          <p>
            Одна визуальная система, единая логика навигации и предсказуемый UX для всех частей сайта.
          </p>
          <div className="site-cta-row">
            <Link to="/login" className="site-btn site-btn-primary">{t.login}</Link>
            <Link to="/register" className="site-btn site-btn-secondary">{t.initAccess}</Link>
          </div>
        </section>

        <section className="site-grid-3">
          <Feature icon={<ShieldCheck className="text-info" />} title="Security" desc="Безопасная модель доступа и аудит действий." />
          <Feature icon={<BrainCircuit className="text-primary" />} title="Consistency" desc="Единые паттерны интерфейса и формы во всех разделах." />
          <Feature icon={<Zap className="text-warning" />} title="Usability" desc="Понятная карта экранов, быстрые действия и читаемая типографика." />
        </section>
      </div>
    </main>
  );
}

interface FeatureProps {
  icon: ReactNode;
  title: string;
  desc: string;
}

function Feature({ icon, title, desc }: FeatureProps) {
  return (
    <article className="site-card">
      {icon}
      <h3>{title}</h3>
      <p>{desc}</p>
    </article>
  );
}
