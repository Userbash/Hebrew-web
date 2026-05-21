import { Router } from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import { db } from '../data/db.js';
import { getJwtSecret } from '../middleware/auth.js';
import { loginLimiter } from '../middleware/security.js';

const router = Router();
const SALT_ROUNDS = 12; // High security factor

// POST /api/auth/register
router.post('/register', loginLimiter, async (req, res) => {
  const { email, password, firstName, lastName } = req.body;
  
  try {
    const existingUser = await db.getUserByEmail(email);
    if (existingUser) {
      return res.status(400).json({ message: 'Пользователь уже существует' });
    }

    // Secure Hashing
    const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

    const newUser = await db.createUser(
      email,
      passwordHash,
      firstName || '',
      lastName || ''
    );

    const token = jwt.sign({ id: newUser.id }, getJwtSecret(), { expiresIn: '24h' });

    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 24 * 60 * 60 * 1000
    });

    res.status(201).json(newUser);
  } catch (err) {
    console.error('Registration error:', err);
    res.status(500).json({ message: 'Internal Server Error' });
  }
});

// POST /api/auth/login
router.post('/login', loginLimiter, async (req, res) => {
  const { email, password } = req.body;
  
  try {
    const user = await db.getUserByEmail(email);
    if (!user) {
      return res.status(401).json({ message: 'Неверные учетные данные' });
    }

    // Secure comparison
    const isMatch = await bcrypt.compare(password, user.password_hash);
    if (!isMatch) {
      return res.status(401).json({ message: 'Неверные учетные данные' });
    }

    const token = jwt.sign({ id: user.id }, getJwtSecret(), { expiresIn: '24h' });

    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 24 * 60 * 60 * 1000
    });

    res.json({
      id: user.id,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      xp_total: user.xp_total,
      level: user.level
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ message: 'Internal Server Error' });
  }
});

// GET /api/auth/verify (Dedicated session check)
router.get('/verify', async (req, res) => {
  const token = req.cookies.token;
  if (!token) return res.status(401).json({ authenticated: false });

  try {
    const decoded: any = jwt.verify(token, getJwtSecret());
    const user = await db.getUserById(decoded.id);
    if (!user) return res.status(401).json({ authenticated: false });
    
    res.json({ 
      authenticated: true, 
      id: user.id, 
      email: user.email, 
      role: user.role 
    });
  } catch (err) {
    res.status(401).json({ authenticated: false });
  }
});

// GET /api/auth/me
router.get('/me', async (req, res) => {
  const token = req.cookies.token;
  if (!token) return res.status(401).json({ message: 'Не авторизован' });

  try {
    const decoded: any = jwt.verify(token, getJwtSecret());
    const user = await db.getUserById(decoded.id);
    if (!user) return res.status(401).json({ message: 'Пользователь не найден' });
    
    res.json(user);
  } catch (err) {
    res.status(401).json({ message: 'Невалидный токен' });
  }
});

// POST /api/auth/logout
router.post('/logout', (req, res) => {
  res.clearCookie('token');
  res.json({ message: 'Вышли из системы' });
});

export default router;
