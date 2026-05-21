import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { UnauthorizedError, asyncHandler } from './errorHandler.js';

const JWT_SECRET = process.env.JWT_SECRET || 'your_super_secret_key_2025';

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
        const decoded: any = jwt.verify(token, JWT_SECRET);
        (req as RequestWithAuth).userId = decoded.id;
        next();
    } catch (err) {
        throw new UnauthorizedError('Invalid or expired token');
    }
});

/**
 * Optional auth - doesn't fail if no token
 */
export const optionalAuth = asyncHandler(async (req: Request, res: Response, next: NextFunction) => {
    const token = req.cookies.token;

    if (token) {
        try {
            const decoded: any = jwt.verify(token, JWT_SECRET);
            (req as RequestWithAuth).userId = decoded.id;
        } catch (err) {
            // Silently fail for optional auth
        }
    }

    next();
});
