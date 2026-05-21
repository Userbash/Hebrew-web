/**
 * Dictionary Routes
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { asyncHandler, NotFoundError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/dictionary
 * Get all words or search
 */
router.get('/', asyncHandler(async (req: Request, res: Response) => {
    const query = req.query.q as string | undefined;
    let words;

    if (query) {
        // Use our optimized searchItems method for dictionary too (category='dictionary')
        words = await db.searchItems(query);
    } else {
        const res_db = await db.query("SELECT * FROM items WHERE category = 'dictionary'");
        words = res_db.rows;
    }

    res.status(200).json({
        success: true,
        words,
        count: words.length
    });
}));

/**
 * GET /api/dictionary/:id
 * Get word by ID
 */
router.get('/:id', asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const res_db = await db.query("SELECT * FROM items WHERE id = $1 AND category = 'dictionary'", [id]);
    const word = res_db.rows[0];

    if (!word) {
        throw new NotFoundError('Word not found');
    }

    res.status(200).json({
        success: true,
        word
    });
}));

export default router;
