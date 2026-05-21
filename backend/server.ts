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
import { telemetryMiddleware } from './api/middleware/telemetry.js';
import { apiLimiter } from './api/middleware/security.js';

// Initialize Express app
const app = express();
app.set('trust proxy', 1);
const PORT: string | number = process.env.BACKEND_PORT || 3001;

// ═══════════════════════════════════════════════════════════════════════════
// MIDDLEWARE
// ═══════════════════════════════════════════════════════════════════════════

app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", "http://localhost:3001", "http://localhost:8081"]
        }
    }
}));
app.use(cookieParser());
app.use(compression());
app.use(apiLimiter); // Protect all routes by default

const configuredOrigins = (process.env.CORS_ORIGINS || '')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);

const defaultOrigins = process.env.NODE_ENV === 'production'
    ? [process.env.DOMAIN_NAME ? `https://${process.env.DOMAIN_NAME}` : ''].filter(Boolean)
    : ['http://localhost:5173', 'http://localhost:3000', 'http://localhost:8081'];

const allowedOrigins = configuredOrigins.length > 0 ? configuredOrigins : defaultOrigins;

app.use(cors({
    origin: (origin, callback) => {
        if (!origin || allowedOrigins.includes(origin)) {
            callback(null, true);
            return;
        }

        callback(new Error('CORS origin denied'));
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));
app.use(telemetryMiddleware);
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
