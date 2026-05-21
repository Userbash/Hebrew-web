/**
 * User Routes
 */

import express, { Request, Response } from 'express';
import { store } from '../data/store.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/users/profile
 * Get current user profile
 */
router.get('/profile', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const user = store.getUserById(authReq.userId);

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
router.put('/profile', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const { firstName, lastName, avatar } = req.body;
    const authReq = req as RequestWithAuth;

    const user = store.updateUser(authReq.userId, {
        firstName: firstName || undefined,
        lastName: lastName || undefined,
        // @ts-ignore
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
router.get('/:id', asyncHandler(async (req: Request, res: Response) => {
    const id = Array.isArray(req.params.id) ? req.params.id[0] : req.params.id;
    const user = store.getUserById(id);

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
router.get('/stats/leaderboard', asyncHandler(async (req: Request, res: Response) => {
    const limit = parseInt(req.query.limit as string) || 10;

    const users = store.getAllUsers()
        .map((u: any) => ({
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
