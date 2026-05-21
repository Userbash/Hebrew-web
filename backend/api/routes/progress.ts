/**
 * Progress Routes
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/progress
 * Get current user's progress
 */
router.get('/', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const progress = await db.getUserProgress(authReq.userId);

    if (!progress) {
        throw new NotFoundError('Progress not found');
    }

    res.status(200).json({
        success: true,
        progress
    });
}));

/**
 * GET /api/progress/stats/summary
 * Get progress summary
 */
router.get('/stats/summary', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
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
        nextLevelXp: (user.level * 500),
        xpToNextLevel: Math.max(0, (user.level * 500) - user.xp_total),

        streak: user.streak || 0,
        lastActiveDate: userProgress.lastActiveDate
    };

    res.status(200).json({
        success: true,
        stats: completionStats
    });
}));

/**
 * GET /api/progress/stats/comparision
 * Compare with other users
 */
router.get('/stats/comparison', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    
    const allUsers_raw = await db.getAllUsers();
    const allUsers = allUsers_raw
        .map((u: any) => ({
            id: u.id,
            firstName: u.first_name,
            level: u.level,
            xpTotal: u.xp_total
        }))
        .sort((a: any, b: any) => b.xpTotal - a.xpTotal);

    const currentUserRank = allUsers.findIndex((u: any) => u.id === authReq.userId) + 1;

    res.status(200).json({
        success: true,
        currentUserRank,
        totalUsers: allUsers.length,
        topUsers: allUsers.slice(0, 5),
        userStats: allUsers.find((u: any) => u.id === authReq.userId)
    });
}));

/**
 * GET /api/progress/:userId
 * Get user's progress (if public)
 */
router.get('/:userId', asyncHandler(async (req: Request, res: Response) => {
    const userId = req.params.userId;
    const progress = await db.getUserProgress(userId);

    if (!progress) {
        throw new NotFoundError('Progress not found');
    }

    // Return only public stats
    const publicProgress = {
        userId: progress.userId,
        level: progress.level,
        xpTotal: progress.xpTotal,
        lessonsCompletedCount: progress.lessonsCompleted.length,
        quizzesCompletedCount: progress.quizzesCompleted.length
    };

    res.status(200).json({
        success: true,
        progress: publicProgress
    });
}));

export default router;
