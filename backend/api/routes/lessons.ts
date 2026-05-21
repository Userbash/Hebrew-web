/**
 * Lessons Routes
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken, optionalAuth, requireAdmin, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/lessons
 * Get all lessons with optional filtering
 */
router.get('/', optionalAuth, asyncHandler(async (req: Request, res: Response) => {
    const difficulty = req.query.difficulty as string | undefined;
    let lessons = await db.getAllLessons();

    if (difficulty) {
        lessons = lessons.filter((l: any) => l.difficulty === difficulty);
    }

    // Add completion status for authenticated users
    const authReq = req as RequestWithAuth;
    if (authReq.userId) {
        const user = await db.getUserById(authReq.userId);
        if (user) {
            // Check acquisition from user_items
            const acquisitionsRes = await db.query('SELECT item_id FROM user_items WHERE user_id = $1', [authReq.userId]);
            const acquiredIds = acquisitionsRes.rows.map(r => r.item_id);
            lessons = lessons.map((lesson: any) => ({
                ...lesson,
                isCompleted: acquiredIds.includes(lesson.id)
            }));
        }
    }

    res.status(200).json({
        success: true,
        lessons,
        count: lessons.length
    });
}));

/**
 * GET /api/lessons/:id
 * Get lesson by ID
 */
router.get('/:id', optionalAuth, asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id as string;
    const lesson = await db.getLessonById(id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    // Add completion status
    let lessonData: any = { ...lesson };
    const authReq = req as RequestWithAuth;
    if (authReq.userId) {
        const acquisitionsRes = await db.query('SELECT 1 FROM user_items WHERE user_id = $1 AND item_id = $2', [authReq.userId, id]);
        lessonData.isCompleted = (acquisitionsRes.rowCount ?? 0) > 0;
    }

    res.status(200).json({
        success: true,
        lesson: lessonData
    });
}));

/**
 * POST /api/lessons/:id/complete
 * Mark lesson as completed
 */
router.post('/:id/complete', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id as string;
    const lesson = await db.getLessonById(id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    const authReq = req as RequestWithAuth;
    const userProgress = await db.completeLesson(authReq.userId, id);

    res.status(200).json({
        success: true,
        message: 'Lesson marked as completed',
        xpEarned: userProgress.xpEarned,
        userLevel: userProgress.level,
        userXp: userProgress.xp_total
    });
}));

/**
 * POST /api/lessons
 * Create new lesson (admin only - demo endpoint)
 */
router.post('/', ...requireAdmin, asyncHandler(async (req: Request, res: Response) => {
    const { title, description, difficulty, duration, content, xpReward } = req.body;

    if (!title || !description || !difficulty) {
        throw new ValidationError('Title, description, and difficulty are required');
    }

    const lesson = await db.createLesson({
        title,
        description,
        difficulty,
        duration: duration || 15,
        content: content || [],
        xpReward: xpReward || 50
    });

    res.status(201).json({
        success: true,
        message: 'Lesson created successfully',
        lesson
    });
}));

/**
 * PUT /api/lessons/:id
 * Update lesson
 */
router.put('/:id', ...requireAdmin, asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id as string;
    const lesson = await db.updateLesson(id, req.body);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    res.status(200).json({
        success: true,
        message: 'Lesson updated successfully',
        lesson
    });
}));

export default router;
