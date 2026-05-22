/**
 * User routes with RBAC enforcement.
 */

import express, { Request, Response } from 'express';
import bcrypt from 'bcrypt';
import { db } from '../data/db.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import {
  requireAnyOrOwnPermission,
  requirePermission,
  type RequestWithAccess,
} from '../middleware/authorization.js';
import { asyncHandler, ForbiddenError, NotFoundError, ValidationError } from '../middleware/errorHandler.js';
import { setAuditContext } from '../middleware/auditTrail.js';
import { clearAccessProfileCache, getUserAccessProfile } from '../security/rbacService.js';
import {
  isValidEmail,
  isValidUsername,
  normalizeEmail,
  normalizeUsername,
  validatePassword,
} from '../security/credentials.js';

const router = express.Router();
const SALT_ROUNDS = 12;

const parsePositiveInt = (value: unknown, fallback: number, min = 1, max = 100) => {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return Math.min(max, Math.max(min, parsed));
};

const parseBooleanQuery = (value: unknown): boolean | undefined => {
  if (typeof value === 'boolean') {
    return value;
  }

  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (normalized === 'true') {
      return true;
    }

    if (normalized === 'false') {
      return false;
    }
  }

  return undefined;
};

const USER_SORT_COLUMNS = {
  id: "u.id",
  username: "u.username",
  email: "u.email",
  created_at: "u.created_at",
  updated_at: "u.updated_at",
  registered_at: "u.registered_at",
  last_login: "u.last_login",
  xp_total: "u.xp_total",
  level: "u.level",
  publication_count: "publication_count",
} as const;

const ALLOWED_UI_THEME_MODES = new Set(["system", "light", "dark"]);
const ALLOWED_UI_LANGUAGES = new Set(["ru", "en", "he"]);

interface UserUiPreferences {
  language?: "ru" | "en" | "he";
  languageMode?: "system" | "ru" | "en" | "he";
  themeMode?: "system" | "light" | "dark";
  timezone?: string;
  density?: "compact" | "comfortable";
  reduceMotion?: boolean;
  adminLandingSection?: string;
  dashboardLayout?: "classic" | "focus";
}

const sanitizeUiPreferences = (input: unknown): UserUiPreferences => {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new ValidationError("preferences must be an object");
  }

  const payload = input as Record<string, unknown>;
  const next: UserUiPreferences = {};

  if (typeof payload.language === "string" && ALLOWED_UI_LANGUAGES.has(payload.language)) {
    next.language = payload.language as UserUiPreferences["language"];
  }

  if (payload.languageMode === "system" || (typeof payload.languageMode === "string" && ALLOWED_UI_LANGUAGES.has(payload.languageMode))) {
    next.languageMode = payload.languageMode as UserUiPreferences["languageMode"];
  }

  if (typeof payload.themeMode === "string" && ALLOWED_UI_THEME_MODES.has(payload.themeMode)) {
    next.themeMode = payload.themeMode as UserUiPreferences["themeMode"];
  }

  if (typeof payload.timezone === "string") {
    const trimmed = payload.timezone.trim();
    if (trimmed.length > 0 && trimmed.length <= 64) {
      next.timezone = trimmed;
    }
  }

  if (payload.density === "compact" || payload.density === "comfortable") {
    next.density = payload.density;
  }

  if (typeof payload.reduceMotion === "boolean") {
    next.reduceMotion = payload.reduceMotion;
  }

  if (typeof payload.adminLandingSection === "string") {
    const trimmed = payload.adminLandingSection.trim();
    if (trimmed.length > 0 && trimmed.length <= 64) {
      next.adminLandingSection = trimmed;
    }
  }

  if (payload.dashboardLayout === "classic" || payload.dashboardLayout === "focus") {
    next.dashboardLayout = payload.dashboardLayout;
  }

  if (Object.keys(next).length === 0) {
    throw new ValidationError("No valid preference fields provided");
  }

  return next;
};

/**
 * GET /api/users/profile
 * Returns current user profile.
 */
router.get(
  '/profile',
  verifyToken,
  requirePermission('users', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const user = await db.getUserById(authReq.userId);

    if (!user) {
      throw new NotFoundError('User not found');
    }

    res.status(200).json({ success: true, user });
  })
);

/**
 * PUT /api/users/profile
 * Updates current user profile.
 */
router.put(
  '/profile',
  verifyToken,
  requirePermission('users', 'update', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const { firstName, lastName } = req.body;
    const authReq = req as RequestWithAuth;

    const query = `
      UPDATE users
      SET first_name = COALESCE($1, first_name),
          last_name = COALESCE($2, last_name),
          updated_at = CURRENT_TIMESTAMP
      WHERE id = $3 AND deleted_at IS NULL
      RETURNING id, email, username, first_name, last_name, role, xp_total, level, created_at, updated_at;
    `;

    const resDb = await db.query(query, [firstName, lastName, authReq.userId]);
    const user = resDb.rows[0];

    if (!user) {
      throw new NotFoundError('User not found');
    }

    await db.cacheUser(user);

    res.status(200).json({
      success: true,
      message: 'Profile updated successfully',
      user,
    });
  })
);

/**
 * GET /api/users/preferences
 * Returns current user UI preferences.
 */
router.get(
  "/preferences",
  verifyToken,
  requirePermission("users", "read", "own"),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const user = await db.getUserById(authReq.userId);

    if (!user) {
      throw new NotFoundError("User not found");
    }

    res.status(200).json({
      success: true,
      preferences: user.ui_preferences || {},
    });
  })
);

/**
 * PUT /api/users/preferences
 * Updates current user UI preferences.
 */
router.put(
  "/preferences",
  verifyToken,
  requirePermission("users", "update", "own"),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const patch = sanitizeUiPreferences(req.body?.preferences ?? req.body);

    const updated = await db.query(
      `UPDATE users
       SET ui_preferences = COALESCE(ui_preferences, '{}'::jsonb) || $1::jsonb,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $2 AND deleted_at IS NULL
       RETURNING id, ui_preferences`,
      [JSON.stringify(patch), authReq.userId]
    );

    const row = updated.rows[0] as { id: string; ui_preferences: Record<string, unknown> } | undefined;

    if (!row) {
      throw new NotFoundError("User not found");
    }

    const user = await db.getUserById(authReq.userId);
    if (user) {
      await db.cacheUser(user);
    }

    setAuditContext(res, {
      resource: "users",
      action: "update",
      targetType: "user",
      targetId: authReq.userId,
      message: "Updated user UI preferences",
    });

    res.status(200).json({
      success: true,
      preferences: row.ui_preferences || {},
    });
  })
);

/**
 * POST /api/users
 * Admin creates a new user with validated credentials.
 */
router.post(
  '/',
  verifyToken,
  requirePermission('users', 'create', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const normalizedEmail = normalizeEmail(String(req.body?.email || ''));
    const normalizedUsername = normalizeUsername(String(req.body?.username || ''));
    const password = String(req.body?.password || '');
    const firstName = String(req.body?.first_name || '').trim();
    const lastName = String(req.body?.last_name || '').trim();

    if (!isValidEmail(normalizedEmail)) {
      throw new ValidationError('Некорректный email');
    }

    if (!isValidUsername(normalizedUsername)) {
      throw new ValidationError('Некорректный username. Разрешены: буквы, цифры, ., _, - (3-50 символов)');
    }

    const passwordValidation = validatePassword(password, {
      email: normalizedEmail,
      username: normalizedUsername,
    });

    if (!passwordValidation.valid) {
      throw new ValidationError(`Пароль не соответствует требованиям: ${passwordValidation.errors.join('; ')}`);
    }

    const [existingEmail, existingUsername] = await Promise.all([
      db.getUserByEmail(normalizedEmail),
      db.getUserByUsername(normalizedUsername),
    ]);

    if (existingEmail) {
      throw new ValidationError('Пользователь с таким email уже существует');
    }

    if (existingUsername) {
      throw new ValidationError('Пользователь с таким username уже существует');
    }

    const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

    const createdRes = await db.query(
      `INSERT INTO users (email, password_hash, username, first_name, last_name, role, registered_at, password_changed_at)
       VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
       RETURNING id, email, username, first_name, last_name, role, xp_total, level, failed_login_attempts, locked_until, deleted_at, created_at, updated_at, registered_at, last_login`,
      [normalizedEmail, passwordHash, normalizedUsername, firstName, lastName, 'user']
    );

    const user = createdRes.rows[0];
    await db.cacheUser(user);

    res.status(201).json({
      success: true,
      message: 'User created successfully',
      user,
    });
  })
);

/**
 * GET /api/users
 * Admin list endpoint with advanced filters and typed sorting.
 */
router.get(
  '/',
  verifyToken,
  requirePermission('users', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const page = parsePositiveInt(req.query.page, 1, 1, 100000);
    const limit = parsePositiveInt(req.query.limit, 20, 1, 100);
    const offset = (page - 1) * limit;

    const userId = typeof req.query.id === 'string' ? req.query.id.trim() : '';
    const search = typeof req.query.search === 'string' ? req.query.search.trim() : '';
    const role = typeof req.query.role === 'string' ? req.query.role.trim() : '';
    const includeDeleted = parseBooleanQuery(req.query.includeDeleted) ?? false;
    const rbacRole = typeof req.query.rbacRole === 'string' ? req.query.rbacRole.trim() : '';
    const permission = typeof req.query.permission === 'string' ? req.query.permission.trim() : '';
    const publicationStatus = typeof req.query.publicationStatus === 'string' ? req.query.publicationStatus.trim() : '';
    const publicationSearch = typeof req.query.publicationSearch === 'string' ? req.query.publicationSearch.trim() : '';
    const hasPublications = parseBooleanQuery(req.query.hasPublications);
    const isBlocked = parseBooleanQuery(req.query.isBlocked);
    const sortByRaw = typeof req.query.sortBy === 'string' ? req.query.sortBy.trim() : 'created_at';
    const sortOrderRaw = typeof req.query.sortOrder === 'string' ? req.query.sortOrder.trim().toLowerCase() : 'desc';

    const sortOrder = sortOrderRaw === 'asc' ? 'ASC' : 'DESC';
    const sortBy = (sortByRaw in USER_SORT_COLUMNS ? sortByRaw : 'created_at') as keyof typeof USER_SORT_COLUMNS;
    const sortColumn = USER_SORT_COLUMNS[sortBy];

    const whereParts: string[] = [];
    const params: unknown[] = [];

    if (!includeDeleted) {
      whereParts.push('u.deleted_at IS NULL');
    }

    if (userId) {
      params.push(userId);
      whereParts.push(`u.id::text = $${params.length}`);
    }

    if (search) {
      params.push(`%${search}%`);
      const searchLikeParam = params.length;
      params.push(search);
      const searchTextParam = params.length;

      // Use both full-text and fallback ILIKE so admins can find partial fragments quickly.
      whereParts.push(`(
        u.search_vector @@ plainto_tsquery('simple', $${searchTextParam})
        OR u.email ILIKE $${searchLikeParam}
        OR u.username ILIKE $${searchLikeParam}
        OR COALESCE(u.first_name, '') ILIKE $${searchLikeParam}
        OR COALESCE(u.last_name, '') ILIKE $${searchLikeParam}
      )`);
    }

    if (role) {
      params.push(role);
      whereParts.push(`u.role = $${params.length}`);
    }

    if (rbacRole) {
      params.push(rbacRole);
      whereParts.push(`EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = u.id
          AND ur.is_active = TRUE
          AND ur.revoked_at IS NULL
          AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
          AND r.role_key = $${params.length}
      )`);
    }

    if (permission) {
      params.push(permission);
      whereParts.push(`EXISTS (
        SELECT 1
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        JOIN role_permissions rp ON rp.role_id = r.id
        JOIN permissions p ON p.id = rp.permission_id
        WHERE ur.user_id = u.id
          AND ur.is_active = TRUE
          AND ur.revoked_at IS NULL
          AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
          AND rp.granted = TRUE
          AND (
            p.permission_name = $${params.length}
            OR (p.resource || '.' || p.action || '.' || p.scope) = $${params.length}
          )
      )`);
    }

    if (publicationStatus) {
      params.push(publicationStatus);
      whereParts.push(`EXISTS (
        SELECT 1
        FROM items i
        WHERE i.category = 'publication'
          AND i.metadata->>'authorId' = u.id::text
          AND COALESCE(i.metadata->>'status', 'draft') = $${params.length}
      )`);
    }

    if (publicationSearch) {
      params.push(`%${publicationSearch}%`);
      whereParts.push(`EXISTS (
        SELECT 1
        FROM items i
        WHERE i.category = 'publication'
          AND i.metadata->>'authorId' = u.id::text
          AND (
            i.name ILIKE $${params.length}
            OR COALESCE(i.description, '') ILIKE $${params.length}
          )
      )`);
    }

    if (hasPublications === true) {
      whereParts.push(`EXISTS (
        SELECT 1
        FROM items i
        WHERE i.category = 'publication'
          AND i.metadata->>'authorId' = u.id::text
      )`);
    }

    if (hasPublications === false) {
      whereParts.push(`NOT EXISTS (
        SELECT 1
        FROM items i
        WHERE i.category = 'publication'
          AND i.metadata->>'authorId' = u.id::text
      )`);
    }

    if (typeof isBlocked === 'boolean') {
      params.push(isBlocked);
      whereParts.push(`u.is_system_blocked = $${params.length}`);
    }

    const whereSql = whereParts.length > 0 ? `WHERE ${whereParts.join(' AND ')}` : '';

    const countRes = await db.query(
      `SELECT COUNT(*)::int AS total FROM users u ${whereSql}`,
      params
    );

    params.push(limit, offset);

    const listRes = await db.query(
      `SELECT
          u.id,
          u.email,
          u.username,
          u.first_name,
          u.last_name,
          u.role,
          u.xp_total,
          u.level,
          u.registered_at,
          u.last_login,
          u.failed_login_attempts,
          u.locked_until,
          u.is_system_blocked,
          u.deleted_at,
          u.created_at,
          u.updated_at,
          COALESCE(access_stats.rbac_roles, ARRAY[]::text[]) AS rbac_roles,
          COALESCE(access_stats.permission_count, 0)::int AS permission_count,
          COALESCE(publication_stats.publication_count, 0)::int AS publication_count,
          COALESCE(publication_stats.published_publication_count, 0)::int AS published_publication_count
       FROM users u
       LEFT JOIN LATERAL (
         SELECT
           COALESCE(ARRAY_AGG(DISTINCT r.role_key ORDER BY r.role_key), ARRAY[]::text[]) AS rbac_roles,
           COUNT(DISTINCT p.id)::int AS permission_count
         FROM user_roles ur
         JOIN roles r ON r.id = ur.role_id
         LEFT JOIN role_permissions rp ON rp.role_id = r.id AND rp.granted = TRUE
         LEFT JOIN permissions p ON p.id = rp.permission_id
         WHERE ur.user_id = u.id
           AND ur.is_active = TRUE
           AND ur.revoked_at IS NULL
           AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
       ) AS access_stats ON TRUE
       LEFT JOIN LATERAL (
         SELECT
           COUNT(*)::int AS publication_count,
           COUNT(*) FILTER (WHERE COALESCE(i.metadata->>'status', 'draft') = 'published')::int AS published_publication_count
         FROM items i
         WHERE i.category = 'publication'
           AND i.metadata->>'authorId' = u.id::text
       ) AS publication_stats ON TRUE
       ${whereSql}
       ORDER BY ${sortColumn} ${sortOrder}, u.id ASC
       LIMIT $${params.length - 1}
       OFFSET $${params.length}`,
      params
    );

    const total = (countRes.rows[0] as { total: number } | undefined)?.total ?? 0;

    res.status(200).json({
      success: true,
      users: listRes.rows,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.max(1, Math.ceil(total / limit)),
      },
    });
  })
);

/**
 * PATCH /api/users/:id
 * Admin update endpoint.
 */
router.patch(
  '/:id',
  verifyToken,
  requirePermission('users', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;

    const updates = {
      email: typeof req.body?.email === 'string' ? req.body.email.trim() : null,
      username: typeof req.body?.username === 'string' ? req.body.username.trim() : null,
      first_name: typeof req.body?.first_name === 'string' ? req.body.first_name.trim() : null,
      last_name: typeof req.body?.last_name === 'string' ? req.body.last_name.trim() : null,
      xp_total: typeof req.body?.xp_total === 'number' ? req.body.xp_total : null,
      level: typeof req.body?.level === 'number' ? req.body.level : null,
      locked_until: typeof req.body?.locked_until === 'string' ? req.body.locked_until : null,
    };

    const query = `
      UPDATE users
      SET email = COALESCE($1, email),
          username = COALESCE($2, username),
          first_name = COALESCE($3, first_name),
          last_name = COALESCE($4, last_name),
          xp_total = COALESCE($5, xp_total),
          level = COALESCE($6, level),
          locked_until = CASE
            WHEN $7::text IS NULL THEN locked_until
            WHEN trim($7::text) = '' THEN NULL
            ELSE $7::timestamptz
          END,
          updated_at = CURRENT_TIMESTAMP
      WHERE id = $8
      RETURNING id, email, username, first_name, last_name, role, xp_total, level, failed_login_attempts, locked_until, deleted_at, created_at, updated_at;
    `;

    const resDb = await db.query(query, [
      updates.email,
      updates.username,
      updates.first_name,
      updates.last_name,
      updates.xp_total,
      updates.level,
      updates.locked_until,
      id,
    ]);

    const user = resDb.rows[0];
    if (!user) {
      throw new NotFoundError('User not found');
    }

    await db.invalidateUserCache({
      id: user.id,
      email: user.email,
      username: user.username,
    });

    res.status(200).json({
      success: true,
      message: 'User updated successfully',
      user,
    });
  })
);

/**
 * DELETE /api/users/:id
 * Soft-delete user account.
 */
router.delete(
  '/:id',
  verifyToken,
  requirePermission('users', 'delete', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const authReq = req as RequestWithAuth;

    if (id === authReq.userId) {
      throw new ValidationError('You cannot delete your own account');
    }

    const resDb = await db.query(
      `UPDATE users
       SET deleted_at = CURRENT_TIMESTAMP,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $1 AND deleted_at IS NULL
       RETURNING id, email, username`,
      [id]
    );

    const deleted = resDb.rows[0] as { id: string; email: string; username: string } | undefined;
    if (!deleted) {
      throw new NotFoundError('User not found or already deleted');
    }

    await db.invalidateUserCache(deleted);

    res.status(200).json({
      success: true,
      message: 'User soft-deleted successfully',
      userId: deleted.id,
    });
  })
);

/**
 * PATCH /api/users/:id/restore
 * Restore a soft-deleted user account.
 */
router.patch(
  '/:id/restore',
  verifyToken,
  requirePermission('users', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;

    const resDb = await db.query(
      `UPDATE users
       SET deleted_at = NULL,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $1
       RETURNING id, email, username, deleted_at`,
      [id]
    );

    const restored = resDb.rows[0] as { id: string; email: string; username: string; deleted_at: string | null } | undefined;
    if (!restored) {
      throw new NotFoundError('User not found');
    }

    await db.invalidateUserCache(restored);

    res.status(200).json({
      success: true,
      message: 'User restored successfully',
      user: restored,
    });
  })
);

/**
 * GET /api/users/:id/sessions
 * Returns current and historical sessions for a user.
 */
router.get(
  '/:id/sessions',
  verifyToken,
  requirePermission('users', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;

    const user = await db.getUserById(id);
    if (!user) {
      throw new NotFoundError('User not found');
    }

    const sessionsRes = await db.query(
      `SELECT id, user_agent, ip_address, created_at, last_seen_at, expires_at, revoked_at
       FROM user_sessions
       WHERE user_id = $1
       ORDER BY created_at DESC
       LIMIT 100`,
      [id]
    );

    res.status(200).json({
      success: true,
      sessions: sessionsRes.rows,
      count: sessionsRes.rowCount ?? sessionsRes.rows.length,
    });
  })
);

/**
 * GET /api/users/stats/leaderboard
 * Read leaderboard by XP.
 */
router.get(
  '/stats/leaderboard',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const limit = parseInt(req.query.limit as string, 10) || 10;

    const query = `
      SELECT id, username, first_name, last_name, xp_total, level
      FROM users
      WHERE deleted_at IS NULL
      ORDER BY xp_total DESC
      LIMIT $1;
    `;

    const resDb = await db.query(query, [limit]);

    res.status(200).json({
      success: true,
      leaderboard: resDb.rows,
      count: resDb.rows.length,
    });
  })
);

/**
 * GET /api/users/:id
 * Reads another user profile when allowed, or own profile via own-scope permission.
 */
router.get(
  '/:id',
  verifyToken,
  requireAnyOrOwnPermission(
    'users',
    'read',
    (req: RequestWithAccess) => req.params.id === req.userId
  ),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const user = await db.getUserById(id);

    if (!user) {
      throw new NotFoundError('User not found');
    }

    res.status(200).json({ success: true, user });
  })
);


const ADMIN_ROLE_KEYS = new Set(['root', 'platform_admin']);

const parseStringArray = (value: unknown, fieldName: string) => {
  if (!Array.isArray(value)) {
    throw new ValidationError(fieldName + ' must be an array of strings');
  }

  const normalized = value.map((item) => {
    if (typeof item !== 'string') {
      throw new ValidationError(fieldName + ' must contain only strings');
    }

    const next = item.trim().toLowerCase();
    if (!next) {
      throw new ValidationError(fieldName + ' contains empty value');
    }

    return next;
  });

  return Array.from(new Set(normalized));
};

const isSuperadminLike = (roleKeys: string[], legacyRole?: string | null) => {
  if (String(legacyRole || '').toLowerCase() === 'superadmin') {
    return true;
  }

  return roleKeys.some((role) => ADMIN_ROLE_KEYS.has(role));
};

const ensurePermissionManageAccess = async (userId: string) => {
  const hasNamedRes = await db.query(
    `SELECT 1
     FROM user_roles ur
     JOIN roles r ON r.id = ur.role_id
     JOIN role_permissions rp ON rp.role_id = r.id AND rp.granted = TRUE
     JOIN permissions p ON p.id = rp.permission_id
     WHERE ur.user_id = $1
       AND ur.is_active = TRUE
       AND ur.revoked_at IS NULL
       AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
       AND p.permission_name = 'users.permissions.manage'
     LIMIT 1`,
    [userId]
  );

  if ((hasNamedRes.rowCount || 0) > 0) {
    return;
  }

  const fallbackRes = await db.query(
    `SELECT 1
     FROM user_roles ur
     JOIN roles r ON r.id = ur.role_id
     JOIN role_permissions rp ON rp.role_id = r.id AND rp.granted = TRUE
     JOIN permissions p ON p.id = rp.permission_id
     WHERE ur.user_id = $1
       AND ur.is_active = TRUE
       AND ur.revoked_at IS NULL
       AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
       AND p.resource = 'users'
       AND p.action = 'update'
       AND p.scope = 'any'
     LIMIT 1`,
    [userId]
  );

  if ((fallbackRes.rowCount || 0) === 0) {
    throw new ForbiddenError('Missing permission: users.permissions.manage');
  }
};

/**
 * GET /api/users/:id/permissions
 * Read current role+permission snapshot for user permissions editor.
 */
router.get(
  '/:id/permissions',
  verifyToken,
  requirePermission('users', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    await ensurePermissionManageAccess(authReq.userId);

    const targetId = req.params.id;
    const userRes = await db.query(
      `SELECT id, email, username, role, deleted_at
       FROM users
       WHERE id = $1
       LIMIT 1`,
      [targetId]
    );

    const targetUser = userRes.rows[0] as { id: string; email: string; username: string; role: string; deleted_at: string | null } | undefined;
    if (!targetUser) {
      throw new NotFoundError('User not found');
    }

    const rolesRes = await db.query(
      `SELECT DISTINCT r.role_key
       FROM user_roles ur
       JOIN roles r ON r.id = ur.role_id
       WHERE ur.user_id = $1
         AND ur.is_active = TRUE
         AND ur.revoked_at IS NULL
         AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
       ORDER BY r.role_key`,
      [targetId]
    );

    const permissionsRes = await db.query(
      `SELECT DISTINCT p.permission_name
       FROM user_roles ur
       JOIN roles r ON r.id = ur.role_id
       JOIN role_permissions rp ON rp.role_id = r.id AND rp.granted = TRUE
       JOIN permissions p ON p.id = rp.permission_id
       WHERE ur.user_id = $1
         AND ur.is_active = TRUE
         AND ur.revoked_at IS NULL
         AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
       ORDER BY p.permission_name`,
      [targetId]
    );

    const availableRolesRes = await db.query(
      `SELECT role_key FROM roles ORDER BY priority DESC, role_key ASC`
    );

    const availablePermissionsRes = await db.query(
      `SELECT permission_name FROM permissions ORDER BY permission_name ASC`
    );

    res.status(200).json({
      success: true,
      user: {
        id: targetUser.id,
        email: targetUser.email,
        username: targetUser.username,
        role: targetUser.role,
        rbac_roles: rolesRes.rows.map((row) => String((row as { role_key: string }).role_key)),
      },
      roles: rolesRes.rows.map((row) => String((row as { role_key: string }).role_key)),
      permissions: permissionsRes.rows.map((row) => String((row as { permission_name: string }).permission_name)),
      availableRoles: availableRolesRes.rows.map((row) => String((row as { role_key: string }).role_key)),
      availablePermissions: availablePermissionsRes.rows.map((row) => String((row as { permission_name: string }).permission_name)),
    });
  })
);

/**
 * PATCH /api/users/:id/permissions
 * Updates role assignments with strict security checks.
 */
router.patch(
  '/:id/permissions',
  verifyToken,
  requirePermission('users', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    await ensurePermissionManageAccess(authReq.userId);

    const targetId = req.params.id;
    const nextRoles = parseStringArray(req.body?.roles, 'roles');
    const nextPermissions = parseStringArray(req.body?.permissions, 'permissions');

    if (targetId === authReq.userId) {
      throw new ForbiddenError('Cannot edit own permissions');
    }

    const actorUser = await db.getUserById(authReq.userId);
    const targetUser = await db.getUserById(targetId);
    if (!actorUser || !targetUser) {
      throw new NotFoundError('User not found');
    }

    const actorProfile = await getUserAccessProfile(authReq.userId);
    const targetProfile = await getUserAccessProfile(targetId);
    if (!actorProfile || !targetProfile) {
      throw new NotFoundError('Access profile not found');
    }

    const actorSuperadmin = isSuperadminLike(actorProfile.roleKeys as string[], actorUser.role);
    const targetSuperadmin = isSuperadminLike(targetProfile.roleKeys as string[], targetUser.role);

    if (targetSuperadmin && !actorSuperadmin) {
      throw new ForbiddenError('Cannot edit superadmin permissions');
    }

    const rolesRes = await db.query(
      `SELECT id, role_key
       FROM roles
       WHERE role_key = ANY($1::text[])`,
      [nextRoles]
    );

    const foundRoles = new Set(rolesRes.rows.map((row) => String((row as { role_key: string }).role_key)));
    const unknownRoles = nextRoles.filter((role) => !foundRoles.has(role));
    if (unknownRoles.length > 0) {
      throw new ValidationError('Unknown roles: ' + unknownRoles.join(', '));
    }

    const permissionsRes = await db.query(
      `SELECT permission_name
       FROM permissions
       WHERE permission_name = ANY($1::text[])`,
      [nextPermissions]
    );

    const foundPermissions = new Set(permissionsRes.rows.map((row) => String((row as { permission_name: string }).permission_name)));
    const unknownPermissions = nextPermissions.filter((permission) => !foundPermissions.has(permission));
    if (unknownPermissions.length > 0) {
      throw new ValidationError('Unknown permissions: ' + unknownPermissions.join(', '));
    }

    const derivedPermissionsRes = await db.query(
      `SELECT DISTINCT p.permission_name
       FROM role_permissions rp
       JOIN permissions p ON p.id = rp.permission_id
       JOIN roles r ON r.id = rp.role_id
       WHERE rp.granted = TRUE
         AND r.role_key = ANY($1::text[])
       ORDER BY p.permission_name`,
      [nextRoles]
    );

    const derivedPermissions = derivedPermissionsRes.rows.map((row) => String((row as { permission_name: string }).permission_name));
    const derivedSet = new Set(derivedPermissions);
    const requestedSet = new Set(nextPermissions);

    const mismatch = derivedPermissions.length !== nextPermissions.length
      || derivedPermissions.some((permission) => !requestedSet.has(permission))
      || nextPermissions.some((permission) => !derivedSet.has(permission));

    if (mismatch) {
      throw new ValidationError('permissions must match effective permissions derived from selected roles');
    }

    const assignsAdminRole = nextRoles.some((role) => ADMIN_ROLE_KEYS.has(role));
    if (!actorSuperadmin && nextRoles.includes('root')) {
      throw new ForbiddenError('Only superadmin can assign superadmin role');
    }

    if (!assignsAdminRole && targetProfile.roleKeys.some((role) => ADMIN_ROLE_KEYS.has(String(role)))) {
      const adminCountRes = await db.query(
        `SELECT COUNT(DISTINCT ur.user_id)::int AS admin_count
         FROM user_roles ur
         JOIN roles r ON r.id = ur.role_id
         JOIN users u ON u.id = ur.user_id
         WHERE ur.is_active = TRUE
           AND ur.revoked_at IS NULL
           AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
           AND u.deleted_at IS NULL
           AND r.role_key IN ('root', 'platform_admin')`
      );

      const adminCount = Number((adminCountRes.rows[0] as { admin_count?: number } | undefined)?.admin_count || 0);
      if (adminCount <= 1) {
        throw new ForbiddenError('Cannot remove the last administrator');
      }
    }

    const beforeRolesRes = await db.query(
      `SELECT DISTINCT r.role_key
       FROM user_roles ur
       JOIN roles r ON r.id = ur.role_id
       WHERE ur.user_id = $1
         AND ur.is_active = TRUE
         AND ur.revoked_at IS NULL
         AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
       ORDER BY r.role_key`,
      [targetId]
    );

    const beforePermissionsRes = await db.query(
      `SELECT DISTINCT p.permission_name
       FROM user_roles ur
       JOIN roles r ON r.id = ur.role_id
       JOIN role_permissions rp ON rp.role_id = r.id AND rp.granted = TRUE
       JOIN permissions p ON p.id = rp.permission_id
       WHERE ur.user_id = $1
         AND ur.is_active = TRUE
         AND ur.revoked_at IS NULL
         AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
       ORDER BY p.permission_name`,
      [targetId]
    );

    const beforeRoles = beforeRolesRes.rows.map((row) => String((row as { role_key: string }).role_key));
    const beforePermissions = beforePermissionsRes.rows.map((row) => String((row as { permission_name: string }).permission_name));

    await db.query('BEGIN');

    try {
      await db.query(
        `UPDATE user_roles
         SET is_active = FALSE,
             revoked_at = CURRENT_TIMESTAMP,
             note = 'permissions update via admin panel'
         WHERE user_id = $1
           AND is_active = TRUE
           AND revoked_at IS NULL`,
        [targetId]
      );

      for (const roleRow of rolesRes.rows as Array<{ id: string; role_key: string }>) {
        await db.query(
          `INSERT INTO user_roles (user_id, role_id, assigned_by, note, is_active)
           VALUES ($1, $2, $3, $4, TRUE)`,
          [targetId, roleRow.id, authReq.userId, 'permissions update via admin panel']
        );
      }

      const legacyRole = assignsAdminRole ? 'admin' : 'user';
      await db.query(
        `UPDATE users
         SET role = $2,
             updated_at = CURRENT_TIMESTAMP
         WHERE id = $1`,
        [targetId, legacyRole]
      );

      await db.query('COMMIT');
    } catch (error) {
      await db.query('ROLLBACK');
      throw error;
    }

    clearAccessProfileCache(targetId);

    setAuditContext(res, {
      action: 'users.permissions.update',
      resource: 'users.permissions',
      targetType: 'user',
      targetId,
      message: 'User permissions updated',
      metadata: {
        actorId: authReq.userId,
        targetUserId: targetId,
        before: {
          roles: beforeRoles,
          permissions: beforePermissions,
        },
        after: {
          roles: nextRoles,
          permissions: nextPermissions,
        },
        createdAt: new Date().toISOString(),
      },
    });

    res.status(200).json({
      success: true,
      message: 'User permissions updated',
      roles: nextRoles,
      permissions: nextPermissions,
    });
  })
);

export default router;
