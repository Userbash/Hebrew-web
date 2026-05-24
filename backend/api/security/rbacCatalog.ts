import { AccessControl } from 'accesscontrol';

export type RoleKey =
  | 'root'
  | 'platform_admin'
  | 'security_admin'
  | 'content_admin'
  | 'editor'
  | 'moderator'
  | 'support'
  | 'analyst'
  | 'user'
  | (string & {});

export type RbacResource =
  | 'system'
  | 'rbac'
  | 'users'
  | 'lessons'
  | 'quizzes'
  | 'dictionary'
  | 'items'
  | 'progress'
  | 'telemetry'
  | 'publications';

export type CrudAction = 'create' | 'read' | 'update' | 'delete';
export type PermissionScope = 'own' | 'any';

export interface PermissionTuple {
  resource: RbacResource;
  action: CrudAction;
  scope: PermissionScope;
}

export interface RolePrivileges {
  role: RoleKey;
  title: string;
  priority: number;
  summary: string;
  privileges: string[];
}

export const ROLE_PRIORITY: Record<RoleKey, number> = {
  root: 1000,
  platform_admin: 900,
  security_admin: 800,
  content_admin: 700,
  editor: 600,
  moderator: 500,
  support: 400,
  analyst: 300,
  user: 100,
};

const ALL_RESOURCES: RbacResource[] = [
  'system',
  'rbac',
  'users',
  'lessons',
  'quizzes',
  'dictionary',
  'items',
  'progress',
  'telemetry',
  'publications',
];

const allCrudAny = (resource: RbacResource): PermissionTuple[] => [
  { resource, action: 'create', scope: 'any' },
  { resource, action: 'read', scope: 'any' },
  { resource, action: 'update', scope: 'any' },
  { resource, action: 'delete', scope: 'any' },
];

const ROLE_GRANTS: Record<RoleKey, PermissionTuple[]> = {
  root: ALL_RESOURCES.flatMap(allCrudAny),

  platform_admin: [
    ...allCrudAny('users'),
    ...allCrudAny('lessons'),
    ...allCrudAny('quizzes'),
    ...allCrudAny('dictionary'),
    ...allCrudAny('items'),
    ...allCrudAny('publications'),
    { resource: 'rbac', action: 'read', scope: 'any' },
    { resource: 'rbac', action: 'update', scope: 'any' },
    { resource: 'system', action: 'read', scope: 'any' },
    { resource: 'system', action: 'update', scope: 'any' },
    { resource: 'progress', action: 'read', scope: 'any' },
    { resource: 'telemetry', action: 'read', scope: 'any' },
    { resource: 'telemetry', action: 'delete', scope: 'any' },
  ],

  security_admin: [
    { resource: 'system', action: 'read', scope: 'any' },
    { resource: 'rbac', action: 'read', scope: 'any' },
    { resource: 'users', action: 'read', scope: 'any' },
    { resource: 'users', action: 'update', scope: 'any' },
    { resource: 'telemetry', action: 'read', scope: 'any' },
    { resource: 'telemetry', action: 'delete', scope: 'any' },
    { resource: 'progress', action: 'read', scope: 'any' },
  ],

  content_admin: [
    ...allCrudAny('lessons'),
    ...allCrudAny('quizzes'),
    ...allCrudAny('dictionary'),
    ...allCrudAny('items'),
    ...allCrudAny('publications'),
    { resource: 'progress', action: 'read', scope: 'any' },
  ],

  editor: [
    { resource: 'lessons', action: 'read', scope: 'any' },
    { resource: 'lessons', action: 'update', scope: 'any' },
    { resource: 'quizzes', action: 'read', scope: 'any' },
    { resource: 'quizzes', action: 'update', scope: 'any' },
    { resource: 'dictionary', action: 'read', scope: 'any' },
    { resource: 'publications', action: 'create', scope: 'own' },
    { resource: 'publications', action: 'read', scope: 'own' },
    { resource: 'publications', action: 'update', scope: 'own' },
    { resource: 'publications', action: 'delete', scope: 'own' },
  ],

  moderator: [
    { resource: 'users', action: 'read', scope: 'any' },
    { resource: 'progress', action: 'read', scope: 'any' },
    { resource: 'publications', action: 'read', scope: 'any' },
    { resource: 'publications', action: 'update', scope: 'any' },
    { resource: 'dictionary', action: 'read', scope: 'any' },
  ],

  support: [
    { resource: 'users', action: 'read', scope: 'any' },
    { resource: 'users', action: 'update', scope: 'any' },
    { resource: 'progress', action: 'read', scope: 'any' },
    { resource: 'lessons', action: 'read', scope: 'any' },
    { resource: 'quizzes', action: 'read', scope: 'any' },
    { resource: 'dictionary', action: 'read', scope: 'any' },
  ],

  analyst: [
    { resource: 'system', action: 'read', scope: 'any' },
    { resource: 'telemetry', action: 'read', scope: 'any' },
    { resource: 'progress', action: 'read', scope: 'any' },
    { resource: 'users', action: 'read', scope: 'any' },
  ],

  user: [
    { resource: 'users', action: 'read', scope: 'own' },
    { resource: 'users', action: 'update', scope: 'own' },
    { resource: 'lessons', action: 'read', scope: 'any' },
    { resource: 'quizzes', action: 'read', scope: 'any' },
    { resource: 'quizzes', action: 'update', scope: 'own' },
    { resource: 'dictionary', action: 'read', scope: 'any' },
    { resource: 'progress', action: 'read', scope: 'own' },
  ],
};

export const ROLE_PRIVILEGES_OVERVIEW: RolePrivileges[] = [
  {
    role: 'root',
    title: 'Root',
    priority: 1000,
    summary: 'Unrestricted system owner rights.',
    privileges: ['All resources, all actions, any scope.'],
  },
  {
    role: 'platform_admin',
    title: 'Platform Administrator',
    priority: 900,
    summary: 'Global platform operations and user/content governance.',
    privileges: [
      'Manage users and role assignments.',
      'Manage all learning content and publications.',
      'Read and update system settings and telemetry.',
    ],
  },
  {
    role: 'security_admin',
    title: 'Security Administrator',
    priority: 800,
    summary: 'Security controls and audit management without role mutation.',
    privileges: [
      'Update user security state.',
      'Read role graph only.',
      'Read and prune telemetry.',
    ],
  },
  {
    role: 'content_admin',
    title: 'Content Administrator',
    priority: 700,
    summary: 'Full control over lessons, quizzes, dictionary, and publications.',
    privileges: [
      'CRUD lessons/quizzes/dictionary/items/publications.',
      'Read user progress stats.',
    ],
  },
  {
    role: 'editor',
    title: 'Editor',
    priority: 600,
    summary: 'Content editing with limited ownership scope for publications.',
    privileges: [
      'Read/update lessons and quizzes.',
      'Manage own publication drafts.',
    ],
  },
  {
    role: 'moderator',
    title: 'Moderator',
    priority: 500,
    summary: 'Moderation and operational oversight.',
    privileges: [
      'Read users and progress.',
      'Review and update publications.',
    ],
  },
  {
    role: 'support',
    title: 'Support Specialist',
    priority: 400,
    summary: 'Operational assistance without destructive rights.',
    privileges: [
      'Read users/progress.',
      'Limited user update actions.',
      'Read educational content.',
    ],
  },
  {
    role: 'analyst',
    title: 'Analyst',
    priority: 300,
    summary: 'Read-only analytics and system observability.',
    privileges: [
      'Read telemetry and progress.',
      'Read user/system metrics.',
    ],
  },
  {
    role: 'user',
    title: 'User',
    priority: 100,
    summary: 'Baseline self-service access for authenticated learning flows.',
    privileges: [
      'Read/update own profile and progress.',
      'Read lessons/quizzes/dictionary and submit own quiz attempts.',
    ],
  },
];

const runGrant = (
  ac: AccessControl,
  role: RoleKey,
  permission: PermissionTuple
) => {
  const chain = ac.grant(role);

  if (permission.action === 'create' && permission.scope === 'any') chain.createAny(permission.resource);
  if (permission.action === 'create' && permission.scope === 'own') chain.createOwn(permission.resource);

  if (permission.action === 'read' && permission.scope === 'any') chain.readAny(permission.resource);
  if (permission.action === 'read' && permission.scope === 'own') chain.readOwn(permission.resource);

  if (permission.action === 'update' && permission.scope === 'any') chain.updateAny(permission.resource);
  if (permission.action === 'update' && permission.scope === 'own') chain.updateOwn(permission.resource);

  if (permission.action === 'delete' && permission.scope === 'any') chain.deleteAny(permission.resource);
  if (permission.action === 'delete' && permission.scope === 'own') chain.deleteOwn(permission.resource);
};

export const buildAccessControl = () => {
  const ac = new AccessControl();

  (Object.keys(ROLE_GRANTS) as RoleKey[]).forEach((role) => {
    ROLE_GRANTS[role].forEach((permission) => runGrant(ac, role, permission));
  });

  return ac;
};

export const LEGACY_ROLE_TO_ROLE_KEY: Record<string, RoleKey> = {
  admin: 'platform_admin',
  moderator: 'moderator',
  user: 'user',
};

export const roleFromLegacy = (legacyRole: string | undefined | null): RoleKey => {
  if (!legacyRole) {
    return 'user';
  }

  return LEGACY_ROLE_TO_ROLE_KEY[legacyRole.toLowerCase()] || 'user';
};
