import rateLimit from 'express-rate-limit';

/**
 * Brute-force protection:
 * Limits each IP to 5 login attempts per 15 minutes.
 */
export const loginLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5,
    message: { message: 'Too many login attempts, please try again after 15 minutes' },
    standardHeaders: true,
    legacyHeaders: false,
});

/**
 * General API limiter:
 * Limits each IP to 100 requests per 15 minutes.
 */
export const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
});

/**
 * Admin API limiter:
 * Keeps admin surface tighter than general API to reduce abuse risk.
 */
export const adminApiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 60,
    standardHeaders: true,
    legacyHeaders: false,
    message: { message: 'Too many admin requests, please retry later' },
});
