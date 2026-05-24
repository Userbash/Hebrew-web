import { Request, Response, NextFunction } from 'express';
import { db } from '../data/db.js';
import { RequestWithAuth, getClientIp } from './auth.js';

type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

type AuditContext = {
  action?: string;
  resource?: string;
  targetType?: string;
  targetId?: string | null;
  message?: string;
  metadata?: Record<string, JsonValue>;
};

const MUTATION_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
const SENSITIVE_KEYS = ['password', 'token', 'secret', 'cookie', 'authorization', 'hash', 'refresh'];

const truncate = (value: string, max = 300) => (value.length > max ? `${value.slice(0, max)}…` : value);

const isSensitiveKey = (key: string) => {
  const lower = key.toLowerCase();
  return SENSITIVE_KEYS.some((entry) => lower.includes(entry));
};

const sanitizeValue = (value: unknown, depth = 0): JsonValue => {
  if (depth > 3) {
    return '[max-depth]';
  }

  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === 'string') {
    return truncate(value, 500);
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }

  if (Array.isArray(value)) {
    return value.slice(0, 25).map((item) => sanitizeValue(item, depth + 1));
  }

  if (typeof value === 'object') {
    const src = value as Record<string, unknown>;
    const entries = Object.entries(src).slice(0, 40);
    const sanitized: Record<string, JsonValue> = {};

    for (const [key, raw] of entries) {
      sanitized[key] = isSensitiveKey(key) ? '[redacted]' : sanitizeValue(raw, depth + 1);
    }

    return sanitized;
  }

  return String(value);
};

const inferArea = (path: string) => {
  if (path.startsWith('/api/admin')) return 'admin';
  if (path.startsWith('/api/auth')) return 'auth';
  return 'site';
};

const inferResource = (path: string) => {
  const segments = path.split('/').filter(Boolean);
  if (segments.length < 2) return 'unknown';

  if (segments[1] === 'admin') {
    const primary = segments[2] || 'admin';
    const secondary = segments[3] || '';
    return secondary && !/^[0-9a-f-]{8,}$/i.test(secondary)
      ? `${primary}.${secondary}`
      : primary;
  }

  return segments[1];
};

const inferAction = (method: string, path: string) => {
  if (path.startsWith('/api/auth/login')) return 'login';
  if (path.startsWith('/api/auth/logout')) return 'logout';
  if (path.startsWith('/api/auth/register')) return 'register';
  if (path.startsWith('/api/auth/refresh')) return 'refresh';

  switch (method.toUpperCase()) {
    case 'POST':
      return 'create';
    case 'PUT':
    case 'PATCH':
      return 'update';
    case 'DELETE':
      return 'delete';
    default:
      return 'mutate';
  }
};

const inferOutcome = (statusCode: number): 'success' | 'error' | 'blocked' => {
  if (statusCode >= 200 && statusCode < 400) return 'success';
  if (statusCode === 401 || statusCode === 403) return 'blocked';
  return 'error';
};

const inferTargetId = (req: Request) => {
  const params = req.params || {};
  return (
    params.id ||
    params.userId ||
    params.roleKey ||
    params.publicationId ||
    params.itemId ||
    params.quizId ||
    null
  );
};

const pickObject = (value: unknown) => (value && typeof value === 'object' ? value as Record<string, unknown> : null);

const enrichContextFromResponseBody = (res: Response, body: unknown) => {
  const payload = pickObject(body);
  if (!payload) {
    return;
  }

  const locals = res.locals as { auditContext?: AuditContext };
  const current = locals.auditContext || {};

  const candidates: Array<[string, string]> = [
    ['user', 'user'],
    ['role', 'role'],
    ['publication', 'publication'],
    ['item', 'item'],
    ['assignment', 'assignment'],
    ['session', 'session'],
  ];

  for (const [key, targetType] of candidates) {
    const nested = pickObject(payload[key]);
    const nestedId = nested && typeof nested.id === 'string' ? nested.id : null;

    if (nestedId) {
      locals.auditContext = {
        ...current,
        targetType: current.targetType || targetType,
        targetId: current.targetId || nestedId,
        message: current.message || (typeof payload.message === 'string' ? payload.message : undefined),
      };
      return;
    }
  }

  const rootId = typeof payload.id === 'string' ? payload.id : null;
  if (rootId) {
    locals.auditContext = {
      ...current,
      targetType: current.targetType || 'entity',
      targetId: current.targetId || rootId,
      message: current.message || (typeof payload.message === 'string' ? payload.message : undefined),
    };
    return;
  }

  if (typeof payload.message === 'string' && !current.message) {
    locals.auditContext = {
      ...current,
      message: payload.message,
    };
  }
};

export const setAuditContext = (res: Response, context: AuditContext) => {
  const locals = res.locals as { auditContext?: AuditContext };
  locals.auditContext = { ...(locals.auditContext || {}), ...context };
};

export const auditTrailMiddleware = (req: Request, res: Response, next: NextFunction) => {
  const method = req.method.toUpperCase();
  const originalPath = req.originalUrl.split('?')[0] || req.path;
  const isApi = originalPath.startsWith('/api/');

  if (!isApi || !MUTATION_METHODS.has(method)) {
    next();
    return;
  }

  const startedAt = Date.now();

  const originalJson = res.json.bind(res);
  res.json = ((body: unknown) => {
    enrichContextFromResponseBody(res, body);
    return originalJson(body);
  }) as Response['json'];

  res.on('finish', () => {
    const durationMs = Math.max(0, Date.now() - startedAt);
    const authReq = req as Partial<RequestWithAuth>;
    const locals = res.locals as { auditContext?: AuditContext };
    const context = locals.auditContext || {};

    const metadata: Record<string, JsonValue> = {
      params: sanitizeValue(req.params),
      query: sanitizeValue(req.query),
      body: sanitizeValue(req.body),
      body_keys: Object.keys((req.body && typeof req.body === 'object') ? (req.body as Record<string, unknown>) : {}),
      ...(context.metadata || {}),
    };

    void db.query(
      `INSERT INTO audit_events (
         actor_user_id,
         session_id,
         area,
         resource,
         action,
         outcome,
         method,
         path,
         target_type,
         target_id,
         status_code,
         ip_address,
         user_agent,
         duration_ms,
         message,
         metadata
       ) VALUES (
         $1, $2, $3, $4, $5, $6,
         $7, $8, $9, $10, $11, $12,
         $13, $14, $15, $16::jsonb
       )`,
      [
        authReq.userId || null,
        authReq.sessionId || null,
        inferArea(originalPath),
        context.resource || inferResource(originalPath),
        context.action || inferAction(method, originalPath),
        inferOutcome(res.statusCode),
        method,
        originalPath,
        context.targetType || null,
        context.targetId ?? inferTargetId(req),
        res.statusCode,
        getClientIp(req) || null,
        req.get('user-agent') || null,
        durationMs,
        context.message || null,
        JSON.stringify(metadata),
      ]
    ).catch((error: unknown) => {
      console.error('[AuditTrail] Failed to store mutation audit', error);
    });
  });

  next();
};
