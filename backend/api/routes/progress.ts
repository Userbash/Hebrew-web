/**
 * Progress Routes
 */

import express, { Request, Response } from 'express';
import { store } from '../data/store.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/progress
 * Get current user's progress
 */
router.get('/', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const progress = store.getUserProgress(authReq.userId);

    if (!progress) {
        throw new NotFoundError('Progress not found');
    }

    res.status(200).json({
        success: true,
        progress
    });
}));

/**
 * GET /api/progress/:userId
 * Get user's progress (if public)
 */
router.get('/:userId', asyncHandler(async (req: Request, res: Response) => {
    const userId = Array.isArray(req.params.userId) ? req.params.userId[0] : req.params.userId;
    const progress = store.getUserProgress(userId);

    if (!progress) {
        throw new NotFoundError('Progress not found');
    }

    // Return only public stats
    const publicProgress = {
        userId: progress.userId,
        level: progress.level,
        xpTotal: progress.xpTotal,
        lessonsCompleted: progress.lessonsCompleted.length,
        quizzesCompleted: progress.quizzesCompleted.length
    };

    res.status(200).json({
        success: true,
        progress: publicProgress
    });
}));

/**
 * GET /api/progress/stats/summary
 * Get progress summary
 */
router.get('/stats/summary', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const user = store.getUserById(authReq.userId);

    if (!user) {
        throw new NotFoundError('User not found');
    }

    const allLessons = store.getAllLessons();
    const allQuizzes = store.getAllQuizzes();
    const userProgress = store.getUserProgress(authReq.userId);
    
    if (!userProgress) {
        throw new NotFoundError('Progress not found');
    }

    const completionStats = {
        lessonsCompleted: user.lessonsCompleted.length,
        lessonsTotal: allLessons.length,
        lessonsPercentage: Math.round((user.lessonsCompleted.length / (allLessons.length || 1)) * 100),

        quizzesCompleted: user.quizzesCompleted.length,
        quizzesTotal: allQuizzes.length,
        quizzesPercentage: Math.round((user.quizzesCompleted.length / (allQuizzes.length || 1)) * 100),

        currentLevel: user.level,
        currentXp: user.xpTotal,
        nextLevelXp: (user.level * 500),
        xpToNextLevel: Math.max(0, (user.level * 500) - user.xpTotal),

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
    const currentUser = store.getUserById(authReq.userId);

    if (!currentUser) {
        throw new NotFoundError('User not found');
    }

    const allUsers = store.getAllUsers()
        .map(u => ({
            id: u.id,
            firstName: (u as any).firstName, // Handle dynamic property if exists
            level: u.level,
            xpTotal: u.xpTotal
        }))
        .sort((a, b) => b.xpTotal - a.xpTotal);

    const currentUserRank = allUsers.findIndex(u => u.id === authReq.userId) + 1;

    res.status(200).json({
        success: true,
        currentUserRank,
        totalUsers: allUsers.length,
        topUsers: allUsers.slice(0, 5),
        userStats: allUsers.find(u => u.id === authReq.userId)
    });
}));

export default router;
