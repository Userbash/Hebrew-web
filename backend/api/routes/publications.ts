/**
 * Publications Routes
 *
 * Uses items table with category='publication'.
 * Metadata structure is flexible and stores publication-specific fields.
 */

import express, { Request, Response } from 'express';
import { db } from '../data/db.js';
import { verifyToken, RequestWithAuth } from '../middleware/auth.js';
import {
  requireAnyOrOwnPermission,
  requirePermission,
  type RequestWithAccess,
} from '../middleware/authorization.js';
import { asyncHandler, NotFoundError, ValidationError } from '../middleware/errorHandler.js';

const router = express.Router();

interface PublicationRow {
  id: string;
  name: string;
  description: string | null;
  category: string;
  price: string | number;
  metadata: {
    authorId?: string;
    status?: string;
    tags?: string[];
    publishedAt?: string | null;
    visibility?: 'private' | 'team' | 'public';
    [key: string]: unknown;
  } | null;
  created_at: string;
  updated_at: string;
}

const normalizePublicationPayload = (body: unknown, userId: string) => {
  const source = body && typeof body === 'object' && !Array.isArray(body)
    ? (body as Record<string, unknown>)
    : {};

  const title = typeof source.title === 'string' ? source.title.trim() : '';
  if (!title) {
    throw new ValidationError('title is required');
  }

  const description = typeof source.description === 'string' ? source.description : '';
  const status = typeof source.status === 'string' ? source.status : 'draft';
  const tags = Array.isArray(source.tags)
    ? source.tags.filter((tag): tag is string => typeof tag === 'string').slice(0, 32)
    : [];

  const metadataFromBody = source.metadata && typeof source.metadata === 'object' && !Array.isArray(source.metadata)
    ? (source.metadata as Record<string, unknown>)
    : {};

  const visibility = source.visibility === 'team' || source.visibility === 'public'
    ? source.visibility
    : 'private';

  const metadata = {
    ...metadataFromBody,
    status,
    tags,
    authorId: typeof source.authorId === 'string' ? source.authorId : userId,
    visibility: visibility as 'private' | 'team' | 'public',
    publishedAt: status === 'published' ? new Date().toISOString() : null,
  };

  return {
    title,
    description,
    metadata,
  };
};

const isOwner = (publication: PublicationRow, userId: string) => {
  return publication.metadata?.authorId === userId;
};

const getPublicationById = async (id: string) => {
  const resDb = await db.query(
    `SELECT id, name, description, category, price, metadata, created_at, updated_at
     FROM items
     WHERE id = $1 AND category = 'publication'
     LIMIT 1`,
    [id]
  );

  return resDb.rows[0] as PublicationRow | undefined;
};

/**
 * GET /api/publications
 * Admin visibility endpoint (read.any).
 */
router.get(
  '/',
  verifyToken,
  requirePermission('publications', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const search = typeof req.query.search === 'string' ? req.query.search.trim() : '';
    const status = typeof req.query.status === 'string' ? req.query.status.trim() : '';
    const authorId = typeof req.query.authorId === 'string' ? req.query.authorId.trim() : '';

    const where: string[] = [`category = 'publication'`];
    const params: unknown[] = [];

    if (search) {
      params.push(`%${search}%`);
      where.push(`(name ILIKE $${params.length} OR description ILIKE $${params.length})`);
    }

    if (status) {
      params.push(status);
      where.push(`COALESCE(metadata->>'status', 'draft') = $${params.length}`);
    }

    if (authorId) {
      params.push(authorId);
      where.push(`metadata->>'authorId' = $${params.length}`);
    }

    const whereSql = where.length ? `WHERE ${where.join(' AND ')}` : '';

    const publicationsRes = await db.query(
      `SELECT id, name, description, category, price, metadata, created_at, updated_at
       FROM items
       ${whereSql}
       ORDER BY updated_at DESC
       LIMIT 200`,
      params
    );

    res.status(200).json({
      success: true,
      publications: publicationsRes.rows,
      count: publicationsRes.rows.length,
    });
  })
);

/**
 * GET /api/publications/:id
 */
router.get(
  '/:id',
  verifyToken,
  requirePermission('publications', 'read', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const publication = await getPublicationById(req.params.id);

    if (!publication) {
      throw new NotFoundError('Publication not found');
    }

    res.status(200).json({ success: true, publication });
  })
);

/**
 * POST /api/publications
 */
router.post(
  '/',
  verifyToken,
  requirePermission('publications', 'create', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const authReq = req as RequestWithAuth;
    const payload = normalizePublicationPayload(req.body, authReq.userId);

    const created = await db.createItem(
      payload.title,
      payload.description,
      'publication',
      0,
      payload.metadata
    );

    res.status(201).json({
      success: true,
      message: 'Publication created successfully',
      publication: created,
    });
  })
);

/**
 * PUT /api/publications/:id
 */
router.put(
  '/:id',
  verifyToken,
  requireAnyOrOwnPermission(
    'publications',
    'update',
    (req: RequestWithAccess) => {
      const candidateOwnerId = typeof req.body?.authorId === 'string' ? req.body.authorId : undefined;
      return Boolean(candidateOwnerId && candidateOwnerId === req.userId);
    }
  ),
  asyncHandler(async (req: Request, res: Response) => {
    const id = req.params.id;
    const authReq = req as RequestWithAuth;
    const existing = await getPublicationById(id);

    if (!existing) {
      throw new NotFoundError('Publication not found');
    }

    const requestHasAnyScope = (req as RequestWithAccess)?.accessProfile?.roleKeys?.some((role) => {
      return ['root', 'platform_admin', 'content_admin'].includes(role);
    });

    if (!requestHasAnyScope && !isOwner(existing, authReq.userId)) {
      throw new ValidationError('You can update only your own publication');
    }

    const nextTitle = typeof req.body?.title === 'string' ? req.body.title.trim() : null;
    const nextDescription = typeof req.body?.description === 'string' ? req.body.description : null;

    const metadataPatch = req.body?.metadata && typeof req.body.metadata === 'object' && !Array.isArray(req.body.metadata)
      ? (req.body.metadata as Record<string, unknown>)
      : {};

    const status = typeof req.body?.status === 'string' ? req.body.status : null;

    if (status) {
      metadataPatch.status = status;
      if (status === 'published') {
        metadataPatch.publishedAt = new Date().toISOString();
      }
    }

    const updatedRes = await db.query(
      `UPDATE items
       SET name = COALESCE($1, name),
           description = COALESCE($2, description),
           metadata = metadata || $3::jsonb,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $4 AND category = 'publication'
       RETURNING id, name, description, category, price, metadata, created_at, updated_at`,
      [nextTitle, nextDescription, JSON.stringify(metadataPatch), id]
    );

    const publication = updatedRes.rows[0];
    if (!publication) {
      throw new NotFoundError('Publication not found');
    }

    res.status(200).json({
      success: true,
      message: 'Publication updated successfully',
      publication,
    });
  })
);

/**
 * DELETE /api/publications/:id
 */
router.delete(
  '/:id',
  verifyToken,
  requirePermission('publications', 'delete', 'any'),
  asyncHandler(async (req: Request, res: Response) => {
    const deleted = await db.query(
      `DELETE FROM items WHERE id = $1 AND category = 'publication' RETURNING id`,
      [req.params.id]
    );

    if (!deleted.rows[0]) {
      throw new NotFoundError('Publication not found');
    }

    res.status(200).json({
      success: true,
      message: 'Publication deleted successfully',
      id: deleted.rows[0].id,
    });
  })
);

export default router;
