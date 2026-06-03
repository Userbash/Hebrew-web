import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, BookOpen, CalendarDays, FileText, Search, Sparkles } from 'lucide-react';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';
import { publicationsApi, type Publication } from '../api/publications';
import { useLanguage } from '../context/LanguageContext';

export default function PublicationsPage() {
  const { language, t } = useLanguage();
  const [items, setItems] = useState<Publication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await publicationsApi.listPublic();
        setItems(data.publications || []);
      } catch {
        setError(t.publicationsLoadError);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [t.publicationsLoadError]);

  return (
    <main className="site-page public-catalog-page">
      <div className="site-wrap public-catalog-wrap">
        <header className="public-catalog-topbar">
          <Link to="/" className="public-brand public-brand-v4">NoriGate</Link>
          <UiPreferencesControls className="site-prefs public-prefs" />
        </header>

        <section className="public-catalog-hero">
          <div>
            <p className="site-kicker">{t.publicationsKicker}</p>
            <h1>{t.publicationsTitle}</h1>
            <p>{t.publicationsDesc}</p>
            <div className="public-catalog-actions">
              <Link to="/" className="site-btn site-btn-secondary">
                <ArrowLeft size={16} />
                {t.publicationsBack}
              </Link>
              <Link to="/login" className="site-btn site-btn-primary">
                <Sparkles size={16} />
                Start from portal
              </Link>
            </div>
          </div>
          <aside className="public-catalog-panel" aria-label="Catalog overview">
            <div className="public-catalog-panel-item">
              <BookOpen size={18} />
              <span>Programs</span>
              <strong>{loading ? '...' : items.length}</strong>
            </div>
            <div className="public-catalog-panel-item">
              <FileText size={18} />
              <span>Status</span>
              <strong>{error ? 'Issue' : 'Live'}</strong>
            </div>
            <div className="public-catalog-panel-item">
              <CalendarDays size={18} />
              <span>Season</span>
              <strong>2026</strong>
            </div>
          </aside>
        </section>

        <section className="public-catalog-toolbar">
          <div className="public-catalog-search">
            <Search size={16} />
            <span>Catalog is filtered by published materials</span>
          </div>
          <span className="site-chip">{loading ? t.publicationsLoading : `${items.length} items`}</span>
        </section>

        {loading && (
          <section className="public-catalog-grid" aria-label={t.publicationsLoading}>
            {[0, 1, 2].map((item) => (
              <div className="public-catalog-skeleton" key={item} />
            ))}
          </section>
        )}

        {error && <div className="site-error public-catalog-alert">{error}</div>}

        {!loading && !error && items.length > 0 && (
          <section className="public-catalog-grid">
            {items.map((item) => (
              <article key={item.id} className="public-catalog-card">
                <div className="public-catalog-card-icon">
                  <BookOpen size={18} />
                </div>
                <div>
                  <span className="site-chip">{item.category || item.metadata?.status || t.publicationsStatusPublished}</span>
                  <h3>{item.name}</h3>
                </div>
                <p>{item.description || t.publicationsNoDesc}</p>
                <footer className="site-meta">
                  <span className="site-chip">{item.metadata?.status || t.publicationsStatusPublished}</span>
                  <span>{new Date(item.updated_at).toLocaleDateString(language)}</span>
                </footer>
              </article>
            ))}
          </section>
        )}

        {!loading && !error && items.length === 0 && (
          <section className="public-catalog-empty">
            <FileText size={28} />
            <h2>{t.publicationsEmpty}</h2>
            <p>Published materials will appear here after moderation. Use the portal to track programs and admission steps.</p>
            <Link to="/" className="site-btn site-btn-primary">Back to overview</Link>
          </section>
        )}

        <section className="public-catalog-guide" aria-label="Admission support">
          <article>
            <BookOpen size={20} />
            <h2>Compare schools</h2>
            <p>Review available language school tracks, admission timing, and preparation steps before opening a request.</p>
          </article>
          <article>
            <CalendarDays size={20} />
            <h2>Plan intake</h2>
            <p>Use the 2026 cycle as the working timeline for documents, interview preparation, and program selection.</p>
          </article>
          <article>
            <Sparkles size={20} />
            <h2>Continue in portal</h2>
            <p>Sign in to keep the process structured: profile, documents, moderation updates, and next actions.</p>
          </article>
        </section>
      </div>
    </main>
  );
}
