import express, { Request, Response, NextFunction } from 'express';
import { verifyToken } from '../middleware/auth.js';
import { requireRole } from '../middleware/authorization.js';
import { adminApiLimiter } from '../middleware/security.js';
import { type RoleKey } from '../security/rbacCatalog.js';
import userRoutes from './users.js';
import accessControlRoutes from './accessControl.js';
import publicationsRoutes from './publications.js';

const router = express.Router();

const ADMIN_ROLES: RoleKey[] = ['root', 'platform_admin'];

// Isolate admin surface under dedicated URI and harden defaults.
router.use(verifyToken);
router.use(adminApiLimiter);
router.use(requireRole(ADMIN_ROLES, 'Administrator role required'));
router.use((_req: Request, res: Response, next: NextFunction) => {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Pragma', 'no-cache');
  next();
});

router.get('/health', (_req: Request, res: Response) => {
  res.status(200).json({
    success: true,
    scope: 'admin',
  });
});

router.use('/users', userRoutes);
router.use('/access', accessControlRoutes);
router.use('/publications', publicationsRoutes);

export default router;
