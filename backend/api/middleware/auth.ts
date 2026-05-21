/**
 * Authentication Middleware
 */

import { Request, Response, NextFunction } from 'express';
import { store } from '../data/store.js';
import { UnauthorizedError, asyncHandler } from './errorHandler.js';

export interface RequestWithAuth extends Request {
    userId: string;
    token: string;
}

/**
 * Verify authentication token
 */
export const verifyToken = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    const token = authHeader?.split(' ')[1];

    if (!token) {
        throw new UnauthorizedError('No token provided');
    }

    const session = store.getSession(token);
    if (!session) {
        throw new UnauthorizedError('Invalid or expired token');
    }

    (req as RequestWithAuth).userId = session.userId;
    (req as RequestWithAuth).token = token;
    next();
});

/**
 * Optional auth - doesn't fail if no token
 */
export const optionalAuth = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    const token = authHeader?.split(' ')[1];

    if (token) {
        const session = store.getSession(token);
        if (session) {
            (req as RequestWithAuth).userId = session.userId;
            (req as RequestWithAuth).token = token;
        }
    }

    next();
});

/**
 * Simple password hashing (for demo - use bcrypt in production)
 */
export const hashPassword = (password: string): string => {
    return Buffer.from(password).toString('base64');
};

export const comparePassword = (password: string, hash: string): boolean => {
    return hashPassword(password) === hash;
};
