/**
 * Error Handling Middleware
 */

export const notFound = (req, res) => {
    res.status(404).json({
        success: false,
        error: 'Not Found',
        message: `Cannot ${req.method} ${req.originalUrl}`,
        path: req.originalUrl,
        timestamp: new Date().toISOString()
    });
};

export const errorHandler = (err, req, res, next) => {
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
    constructor(message, statusCode = 500) {
        super(message);
        this.statusCode = statusCode;
        Error.captureStackTrace(this, this.constructor);
    }
}

export class ValidationError extends AppError {
    constructor(message = 'Validation Error') {
        super(message, 400);
        this.name = 'ValidationError';
    }
}

export class UnauthorizedError extends AppError {
    constructor(message = 'Unauthorized') {
        super(message, 401);
        this.name = 'UnauthorizedError';
    }
}

export class NotFoundError extends AppError {
    constructor(message = 'Not Found') {
        super(message, 404);
        this.name = 'NotFoundError';
    }
}

export class ConflictError extends AppError {
    constructor(message = 'Conflict') {
        super(message, 409);
        this.name = 'ConflictError';
    }
}

// Wrapper for async route handlers
export const asyncHandler = (fn) => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};
