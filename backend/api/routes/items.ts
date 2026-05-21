import { Router } from 'express';
import { db } from '../data/db.js';

const router = Router();

// GET /api/items/search?q=query
router.get('/search', async (req, res) => {
  const { q } = req.query;
  
  if (!q || typeof q !== 'string') {
    return res.status(400).json({ message: 'Search query is required' });
  }

  try {
    const items = await db.searchItems(q);
    res.json(items);
  } catch (err) {
    console.error('Search error:', err);
    res.status(500).json({ message: 'Error performing search' });
  }
});

// POST /api/items
router.post('/', async (req, res) => {
  const { name, description, category, price } = req.body;
  
  try {
    const newItem = await db.createItem(name, description, category, price);
    res.status(201).json(newItem);
  } catch (err) {
    console.error('Create item error:', err);
    res.status(500).json({ message: 'Error creating item' });
  }
});

// DELETE /api/items/:id
router.delete('/:id', async (req, res) => {
  const { id } = req.params;
  
  try {
    const deleted = await db.deleteItem(id);
    if (!deleted) return res.status(404).json({ message: 'Item not found' });
    res.json({ message: 'Item deleted', id: deleted.id });
  } catch (err) {
    res.status(500).json({ message: 'Error deleting item' });
  }
});

export default router;
