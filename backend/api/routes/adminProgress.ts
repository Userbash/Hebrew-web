import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { asyncHandler } from '../middleware/errorHandler.js';

const router = express.Router();

router.get('/overview', asyncHandler(async (_req: Request, res: Response) => {
  const summary = await db.getAdminProgressOverview();

  res.status(200).json({
    success: true,
    data: {
      summary: {
        usersTotal: Number(summary?.users_total || 0),
        lessonsCompletedTotal: Number(summary?.lessons_completed_total || 0),
        quizzesCompletedTotal: Number(summary?.quizzes_completed_total || 0),
        activeLessonsTotal: Number(summary?.active_lessons_total || 0),
      },
    },
  });
}));

router.get('/users', asyncHandler(async (req: Request, res: Response) => {
  const limit = Number(req.query.limit || 50);
  const users = await db.getAdminProgressUsers(Number.isFinite(limit) ? limit : 50);
  res.status(200).json({ success: true, data: { users } });
}));

router.get('/users/:userId', asyncHandler(async (req: Request, res: Response) => {
  const detail = await db.getAdminProgressUserDetail(req.params.userId);
  res.status(200).json({ success: true, data: detail });
}));

router.get('/lessons/:lessonId', asyncHandler(async (req: Request, res: Response) => {
  const analytics = await db.getAdminLessonProgressAnalytics(req.params.lessonId);
  res.status(200).json({ success: true, data: { analytics } });
}));

export default router;
