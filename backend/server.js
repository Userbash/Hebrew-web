/**
 * Hebrew AI 2025 - Backend Server
 * Express.js server with in-memory data store
 * No external database required
 */

import express from 'express';
import cors from 'cors';
import compression from 'compression';
import helmet from 'helmet';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { config } from 'dotenv';

// Get current directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
config({ path: join(__dirname, '..', '.env') });

// Import routes
import authRoutes from './api/routes/auth.js';
import lessonsRoutes from './api/routes/lessons.js';
import quizzesRoutes from './api/routes/quizzes.js';
import dictionaryRoutes from './api/routes/dictionary.js';
import progressRoutes from './api/routes/progress.js';
import userRoutes from './api/routes/users.js';

// Import middleware
import { errorHandler, notFound } from './api/middleware/errorHandler.js';

// Initialize Express app
const app = express();
const PORT = process.env.BACKEND_PORT || 3001;

// ═══════════════════════════════════════════════════════════════════════════
// MIDDLEWARE
// ═══════════════════════════════════════════════════════════════════════════

// Security middleware
app.use(helmet());

// Compression middleware
app.use(compression());

// CORS middleware
app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

// Body parser middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

// Static files
app.use(express.static(join(__dirname, 'public')));

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH CHECK ENDPOINT
// ═══════════════════════════════════════════════════════════════════════════

app.get('/api/health', (req, res) => {
    res.status(200).json({
        status: 'OK',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        environment: process.env.NODE_ENV || 'development'
    });
});

// ═══════════════════════════════════════════════════════════════════════════
// API ROUTES
// ═══════════════════════════════════════════════════════════════════════════

// Authentication routes
app.use('/api/auth', authRoutes);

// User routes
app.use('/api/users', userRoutes);

// Lessons routes
app.use('/api/lessons', lessonsRoutes);

// Quizzes routes
app.use('/api/quizzes', quizzesRoutes);

// Dictionary routes
app.use('/api/dictionary', dictionaryRoutes);

// Progress routes
app.use('/api/progress', progressRoutes);

// ═══════════════════════════════════════════════════════════════════════════
// FRONTEND ROUTES - Serve HTML
// ═══════════════════════════════════════════════════════════════════════════

app.get('/', (req, res) => {
    res.sendFile(join(__dirname, 'public', 'START_HERE.html'));
});

app.get('/pages/:page', (req, res) => {
    const page = req.params.page.replace(/\.\./g, ''); // Security: prevent directory traversal
    res.sendFile(join(__dirname, 'public', 'pages', `${page}.html`));
});

// ═══════════════════════════════════════════════════════════════════════════
// ERROR HANDLING
// ═══════════════════════════════════════════════════════════════════════════

// 404 handler
app.use(notFound);

// Error handler
app.use(errorHandler);

// ═══════════════════════════════════════════════════════════════════════════
// SERVER STARTUP
// ═══════════════════════════════════════════════════════════════════════════

const server = app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          🚀 Hebrew AI 2025 - Backend Server Started           ║
║                                                                ║
║  Server: http://localhost:${PORT}                              ║
║  API Docs: http://localhost:${PORT}/api/docs                   ║
║  Health: http://localhost:${PORT}/api/health                   ║
║                                                                ║
║  Routes:                                                       ║
║  • POST   /api/auth/register       - Create new user          ║
║  • POST   /api/auth/login          - User login               ║
║  • GET    /api/users/profile       - Get user profile         ║
║  • GET    /api/lessons             - Get all lessons          ║
║  • GET    /api/quizzes             - Get all quizzes          ║
║  • GET    /api/dictionary/:word    - Search dictionary        ║
║  • GET    /api/progress/:userId    - Get user progress        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    `);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, closing server gracefully...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('\nSIGINT received, closing server gracefully...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

export default app;
