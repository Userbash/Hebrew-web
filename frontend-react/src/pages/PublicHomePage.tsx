import { Link } from 'react-router-dom';
import { Badge, Card, Col, Container, Row } from 'react-bootstrap';
import UiPreferencesControls from '../components/Layout/UiPreferencesControls';
import { ArrowRight, BookOpen, GraduationCap, ShieldCheck, Sparkles, Workflow } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function PublicHomePage() {
  const { t } = useLanguage();

  return (
    <main className="site-page school-landing-bg school-public-page">
      <Container className="py-4 py-lg-5">
        <UiPreferencesControls className="site-prefs" />

        <Card className="school-panel school-hero-panel mb-4">
          <Card.Body className="p-4 p-lg-5">
            <Badge bg="warning" text="dark" className="mb-3 px-3 py-2">{t.publicKicker}</Badge>
            <h1 className="display-5 fw-bold mb-3">{t.publicTitle}</h1>
            <p className="lead mb-4 school-hero-text">{t.publicDesc}</p>
            <div className="d-flex flex-wrap gap-2">
              <Link to="/publications" className="btn btn-primary d-inline-flex align-items-center gap-2">
                {t.publicBrowse} <ArrowRight size={16} />
              </Link>
              <Link to="/login" className="btn btn-outline-light">{t.signIn}</Link>
            </div>
          </Card.Body>
        </Card>

        <Row className="g-3">
          <Col lg={4}>
            <Card className="school-panel school-feature-card h-100">
              <Card.Body>
                <BookOpen size={20} className="mb-2" />
                <h3 className="h5">{t.publicCard1Title}</h3>
                <p className="mb-0">{t.publicCard1Desc}</p>
              </Card.Body>
            </Card>
          </Col>
          <Col lg={4}>
            <Card className="school-panel school-feature-card h-100">
              <Card.Body>
                <GraduationCap size={20} className="mb-2" />
                <h3 className="h5">{t.publicCard2Title}</h3>
                <p className="mb-0">{t.publicCard2Desc}</p>
              </Card.Body>
            </Card>
          </Col>
          <Col lg={4}>
            <Card className="school-panel school-feature-card h-100">
              <Card.Body>
                <ShieldCheck size={20} className="mb-2" />
                <h3 className="h5">{t.publicCard3Title}</h3>
                <p className="mb-0">{t.publicCard3Desc}</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <Row className="g-3 mt-1">
          <Col md={6}>
            <Card className="school-panel school-map-card h-100">
              <Card.Body className="d-flex align-items-start gap-3">
                <Sparkles size={18} className="mt-1" />
                <div>
                  <h4 className="h6 mb-1">Понятный старт</h4>
                  <p className="mb-0">Сначала публикации, затем вход, после входа сразу рабочий кабинет без лишних шагов.</p>
                </div>
              </Card.Body>
            </Card>
          </Col>
          <Col md={6}>
            <Card className="school-panel school-map-card h-100">
              <Card.Body className="d-flex align-items-start gap-3">
                <Workflow size={18} className="mt-1" />
                <div>
                  <h4 className="h6 mb-1">Единая стилистика</h4>
                  <p className="mb-0">Одинаковые карточки, кнопки и типографика на главной, в форме входа и кабинете пользователя.</p>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </main>
  );
}
