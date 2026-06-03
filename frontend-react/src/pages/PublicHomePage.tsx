import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { Badge, Card, Col, Container, Row } from 'react-bootstrap';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';
import {
  ArrowRight,
  BookOpen,
  CalendarDays,
  GraduationCap,
  Newspaper,
  ShieldCheck,
  Star,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react';

type Tile = { title: string; text: string; image: string; tag?: string };

const schools: Tile[] = [
  { title: 'OHARA', text: 'Языковая школа в Токио', image: 'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?auto=format&fit=crop&w=700&q=80', tag: 'NEW' },
  { title: 'Tokyo Galaxy', text: 'Интенсивные программы', image: 'https://images.unsplash.com/photo-1492571350019-22de08371fd3?auto=format&fit=crop&w=700&q=80', tag: 'HOT' },
  { title: 'UNITAS', text: 'Академический трек', image: 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=700&q=80', tag: 'TOP' },
];

const programs: Tile[] = [
  { title: 'Осенний лагерь в Японии', text: '7 недель, сопровождение и проживание', image: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=700&q=80' },
  { title: 'Подготовка к языковой школе', text: 'Интенсив + интервью', image: 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=700&q=80' },
  { title: 'Летний учебный тур', text: 'Япония 2026', image: 'https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?auto=format&fit=crop&w=700&q=80' },
];

const news: Tile[] = [
  { title: 'Новый набор в группу Telegram', text: 'Открыта регистрация', image: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=700&q=80' },
  { title: 'Стипендия до 5000$', text: 'Для языковых школ', image: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=700&q=80' },
  { title: 'Обучение в Японии 2026', text: 'Новый сезон', image: 'https://images.unsplash.com/photo-1531545514256-b1400bc00f31?auto=format&fit=crop&w=700&q=80' },
];

const journey = [
  { step: '01', title: 'Выбор', text: 'Сначала школа, затем программа и документы.' },
  { step: '02', title: 'Подготовка', text: 'Проверка анкеты, интервью и запуск заявки.' },
  { step: '03', title: 'Поступление', text: 'Статус, контроль и быстрый вход в личный кабинет.' },
];

function Section({ title, icon, items, linkLabel = 'Смотреть все' }: { title: string; icon: React.ReactNode; items: Tile[]; linkLabel?: string }) {
  return (
    <section className="public-section">
      <div className="public-section-head">
        <h2>{icon}{title}</h2>
        <Link to="/publications" className="public-more">{linkLabel}</Link>
      </div>
      <div className="public-card-grid">
        {items.map((item) => (
          <Card className="public-content-card" key={item.title}>
            <div className="public-content-image-wrap">
              <Card.Img src={item.image} alt={item.title} className="public-content-image" />
              {item.tag && <Badge bg="danger" className="public-tag">{item.tag}</Badge>}
            </div>
            <Card.Body>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <Link to="/publications" className="public-read-link">Читать</Link>
            </Card.Body>
          </Card>
        ))}
      </div>
    </section>
  );
}

function Stat({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <Card className="public-stat-card">
      <Card.Body>
        <div className="public-stat-icon">{icon}</div>
        <div className="public-stat-value">{value}</div>
        <div className="public-stat-label">{label}</div>
      </Card.Body>
    </Card>
  );
}

export default function PublicHomePage() {
  const { theme } = useTheme();

  return (
    <main className={`site-page school-landing-bg school-public-page public-ux-v4 ${theme === 'dark' ? 'public-dark-2026' : 'public-light-2026'}`}>
      <Container className="py-4 py-lg-4 public-shell-v4">
        <header className="public-topbar public-topbar-v4 mb-3">
          <div className="public-brand public-brand-v4">NoriGate</div>
          <nav className="public-nav public-nav-v4" aria-label="Main navigation">
            <a href="#schools">Школы</a>
            <a href="#programs">Программы</a>
            <a href="#news">Новости</a>
          </nav>
          <UiPreferencesControls className="site-prefs public-prefs" />
        </header>

        <section className="public-hero-v4 mb-4">
          <div className="public-hero-copy">
            <Badge bg="warning" text="dark" className="public-hero-badge px-3 py-2">Платформа Language School</Badge>
            <h1>Учёба в Японии, школы, программы и новости в одном рабочем интерфейсе</h1>
            <p>Главная построена как продуктовый dashboard: меньше пустоты, больше данных, быстрые действия и единая тема с входом и админкой.</p>
            <div className="public-hero-actions">
              <Link to="/publications" className="btn btn-primary public-cta-primary d-inline-flex align-items-center gap-2">Смотреть программы <ArrowRight size={16} /></Link>
              <Link to="/login" className="btn btn-outline-light public-cta-secondary">Войти в систему</Link>
            </div>
          </div>

          <div className="public-hero-panel">
            <div className="public-hero-panel-head">
              <Sparkles size={16} />
              <span>Dashboard overview</span>
            </div>
            <div className="public-hero-panel-grid">
              <div>
                <strong>Schools</strong>
                <span>3 active</span>
              </div>
              <div>
                <strong>Programs</strong>
                <span>3 featured</span>
              </div>
              <div>
                <strong>News</strong>
                <span>3 updates</span>
              </div>
              <div>
                <strong>Access</strong>
                <span>secure login</span>
              </div>
            </div>
          </div>
        </section>

        <Row className="g-3 g-lg-3 mb-4 public-stat-grid">
          <Col md={3}><Stat icon={<Users size={18} />} value="3" label="Schools in focus" /></Col>
          <Col md={3}><Stat icon={<TrendingUp size={18} />} value="6" label="Programs and news items" /></Col>
          <Col md={3}><Stat icon={<ShieldCheck size={18} />} value="RBAC" label="Unified access theme" /></Col>
          <Col md={3}><Stat icon={<CalendarDays size={18} />} value="2026" label="Current intake cycle" /></Col>
        </Row>

        <section className="public-journey">
          <div className="public-journey-head">
            <div>
              <span className="public-journey-kicker">Learning path</span>
              <h2>Short path to admission, laid out like a product flow</h2>
            </div>
            <Link to="/login" className="public-read-link">Start from portal</Link>
          </div>
          <div className="public-journey-grid">
            {journey.map((item) => (
              <Card className="public-journey-card" key={item.step}>
                <Card.Body>
                  <div className="public-journey-step">{item.step}</div>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </Card.Body>
              </Card>
            ))}
          </div>
        </section>

        <div className="public-layout-v4">
          <div className="public-main-v4">
            <div id="schools"><Section title="Школы" icon={<BookOpen size={18} />} items={schools} /></div>
            <div id="programs"><Section title="Программы" icon={<GraduationCap size={18} />} items={programs} /></div>
            <div id="news"><Section title="Новости" icon={<Newspaper size={18} />} items={news} /></div>
          </div>

          <aside className="public-sidebar public-sidebar-v4">
            <Card className="public-side-card public-side-accent">
              <Card.Body>
                <h3>Быстрый путь</h3>
                <ol>
                  <li>Выберите школу</li>
                  <li>Подберите программу</li>
                  <li>Войдите и отправьте заявку</li>
                </ol>
              </Card.Body>
            </Card>

            <Card className="public-side-card">
              <Card.Body>
                <h3><CalendarDays size={16} /> Вебинар</h3>
                <p>Разбор поступления и визы в Японию 2026.</p>
                <Link to="/publications" className="public-read-link">Участвовать</Link>
              </Card.Body>
            </Card>

            <Card className="public-side-card">
              <Card.Body>
                <h3><ShieldCheck size={16} /> Проверка документов</h3>
                <p>Проверим анкету перед отправкой в школу.</p>
                <Link to="/login" className="public-read-link">Начать</Link>
              </Card.Body>
            </Card>

            <Card className="public-side-card">
              <Card.Body>
                <h3><Star size={16} /> Отзывы</h3>
                <p>Реальные кейсы студентов и результаты поступления.</p>
                <Link to="/publications" className="public-read-link">Читать отзывы</Link>
              </Card.Body>
            </Card>
          </aside>
        </div>

        <footer className="public-footer-2026 mt-4 mt-lg-5">
          <div>
            <strong>NoriGate</strong>
            <p>Единый образовательный портал 2026.</p>
          </div>
          <div className="public-footer-links">
            <Link to="/publications">Публикации</Link>
            <Link to="/login">Вход</Link>
          </div>
        </footer>
      </Container>
    </main>
  );
}
