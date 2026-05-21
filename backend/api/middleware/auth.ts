import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import { db } from '../data/db.js';
import { ForbiddenError, UnauthorizedError, asyncHandler } from './errorHandler.js';

export const ACCESS_COOKIE_NAME = 'token';
export const REFRESH_COOKIE_NAME = 'refresh_token';

const ACCESS_TOKEN_TTL_SECONDS = 15 * 60;
const REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60;

interface AuthTokenClaims extends jwt.JwtPayload {
    id?: string;
    sid?: string;
    typ?: 'access' | 'refresh';
}

export const getJwtSecret = () => {
    const secret = process.env.JWT_SECRET;

    if (!secret && process.env.NODE_ENV === 'production') {
        throw new Error('JWT_SECRET is required in production');
    }

    return secret || 'dev_only_jwt_secret_change_me';
};

export const getAccessTokenTtlMs = () => ACCESS_TOKEN_TTL_SECONDS * 1000;
export const getRefreshTokenTtlMs = () => REFRESH_TOKEN_TTL_SECONDS * 1000;

export const getAccessCookieOptions = () => ({
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict' as const,
    path: '/',
    maxAge: getAccessTokenTtlMs()
});

export const getRefreshCookieOptions = () => ({
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict' as const,
    path: '/api/auth',
    maxAge: getRefreshTokenTtlMs()
});

export const clearAuthCookies = (res: Response) => {
    res.clearCookie(ACCESS_COOKIE_NAME, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        path: '/'
    });

    res.clearCookie(REFRESH_COOKIE_NAME, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        path: '/api/auth'
    });
};

const normalizeIp = (ip: string) => {
    if (ip.startsWith('::ffff:')) {
        return ip.slice(7);
    }
    return ip;
};

const getIpPrefix = (ip: string) => {
    const normalized = normalizeIp(ip);

    const v4 = normalized.split('.');
    if (v4.length === 4) {
        return `${v4[0]}.${v4[1]}.${v4[2]}`;
    }

    const v6 = normalized.split(':').filter(Boolean);
    return v6.slice(0, 4).join(':');
};

export const getClientIp = (req: Request) => {
    const xForwardedFor = req.headers['x-forwarded-for'];

    if (typeof xForwardedFor === 'string' && xForwardedFor.length > 0) {
        return xForwardedFor.split(',')[0].trim();
    }

    return req.ip || '';
};

export const buildRequestFingerprint = (req: Request) => {
    const userAgent = req.get('user-agent') || '';
    const language = req.get('accept-language') || '';
    const ipPrefix = getIpPrefix(getClientIp(req));

    return crypto
        .createHash('sha256')
        .update(`${userAgent}|${language}|${ipPrefix}`)
        .digest('hex');
};

export const hashRefreshToken = (refreshToken: string) => {
    return crypto.createHash('sha256').update(refreshToken).digest('hex');
};

const secureHashEquals = (a: string, b: string) => {
    const aBuffer = Buffer.from(a);
    const bBuffer = Buffer.from(b);

    if (aBuffer.length !== bBuffer.length) {
        return false;
    }

    return crypto.timingSafeEqual(aBuffer, bBuffer);
};

export const signAccessToken = (userId: string, sessionId: string) => {
    return jwt.sign(
        { id: userId, sid: sessionId, typ: 'access' },
        getJwtSecret(),
        { expiresIn: ACCESS_TOKEN_TTL_SECONDS }
    );
};

export const signRefreshToken = (userId: string, sessionId: string) => {
    return jwt.sign(
        { id: userId, sid: sessionId, typ: 'refresh' },
        getJwtSecret(),
        { expiresIn: REFRESH_TOKEN_TTL_SECONDS }
    );
};

const readBearerToken = (req: Request) => {
    const auth = req.headers.authorization;
    if (!auth || !auth.startsWith('Bearer ')) {
        return null;
    }

    const token = auth.slice(7).trim();
    return token.length > 0 ? token : null;
};

const readAccessToken = (req: Request) => {
    const cookieToken = req.cookies[ACCESS_COOKIE_NAME] as string | undefined;
    if (cookieToken) {
        return cookieToken;
    }

    return readBearerToken(req);
};

export const verifyTypedToken = (token: string, expectedType: 'access' | 'refresh') => {
    const decoded = jwt.verify(token, getJwtSecret()) as AuthTokenClaims;

    if (!decoded.id || !decoded.sid || decoded.typ !== expectedType) {
        throw new UnauthorizedError('Invalid token payload');
    }

    return decoded as Required<Pick<AuthTokenClaims, 'id' | 'sid' | 'typ'>> & AuthTokenClaims;
};

const assertActiveSession = async (req: Request, sessionId: string, userId: string) => {
    const resDb = await db.query(
        `SELECT id, user_id, fingerprint_hash
         FROM user_sessions
         WHERE id = $1
           AND user_id = $2
           AND revoked_at IS NULL
           AND expires_at > CURRENT_TIMESTAMP
         LIMIT 1`,
        [sessionId, userId]
    );

    if (!resDb.rows[0]) {
        throw new UnauthorizedError('Session not found or expired');
    }

    const expectedFingerprint = resDb.rows[0].fingerprint_hash as string;
    const currentFingerprint = buildRequestFingerprint(req);

    if (!secureHashEquals(expectedFingerprint, currentFingerprint)) {
        throw new UnauthorizedError('Session fingerprint mismatch');
    }

    await db.query(
        'UPDATE user_sessions SET last_seen_at = CURRENT_TIMESTAMP WHERE id = $1',
        [sessionId]
    );
};

export interface RequestWithAuth extends Request {
    userId: string;
    sessionId: string;
}

/**
 * Verify authentication token + active server-side session.
 */
export const verifyToken = asyncHandler(async (req: Request, _res: Response, next: NextFunction) => {
    const token = readAccessToken(req);

    if (!token) {
        throw new UnauthorizedError('No token provided');
    }

    try {
        const decoded = verifyTypedToken(token, 'access');
        await assertActiveSession(req, decoded.sid, decoded.id);
        (req as RequestWithAuth).userId = decoded.id;
        (req as RequestWithAuth).sessionId = decoded.sid;
        next();
    } catch (_err) {
        throw new UnauthorizedError('Invalid or expired token');
    }
});

export const requireAdmin = [
    verifyToken,
    asyncHandler(async (req: Request, _res: Response, next: NextFunction) => {
        const authReq = req as RequestWithAuth;
        const user = await db.getUserById(authReq.userId);

        if (!user || user.role !== 'admin') {
            throw new ForbiddenError('Admin role required');
        }

        next();
    })
];

/**
 * Optional auth - doesn't fail if no token or invalid session.
 */
export const optionalAuth = asyncHandler(async (req: Request, _res: Response, next: NextFunction) => {
    const token = readAccessToken(req);

    if (!token) {
        next();
        return;
    }

    try {
        const decoded = verifyTypedToken(token, 'access');
        await assertActiveSession(req, decoded.sid, decoded.id);
        (req as RequestWithAuth).userId = decoded.id;
        (req as RequestWithAuth).sessionId = decoded.sid;
    } catch (_err) {
        // Optional auth intentionally ignores failures.
    }

    next();
});
