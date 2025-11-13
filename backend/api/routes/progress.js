/**
 * Progress Routes
 */

import express from 'express';
import { store } from '../data/store.js';
import { verifyToken } from '../middleware/auth.js';
import { asyncHandler, NotFoundError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/progress
 * Get current user's progress
 */
router.get('/', verifyToken, asyncHandler((req, res) => {
    const progress = store.getUserProgress(req.userId);

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
router.get('/:userId', asyncHandler((req, res) => {
    const progress = store.getUserProgress(req.params.userId);

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
router.get('/stats/summary', verifyToken, asyncHandler((req, res) => {
    const user = store.getUserById(req.userId);

    if (!user) {
        throw new NotFoundError('User not found');
    }

    const allLessons = store.getAllLessons();
    const allQuizzes = store.getAllQuizzes();
    const userProgress = store.getUserProgress(req.userId);

    const completionStats = {
        lessonsCompleted: user.lessonsCompleted.length,
        lessonsTotal: allLessons.length,
        lessonsPercentage: Math.round((user.lessonsCompleted.length / allLessons.length) * 100),

        quizzesCompleted: user.quizzesCompleted.length,
        quizzesTotal: allQuizzes.length,
        quizzesPercentage: Math.round((user.quizzesCompleted.length / allQuizzes.length) * 100),

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
router.get('/stats/comparison', verifyToken, asyncHandler((req, res) => {
    const currentUser = store.getUserById(req.userId);

    if (!currentUser) {
        throw new NotFoundError('User not found');
    }

    const allUsers = store.getAllUsers()
        .map(u => ({
            id: u.id,
            firstName: u.firstName,
            level: u.level,
            xpTotal: u.xpTotal
        }))
        .sort((a, b) => b.xpTotal - a.xpTotal);

    const currentUserRank = allUsers.findIndex(u => u.id === req.userId) + 1;

    res.status(200).json({
        success: true,
        currentUserRank,
        totalUsers: allUsers.length,
        topUsers: allUsers.slice(0, 5),
        userStats: allUsers.find(u => u.id === req.userId)
    });
}));

export default router;
