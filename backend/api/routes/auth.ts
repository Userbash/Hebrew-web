import { Request, Response, Router } from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import MailChecker from 'mailchecker';
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
  verifyTypedToken,
  type RequestWithAuth
} from '../middleware/auth.js';
import { loginLimiter } from '../middleware/security.js';
import { setTelemetryContext } from '../middleware/telemetry.js';
import { setAuditContext } from '../middleware/auditTrail.js';
import {
  isValidEmail,
  isValidUsername,
  normalizeEmail,
  normalizeUsername,
  validatePassword,
  PASSWORD_RULES_TEXT
} from '../security/credentials.js';
import { isBlockedEmailByDomainPolicy } from '../security/emailDomainBlocklist.js';
import { getUserAccessProfile } from '../security/rbacService.js';

const router = Router();
const SALT_ROUNDS = 12;
const MAX_FAILED_LOGIN_ATTEMPTS = 5;
const LOCK_WINDOW_MINUTES = 15;
const USERNAME_SUGGESTION_COUNT = 8;

const isBlockedEmailForRegistration = (email: string) => {
  if (!MailChecker.isValid(email)) {
    return true;
  }

  return isBlockedEmailByDomainPolicy(email);
};

const sanitizeUsernameSeed = (value: string) => {
  const normalized = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_.-]/g, '')
    .replace(/[_.-]{2,}/g, '.')
    .replace(/^[_.-]+|[_.-]+$/g, '');

  if (normalized.length >= 3) {
    return normalized.slice(0, 50);
  }

  return 'user';
};

const applyUsernameLength = (candidate: string) => {
  const trimmed = candidate.slice(0, 50).replace(/[_.-]+$/g, '');
  if (trimmed.length >= 3) {
    return trimmed;
  }

  return 'user001';
};

const buildUsernameSuggestions = async (requestedUsername: string, email: string) => {
  const localPart = email.split('@')[0] || 'user';
  const baseVariants = Array.from(new Set([
    sanitizeUsernameSeed(requestedUsername),
    sanitizeUsernameSeed(localPart),
  ]));

  const semanticTokens = [
    'learn',
    'ivrit',
    'mentor',
    'focus',
    'guide',
    'craft',
    'quest',
    'spark',
    'atlas',
    'pilot',
    'study',
    'pro',
  ];

  const yearSuffix = String(new Date().getUTCFullYear());
  const candidatePool: string[] = [];

  for (const base of baseVariants) {
    candidatePool.push(
      `${base}.learn`,
      `${base}_ivrit`,
      `${base}-mentor`,
      `${base}.guide`,
      `${base}${yearSuffix}`,
      `${base}.study`,
      `learn.${base}`,
      `${base}_craft`,
      `${base}.quest`,
      `${base}_spark`,
      `${base}.atlas`,
      `${base}.pilot`,
      `${base}.pro`,
    );
  }

  for (const base of baseVariants) {
    for (const token of semanticTokens) {
      candidatePool.push(`${base}.${token}`);
      candidatePool.push(`${base}_${token}`);
      candidatePool.push(`${token}.${base}`);
    }
  }

  const uniqueCandidates = Array.from(new Set(candidatePool.map((candidate) => applyUsernameLength(candidate))));

  const suggestions: string[] = [];

  for (const candidate of uniqueCandidates) {
    if (!isValidUsername(candidate)) {
      continue;
    }

    const existing = await db.getUserByUsername(candidate);
    if (existing) {
      continue;
    }

    suggestions.push(candidate);
    if (suggestions.length >= USERNAME_SUGGESTION_COUNT) {
      break;
    }
  }

  if (suggestions.length >= USERNAME_SUGGESTION_COUNT) {
    return suggestions.slice(0, USERNAME_SUGGESTION_COUNT);
  }

  let numericSuffix = 101;
  const reserved = new Set(suggestions);
  while (suggestions.length < USERNAME_SUGGESTION_COUNT && numericSuffix < 9999) {
    for (const base of baseVariants) {
      const candidate = applyUsernameLength(`${base}${numericSuffix}`);
      numericSuffix += 1;

      if (reserved.has(candidate) || !isValidUsername(candidate)) {
        continue;
      }

      const existing = await db.getUserByUsername(candidate);
      if (existing) {
        continue;
      }

      suggestions.push(candidate);
      reserved.add(candidate);

      if (suggestions.length >= USERNAME_SUGGESTION_COUNT) {
        break;
      }
    }
  }

  return suggestions.slice(0, USERNAME_SUGGESTION_COUNT);
};

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

  return { sessionId, accessToken, refreshToken };
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

const buildAuthResponseUser = async (user: any) => {
  const access = await getUserAccessProfile(user.id);

  return {
    ...toPublicUser(user),
    access: access
      ? {
          roleKeys: access.roleKeys,
          highestRole: access.highestRole,
          highestPriority: access.highestPriority,
          isSystemBlocked: access.isSystemBlocked,
        }
      : null,
  };
};

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

  if (isBlockedEmailForRegistration(normalizedEmail)) {
    return res.status(400).json({
      message: 'Регистрация с этим email запрещена: одноразовая или заблокированная почта',
      field: 'email',
      code: 'EMAIL_DOMAIN_NOT_ALLOWED',
    });
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
    const [existingUserByEmail, existingUserByUsername] = await Promise.all([
      db.getUserByEmail(normalizedEmail),
      db.getUserByUsername(normalizedUsername),
    ]);

    if (existingUserByEmail && existingUserByUsername) {
      return res.status(409).json({
        message: 'Пользователь с таким email и username уже существует',
        field: 'both',
        code: 'EMAIL_AND_USERNAME_EXISTS',
      });
    }

    if (existingUserByEmail) {
      return res.status(409).json({
        message: 'Пользователь с таким email уже существует',
        field: 'email',
        code: 'EMAIL_EXISTS',
      });
    }

    if (existingUserByUsername) {
      const suggestions = await buildUsernameSuggestions(normalizedUsername, normalizedEmail);
      return res.status(409).json({
        message: 'Пользователь с таким username уже существует',
        field: 'username',
        code: 'USERNAME_EXISTS',
        suggestions,
      });
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

    const responseUser = await buildAuthResponseUser(user);
    res.status(201).json(responseUser);
  } catch (err: unknown) {
    const conflict = err as { code?: string; constraint?: string };

    if (conflict?.code === '23505') {
      if (conflict.constraint?.includes('email')) {
        return res.status(409).json({
          message: 'Пользователь с таким email уже существует',
          field: 'email',
          code: 'EMAIL_EXISTS',
        });
      }

      if (conflict.constraint?.includes('username')) {
        const suggestions = await buildUsernameSuggestions(normalizedUsername, normalizedEmail);
        return res.status(409).json({
          message: 'Пользователь с таким username уже существует',
          field: 'username',
          code: 'USERNAME_EXISTS',
          suggestions,
        });
      }
    }

    console.error('Registration error:', err);
    res.status(500).json({ message: 'Internal Server Error' });
  }
});

// POST /api/auth/login
router.post('/login', loginLimiter, async (req, res) => {
  const { email, password } = req.body || {};
  const loginIdentifier = normalizeEmail(String(email || ''));

  setTelemetryContext(res, {
    area: 'auth',
    resource: 'auth',
    action: 'login',
    loginIdentifier: loginIdentifier || null,
    isAuthenticated: false,
  });

  if (!email || !password) {
    setTelemetryContext(res, {
      outcome: 'error',
      metadata: { reason: 'missing_credentials' },
    });

    return res.status(400).json({ message: 'Email и пароль обязательны' });
  }

  const normalizedEmail = normalizeEmail(String(email));
  if (!isValidEmail(normalizedEmail)) {
    setTelemetryContext(res, {
      loginIdentifier: normalizedEmail,
      outcome: 'error',
      metadata: { reason: 'invalid_email_format' },
    });

    return res.status(400).json({ message: 'Некорректный email' });
  }

  try {
    const user = await db.getUserByEmail(normalizedEmail);
    if (!user) {
      setTelemetryContext(res, {
        loginIdentifier: normalizedEmail,
        outcome: 'blocked',
        accountLocked: false,
        hadPreviousLogin: false,
        failedLoginAttempts: 0,
        metadata: { reason: 'user_not_found' },
      });

      setAuditContext(res, {
        resource: 'auth',
        action: 'login',
        message: 'Login failed: user not found',
        metadata: { login_identifier: normalizedEmail },
      });

      return res.status(401).json({ message: 'Неверные учетные данные' });
    }

    const hadPreviousLogin = Boolean(user.last_login);
    const lockIsActive = Boolean(user.locked_until && new Date(user.locked_until).getTime() > Date.now());

    if (lockIsActive) {
      setTelemetryContext(res, {
        targetUserId: user.id,
        loginIdentifier: normalizedEmail,
        userRole: user.role,
        outcome: 'blocked',
        accountLocked: true,
        hadPreviousLogin,
        failedLoginAttempts: user.failed_login_attempts || 0,
        metadata: {
          reason: 'locked_until_active',
          locked_until: user.locked_until || null,
        },
      });

      setAuditContext(res, {
        resource: 'auth',
        action: 'login',
        targetType: 'user',
        targetId: user.id,
        message: 'Login blocked: account temporarily locked',
        metadata: {
          locked_until: user.locked_until || null,
          failed_login_attempts: user.failed_login_attempts || 0,
        },
      });

      return res.status(423).json({
        message: 'Аккаунт временно заблокирован из-за большого числа неудачных попыток входа',
        lockedUntil: user.locked_until,
      });
    }

    if (!user.password_hash) {
      setTelemetryContext(res, {
        targetUserId: user.id,
        loginIdentifier: normalizedEmail,
        outcome: 'blocked',
        accountLocked: false,
        hadPreviousLogin,
        failedLoginAttempts: user.failed_login_attempts || 0,
        metadata: { reason: 'missing_password_hash' },
      });

      setAuditContext(res, {
        resource: 'auth',
        action: 'login',
        targetType: 'user',
        targetId: user.id,
        message: 'Login blocked: no password hash',
      });

      return res.status(401).json({ message: 'Неверные учетные данные' });
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

      const failInfo = failRes.rows[0] as {
        failed_login_attempts?: number;
        locked_until?: string | null;
      } | undefined;

      await db.invalidateUserCache({ id: user.id, email: user.email, username: user.username });

      const nowLocked = Boolean(failInfo?.locked_until && new Date(String(failInfo.locked_until)).getTime() > Date.now());
      const failedAttempts = failInfo?.failed_login_attempts || 0;

      setTelemetryContext(res, {
        targetUserId: user.id,
        loginIdentifier: normalizedEmail,
        userRole: user.role,
        outcome: 'blocked',
        accountLocked: nowLocked,
        hadPreviousLogin,
        failedLoginAttempts: failedAttempts,
        metadata: {
          reason: 'invalid_password',
          locked_until: failInfo?.locked_until || null,
        },
      });

      setAuditContext(res, {
        resource: 'auth',
        action: 'login',
        targetType: 'user',
        targetId: user.id,
        message: nowLocked ? 'Login blocked: too many failed attempts' : 'Login failed: invalid password',
        metadata: {
          failed_login_attempts: failedAttempts,
          locked_until: failInfo?.locked_until || null,
        },
      });

      if (nowLocked) {
        return res.status(423).json({
          message: 'Аккаунт временно заблокирован из-за большого числа неудачных попыток входа',
          lockedUntil: failInfo?.locked_until || null,
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

    const { sessionId, accessToken, refreshToken } = await createSessionAndTokens(req, user.id);
    setAuthCookies(res, accessToken, refreshToken);

    await db.invalidateUserCache({ id: user.id, email: user.email, username: user.username });
    await db.cacheUser(updatedUser);

    const responseUser = await buildAuthResponseUser(updatedUser);

    setTelemetryContext(res, {
      userId: user.id,
      targetUserId: user.id,
      sessionId,
      loginIdentifier: normalizedEmail,
      isAuthenticated: true,
      userRole: updatedUser.role,
      highestRole: responseUser.access?.highestRole || updatedUser.role,
      roleKeys: responseUser.access?.roleKeys || [],
      isSystemBlocked: responseUser.access?.isSystemBlocked ?? null,
      hadPreviousLogin,
      accountLocked: false,
      failedLoginAttempts: 0,
      outcome: 'success',
      metadata: {
        reason: 'login_success',
      },
    });

    setAuditContext(res, {
      resource: 'auth',
      action: 'login',
      targetType: 'user',
      targetId: user.id,
      message: 'Login success',
      metadata: {
        had_previous_login: hadPreviousLogin,
        highest_role: responseUser.access?.highestRole || updatedUser.role,
        role_keys: responseUser.access?.roleKeys || [],
      },
    });

    res.json(responseUser);
  } catch (err) {
    setTelemetryContext(res, {
      loginIdentifier: normalizedEmail,
      outcome: 'error',
      metadata: { reason: 'internal_error' },
    });

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

  const responseUser = await buildAuthResponseUser(user);

  return res.json({
    authenticated: true,
    ...responseUser,
  });
});

// POST /api/auth/change-password
router.post("/change-password", verifyToken, async (req, res) => {
  const authReq = req as RequestWithAuth;
  const { currentPassword, newPassword, confirmPassword } = req.body || {};

  setTelemetryContext(res, {
    area: "auth",
    resource: "auth",
    action: "update",
    userId: authReq.userId,
    targetUserId: authReq.userId,
    isAuthenticated: true,
  });

  if (!currentPassword || !newPassword || !confirmPassword) {
    setTelemetryContext(res, {
      outcome: "error",
      metadata: { reason: "missing_change_password_fields" },
    });

    return res.status(400).json({ message: "Current password, new password and confirmation are required" });
  }

  if (String(newPassword) !== String(confirmPassword)) {
    setTelemetryContext(res, {
      outcome: "error",
      metadata: { reason: "password_confirmation_mismatch" },
    });

    return res.status(400).json({ message: "New password confirmation does not match" });
  }

  if (String(currentPassword) === String(newPassword)) {
    setTelemetryContext(res, {
      outcome: "blocked",
      metadata: { reason: "same_as_current_password" },
    });

    return res.status(400).json({ message: "New password must be different from current password" });
  }

  try {
    const userRes = await db.query(
      `SELECT id, email, username, password_hash, deleted_at
       FROM users
       WHERE id = $1
       LIMIT 1`,
      [authReq.userId]
    );

    const user = userRes.rows[0] as {
      id: string;
      email: string;
      username: string;
      password_hash: string | null;
      deleted_at: string | null;
    } | undefined;

    if (!user || user.deleted_at) {
      setTelemetryContext(res, {
        outcome: "error",
        metadata: { reason: "user_not_found" },
      });

      return res.status(404).json({ message: "User not found" });
    }

    if (!user.password_hash) {
      setTelemetryContext(res, {
        outcome: "blocked",
        metadata: { reason: "missing_password_hash" },
      });

      return res.status(400).json({ message: "Password cannot be changed for this account" });
    }

    const currentMatches = await bcrypt.compare(String(currentPassword), user.password_hash);
    if (!currentMatches) {
      setTelemetryContext(res, {
        outcome: "blocked",
        metadata: { reason: "current_password_mismatch" },
      });

      setAuditContext(res, {
        resource: "auth",
        action: "update",
        targetType: "user",
        targetId: authReq.userId,
        message: "Password change rejected: current password mismatch",
      });

      return res.status(400).json({ message: "Current password is incorrect" });
    }

    const passwordValidation = validatePassword(String(newPassword), {
      email: user.email,
      username: user.username,
    });

    if (!passwordValidation.valid) {
      setTelemetryContext(res, {
        outcome: "blocked",
        metadata: { reason: "new_password_policy_rejected" },
      });

      return res.status(400).json({
        message: "Password does not meet requirements: " + passwordValidation.errors.join("; "),
        passwordRules: PASSWORD_RULES_TEXT,
      });
    }

    const nextPasswordHash = await bcrypt.hash(String(newPassword), SALT_ROUNDS);

    await db.query(
      `UPDATE users
       SET password_hash = $1,
           password_changed_at = CURRENT_TIMESTAMP,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $2`,
      [nextPasswordHash, authReq.userId]
    );

    await db.query(
      `UPDATE user_sessions
       SET revoked_at = CURRENT_TIMESTAMP
       WHERE user_id = $1
         AND id <> $2
         AND revoked_at IS NULL`,
      [authReq.userId, authReq.sessionId]
    );

    await db.invalidateUserCache({
      id: user.id,
      email: user.email,
      username: user.username,
    });

    setTelemetryContext(res, {
      outcome: "success",
      metadata: { reason: "password_changed" },
    });

    setAuditContext(res, {
      resource: "auth",
      action: "update",
      targetType: "user",
      targetId: authReq.userId,
      message: "Password changed successfully",
    });

    return res.status(200).json({ success: true, message: "Password changed successfully" });
  } catch (err) {
    setTelemetryContext(res, {
      outcome: "error",
      metadata: { reason: "change_password_internal_error" },
    });

    console.error("Change password error:", err);
    return res.status(500).json({ message: "Internal Server Error" });
  }
});

// GET /api/auth/me
router.get('/me', verifyToken, async (req, res) => {
  const userId = (req as Request & { userId: string }).userId;
  const user = await db.getUserById(userId);

  if (!user) {
    clearAuthCookies(res);
    return res.status(401).json({ message: 'User not found' });
  }

  const responseUser = await buildAuthResponseUser(user);
  res.json(responseUser);
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
