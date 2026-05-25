/**
 * Progress Routes
 *
 * RBAC model:
 * - Users can read their own progress and summary.
 * - Privileged roles with progress.read.any can read other users.
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken } from '../middleware/auth.js';
import {
  requireAnyOrOwnPermission,
  requirePermission,
  type RequestWithAccess,
} from '../middleware/authorization.js';
import { asyncHandler, NotFoundError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/progress
 * Get current user's progress.
 */
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

    res.status(200).json({
      success: true,
      progress,
    });
  })
);

/**
 * GET /api/progress/stats/summary
 * Get current user's summary statistics.
 */
router.get(
  '/stats/summary',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAccess;
    const user = await db.getUserById(authReq.userId);

    if (!user) {
      throw new NotFoundError('User not found');
    }

    const allLessons = await db.getAllLessons();
    const allQuizzes = await db.getAllQuizzes();
    const userProgress = await db.getUserProgress(authReq.userId);

    if (!userProgress) {
      throw new NotFoundError('Progress not found');
    }

    const completionStats = {
      lessonsCompleted: userProgress.lessonsCompleted.length,
      lessonsTotal: allLessons.length,
      lessonsPercentage: Math.round((userProgress.lessonsCompleted.length / (allLessons.length || 1)) * 100),

      quizzesCompleted: userProgress.quizzesCompleted.length,
      quizzesTotal: allQuizzes.length,
      quizzesPercentage: Math.round((userProgress.quizzesCompleted.length / (allQuizzes.length || 1)) * 100),

      currentLevel: user.level,
      currentXp: user.xp_total,
      nextLevelXp: user.level * 500,
      xpToNextLevel: Math.max(0, (user.level * 500) - user.xp_total),

      streak: user.streak || 0,
      lastActiveDate: userProgress.lastActiveDate,
    };

    res.status(200).json({
      success: true,
      stats: completionStats,
    });
  })
);

/**
 * GET /api/progress/stats/comparison
 * Compare current user's rank with other users.
 */
router.get(
  '/stats/comparison',
  verifyToken,
  requirePermission('progress', 'read', 'own'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAccess;

    const allUsersRaw = await db.getAllUsers();
    const allUsers = allUsersRaw
      .map((user: { id: string; first_name: string | null; level: number; xp_total: number }) => ({
        id: user.id,
        firstName: user.first_name,
        level: user.level,
        xpTotal: user.xp_total,
      }))
      .sort((a, b) => b.xpTotal - a.xpTotal);

    const currentUserRank = allUsers.findIndex((user) => user.id === authReq.userId) + 1;

    res.status(200).json({
      success: true,
      currentUserRank,
      totalUsers: allUsers.length,
      topUsers: allUsers.slice(0, 5),
      userStats: allUsers.find((user) => user.id === authReq.userId),
    });
  })
);

/**
 * GET /api/progress/:userId
 * Read public progress for a user.
 * - own profile: progress.read.own
 * - any profile: progress.read.any
 */
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

    res.status(200).json({
      success: true,
      progress: publicProgress,
    });
  })
);

export default router;
