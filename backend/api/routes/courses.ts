import express, { Request, Response } from 'express';

const router = express.Router();

// Mock data for Language School courses
const MOCK_COURSES = [
  {
    id: '1',
    title: 'Modern Hebrew for Beginners',
    description: 'Master the basics of reading, writing and speaking.',
    level: 'Beginner',
    duration: '12 weeks',
    students: 124,
    rating: 4.8
  },
  {
    id: '2',
    title: 'Intermediate Conversational Hebrew',
    description: 'Focused on daily communication and fluency.',
    level: 'Intermediate',
    duration: '10 weeks',
    students: 89,
    rating: 4.9
  },
  {
    id: '3',
    title: 'Advanced Business Hebrew',
    description: 'Professional terminology and formal communication.',
    level: 'Advanced',
    duration: '8 weeks',
    students: 45,
    rating: 4.7
  }
];

/**
 * @route GET /api/courses
 * @desc Get all available courses
 */
router.get('/', (req: Request, res: Response) => {
  res.status(200).json(MOCK_COURSES);
});

export default router;
