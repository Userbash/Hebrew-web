import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, Card, Col, Form, Row, Spinner } from 'react-bootstrap';
import { AlertCircle, Bot, CheckCircle2, ClipboardList, MessageSquareCode, Play, RefreshCw, ShieldCheck, Sparkles, Workflow } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { devToolkitApi, type DevToolkitMessage, type DevToolkitMode, type DevToolkitResponse, type DevToolkitSession } from '../../api/devtoolkit';
import './DevToolkitPage.css';

const MODE_OPTIONS: Array<{ value: DevToolkitMode; label: string; description: string }> = [
  { value: 'plan', label: 'Plan', description: 'Read-only planning only' },
  { value: 'dry_run', label: 'Dry Run', description: 'Preview planned changes' },
  { value: 'apply', label: 'Apply', description: 'Requires confirmation later' },
  { value: 'review', label: 'Review', description: 'Inspect existing changes' },
  { value: 'repo', label: 'Repo', description: 'SourceCraft repo tasks' },
];

const DEVELOPMENT_PLAN = [
  'Define a stable response contract: accepted, planned, blocked, failed, next step.',
  'Expand the composer surface so multi-line tasks and constraints are readable before send.',
  'Render human summary first, structured tasks second, raw trace last.',
  'Separate planning state from execution state so the operator always knows whether code changed.',
  'Add clear review controls for clipboard payload, diff preview, and approval gates.',
];

const toPrettyJson = (value: unknown) => {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

const getStatusVariant = (status?: string) => {
  if (status === 'planned' || status === 'completed') return 'success';
  if (status === 'blocked' || status === 'warning') return 'warning';
  if (status === 'error' || status === 'failed') return 'danger';
  return 'secondary';
};

const getExecutionMessage = (response: DevToolkitResponse | null) => {
  if (!response) return 'No orchestrator response yet.';
  if (response.status === 'planned') return 'Plan created. No files changed and no commands executed in this workspace.';
  if (response.status === 'blocked') return 'The planner responded, but execution is blocked until approval.';
  if (response.status === 'error') return 'The planner returned an error and needs operator review.';
  return 'Response received. Review the trace and next steps.';
};

const getTraceError = (response: DevToolkitResponse | null) => {
  if (!response || !response.fulltrace || typeof response.fulltrace !== 'object') return '';
  const message = (response.fulltrace as Record<string, unknown>).message;
  return typeof message === 'string' ? message : '';
};

export function DevSessionSidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  loading,
}: {
  sessions: DevToolkitSession[];
  activeSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  loading?: boolean;
}) {
  return (
    <Card className="devtoolkit-panel devtoolkit-sidebar-panel">
      <Card.Body>
        <div className="devtoolkit-panel-head">
          <div>
            <p className="devtoolkit-kicker">Sessions</p>
            <h2>Dev Sessions</h2>
          </div>
          <Button variant="outline-light" size="sm" onClick={onNewSession} className="devtoolkit-ghost-btn">
            New
          </Button>
        </div>

        <div className="devtoolkit-session-list">
          {loading && <div className="devtoolkit-muted"><Spinner animation="border" size="sm" /> Loading sessions...</div>}
          {!loading && sessions.length === 0 && <div className="devtoolkit-muted">No sessions yet. Start with a planning request.</div>}
          {sessions.map((session) => (
            <button
              key={session.session_id}
              type="button"
              className={`devtoolkit-session-item ${activeSessionId === session.session_id ? 'active' : ''}`}
              onClick={() => onSelectSession(session.session_id)}
            >
              <div className="devtoolkit-session-item-top">
                <strong>{session.title}</strong>
                <Badge bg={session.mode === 'plan' ? 'info' : 'secondary'}>{session.mode}</Badge>
              </div>
              <div className="devtoolkit-session-meta">
                <span>{session.session_id.slice(0, 8)}</span>
                <span>{session.message_count} msg</span>
              </div>
              {session.last_summary && <p>{session.last_summary}</p>}
            </button>
          ))}
        </div>
      </Card.Body>
    </Card>
  );
}

export function DevChatWindow({
  messages,
  value,
  onChange,
  onSend,
  sending,
  mode,
  onModeChange,
  repoContext,
  onToggleRepoContext,
  sessionId,
  connectionState,
  response,
}: {
  messages: DevToolkitMessage[];
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  sending?: boolean;
  mode: DevToolkitMode;
  onModeChange: (mode: DevToolkitMode) => void;
  repoContext: boolean;
  onToggleRepoContext: (next: boolean) => void;
  sessionId: string;
  connectionState: 'online' | 'idle' | 'loading';
  response: DevToolkitResponse | null;
}) {
  const taskCount = response?.tasks?.length || 0;
  const agentCount = response?.agents?.length || 0;

  return (
    <Card className="devtoolkit-panel devtoolkit-chat-panel">
      <Card.Body>
        <div className="devtoolkit-panel-head devtoolkit-panel-head-stack">
          <div>
            <p className="devtoolkit-kicker">AI Bridge Orchestrator</p>
            <div className="devtoolkit-title-row">
              <h2>Dev Toolkit Chat</h2>
              <Badge bg={connectionState === 'online' ? 'success' : connectionState === 'loading' ? 'warning' : 'secondary'} className="devtoolkit-connection-badge">
                {connectionState === 'online' ? 'Connected' : connectionState === 'loading' ? 'Checking' : 'Idle'}
              </Badge>
            </div>
          </div>

          <div className="devtoolkit-mode-row">
            {MODE_OPTIONS.map((item) => (
              <button
                key={item.value}
                type="button"
                className={`devtoolkit-mode-chip ${mode === item.value ? 'active' : ''}`}
                onClick={() => onModeChange(item.value)}
              >
                <span>{item.label}</span>
                <small>{item.description}</small>
              </button>
            ))}
          </div>

          <div className="devtoolkit-status-strip">
            <div>
              <span>Session</span>
              <strong>{sessionId.slice(0, 12)}</strong>
            </div>
            <div>
              <span>Mode</span>
              <strong>{mode}</strong>
            </div>
            <div>
              <span>Tasks</span>
              <strong>{taskCount}</strong>
            </div>
            <div>
              <span>Agents</span>
              <strong>{agentCount}</strong>
            </div>
          </div>
        </div>

        <div className="devtoolkit-chat-scroller" aria-live="polite">
          {messages.length === 0 && <div className="devtoolkit-empty-state">Send a task to create a planning trace. This surface is for operator-readable orchestration, not raw backend debugging.</div>}
          {messages.map((message) => (
            <article key={message.message_id} className={`devtoolkit-message ${message.role}`}>
              <div className="devtoolkit-message-meta">
                <strong>{message.role === 'assistant' ? 'AI Orchestrator' : 'You'}</strong>
                <span>{new Date(message.created_at).toLocaleString()}</span>
              </div>
              <div className="devtoolkit-message-body">{message.content}</div>
            </article>
          ))}
          {sending && <div className="devtoolkit-muted"><Spinner animation="border" size="sm" /> Building plan...</div>}
        </div>

        <div className="devtoolkit-composer-shell">
          <div className="devtoolkit-composer-head">
            <div>
              <strong>Task input</strong>
              <p>Describe the goal, constraints, expected output, and review focus. The planner should not need guesswork.</p>
            </div>
            <Badge bg="dark">Shift+Enter for newline</Badge>
          </div>

          <Form.Control
            as="textarea"
            rows={6}
            placeholder="Example: Analyze the admin telemetry flow, identify weak status messaging, propose a safer response format, and produce a reviewable frontend implementation plan."
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                onSend();
              }
            }}
            disabled={sending}
            className="devtoolkit-composer-input"
          />

          <div className="devtoolkit-composer-footer">
            <Form.Check
              type="switch"
              label="Include repo context"
              checked={repoContext}
              onChange={(event) => onToggleRepoContext(event.target.checked)}
            />
            <span className="devtoolkit-muted inline">The response should explain accepted state, plan status, next step, and whether anything actually changed.</span>
            <Button className="devtoolkit-send-btn" onClick={onSend} disabled={sending || !value.trim()}>
              {sending ? <Spinner size="sm" animation="border" /> : <MessageSquareCode size={16} />}
              Send to Orchestrator
            </Button>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
}

export function ExecutionPlanPanel({ response }: { response: DevToolkitResponse | null }) {
  const tasks = response?.tasks || [];
  const agents = response?.agents || [];
  const traceError = getTraceError(response);

  return (
    <Card className="devtoolkit-panel">
      <Card.Body>
        <div className="devtoolkit-panel-head">
          <div>
            <p className="devtoolkit-kicker">Planner result</p>
            <h2>Readable response</h2>
          </div>
          <Badge bg={getStatusVariant(response?.status)}>{response?.status || 'idle'}</Badge>
        </div>

        <div className="devtoolkit-result-grid">
          <div className="devtoolkit-result-card success">
            <span>Request</span>
            <strong>{response ? 'Accepted' : 'Waiting'}</strong>
            <small>{response ? `Session ${response.session_id.slice(0, 12)}` : 'No request sent yet'}</small>
          </div>
          <div className={`devtoolkit-result-card ${response?.status === 'planned' ? 'success' : response ? 'warning' : 'neutral'}`}>
            <span>Planner state</span>
            <strong>{response?.status || 'idle'}</strong>
            <small>{getExecutionMessage(response)}</small>
          </div>
          <div className="devtoolkit-result-card neutral">
            <span>Tasks</span>
            <strong>{tasks.length}</strong>
            <small>{agents.length} candidate agents</small>
          </div>
          <div className="devtoolkit-result-card neutral">
            <span>Clipboard</span>
            <strong>{response?.clipboard_payload ? 'Ready' : 'Empty'}</strong>
            <small>{response?.clipboard_payload ? 'Plan payload available' : 'No export yet'}</small>
          </div>
        </div>

        <p className="devtoolkit-summary">{response?.summary || 'No plan yet. The panel should show accepted state first, then a concise operator-facing result.'}</p>

        {traceError && (
          <div className="devtoolkit-error devtoolkit-inline-error">
            <AlertCircle size={16} />
            <span>{traceError}</span>
          </div>
        )}

        <div className="devtoolkit-explainer-grid">
          <div className="devtoolkit-explainer-card">
            <CheckCircle2 size={16} />
            <div>
              <strong>What happened</strong>
              <p>The request was stored in the session and the planner returned a structured response.</p>
            </div>
          </div>
          <div className="devtoolkit-explainer-card">
            <ShieldCheck size={16} />
            <div>
              <strong>What did not happen</strong>
              <p>No file mutations, shell execution, migrations, or deploy actions were run from this screen.</p>
            </div>
          </div>
          <div className="devtoolkit-explainer-card">
            <Workflow size={16} />
            <div>
              <strong>What to review next</strong>
              <p>Check tasks, candidate agents, and trace details before moving to any approval or execution stage.</p>
            </div>
          </div>
        </div>

        <div className="devtoolkit-task-list">
          {tasks.length === 0 && <div className="devtoolkit-muted">No planned tasks yet.</div>}
          {tasks.map((task, index) => (
            <div key={String(task.task_id || task.id || index)} className="devtoolkit-task-item">
              <div className="devtoolkit-task-item-top">
                <strong>{String(task.description || task.title || task.task_id || 'Task')}</strong>
                <Badge bg="info">{String(task.type || task.task_type || 'plan')}</Badge>
              </div>
              <p>{String(task.required_capability || task.capability || 'plan')}</p>
              {Array.isArray(task.dependencies) && task.dependencies.length > 0 && (
                <small>Depends on: {task.dependencies.map(String).join(', ')}</small>
              )}
            </div>
          ))}
        </div>

        <details className="devtoolkit-disclosure">
          <summary>Raw plan JSON</summary>
          <pre className="devtoolkit-json-block">{toPrettyJson(response?.plan || {})}</pre>
        </details>

        <details className="devtoolkit-disclosure">
          <summary>Full trace</summary>
          <pre className="devtoolkit-json-block devtoolkit-fulltrace">{toPrettyJson(response?.fulltrace || {})}</pre>
        </details>
      </Card.Body>
    </Card>
  );
}

function DevelopmentRoadmapPanel() {
  return (
    <Card className="devtoolkit-panel devtoolkit-notice-panel">
      <Card.Body>
        <div className="devtoolkit-panel-head">
          <div>
            <p className="devtoolkit-kicker">Development plan</p>
            <h2>How this screen should evolve</h2>
          </div>
          <ClipboardList size={18} />
        </div>
        <div className="devtoolkit-roadmap-list">
          {DEVELOPMENT_PLAN.map((item) => (
            <div key={item} className="devtoolkit-roadmap-item">{item}</div>
          ))}
        </div>
      </Card.Body>
    </Card>
  );
}

export default function DevToolkitPage({ embedded = false }: { embedded?: boolean }) {
  const { user } = useAuth();
  const { theme } = useTheme();

  const [sessions, setSessions] = useState<DevToolkitSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState('');
  const [messages, setMessages] = useState<DevToolkitMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [mode, setMode] = useState<DevToolkitMode>('plan');
  const [repoContext, setRepoContext] = useState(false);
  const [sending, setSending] = useState(false);
  const [response, setResponse] = useState<DevToolkitResponse | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState('');
  const connectionState: 'online' | 'idle' | 'loading' = loadingSessions ? 'loading' : activeSessionId ? 'online' : 'idle';

  const currentSession = useMemo(
    () => sessions.find((session) => session.session_id === activeSessionId) || null,
    [activeSessionId, sessions]
  );

  const loadSessions = async () => {
    setLoadingSessions(true);
    setError('');
    try {
      const data = await devToolkitApi.listSessions();
      const next = data.sessions || [];
      setSessions(next);
      if (!activeSessionId && next.length > 0) {
        setActiveSessionId(next[0].session_id);
      }
    } catch {
      setError('Failed to load Dev Toolkit sessions.');
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadMessages = async (sessionId: string) => {
    setError('');
    if (!sessionId) {
      setMessages([]);
      return;
    }
    setLoadingMessages(true);
    try {
      const data = await devToolkitApi.getSessionMessages(sessionId);
      setMessages(data.messages || []);
    } catch {
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  useEffect(() => {
    void loadSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      void loadMessages(activeSessionId);
    }
  }, [activeSessionId]);

  const createSession = async () => {
    const result = await devToolkitApi.createSession({ mode, repo_context: repoContext });
    const session = result.session;
    setSessions((prev) => [session, ...prev.filter((item) => item.session_id !== session.session_id)]);
    setActiveSessionId(session.session_id);
    setMessages([]);
    setResponse(null);
  };

  const createSessionAndReturnId = async () => {
    const result = await devToolkitApi.createSession({ mode, repo_context: repoContext });
    const session = result.session;
    setSessions((prev) => [session, ...prev.filter((item) => item.session_id !== session.session_id)]);
    setActiveSessionId(session.session_id);
    return session.session_id;
  };

  const handleSend = async () => {
    if (!draft.trim() || sending) {
      return;
    }

    setSending(true);
    setError('');
    try {
      const sessionId = activeSessionId || (await createSessionAndReturnId());
      const result = await devToolkitApi.chat({
        session_id: sessionId,
        message: draft.trim(),
        mode,
        repo_context: repoContext,
        allow_code_changes: false,
        allow_execution: false,
        dry_run: mode === 'dry_run',
      });
      setResponse(result);
      setActiveSessionId(result.session_id);
      setSessions((prev) => prev.map((session) => (
        session.session_id === result.session_id
          ? { ...session, last_summary: result.summary, mode: result.status === 'planned' ? 'plan' : session.mode }
          : session
      )));
      setDraft('');
      await loadMessages(result.session_id);
      await loadSessions();
    } catch {
      setError('Dev Toolkit planning failed.');
    } finally {
      setSending(false);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    setResponse(null);
    await loadMessages(sessionId);
  };

  const topSummary = response?.summary || currentSession?.last_summary || 'Plan-only Dev Toolkit for safe orchestrator planning.';

  return (
    <main className={`devtoolkit-page ${embedded ? 'embedded' : ''} ${theme === 'dark' ? 'dark' : 'light'}`}>
      {!embedded && (
        <section className="devtoolkit-hero">
          <div>
            <p className="devtoolkit-kicker">Admin Panel / Dev Toolkit</p>
            <h1>Readable orchestrator planning for internal engineering work</h1>
            <p>{topSummary}</p>
            <p className="devtoolkit-muted inline">Operator: {user?.email || user?.username || 'unknown'}</p>
          </div>
          <div className="devtoolkit-hero-stats">
            <div>
              <strong>{sessions.length}</strong>
              <span>Sessions</span>
            </div>
            <div>
              <strong>{messages.length}</strong>
              <span>Messages</span>
            </div>
            <div>
              <strong>{response?.status || 'idle'}</strong>
              <span>Status</span>
            </div>
          </div>
        </section>
      )}

      {embedded && (
        <section className="devtoolkit-embedded-status">
          <div>
            <p className="devtoolkit-kicker">AI Bridge Orchestrator</p>
            <h2>Dev Toolkit Chat</h2>
            <p>{topSummary}</p>
          </div>
          <div className="devtoolkit-embedded-stats">
            <Badge bg="info">{sessions.length} sessions</Badge>
            <Badge bg="secondary">{messages.length} messages</Badge>
            <Badge bg={getStatusVariant(response?.status)}>{response?.status || 'idle'}</Badge>
          </div>
        </section>
      )}

      {error && <div className="devtoolkit-error">{error}</div>}

      <div className="devtoolkit-toolbar">
        <Button variant="light" className="devtoolkit-toolbar-btn" onClick={() => void loadSessions()}>
          <RefreshCw size={16} /> Refresh
        </Button>
        <Button variant="light" className="devtoolkit-toolbar-btn" onClick={() => void createSession()}>
          <Sparkles size={16} /> New session
        </Button>
        <Button variant="light" className="devtoolkit-toolbar-btn" onClick={() => void handleSend()} disabled={sending || !draft.trim()}>
          <Play size={16} /> Plan
        </Button>
      </div>

      <Row className="g-3 g-xl-4 devtoolkit-grid mt-4">
        <Col xl={3} lg={4} md={12}>
          <DevSessionSidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={(sessionId) => void handleSelectSession(sessionId)}
            onNewSession={() => void createSession()}
            loading={loadingSessions}
          />
        </Col>
        <Col xl={9} lg={8} md={12}>
          <div className="devtoolkit-main-grid">
            <DevChatWindow
              messages={messages}
              value={draft}
              onChange={setDraft}
              onSend={() => void handleSend()}
              sending={sending || loadingMessages}
              mode={mode}
              onModeChange={setMode}
              repoContext={repoContext}
              onToggleRepoContext={setRepoContext}
              sessionId={activeSessionId || response?.session_id || 'draft'}
              connectionState={connectionState}
              response={response}
            />

            <ExecutionPlanPanel response={response} />
            <DevelopmentRoadmapPanel />

            <Card className="devtoolkit-panel devtoolkit-notice-panel">
              <Card.Body>
                <div className="devtoolkit-panel-head">
                  <div>
                    <p className="devtoolkit-kicker">Safety</p>
                    <h2>Plan mode boundary</h2>
                  </div>
                  <Bot size={18} />
                </div>
                <p>
                  This screen is intentionally read-only. It should clearly tell the operator whether the planner accepted the request,
                  what plan was returned, and what still requires explicit approval before any code or infrastructure action.
                </p>
              </Card.Body>
            </Card>
          </div>
        </Col>
      </Row>
    </main>
  );
}
