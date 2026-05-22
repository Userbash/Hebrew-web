import { useEffect, useMemo, useState, useRef, type ChangeEvent } from 'react';
import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Form,
  InputGroup,
  Modal,
  ProgressBar,
  Row,
  Spinner,
  Table,
} from 'react-bootstrap';
import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  BookMarked,
  CheckCircle2,
  CircleUserRound,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  FileText,
  KeyRound,
  LayoutDashboard,
  Lock,
  LogOut,
  Settings,
  Shield,
  Siren,
  UserPlus,
  Users,
  UsersRound,
  X,
} from 'lucide-react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth, type RoleKey } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import api from '../../api/client';
import { accessApi, type AccessGroupSummary, type CatalogPermission, type UserRoleAssignment } from '../../api/access';
import { adminUsersApi, type AdminUser, type AdminUsersListParams, type CreateAdminUserPayload, type UserSession } from '../../api/adminUsers';
import { publicationsApi, type Publication } from '../../api/publications';
import { adminLogsApi, type AdminLogItem } from '../../api/adminLogs';
import { adminSystemApi, type AdminSystemMetricsResponse } from '../../api/adminSystem';
import { adminAuditApi, type AuditEventItem, type AuditMapItem } from '../../api/adminAudit';
import { canEditUserPermissions } from '../../security/canEditUserPermissions';
import { hasPermission } from '../../security/rbac';
import './AdminPanel.css';
import UiPreferencesControls from '../Layout/UiPreferencesControls';

const ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];
const SEARCHABLE_RBAC_ROLES = [
  'root',
  'platform_admin',
  'security_admin',
  'content_admin',
  'editor',
  'moderator',
  'support',
  'analyst',
  'user',
];

const USER_SORT_OPTIONS: Array<{ value: NonNullable<AdminUsersListParams['sortBy']>; label: string }> = [
  { value: 'created_at', label: 'Created at' },
  { value: 'updated_at', label: 'Updated at' },
  { value: 'last_login', label: 'Last login' },
  { value: 'publication_count', label: 'Publications' },
  { value: 'xp_total', label: 'XP' },
  { value: 'level', label: 'Level' },
  { value: 'username', label: 'Username' },
  { value: 'email', label: 'Email' },
  { value: 'id', label: 'User ID' },
];

type SectionId =
  | 'overview'
  | 'admin-map'
  | 'system-monitoring'
  | 'user-directory'
  | 'user-create'
  | 'groups-catalog'
  | 'group-assignments'
  | 'publications-review'
  | 'audit-trail'
  | 'audit-logs';

type NavGroupId = 'dashboard' | 'users' | 'groups' | 'content' | 'audit';

const NAV_GROUPS_BASE: Array<{
  id: NavGroupId;
  title: string;
  icon: React.ReactNode;
  items: Array<{ id: SectionId; label: string }>;
}> = [
  {
    id: 'dashboard',
    title: 'Dashboard',
    icon: <LayoutDashboard size={16} />,
    items: [
      { id: 'overview', label: 'Overview & health' },
      { id: 'admin-map', label: 'Admin map & logging' },
      { id: 'system-monitoring', label: 'System monitoring' },
    ],
  },
  {
    id: 'users',
    title: 'Users',
    icon: <Users size={16} />,
    items: [
      { id: 'user-directory', label: 'Directory' },
      { id: 'user-create', label: 'Create user' },
    ],
  },
  {
    id: 'groups',
    title: 'Groups & access',
    icon: <Shield size={16} />,
    items: [
      { id: 'groups-catalog', label: 'Groups catalog' },
      { id: 'group-assignments', label: 'User assignments' },
    ],
  },
  {
    id: 'content',
    title: 'Content moderation',
    icon: <BookMarked size={16} />,
    items: [{ id: 'publications-review', label: 'Publications queue' }],
  },
  {
    id: 'audit',
    title: 'Audit & logs',
    icon: <Activity size={16} />,
    items: [
      { id: 'audit-trail', label: 'Change audit trail' },
      { id: 'audit-logs', label: 'API activity logs' },
    ],
  },
];


const SECTION_GUIDE_BASE: Record<SectionId, { title: string; description: string; nextStep: string }> = {
  overview: {
    title: 'Control center',
    description: 'Main system health, key metrics and recent platform activity in one place.',
    nextStep: 'Start here, then move to Users or Groups to make changes.'
  },
  'admin-map': {
    title: 'Admin map and logging map',
    description: 'Clear map of where each admin function lives and how every critical change is logged.',
    nextStep: 'Use this map when you need to quickly find where to create users, manage groups, moderate publications or inspect who changed what.'
  },
  'system-monitoring': {
    title: 'System monitoring',
    description: 'Live CPU, memory, disk, database latency, locks, I/O and runtime health metrics.',
    nextStep: 'Use this section first to detect bottlenecks before changing users, roles or publications.'
  },
  'user-directory': {
    title: 'User directory',
    description: 'Search users, check access and edit profile data without leaving this section.',
    nextStep: 'Use quick search first, then open advanced filters only when needed.'
  },
  'user-create': {
    title: 'Create user',
    description: 'Create a new account with minimal required fields and temporary credentials.',
    nextStep: 'After creation, open User assignments to grant roles.'
  },
  'groups-catalog': {
    title: 'Groups and permissions',
    description: 'Manage role groups and permission sets used by RBAC policy.',
    nextStep: 'Select an existing group on the left before editing permissions.'
  },
  'group-assignments': {
    title: 'Role assignments',
    description: 'Assign or revoke role groups for the selected user with audit notes.',
    nextStep: 'Keep an audit note for every security-sensitive role mutation.'
  },
  'publications-review': {
    title: 'Publications moderation',
    description: 'Create content, review queue state and moderate publication lifecycle.',
    nextStep: 'Use status actions on the right side of each row.'
  },
  'audit-trail': {
    title: 'Change audit trail',
    description: 'Who changed what, when, where, and with which outcome across site and admin areas.',
    nextStep: 'Filter by resource/action/outcome to pinpoint exact change operations quickly.'
  },
  'audit-logs': {
    title: 'Audit logs',
    description: 'Filter API activity by method, path and status for incident review.',
    nextStep: 'Use status and path filters to isolate a specific operation.'
  }
};

const ADMIN_SECTION_MAP: Array<{
  section: string;
  purpose: string;
  primaryActions: string;
  apiScope: string;
}> = [
  {
    section: 'Dashboard / Overview',
    purpose: 'Quick health and operational status of admin + site.',
    primaryActions: 'Read KPI cards, detect anomalies, jump to target section.',
    apiScope: '/api/admin/system, /api/admin/logs, /api/admin/audit',
  },
  {
    section: 'Users / Directory',
    purpose: 'Find users and edit profile/access context.',
    primaryActions: 'Search, open sessions, soft-delete, restore, edit account.',
    apiScope: '/api/admin/users/*',
  },
  {
    section: 'Users / Create user',
    purpose: 'Provision new account with temporary credentials.',
    primaryActions: 'Create user, then move to assignments for role grants.',
    apiScope: '/api/admin/users (POST)',
  },
  {
    section: 'Groups / Catalog',
    purpose: 'Manage RBAC groups and permission templates.',
    primaryActions: 'Create, edit, delete groups and save permission sets.',
    apiScope: '/api/admin/access/roles*',
  },
  {
    section: 'Groups / Assignments',
    purpose: 'Grant/revoke group roles per user and control block state.',
    primaryActions: 'Assign role, revoke role, block/unblock with audit note.',
    apiScope: '/api/admin/access/users/*',
  },
  {
    section: 'Content / Publications',
    purpose: 'Moderate and publish content lifecycle.',
    primaryActions: 'Create publication, send to review, approve, archive, delete.',
    apiScope: '/api/admin/publications*',
  },
  {
    section: 'Audit / Change trail',
    purpose: 'Investigate who changed what and with what result.',
    primaryActions: 'Filter by area/resource/action/outcome/path.',
    apiScope: '/api/admin/audit/events',
  },
  {
    section: 'Audit / API activity logs',
    purpose: 'Technical API stream for incident analysis.',
    primaryActions: 'Filter by method/path/status, inspect latency/errors.',
    apiScope: '/api/admin/logs',
  },
];

const LOGGING_EVENT_MAP: Array<{
  eventType: string;
  source: string;
  whereToCheck: string;
}> = [
  { eventType: 'User create/update/delete/restore', source: 'Users + Access endpoints', whereToCheck: 'Audit -> Change trail (resource: users)' },
  { eventType: 'Role assign/revoke/block/unblock', source: 'Access control endpoints', whereToCheck: 'Audit -> Change trail (resource: access)' },
  { eventType: 'Publication moderation', source: 'Publications endpoints', whereToCheck: 'Audit -> Change trail (resource: publications)' },
  { eventType: 'Auth mutations (login/logout/register)', source: 'Auth endpoints', whereToCheck: 'Audit -> Change trail (area: auth)' },
  { eventType: 'Raw request/response telemetry', source: 'Global telemetry middleware', whereToCheck: 'Audit -> API activity logs' },
];

const formatBytes = (bytes?: number | null) => {
  const value = Number(bytes || 0);
  if (!Number.isFinite(value) || value <= 0) {
    return '0 B';
  }

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let index = 0;
  let next = value;

  while (next >= 1024 && index < units.length - 1) {
    next /= 1024;
    index += 1;
  }

  return `${next.toFixed(index === 0 ? 0 : 2)} ${units[index]}`;
};

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  return new Date(value).toLocaleString();
};

const statusVariant = (status?: string) => {
  switch (status) {
    case 'published':
      return 'success';
    case 'archived':
      return 'secondary';
    case 'review':
      return 'warning';
    default:
      return 'info';
  }
};

const normalizeRoleKey = (value: string) =>
  value.trim().toLowerCase().replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 64);

const AVATAR_MAX_SIZE_BYTES = 2 * 1024 * 1024;
const AVATAR_ALLOWED_MIME_TYPES = ['image/png', 'image/jpeg', 'image/webp'];

const getAvatarInitials = (username?: string | null, email?: string | null) => {
  const source = (username || email || "U").trim();
  const pure = source.includes("@") ? source.split("@")[0] : source;
  const compact = pure.replace(/[^a-zA-Z0-9]+/g, " ").trim();

  if (!compact) {
    return "U";
  }

  const parts = compact.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  return compact.slice(0, 2).toUpperCase();
};

const toReadableError = (message?: string) => {
  if (!message) {
    return 'Action failed';
  }

  if (message.includes('Self block mutation is not allowed')) {
    return 'You cannot block your own administrator account.';
  }

  return message;
};

const getSeverity = (value: number, warnAt: number, criticalAt: number): 'healthy' | 'warning' | 'critical' => {
  if (value >= criticalAt) return 'critical';
  if (value >= warnAt) return 'warning';
  return 'healthy';
};
export default function AdminPanel() {
  const { user, setUser, hasAnyRole } = useAuth();
  const { language } = useLanguage();

  const [activeSection, setActiveSection] = useState<SectionId>('overview');
  const [openNavGroups, setOpenNavGroups] = useState<Record<NavGroupId, boolean>>({
    dashboard: true,
    users: true,
    groups: true,
    content: true,
    audit: true,
  });


  const A = (ru: string, en: string, he: string) => {
    if (language === 'ru') return ru;
    if (language === 'he') return he;
    return en;
  };

  const NAV_GROUPS = NAV_GROUPS_BASE.map((group) => ({
    ...group,
    title:
      group.id === 'dashboard' ? A('Панель', 'Dashboard', 'לוח בקרה') :
      group.id === 'users' ? A('Пользователи', 'Users', 'משתמשים') :
      group.id === 'groups' ? A('Группы и доступ', 'Groups & access', 'קבוצות והרשאות') :
      group.id === 'content' ? A('Модерация контента', 'Content moderation', 'ניהול תוכן') :
      A('Аудит и логи', 'Audit & logs', 'ביקורת ולוגים'),
    items: group.items.map((item) => ({
      ...item,
      label:
        item.id === 'overview' ? A('Обзор и состояние', 'Overview & health', 'סקירה ומצב') :
        item.id === 'admin-map' ? A('Карта админа и логирование', 'Admin map & logging', 'מפת ניהול ולוגים') :
        item.id === 'system-monitoring' ? A('Мониторинг системы', 'System monitoring', 'ניטור מערכת') :
        item.id === 'user-directory' ? A('Каталог', 'Directory', 'ספרייה') :
        item.id === 'user-create' ? A('Создать пользователя', 'Create user', 'יצירת משתמש') :
        item.id === 'groups-catalog' ? A('Каталог групп', 'Groups catalog', 'קטלוג קבוצות') :
        item.id === 'group-assignments' ? A('Назначения пользователей', 'User assignments', 'שיוכי משתמשים') :
        item.id === 'publications-review' ? A('Очередь публикаций', 'Publications queue', 'תור פרסומים') :
        item.id === 'audit-trail' ? A('Журнал изменений', 'Change audit trail', 'יומן שינויים') :
        A('Логи API', 'API activity logs', 'לוגים של API'),
    })),
  }));

  const SECTION_GUIDE = SECTION_GUIDE_BASE;

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okMessage, setOkMessage] = useState<string | null>(null);

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [rbacRoleFilter, setRbacRoleFilter] = useState('');
  const [permissionFilter, setPermissionFilter] = useState('');
  const [publicationStatusFilter, setPublicationStatusFilter] = useState('');
  const [publicationSearchFilter, setPublicationSearchFilter] = useState('');
  const [hasPublicationsFilter, setHasPublicationsFilter] = useState<'all' | 'yes' | 'no'>('all');
  const [blockedFilter, setBlockedFilter] = useState<'all' | 'blocked' | 'active'>('all');
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [sortBy, setSortBy] = useState<NonNullable<AdminUsersListParams['sortBy']>>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showAdvancedUserFilters, setShowAdvancedUserFilters] = useState(false);

  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [selectedUserSessions, setSelectedUserSessions] = useState<UserSession[]>([]);
  const [showSessionsModal, setShowSessionsModal] = useState(false);
  const [showUserSettingsModal, setShowUserSettingsModal] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [selectedUserTab, setSelectedUserTab] = useState<"profile" | "security">("profile");
  const [avatarRefreshSeed, setAvatarRefreshSeed] = useState(() => Date.now());
  const [avatarLoadFailed, setAvatarLoadFailed] = useState(false);
  const [profileDraft, setProfileDraft] = useState({ username: "", first_name: "", last_name: "", email: "" });
  const [passwordDraft, setPasswordDraft] = useState({ currentPassword: "", newPassword: "", confirmPassword: "" });
  const [userAssignments, setUserAssignments] = useState<UserRoleAssignment[]>([]);

  const [createUserForm, setCreateUserForm] = useState<CreateAdminUserPayload>({
    email: '',
    username: '',
    password: '',
    first_name: '',
    last_name: '',
  });

  const [catalogHierarchy, setCatalogHierarchy] = useState<Array<{ role: RoleKey; title: string; priority: number; summary: string; privileges: string[] }>>([]);
  const [catalogPermissions, setCatalogPermissions] = useState<CatalogPermission[]>([]);
  const [groups, setGroups] = useState<AccessGroupSummary[]>([]);
  const [rolePermissionMap, setRolePermissionMap] = useState<Record<string, string[]>>({});

  const [selectedRole, setSelectedRole] = useState<RoleKey>('user');
  const [assignmentNote, setAssignmentNote] = useState('');

  const [selectedGroupKey, setSelectedGroupKey] = useState('');
  const [groupForm, setGroupForm] = useState({ roleKey: '', title: '', description: '', priority: 150 });
  const [groupPermissionDraft, setGroupPermissionDraft] = useState<string[]>([]);

  const [publications, setPublications] = useState<Publication[]>([]);
  const [publicationForm, setPublicationForm] = useState({
    title: '',
    description: '',
    status: 'draft',
    visibility: 'private' as 'private' | 'team' | 'public',
    tags: '',
  });
  const [publicationOwnerFilter, setPublicationOwnerFilter] = useState<'all' | 'mine'>('all');

  const [logs, setLogs] = useState<AdminLogItem[]>([]);
  const [logsSummary, setLogsSummary] = useState({ total: 0, server_errors: 0, client_errors: 0, success: 0, blocked: 0, errors: 0, authenticated: 0, locked_accounts: 0, avg_response_ms: 0 });
  const [logMethod, setLogMethod] = useState('');
  const [logArea, setLogArea] = useState('');
  const [logOutcome, setLogOutcome] = useState('');
  const [logPath, setLogPath] = useState('');
  const [logStatusCode, setLogStatusCode] = useState('');
  const [logLoginIdentifier, setLogLoginIdentifier] = useState('');

  const [auditEvents, setAuditEvents] = useState<AuditEventItem[]>([]);
  const [auditMap, setAuditMap] = useState<AuditMapItem[]>([]);
  const [auditSummary, setAuditSummary] = useState({ total: 0, success: 0, errors: 0, blocked: 0, admin_actions: 0, site_actions: 0, avg_duration_ms: 0 });
  const [auditArea, setAuditArea] = useState('');
  const [auditResource, setAuditResource] = useState('');
  const [auditAction, setAuditAction] = useState('');
  const [auditOutcome, setAuditOutcome] = useState('');
  const [auditPath, setAuditPath] = useState('');

  const [systemMetrics, setSystemMetrics] = useState<AdminSystemMetricsResponse['metrics'] | null>(null);

  const activeRoles = user?.access?.roleKeys || [];
  const userMenuRef = useRef<HTMLDivElement | null>(null);

  const currentUserId = user?.id || null;
  const avatarUrl = currentUserId ? '/api/profile-avatar/me?v=' + avatarRefreshSeed : null;
  const hasAvatarImage = Boolean(avatarUrl) && !avatarLoadFailed;

  const currentUserDisplayName = user?.username || user?.email?.split('@')[0] || 'Operator';
  const currentUserRole = user?.access?.highestRole || user?.role || 'user';
  const currentUserStatus = user?.access?.isSystemBlocked ? 'Blocked' : 'Active';
  const currentUserPosts = publications.filter((item) => item.metadata?.authorId === currentUserId).length;
  const avatarInitials = getAvatarInitials(user?.username, user?.email);

  const selectedGroup = useMemo(
    () => groups.find((group) => group.role_key === selectedGroupKey) || null,
    [groups, selectedGroupKey]
  );

  const reloadUsers = async () => {
    const hasPublications = hasPublicationsFilter === 'yes'
      ? true
      : hasPublicationsFilter === 'no'
        ? false
        : undefined;

    const isBlocked = blockedFilter === 'blocked'
      ? true
      : blockedFilter === 'active'
        ? false
        : undefined;

    const data = await adminUsersApi.list({
      page: 1,
      limit: 50,
      id: userIdFilter || undefined,
      search: search || undefined,
      role: roleFilter || undefined,
      rbacRole: rbacRoleFilter || undefined,
      permission: permissionFilter || undefined,
      publicationStatus: publicationStatusFilter || undefined,
      publicationSearch: publicationSearchFilter || undefined,
      hasPublications,
      includeDeleted,
      isBlocked,
      sortBy,
      sortOrder,
    });

    setUsers(data.users);
    setUsersTotal(data.pagination.total);

    if (data.users.length > 0 && !selectedUser) {
      setSelectedUser(data.users[0]);
    }
  };

  const reloadCatalog = async () => {
    const [catalog, roleList] = await Promise.all([accessApi.getCatalog(), accessApi.listRoles()]);

    const nextRolePermissionMap = catalog.rolePermissions.reduce<Record<string, string[]>>((acc, row) => {
      if (!row.granted) {
        return acc;
      }

      const role = String(row.role_key);
      if (!acc[role]) {
        acc[role] = [];
      }
      acc[role].push(row.permission_name);
      return acc;
    }, {});

    setCatalogHierarchy(catalog.hierarchy || []);
    setCatalogPermissions(catalog.permissions || []);
    setRolePermissionMap(nextRolePermissionMap);
    setGroups(roleList.roles || []);

    if (roleList.roles.length > 0) {
      setSelectedRole((prev) => prev || roleList.roles[0].role_key);
      setSelectedGroupKey((prev) => {
        const nextKey = prev || roleList.roles[0].role_key;
        setGroupPermissionDraft(nextRolePermissionMap[nextKey] || []);
        return nextKey;
      });
    }
  };

  const reloadPublications = async () => {
    const data = await publicationsApi.list();
    setPublications(data.publications || []);
  };

  const reloadLogs = async () => {
    const statusCodeNumber = Number.parseInt(logStatusCode, 10);

    const data = await adminLogsApi.list({
      page: 1,
      limit: 100,
      method: logMethod || undefined,
      area: logArea || undefined,
      outcome: logOutcome || undefined,
      path: logPath || undefined,
      loginIdentifier: logLoginIdentifier || undefined,
      statusCode: Number.isFinite(statusCodeNumber) && statusCodeNumber > 0 ? statusCodeNumber : undefined,
    });

    setLogs(data.logs || []);

    const summary = data.summary || {};
    setLogsSummary({
      total: summary.total ?? 0,
      server_errors: summary.server_errors ?? 0,
      client_errors: summary.client_errors ?? 0,
      success: summary.success ?? 0,
      blocked: summary.blocked ?? 0,
      errors: summary.errors ?? 0,
      authenticated: summary.authenticated ?? 0,
      locked_accounts: summary.locked_accounts ?? 0,
      avg_response_ms: summary.avg_response_ms ?? 0,
    });
  };

  const reloadSystemMetrics = async () => {
    const data = await adminSystemApi.metrics();
    setSystemMetrics(data.metrics || null);
  };

  const reloadAuditEvents = async () => {
    const data = await adminAuditApi.list({
      page: 1,
      limit: 100,
      area: auditArea || undefined,
      resource: auditResource || undefined,
      action: auditAction || undefined,
      outcome: auditOutcome || undefined,
      path: auditPath || undefined,
    });

    setAuditEvents(data.events || []);
    setAuditMap(data.map || []);
    setAuditSummary(data.summary || { total: 0, success: 0, errors: 0, blocked: 0, admin_actions: 0, site_actions: 0, avg_duration_ms: 0 });
  };

  const loadInitial = async () => {
    setBusy(true);
    setError(null);

    try {
      await Promise.all([reloadUsers(), reloadCatalog(), reloadPublications(), reloadLogs(), reloadSystemMetrics(), reloadAuditEvents()]);
    } catch (loadError) {
      const apiMessage = (loadError as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(toReadableError(apiMessage || 'Failed to load admin data'));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (!hasAnyRole(ADMIN_ROLES)) {
      return;
    }

    const timer = window.setTimeout(() => {
      void loadInitial();
    }, 0);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasAnyRole]);

  const autoRefreshRef = useRef<() => void>(() => undefined);

  useEffect(() => {
    autoRefreshRef.current = () => {
      if (activeSection === 'overview') {
        void Promise.all([
          reloadUsers(),
          reloadCatalog(),
          reloadPublications(),
          reloadLogs(),
          reloadSystemMetrics(),
        ]);
      } else if (activeSection === 'system-monitoring') {
        void reloadSystemMetrics();
      }
    };
  }, [activeSection]);

  useEffect(() => {
    if (!hasAnyRole(ADMIN_ROLES)) {
      return;
    }

    // 5 seconds interval is safe for older hardware (e.g. HDD)
    // while providing near real-time updates for the admin console.
    const interval = window.setInterval(() => {
      if (autoRefreshRef.current) {
        autoRefreshRef.current();
      }
    }, 5000);

    return () => window.clearInterval(interval);
  }, [hasAnyRole]);

  useEffect(() => {
    if (!error && !okMessage) {
      return;
    }

    const timer = window.setTimeout(() => {
      setError(null);
      setOkMessage(null);
    }, 7000);

    return () => window.clearTimeout(timer);
  }, [error, okMessage]);

  useEffect(() => {
    const onDocumentMouseDown = (event: MouseEvent) => {
      if (!userMenuRef.current) {
        return;
      }

      if (!userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", onDocumentMouseDown);
    return () => document.removeEventListener("mousedown", onDocumentMouseDown);
  }, []);

  const withAction = async (action: () => Promise<void>, successMessage: string) => {
    setBusy(true);
    setError(null);
    setOkMessage(null);

    try {
      await action();
      setOkMessage(successMessage);
    } catch (actionError) {
      const apiMessage = (actionError as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(toReadableError(apiMessage));
    } finally {
      setBusy(false);
    }
  };

  const openUserSettingsModal = () => {
    setProfileDraft({
      username: user?.username || "",
      first_name: user?.first_name || "",
      last_name: user?.last_name || "",
      email: user?.email || "",
    });
    setPasswordDraft({ currentPassword: "", newPassword: "", confirmPassword: "" });
    setSelectedUserTab("profile");
    setAvatarLoadFailed(false);
    setShowUserSettingsModal(true);
    setIsUserMenuOpen(false);
  };

  const jumpToMyPublications = () => {
    setPublicationOwnerFilter("mine");
    setActiveSection("publications-review");
    setIsUserMenuOpen(false);
  };

  const openMySessions = () => {
    if (!user?.id) {
      return;
    }

    setIsUserMenuOpen(false);
    void loadSessions(user.id);
  };

  const saveProfileSettings = async () => {
    if (!user?.id) {
      return;
    }

    await withAction(async () => {
      await adminUsersApi.update(user.id, {
        username: profileDraft.username.trim(),
        first_name: profileDraft.first_name.trim(),
        last_name: profileDraft.last_name.trim(),
        email: profileDraft.email.trim(),
      });

      const me = await api.get("/auth/me");
      setUser(me.data);
      await reloadUsers();
    }, "User profile updated");
  };

  const savePasswordSettings = async () => {
    await withAction(async () => {
      await api.post("/auth/change-password", passwordDraft);
      setPasswordDraft({ currentPassword: "", newPassword: "", confirmPassword: "" });
    }, "Password changed successfully");
  };

  const handleAvatarUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) {
      return;
    }

    if (!AVATAR_ALLOWED_MIME_TYPES.includes(file.type)) {
      setError('Unsupported avatar format. Use PNG, JPG or WEBP.');
      return;
    }

    if (file.size > AVATAR_MAX_SIZE_BYTES) {
      setError('Avatar file must be up to 2 MB.');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const imageBase64 = typeof reader.result === 'string' ? reader.result : null;
      if (!imageBase64) {
        return;
      }

      void withAction(async () => {
        await api.post('/profile-avatar/me', {
          imageBase64,
          mimeType: file.type,
        });

        setAvatarLoadFailed(false);
        setAvatarRefreshSeed(Date.now());
      }, 'Avatar updated');
    };

    reader.onerror = () => setError('Failed to read avatar file');
    reader.readAsDataURL(file);
  };

  const clearAvatar = async () => {
    await withAction(async () => {
      await api.delete('/profile-avatar/me');
      setAvatarLoadFailed(false);
      setAvatarRefreshSeed(Date.now());
    }, 'Avatar removed');
  };

  const toggleNavGroup = (groupId: NavGroupId) => {
    setOpenNavGroups((prev) => ({ ...prev, [groupId]: !prev[groupId] }));
  };

  const loadAssignments = async (userId: string) => {
    await withAction(async () => {
      const assignmentData = await accessApi.getUserAccess(userId);
      setUserAssignments(assignmentData.assignments);
    }, 'User access loaded');
  };

  const loadSessions = async (userId: string) => {
    await withAction(async () => {
      const sessionData = await adminUsersApi.sessions(userId);
      setSelectedUserSessions(sessionData.sessions || []);
      setShowSessionsModal(true);
    }, 'User sessions loaded');
  };

  const assignRole = async () => {
    if (!selectedUser) return;

    await withAction(async () => {
      await accessApi.assignRole(selectedUser.id, selectedRole, assignmentNote || undefined, null);
      const assignmentData = await accessApi.getUserAccess(selectedUser.id);
      setUserAssignments(assignmentData.assignments);
      setAssignmentNote('');
      await reloadUsers();
    }, `Role ${selectedRole} assigned to ${selectedUser.username}`);
  };

  const revokeRole = async () => {
    if (!selectedUser) return;

    await withAction(async () => {
      await accessApi.revokeRole(selectedUser.id, selectedRole, assignmentNote || undefined);
      const assignmentData = await accessApi.getUserAccess(selectedUser.id);
      setUserAssignments(assignmentData.assignments);
      setAssignmentNote('');
      await reloadUsers();
    }, `Role ${selectedRole} revoked from ${selectedUser.username}`);
  };

  const toggleBlockState = async (blocked: boolean) => {
    if (!selectedUser) return;

    await withAction(async () => {
      await accessApi.setBlockedState(
        selectedUser.id,
        blocked,
        assignmentNote || (blocked ? 'Blocked from admin panel' : 'Unblocked from admin panel')
      );
      setAssignmentNote('');
      await reloadUsers();
    }, blocked ? `${selectedUser.username} has been blocked` : `${selectedUser.username} has been unblocked`);
  };

  const updateUser = async (userToUpdate: AdminUser) => {
    await withAction(async () => {
      await adminUsersApi.update(userToUpdate.id, {
        first_name: userToUpdate.first_name,
        last_name: userToUpdate.last_name,
        username: userToUpdate.username,
        email: userToUpdate.email,
        xp_total: userToUpdate.xp_total,
        level: userToUpdate.level,
      });
      await reloadUsers();
    }, `${userToUpdate.username} updated`);
  };

  const createUser = async () => {
    await withAction(async () => {
      const payload: CreateAdminUserPayload = {
        email: createUserForm.email,
        username: createUserForm.username,
        password: createUserForm.password,
        first_name: createUserForm.first_name,
        last_name: createUserForm.last_name,
      };

      const result = await adminUsersApi.create(payload);
      setCreateUserForm({ email: '', username: '', password: '', first_name: '', last_name: '' });
      await reloadUsers();
      setSelectedUser(result.user);
      setActiveSection('user-directory');
    }, 'User created');
  };

  const softDeleteUser = async (userId: string) => {
    await withAction(async () => {
      await adminUsersApi.softDelete(userId);
      await reloadUsers();
    }, 'User soft-deleted');
  };

  const restoreUser = async (userId: string) => {
    await withAction(async () => {
      await adminUsersApi.restore(userId);
      await reloadUsers();
    }, 'User restored');
  };

  const createGroup = async () => {
    await withAction(async () => {
      const roleKey = normalizeRoleKey(groupForm.roleKey || groupForm.title);
      await accessApi.createRole({
        roleKey,
        title: groupForm.title,
        description: groupForm.description,
        priority: groupForm.priority,
      });
      await reloadCatalog();
      setSelectedGroupKey(roleKey);
    }, 'Group created');
  };

  const updateGroup = async () => {
    if (!selectedGroup) return;

    await withAction(async () => {
      await accessApi.updateRole(selectedGroup.role_key, {
        title: groupForm.title,
        description: groupForm.description,
        priority: groupForm.priority,
      });
      await reloadCatalog();
    }, `Group ${selectedGroup.role_key} updated`);
  };

  const deleteGroup = async () => {
    if (!selectedGroup) return;

    await withAction(async () => {
      await accessApi.deleteRole(selectedGroup.role_key);
      await reloadCatalog();
      setSelectedGroupKey('');
      setGroupPermissionDraft([]);
    }, `Group ${selectedGroup.role_key} deleted`);
  };

  const saveGroupPermissions = async () => {
    if (!selectedGroup) return;

    await withAction(async () => {
      await accessApi.setRolePermissions(selectedGroup.role_key, groupPermissionDraft);
      await reloadCatalog();
    }, `Permissions updated for ${selectedGroup.role_key}`);
  };

  const togglePermission = (permissionName: string) => {
    setGroupPermissionDraft((prev) => {
      if (prev.includes(permissionName)) {
        return prev.filter((item) => item !== permissionName);
      }

      return [...prev, permissionName];
    });
  };

  const createPublication = async () => {
    if (!publicationForm.title.trim()) {
      setError('Publication title is required');
      return;
    }

    await withAction(async () => {
      await publicationsApi.create({
        title: publicationForm.title,
        description: publicationForm.description,
        status: publicationForm.status,
        visibility: publicationForm.visibility,
        tags: publicationForm.tags.split(',').map((item) => item.trim()).filter(Boolean),
      });

      setPublicationForm({
        title: '',
        description: '',
        status: 'draft',
        visibility: 'private',
        tags: '',
      });

      await reloadPublications();
    }, 'Publication created');
  };

  const updatePublicationStatus = async (publicationId: string, status: string) => {
    await withAction(async () => {
      await publicationsApi.update(publicationId, { status });
      await reloadPublications();
    }, `Publication status changed to ${status}`);
  };

  const deletePublication = async (publicationId: string) => {
    await withAction(async () => {
      await publicationsApi.remove(publicationId);
      await reloadPublications();
    }, 'Publication deleted');
  };

  const sectionMeta = (() => {
    for (const group of NAV_GROUPS) {
      const item = group.items.find((entry) => entry.id === activeSection);
      if (item) {
        return { groupTitle: group.title, sectionLabel: item.label };
      }
    }
    return { groupTitle: 'Admin', sectionLabel: 'Admin' };
  })();

  const sectionGuide = SECTION_GUIDE[activeSection];

  const visibleUsersSummary = useMemo(() => {
    const active = users.filter((item) => !item.deleted_at).length;
    const blocked = users.filter((item) => item.is_system_blocked).length;
    const deleted = users.filter((item) => Boolean(item.deleted_at)).length;
    return { active, blocked, deleted };
  }, [users]);

  const publicationSummary = useMemo(() => {
    return publications.reduce(
      (acc, publication) => {
        const status = publication.metadata?.status || 'draft';
        if (status === 'published') acc.published += 1;
        else if (status === 'review') acc.review += 1;
        else if (status === 'archived') acc.archived += 1;
        else acc.draft += 1;
        return acc;
      },
      { draft: 0, review: 0, published: 0, archived: 0 }
    );
  }, [publications]);

  const visiblePublications = useMemo(() => {
    if (publicationOwnerFilter === 'mine' && currentUserId) {
      return publications.filter((item) => item.metadata?.authorId === currentUserId);
    }

    return publications;
  }, [publicationOwnerFilter, publications, currentUserId]);

  const logsHealth = useMemo(() => {
    const success = Math.max(logsSummary.total - logsSummary.client_errors - logsSummary.server_errors, 0);
    const successRate = logsSummary.total > 0 ? Math.round((success / logsSummary.total) * 100) : 100;
    const degradation = Math.min(100, logsSummary.server_errors * 12 + logsSummary.client_errors * 4 + Math.floor(logsSummary.avg_response_ms / 120));
    const healthScore = Math.max(0, 100 - degradation);
    return { success, successRate, healthScore };
  }, [logsSummary]);

  const monitoringSignals = useMemo(() => {
    if (!systemMetrics) {
      return {
        riskScore: 0,
        dbPressure: 0,
        diskPressure: 0,
        memoryPressure: 0,
      };
    }

    const dbPressure = Math.min(100,
      Math.round(systemMetrics.database.probe_latency_ms / 8) +
      systemMetrics.database.waiting_locks * 8 +
      systemMetrics.database.long_running_queries * 10 +
      Math.round(systemMetrics.database.max_active_query_age_seconds * 2)
    );

    const diskPressure = Math.min(100, Math.round(systemMetrics.system.disk.used_percent * 0.7 + systemMetrics.system.disk.inode_used_percent * 0.3));
    const memoryPressure = Math.min(100, Math.round(systemMetrics.system.memory.used_percent));
    const cpuPressure = Math.min(100, Math.round(systemMetrics.system.cpu.load_percent_1m));

    const riskScore = Math.round((dbPressure * 0.35) + (diskPressure * 0.25) + (memoryPressure * 0.2) + (cpuPressure * 0.2));
    return { riskScore, dbPressure, diskPressure, memoryPressure };
  }, [systemMetrics]);

  const topTabs = NAV_GROUPS.flatMap((group) => group.items);

  const attentionItems = useMemo(() => {
    const items: string[] = [];
    const degradedServices = [
      getSeverity(systemMetrics?.system.cpu.load_percent_1m || 0, 70, 90),
      getSeverity(systemMetrics?.system.memory.used_percent || 0, 75, 90),
      getSeverity(systemMetrics?.database.probe_latency_ms || 0, 200, 500),
    ].filter((s) => s !== 'healthy').length;

    if (degradedServices > 0) items.push(`${degradedServices} services degraded`);
    if (visibleUsersSummary.blocked > 0) items.push(`${visibleUsersSummary.blocked} users blocked`);
    if ((systemMetrics?.database.probe_latency_ms || 0) >= 200) items.push('DB latency rising');
    if (logsSummary.server_errors > 0) items.push(`${logsSummary.server_errors} server errors`);

    return items.slice(0, 3);
  }, [systemMetrics, visibleUsersSummary.blocked, logsSummary.server_errors]);


  const handleLogout = async () => {
    await api.post('/auth/logout').catch(() => undefined);
    setUser(null);
  };

  if (!hasAnyRole(ADMIN_ROLES)) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-brand-main">
            <div className="admin-brand-mark">A</div>
            <div>
              <strong>{A('Админ-консоль', 'Admin Console', 'קונסולת ניהול')}</strong>
              <span>{A('Безопасное управление', 'Secure governance', 'ממשל מאובטח')}</span>
            </div>
          </div>

          <div className="admin-brand-user-shell" ref={userMenuRef}>
            <button
              type="button"
              className="admin-user-trigger admin-user-trigger-sidebar"
              onClick={() => setIsUserMenuOpen((prev) => !prev)}
              aria-expanded={isUserMenuOpen}
              aria-haspopup="menu"
            >
              <div className="admin-user-avatar" aria-hidden="true">
                {hasAvatarImage ? <img src={avatarUrl || undefined} alt="" onError={() => setAvatarLoadFailed(true)} /> : <span>{avatarInitials}</span>}
              </div>

              <div className="admin-user-meta">
                <div className="admin-sidebar-meta-title">{A('Оператор', 'Operator', 'מפעיל')}</div>
                <div className="admin-sidebar-meta-value">{currentUserDisplayName}</div>
                <div className="admin-user-meta-sub">{currentUserRole} • {currentUserStatus}</div>
              </div>

              <ChevronDown size={16} className={isUserMenuOpen ? "admin-user-chevron open" : "admin-user-chevron"} />
            </button>

            {isUserMenuOpen && (
              <div className="admin-user-menu" role="menu">
                <button type="button" className="admin-user-menu-item" onClick={openUserSettingsModal}>
                  <Settings size={15} />
                  Settings
                </button>
                <button type="button" className="admin-user-menu-item" onClick={jumpToMyPublications}>
                  <FileText size={15} />
                  My publications ({currentUserPosts})
                </button>
                <button type="button" className="admin-user-menu-item" onClick={openMySessions}>
                  <CircleUserRound size={15} />
                  My sessions
                </button>

                <div className="admin-user-menu-roles" aria-hidden="true">
                  {activeRoles.length === 0 && <Badge bg="secondary">{A('нет ролей', 'no roles', 'ללא תפקידים')}</Badge>}
                  {activeRoles.map((role) => (
                    <Badge key={role} bg="primary">{role}</Badge>
                  ))}
                </div>

                <button type="button" className="admin-user-menu-item danger" onClick={() => void handleLogout()}>
                  <LogOut size={15} />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="admin-nav-groups">
          {NAV_GROUPS.map((group) => {
            const isOpen = openNavGroups[group.id];

            return (
              <div className="admin-nav-group" key={group.id}>
                <button type="button" className="admin-nav-group-toggle" onClick={() => toggleNavGroup(group.id)}>
                  <span className="admin-nav-group-title">
                    {group.icon}
                    {group.title}
                  </span>
                  {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>

                {isOpen && (
                  <div className="admin-nav-items">
                    {group.items.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        className={`admin-nav-item ${activeSection === item.id ? 'active' : ''}`}
                        onClick={() => setActiveSection(item.id)}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <Button variant="outline-light" className="admin-sidebar-logout" onClick={() => void handleLogout()}>
          <LogOut size={15} className="me-2" />
          {A('Выход из админки', 'Exit admin', 'יציאה מניהול')}
        </Button>

      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <div className="admin-header-row admin-header-row-main">
            <div className="admin-topbar-title-block">
              <div className="admin-topbar-path">{sectionMeta.groupTitle} / {sectionMeta.sectionLabel}</div>
              <h1>{sectionGuide.title}</h1>
              <p>{sectionGuide.description}</p>
            </div>

            <div className="admin-topbar-actions" aria-label="Page actions">
              <UiPreferencesControls className="admin-prefs" />
              <Badge className="badge-soft">Users: {usersTotal}</Badge>
              <Badge className="badge-soft">Groups: {groups.length}</Badge>
              <Badge className="badge-soft">Publications: {publications.length}</Badge>
              <Badge className="badge-soft">Changes: {auditSummary.total}</Badge>
            </div>
          </div>

          <div className="admin-header-row admin-top-tabs" role="tablist" aria-label="Quick sections">
            {topTabs.map((item) => (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={activeSection === item.id}
                className={`admin-top-tab ${activeSection === item.id ? 'active' : ''}`}
                onClick={() => setActiveSection(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="admin-header-row admin-context-summary" aria-live="polite">
            <div className="admin-context-title">
              <Siren size={16} />
              {A('Что требует внимания сейчас', 'What needs attention now', 'מה דורש תשומת לב כעת')}
            </div>
            <div className="admin-context-items">
              {attentionItems.length === 0 ? (
                <span className="admin-context-item healthy"><CheckCircle2 size={14} />{A('Критичных сигналов нет', 'No critical signals', 'אין התראות קריטיות')}</span>
              ) : (
                attentionItems.map((item) => (
                  <span key={item} className="admin-context-item warning"><AlertTriangle size={14} />{item}</span>
                ))
              )}
            </div>
          </div>
        </header>

{(error || okMessage) && (
          <div className="admin-message-stack">
            {error && <Alert variant="danger" className="mb-0">{error}</Alert>}
            {okMessage && <Alert variant="success" className="mb-0">{okMessage}</Alert>}
          </div>
        )}

        {busy && (
          <div className="admin-progress">
            <Spinner animation="border" size="sm" />
            <span>{A('Обработка защищенного запроса...', 'Processing secured request...', 'מעבד בקשה מאובטחת...')}</span>
          </div>
        )}

        <Card className="admin-surface admin-section-helper mb-3">
          <Card.Body>
            <div className="admin-section-helper-title">{A('Назначение раздела', 'What this section is for', 'מטרת הסעיף')}</div>
            <div className="admin-section-helper-text">{sectionGuide.nextStep}</div>
          </Card.Body>
        </Card>

        <Card className="admin-surface admin-user-map mb-3">
          <Card.Body>
            <div className="admin-section-helper-title">{A('Быстрая карта профиля', 'Profile quick map', 'מפת פרופיל מהירה')}</div>
            <div className="admin-user-map-grid">
              <button type="button" className="admin-user-map-step" onClick={openUserSettingsModal}>
                <strong>1. Open Settings</strong>
                <span>Open your profile menu in the left top Admin Console block, then choose Settings.</span>
              </button>
              <button type="button" className="admin-user-map-step" onClick={jumpToMyPublications}>
                <strong>2. Manage my publications</strong>
                <span>Jump directly to your own publications and update moderation status.</span>
              </button>
              <button type="button" className="admin-user-map-step" onClick={openMySessions}>
                <strong>3. Check my sessions</strong>
                <span>Open active/revoked sessions to review security access.</span>
              </button>
            </div>
          </Card.Body>
        </Card>

        {activeSection === 'overview' && (
          <>
            <Row className="g-3 mb-4">
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">Users</div><div className="kpi-value">{usersTotal}</div><div className="kpi-sub">Active directory records</div></Card></Col>
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">Groups</div><div className="kpi-value">{groups.length}</div><div className="kpi-sub">RBAC groups / roles</div></Card></Col>
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">Publications</div><div className="kpi-value">{publications.length}</div><div className="kpi-sub">Draft + review + published</div></Card></Col>
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">Avg response</div><div className="kpi-value">{logsSummary.avg_response_ms} ms</div><div className="kpi-sub">From API telemetry stream</div></Card></Col>
            </Row>

            <Row className="g-3 mb-3">
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">Site uptime</div><div className="kpi-value">{systemMetrics?.site.uptime_human || '—'}</div><div className="kpi-sub">Application runtime</div></Card></Col>
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">CPU load</div><div className="kpi-value">{systemMetrics ? `${systemMetrics.system.cpu.load_percent_1m}%` : '—'}</div><div className="kpi-sub">1m normalized by cores</div></Card></Col>
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">Memory used</div><div className="kpi-value">{systemMetrics ? `${systemMetrics.system.memory.used_percent}%` : '—'}</div><div className="kpi-sub">Host memory usage</div></Card></Col>
              <Col md={6} xl={3}><Card body className="admin-kpi"><div className="kpi-title">DB latency</div><div className="kpi-value">{systemMetrics ? `${systemMetrics.database.probe_latency_ms} ms` : '—'}</div><div className="kpi-sub">SELECT 1 probe time</div></Card></Col>
            </Row>

            <Row className="g-3 mb-3">
              <Col lg={8}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">System state</h5>
                    <div className="admin-chart-list">
                      <div className="admin-chart-item">
                        <div className="admin-chart-head"><span>API success rate</span><strong>{logsHealth.successRate}%</strong></div>
                        <ProgressBar now={logsHealth.successRate} variant={logsHealth.successRate >= 95 ? 'success' : logsHealth.successRate >= 80 ? 'warning' : 'danger'} />
                      </div>
                      <div className="admin-chart-item">
                        <div className="admin-chart-head"><span>Platform health score</span><strong>{logsHealth.healthScore}/100</strong></div>
                        <ProgressBar now={logsHealth.healthScore} variant={logsHealth.healthScore >= 85 ? 'success' : logsHealth.healthScore >= 65 ? 'warning' : 'danger'} />
                      </div>
                      <div className="admin-chart-item">
                        <div className="admin-chart-head"><span>Published content ratio</span><strong>{publications.length > 0 ? Math.round((publicationSummary.published / publications.length) * 100) : 0}%</strong></div>
                        <ProgressBar now={publications.length > 0 ? Math.round((publicationSummary.published / publications.length) * 100) : 0} variant="info" />
                      </div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col lg={4}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Data footprint</h5>
                    <div className="admin-health-list">
                      <div><span><UsersRound size={15} /> Users (visible)</span><strong>{users.length}</strong></div>
                      <div><span><Shield size={15} /> Groups / roles</span><strong>{groups.length}</strong></div>
                      <div><span><ClipboardList size={15} /> Role catalog</span><strong>{catalogHierarchy.length}</strong></div>
                      <div><span><BookMarked size={15} /> Publications</span><strong>{publications.length}</strong></div>
                      <div><span><Activity size={15} /> Log events</span><strong>{logsSummary.total}</strong></div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            <Row className="g-3 mb-3">
              <Col xs={12}>
                <Card className="admin-surface">
                  <Card.Body>
                    <h5 className="mb-3">Admin map</h5>
                    <div className="admin-map-grid">
                      {NAV_GROUPS.map((group) => (
                        <div key={group.id} className="admin-map-item">
                          <strong>{group.title}</strong>
                          <div className="small text-secondary">{group.items.map((item) => item.label).join(' • ')}</div>
                        </div>
                      ))}
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            <Row className="g-3">
              <Col lg={8}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Recent API activity</h5>
                    <div className="table-responsive">
                      <Table hover className="admin-table">
                        <thead>
                          <tr>
                            <th>When</th>
                            <th>Method</th>
                            <th>Path</th>
                            <th>Status</th>
                            <th>User</th>
                            <th>Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {logs.slice(0, 8).map((item) => (
                            <tr key={item.id}>
                              <td>{formatDate(item.created_at)}</td>
                              <td><Badge bg="dark">{item.method}</Badge></td>
                              <td>{item.path}</td>
                              <td>{item.status_code}</td>
                              <td>{item.username || item.email || 'anonymous'}</td>
                              <td>{item.response_time_ms} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col lg={4}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Operational summary</h5>
                    <div className="admin-health-list">
                      <div><span><BadgeCheck size={15} /> Active users (visible)</span><strong>{visibleUsersSummary.active}</strong></div>
                      <div><span><Shield size={15} /> Blocked users (visible)</span><strong>{visibleUsersSummary.blocked}</strong></div>
                      <div><span><ClipboardList size={15} /> 4xx / 5xx errors</span><strong>{logsSummary.client_errors} / {logsSummary.server_errors}</strong></div>
                      <div><span><BookMarked size={15} /> Draft / review queue</span><strong>{publicationSummary.draft} / {publicationSummary.review}</strong></div>
                      <div><span><Activity size={15} /> Successful API calls</span><strong>{logsHealth.success}</strong></div>
                      <div><span><UsersRound size={15} /> Selected user</span><strong>{selectedUser?.username || 'none'}</strong></div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </>
        )}

        {activeSection === 'admin-map' && (
          <>
            <Row className="g-3 mb-3">
              <Col lg={8}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                      <h5 className="mb-0">Admin functional map</h5>
                      <Button variant="outline-light" size="sm" onClick={() => void withAction(loadInitial, 'Admin map refreshed')}>Refresh map data</Button>
                    </div>
                    <div className="table-responsive">
                      <Table hover className="admin-table">
                        <thead>
                          <tr>
                            <th>Section</th>
                            <th>Purpose</th>
                            <th>Actions</th>
                            <th>REST API</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ADMIN_SECTION_MAP.map((row) => (
                            <tr key={row.section}>
                              <td className="fw-semibold">{row.section}</td>
                              <td>{row.purpose}</td>
                              <td>{row.primaryActions}</td>
                              <td><code>{row.apiScope}</code></td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  </Card.Body>
                </Card>
              </Col>

              <Col lg={4}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Quick jump</h5>
                    <div className="admin-quick-action-grid">
                      <Button variant="outline-light" onClick={() => setActiveSection('user-directory')}>Users directory</Button>
                      <Button variant="outline-light" onClick={() => setActiveSection('user-create')}>Create user</Button>
                      <Button variant="outline-light" onClick={() => setActiveSection('groups-catalog')}>Groups catalog</Button>
                      <Button variant="outline-light" onClick={() => setActiveSection('group-assignments')}>Role assignments</Button>
                      <Button variant="outline-light" onClick={() => setActiveSection('publications-review')}>Publications queue</Button>
                      <Button variant="outline-light" onClick={() => setActiveSection('audit-trail')}>Change audit trail</Button>
                      <Button variant="outline-light" onClick={() => setActiveSection('audit-logs')}>API activity logs</Button>
                      <Button variant="primary" onClick={() => setActiveSection('system-monitoring')}>System monitoring</Button>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            <Row className="g-3">
              <Col lg={7}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Logging map</h5>
                    <div className="table-responsive">
                      <Table hover className="admin-table">
                        <thead>
                          <tr>
                            <th>Event type</th>
                            <th>Source</th>
                            <th>Where to inspect</th>
                          </tr>
                        </thead>
                        <tbody>
                          {LOGGING_EVENT_MAP.map((row) => (
                            <tr key={row.eventType}>
                              <td className="fw-semibold">{row.eventType}</td>
                              <td>{row.source}</td>
                              <td>{row.whereToCheck}</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  </Card.Body>
                </Card>
              </Col>

              <Col lg={5}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Live logging counters</h5>
                    <div className="admin-health-list">
                      <div><span>All change events</span><strong>{auditSummary.total}</strong></div>
                      <div><span>Success events</span><strong>{auditSummary.success}</strong></div>
                      <div><span>Blocked events</span><strong>{auditSummary.blocked}</strong></div>
                      <div><span>Error events</span><strong>{auditSummary.errors}</strong></div>
                      <div><span>Admin area changes</span><strong>{auditSummary.admin_actions}</strong></div>
                      <div><span>Site area changes</span><strong>{auditSummary.site_actions}</strong></div>
                      <div><span>Average mutation latency</span><strong>{auditSummary.avg_duration_ms} ms</strong></div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </>
        )}

        {activeSection === 'system-monitoring' && (
          <>
            <Card className="admin-surface mb-3">
              <Card.Body>
                <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                  <h5 className="mb-0">System and infrastructure telemetry</h5>
                  <Button variant="primary" onClick={() => void withAction(reloadSystemMetrics, 'System metrics refreshed')}>Refresh metrics</Button>
                </div>

                {!systemMetrics && <p className="text-secondary mb-0">Metrics are loading...</p>}

                {systemMetrics && (
                  <Row className="g-3">
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">Site uptime</div><div className="kpi-value">{systemMetrics.site.uptime_human}</div><div className="kpi-sub">PID: {systemMetrics.site.pid} • {systemMetrics.site.environment}</div></Card></Col>
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">CPU 1m</div><div className="kpi-value">{systemMetrics.system.cpu.load_percent_1m}%</div><div className="kpi-sub">{systemMetrics.system.cpu.cores} cores • proc {systemMetrics.system.cpu.process_cpu_percent}%</div></Card></Col>
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">Memory used</div><div className="kpi-value">{systemMetrics.system.memory.used_percent}%</div><div className="kpi-sub">{formatBytes(systemMetrics.system.memory.used_bytes)} / {formatBytes(systemMetrics.system.memory.total_bytes)}</div></Card></Col>
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">Disk used</div><div className="kpi-value">{systemMetrics.system.disk.used_percent}%</div><div className="kpi-sub">Inodes: {systemMetrics.system.disk.inode_used_percent}%</div></Card></Col>
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">DB size</div><div className="kpi-value">{formatBytes(systemMetrics.database.storage.database_size_bytes)}</div><div className="kpi-sub">{systemMetrics.database.storage.table_count} tables • {systemMetrics.database.storage.index_count} indexes</div></Card></Col>
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">Longest DB query</div><div className="kpi-value">{systemMetrics.database.max_active_query_age_seconds}s</div><div className="kpi-sub">Long-running: {systemMetrics.database.long_running_queries}</div></Card></Col>
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">Lock waiting queries</div><div className="kpi-value">{systemMetrics.database.lock_waiting_queries}</div><div className="kpi-sub">Waiting locks: {systemMetrics.database.waiting_locks}</div></Card></Col>
                    <Col md={6} xl={3}><Card body className="admin-surface-sub"><div className="kpi-title">Infra risk score</div><div className="kpi-value">{monitoringSignals.riskScore}/100</div><div className="kpi-sub">DB {monitoringSignals.dbPressure}% • Disk {monitoringSignals.diskPressure}%</div></Card></Col>
                  </Row>
                )}
              </Card.Body>
            </Card>

            {systemMetrics && (
              <>
                <Row className="g-3 mb-3">
                  <Col lg={8}>
                    <Card className="admin-surface h-100">
                      <Card.Body>
                        <h5 className="mb-3">Load and bottleneck signals</h5>
                        <div className="admin-chart-list">
                          <div className="admin-chart-item">
                            <div className="admin-chart-head"><span>CPU load (1m)</span><strong>{systemMetrics.system.cpu.load_percent_1m}%</strong></div>
                            <ProgressBar now={Math.min(systemMetrics.system.cpu.load_percent_1m, 100)} variant={systemMetrics.system.cpu.load_percent_1m >= 90 ? 'danger' : systemMetrics.system.cpu.load_percent_1m >= 70 ? 'warning' : 'success'} />
                          </div>
                          <div className="admin-chart-item">
                            <div className="admin-chart-head"><span>Memory usage</span><strong>{systemMetrics.system.memory.used_percent}%</strong></div>
                            <ProgressBar now={Math.min(systemMetrics.system.memory.used_percent, 100)} variant={systemMetrics.system.memory.used_percent >= 90 ? 'danger' : systemMetrics.system.memory.used_percent >= 75 ? 'warning' : 'success'} />
                          </div>
                          <div className="admin-chart-item">
                            <div className="admin-chart-head"><span>Disk usage</span><strong>{systemMetrics.system.disk.used_percent}%</strong></div>
                            <ProgressBar now={Math.min(systemMetrics.system.disk.used_percent, 100)} variant={systemMetrics.system.disk.used_percent >= 90 ? 'danger' : systemMetrics.system.disk.used_percent >= 75 ? 'warning' : 'success'} />
                          </div>
                          <div className="admin-chart-item">
                            <div className="admin-chart-head"><span>DB probe latency</span><strong>{systemMetrics.database.probe_latency_ms} ms</strong></div>
                            <ProgressBar now={Math.min((systemMetrics.database.probe_latency_ms / 800) * 100, 100)} variant={systemMetrics.database.probe_latency_ms >= 500 ? 'danger' : systemMetrics.database.probe_latency_ms >= 200 ? 'warning' : 'success'} />
                          </div>
                        </div>
                      </Card.Body>
                    </Card>
                  </Col>

                  <Col lg={4}>
                    <Card className="admin-surface h-100">
                      <Card.Body>
                        <h5 className="mb-3">Alerts</h5>
                        <div className="admin-alert-stack">
                          {systemMetrics.alerts.map((alert) => (
                            <Alert key={`${alert.code}-${alert.message}`} variant={alert.level === 'critical' ? 'danger' : alert.level === 'warn' ? 'warning' : 'success'} className="mb-0">
                              <div className="fw-semibold text-uppercase small">{alert.code}</div>
                              <div>{alert.message}</div>
                            </Alert>
                          ))}
                        </div>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>

                <Row className="g-3 mb-3">
                  <Col lg={6}>
                    <Card className="admin-surface h-100">
                      <Card.Body>
                        <h5 className="mb-3">Database health</h5>
                        <div className="admin-health-list">
                          <div><span>Status</span><strong>{systemMetrics.database.status}</strong></div>
                          <div><span>Active connections</span><strong>{systemMetrics.database.active_connections}</strong></div>
                          <div><span>Waiting locks</span><strong>{systemMetrics.database.waiting_locks}</strong></div>
                          <div><span>Lock waiting queries</span><strong>{systemMetrics.database.lock_waiting_queries}</strong></div>
                          <div><span>Long running queries</span><strong>{systemMetrics.database.long_running_queries}</strong></div>
                          <div><span>Longest active query</span><strong>{systemMetrics.database.max_active_query_age_seconds}s</strong></div>
                          <div><span>Cache hit ratio</span><strong>{systemMetrics.database.cache_hit_percent}%</strong></div>
                          <div><span>Deadlocks</span><strong>{systemMetrics.database.errors.deadlocks}</strong></div>
                        </div>
                      </Card.Body>
                    </Card>
                  </Col>

                  <Col lg={6}>
                    <Card className="admin-surface h-100">
                      <Card.Body>
                        <h5 className="mb-3">DB I/O and throughput</h5>
                        <div className="admin-health-list">
                          <div><span>Blocks read</span><strong>{systemMetrics.database.io.blocks_read}</strong></div>
                          <div><span>Blocks hit</span><strong>{systemMetrics.database.io.blocks_hit}</strong></div>
                          <div><span>Read time</span><strong>{systemMetrics.database.io.read_time_ms} ms</strong></div>
                          <div><span>Write time</span><strong>{systemMetrics.database.io.write_time_ms} ms</strong></div>
                          <div><span>Temp files</span><strong>{systemMetrics.database.io.temp_files}</strong></div>
                          <div><span>Temp bytes</span><strong>{formatBytes(systemMetrics.database.io.temp_bytes)}</strong></div>
                        </div>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>

                <Card className="admin-surface">
                  <Card.Body>
                    <h5 className="mb-3">Runtime and storage details</h5>
                    <div className="table-responsive">
                      <Table hover className="admin-table">
                        <tbody>
                          <tr><th>Collected at</th><td>{formatDate(systemMetrics.collected_at)}</td><th>Node</th><td>{systemMetrics.site.node_version}</td></tr>
                          <tr><th>Host</th><td>{systemMetrics.system.hostname}</td><th>Platform</th><td>{systemMetrics.system.platform} / {systemMetrics.system.arch} / {systemMetrics.system.release}</td></tr>
                          <tr><th>System uptime</th><td>{systemMetrics.system.uptime_human}</td><th>Site uptime</th><td>{systemMetrics.site.uptime_human}</td></tr>
                          <tr><th>Disk total</th><td>{formatBytes(systemMetrics.system.disk.total_bytes)}</td><th>Disk free</th><td>{formatBytes(systemMetrics.system.disk.free_bytes)}</td></tr>
                          <tr><th>Disk available</th><td>{formatBytes(systemMetrics.system.disk.available_bytes)}</td><th>Inodes used</th><td>{systemMetrics.system.disk.inode_used_percent}%</td></tr>
                          <tr><th>DB commits</th><td>{systemMetrics.database.transaction.commits}</td><th>DB rollbacks</th><td>{systemMetrics.database.transaction.rollbacks}</td></tr>
                          <tr><th>Rows returned</th><td>{systemMetrics.database.rows.returned}</td><th>Rows fetched</th><td>{systemMetrics.database.rows.fetched}</td></tr>
                          <tr><th>Rows inserted</th><td>{systemMetrics.database.rows.inserted}</td><th>Rows updated/deleted</th><td>{systemMetrics.database.rows.updated} / {systemMetrics.database.rows.deleted}</td></tr>
                          <tr><th>DB size</th><td>{formatBytes(systemMetrics.database.storage.database_size_bytes)}</td><th>Tables / indexes</th><td>{systemMetrics.database.storage.table_count} / {systemMetrics.database.storage.index_count}</td></tr>
                          <tr><th>Longest active query</th><td>{systemMetrics.database.max_active_query_age_seconds}s</td><th>Lock waiting queries</th><td>{systemMetrics.database.lock_waiting_queries}</td></tr>
                          <tr><th>Sessions by state</th><td colSpan={3}>{Object.entries(systemMetrics.database.sessions_by_state).map(([state, count]) => `${state}: ${count}`).join(' | ') || '—'}</td></tr>
                          <tr><th>Stats reset</th><td colSpan={3}>{formatDate(systemMetrics.database.stats_reset_at)}</td></tr>
                        </tbody>
                      </Table>
                    </div>
                  </Card.Body>
                </Card>
              </>
            )}
          </>
        )}

        {activeSection === 'user-directory' && (
          <>
            <Card className="admin-surface mb-3">
              <Card.Body>
                <Row className="g-3 align-items-center">
                  <Col lg={5}>
                    <InputGroup>
                      <InputGroup.Text>Search</InputGroup.Text>
                      <Form.Control value={search} onChange={(e) => setSearch(e.target.value)} placeholder="email / username / first / last" />
                    </InputGroup>
                  </Col>
                  <Col lg={4}>
                    <InputGroup>
                      <InputGroup.Text>User ID</InputGroup.Text>
                      <Form.Control value={userIdFilter} onChange={(e) => setUserIdFilter(e.target.value)} placeholder="exact UUID" />
                    </InputGroup>
                  </Col>
                  <Col lg={3} className="d-flex gap-2 justify-content-lg-end">
                    <Button variant="outline-light" onClick={() => setShowAdvancedUserFilters((prev) => !prev)}>
                      {showAdvancedUserFilters ? 'Hide filters' : 'Advanced filters'}
                    </Button>
                    <Button variant="primary" onClick={() => void withAction(reloadUsers, 'User search refreshed')}>Run Search</Button>
                  </Col>
                </Row>

                {showAdvancedUserFilters && (
                  <>
                    <hr className="admin-soft-separator" />
                    <Row className="g-3 mb-3">
                      <Col lg={2}>
                        <Form.Select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
                          <option value="">Legacy role</option>
                          <option value="user">user</option>
                          <option value="admin">admin</option>
                          <option value="moderator">moderator</option>
                        </Form.Select>
                      </Col>
                      <Col lg={2}>
                        <Form.Select value={rbacRoleFilter} onChange={(e) => setRbacRoleFilter(e.target.value)}>
                          <option value="">RBAC role</option>
                          {SEARCHABLE_RBAC_ROLES.map((role) => <option key={role} value={role}>{role}</option>)}
                        </Form.Select>
                      </Col>
                      <Col lg={3}>
                        <InputGroup>
                          <InputGroup.Text>Permission</InputGroup.Text>
                          <Form.Control value={permissionFilter} onChange={(e) => setPermissionFilter(e.target.value)} placeholder="users.read.any" />
                        </InputGroup>
                      </Col>
                      <Col lg={2}>
                        <Form.Select value={publicationStatusFilter} onChange={(e) => setPublicationStatusFilter(e.target.value)}>
                          <option value="">Pub status</option>
                          <option value="draft">draft</option>
                          <option value="review">review</option>
                          <option value="published">published</option>
                          <option value="archived">archived</option>
                        </Form.Select>
                      </Col>
                      <Col lg={3}>
                        <InputGroup>
                          <InputGroup.Text>Pub search</InputGroup.Text>
                          <Form.Control value={publicationSearchFilter} onChange={(e) => setPublicationSearchFilter(e.target.value)} placeholder="publication title / description" />
                        </InputGroup>
                      </Col>
                    </Row>

                    <Row className="g-3 align-items-center">
                      <Col lg={2}>
                        <Form.Select value={hasPublicationsFilter} onChange={(e) => setHasPublicationsFilter(e.target.value as 'all' | 'yes' | 'no')}>
                          <option value="all">Any publication count</option>
                          <option value="yes">Has publications</option>
                          <option value="no">No publications</option>
                        </Form.Select>
                      </Col>
                      <Col lg={2}>
                        <Form.Select value={blockedFilter} onChange={(e) => setBlockedFilter(e.target.value as 'all' | 'blocked' | 'active')}>
                          <option value="all">Block state</option>
                          <option value="blocked">Blocked</option>
                          <option value="active">Not blocked</option>
                        </Form.Select>
                      </Col>
                      <Col lg={3}>
                        <Form.Select value={sortBy} onChange={(e) => setSortBy(e.target.value as NonNullable<AdminUsersListParams['sortBy']>)}>
                          {USER_SORT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                        </Form.Select>
                      </Col>
                      <Col lg={2}>
                        <Form.Select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}>
                          <option value="desc">Descending</option>
                          <option value="asc">Ascending</option>
                        </Form.Select>
                      </Col>
                      <Col lg={3}>
                        <Form.Check checked={includeDeleted} onChange={(e) => setIncludeDeleted(e.target.checked)} label="Include deleted" />
                      </Col>
                    </Row>
                  </>
                )}
              </Card.Body>
            </Card>

            <Card className="admin-surface">
              <Card.Body>
                <div className="table-responsive">
                  <Table hover className="admin-table">
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Legacy</th>
                        <th>RBAC Roles</th>
                        <th>Perms</th>
                        <th>Pubs</th>
                        <th>Last Login</th>
                        <th>Status</th>
                        <th className="text-end">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((item) => (
                        <tr key={item.id}>
                          <td>
                            <div className="fw-semibold">{item.username}</div>
                            <div className="text-secondary small">{item.email}</div>
                            <div className="text-secondary small">{item.id}</div>
                          </td>
                          <td>{item.role}</td>
                          <td>{item.rbac_roles?.join(', ') || '—'}</td>
                          <td>{item.permission_count ?? 0}</td>
                          <td>
                            {item.publication_count ?? 0}
                            <span className="text-secondary small"> / published: {item.published_publication_count ?? 0}</span>
                          </td>
                          <td>{formatDate(item.last_login)}</td>
                          <td>
                            <div className="d-flex flex-column gap-1">
                              {item.deleted_at ? <Badge bg="danger">Deleted</Badge> : <Badge bg="success">Active</Badge>}
                              {item.is_system_blocked ? <Badge bg="warning">Blocked</Badge> : <Badge bg="info">Open</Badge>}
                            </div>
                          </td>
                          <td className="text-end">
                            <Button size="sm" variant="outline-light" className="me-2" onClick={() => { setSelectedUser(item); void loadAssignments(item.id); setActiveSection('group-assignments'); }}>Access</Button>
                            <Button size="sm" variant="outline-light" className="me-2" onClick={() => void loadSessions(item.id)}>Sessions</Button>
                            {hasPermission(user, 'users.permissions.manage') && canEditUserPermissions(user, item) && (
                              <Link className="btn btn-sm btn-outline-primary me-2" to={'/admin/users/' + item.id + '/permissions'}>
                                Редактировать права
                              </Link>
                            )}
                            {!item.deleted_at && <Button size="sm" variant="outline-danger" onClick={() => void softDeleteUser(item.id)}>Delete</Button>}
                            {item.deleted_at && <Button size="sm" variant="outline-success" onClick={() => void restoreUser(item.id)}>Restore</Button>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>

                {selectedUser && (
                  <Card className="admin-surface-sub mt-3">
                    <Card.Body>
                      <h6 className="mb-3">Edit User: {selectedUser.username}</h6>
                      <Row className="g-3">
                        <Col md={4}><Form.Control value={selectedUser.first_name || ''} placeholder="First name" onChange={(e) => setSelectedUser({ ...selectedUser, first_name: e.target.value })} /></Col>
                        <Col md={4}><Form.Control value={selectedUser.last_name || ''} placeholder="Last name" onChange={(e) => setSelectedUser({ ...selectedUser, last_name: e.target.value })} /></Col>
                        <Col md={4}><Form.Control value={selectedUser.email} placeholder="Email" onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })} /></Col>
                        <Col md={4}><Form.Control value={selectedUser.username} placeholder="Username" onChange={(e) => setSelectedUser({ ...selectedUser, username: e.target.value })} /></Col>
                        <Col md={4}><Form.Control type="number" value={selectedUser.xp_total} placeholder="XP" onChange={(e) => setSelectedUser({ ...selectedUser, xp_total: Number.parseInt(e.target.value || '0', 10) })} /></Col>
                        <Col md={4}><Form.Control type="number" value={selectedUser.level} placeholder="Level" onChange={(e) => setSelectedUser({ ...selectedUser, level: Number.parseInt(e.target.value || '1', 10) })} /></Col>
                      </Row>
                      <div className="mt-3 text-end">
                        <Button onClick={() => void updateUser(selectedUser)}>Save User</Button>
                      </div>
                    </Card.Body>
                  </Card>
                )}
              </Card.Body>
            </Card>
          </>
        )}

        {activeSection === 'user-create' && (
          <Card className="admin-surface">
            <Card.Body>
              <h5 className="mb-3"><UserPlus size={18} className="me-2" />Create new user</h5>
              <Row className="g-3">
                <Col md={6}><Form.Control value={createUserForm.email} placeholder="Email" onChange={(e) => setCreateUserForm({ ...createUserForm, email: e.target.value })} /></Col>
                <Col md={6}><Form.Control value={createUserForm.username} placeholder="Username" onChange={(e) => setCreateUserForm({ ...createUserForm, username: e.target.value })} /></Col>
                <Col md={6}><Form.Control value={createUserForm.first_name || ''} placeholder="First name" onChange={(e) => setCreateUserForm({ ...createUserForm, first_name: e.target.value })} /></Col>
                <Col md={6}><Form.Control value={createUserForm.last_name || ''} placeholder="Last name" onChange={(e) => setCreateUserForm({ ...createUserForm, last_name: e.target.value })} /></Col>
                <Col md={12}>
                  <InputGroup>
                    <InputGroup.Text><Lock size={14} /></InputGroup.Text>
                    <Form.Control type="password" value={createUserForm.password} placeholder="Temporary password (strong)" onChange={(e) => setCreateUserForm({ ...createUserForm, password: e.target.value })} />
                  </InputGroup>
                </Col>
              </Row>
              <div className="mt-3 d-flex justify-content-end">
                <Button onClick={() => void createUser()}>Create User</Button>
              </div>
            </Card.Body>
          </Card>
        )}

        {activeSection === 'groups-catalog' && (
          <Row className="g-3">
            <Col lg={4}>
              <Card className="admin-surface h-100">
                <Card.Body>
                  <h5 className="mb-3">Groups catalog</h5>
                  <div className="admin-group-list">
                    {groups.map((group) => (
                      <button
                        key={group.role_key}
                        type="button"
                        className={`admin-group-item ${selectedGroupKey === group.role_key ? 'active' : ''}`}
                        onClick={() => {
                          setSelectedGroupKey(group.role_key);
                          setGroupPermissionDraft(rolePermissionMap[group.role_key] || []);
                          setGroupForm({
                            roleKey: group.role_key,
                            title: group.title,
                            description: group.description || '',
                            priority: group.priority,
                          });
                        }}
                      >
                        <div>
                          <strong>{group.title}</strong>
                          <div className="small text-secondary">{group.role_key}</div>
                        </div>
                        <div className="small text-end">
                          <div>{group.permissions_count} perms</div>
                          <div>{group.assignments_count} users</div>
                        </div>
                      </button>
                    ))}
                  </div>
                </Card.Body>
              </Card>
            </Col>

            <Col lg={8}>
              <Card className="admin-surface mb-3">
                <Card.Body>
                  <h5 className="mb-3">Create / edit group</h5>
                  <Row className="g-3">
                    <Col md={4}><Form.Control value={groupForm.roleKey} placeholder="group_key" onChange={(e) => setGroupForm({ ...groupForm, roleKey: normalizeRoleKey(e.target.value) })} /></Col>
                    <Col md={5}><Form.Control value={groupForm.title} placeholder="Group title" onChange={(e) => setGroupForm({ ...groupForm, title: e.target.value })} /></Col>
                    <Col md={3}><Form.Control type="number" value={groupForm.priority} placeholder="Priority" onChange={(e) => setGroupForm({ ...groupForm, priority: Number.parseInt(e.target.value || '100', 10) })} /></Col>
                    <Col xs={12}><Form.Control as="textarea" rows={2} value={groupForm.description} placeholder="Description" onChange={(e) => setGroupForm({ ...groupForm, description: e.target.value })} /></Col>
                  </Row>

                  <div className="mt-3 d-flex gap-2 justify-content-end flex-wrap">
                    <Button variant="outline-light" onClick={() => void createGroup()}>Create Group</Button>
                    <Button variant="warning" disabled={!selectedGroup || selectedGroup.is_system} onClick={() => void updateGroup()}>Edit Group</Button>
                    <Button variant="danger" disabled={!selectedGroup || selectedGroup.is_system} onClick={() => void deleteGroup()}>Delete Group</Button>
                  </div>
                </Card.Body>
              </Card>

              <Card className="admin-surface">
                <Card.Body>
                  <h5 className="mb-3">Group permissions</h5>
                  {!selectedGroup && <p className="text-secondary mb-0">Select group on the left to manage permissions.</p>}
                  {selectedGroup && (
                    <>
                      <div className="admin-permissions-grid">
                        {catalogPermissions.map((permission) => (
                          <label key={permission.permission_name} className="admin-permission-item">
                            <input
                              type="checkbox"
                              checked={groupPermissionDraft.includes(permission.permission_name)}
                              onChange={() => togglePermission(permission.permission_name)}
                              disabled={selectedGroup.is_system}
                            />
                            <span>
                              <strong>{permission.permission_name}</strong>
                              <small>{permission.resource}.{permission.action}.{permission.scope}</small>
                            </span>
                          </label>
                        ))}
                      </div>
                      <div className="mt-3 text-end">
                        <Button disabled={selectedGroup.is_system} onClick={() => void saveGroupPermissions()}>Save Permissions</Button>
                      </div>
                    </>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {activeSection === 'group-assignments' && (
          <Card className="admin-surface">
            <Card.Body>
              <h5 className="mb-3">User role assignments</h5>
              {!selectedUser && <p className="text-secondary">Choose user in "Users → Directory" first.</p>}

              {selectedUser && (
                <>
                  <div className="mb-3">
                    <strong>{selectedUser.username}</strong>
                    <span className="text-secondary ms-2">{selectedUser.email}</span>
                  </div>

                  <Row className="g-3 mb-3">
                    <Col md={6}>
                      <Form.Select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value as RoleKey)}>
                        {groups.map((group) => <option key={group.role_key} value={group.role_key}>{group.role_key}</option>)}
                      </Form.Select>
                    </Col>
                    <Col md={6}><Form.Control value={assignmentNote} onChange={(e) => setAssignmentNote(e.target.value)} placeholder="Audit note" /></Col>
                  </Row>

                  <div className="d-flex gap-2 justify-content-end flex-wrap mb-3">
                    <Button variant="outline-light" onClick={() => void loadAssignments(selectedUser.id)}>Refresh</Button>
                    <Button variant="success" onClick={() => void assignRole()}>Assign Role</Button>
                    <Button variant="warning" onClick={() => void revokeRole()}>Revoke Role</Button>
                    <Button variant="danger" onClick={() => void toggleBlockState(true)}>Block</Button>
                    <Button variant="outline-success" onClick={() => void toggleBlockState(false)}>Unblock</Button>
                  </div>

                  <div className="table-responsive">
                    <Table hover className="admin-table">
                      <thead>
                        <tr>
                          <th>Role</th>
                          <th>Priority</th>
                          <th>Active</th>
                          <th>Assigned</th>
                          <th>Expires</th>
                          <th>Note</th>
                        </tr>
                      </thead>
                      <tbody>
                        {userAssignments.map((assignment) => (
                          <tr key={assignment.id}>
                            <td>{assignment.role_key}</td>
                            <td>{assignment.priority}</td>
                            <td>{assignment.is_active ? 'yes' : 'no'}</td>
                            <td>{formatDate(assignment.assigned_at)}</td>
                            <td>{formatDate(assignment.expires_at)}</td>
                            <td>{assignment.note || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                </>
              )}
            </Card.Body>
          </Card>
        )}

        {activeSection === 'publications-review' && (
          <>
            <Row className="g-3 mb-3">
              <Col lg={8}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                    <h5 className="mb-0">Create publication</h5>
                    <div className="d-flex gap-2">
                      <Button size="sm" variant={publicationOwnerFilter === 'all' ? 'primary' : 'outline-light'} onClick={() => setPublicationOwnerFilter('all')}>All publications</Button>
                      <Button size="sm" variant={publicationOwnerFilter === 'mine' ? 'primary' : 'outline-light'} onClick={() => setPublicationOwnerFilter('mine')}>My publications</Button>
                    </div>
                  </div>
                    <Row className="g-3">
                      <Col md={6}><Form.Control value={publicationForm.title} placeholder="Title" onChange={(e) => setPublicationForm({ ...publicationForm, title: e.target.value })} /></Col>
                      <Col md={3}>
                        <Form.Select value={publicationForm.status} onChange={(e) => setPublicationForm({ ...publicationForm, status: e.target.value })}>
                          <option value="draft">draft</option>
                          <option value="review">review</option>
                          <option value="published">published</option>
                          <option value="archived">archived</option>
                        </Form.Select>
                      </Col>
                      <Col md={3}>
                        <Form.Select value={publicationForm.visibility} onChange={(e) => setPublicationForm({ ...publicationForm, visibility: e.target.value as 'private' | 'team' | 'public' })}>
                          <option value="private">private</option>
                          <option value="team">team</option>
                          <option value="public">public</option>
                        </Form.Select>
                      </Col>
                      <Col xs={12}><Form.Control value={publicationForm.tags} placeholder="Tags (comma-separated)" onChange={(e) => setPublicationForm({ ...publicationForm, tags: e.target.value })} /></Col>
                      <Col xs={12}><Form.Control as="textarea" rows={3} value={publicationForm.description} placeholder="Description" onChange={(e) => setPublicationForm({ ...publicationForm, description: e.target.value })} /></Col>
                    </Row>
                    <div className="mt-3 text-end">
                      <Button onClick={() => void createPublication()}>Create Publication</Button>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col lg={4}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Moderation actions</h5>
                    <ul className="admin-feature-list">
                      <li>Queue drafts and review-ready entries.</li>
                      <li>Approve and publish from one click.</li>
                      <li>Archive outdated entries quickly.</li>
                      <li>Delete low-quality or invalid publications.</li>
                    </ul>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            <Card className="admin-surface">
              <Card.Body>
                <div className="table-responsive">
                  <Table hover className="admin-table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Status</th>
                        <th>Visibility</th>
                        <th>Updated</th>
                        <th className="text-end">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visiblePublications.map((publication) => (
                        <tr key={publication.id}>
                          <td>
                            <div className="fw-semibold">{publication.name}</div>
                            <div className="small text-secondary">{publication.description || 'No description'}</div>
                          </td>
                          <td>{publication.metadata?.authorId || '—'}</td>
                          <td><Badge bg={statusVariant(publication.metadata?.status)}>{publication.metadata?.status || 'draft'}</Badge></td>
                          <td>{publication.metadata?.visibility || 'private'}</td>
                          <td>{formatDate(publication.updated_at)}</td>
                          <td className="text-end">
                            <Button size="sm" variant="outline-light" className="me-2" onClick={() => void updatePublicationStatus(publication.id, 'review')}>To Review</Button>
                            <Button size="sm" variant="outline-success" className="me-2" onClick={() => void updatePublicationStatus(publication.id, 'published')}>Approve</Button>
                            <Button size="sm" variant="outline-secondary" className="me-2" onClick={() => void updatePublicationStatus(publication.id, 'archived')}>Archive</Button>
                            <Button size="sm" variant="outline-danger" onClick={() => void deletePublication(publication.id)}>Delete</Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              </Card.Body>
            </Card>
          </>
        )}

        {activeSection === 'audit-trail' && (
          <>
            <Card className="admin-surface mb-3">
              <Card.Body>
                <Row className="g-3 align-items-end">
                  <Col md={2}>
                    <Form.Label>Area</Form.Label>
                    <Form.Select value={auditArea} onChange={(e) => setAuditArea(e.target.value)}>
                      <option value="">Any</option>
                      <option value="admin">admin</option>
                      <option value="site">site</option>
                      <option value="auth">auth</option>
                    </Form.Select>
                  </Col>
                  <Col md={2}>
                    <Form.Label>Outcome</Form.Label>
                    <Form.Select value={auditOutcome} onChange={(e) => setAuditOutcome(e.target.value)}>
                      <option value="">Any</option>
                      <option value="success">success</option>
                      <option value="blocked">blocked</option>
                      <option value="error">error</option>
                    </Form.Select>
                  </Col>
                  <Col md={2}>
                    <Form.Label>Resource</Form.Label>
                    <Form.Control value={auditResource} onChange={(e) => setAuditResource(e.target.value)} placeholder="users / access / publications" />
                  </Col>
                  <Col md={2}>
                    <Form.Label>Action</Form.Label>
                    <Form.Control value={auditAction} onChange={(e) => setAuditAction(e.target.value)} placeholder="create / update / delete" />
                  </Col>
                  <Col md={3}>
                    <Form.Label>Path</Form.Label>
                    <Form.Control value={auditPath} onChange={(e) => setAuditPath(e.target.value)} placeholder="/api/admin/users" />
                  </Col>
                  <Col md={1} className="text-md-end">
                    <Button variant="primary" onClick={() => void withAction(reloadAuditEvents, 'Audit trail refreshed')}>Run</Button>
                  </Col>
                </Row>
              </Card.Body>
            </Card>

            <Row className="g-3 mb-3">
              <Col md={4}><Card body className="admin-kpi"><div className="kpi-title">Total changes</div><div className="kpi-value">{auditSummary.total}</div></Card></Col>
              <Col md={4}><Card body className="admin-kpi"><div className="kpi-title">Success / blocked / errors</div><div className="kpi-value">{auditSummary.success} / {auditSummary.blocked} / {auditSummary.errors}</div></Card></Col>
              <Col md={4}><Card body className="admin-kpi"><div className="kpi-title">Avg action time</div><div className="kpi-value">{auditSummary.avg_duration_ms} ms</div></Card></Col>
            </Row>

            <Row className="g-3 mb-3">
              <Col lg={8}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Audit trail: who changed what</h5>
                    <div className="table-responsive">
                      <Table hover className="admin-table">
                        <thead>
                          <tr>
                            <th>When</th>
                            <th>Actor</th>
                            <th>Area</th>
                            <th>Resource / action</th>
                            <th>Target</th>
                            <th>Status</th>
                            <th>Where</th>
                            <th>Time</th>
                          </tr>
                        </thead>
                        <tbody>
                          {auditEvents.map((event) => (
                            <tr key={event.id}>
                              <td>{formatDate(event.created_at)}</td>
                              <td>{event.username || event.email || event.actor_user_id || 'anonymous'}</td>
                              <td>{event.area}</td>
                              <td>
                                <div className="fw-semibold">{event.resource}.{event.action}</div>
                                <div className="small text-secondary">{event.method}</div>
                              </td>
                              <td>{event.target_type || '—'} {event.target_id ? `#${event.target_id}` : ''}</td>
                              <td>
                                <Badge bg={event.outcome === 'success' ? 'success' : event.outcome === 'blocked' ? 'warning' : 'danger'}>{event.outcome}</Badge>
                                <div className="small text-secondary">HTTP {event.status_code}</div>
                              </td>
                              <td>
                                <div>{event.path}</div>
                                <div className="small text-secondary">{event.ip_address || '—'}</div>
                              </td>
                              <td>{event.duration_ms} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  </Card.Body>
                </Card>
              </Col>

              <Col lg={4}>
                <Card className="admin-surface h-100">
                  <Card.Body>
                    <h5 className="mb-3">Logging map (last 24h)</h5>
                    <div className="admin-map-grid">
                      {auditMap.slice(0, 30).map((item) => (
                        <div key={`${item.area}-${item.resource}-${item.action}`} className="admin-map-item">
                          <strong>{item.area} / {item.resource}.{item.action}</strong>
                          <div className="small text-secondary">events: {item.total} • non-success: {item.non_success}</div>
                        </div>
                      ))}
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </>
        )}

        {activeSection === 'audit-logs' && (
          <>
            <Card className="admin-surface mb-3">
              <Card.Body>
                <Row className="g-3 align-items-end mb-2">
                  <Col md={2}>
                    <Form.Label>Method</Form.Label>
                    <Form.Select value={logMethod} onChange={(e) => setLogMethod(e.target.value)}>
                      <option value="">Any</option>
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="PATCH">PATCH</option>
                      <option value="DELETE">DELETE</option>
                    </Form.Select>
                  </Col>
                  <Col md={2}>
                    <Form.Label>Area</Form.Label>
                    <Form.Select value={logArea} onChange={(e) => setLogArea(e.target.value)}>
                      <option value="">Any</option>
                      <option value="site">site</option>
                      <option value="auth">auth</option>
                      <option value="admin">admin</option>
                    </Form.Select>
                  </Col>
                  <Col md={2}>
                    <Form.Label>Outcome</Form.Label>
                    <Form.Select value={logOutcome} onChange={(e) => setLogOutcome(e.target.value)}>
                      <option value="">Any</option>
                      <option value="success">success</option>
                      <option value="blocked">blocked</option>
                      <option value="error">error</option>
                    </Form.Select>
                  </Col>
                  <Col md={4}>
                    <Form.Label>Path contains</Form.Label>
                    <Form.Control value={logPath} onChange={(e) => setLogPath(e.target.value)} placeholder="/api/admin/users" />
                  </Col>
                  <Col md={1}>
                    <Form.Label>Status</Form.Label>
                    <Form.Control value={logStatusCode} onChange={(e) => setLogStatusCode(e.target.value)} placeholder="200" />
                  </Col>
                  <Col md={1} className="text-md-end">
                    <Button variant="outline-light" onClick={() => void withAction(reloadLogs, 'Logs refreshed')}>Run</Button>
                  </Col>
                </Row>

                <Row className="g-3 align-items-end">
                  <Col md={6}>
                    <Form.Label>Login / email contains</Form.Label>
                    <Form.Control value={logLoginIdentifier} onChange={(e) => setLogLoginIdentifier(e.target.value)} placeholder="user@example.com" />
                  </Col>
                </Row>
              </Card.Body>
            </Card>

            <Row className="g-3 mb-3">
              <Col md={3}><Card body className="admin-kpi"><div className="kpi-title">Total events</div><div className="kpi-value">{logsSummary.total}</div></Card></Col>
              <Col md={3}><Card body className="admin-kpi"><div className="kpi-title">Success / blocked / errors</div><div className="kpi-value">{logsSummary.success || 0} / {logsSummary.blocked || 0} / {logsSummary.errors || 0}</div></Card></Col>
              <Col md={3}><Card body className="admin-kpi"><div className="kpi-title">Auth sessions</div><div className="kpi-value">{logsSummary.authenticated || 0}</div><div className="kpi-sub">Locked accounts: {logsSummary.locked_accounts || 0}</div></Card></Col>
              <Col md={3}><Card body className="admin-kpi"><div className="kpi-title">Average API latency</div><div className="kpi-value">{logsSummary.avg_response_ms} ms</div><div className="kpi-sub">4xx / 5xx: {logsSummary.client_errors} / {logsSummary.server_errors}</div></Card></Col>
            </Row>

            <Card className="admin-surface">
              <Card.Body>
                <div className="table-responsive">
                  <Table hover className="admin-table">
                    <thead>
                      <tr>
                        <th>When</th>
                        <th>User</th>
                        <th>Scope</th>
                        <th>Method / Path</th>
                        <th>Outcome</th>
                        <th>User state</th>
                        <th>IP</th>
                        <th>Latency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((item) => (
                        <tr key={item.id}>
                          <td>{formatDate(item.created_at)}</td>
                          <td>
                            <div className="fw-semibold">{item.username || item.email || item.login_identifier || 'anonymous'}</div>
                            <div className="small text-secondary">{item.user_id || 'no user id'}</div>
                          </td>
                          <td>
                            <div className="fw-semibold">{item.area || 'site'}</div>
                            <div className="small text-secondary">{item.resource || 'unknown'}.{item.action || 'request'}</div>
                          </td>
                          <td>
                            <Badge bg="dark">{item.method}</Badge>
                            <div className="small text-secondary mt-1">{item.path}</div>
                          </td>
                          <td>
                            <Badge bg={item.outcome === 'success' ? 'success' : item.outcome === 'blocked' ? 'warning' : 'danger'}>{item.outcome || 'unknown'}</Badge>
                            <div className="small text-secondary">HTTP {item.status_code}</div>
                          </td>
                          <td>
                            <div className="small">role: {item.highest_role || item.user_role || '—'}</div>
                            <div className="small text-secondary">prev login: {item.had_previous_login ? 'yes' : 'no'} | locked: {item.account_locked ? 'yes' : 'no'}</div>
                          </td>
                          <td>{item.ip_address || '—'}</td>
                          <td>{item.response_time_ms} ms</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              </Card.Body>
            </Card>
          </>
        )}

        {showUserSettingsModal && (
          <div
            className="admin-user-modal-overlay"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) {
                setShowUserSettingsModal(false);
              }
            }}
          >
            <div className="admin-user-modal-window" role="dialog" aria-modal="true" aria-label="User settings">
              <button type="button" className="admin-user-modal-close" onClick={() => setShowUserSettingsModal(false)} aria-label="Close settings">
                <X size={16} />
              </button>

              <div className="admin-user-modal-head">
                <h5 className="mb-1">User settings</h5>
                <p className="mb-0">Profile management, security and account summary.</p>
              </div>

              <div className="admin-user-modal-tabs">
                <button type="button" className={selectedUserTab === "profile" ? "active" : ""} onClick={() => setSelectedUserTab("profile")}>
                  <Settings size={15} />
                  Profile
                </button>
                <button type="button" className={selectedUserTab === "security" ? "active" : ""} onClick={() => setSelectedUserTab("security")}>
                  <KeyRound size={15} />
                  Security
                </button>
              </div>

              {selectedUserTab === "profile" && (
                <div className="admin-user-modal-content">
                  <div className="admin-user-modal-avatar-block">
                    <div className="admin-user-avatar large">
                      {hasAvatarImage ? <img src={avatarUrl || undefined} alt="" onError={() => setAvatarLoadFailed(true)} /> : <span>{avatarInitials}</span>}
                    </div>
                    <div className="admin-user-avatar-actions">
                      <Form.Control type="file" accept="image/png,image/jpeg,image/webp" onChange={handleAvatarUpload} />
                      <div className="admin-user-avatar-rules">Allowed: PNG, JPG, WEBP • Max 2 MB</div>
                      <Button size="sm" variant="outline-danger" onClick={() => void clearAvatar()}>Remove avatar</Button>
                    </div>
                  </div>

                  <Row className="g-3">
                    <Col md={6}>
                      <Form.Label>Nickname</Form.Label>
                      <Form.Control value={profileDraft.username} onChange={(event) => setProfileDraft((prev) => ({ ...prev, username: event.target.value }))} />
                    </Col>
                    <Col md={6}>
                      <Form.Label>Email</Form.Label>
                      <Form.Control type="email" value={profileDraft.email} onChange={(event) => setProfileDraft((prev) => ({ ...prev, email: event.target.value }))} />
                    </Col>
                    <Col md={6}>
                      <Form.Label>First name</Form.Label>
                      <Form.Control value={profileDraft.first_name} onChange={(event) => setProfileDraft((prev) => ({ ...prev, first_name: event.target.value }))} />
                    </Col>
                    <Col md={6}>
                      <Form.Label>Last name</Form.Label>
                      <Form.Control value={profileDraft.last_name} onChange={(event) => setProfileDraft((prev) => ({ ...prev, last_name: event.target.value }))} />
                    </Col>
                  </Row>

                  <div className="admin-user-modal-summary">
                    <div><span>Posts</span><strong>{currentUserPosts}</strong></div>
                    <div><span>Role</span><strong>{currentUserRole}</strong></div>
                    <div><span>Status</span><strong>{currentUserStatus}</strong></div>
                    <div><span>Last login</span><strong>{formatDate(user?.last_login)}</strong></div>
                  </div>

                  <div className="admin-user-modal-footer">
                    <Button variant="primary" onClick={() => void saveProfileSettings()}>Save profile</Button>
                  </div>
                </div>
              )}

              {selectedUserTab === "security" && (
                <div className="admin-user-modal-content">
                  <Row className="g-3">
                    <Col xs={12}>
                      <Form.Label>Current password</Form.Label>
                      <Form.Control type="password" value={passwordDraft.currentPassword} onChange={(event) => setPasswordDraft((prev) => ({ ...prev, currentPassword: event.target.value }))} />
                    </Col>
                    <Col md={6}>
                      <Form.Label>New password</Form.Label>
                      <Form.Control type="password" value={passwordDraft.newPassword} onChange={(event) => setPasswordDraft((prev) => ({ ...prev, newPassword: event.target.value }))} />
                    </Col>
                    <Col md={6}>
                      <Form.Label>Confirm new password</Form.Label>
                      <Form.Control type="password" value={passwordDraft.confirmPassword} onChange={(event) => setPasswordDraft((prev) => ({ ...prev, confirmPassword: event.target.value }))} />
                    </Col>
                  </Row>

                  <div className="admin-user-modal-summary">
                    <div><span>User ID</span><strong>{user?.id || "-"}</strong></div>
                    <div><span>Nickname</span><strong>{profileDraft.username || "-"}</strong></div>
                    <div><span>Role</span><strong>{currentUserRole}</strong></div>
                    <div><span>Status</span><strong>{currentUserStatus}</strong></div>
                  </div>

                  <div className="admin-user-modal-footer">
                    <Button variant="primary" onClick={() => void savePasswordSettings()}>Change password</Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <Modal show={showSessionsModal} onHide={() => setShowSessionsModal(false)} size="lg" centered>
          <Modal.Header closeButton>
            <Modal.Title>User Sessions</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Table size="sm" striped>
              <thead>
                <tr>
                  <th>Created</th>
                  <th>Last Seen</th>
                  <th>IP</th>
                  <th>User Agent</th>
                  <th>Revoked</th>
                </tr>
              </thead>
              <tbody>
                {selectedUserSessions.map((session) => (
                  <tr key={session.id}>
                    <td>{formatDate(session.created_at)}</td>
                    <td>{formatDate(session.last_seen_at)}</td>
                    <td>{session.ip_address || '—'}</td>
                    <td>{session.user_agent || '—'}</td>
                    <td>{session.revoked_at ? 'yes' : 'no'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Modal.Body>
        </Modal>
      </main>
    </div>
  );
}
