import { Router } from 'express';
import { db } from '../data/db.js';
import { verifyToken } from '../middleware/auth.js';
import { requirePermission } from '../middleware/authorization.js';
import { asyncHandler, ValidationError } from '../middleware/errorHandler.js';

const router = Router();

// GET /api/items/search?q=query
router.get(
  '/search',
  verifyToken,
  requirePermission('items', 'read', 'any'),
  asyncHandler(async (req, res) => {
    const q = typeof req.query.q === 'string' ? req.query.q.trim() : '';

    if (!q) {
      throw new ValidationError('Search query is required');
    }

    const items = await db.searchItems(q);
    res.json(items);
  })
);

// POST /api/items
router.post(
  '/',
  verifyToken,
  requirePermission('items', 'create', 'any'),
  asyncHandler(async (req, res) => {
    const { name, description, category, price } = req.body || {};

    if (!name || !category) {
      throw new ValidationError('name and category are required');
    }

    const normalizedPrice = typeof price === 'number' ? price : Number(price || 0);
    const newItem = await db.createItem(
      String(name),
      description ? String(description) : '',
      String(category),
      Number.isFinite(normalizedPrice) ? normalizedPrice : 0
    );

    res.status(201).json(newItem);
  })
);

// DELETE /api/items/:id
router.delete(
  '/:id',
  verifyToken,
  requirePermission('items', 'delete', 'any'),
  asyncHandler(async (req, res) => {
    const { id } = req.params;
    const deleted = await db.deleteItem(id);

    if (!deleted) {
      res.status(404).json({ message: 'Item not found' });
      return;
    }

    res.json({ message: 'Item deleted', id: deleted.id });
  })
);

export default router;
