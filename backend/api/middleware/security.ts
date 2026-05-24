import type { Request } from 'express';
import rateLimit from 'express-rate-limit';

const isReadOnlyMethod = (req: Request) => ['GET', 'HEAD', 'OPTIONS'].includes(req.method.toUpperCase());

/**
 * Brute-force protection:
 * Limits each IP to failed login attempts.
 */
export const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5,
    skipSuccessfulRequests: true,
    message: { message: 'Too many login attempts, please try again after 15 minutes' },
    standardHeaders: true,
    legacyHeaders: false,
});

/**
 * General API limiter:
 * Limits broad API abuse but avoids false lockouts for auth bootstrap.
 */
export const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
    message: { message: 'Too many requests, please retry later' },
    skip: (req) => {
        // Admin routes are guarded by dedicated limiter below.
        if (req.path.startsWith('/api/admin')) {
            return true;
        }

        // Do not break auth bootstrap under bursty page reloads.
        if (req.path === '/api/auth/me' || req.path === '/api/auth/refresh') {
            return true;
        }

        return false;
    },
});

/**
 * Admin API limiter:
 * Keeps admin write surface tighter than general API to reduce abuse risk.
 * Allows more frequent read requests for dashboard auto-refresh.
 */
export const adminApiLimiter = rateLimit({
    windowMs: 5 * 60 * 1000, // 5 minutes window
    max: async (req: Request) => {
        if (isReadOnlyMethod(req)) {
            return 300; // Allow 300 read requests per 5 min (1 per sec average)
        }
        return 30; // Stricter limit for write requests (30 per 5 min)
    },
    standardHeaders: true,
    legacyHeaders: false,
    message: async (req: Request) => {
        if (isReadOnlyMethod(req)) {
            return { message: 'Too many admin read requests, please retry later' };
        }
        return { message: 'Too many admin write requests, please retry later' };
    },
});
