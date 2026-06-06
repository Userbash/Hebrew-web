import express, { Request, Response } from 'express';
import { asyncHandler, ForbiddenError, UnauthorizedError, ValidationError } from '../middleware/errorHandler.js';
import { verifyToken } from '../middleware/auth.js';
import { requireRole } from '../middleware/authorization.js';
import { type RoleKey } from '../security/rbacCatalog.js';

const router = express.Router();

const ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];
const DEVTOOLKIT_BRIDGE_URL = process.env.DEVTOOLKIT_BRIDGE_URL || process.env.ORCHESTRATOR_BRIDGE_URL || 'http://127.0.0.1:8000';
const DEVTOOLKIT_TIMEOUT_MS = Number(process.env.DEVTOOLKIT_TIMEOUT_MS || 120_000);

type DevToolkitPermission = 'devtoolkit:read' | 'devtoolkit:plan' | 'devtoolkit:execute' | 'devtoolkit:apply_changes';

const canUsePermission = (roleKeys: string[], permission: DevToolkitPermission) => {
  const isElevated = roleKeys.includes('root') || roleKeys.includes('platform_admin');
  if (permission === 'devtoolkit:read' || permission === 'devtoolkit:plan') {
    return isElevated || roleKeys.includes('security_admin');
  }
  return isElevated;
};

const requireDevToolkitPermission = (permission: DevToolkitPermission) => asyncHandler(async (req: Request, _res: Response, next) => {
  const authReq = req as Request & { userId?: string };
  if (!authReq.userId) {
    throw new UnauthorizedError('Authentication required');
  }

  const profileModule = await import('../security/rbacService.js');
  const profile = await profileModule.getUserAccessProfile(authReq.userId);
  if (!profile) {
    throw new UnauthorizedError('Access profile not found');
  }
  if (!canUsePermission(profile.roleKeys as string[], permission)) {
    throw new ForbiddenError(`Missing permission: ${permission}`);
  }
  next();
});

const proxyJson = async (path: string, init?: RequestInit) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEVTOOLKIT_TIMEOUT_MS);
  try {
    const response = await fetch(DEVTOOLKIT_BRIDGE_URL + path, {
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
    });

    const text = await response.text();
    let parsed: unknown = null;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch {
      parsed = { raw: text };
    }

    return { response, parsed };
  } finally {
    clearTimeout(timeout);
  }
};

const forward = async (res: Response, path: string, init?: RequestInit) => {
  try {
    const { response, parsed } = await proxyJson(path, init);
    res.status(response.ok ? response.status : 502).json(parsed);
  } catch (error) {
    const isAbort = (error as { name?: string })?.name === 'AbortError';
    res.status(isAbort ? 504 : 502).json({
      status: 'error',
      message: isAbort ? 'Dev Toolkit bridge timeout' : 'Failed to reach Dev Toolkit bridge',
      bridge_url: DEVTOOLKIT_BRIDGE_URL + path,
    });
  }
};

router.use(verifyToken);
router.use(requireRole(ADMIN_ROLES, 'Administrator role required'));

router.post(
  '/sessions',
  requireDevToolkitPermission('devtoolkit:read'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as Request & { userId?: string };
    await forward(res, '/devtoolkit/sessions', {
      method: 'POST',
      body: JSON.stringify({ ...(req.body || {}), user_id: authReq.userId || undefined }),
    });
  })
);

router.get(
  '/sessions',
  requireDevToolkitPermission('devtoolkit:read'),
  asyncHandler(async (_req: Request, res: Response) => {
    await forward(res, '/devtoolkit/sessions');
  })
);

router.get(
  '/sessions/:sessionId/messages',
  requireDevToolkitPermission('devtoolkit:read'),
  asyncHandler(async (req: Request, res: Response) => {
    const sessionId = String(req.params?.sessionId || '').trim();
    if (!sessionId) {
      throw new ValidationError('sessionId is required');
    }
    await forward(res, `/devtoolkit/sessions/${encodeURIComponent(sessionId)}/messages`);
  })
);

router.get(
  '/sessions/:sessionId/diff',
  requireDevToolkitPermission('devtoolkit:read'),
  asyncHandler(async (req: Request, res: Response) => {
    const sessionId = String(req.params?.sessionId || '').trim();
    if (!sessionId) {
      throw new ValidationError('sessionId is required');
    }
    await forward(res, `/devtoolkit/sessions/${encodeURIComponent(sessionId)}/diff`);
  })
);

router.post(
  '/chat',
  requireDevToolkitPermission('devtoolkit:plan'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as Request & { userId?: string };
    await forward(res, '/devtoolkit/chat', {
      method: 'POST',
      body: JSON.stringify({ ...(req.body || {}), user_id: authReq.userId || undefined }),
    });
  })
);

router.post(
  '/execute',
  requireDevToolkitPermission('devtoolkit:execute'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as Request & { userId?: string };
    await forward(res, '/devtoolkit/execute', {
      method: 'POST',
      body: JSON.stringify({ ...(req.body || {}), user_id: authReq.userId || undefined }),
    });
  })
);

router.post(
  '/clipboard',
  requireDevToolkitPermission('devtoolkit:read'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as Request & { userId?: string };
    await forward(res, '/devtoolkit/clipboard', {
      method: 'POST',
      body: JSON.stringify({ ...(req.body || {}), user_id: authReq.userId || undefined }),
    });
  })
);

export default router;
