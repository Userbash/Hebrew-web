import { Router } from 'express';
import { promises as fs } from 'fs';
import { join } from 'path';
import { verifyToken, type RequestWithAuth } from '../middleware/auth.js';
import { setTelemetryContext } from '../middleware/telemetry.js';
import { setAuditContext } from '../middleware/auditTrail.js';

const router = Router();

const AVATAR_MAX_SIZE_BYTES = Math.max(256 * 1024, Number(process.env.AVATAR_MAX_SIZE_BYTES || 2 * 1024 * 1024));
const AVATAR_STORAGE_DIR = process.env.AVATAR_STORAGE_DIR || join(process.cwd(), 'public', 'uploads', 'avatars');

const AVATAR_ALLOWED_MIME_TYPES: Record<string, string> = {
  'image/png': 'png',
  'image/jpeg': 'jpg',
  'image/webp': 'webp',
};

const AVATAR_ALLOWED_FORMATS = Object.keys(AVATAR_ALLOWED_MIME_TYPES);

const sanitizeUserIdForFilename = (userId: string) => userId.replace(/[^a-zA-Z0-9_-]/g, '_');

const ensureAvatarStorageDir = async () => {
  await fs.mkdir(AVATAR_STORAGE_DIR, { recursive: true });
};

const listAvatarFilesForUser = async (userId: string) => {
  await ensureAvatarStorageDir();
  const safeId = sanitizeUserIdForFilename(userId);
  const entries = await fs.readdir(AVATAR_STORAGE_DIR, { withFileTypes: true });

  return entries
    .filter((entry) => entry.isFile() && entry.name.startsWith(safeId + '.'))
    .map((entry) => entry.name)
    .sort();
};

const resolveAvatarFileForUser = async (userId: string) => {
  const files = await listAvatarFilesForUser(userId);
  return files[0] || null;
};

const removeAvatarFilesForUser = async (userId: string) => {
  const files = await listAvatarFilesForUser(userId);
  await Promise.all(files.map((filename) => fs.unlink(join(AVATAR_STORAGE_DIR, filename)).catch(() => undefined)));
};

const parseAvatarPayload = (payload: unknown) => {
  const source = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? payload as { imageBase64?: unknown; mimeType?: unknown }
    : {};

  const rawBase64 = String(source.imageBase64 || '').trim();
  const requestedMimeType = String(source.mimeType || '').trim().toLowerCase();

  if (!rawBase64) {
    throw new Error('Avatar payload is empty');
  }

  const dataUrlMatch = rawBase64.match(/^data:([^;]+);base64,(.+)$/i);
  const mimeType = (requestedMimeType || (dataUrlMatch?.[1] || '').toLowerCase()).trim();
  const base64Data = (dataUrlMatch?.[2] || rawBase64).replace(/\s+/g, '');

  if (!AVATAR_ALLOWED_MIME_TYPES[mimeType]) {
    throw new Error('Unsupported avatar format. Allowed: ' + AVATAR_ALLOWED_FORMATS.join(', '));
  }

  if (!/^[A-Za-z0-9+/=]+$/.test(base64Data) || base64Data.length % 4 !== 0) {
    throw new Error('Avatar payload must be valid base64');
  }

  const buffer = Buffer.from(base64Data, 'base64');
  if (buffer.length === 0) {
    throw new Error('Avatar payload is empty after decoding');
  }

  if (buffer.length > AVATAR_MAX_SIZE_BYTES) {
    throw new Error('Avatar file is too large. Max: ' + Math.round(AVATAR_MAX_SIZE_BYTES / 1024 / 1024) + ' MB');
  }

  return {
    buffer,
    mimeType,
    extension: AVATAR_ALLOWED_MIME_TYPES[mimeType],
  };
};

router.get('/config', verifyToken, (_req, res) => {
  return res.status(200).json({
    allowedFormats: AVATAR_ALLOWED_FORMATS,
    maxSizeBytes: AVATAR_MAX_SIZE_BYTES,
  });
});

router.get('/me', verifyToken, async (req, res) => {
  const authReq = req as RequestWithAuth;

  try {
    const avatarFile = await resolveAvatarFileForUser(authReq.userId);
    if (!avatarFile) {
      return res.status(404).json({ message: 'Avatar not found' });
    }

    const filePath = join(AVATAR_STORAGE_DIR, avatarFile);
    const ext = avatarFile.split('.').pop() || '';
    const mimeByExt: Record<string, string> = {
      png: 'image/png',
      jpg: 'image/jpeg',
      jpeg: 'image/jpeg',
      webp: 'image/webp',
    };

    const contentType = mimeByExt[ext.toLowerCase()] || 'application/octet-stream';
    res.setHeader('Cache-Control', 'private, max-age=300');
    res.type(contentType);
    return res.sendFile(filePath);
  } catch {
    return res.status(404).json({ message: 'Avatar not found' });
  }
});

router.post('/me', verifyToken, async (req, res) => {
  const authReq = req as RequestWithAuth;

  try {
    const parsed = parseAvatarPayload(req.body);
    const safeId = sanitizeUserIdForFilename(authReq.userId);
    const nextFilename = safeId + '.' + parsed.extension;

    await ensureAvatarStorageDir();
    await removeAvatarFilesForUser(authReq.userId);
    await fs.writeFile(join(AVATAR_STORAGE_DIR, nextFilename), parsed.buffer);

    setTelemetryContext(res, {
      area: 'auth',
      resource: 'profile_avatar',
      action: 'update',
      userId: authReq.userId,
      targetUserId: authReq.userId,
      isAuthenticated: true,
      outcome: 'success',
      metadata: {
        mime_type: parsed.mimeType,
        bytes: parsed.buffer.length,
      },
    });

    setAuditContext(res, {
      resource: 'profile_avatar',
      action: 'update',
      targetType: 'user',
      targetId: authReq.userId,
      message: 'Profile avatar updated',
      metadata: {
        mime_type: parsed.mimeType,
        bytes: parsed.buffer.length,
      },
    });

    return res.status(200).json({
      success: true,
      message: 'Avatar uploaded successfully',
      allowedFormats: AVATAR_ALLOWED_FORMATS,
      maxSizeBytes: AVATAR_MAX_SIZE_BYTES,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Avatar upload failed';
    return res.status(400).json({
      message,
      allowedFormats: AVATAR_ALLOWED_FORMATS,
      maxSizeBytes: AVATAR_MAX_SIZE_BYTES,
    });
  }
});

router.delete('/me', verifyToken, async (req, res) => {
  const authReq = req as RequestWithAuth;

  await removeAvatarFilesForUser(authReq.userId);

  setTelemetryContext(res, {
    area: 'auth',
    resource: 'profile_avatar',
    action: 'delete',
    userId: authReq.userId,
    targetUserId: authReq.userId,
    isAuthenticated: true,
    outcome: 'success',
  });

  setAuditContext(res, {
    resource: 'profile_avatar',
    action: 'delete',
    targetType: 'user',
    targetId: authReq.userId,
    message: 'Profile avatar removed',
  });

  return res.status(200).json({ success: true, message: 'Avatar removed' });
});

export default router;
