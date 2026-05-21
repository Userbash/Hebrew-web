/**
 * Error Handling Middleware
 */

import { Request, Response, NextFunction, RequestHandler } from 'express';

export const notFound = (req: Request, res: Response) => {
    res.status(404).json({
        success: false,
        error: 'Not Found',
        message: `Cannot ${req.method} ${req.originalUrl}`,
        path: req.originalUrl,
        timestamp: new Date().toISOString()
    });
};

export const errorHandler = (err: any, req: Request, res: Response, next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || 'Internal Server Error';

    console.error(`[ERROR] ${status} - ${message}`, {
        path: req.originalUrl,
        method: req.method,
        stack: err.stack
    });

    res.status(status).json({
        success: false,
        error: err.name || 'Error',
        message,
        ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    });
};

export class AppError extends Error {
    public statusCode: number;

    constructor(message: string, statusCode: number = 500) {
        super(message);
        this.statusCode = statusCode;
        Error.captureStackTrace(this, this.constructor);
    }
}

export class ValidationError extends AppError {
    constructor(message: string = 'Validation Error') {
        super(message, 400);
        this.name = 'ValidationError';
    }
}

export class UnauthorizedError extends AppError {
    constructor(message: string = 'Unauthorized') {
        super(message, 401);
        this.name = 'UnauthorizedError';
    }
}

export class NotFoundError extends AppError {
    constructor(message: string = 'Not Found') {
        super(message, 404);
        this.name = 'NotFoundError';
    }
}

export class ConflictError extends AppError {
    constructor(message: string = 'Conflict') {
        super(message, 409);
        this.name = 'ConflictError';
    }
}

// Wrapper for async route handlers
export const asyncHandler = (fn: RequestHandler): RequestHandler => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};
