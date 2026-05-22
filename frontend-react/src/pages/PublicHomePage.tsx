import { Link } from 'react-router-dom';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';
import { BookOpen, ShieldCheck, Workflow } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function PublicHomePage() {
  const { language } = useLanguage();

  const text = {
    ru: {
      kicker: 'Платформа Hebrew AI',
      title: 'Единый публичный сайт, личный кабинет и админ-панель',
      desc: 'Единая дизайн-система, централизованное управление контентом, RBAC-модель доступа и безопасный процесс модерации.',
      browse: 'Смотреть публикации',
      signIn: 'Войти',
      card1Title: 'Публичный сайт',
      card1Desc: 'SEO-страницы только с опубликованными и публичными материалами.',
      card2Title: 'Личный кабинет',
      card2Desc: 'Рабочее пространство пользователя с управлением профилем и доступом.',
      card3Title: 'Админ-управление',
      card3Desc: 'Управление пользователями, ролями, правами, модерацией и аудитом.',
    },
    en: {
      kicker: 'Hebrew AI Platform',
      title: 'Unified Public Website, Client Cabinet, and Admin Panel',
      desc: 'Single design system, centralized content governance, RBAC access model, and secure moderation workflow.',
      browse: 'Browse Publications',
      signIn: 'Sign In',
      card1Title: 'Public Website',
      card1Desc: 'SEO-friendly content pages with only published and public materials.',
      card2Title: 'Client Cabinet',
      card2Desc: 'Authorized user workspace with ownership-aware access and profile control.',
      card3Title: 'Admin Governance',
      card3Desc: 'Admin panel controls users, roles, rights, moderation, and audit trails.',
    },
    he: {
      kicker: 'פלטפורמת Hebrew AI',
      title: 'אתר ציבורי, אזור אישי ופאנל ניהול מאוחדים',
      desc: 'מערכת עיצוב אחת, ניהול תוכן מרכזי, מודל גישה RBAC ותהליך מודרציה מאובטח.',
      browse: 'עיון בפרסומים',
      signIn: 'התחברות',
      card1Title: 'אתר ציבורי',
      card1Desc: 'עמודי SEO עם חומרים שפורסמו לציבור בלבד.',
      card2Title: 'אזור אישי',
      card2Desc: 'סביבת עבודה למשתמש עם גישה וניהול פרופיל.',
      card3Title: 'ניהול אדמין',
      card3Desc: 'ניהול משתמשים, תפקידים, הרשאות, מודרציה וביקורת.',
    },
  }[language];

  return (
    <main className="site-page">
      <div className="site-wrap">
        <UiPreferencesControls className="site-prefs" />
        <section className="site-hero">
          <p className="site-kicker">{text.kicker}</p>
          <h1>{text.title}</h1>
          <p>{text.desc}</p>
          <div className="site-cta-row">
            <Link to="/publications" className="site-btn site-btn-primary">{text.browse}</Link>
            <Link to="/login" className="site-btn site-btn-secondary">{text.signIn}</Link>
          </div>
        </section>

        <section className="site-grid-3">
          <article className="site-card">
            <BookOpen size={20} />
            <h3>{text.card1Title}</h3>
            <p>{text.card1Desc}</p>
          </article>
          <article className="site-card">
            <Workflow size={20} />
            <h3>{text.card2Title}</h3>
            <p>{text.card2Desc}</p>
          </article>
          <article className="site-card">
            <ShieldCheck size={20} />
            <h3>{text.card3Title}</h3>
            <p>{text.card3Desc}</p>
          </article>
        </section>
      </div>
    </main>
  );
}
