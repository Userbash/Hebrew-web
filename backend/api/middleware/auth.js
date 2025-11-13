/**
 * Authentication Middleware
 */

import { store } from '../data/store.js';
import { UnauthorizedError, asyncHandler } from './errorHandler.js';

/**
 * Verify authentication token
 */
export const verifyToken = asyncHandler((req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];

    if (!token) {
        throw new UnauthorizedError('No token provided');
    }

    const session = store.getSession(token);
    if (!session) {
        throw new UnauthorizedError('Invalid or expired token');
    }

    req.userId = session.userId;
    req.token = token;
    next();
});

/**
 * Optional auth - doesn't fail if no token
 */
export const optionalAuth = asyncHandler((req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];

    if (token) {
        const session = store.getSession(token);
        if (session) {
            req.userId = session.userId;
            req.token = token;
        }
    }

    next();
});

/**
 * Simple password hashing (for demo - use bcrypt in production)
 */
export const hashPassword = (password) => {
    // Simple hash for demonstration
    return Buffer.from(password).toString('base64');
};

export const comparePassword = (password, hash) => {
    return hashPassword(password) === hash;
};
