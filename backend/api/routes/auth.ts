import { Request, Response, Router } from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import { randomUUID, timingSafeEqual } from 'crypto';
import { db } from '../data/db.js';
import {
  ACCESS_COOKIE_NAME,
  REFRESH_COOKIE_NAME,
  clearAuthCookies,
  buildRequestFingerprint,
  getAccessCookieOptions,
  getRefreshCookieOptions,
  getClientIp,
  getRefreshTokenTtlMs,
  hashRefreshToken,
  signAccessToken,
  signRefreshToken,
  verifyToken,
  verifyTypedToken
} from '../middleware/auth.js';
import { loginLimiter } from '../middleware/security.js';
import {
  isValidEmail,
  isValidUsername,
  normalizeEmail,
  normalizeUsername,
  validatePassword,
  PASSWORD_RULES_TEXT
} from '../security/credentials.js';

const router = Router();
const SALT_ROUNDS = 12;
const MAX_FAILED_LOGIN_ATTEMPTS = 5;
const LOCK_WINDOW_MINUTES = 15;

const secureEquals = (a: string, b: string) => {
  const aBuffer = Buffer.from(a);
  const bBuffer = Buffer.from(b);

  if (aBuffer.length !== bBuffer.length) {
    return false;
  }

  return timingSafeEqual(aBuffer, bBuffer);
};

const getAuthClaimsFromToken = (token?: string | null) => {
  if (!token) {
    return null;
  }

  const decoded = jwt.decode(token);
  if (!decoded || typeof decoded === 'string') {
    return null;
  }

  const id = typeof decoded.id === 'string' ? decoded.id : null;
  const sid = typeof decoded.sid === 'string' ? decoded.sid : null;

  if (!id || !sid) {
    return null;
  }

  return { id, sid };
};

const createSessionAndTokens = async (req: Request, userId: string) => {
  const sessionId = randomUUID();
  const accessToken = signAccessToken(userId, sessionId);
  const refreshToken = signRefreshToken(userId, sessionId);
  const fingerprintHash = buildRequestFingerprint(req);

  await db.query(
    `INSERT INTO user_sessions (id, user_id, refresh_token_hash, fingerprint_hash, user_agent, ip_address, expires_at)
     VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP + ($7 || ' milliseconds')::interval)`,
    [
      sessionId,
      userId,
      hashRefreshToken(refreshToken),
      fingerprintHash,
      req.get('user-agent') || null,
      getClientIp(req) || null,
      getRefreshTokenTtlMs()
    ]
  );

  return { accessToken, refreshToken };
};

const setAuthCookies = (res: Response, accessToken: string, refreshToken: string) => {
  res.cookie(ACCESS_COOKIE_NAME, accessToken, getAccessCookieOptions());
  res.cookie(REFRESH_COOKIE_NAME, refreshToken, getRefreshCookieOptions());
};

const toPublicUser = (user: any) => ({
  id: user.id,
  email: user.email,
  username: user.username,
  first_name: user.first_name,
  last_name: user.last_name,
  role: user.role,
  created_at: user.created_at,
  updated_at: user.updated_at,
  registered_at: user.registered_at,
  last_login: user.last_login,
  xp_total: user.xp_total,
  level: user.level,
});

// POST /api/auth/register
router.post('/register', loginLimiter, async (req, res) => {
  const {
    email,
    password,
    confirmPassword,
    username,
    nickname,
    firstName,
    lastName,
  } = req.body || {};

  if (!email || !password || !confirmPassword) {
    return res.status(400).json({ message: 'Email, пароль и подтверждение пароля обязательны' });
  }

  const normalizedEmail = normalizeEmail(String(email));
  const normalizedUsername = normalizeUsername(String(username || nickname || ''));

  if (!isValidEmail(normalizedEmail)) {
    return res.status(400).json({ message: 'Некорректный email' });
  }

  if (!isValidUsername(normalizedUsername)) {
    return res.status(400).json({ message: 'Некорректный username. Разрешены: буквы, цифры, ., _, - (3-50 символов)' });
  }

  if (String(password) !== String(confirmPassword)) {
    return res.status(400).json({ message: 'Пароли не совпадают' });
  }

  const passwordValidation = validatePassword(String(password), {
    username: normalizedUsername,
    email: normalizedEmail,
  });

  if (!passwordValidation.valid) {
    return res.status(400).json({
      message: `Пароль не соответствует требованиям: ${passwordValidation.errors.join('; ')}`,
      passwordRules: PASSWORD_RULES_TEXT,
    });
  }

  try {
    const existingUserByEmail = await db.getUserByEmail(normalizedEmail);
    if (existingUserByEmail) {
      return res.status(409).json({ message: 'Пользователь с таким email уже существует' });
    }

    const existingUserByUsername = await db.getUserByUsername(normalizedUsername);
    if (existingUserByUsername) {
      return res.status(409).json({ message: 'Пользователь с таким username уже существует' });
    }

    const passwordHash = await bcrypt.hash(String(password), SALT_ROUNDS);

    const firstNameValue = String(firstName || '').trim();
    const lastNameValue = String(lastName || '').trim();

    const newUserRes = await db.query(
      `INSERT INTO users (email, password_hash, username, first_name, last_name, registered_at, password_changed_at)
       VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
       RETURNING id, email, username, first_name, last_name, role, xp_total, level, created_at, updated_at, registered_at, last_login`,
      [normalizedEmail, passwordHash, normalizedUsername, firstNameValue, lastNameValue]
    );

    const user = newUserRes.rows[0];
    const { accessToken, refreshToken } = await createSessionAndTokens(req, user.id);

    setAuthCookies(res, accessToken, refreshToken);
    await db.cacheUser(user);

    res.status(201).json({
      ...toPublicUser(user),
      token: accessToken,
    });
  } catch (err) {
    console.error('Registration error:', err);
    res.status(500).json({ message: 'Internal Server Error' });
  }
});

// POST /api/auth/login
router.post('/login', loginLimiter, async (req, res) => {
  const { email, password } = req.body || {};

  if (!email || !password) {
    return res.status(400).json({ message: 'Email и пароль обязательны' });
  }

  const normalizedEmail = normalizeEmail(String(email));
  if (!isValidEmail(normalizedEmail)) {
    return res.status(400).json({ message: 'Некорректный email' });
  }

  try {
    const user = await db.getUserByEmail(normalizedEmail);
    if (!user) {
      return res.status(401).json({ message: 'Неверные учетные данные' });
    }

    if (user.locked_until && new Date(user.locked_until).getTime() > Date.now()) {
      return res.status(423).json({
        message: 'Аккаунт временно заблокирован из-за большого числа неудачных попыток входа',
        lockedUntil: user.locked_until,
      });
    }

    const isMatch = await bcrypt.compare(String(password), user.password_hash);
    if (!isMatch) {
      const failRes = await db.query(
        `UPDATE users
         SET failed_login_attempts = failed_login_attempts + 1,
             locked_until = CASE
               WHEN failed_login_attempts + 1 >= $1
                 THEN CURRENT_TIMESTAMP + ($2 || ' minutes')::interval
               ELSE locked_until
             END,
             updated_at = CURRENT_TIMESTAMP
         WHERE id = $3
         RETURNING failed_login_attempts, locked_until, id, email, username`,
        [MAX_FAILED_LOGIN_ATTEMPTS, LOCK_WINDOW_MINUTES, user.id]
      );

      const failInfo = failRes.rows[0];
      await db.invalidateUserCache({ id: user.id, email: user.email, username: user.username });

      if (failInfo?.locked_until && new Date(failInfo.locked_until).getTime() > Date.now()) {
        return res.status(423).json({
          message: 'Аккаунт временно заблокирован из-за большого числа неудачных попыток входа',
          lockedUntil: failInfo.locked_until,
        });
      }

      return res.status(401).json({ message: 'Неверные учетные данные' });
    }

    const updateRes = await db.query(
      `UPDATE users
       SET last_login = CURRENT_TIMESTAMP,
           failed_login_attempts = 0,
           locked_until = NULL,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $1
       RETURNING id, email, username, first_name, last_name, role, xp_total, level, created_at, updated_at, registered_at, last_login`,
      [user.id]
    );

    const updatedUser = updateRes.rows[0];

    const { accessToken, refreshToken } = await createSessionAndTokens(req, user.id);
    setAuthCookies(res, accessToken, refreshToken);

    await db.invalidateUserCache({ id: user.id, email: user.email, username: user.username });
    await db.cacheUser(updatedUser);

    res.json({
      ...toPublicUser(updatedUser),
      token: accessToken,
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ message: 'Internal Server Error' });
  }
});

// POST /api/auth/refresh
router.post('/refresh', async (req, res) => {
  const refreshToken = req.cookies[REFRESH_COOKIE_NAME] as string | undefined;

  if (!refreshToken) {
    clearAuthCookies(res);
    return res.status(401).json({ message: 'Refresh token missing' });
  }

  try {
    const decoded = verifyTypedToken(refreshToken, 'refresh');

    const sessionRes = await db.query(
      `SELECT id, user_id, refresh_token_hash, fingerprint_hash
       FROM user_sessions
       WHERE id = $1
         AND user_id = $2
         AND revoked_at IS NULL
         AND expires_at > CURRENT_TIMESTAMP
       LIMIT 1`,
      [decoded.sid, decoded.id]
    );

    const session = sessionRes.rows[0];
    if (!session) {
      clearAuthCookies(res);
      return res.status(401).json({ message: 'Session expired' });
    }

    const currentRefreshHash = hashRefreshToken(refreshToken);
    if (!secureEquals(currentRefreshHash, session.refresh_token_hash as string)) {
      await db.query('UPDATE user_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE id = $1', [decoded.sid]);
      clearAuthCookies(res);
      return res.status(401).json({ message: 'Refresh token mismatch' });
    }

    const currentFingerprint = buildRequestFingerprint(req);
    if (!secureEquals(currentFingerprint, session.fingerprint_hash as string)) {
      await db.query('UPDATE user_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE id = $1', [decoded.sid]);
      clearAuthCookies(res);
      return res.status(401).json({ message: 'Fingerprint mismatch' });
    }

    const newAccessToken = signAccessToken(decoded.id, decoded.sid);
    const newRefreshToken = signRefreshToken(decoded.id, decoded.sid);

    await db.query(
      `UPDATE user_sessions
       SET refresh_token_hash = $1,
           last_seen_at = CURRENT_TIMESTAMP,
           expires_at = CURRENT_TIMESTAMP + ($2 || ' milliseconds')::interval
       WHERE id = $3`,
      [hashRefreshToken(newRefreshToken), getRefreshTokenTtlMs(), decoded.sid]
    );

    setAuthCookies(res, newAccessToken, newRefreshToken);

    return res.json({ authenticated: true });
  } catch (_err) {
    clearAuthCookies(res);
    return res.status(401).json({ message: 'Invalid refresh token' });
  }
});

// GET /api/auth/verify
router.get('/verify', verifyToken, async (req, res) => {
  const userId = (req as Request & { userId: string }).userId;
  const user = await db.getUserById(userId);

  if (!user) {
    clearAuthCookies(res);
    return res.status(401).json({ authenticated: false });
  }

  return res.json({
    authenticated: true,
    id: user.id,
    email: user.email,
    username: user.username,
    role: user.role
  });
});

// GET /api/auth/me
router.get('/me', verifyToken, async (req, res) => {
  const userId = (req as Request & { userId: string }).userId;
  const user = await db.getUserById(userId);

  if (!user) {
    clearAuthCookies(res);
    return res.status(401).json({ message: 'Пользователь не найден' });
  }

  res.json(user);
});

// POST /api/auth/logout
router.post('/logout', async (req, res) => {
  try {
    const accessToken = req.cookies[ACCESS_COOKIE_NAME] as string | undefined;
    const refreshToken = req.cookies[REFRESH_COOKIE_NAME] as string | undefined;

    const accessClaims = getAuthClaimsFromToken(accessToken);
    const refreshClaims = getAuthClaimsFromToken(refreshToken);
    const sessionId = accessClaims?.sid || refreshClaims?.sid;

    if (sessionId) {
      await db.query('UPDATE user_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE id = $1', [sessionId]);
    }
  } catch (err) {
    console.error('Logout error:', err);
  }

  clearAuthCookies(res);
  res.json({ message: 'Вышли из системы' });
});

export default router;
