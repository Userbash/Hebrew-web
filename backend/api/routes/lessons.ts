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

    res.status(200).json({ success: true, data: { lessons, count: lessons.length } });
}));

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

    res.status(200).json({ success: true, data: { lesson: lessonData } });
}));

router.post('/:id/start', verifyToken, requirePermission('progress', 'read', 'own'), asyncHandler(async (req: Request, res: Response) => {
    const lessonId = req.params.id as string;
    const lesson = await db.getLessonById(lessonId);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    const authReq = req as RequestWithAuth;
    await db.startLessonProgress(authReq.userId, lessonId);

    res.status(200).json({ success: true, data: { lessonId, status: 'in_progress' } });
}));

router.post('/:id/progress', verifyToken, requirePermission('progress', 'read', 'own'), asyncHandler(async (req: Request, res: Response) => {
    const lessonId = req.params.id as string;
    const lesson = await db.getLessonById(lessonId);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    const progressPercent = Number(req.body?.progressPercent);
    if (!Number.isFinite(progressPercent)) {
        throw new ValidationError('progressPercent must be a number');
    }

    const authReq = req as RequestWithAuth;
    const state = await db.updateLessonProgressPercent(authReq.userId, lessonId, progressPercent);

    res.status(200).json({
        success: true,
        data: {
            lessonId,
            status: state.status,
            progressPercent: state.progress_percent,
        },
    });
}));

router.get('/:id/progress', verifyToken, requirePermission('progress', 'read', 'own'), asyncHandler(async (req: Request, res: Response) => {
    const lessonId = req.params.id as string;
    const authReq = req as RequestWithAuth;

    const rows = await db.query(
        `SELECT status, progress_percent, started_at, last_activity_at, completed_at
         FROM user_lesson_progress
         WHERE user_id = $1 AND lesson_id = $2
         LIMIT 1`,
        [authReq.userId, lessonId]
    );

    const row = rows.rows[0] || null;
    res.status(200).json({ success: true, data: { lessonId, progress: row } });
}));

router.post('/:id/complete', verifyToken, requirePermission('progress', 'read', 'own'), asyncHandler(async (req: Request, res: Response) => {
    const lessonId = req.params.id as string;
    const lesson = await db.getLessonById(lessonId);

    if (!lesson) {
        throw new NotFoundError('Lesson not found');
    }

    const authReq = req as RequestWithAuth;
    const xpReward = typeof lesson.metadata?.xpReward === 'number' ? lesson.metadata.xpReward : 50;
    const result = await db.completeLessonWorkflow(authReq.userId, lessonId, xpReward);

    res.status(200).json({
        success: true,
        data: {
            lessonId,
            status: 'completed',
            xpEarned: result.xpEarned,
            userLevel: result.level,
            userXp: result.xp_total,
        },
    });
}));

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

    res.status(201).json({ success: true, data: { lesson } });
}));

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

    res.status(200).json({ success: true, data: { lesson } });
}));

export default router;
