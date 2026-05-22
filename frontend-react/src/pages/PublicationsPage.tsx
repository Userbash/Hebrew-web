import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
    <main className="site-page">
      <div className="site-wrap">
        <UiPreferencesControls className="site-prefs" />
        <section className="site-section-head">
          <p className="site-kicker">{t.publicationsKicker}</p>
          <h1>{t.publicationsTitle}</h1>
          <p>{t.publicationsDesc}</p>
        </section>

        {loading && <div className="site-muted">{t.publicationsLoading}</div>}
        {error && <div className="site-error">{error}</div>}

        <section className="site-grid-3">
          {items.map((item) => (
            <article key={item.id} className="site-card">
              <h3>{item.name}</h3>
              <p>{item.description || t.publicationsNoDesc}</p>
              <div className="site-meta">
                <span className="site-chip">{item.metadata?.status || t.publicationsStatusPublished}</span>
                <span>{new Date(item.updated_at).toLocaleDateString(language)}</span>
              </div>
            </article>
          ))}
        </section>

        {!loading && !error && items.length === 0 && (
          <div className="site-muted">{t.publicationsEmpty}</div>
        )}

        <div className="site-cta-row">
          <Link to="/" className="site-btn site-btn-secondary">{t.publicationsBack}</Link>
        </div>
      </div>
    </main>
  );
}
