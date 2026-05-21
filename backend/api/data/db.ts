import pkg from 'pg';
const { Pool } = pkg;
import { config } from 'dotenv';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { redisDel, redisGetJson, redisSetJson } from './redis.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

config({ path: join(__dirname, '../../..', '.env') });

const requiredInProduction = (name: string, fallback: string) => {
    const value = process.env[name];

    if (!value && process.env.NODE_ENV === 'production') {
        throw new Error(`${name} is required in production`);
    }

    return value || fallback;
};

const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    user: requiredInProduction('DB_USER', 'admin'),
    password: requiredInProduction('DB_PASSWORD', 'master_pass_2025'),
    database: requiredInProduction('DB_NAME', 'hebrew_db'),
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});

const USER_CACHE_TTL_SECONDS = 300;

const userProfileByIdKey = (id: string) => `user:profile:id:${id}`;
const userAuthByEmailKey = (email: string) => `user:auth:email:${email.trim().toLowerCase()}`;
const userAuthByUsernameKey = (username: string) => `user:auth:username:${username.trim().toLowerCase()}`;

const toPublicUser = (user: any) => ({
    id: user.id,
    email: user.email,
    username: user.username,
    first_name: user.first_name,
    last_name: user.last_name,
    role: user.role,
    xp_total: user.xp_total,
    level: user.level,
    created_at: user.created_at,
    updated_at: user.updated_at,
    registered_at: user.registered_at,
    last_login: user.last_login,
});

const cacheUserRecord = async (user: any) => {
    if (!user?.id || !user?.email) {
        return;
    }

    const publicUser = toPublicUser(user);
    await redisSetJson(userProfileByIdKey(user.id), publicUser, USER_CACHE_TTL_SECONDS);

    if (user.password_hash) {
        await redisSetJson(userAuthByEmailKey(user.email), user, USER_CACHE_TTL_SECONDS);

        if (user.username) {
            await redisSetJson(userAuthByUsernameKey(user.username), user, USER_CACHE_TTL_SECONDS);
        }
    }
};

const invalidateUserCaches = async (user: { id?: string; email?: string; username?: string }) => {
    const keys: string[] = [];

    if (user.id) {
        keys.push(userProfileByIdKey(user.id));
    }

    if (user.email) {
        keys.push(userAuthByEmailKey(user.email));
    }

    if (user.username) {
        keys.push(userAuthByUsernameKey(user.username));
    }

    await redisDel(...keys);
};

export const db = {
    query: (text: string, params?: any[]) => pool.query(text, params),

    // --- USER METHODS ---

    createUser: async (email: string, passwordHash: string, username: string, firstName: string, lastName: string) => {
        const query = `
            INSERT INTO users (email, password_hash, username, first_name, last_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *;
        `;
        const res = await pool.query(query, [email, passwordHash, username, firstName, lastName]);
        const user = res.rows[0];
        await cacheUserRecord(user);
        return toPublicUser(user);
    },

    getUserByEmail: async (email: string) => {
        const cacheKey = userAuthByEmailKey(email);
        const cached = await redisGetJson<any>(cacheKey);
        if (cached) {
            return cached;
        }

        const query = 'SELECT * FROM users WHERE lower(email) = lower($1) AND deleted_at IS NULL LIMIT 1';
        const res = await pool.query(query, [email]);
        const user = res.rows[0];

        if (user) {
            await cacheUserRecord(user);
        }

        return user;
    },

    getUserByUsername: async (username: string) => {
        const cacheKey = userAuthByUsernameKey(username);
        const cached = await redisGetJson<any>(cacheKey);
        if (cached) {
            return cached;
        }

        const query = 'SELECT * FROM users WHERE lower(username) = lower($1) AND deleted_at IS NULL LIMIT 1';
        const res = await pool.query(query, [username]);
        const user = res.rows[0];

        if (user) {
            await cacheUserRecord(user);
        }

        return user;
    },

    getUserById: async (id: string) => {
        const cacheKey = userProfileByIdKey(id);
        const cached = await redisGetJson<any>(cacheKey);
        if (cached) {
            return cached;
        }

        const query = `
            SELECT id, email, username, first_name, last_name, role, xp_total, level, created_at, updated_at, registered_at, last_login
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
            LIMIT 1
        `;
        const res = await pool.query(query, [id]);
        const user = res.rows[0];

        if (user) {
            await redisSetJson(cacheKey, user, USER_CACHE_TTL_SECONDS);
        }

        return user;
    },

    cacheUser: async (user: any) => {
        await cacheUserRecord(user);
    },

    invalidateUserCache: async (user: { id?: string; email?: string; username?: string }) => {
        await invalidateUserCaches(user);
    },

    // --- ITEM METHODS ---

    createItem: async (name: string, description: string, category: string, price: number) => {
        const query = `
            INSERT INTO items (name, description, category, price)
            VALUES ($1, $2, $3, $4)
            RETURNING *;
        `;
        const res = await pool.query(query, [name, description, category, price]);
        return res.rows[0];
    },

    searchItems: async (searchTerm: string) => {
        const query = `
            SELECT id, name, description, category, price, 
                   ts_rank(search_vector, to_tsquery('english', $1)) as rank
            FROM items
            WHERE search_vector @@ to_tsquery('english', $1)
            ORDER BY rank DESC
            LIMIT 50;
        `;
        const formattedSearch = searchTerm.trim().split(/\s+/).join(' & ');
        const res = await pool.query(query, [formattedSearch]);
        return res.rows;
    },

    deleteItem: async (id: string) => {
        const query = 'DELETE FROM items WHERE id = $1 RETURNING id';
        const res = await pool.query(query, [id]);
        return res.rows[0];
    },

    updateUserXP: async (userId: string, xpToAdd: number) => {
        const query = `
            UPDATE users 
            SET xp_total = xp_total + $1,
                level = floor((xp_total + $1) / 100) + 1
            WHERE id = $2
            RETURNING xp_total, level;
        `;
        const res = await pool.query(query, [xpToAdd, userId]);
        const updated = res.rows[0];

        if (updated) {
            await invalidateUserCaches({ id: userId });
        }

        return updated;
    },

    // --- LESSONS ---
    getAllLessons: async () => {
        const res = await pool.query('SELECT * FROM items WHERE category = $1', ['lesson']);
        return res.rows;
    },

    getLessonById: async (id: string) => {
        const res = await pool.query('SELECT * FROM items WHERE id = $1 AND category = $2', [id, 'lesson']);
        return res.rows[0];
    },

    createLesson: async (data: any) => {
        const query = `
            INSERT INTO items (name, description, category, price)
            VALUES ($1, $2, $3, $4)
            RETURNING *;
        `;
        const res = await pool.query(query, [data.title, data.description, 'lesson', 0]);
        return res.rows[0];
    },

    updateLesson: async (id: string, updates: any) => {
        const query = `
            UPDATE items 
            SET name = COALESCE($1, name),
                description = COALESCE($2, description)
            WHERE id = $3 AND category = 'lesson'
            RETURNING *;
        `;
        const res = await pool.query(query, [updates.title, updates.description, id]);
        return res.rows[0];
    },

    completeItemWithXp: async (userId: string, itemId: string, xpToAdd: number) => {
        const acquisition = await pool.query(
            'INSERT INTO user_items (user_id, item_id) VALUES ($1, $2) ON CONFLICT DO NOTHING RETURNING item_id',
            [userId, itemId]
        );

        if ((acquisition.rowCount ?? 0) === 0) {
            const user = await db.getUserById(userId);
            return { ...user, xpEarned: 0 };
        }

        const progress = await db.updateUserXP(userId, xpToAdd);
        return { ...progress, xpEarned: xpToAdd };
    },

    completeLesson: async (userId: string, lessonId: string) => {
        return await db.completeItemWithXp(userId, lessonId, 50);
    },

    // --- QUIZZES ---
    getAllQuizzes: async () => {
        const res = await pool.query('SELECT * FROM items WHERE category = $1', ['quiz']);
        return res.rows;
    },

    getQuizById: async (id: string) => {
        const res = await pool.query('SELECT * FROM items WHERE id = $1 AND category = $2', [id, 'quiz']);
        return res.rows[0];
    },

    getUserProgress: async (userId: string) => {
        const user = await db.getUserById(userId);
        if (!user) return null;

        const res = await pool.query('SELECT item_id FROM user_items WHERE user_id = $1', [userId]);
        const acquisitions = res.rows.map(r => r.item_id);

        return {
            userId,
            level: user.level,
            xpTotal: user.xp_total,
            lessonsCompleted: acquisitions,
            quizzesCompleted: [],
            lastActiveDate: new Date().toISOString()
        };
    },

    getAllUsers: async () => {
        const res = await pool.query('SELECT id, username, email, first_name, last_name, xp_total, level FROM users WHERE deleted_at IS NULL');
        return res.rows;
    }
};
