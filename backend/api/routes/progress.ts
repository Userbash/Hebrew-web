import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken } from '../middleware/auth.js';
import {
  requireAnyOrOwnPermission,
  requirePermission,
  type RequestWithAccess,
} from '../middleware/authorization.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

type RangeType = 'week' | 'month' | 'halfYear' | 'year';
const RANGE_LIST: RangeType[] = ['week', 'month', 'halfYear', 'year'];

router.get(
  '/dashboard',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAccess;
    const dashboard = await db.getUserDashboardProgress(authReq.userId);
    const user = await db.getUserById(authReq.userId);

    if (!user) {
      throw new NotFoundError('User not found');
    }

    res.status(200).json({
      success: true,
      data: {
        ...dashboard,
        user: {
          id: user.id,
          level: user.level,
          xpTotal: user.xp_total,
          streak: user.streak || 0,
        },
      },
    });
  })
);

router.get(
  '/active-lessons',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAccess;
    const activeLessons = await db.getUserActiveLessons(authReq.userId);
    res.status(200).json({ success: true, data: { activeLessons } });
  })
);

router.get(
  '/recent-activity',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAccess;
    const limit = Number(req.query.limit || 20);
    const events = await db.getUserRecentActivity(authReq.userId, Number.isFinite(limit) ? limit : 20);
    res.status(200).json({ success: true, data: { events } });
  })
);

router.get(
  '/stats/range',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAccess;
    const range = typeof req.query.range === 'string' ? req.query.range : 'week';
    if (!RANGE_LIST.includes(range as RangeType)) {
      throw new ValidationError('Invalid range. Use: week, month, halfYear, year');
    }

    const completed = await db.getUserRangeStats(authReq.userId, range as RangeType);
    const targets: Record<RangeType, number> = { week: 5, month: 20, halfYear: 80, year: 160 };
    const progressPercent = Math.max(0, Math.min(100, Math.round((completed / targets[range as RangeType]) * 100)));

    res.status(200).json({
      success: true,
      data: {
        range,
        completed,
        progressPercent,
      },
    });
  })
);

router.get(
  '/',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAccess;
    const progress = await db.getUserProgress(authReq.userId);

    if (!progress) {
      throw new NotFoundError('Progress not found');
    }

    res.status(200).json({ success: true, data: { progress } });
  })
);

router.get(
  '/:userId',
  verifyToken,
  requireAnyOrOwnPermission(
    'progress',
    'read',
    (req: RequestWithAccess) => req.params.userId === req.userId
  ),
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.params.userId;
    const progress = await db.getUserProgress(userId);

    if (!progress) {
      throw new NotFoundError('Progress not found');
    }

    const publicProgress = {
      userId: progress.userId,
      level: progress.level,
      xpTotal: progress.xpTotal,
      lessonsCompletedCount: progress.lessonsCompleted.length,
      quizzesCompletedCount: progress.quizzesCompleted.length,
    };

    res.status(200).json({ success: true, data: { progress: publicProgress } });
  })
);

export default router;
