/**
 * Dictionary Routes
 *
 * Read is available to authenticated users with dictionary.read.any.
 * Mutations require elevated RBAC permissions.
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken } from '../middleware/auth.js';
import { requirePermission } from '../middleware/authorization.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/dictionary
 * Returns dictionary entries or full-text results scoped to dictionary category.
 */
router.get(
  '/',
  verifyToken,
  requirePermission('dictionary', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const query = typeof req.query.q === 'string' ? req.query.q.trim() : '';

    const words = query
      ? await db.searchItems(query, { category: 'dictionary' })
      : await db
          .query('SELECT * FROM items WHERE category = $1 ORDER BY created_at DESC', ['dictionary'])
          .then((result) => result.rows);

    res.status(200).json({
      success: true,
      words,
      count: words.length,
    });
  })
);

/**
 * GET /api/dictionary/:id
 * Get dictionary entry by ID.
 */
router.get(
  '/:id',
  verifyToken,
  requirePermission('dictionary', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const resDb = await db.query('SELECT * FROM items WHERE id = $1 AND category = $2', [id, 'dictionary']);
    const word = resDb.rows[0];

    if (!word) {
      throw new NotFoundError('Word not found');
    }

    res.status(200).json({
      success: true,
      word,
    });
  })
);

/**
 * POST /api/dictionary
 * Create dictionary entry.
 */
router.post(
  '/',
  verifyToken,
  requirePermission('dictionary', 'create', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const { name, description, metadata } = req.body || {};

    if (!name || typeof name !== 'string') {
      throw new ValidationError('name is required');
    }

    const created = await db.createItem(
      name.trim(),
      typeof description === 'string' ? description : '',
      'dictionary',
      0,
      metadata && typeof metadata === 'object' && !Array.isArray(metadata) ? metadata : {}
    );

    res.status(201).json({
      success: true,
      message: 'Dictionary entry created',
      word: created,
    });
  })
);

/**
 * PUT /api/dictionary/:id
 * Update dictionary entry.
 */
router.put(
  '/:id',
  verifyToken,
  requirePermission('dictionary', 'update', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const { name, description, metadata } = req.body || {};

    const resDb = await db.query(
      `UPDATE items
       SET name = COALESCE($1, name),
           description = COALESCE($2, description),
           metadata = CASE
             WHEN $3::jsonb IS NULL THEN metadata
             ELSE metadata || $3::jsonb
           END,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $4 AND category = 'dictionary'
       RETURNING *`,
      [
        typeof name === 'string' ? name : null,
        typeof description === 'string' ? description : null,
        metadata && typeof metadata === 'object' && !Array.isArray(metadata) ? JSON.stringify(metadata) : null,
        id,
      ]
    );

    const word = resDb.rows[0];
    if (!word) {
      throw new NotFoundError('Word not found');
    }

    res.status(200).json({
      success: true,
      message: 'Dictionary entry updated',
      word,
    });
  })
);

/**
 * DELETE /api/dictionary/:id
 * Delete dictionary entry.
 */
router.delete(
  '/:id',
  verifyToken,
  requirePermission('dictionary', 'delete', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;

    const resDb = await db.query(
      'DELETE FROM items WHERE id = $1 AND category = $2 RETURNING id',
      [id, 'dictionary']
    );

    if (!resDb.rows[0]) {
      throw new NotFoundError('Word not found');
    }

    res.status(200).json({
      success: true,
      message: 'Dictionary entry deleted',
      id,
    });
  })
);

export default router;
