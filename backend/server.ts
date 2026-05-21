/**
 * Hebrew AI 2025 - Backend Server
 * Express.js server with in-memory data store
 */

import express, { Request, Response } from 'express';
import cors from 'cors';
import compression from 'compression';
import helmet from 'helmet';
import cookieParser from 'cookie-parser';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { config } from 'dotenv';

// Get current directory
const __filename: string = fileURLToPath(import.meta.url);
const __dirname: string = dirname(__filename);

// Load environment variables
config({ path: join(__dirname, '..', '.env') });

// Import routes
import authRoutes from './api/routes/auth.js';
import itemsRoutes from './api/routes/items.js';
import lessonsRoutes from './api/routes/lessons.js';
import quizzesRoutes from './api/routes/quizzes.js';
import dictionaryRoutes from './api/routes/dictionary.js';
import progressRoutes from './api/routes/progress.js';
import userRoutes from './api/routes/users.js';

// Import middleware
import { errorHandler, notFound } from './api/middleware/errorHandler.js';

// Initialize Express app
const app = express();
const PORT: string | number = process.env.BACKEND_PORT || 3001;

// ═══════════════════════════════════════════════════════════════════════════
// MIDDLEWARE
// ═══════════════════════════════════════════════════════════════════════════

app.use(helmet());
app.use(cookieParser());
app.use(compression());

app.use(cors({
    origin: true, // Временно разрешаем все источники для отладки с куками
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));
app.use(express.static(join(__dirname, '..', 'public')));

// ═══════════════════════════════════════════════════════════════════════════
// API ROUTES
// ═══════════════════════════════════════════════════════════════════════════

app.get('/api/health', (req: Request, res: Response) => {
    res.status(200).json({ status: 'OK' });
});

app.use('/api/auth', authRoutes);
app.use('/api/items', itemsRoutes);
app.use('/api/users', userRoutes);
app.use('/api/lessons', lessonsRoutes);
app.use('/api/quizzes', quizzesRoutes);
app.use('/api/dictionary', dictionaryRoutes);
app.use('/api/progress', progressRoutes);

app.use(notFound);
app.use(errorHandler);

const server = app.listen(PORT, () => {
    console.log(`Backend Server Started on http://localhost:${PORT}`);
});

export default app;
