/**
 * Dictionary Routes
 */

import express from 'express';
import { store } from '../data/store.js';
import { verifyToken, optionalAuth } from '../middleware/auth.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

/**
 * GET /api/dictionary
 * Get all dictionary words or search
 */
router.get('/', optionalAuth, asyncHandler((req, res) => {
    const query = req.query.q || req.query.search;

    let words;

    if (query) {
        words = store.searchDictionary(query);
    } else {
        words = store.getAllDictionaryWords();
    }

    // Limit results
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    words = words.slice(0, limit);

    res.status(200).json({
        success: true,
        words,
        count: words.length,
        query: query || null
    });
}));

/**
 * GET /api/dictionary/:id
 * Get word by ID
 */
router.get('/:id', optionalAuth, asyncHandler((req, res) => {
    const word = store.getDictionaryWordById(req.params.id);

    if (!word) {
        throw new NotFoundError('Word not found');
    }

    res.status(200).json({
        success: true,
        word
    });
}));

/**
 * POST /api/dictionary
 * Add new word to dictionary
 */
router.post('/', verifyToken, asyncHandler((req, res) => {
    const { word, hebrew, translation, pronunciation, partOfSpeech, example, exampleHebrew, difficulty, category } = req.body;

    if (!word || !hebrew || !translation) {
        throw new ValidationError('Word, hebrew, and translation are required');
    }

    const newWord = store.addDictionaryWord({
        word,
        hebrew,
        translation,
        pronunciation: pronunciation || '',
        partOfSpeech: partOfSpeech || 'noun',
        example: example || '',
        exampleHebrew: exampleHebrew || '',
        difficulty: difficulty || 'intermediate',
        category: category || 'general'
    });

    res.status(201).json({
        success: true,
        message: 'Word added to dictionary',
        word: newWord
    });
}));

/**
 * GET /api/dictionary/search/:query
 * Search dictionary
 */
router.get('/search/:query', optionalAuth, asyncHandler((req, res) => {
    const results = store.searchDictionary(req.params.query);

    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    const limitedResults = results.slice(0, limit);

    res.status(200).json({
        success: true,
        results: limitedResults,
        count: limitedResults.length,
        totalFound: results.length,
        query: req.params.query
    });
}));

export default router;
