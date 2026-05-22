import { Link } from 'react-router-dom';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';
import { BookOpen, ShieldCheck, Workflow } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function PublicHomePage() {
  const { t } = useLanguage();

  return (
    <main className="site-page">
      <div className="site-wrap">
        <UiPreferencesControls className="site-prefs" />
        <section className="site-hero">
          <p className="site-kicker">{t.publicKicker}</p>
          <h1>{t.publicTitle}</h1>
          <p>{t.publicDesc}</p>
          <div className="site-cta-row">
            <Link to="/publications" className="site-btn site-btn-primary">{t.publicBrowse}</Link>
            <Link to="/login" className="site-btn site-btn-secondary">{t.signIn}</Link>
          </div>
        </section>

        <section className="site-grid-3">
          <article className="site-card">
            <BookOpen size={20} />
            <h3>{t.publicCard1Title}</h3>
            <p>{t.publicCard1Desc}</p>
          </article>
          <article className="site-card">
            <Workflow size={20} />
            <h3>{t.publicCard2Title}</h3>
            <p>{t.publicCard2Desc}</p>
          </article>
          <article className="site-card">
            <ShieldCheck size={20} />
            <h3>{t.publicCard3Title}</h3>
            <p>{t.publicCard3Desc}</p>
          </article>
        </section>
      </div>
    </main>
  );
}
