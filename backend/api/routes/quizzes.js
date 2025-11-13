/**
 * Quizzes Routes
 */

import express from 'express';
import { store } from '../data/store.js';
import { verifyToken, optionalAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/quizzes
 * Get all quizzes with optional filtering
 */
router.get('/', optionalAuth, asyncHandler((req, res) => {
    const difficulty = req.query.difficulty;
    const lessonId = req.query.lessonId;

    let quizzes = store.getAllQuizzes();

    if (difficulty) {
        quizzes = quizzes.filter(q => q.difficulty === difficulty);
    }

    if (lessonId) {
        quizzes = quizzes.filter(q => q.lessonId === lessonId);
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
router.get('/:id', optionalAuth, asyncHandler((req, res) => {
    const quiz = store.getQuizById(req.params.id);

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
 * Submit quiz attempt and get results
 */
router.post('/:id/submit', verifyToken, asyncHandler((req, res) => {
    const { answers } = req.body;

    if (!answers || !Array.isArray(answers)) {
        throw new ValidationError('Answers array is required');
    }

    const quiz = store.getQuizById(req.params.id);
    if (!quiz) {
        throw new NotFoundError('Quiz not found');
    }

    if (answers.length !== quiz.questions.length) {
        throw new ValidationError('Number of answers must match number of questions');
    }

    const attempt = store.submitQuizAttempt(req.userId, req.params.id, answers);

    const user = store.getUserById(req.userId);

    res.status(200).json({
        success: true,
        message: 'Quiz submitted successfully',
        attempt,
        userXp: user.xpTotal,
        userLevel: user.level,
        passed: attempt.passed
    });
}));

/**
 * GET /api/quizzes/:id/attempts
 * Get user's quiz attempts
 */
router.get('/:id/attempts', verifyToken, asyncHandler((req, res) => {
    const attempts = store.getQuizAttempts(req.userId, req.params.id);

    res.status(200).json({
        success: true,
        attempts,
        count: attempts.length,
        bestScore: attempts.length > 0 ? Math.max(...attempts.map(a => a.score)) : 0
    });
}));

/**
 * POST /api/quizzes
 * Create new quiz (admin only)
 */
router.post('/', verifyToken, asyncHandler((req, res) => {
    const { title, description, difficulty, lessonId, questions, passingScore, xpReward } = req.body;

    if (!title || !questions || !Array.isArray(questions)) {
        throw new ValidationError('Title and questions array are required');
    }

    const quiz = store.createQuiz({
        title,
        description: description || '',
        difficulty: difficulty || 'medium',
        lessonId: lessonId || null,
        questions,
        passingScore: passingScore || 70,
        xpReward: xpReward || 100
    });

    res.status(201).json({
        success: true,
        message: 'Quiz created successfully',
        quiz
    });
}));

export default router;
