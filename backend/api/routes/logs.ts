import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken } from '../middleware/auth.js';
import { requirePermission } from '../middleware/authorization.js';
import { asyncHandler } from '../middleware/errorHandler.js';

const router = express.Router();

const parseIntParam = (value: unknown, fallback: number, min: number, max: number) => {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return Math.min(max, Math.max(min, parsed));
};

const parseBoolParam = (value: unknown): boolean | undefined => {
  if (value === true || value === 'true' || value === '1') {
    return true;
  }

  if (value === false || value === 'false' || value === '0') {
    return false;
  }

  return undefined;
};

/**
 * GET /api/admin/logs
 * Query recent API telemetry (read-only).
 */
router.get(
  '/',
  verifyToken,
  requirePermission('telemetry', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const page = parseIntParam(req.query.page, 1, 1, 100000);
    const limit = parseIntParam(req.query.limit, 50, 1, 200);
    const offset = (page - 1) * limit;

    const method = typeof req.query.method === 'string' ? req.query.method.trim().toUpperCase() : '';
    const path = typeof req.query.path === 'string' ? req.query.path.trim() : '';
    const userId = typeof req.query.userId === 'string' ? req.query.userId.trim() : '';
    const targetUserId = typeof req.query.targetUserId === 'string' ? req.query.targetUserId.trim() : '';
    const statusCode = parseIntParam(req.query.statusCode, 0, 0, 999);
    const area = typeof req.query.area === 'string' ? req.query.area.trim() : '';
    const action = typeof req.query.action === 'string' ? req.query.action.trim() : '';
    const outcome = typeof req.query.outcome === 'string' ? req.query.outcome.trim() : '';
    const userRole = typeof req.query.userRole === 'string' ? req.query.userRole.trim() : '';
    const loginIdentifier = typeof req.query.loginIdentifier === 'string' ? req.query.loginIdentifier.trim() : '';

    const isAuthenticated = parseBoolParam(req.query.isAuthenticated);
    const isSystemBlocked = parseBoolParam(req.query.isSystemBlocked);
    const accountLocked = parseBoolParam(req.query.accountLocked);
    const hadPreviousLogin = parseBoolParam(req.query.hadPreviousLogin);

    const where: string[] = [];
    const params: unknown[] = [];

    if (method) {
      params.push(method);
      where.push(`t.method = $${params.length}`);
    }

    if (path) {
      params.push(`%${path}%`);
      where.push(`t.path ILIKE $${params.length}`);
    }

    if (userId) {
      params.push(userId);
      where.push(`t.user_id::text = $${params.length}`);
    }

    if (targetUserId) {
      params.push(targetUserId);
      where.push(`t.target_user_id::text = $${params.length}`);
    }

    if (statusCode > 0) {
      params.push(statusCode);
      where.push(`t.status_code = $${params.length}`);
    }

    if (area) {
      params.push(area);
      where.push(`t.area = $${params.length}`);
    }

    if (action) {
      params.push(`%${action}%`);
      where.push(`t.action ILIKE $${params.length}`);
    }

    if (outcome) {
      params.push(outcome);
      where.push(`t.outcome = $${params.length}`);
    }

    if (userRole) {
      params.push(userRole);
      where.push(`COALESCE(t.highest_role, t.user_role, '') = $${params.length}`);
    }

    if (loginIdentifier) {
      params.push(`%${loginIdentifier.toLowerCase()}%`);
      where.push(`lower(COALESCE(t.login_identifier, '')) LIKE $${params.length}`);
    }

    if (isAuthenticated !== undefined) {
      params.push(isAuthenticated);
      where.push(`t.is_authenticated = $${params.length}`);
    }

    if (isSystemBlocked !== undefined) {
      params.push(isSystemBlocked);
      where.push(`COALESCE(t.is_system_blocked, false) = $${params.length}`);
    }

    if (accountLocked !== undefined) {
      params.push(accountLocked);
      where.push(`COALESCE(t.account_locked, false) = $${params.length}`);
    }

    if (hadPreviousLogin !== undefined) {
      params.push(hadPreviousLogin);
      where.push(`COALESCE(t.had_previous_login, false) = $${params.length}`);
    }

    const whereSql = where.length > 0 ? `WHERE ${where.join(' AND ')}` : '';

    const countRes = await db.query(
      `SELECT COUNT(*)::int AS total FROM user_telemetry t ${whereSql}`,
      params
    );

    params.push(limit, offset);

    const listRes = await db.query(
      `SELECT
          t.id,
          t.user_id,
          u.username,
          u.email,
          t.session_id,
          t.method,
          t.path,
          t.area,
          t.resource,
          t.action,
          t.outcome,
          t.status_code,
          t.ip_address,
          t.user_agent,
          t.response_time_ms,
          t.target_user_id,
          t.is_authenticated,
          t.login_identifier,
          t.user_role,
          t.highest_role,
          t.role_keys,
          t.is_system_blocked,
          t.had_previous_login,
          t.account_locked,
          t.failed_login_attempts,
          t.metadata,
          t.created_at
       FROM user_telemetry t
       LEFT JOIN users u ON u.id = t.user_id
       ${whereSql}
       ORDER BY t.created_at DESC
       LIMIT $${params.length - 1}
       OFFSET $${params.length}`,
      params
    );

    const summaryRes = await db.query(
      `SELECT
          COUNT(*)::int AS total,
          COUNT(*) FILTER (WHERE status_code >= 500)::int AS server_errors,
          COUNT(*) FILTER (WHERE status_code >= 400 AND status_code < 500)::int AS client_errors,
          COUNT(*) FILTER (WHERE outcome = 'success')::int AS success,
          COUNT(*) FILTER (WHERE outcome = 'blocked')::int AS blocked,
          COUNT(*) FILTER (WHERE outcome = 'error')::int AS errors,
          COUNT(*) FILTER (WHERE is_authenticated = TRUE)::int AS authenticated,
          COUNT(*) FILTER (WHERE COALESCE(account_locked, FALSE) = TRUE)::int AS locked_accounts,
          COALESCE(ROUND(AVG(response_time_ms))::int, 0) AS avg_response_ms
       FROM user_telemetry t
       ${whereSql}`,
      params.slice(0, params.length - 2)
    );

    res.status(200).json({
      success: true,
      logs: listRes.rows,
      summary: summaryRes.rows[0] || {
        total: 0,
        server_errors: 0,
        client_errors: 0,
        success: 0,
        blocked: 0,
        errors: 0,
        authenticated: 0,
        locked_accounts: 0,
        avg_response_ms: 0,
      },
      pagination: {
        page,
        limit,
        total: (countRes.rows[0] as { total: number } | undefined)?.total ?? 0,
        totalPages: Math.max(1, Math.ceil((((countRes.rows[0] as { total: number } | undefined)?.total) ?? 0) / limit)),
      },
    });
  })
);

export default router;
