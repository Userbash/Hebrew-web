/**
 * Lessons Routes
 */

import express, { Request, Response } from 'express';
import { store } from '../data/store.js';
import { verifyToken, optionalAuth, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/lessons
 * Get all lessons with optional filtering
 */
router.get('/', optionalAuth, asyncHandler(async (req: Request, res: Response) => {
    const difficulty = req.query.difficulty as string | undefined;
    let lessons = store.getAllLessons();

    if (difficulty) {
        lessons = lessons.filter(l => l.difficulty === difficulty);
    }

    // Add completion status for authenticated users
    const authReq = req as RequestWithAuth;
    if (authReq.userId) {
        const user = store.getUserById(authReq.userId);
        if (user) {
            lessons = lessons.map(lesson => ({
                ...lesson,
                isCompleted: user.lessonsCompleted.includes(lesson.id)
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
    const lesson = store.getLessonById(id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    // Add completion status
    let lessonData: any = { ...lesson };
    const authReq = req as RequestWithAuth;
    if (authReq.userId) {
        const user = store.getUserById(authReq.userId);
        if (user) {
            lessonData.isCompleted = user.lessonsCompleted.includes(lesson.id);
        }
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
    const lesson = store.getLessonById(id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    const authReq = req as RequestWithAuth;
    const user = store.completeLesson(authReq.userId, id);

    if (!user) {
        throw new NotFoundError('User not found');
    }

    res.status(200).json({
        success: true,
        message: 'Lesson marked as completed',
        xpEarned: lesson.xpReward,
        userLevel: user.level,
        userXp: user.xpTotal
    });
}));

/**
 * POST /api/lessons
 * Create new lesson (admin only - demo endpoint)
 */
router.post('/', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const { title, description, difficulty, duration, content, xpReward } = req.body;

    if (!title || !description || !difficulty) {
        throw new ValidationError('Title, description, and difficulty are required');
    }

    const lesson = store.createLesson({
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
router.put('/:id', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id as string;
    const lesson = store.updateLesson(id, req.body);

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
