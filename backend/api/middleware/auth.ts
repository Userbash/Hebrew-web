import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { db } from '../data/db.js';
import { ForbiddenError, UnauthorizedError, asyncHandler } from './errorHandler.js';

export const getJwtSecret = () => {
    const secret = process.env.JWT_SECRET;

    if (!secret && process.env.NODE_ENV === 'production') {
        throw new Error('JWT_SECRET is required in production');
    }

    return secret || 'dev_only_jwt_secret_change_me';
};

export interface RequestWithAuth extends Request {
    userId: string;
}

/**
 * Verify authentication token
 */
export const verifyToken = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const token = req.cookies.token;

    if (!token) {
        throw new UnauthorizedError('No token provided');
    }

    try {
        const decoded = jwt.verify(token, getJwtSecret()) as { id?: string };
        if (!decoded.id) {
            throw new UnauthorizedError('Invalid token payload');
        }
        (req as RequestWithAuth).userId = decoded.id;
        next();
    } catch (_err) {
        throw new UnauthorizedError('Invalid or expired token');
    }
});

export const requireAdmin = [
    verifyToken,
    asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
        const authReq = req as RequestWithAuth;
        const user = await db.getUserById(authReq.userId);

        if (!user || user.role !== 'admin') {
            throw new ForbiddenError('Admin role required');
        }

        next();
    })
];

/**
 * Optional auth - doesn't fail if no token
 */
export const optionalAuth = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const token = req.cookies.token;

    if (token) {
        try {
            const decoded = jwt.verify(token, getJwtSecret()) as { id?: string };
            if (decoded.id) {
                (req as RequestWithAuth).userId = decoded.id;
            }
        } catch (_err) {
            // Silently fail for optional auth
        }
    }

    next();
});
