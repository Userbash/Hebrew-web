/**
 * Authentication Routes
 */

import express from 'express';
import { store } from '../data/store.js';
import { verifyToken } from '../middleware/auth.js';
import { asyncHandler, ValidationError, ConflictError, UnauthorizedError } from '../middleware/errorHandler.js';
import { hashPassword, comparePassword } from '../middleware/auth.js';

const router = express.Router();

/**
 * POST /api/auth/register
 * Create a new user account
 */
router.post('/register', asyncHandler((req, res) => {
    const { email, password, firstName, lastName } = req.body;

    // Validation
    if (!email || !password) {
        throw new ValidationError('Email and password are required');
    }

    if (password.length < 6) {
        throw new ValidationError('Password must be at least 6 characters');
    }

    // Check if user already exists
    const existingUser = store.getUserByEmail(email);
    if (existingUser) {
        throw new ConflictError('User with this email already exists');
    }

    // Create user
    const user = store.createUser({
        email,
        password: hashPassword(password),
        firstName: firstName || 'User',
        lastName: lastName || '',
        avatar: null
    });

    // Create session
    const session = store.createSession(user.id);

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user;

    res.status(201).json({
        success: true,
        message: 'User registered successfully',
        user: userWithoutPassword,
        token: session.token,
        expiresAt: session.expiresAt
    });
}));

/**
 * POST /api/auth/login
 * Authenticate user and create session
 */
router.post('/login', asyncHandler((req, res) => {
    const { email, password } = req.body;

    // Validation
    if (!email || !password) {
        throw new ValidationError('Email and password are required');
    }

    // Find user
    const user = store.getUserByEmail(email);
    if (!user) {
        throw new UnauthorizedError('Invalid email or password');
    }

    // Verify password
    if (!comparePassword(password, user.password)) {
        throw new UnauthorizedError('Invalid email or password');
    }

    // Create session
    const session = store.createSession(user.id);

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user;

    res.status(200).json({
        success: true,
        message: 'Login successful',
        user: userWithoutPassword,
        token: session.token,
        expiresAt: session.expiresAt
    });
}));

/**
 * POST /api/auth/logout
 * Logout user (invalidate session)
 */
router.post('/logout', verifyToken, asyncHandler((req, res) => {
    store.deleteSession(req.token);

    res.status(200).json({
        success: true,
        message: 'Logged out successfully'
    });
}));

/**
 * GET /api/auth/verify
 * Verify current session
 */
router.get('/verify', verifyToken, asyncHandler((req, res) => {
    const user = store.getUserById(req.userId);

    if (!user) {
        throw new UnauthorizedError('User not found');
    }

    const { password: _, ...userWithoutPassword } = user;

    res.status(200).json({
        success: true,
        user: userWithoutPassword,
        isAuthenticated: true
    });
}));

/**
 * POST /api/auth/refresh
 * Refresh authentication token
 */
router.post('/refresh', verifyToken, asyncHandler((req, res) => {
    const user = store.getUserById(req.userId);

    if (!user) {
        throw new UnauthorizedError('User not found');
    }

    // Invalidate old session
    store.deleteSession(req.token);

    // Create new session
    const newSession = store.createSession(user.id);

    const { password: _, ...userWithoutPassword } = user;

    res.status(200).json({
        success: true,
        message: 'Token refreshed successfully',
        user: userWithoutPassword,
        token: newSession.token,
        expiresAt: newSession.expiresAt
    });
}));

export default router;
