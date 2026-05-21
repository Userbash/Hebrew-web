import { Request, Response, NextFunction } from 'express';
import { db } from '../data/db.js';

export const telemetryMiddleware = async (req: Request, res: Response, next: NextFunction) => {
    // Only track authenticated actions if user is logged in
    const userId = (req as any).user?.id;
    
    if (userId) {
        try {
            await db.query(
                'INSERT INTO user_telemetry (user_id, action, metadata) VALUES ($1, $2, $3)',
                [userId, req.path, JSON.stringify({ method: req.method, ip: req.ip })]
            );
        } catch (e) {
            console.error('Telemetry logging failed', e);
        }
    }
    next();
};
