/**
 * User Routes
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/users/profile
 * Get current user profile
 */
router.get('/profile', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const user = await db.getUserById(authReq.userId);

    if (!user) {
        throw new NotFoundError('User not found');
    }

    res.status(200).json({
        success: true,
        user
    });
}));

/**
 * PUT /api/users/profile
 * Update user profile
 */
router.put('/profile', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const { firstName, lastName } = req.body;
    const authReq = req as RequestWithAuth;

    const query = `
        UPDATE users 
        SET first_name = COALESCE($1, first_name),
            last_name = COALESCE($2, last_name),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $3 AND deleted_at IS NULL
        RETURNING id, email, username, first_name, last_name, role, xp_total, level, created_at, updated_at;
    `;
    const resDb = await db.query(query, [firstName, lastName, authReq.userId]);
    const user = resDb.rows[0];

    if (!user) {
        throw new NotFoundError('User not found');
    }

    await db.cacheUser(user);

    res.status(200).json({
        success: true,
        message: 'Profile updated successfully',
        user
    });
}));

/**
 * GET /api/users/stats/leaderboard
 * Get top users by XP
 */
router.get('/stats/leaderboard', asyncHandler(async (req: Request, res: Response) => {
    const limit = parseInt(req.query.limit as string) || 10;

    const query = `
        SELECT id, username, first_name, last_name, xp_total, level
        FROM users
        WHERE deleted_at IS NULL
        ORDER BY xp_total DESC
        LIMIT $1;
    `;
    const resDb = await db.query(query, [limit]);

    res.status(200).json({
        success: true,
        leaderboard: resDb.rows,
        count: resDb.rows.length
    });
}));

/**
 * GET /api/users/:id
 * Get user by ID (public profile)
 */
router.get('/:id', asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const user = await db.getUserById(id);

    if (!user) {
        throw new NotFoundError('User not found');
    }

    res.status(200).json({
        success: true,
        user
    });
}));

export default router;
