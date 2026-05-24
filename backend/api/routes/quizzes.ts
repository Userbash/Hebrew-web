/**
 * Quizzes Routes
 */

import express, { Request, Response } from 'express';
import { db, ItemMetadata } from '../data/db.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import { requirePermission } from '../middleware/authorization.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

type SupportedAnswer = string | number | boolean | null;

const normalizeAnswers = (input: unknown): SupportedAnswer[] => {
    if (!Array.isArray(input)) {
        throw new ValidationError('Answers must be an array');
    }

    if (input.length === 0) {
        throw new ValidationError('Answers array must not be empty');
    }

    return input.map((value) => {
        if (
            value === null ||
            typeof value === 'string' ||
            typeof value === 'number' ||
            typeof value === 'boolean'
        ) {
            return value;
        }

        throw new ValidationError('Answer values must be string, number, boolean, or null');
    });
};

const extractCorrectAnswers = (metadata: ItemMetadata): SupportedAnswer[] => {
    if (Array.isArray(metadata.correctAnswers) && metadata.correctAnswers.length > 0) {
        return metadata.correctAnswers;
    }

    if (Array.isArray(metadata.questions)) {
        const fromQuestions = metadata.questions
            .map((question) => {
                if (!question || typeof question !== 'object' || Array.isArray(question)) {
                    return undefined;
                }

                return (question as { correctAnswer?: SupportedAnswer }).correctAnswer;
            })
            .filter((answer): answer is SupportedAnswer => answer !== undefined);

        if (fromQuestions.length > 0) {
            return fromQuestions;
        }
    }

    throw new ValidationError('Quiz is missing answer key configuration');
};

const calculateScore = (given: SupportedAnswer[], expected: SupportedAnswer[]) => {
    const questionCount = expected.length;
    const boundedAnswers = given.slice(0, questionCount);

    let correct = 0;
    for (let index = 0; index < questionCount; index += 1) {
        if (boundedAnswers[index] === expected[index]) {
            correct += 1;
        }
    }

    const score = Math.round((correct / questionCount) * 100);
    return {
        score,
        totalQuestions: questionCount,
        correctAnswers: correct,
    };
};

/**
 * GET /api/quizzes
 * Get quizzes with optional difficulty/lesson filter.
 */
router.get('/', verifyToken, requirePermission('quizzes', 'read', 'any'), asyncHandler(async (req: Request, res: Response) => {
    const difficulty = typeof req.query.difficulty === 'string' ? req.query.difficulty.trim() : '';
    const lessonId = typeof req.query.lessonId === 'string' ? req.query.lessonId.trim() : '';

    let quizzes = await db.getAllQuizzes();

    if (difficulty) {
        quizzes = quizzes.filter((quiz) => quiz.metadata?.difficulty === difficulty);
    }

    if (lessonId) {
        quizzes = quizzes.filter((quiz) => quiz.metadata?.lessonId === lessonId);
    }

    res.status(200).json({
        success: true,
        quizzes,
        count: quizzes.length,
    });
}));

/**
 * GET /api/quizzes/:id
 * Get quiz by ID.
 */
router.get('/:id', verifyToken, requirePermission('quizzes', 'read', 'any'), asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const quiz = await db.getQuizById(id);

    if (!quiz) {
        throw new NotFoundError('Quiz not found');
    }

    res.status(200).json({
        success: true,
        quiz,
    });
}));

/**
 * POST /api/quizzes/:id/submit
 * Grades answers and awards XP only for passed attempts.
 */
router.post('/:id/submit', verifyToken, requirePermission('quizzes', 'update', 'own'), asyncHandler(async (req: Request, res: Response) => {
    const answers = normalizeAnswers(req.body?.answers);
    const id = req.params.id;

    const quiz = await db.getQuizById(id);
    if (!quiz) {
        throw new NotFoundError('Quiz not found');
    }

    const expectedAnswers = extractCorrectAnswers(quiz.metadata || {});

    if (answers.length !== expectedAnswers.length) {
        throw new ValidationError(`Answers count mismatch: expected ${expectedAnswers.length}`);
    }

    const { score, totalQuestions, correctAnswers } = calculateScore(answers, expectedAnswers);
    const passingScore = typeof quiz.metadata?.passingScore === 'number' ? quiz.metadata.passingScore : 70;
    const passed = score >= passingScore;

    const authReq = req as RequestWithAuth;
    const attempt = await db.recordQuizAttempt(authReq.userId, id, answers, score, totalQuestions, passed);

    const xpReward = typeof quiz.metadata?.xpReward === 'number' ? quiz.metadata.xpReward : 100;
    const progress = passed
        ? await db.completeItemWithXp(authReq.userId, id, xpReward)
        : { xpEarned: 0, xp_total: 0, level: 0 };

    const userSnapshot = await db.getUserById(authReq.userId);

    res.status(200).json({
        success: true,
        message: 'Quiz submitted successfully',
        passed,
        xpEarned: progress.xpEarned,
        userXp: userSnapshot?.xp_total ?? progress.xp_total,
        userLevel: userSnapshot?.level ?? progress.level,
        attempt: {
            id: attempt.id,
            score,
            totalQuestions,
            correctAnswers,
            passingScore,
            passed,
            submittedAt: attempt.submitted_at,
        },
    });
}));

/**
 * GET /api/quizzes/:id/attempts
 * Returns current user's recent attempts for a quiz.
 */
router.get('/:id/attempts', verifyToken, requirePermission('progress', 'read', 'own'), asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const quiz = await db.getQuizById(id);
    if (!quiz) {
        throw new NotFoundError('Quiz not found');
    }

    const authReq = req as RequestWithAuth;
    const attempts = await db.getQuizAttemptsForUser(authReq.userId, id);

    res.status(200).json({
        success: true,
        attempts: attempts.map((attempt) => ({
            id: attempt.id,
            score: attempt.score,
            totalQuestions: attempt.total_questions,
            passed: attempt.passed,
            submittedAt: attempt.submitted_at,
        })),
        count: attempts.length,
    });
}));

export default router;
