import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react';
import { Alert, Badge, Button, Card, Col, Container, Form, Nav, ProgressBar, Row, Spinner } from 'react-bootstrap';
import {
  BarChart3,
  BookOpen,
  CheckCircle2,
  Clock3,
  Home,
  ImageUp,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
  Trash2,
  UserRound,
} from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';
import { useLanguage } from './context/LanguageContext';
import api from './api/client';
import UiPreferencesControls from './components/Layout/UiPreferencesControls';

type SettingsSection = 'profile' | 'security' | 'avatar' | 'preferences';
type ProgressRange = 'week' | 'month' | 'halfYear' | 'year';

interface DashboardData {
  totals: {
    totalLessons: number;
    completedLessons: number;
    activeLessons: number;
  };
  ranges: Record<ProgressRange, { completed: number; progressPercent: number }>;
  activeLessonItems: Array<{
    lessonId: string;
    title: string;
    progressPercent: number;
    duration: number | null;
    updatedAt: string;
  }>;
  recentActivities: Array<{
    title: string;
    happenedAt: string;
    xp: number;
    kind: string;
  }>;
  user: {
    id: string;
    level: number;
    xpTotal: number;
    streak: number;
  };
}

export default function App() {
  const { user, setUser } = useAuth();
  const { theme } = useTheme();
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState('overview');
  const [settingsSection, setSettingsSection] = useState<SettingsSection>('profile');
  const [selectedRange, setSelectedRange] = useState<ProgressRange>('week');
  const [avatarVersion, setAvatarVersion] = useState(Date.now());
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  const [profileDraft, setProfileDraft] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState('');

  const [passwordDraft, setPasswordDraft] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const [avatarBusy, setAvatarBusy] = useState(false);
  const [avatarMessage, setAvatarMessage] = useState('');
  const [avatarError, setAvatarError] = useState('');

  const firstName = user?.first_name || user?.username || user?.email?.split('@')[0] || 'Student';
  const avatarUrl = `/api/profile-avatar/me?v=${avatarVersion}`;

  const fallbackTasks = useMemo(
    () => [
      { title: t.activity1Title, duration: '10 min', level: 'A1' },
      { title: t.activity2Title, duration: '7 min', level: 'A2' },
      { title: t.activity3Title, duration: '14 min', level: 'B1' },
    ],
    [t],
  );

  const loadDashboard = async () => {
    setDashboardLoading(true);
    try {
      const { data } = await api.get('/progress/dashboard');
      setDashboard(data?.data || null);
    } catch {
      setDashboard(null);
    } finally {
      setDashboardLoading(false);
    }
  };

  useEffect(() => {
    void loadDashboard();
  }, []);

  const handleLogout = async () => {
    await api.post('/auth/logout').catch(() => undefined);
    setUser(null);
  };

  const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setProfileSaving(true);
    setProfileMessage('');
    try {
      const { data } = await api.put('/users/profile', {
        firstName: profileDraft.firstName.trim(),
        lastName: profileDraft.lastName.trim(),
      });
      if (data?.user) {
        setUser((prev) => (prev ? { ...prev, ...data.user } : prev));
      }
      setProfileMessage('Профиль сохранен.');
    } catch {
      setProfileMessage('Не удалось сохранить профиль.');
    } finally {
      setProfileSaving(false);
    }
  };

  const savePassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPasswordSaving(true);
    setPasswordMessage('');
    setPasswordError('');
    try {
      const { data } = await api.post('/auth/change-password', passwordDraft);
      setPasswordMessage(data?.message || 'Пароль успешно обновлен.');
      setPasswordDraft({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (error: any) {
      setPasswordError(error?.response?.data?.message || 'Не удалось изменить пароль.');
    } finally {
      setPasswordSaving(false);
    }
  };

  const uploadAvatar = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setAvatarBusy(true);
    setAvatarMessage('');
    setAvatarError('');

    try {
      const base64 = await fileToBase64(file);
      await api.post('/profile-avatar/me', { imageBase64: base64, mimeType: file.type });
      setAvatarVersion(Date.now());
      setAvatarMessage('Аватар обновлен.');
    } catch (error: any) {
      setAvatarError(error?.response?.data?.message || 'Не удалось загрузить аватар.');
    } finally {
      setAvatarBusy(false);
      event.target.value = '';
    }
  };

  const removeAvatar = async () => {
    setAvatarBusy(true);
    setAvatarMessage('');
    setAvatarError('');
    try {
      await api.delete('/profile-avatar/me');
      setAvatarVersion(Date.now());
      setAvatarMessage('Аватар удален.');
    } catch {
      setAvatarError('Не удалось удалить аватар.');
    } finally {
      setAvatarBusy(false);
    }
  };

  const markLessonCompleted = async (lessonId: string) => {
    await api.post(`/lessons/${lessonId}/complete`).catch(() => undefined);
    await loadDashboard();
  };

  const selectedRangeData = dashboard?.ranges?.[selectedRange];

  return (
    <main className={`school-page ${theme === 'dark' ? 'school-page-dark' : ''}`}>
      <Container fluid="xl" className="py-4 py-lg-5">
        <Row className="g-4">
          <Col xl={3}>
            <Card className="school-panel h-100">
              <Card.Body className="d-flex flex-column gap-4">
                <div className="d-flex align-items-center gap-3">
                  <div className="school-logo">LS</div>
                  <div>
                    <strong className="d-block">Language School</strong>
                    <small className="text-secondary">Student area</small>
                  </div>
                </div>
                <nav aria-label={t.dashboardNavAria} className="d-grid gap-2">
                  <NavItem icon={<Home size={18} />} label={t.navOverview} active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
                  <NavItem icon={<BookOpen size={18} />} label={t.navLessons} active={activeTab === 'lessons'} onClick={() => setActiveTab('lessons')} />
                  <NavItem icon={<BarChart3 size={18} />} label={t.navProgress} active={activeTab === 'progress'} onClick={() => setActiveTab('progress')} />
                  <NavItem icon={<Settings size={18} />} label={t.navSettings} active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
                </nav>
                <Button variant="outline-danger" className="mt-auto d-flex align-items-center justify-content-center gap-2" onClick={handleLogout}>
                  <LogOut size={17} />
                  {t.logout}
                </Button>
              </Card.Body>
            </Card>
          </Col>

          <Col xl={9}>
            {activeTab !== 'settings' && (
              <>
                <div className="d-flex flex-wrap align-items-start justify-content-between gap-3 mb-4">
                  <div>
                    <p className="school-kicker mb-2">{t.today}</p>
                    <h1 className="school-title mb-2">{t.hello}, {firstName}</h1>
                    <p className="text-secondary mb-0">{t.dashboardSubtitle}</p>
                  </div>
                  <div className="d-flex align-items-center flex-wrap gap-2">
                    <UiPreferencesControls />
                    <Badge bg="success" className="d-inline-flex align-items-center gap-1 px-3 py-2">
                      <CheckCircle2 size={14} />
                      {t.systemOnline}
                    </Badge>
                    <Badge bg="light" text="dark" className="d-inline-flex align-items-center gap-1 px-3 py-2 border">
                      <UserRound size={14} />
                      {user?.email || 'student@example.com'}
                    </Badge>
                  </div>
                </div>

                {dashboardLoading && <Alert variant="info" className="py-2">Загрузка прогресса...</Alert>}

                {activeTab === 'overview' && (
                  <>
                    <Card className="school-panel mb-4">
                      <Card.Body>
                        <div className="d-flex flex-wrap justify-content-between gap-3 align-items-start">
                          <div>
                            <h2 className="h4 mb-2">{t.dayReadyTitle}</h2>
                            <p className="text-secondary mb-0">{t.dayReadyDesc}</p>
                          </div>
                          <Button variant="primary">{t.continueLesson}</Button>
                        </div>
                      </Card.Body>
                    </Card>

                    <Row className="g-3 mb-4" aria-label={t.statsAria}>
                      <Col md={4}><StatCard label={t.activeLessons} value={String(dashboard?.totals.activeLessons ?? 0)} note={`${dashboard?.totals.completedLessons ?? 0}/${dashboard?.totals.totalLessons ?? 0}`} icon={<BookOpen size={19} />} /></Col>
                      <Col md={4}><StatCard label={t.weeklyProgress} value={`${dashboard?.ranges.week.progressPercent ?? 0}%`} note={`${dashboard?.ranges.week.completed ?? 0} завершено`} icon={<BarChart3 size={19} />} /></Col>
                      <Col md={4}><StatCard label={t.security} value="OK" note={t.zeroIncidents} icon={<ShieldCheck size={19} />} /></Col>
                    </Row>

                    <Row className="g-4">
                      <Col lg={7}>
                        <Card className="school-panel h-100">
                          <Card.Body>
                            <div className="d-flex justify-content-between align-items-center mb-3">
                              <h3 className="h5 mb-0">{t.recentActions}</h3>
                              <Button variant="link" className="p-0 text-decoration-none" onClick={() => void loadDashboard()}>{t.updatedNow}</Button>
                            </div>
                            <div className="activity-list">
                              {(dashboard?.recentActivities?.length ? dashboard.recentActivities : fallbackTasks).map((task: any, index: number) => (
                                <ActivityItem
                                  key={task.title + index}
                                  title={task.title}
                                  time={task.happenedAt ? new Date(task.happenedAt).toLocaleString() : (index === 0 ? t.twoHoursAgo : index === 1 ? t.yesterday : t.threeDaysAgo)}
                                  result={task.xp ? `+${task.xp} XP` : `${task.duration} • ${task.level}`}
                                />
                              ))}
                            </div>
                          </Card.Body>
                        </Card>
                      </Col>
                      <Col lg={5}>
                        <Card className="school-panel h-100">
                          <Card.Body>
                            <div className="d-flex justify-content-between align-items-center mb-3">
                              <h3 className="h5 mb-0">{t.envStatusTitle}</h3>
                              <small className="text-secondary">{t.updatedNow}</small>
                            </div>
                            <h4 className="h6 mb-2">{t.stable}</h4>
                            <p className="text-secondary mb-3">{t.stableDesc}</p>
                            <ProgressBar now={dashboard?.ranges.week.progressPercent ?? 0} label={`${dashboard?.ranges.week.progressPercent ?? 0}%`} />
                            <label className="form-label small mt-3 mb-1">{t.searchPlaceholder}</label>
                            <div className="school-search-wrap">
                              <Search size={16} />
                              <input placeholder={t.searchPlaceholder} />
                            </div>
                          </Card.Body>
                        </Card>
                      </Col>
                    </Row>
                  </>
                )}

                {activeTab === 'lessons' && (
                  <Card className="school-panel">
                    <Card.Body>
                      <h3 className="h5 mb-3">Активные уроки</h3>
                      <Row className="g-3">
                        {(dashboard?.activeLessonItems || []).map((lesson) => (
                          <Col md={6} key={lesson.lessonId}>
                            <Card className="school-panel school-panel-inner h-100">
                              <Card.Body>
                                <div className="d-flex justify-content-between align-items-center gap-2 mb-2">
                                  <strong>{lesson.title}</strong>
                                  <small className="text-secondary">{lesson.duration ? `${lesson.duration} мин` : 'урок'}</small>
                                </div>
                                <ProgressBar now={lesson.progressPercent} label={`${lesson.progressPercent}%`} className="mb-2" />
                                <div className="d-flex justify-content-between align-items-center">
                                  <small className="text-secondary">{new Date(lesson.updatedAt).toLocaleString()}</small>
                                  <Button size="sm" onClick={() => void markLessonCompleted(lesson.lessonId)}>Завершить</Button>
                                </div>
                              </Card.Body>
                            </Card>
                          </Col>
                        ))}
                        {(!dashboard?.activeLessonItems || dashboard.activeLessonItems.length === 0) && (
                          <Col>
                            <Alert variant="secondary" className="mb-0">Нет активных уроков. Начните урок из каталога, и он появится здесь.</Alert>
                          </Col>
                        )}
                      </Row>
                    </Card.Body>
                  </Card>
                )}

                {activeTab === 'progress' && (
                  <Card className="school-panel">
                    <Card.Body>
                      <div className="d-flex justify-content-between flex-wrap align-items-center gap-2 mb-3">
                        <h3 className="h5 mb-0">Детальный прогресс</h3>
                        <div className="d-flex gap-2 flex-wrap">
                          <Button size="sm" variant={selectedRange === 'week' ? 'primary' : 'outline-primary'} onClick={() => setSelectedRange('week')}>Неделя</Button>
                          <Button size="sm" variant={selectedRange === 'month' ? 'primary' : 'outline-primary'} onClick={() => setSelectedRange('month')}>Месяц</Button>
                          <Button size="sm" variant={selectedRange === 'halfYear' ? 'primary' : 'outline-primary'} onClick={() => setSelectedRange('halfYear')}>Полгода</Button>
                          <Button size="sm" variant={selectedRange === 'year' ? 'primary' : 'outline-primary'} onClick={() => setSelectedRange('year')}>Год</Button>
                        </div>
                      </div>
                      <Row className="g-3 mb-3">
                        <Col md={4}><StatCard label="Текущий диапазон" value={`${selectedRangeData?.progressPercent ?? 0}%`} note={`${selectedRangeData?.completed ?? 0} завершений`} icon={<BarChart3 size={19} />} /></Col>
                        <Col md={4}><StatCard label="Уроки завершено" value={String(dashboard?.totals.completedLessons ?? 0)} note={`из ${dashboard?.totals.totalLessons ?? 0}`} icon={<BookOpen size={19} />} /></Col>
                        <Col md={4}><StatCard label="XP" value={String(dashboard?.user?.xpTotal ?? user?.xp_total ?? 0)} note={`уровень ${dashboard?.user?.level ?? user?.level ?? 1}`} icon={<ShieldCheck size={19} />} /></Col>
                      </Row>
                      <ProgressBar now={selectedRangeData?.progressPercent ?? 0} label={`${selectedRangeData?.progressPercent ?? 0}%`} className="mb-3" />
                    </Card.Body>
                  </Card>
                )}
              </>
            )}

            {activeTab === 'settings' && (
              <Card className="school-panel">
                <Card.Body>
                  <div className="d-flex align-items-center justify-content-between flex-wrap gap-3 mb-3">
                    <div>
                      <h2 className="h4 mb-1">Настройки пользователя</h2>
                      <p className="text-secondary mb-0">Управление профилем, безопасностью и персонализацией интерфейса.</p>
                    </div>
                    <UiPreferencesControls />
                  </div>

                  <Row className="g-4">
                    <Col lg={4}>
                      <Nav variant="pills" className="flex-column gap-2">
                        <Nav.Link active={settingsSection === 'profile'} onClick={() => setSettingsSection('profile')}>Профиль</Nav.Link>
                        <Nav.Link active={settingsSection === 'security'} onClick={() => setSettingsSection('security')}>Безопасность</Nav.Link>
                        <Nav.Link active={settingsSection === 'avatar'} onClick={() => setSettingsSection('avatar')}>Аватар</Nav.Link>
                        <Nav.Link active={settingsSection === 'preferences'} onClick={() => setSettingsSection('preferences')}>Персонализация</Nav.Link>
                      </Nav>
                    </Col>

                    <Col lg={8}>
                      {settingsSection === 'profile' && (
                        <Card className="school-panel school-panel-inner">
                          <Card.Body>
                            <h3 className="h5 mb-3">Данные профиля</h3>
                            <Form onSubmit={saveProfile} className="d-grid gap-3">
                              <Row className="g-3">
                                <Col md={6}><Form.Group><Form.Label>Имя</Form.Label><Form.Control value={profileDraft.firstName} onChange={(e) => setProfileDraft((p) => ({ ...p, firstName: e.target.value }))} /></Form.Group></Col>
                                <Col md={6}><Form.Group><Form.Label>Фамилия</Form.Label><Form.Control value={profileDraft.lastName} onChange={(e) => setProfileDraft((p) => ({ ...p, lastName: e.target.value }))} /></Form.Group></Col>
                              </Row>
                              <Row className="g-3">
                                <Col md={6}><Form.Group><Form.Label>Email</Form.Label><Form.Control value={user?.email || ''} disabled /></Form.Group></Col>
                                <Col md={6}><Form.Group><Form.Label>Username</Form.Label><Form.Control value={user?.username || ''} disabled /></Form.Group></Col>
                              </Row>
                              {profileMessage && <Alert variant={profileMessage.includes('Не удалось') ? 'danger' : 'success'} className="mb-0 py-2">{profileMessage}</Alert>}
                              <Button type="submit" disabled={profileSaving} className="d-inline-flex align-items-center gap-2">{profileSaving && <Spinner size="sm" />} Сохранить профиль</Button>
                            </Form>
                          </Card.Body>
                        </Card>
                      )}

                      {settingsSection === 'security' && (
                        <Card className="school-panel school-panel-inner">
                          <Card.Body>
                            <h3 className="h5 mb-3">Смена пароля</h3>
                            <Form onSubmit={savePassword} className="d-grid gap-3">
                              <Form.Group><Form.Label>Текущий пароль</Form.Label><Form.Control type="password" value={passwordDraft.currentPassword} onChange={(e) => setPasswordDraft((p) => ({ ...p, currentPassword: e.target.value }))} required /></Form.Group>
                              <Form.Group><Form.Label>Новый пароль</Form.Label><Form.Control type="password" value={passwordDraft.newPassword} onChange={(e) => setPasswordDraft((p) => ({ ...p, newPassword: e.target.value }))} required /></Form.Group>
                              <Form.Group><Form.Label>Подтвердите новый пароль</Form.Label><Form.Control type="password" value={passwordDraft.confirmPassword} onChange={(e) => setPasswordDraft((p) => ({ ...p, confirmPassword: e.target.value }))} required /></Form.Group>
                              {passwordMessage && <Alert variant="success" className="mb-0 py-2">{passwordMessage}</Alert>}
                              {passwordError && <Alert variant="danger" className="mb-0 py-2">{passwordError}</Alert>}
                              <Button type="submit" disabled={passwordSaving} className="d-inline-flex align-items-center gap-2">{passwordSaving && <Spinner size="sm" />} Обновить пароль</Button>
                            </Form>
                          </Card.Body>
                        </Card>
                      )}

                      {settingsSection === 'avatar' && (
                        <Card className="school-panel school-panel-inner">
                          <Card.Body>
                            <h3 className="h5 mb-3">Аватар</h3>
                            <div className="d-flex flex-wrap align-items-center gap-3 mb-3">
                              <img src={avatarUrl} alt="avatar" className="school-avatar-preview" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }} />
                              <div className="school-avatar-fallback">{(user?.username || 'U').slice(0, 1).toUpperCase()}</div>
                              <div>
                                <p className="text-secondary mb-2">PNG, JPG, WEBP до 2 MB.</p>
                                <div className="d-flex gap-2 flex-wrap">
                                  <Form.Label className="btn btn-primary mb-0 d-inline-flex align-items-center gap-2"><ImageUp size={16} /> Загрузить<Form.Control type="file" accept="image/png,image/jpeg,image/webp" onChange={uploadAvatar} hidden disabled={avatarBusy} /></Form.Label>
                                  <Button variant="outline-danger" onClick={removeAvatar} disabled={avatarBusy} className="d-inline-flex align-items-center gap-2"><Trash2 size={16} /> Удалить</Button>
                                </div>
                              </div>
                            </div>
                            {avatarMessage && <Alert variant="success" className="mb-0 py-2">{avatarMessage}</Alert>}
                            {avatarError && <Alert variant="danger" className="mb-0 py-2">{avatarError}</Alert>}
                          </Card.Body>
                        </Card>
                      )}

                      {settingsSection === 'preferences' && (
                        <Card className="school-panel school-panel-inner">
                          <Card.Body>
                            <h3 className="h5 mb-3">Персонализация интерфейса</h3>
                            <p className="text-secondary">Настройте язык и тему. Изменения сохраняются для вашего аккаунта.</p>
                            <UiPreferencesControls />
                            <hr />
                            <div className="text-secondary small">Совет: используйте системный режим, если переключаете устройства с разной темой.</div>
                          </Card.Body>
                        </Card>
                      )}
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            )}
          </Col>
        </Row>
      </Container>
    </main>
  );
}

interface NavItemProps {
  icon: ReactNode;
  label: string;
  active?: boolean;
  onClick: () => void;
}

function NavItem({ icon, label, active = false, onClick }: NavItemProps) {
  return (
    <button onClick={onClick} className={`school-nav-item ${active ? 'active' : ''}`}>
      {icon}
      <span>{label}</span>
    </button>
  );
}

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: string;
  note: string;
}

function StatCard({ icon, label, value, note }: StatCardProps) {
  return (
    <Card className="school-panel h-100">
      <Card.Body className="d-flex align-items-start gap-3">
        <div className="school-stat-icon">{icon}</div>
        <div>
          <div className="text-secondary small">{label}</div>
          <div className="h4 mb-1">{value}</div>
          <small className="text-secondary">{note}</small>
        </div>
      </Card.Body>
    </Card>
  );
}

interface ActivityItemProps {
  title: string;
  time: string;
  result: string;
}

function ActivityItem({ title, time, result }: ActivityItemProps) {
  return (
    <div className="activity-item">
      <div className="activity-icon"><Clock3 size={16} /></div>
      <div>
        <strong>{title}</strong>
        <span>{time}</span>
      </div>
      <em>{result}</em>
    </div>
  );
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('File read failed'));
    reader.readAsDataURL(file);
  });
}
