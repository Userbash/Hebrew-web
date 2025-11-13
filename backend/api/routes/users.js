/**
 * User Routes
 */

import express from 'express';
import { store } from '../data/store.js';
import { verifyToken } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/users/profile
 * Get current user profile
 */
router.get('/profile', verifyToken, asyncHandler((req, res) => {
    const user = store.getUserById(req.userId);

    if (!user) {
        throw new NotFoundError('User not found');
    }

    const { password: _, ...userWithoutPassword } = user;

    res.status(200).json({
        success: true,
        user: userWithoutPassword
    });
}));

/**
 * PUT /api/users/profile
 * Update user profile
 */
router.put('/profile', verifyToken, asyncHandler((req, res) => {
    const { firstName, lastName, avatar } = req.body;

    const user = store.updateUser(req.userId, {
        firstName: firstName || undefined,
        lastName: lastName || undefined,
        avatar: avatar || undefined
    });

    if (!user) {
        throw new NotFoundError('User not found');
    }

    const { password: _, ...userWithoutPassword } = user;

    res.status(200).json({
        success: true,
        message: 'Profile updated successfully',
        user: userWithoutPassword
    });
}));

/**
 * GET /api/users/:id
 * Get user by ID (public profile)
 */
router.get('/:id', asyncHandler((req, res) => {
    const user = store.getUserById(req.params.id);

    if (!user) {
        throw new NotFoundError('User not found');
    }

    const { password: _, ...userWithoutPassword } = user;

    res.status(200).json({
        success: true,
        user: userWithoutPassword
    });
}));

/**
 * GET /api/users/stats/leaderboard
 * Get top users by XP
 */
router.get('/stats/leaderboard', asyncHandler((req, res) => {
    const limit = parseInt(req.query.limit) || 10;

    const users = store.getAllUsers()
        .map(u => ({
            id: u.id,
            firstName: u.firstName,
            lastName: u.lastName,
            xpTotal: u.xpTotal,
            level: u.level,
            lessonsCompleted: u.lessonsCompleted.length,
            avatar: u.avatar
        }))
        .sort((a, b) => b.xpTotal - a.xpTotal)
        .slice(0, limit);

    res.status(200).json({
        success: true,
        leaderboard: users,
        count: users.length
    });
}));

export default router;
