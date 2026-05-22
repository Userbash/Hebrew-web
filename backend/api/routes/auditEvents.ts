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

/**
 * GET /api/admin/audit/events
 * Global mutation audit trail for site + admin actions.
 */
router.get(
  '/events',
  verifyToken,
  requirePermission('telemetry', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const page = parseIntParam(req.query.page, 1, 1, 100000);
    const limit = parseIntParam(req.query.limit, 50, 1, 200);
    const offset = (page - 1) * limit;

    const method = typeof req.query.method === 'string' ? req.query.method.trim().toUpperCase() : '';
    const area = typeof req.query.area === 'string' ? req.query.area.trim() : '';
    const resource = typeof req.query.resource === 'string' ? req.query.resource.trim() : '';
    const action = typeof req.query.action === 'string' ? req.query.action.trim() : '';
    const outcome = typeof req.query.outcome === 'string' ? req.query.outcome.trim() : '';
    const path = typeof req.query.path === 'string' ? req.query.path.trim() : '';
    const actorId = typeof req.query.actorId === 'string' ? req.query.actorId.trim() : '';
    const targetId = typeof req.query.targetId === 'string' ? req.query.targetId.trim() : '';
    const statusCode = parseIntParam(req.query.statusCode, 0, 0, 999);
    const dateFrom = typeof req.query.dateFrom === 'string' ? req.query.dateFrom.trim() : '';
    const dateTo = typeof req.query.dateTo === 'string' ? req.query.dateTo.trim() : '';

    const where: string[] = [];
    const params: unknown[] = [];

    if (method) {
      params.push(method);
      where.push(`a.method = $${params.length}`);
    }

    if (area) {
      params.push(area);
      where.push(`a.area = $${params.length}`);
    }

    if (resource) {
      params.push(`%${resource}%`);
      where.push(`a.resource ILIKE $${params.length}`);
    }

    if (action) {
      params.push(`%${action}%`);
      where.push(`a.action ILIKE $${params.length}`);
    }

    if (outcome) {
      params.push(outcome);
      where.push(`a.outcome = $${params.length}`);
    }

    if (path) {
      params.push(`%${path}%`);
      where.push(`a.path ILIKE $${params.length}`);
    }

    if (actorId) {
      params.push(actorId);
      where.push(`a.actor_user_id::text = $${params.length}`);
    }

    if (targetId) {
      params.push(`%${targetId}%`);
      where.push(`COALESCE(a.target_id, '') ILIKE $${params.length}`);
    }

    if (statusCode > 0) {
      params.push(statusCode);
      where.push(`a.status_code = $${params.length}`);
    }

    if (dateFrom) {
      params.push(dateFrom);
      where.push(`a.created_at >= $${params.length}::timestamptz`);
    }

    if (dateTo) {
      params.push(dateTo);
      where.push(`a.created_at <= $${params.length}::timestamptz`);
    }

    const whereSql = where.length > 0 ? `WHERE ${where.join(' AND ')}` : '';

    const countRes = await db.query(
      `SELECT COUNT(*)::int AS total
       FROM audit_events a
       ${whereSql}`,
      params
    );

    params.push(limit, offset);

    const listRes = await db.query(
      `SELECT
          a.id,
          a.event_key,
          a.actor_user_id,
          u.username,
          u.email,
          a.session_id,
          a.area,
          a.resource,
          a.action,
          a.outcome,
          a.method,
          a.path,
          a.target_type,
          a.target_id,
          a.status_code,
          a.ip_address,
          a.user_agent,
          a.duration_ms,
          a.message,
          a.metadata,
          a.created_at
       FROM audit_events a
       LEFT JOIN users u ON u.id = a.actor_user_id
       ${whereSql}
       ORDER BY a.created_at DESC
       LIMIT $${params.length - 1}
       OFFSET $${params.length}`,
      params
    );

    const summaryRes = await db.query(
      `SELECT
          COUNT(*)::int AS total,
          COUNT(*) FILTER (WHERE outcome = 'success')::int AS success,
          COUNT(*) FILTER (WHERE outcome = 'error')::int AS errors,
          COUNT(*) FILTER (WHERE outcome = 'blocked')::int AS blocked,
          COUNT(*) FILTER (WHERE area = 'admin')::int AS admin_actions,
          COUNT(*) FILTER (WHERE area <> 'admin')::int AS site_actions,
          COALESCE(ROUND(AVG(duration_ms))::int, 0) AS avg_duration_ms
       FROM audit_events a
       ${whereSql}`,
      params.slice(0, params.length - 2)
    );

    const mapRes = await db.query(
      `SELECT
          a.area,
          a.resource,
          a.action,
          COUNT(*)::int AS total,
          COUNT(*) FILTER (WHERE a.outcome <> 'success')::int AS non_success
       FROM audit_events a
       WHERE a.created_at >= NOW() - INTERVAL '24 hours'
       GROUP BY a.area, a.resource, a.action
       ORDER BY total DESC, a.area, a.resource, a.action
       LIMIT 300`
    );

    const total = (countRes.rows[0] as { total: number } | undefined)?.total ?? 0;

    res.status(200).json({
      success: true,
      events: listRes.rows,
      summary: summaryRes.rows[0] || {
        total: 0,
        success: 0,
        errors: 0,
        blocked: 0,
        admin_actions: 0,
        site_actions: 0,
        avg_duration_ms: 0,
      },
      map: mapRes.rows,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.max(1, Math.ceil(total / limit)),
      },
    });
  })
);

export default router;
