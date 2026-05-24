/**
 * Lessons Routes
 */

import express, { Request, Response } from 'express';
import { db, ItemRow } from '../data/db.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { requirePermission } from '../middleware/authorization.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

const withCompletionFlag = (lessons: ItemRow[], acquiredIds: Set<string>) => {
    return lessons.map((lesson) => ({
        ...lesson,
        isCompleted: acquiredIds.has(lesson.id),
    }));
};

/**
 * GET /api/lessons
 * Get all lessons with optional difficulty filter.
 */
router.get('/', verifyToken, requirePermission('lessons', 'read', 'any'), asyncHandler(async (req: Request, res: Response) => {
    const difficulty = typeof req.query.difficulty === 'string' ? req.query.difficulty.trim() : '';

    let lessons = await db.getAllLessons();

    if (difficulty) {
        lessons = lessons.filter((lesson) => lesson.metadata?.difficulty === difficulty);
    }

    const authReq = req as RequestWithAuth;
    if (authReq.userId) {
        const acquisitionsRes = await db.query('SELECT item_id FROM user_items WHERE user_id = $1', [authReq.userId]);
        const acquiredIds = new Set<string>(acquisitionsRes.rows.map((row: { item_id: string }) => row.item_id));
        lessons = withCompletionFlag(lessons, acquiredIds);
    }

    res.status(200).json({
        success: true,
        lessons,
        count: lessons.length,
    });
}));

/**
 * GET /api/lessons/:id
 * Get lesson by ID.
 */
router.get('/:id', verifyToken, requirePermission('lessons', 'read', 'any'), asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id as string;
    const lesson = await db.getLessonById(id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    let lessonData: ItemRow & { isCompleted?: boolean } = { ...lesson };
    const authReq = req as RequestWithAuth;
    if (authReq.userId) {
        const acquisitionsRes = await db.query('SELECT 1 FROM user_items WHERE user_id = $1 AND item_id = $2', [authReq.userId, id]);
        lessonData = {
            ...lessonData,
            isCompleted: (acquisitionsRes.rowCount ?? 0) > 0,
        };
    }

    res.status(200).json({
        success: true,
        lesson: lessonData,
    });
}));

/**
 * POST /api/lessons/:id/complete
 * Marks lesson as completed and applies XP once.
 */
router.post('/:id/complete', verifyToken, requirePermission('progress', 'read', 'own'), asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id as string;
    const lesson = await db.getLessonById(id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    const authReq = req as RequestWithAuth;
    const xpReward = typeof lesson.metadata?.xpReward === 'number' ? lesson.metadata.xpReward : 50;
    const userProgress = await db.completeItemWithXp(authReq.userId, id, xpReward);

    res.status(200).json({
        success: true,
        message: 'Lesson marked as completed',
        xpEarned: userProgress.xpEarned,
        userLevel: userProgress.level,
        userXp: userProgress.xp_total,
    });
}));

/**
 * POST /api/lessons
 * Create lesson (admin only).
 */
router.post('/', verifyToken, requirePermission('lessons', 'create', 'any'), asyncHandler(async (req: Request, res: Response) => {
    const { title, description, difficulty, duration, content, xpReward } = req.body;

    if (!title || !description || !difficulty) {
        throw new ValidationError('Title, description, and difficulty are required');
    }

    const lesson = await db.createLesson({
        title: String(title),
        description: String(description),
        difficulty: String(difficulty),
        duration: typeof duration === 'number' ? duration : 15,
        content: Array.isArray(content) ? content : [],
        xpReward: typeof xpReward === 'number' ? xpReward : 50,
    });

    res.status(201).json({
        success: true,
        message: 'Lesson created successfully',
        lesson,
    });
}));

/**
 * PUT /api/lessons/:id
 * Update lesson.
 */
router.put('/:id', verifyToken, requirePermission('lessons', 'update', 'any'), asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id as string;

    const lesson = await db.updateLesson(id, {
        title: typeof req.body?.title === 'string' ? req.body.title : undefined,
        description: typeof req.body?.description === 'string' ? req.body.description : undefined,
        difficulty: typeof req.body?.difficulty === 'string' ? req.body.difficulty : undefined,
        duration: typeof req.body?.duration === 'number' ? req.body.duration : undefined,
        content: Array.isArray(req.body?.content) ? req.body.content : undefined,
        xpReward: typeof req.body?.xpReward === 'number' ? req.body.xpReward : undefined,
    });

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    res.status(200).json({
        success: true,
        message: 'Lesson updated successfully',
        lesson,
    });
}));

export default router;
