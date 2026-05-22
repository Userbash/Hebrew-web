import { Request, Response, NextFunction } from 'express';
import { db } from '../data/db.js';
import { RequestWithAuth, getClientIp } from './auth.js';

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

type TelemetryContext = {
  userId?: string | null;
  sessionId?: string | null;
  area?: string;
  resource?: string;
  action?: string;
  outcome?: 'success' | 'error' | 'blocked';
  targetUserId?: string | null;
  loginIdentifier?: string | null;
  isAuthenticated?: boolean;
  userRole?: string | null;
  highestRole?: string | null;
  roleKeys?: string[];
  isSystemBlocked?: boolean | null;
  hadPreviousLogin?: boolean | null;
  accountLocked?: boolean | null;
  failedLoginAttempts?: number | null;
  metadata?: Record<string, JsonValue>;
};

const MUTATION_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

const toSafeJson = (value: unknown, depth = 0): JsonValue => {
  if (depth > 3) {
    return '[max-depth]';
  }

  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === 'string') {
    return value.length > 300 ? `${value.slice(0, 300)}…` : value;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }

  if (Array.isArray(value)) {
    return value.slice(0, 25).map((item) => toSafeJson(item, depth + 1));
  }

  if (typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    const next: Record<string, JsonValue> = {};

    for (const [key, item] of Object.entries(obj).slice(0, 40)) {
      next[key] = toSafeJson(item, depth + 1);
    }

    return next;
  }

  return String(value);
};

const inferArea = (path: string) => {
  if (path.startsWith('/api/admin')) return 'admin';
  if (path.startsWith('/api/auth')) return 'auth';
  return 'site';
};

const inferResource = (path: string) => {
  const parts = path.split('/').filter(Boolean);
  if (parts.length < 2) {
    return 'unknown';
  }

  if (parts[1] === 'admin') {
    return parts[2] || 'admin';
  }

  return parts[1];
};

const inferAction = (method: string, path: string) => {
  if (path.startsWith('/api/auth/login')) return 'login';
  if (path.startsWith('/api/auth/logout')) return 'logout';
  if (path.startsWith('/api/auth/register')) return 'register';
  if (path.startsWith('/api/auth/refresh')) return 'refresh';

  if (method === 'GET') return 'read';
  if (method === 'POST') return 'create';
  if (method === 'PUT' || method === 'PATCH') return 'update';
  if (method === 'DELETE') return 'delete';

  return MUTATION_METHODS.has(method) ? 'mutate' : 'read';
};

const inferOutcome = (statusCode: number): 'success' | 'error' | 'blocked' => {
  if (statusCode >= 200 && statusCode < 400) return 'success';
  if (statusCode === 401 || statusCode === 403 || statusCode === 423) return 'blocked';
  return 'error';
};

export const setTelemetryContext = (res: Response, context: TelemetryContext) => {
  const locals = res.locals as { telemetryContext?: TelemetryContext };
  const prev = locals.telemetryContext || {};
  locals.telemetryContext = {
    ...prev,
    ...context,
    metadata: {
      ...(prev.metadata || {}),
      ...(context.metadata || {}),
    },
  };
};

/**
 * Lightweight request telemetry.
 *
 * We write after the response is sent so this never blocks request handling.
 */
export const telemetryMiddleware = (req: Request, res: Response, next: NextFunction) => {
  const startedAt = Date.now();

  res.on('finish', () => {
    const authReq = req as Partial<RequestWithAuth> & {
      accessProfile?: {
        roleKeys?: string[];
        highestRole?: string;
        isSystemBlocked?: boolean;
      };
    };

    const locals = res.locals as { telemetryContext?: TelemetryContext };
    const context = locals.telemetryContext || {};

    const durationMs = Date.now() - startedAt;
    const path = req.originalUrl.split('?')[0] || req.path;

    const roleKeys = context.roleKeys || authReq.accessProfile?.roleKeys || [];
    const highestRole = context.highestRole || authReq.accessProfile?.highestRole || null;
    const userRole = context.userRole || highestRole || null;

    const actorUserId = authReq.userId || context.userId || context.targetUserId || null;
    const sessionId = authReq.sessionId || context.sessionId || null;
    const targetUserId = context.targetUserId || req.params.userId || req.params.id || null;

    const contextMetadataRaw = toSafeJson(context.metadata);
    const contextMetadata = (contextMetadataRaw && typeof contextMetadataRaw === 'object' && !Array.isArray(contextMetadataRaw))
      ? contextMetadataRaw as Record<string, JsonValue>
      : {};

    const metadata: Record<string, JsonValue> = {
      query_keys: Object.keys((req.query || {}) as Record<string, unknown>),
      body_keys: Object.keys((req.body && typeof req.body === 'object') ? (req.body as Record<string, unknown>) : {}),
      has_body: Boolean(req.body && typeof req.body === 'object' && Object.keys(req.body as Record<string, unknown>).length > 0),
      content_length: req.get('content-length') || null,
      referer: req.get('referer') || null,
      origin: req.get('origin') || null,
      accept_language: req.get('accept-language') || null,
      user_agent_family: (req.get('user-agent') || '').slice(0, 120),
      ...contextMetadata,
    };

    void db.query(
      `INSERT INTO user_telemetry (
         user_id,
         session_id,
         method,
         path,
         area,
         resource,
         action,
         outcome,
         status_code,
         ip_address,
         user_agent,
         response_time_ms,
         target_user_id,
         is_authenticated,
         login_identifier,
         user_role,
         highest_role,
         role_keys,
         is_system_blocked,
         had_previous_login,
         account_locked,
         failed_login_attempts,
         metadata
       ) VALUES (
         $1, $2, $3, $4, $5, $6, $7, $8,
         $9, $10, $11, $12, $13, $14, $15, $16,
         $17, $18, $19, $20, $21, $22, $23::jsonb
       )`,
      [
        actorUserId,
        sessionId,
        req.method,
        path,
        context.area || inferArea(path),
        context.resource || inferResource(path),
        context.action || inferAction(req.method.toUpperCase(), path),
        context.outcome || inferOutcome(res.statusCode),
        res.statusCode,
        getClientIp(req) || null,
        req.get('user-agent') || null,
        durationMs,
        targetUserId,
        context.isAuthenticated ?? Boolean(authReq.userId),
        context.loginIdentifier || null,
        userRole,
        highestRole,
        roleKeys,
        context.isSystemBlocked ?? authReq.accessProfile?.isSystemBlocked ?? null,
        context.hadPreviousLogin ?? null,
        context.accountLocked ?? null,
        context.failedLoginAttempts ?? null,
        JSON.stringify(metadata),
      ]
    ).catch((error: unknown) => {
      console.error('[Telemetry] Failed to store request metric', error);
    });
  });

  next();
};
