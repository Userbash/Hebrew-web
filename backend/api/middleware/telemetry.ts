import { Request, Response, NextFunction } from 'express';
import { db } from '../data/db.js';
import { RequestWithAuth } from './auth.js';

/**
 * Lightweight request telemetry.
 *
 * We write after the response is sent so this never blocks request handling.
 */
export const telemetryMiddleware = (req: Request, res: Response, next: NextFunction) => {
    const startedAt = Date.now();

    res.on('finish', () => {
        const authReq = req as Partial<RequestWithAuth>;
        const durationMs = Date.now() - startedAt;

        // Fire-and-forget logging: telemetry should never break API responses.
        void db.query(
            `INSERT INTO user_telemetry (user_id, method, path, status_code, ip_address, user_agent, response_time_ms, metadata)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)`,
            [
                authReq.userId || null,
                req.method,
                req.path,
                res.statusCode,
                req.ip || null,
                req.get('user-agent') || null,
                durationMs,
                JSON.stringify({
                    query: req.query,
                    hasBody: Boolean(req.body && Object.keys(req.body).length > 0),
                }),
            ]
        ).catch((error: unknown) => {
            console.error('[Telemetry] Failed to store request metric', error);
        });
    });

    next();
};
