/**
 * Lessons Routes
 */

import express from 'express';
import { store } from '../data/store.js';
import { verifyToken, optionalAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/lessons
 * Get all lessons with optional filtering
 */
router.get('/', optionalAuth, asyncHandler((req, res) => {
    const difficulty = req.query.difficulty;
    let lessons = store.getAllLessons();

    if (difficulty) {
        lessons = lessons.filter(l => l.difficulty === difficulty);
    }

    // Add completion status for authenticated users
    if (req.userId) {
        const user = store.getUserById(req.userId);
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
router.get('/:id', optionalAuth, asyncHandler((req, res) => {
    const lesson = store.getLessonById(req.params.id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    // Add completion status
    let lessonData = { ...lesson };
    if (req.userId) {
        const user = store.getUserById(req.userId);
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
router.post('/:id/complete', verifyToken, asyncHandler((req, res) => {
    const lesson = store.getLessonById(req.params.id);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    const user = store.completeLesson(req.userId, req.params.id);

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
router.post('/', verifyToken, asyncHandler((req, res) => {
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
router.put('/:id', verifyToken, asyncHandler((req, res) => {
    const lesson = store.updateLesson(req.params.id, req.body);

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
