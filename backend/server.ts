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
import publicationsRoutes from './api/routes/publications.js';
import progressRoutes from './api/routes/progress.js';
import userRoutes from './api/routes/users.js';
import accessControlRoutes from './api/routes/accessControl.js';
import adminRoutes from './api/routes/admin.js';

// Import middleware
import { errorHandler, notFound } from './api/middleware/errorHandler.js';
import { telemetryMiddleware } from './api/middleware/telemetry.js';
import { auditTrailMiddleware } from './api/middleware/auditTrail.js';
import { apiLimiter } from './api/middleware/security.js';
import {
    initEmailDomainBlocklistAutomation,
    getEmailDomainBlocklistStatus,
} from './api/security/emailDomainBlocklist.js';
import { runMigrations } from './api/data/migrations.js';

// Initialize Express app
const app = express();
app.set('trust proxy', 1);
const PORT: string | number = process.env.BACKEND_PORT || 3001;

const normalizeOrigin = (origin: string) => {
    try {
        const parsed = new URL(origin);
        return `${parsed.protocol}//${parsed.host}`.toLowerCase();
    } catch {
        return origin.trim().toLowerCase().replace(/\/+$/, '');
    }
};

const wildcardPatternToRegExp = (pattern: string) => {
    const escaped = pattern
        .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
        .replace(/\*/g, '.*');
    return new RegExp(`^${escaped}$`, 'i');
};

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
            connectSrc: [
                "'self'",
                'http://localhost:3001',
                'http://127.0.0.1:3001',
                'http://localhost:8081',
                'http://127.0.0.1:8081',
            ]
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

const fallbackOrigins = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8081',
    'http://127.0.0.1:8081',
];

const productionOrigins = [
    process.env.DOMAIN_NAME ? `https://${process.env.DOMAIN_NAME}` : '',
].filter(Boolean);

const defaultOrigins = process.env.NODE_ENV === 'production'
    ? (productionOrigins.length > 0 ? productionOrigins : fallbackOrigins)
    : fallbackOrigins;

const allowedOriginPatterns = (configuredOrigins.length > 0 ? configuredOrigins : defaultOrigins)
    .map((origin) => normalizeOrigin(origin));

const allowedOriginRegexes = allowedOriginPatterns.map((pattern) => wildcardPatternToRegExp(pattern));

const isAllowedOrigin = (origin: string) => {
    const normalizedOrigin = normalizeOrigin(origin);
    return allowedOriginRegexes.some((regex) => regex.test(normalizedOrigin));
};

app.use(cors({
    origin: (origin, callback) => {
        if (!origin || isAllowedOrigin(origin)) {
            callback(null, true);
            return;
        }

        const error = new Error(`CORS origin denied: ${origin}`) as Error & { status?: number };
        error.status = 403;
        callback(error);
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    optionsSuccessStatus: 204,
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));
app.use(telemetryMiddleware);
app.use(auditTrailMiddleware);
app.use(express.static(join(__dirname, '..', 'public')));

// ═══════════════════════════════════════════════════════════════════════════
// API ROUTES
// ═══════════════════════════════════════════════════════════════════════════

app.get('/api/health', (req: Request, res: Response) => {
    res.status(200).json({
        status: 'OK',
        emailBlocklist: getEmailDomainBlocklistStatus(),
    });
});

app.use('/api/auth', authRoutes);
app.use('/api/items', itemsRoutes);
app.use('/api/users', userRoutes);
app.use('/api/lessons', lessonsRoutes);
app.use('/api/quizzes', quizzesRoutes);
app.use('/api/dictionary', dictionaryRoutes);
app.use('/api/publications', publicationsRoutes);
app.use('/api/progress', progressRoutes);
app.use('/api/access', accessControlRoutes);
app.use('/api/admin', adminRoutes);

app.use(notFound);
app.use(errorHandler);

const bootstrap = async () => {
    try {
        await runMigrations();
        await initEmailDomainBlocklistAutomation();

        app.listen(PORT, () => {
            console.log(`Backend Server Started on http://localhost:${PORT}`);
            console.log('[CORS] Allowed origin patterns:', allowedOriginPatterns);
        });
    } catch (error) {
        console.error('[BOOTSTRAP] Startup failed:', error);
        process.exit(1);
    }
};

void bootstrap();

export default app;
