/**
 * Quizzes Routes
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken, optionalAuth, RequestWithAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/quizzes
 * Get all quizzes with optional filtering
 */
router.get('/', optionalAuth, asyncHandler(async (req: Request, res: Response) => {
    const difficulty = req.query.difficulty as string | undefined;
    const lessonId = req.query.lessonId as string | undefined;

    let quizzes = await db.getAllQuizzes();

    if (difficulty) {
        quizzes = quizzes.filter((q: any) => q.difficulty === difficulty);
    }

    if (lessonId) {
        quizzes = quizzes.filter((q: any) => q.lessonId === lessonId);
    }

    res.status(200).json({
        success: true,
        quizzes,
        count: quizzes.length
    });
}));

/**
 * GET /api/quizzes/:id
 * Get quiz by ID
 */
router.get('/:id', optionalAuth, asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const quiz = await db.getQuizById(id);

    if (!quiz) {
        throw new NotFoundError('Quiz not found');
    }

    res.status(200).json({
        success: true,
        quiz
    });
}));

/**
 * POST /api/quizzes/:id/submit
 */
router.post('/:id/submit', verifyToken, asyncHandler(async (req: Request, res: Response) => {
    const { answers } = req.body;
    const id = req.params.id;

    if (!answers || typeof answers !== 'object') {
        throw new ValidationError('Answers are required');
    }

    const quiz = await db.getQuizById(id);
    if (!quiz) {
        throw new NotFoundError('Quiz not found');
    }

    const authReq = req as RequestWithAuth;
    // Quiz scoring is still simplified; XP is idempotent per user/quiz.
    const userProgress = await db.completeItemWithXp(authReq.userId, id, 100);

    res.status(200).json({
        success: true,
        message: 'Quiz submitted successfully',
        xpEarned: userProgress.xpEarned,
        userXp: userProgress.xp_total,
        userLevel: userProgress.level,
        passed: true
    });
}));

export default router;
