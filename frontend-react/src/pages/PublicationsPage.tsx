import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';
import { publicationsApi, type Publication } from '../api/publications';
import { useLanguage } from '../context/LanguageContext';

export default function PublicationsPage() {
  const { language } = useLanguage();
  const [items, setItems] = useState<Publication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const text = {
    ru: {
      kicker: 'Публичный каталог',
      title: 'Опубликованный контент',
      desc: 'Публичные материалы, прошедшие модерацию.',
      loading: 'Загрузка...',
      loadError: 'Не удалось загрузить публикации',
      empty: 'Пока нет опубликованного контента.',
      noDesc: 'Без описания',
      back: 'Назад на главную',
      published: 'опубликовано',
    },
    en: {
      kicker: 'Public Catalog',
      title: 'Published Content',
      desc: 'Public materials approved by moderation workflow.',
      loading: 'Loading...',
      loadError: 'Failed to load publications',
      empty: 'No published content yet.',
      noDesc: 'No description',
      back: 'Back to Home',
      published: 'published',
    },
    he: {
      kicker: 'קטלוג ציבורי',
      title: 'תוכן שפורסם',
      desc: 'חומרים ציבוריים שאושרו בתהליך המודרציה.',
      loading: 'טוען...',
      loadError: 'טעינת פרסומים נכשלה',
      empty: 'עדיין אין תוכן שפורסם.',
      noDesc: 'ללא תיאור',
      back: 'חזרה לדף הבית',
      published: 'פורסם',
    },
  }[language];

  useEffect(() => {
    const load = async () => {
      try {
        const data = await publicationsApi.listPublic();
        setItems(data.publications || []);
      } catch {
        setError(text.loadError);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, [text.loadError]);

  return (
    <main className="site-page">
      <div className="site-wrap">
        <UiPreferencesControls className="site-prefs" />
        <section className="site-section-head">
          <p className="site-kicker">{text.kicker}</p>
          <h1>{text.title}</h1>
          <p>{text.desc}</p>
        </section>

        {loading && <div className="site-muted">{text.loading}</div>}
        {error && <div className="site-error">{error}</div>}

        <section className="site-grid-3">
          {items.map((item) => (
            <article key={item.id} className="site-card">
              <h3>{item.name}</h3>
              <p>{item.description || text.noDesc}</p>
              <div className="site-meta">
                <span className="site-chip">{item.metadata?.status || text.published}</span>
                <span>{new Date(item.updated_at).toLocaleDateString()}</span>
              </div>
            </article>
          ))}
        </section>

        {!loading && !error && items.length === 0 && (
          <div className="site-muted">{text.empty}</div>
        )}

        <div className="site-cta-row">
          <Link to="/" className="site-btn site-btn-secondary">{text.back}</Link>
        </div>
      </div>
    </main>
  );
}
