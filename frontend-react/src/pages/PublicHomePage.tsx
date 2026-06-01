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

function Section({ title, icon, items }: { title: string; icon: React.ReactNode; items: Tile[] }) {
  return (
    <section className="public-section">
      <div className="public-section-head">
        <h2>{icon}{title}</h2>
        <Link to="/publications" className="public-more">Смотреть все</Link>
      </div>
      <Row className="g-3 g-lg-4">
        {items.map((item) => (
          <Col md={4} key={item.title}>
            <Card className="public-content-card h-100">
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
          </Col>
        ))}
      </Row>
    </section>
  );
}

export default function PublicHomePage() {
  const { theme } = useTheme();

  return (
    <main className={`site-page school-landing-bg school-public-page public-ux-v3 ${theme === "dark" ? "public-dark-2026" : "public-light-2026"}` }>
      <Container className="py-4 py-lg-5">
        <header className="public-topbar mb-3 mb-lg-4">
          <div className="public-brand">NoriGate</div>
          <nav className="public-nav" aria-label="Main navigation">
            <a href="#schools">Школы</a>
            <a href="#programs">Программы</a>
            <a href="#news">Новости</a>
          </nav>
          <UiPreferencesControls className="site-prefs" />
        </header>

        <Row className="g-4 g-lg-4 align-items-start">
          <Col lg={9}>
            <Card className="school-panel school-hero-panel public-hero">
              <Card.Body className="p-4 p-lg-5">
                <Badge bg="warning" text="dark" className="px-3 py-2 mb-3">Платформа Language School</Badge>
                <h1 className="public-title">Учёба в Японии: школы, программы, новости и понятный путь поступления</h1>
                <p className="public-subtitle">Сначала выберите школу и программу, затем авторизуйтесь и получите персональный трек обучения и сопровождения.</p>
                <div className="d-flex flex-wrap gap-2 gap-lg-3">
                  <Link to="/publications" className="btn btn-primary public-cta-primary d-inline-flex align-items-center gap-2">Смотреть программы <ArrowRight size={16} /></Link>
                  <Link to="/login" className="btn btn-outline-light public-cta-secondary">Войти в систему</Link>
                </div>
              </Card.Body>
            </Card>

            <div id="schools"><Section title="Школы" icon={<BookOpen size={18} />} items={schools} /></div>
            <div id="programs"><Section title="Программы" icon={<GraduationCap size={18} />} items={programs} /></div>
            <div id="news"><Section title="Новости" icon={<Newspaper size={18} />} items={news} /></div>
          </Col>

          <Col lg={3}>
            <aside className="public-sidebar d-grid gap-3">
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
                  <h3><CalendarDays size={16} /> Ближайший вебинар</h3>
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
          </Col>
        </Row>

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
