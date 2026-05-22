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

const buildPoolConfig = () => {
    if (process.env.DATABASE_URL) {
        return {
            connectionString: process.env.DATABASE_URL,
            max: 20,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 2000,
        };
    }

    return {
        host: process.env.DB_HOST || '127.0.0.1',
        port: parseInt(process.env.DB_PORT || '5432', 10),
        user: requiredInProduction('DB_USER', 'postgres'),
        password: requiredInProduction('DB_PASSWORD', 'postgres123'),
        database: requiredInProduction('DB_NAME', 'hebrew_ai_db'),
        max: 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
    };
};

const pool = new Pool(buildPoolConfig());

type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
type JsonObject = { [key: string]: JsonValue };

export interface UserRow {
    ui_preferences?: Record<string, unknown> | null;
    id: string;
    email: string;
    username: string;
    first_name: string | null;
    last_name: string | null;
    role: 'user' | 'admin' | 'moderator';
    xp_total: number;
    level: number;
    created_at: string;
    updated_at: string;
    registered_at: string | null;
    last_login: string | null;
    password_hash?: string;
    streak?: number;
    locked_until?: string | null;
    failed_login_attempts?: number;
    is_system_blocked?: boolean;
}

export interface ItemMetadata {
    difficulty?: string;
    duration?: number;
    content?: JsonValue[];
    xpReward?: number;
    lessonId?: string;
    questions?: JsonValue[];
    correctAnswers?: Array<string | number | boolean | null>;
    passingScore?: number;
    authorId?: string;
    status?: string;
    tags?: string[];
    visibility?: 'private' | 'team' | 'public';
    publishedAt?: string | null;
    [key: string]: JsonValue | undefined;
}

export interface ItemRow {
    id: string;
    name: string;
    description: string | null;
    category: string | null;
    price: string | number;
    stock?: number | null;
    metadata?: ItemMetadata;
    created_at?: string;
    updated_at?: string;
}

export interface UserProgress {
    userId: string;
    level: number;
    xpTotal: number;
    lessonsCompleted: string[];
    quizzesCompleted: string[];
    lastActiveDate: string;
}

export interface QuizAttemptRow {
    id: string;
    user_id: string;
    quiz_id: string;
    answers: JsonValue;
    score: number;
    total_questions: number;
    passed: boolean;
    submitted_at: string;
}

const USER_CACHE_TTL_SECONDS = 300;

const userProfileByIdKey = (id: string) => `user:profile:id:${id}`;
const userAuthByEmailKey = (email: string) => `user:auth:email:${email.trim().toLowerCase()}`;
const userAuthByUsernameKey = (username: string) => `user:auth:username:${username.trim().toLowerCase()}`;

const toPublicUser = (user: UserRow) => ({
    id: user.id,
    email: user.email,
    username: user.username,
    first_name: user.first_name,
    last_name: user.last_name,
    role: user.role,
    xp_total: user.xp_total,
    level: user.level,
    ui_preferences: user.ui_preferences ?? {},
    created_at: user.created_at,
    updated_at: user.updated_at,
    registered_at: user.registered_at,
    last_login: user.last_login,
});

const cacheUserRecord = async (user: UserRow) => {
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

const parseItemMetadata = (raw: unknown): ItemMetadata => {
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
        return {};
    }

    return raw as ItemMetadata;
};

const mapItem = (row: Record<string, unknown>): ItemRow => ({
    ...(row as unknown as ItemRow),
    metadata: parseItemMetadata(row.metadata),
});

const stripUndefined = <T extends Record<string, unknown>>(value: T) => {
    const entries = Object.entries(value).filter(([, v]) => v !== undefined);
    return Object.fromEntries(entries);
};

const buildSearchQuery = (searchTerm: string, category?: string) => {
    const trimmed = searchTerm.trim();
    if (!trimmed) {
        return null;
    }

    const params: unknown[] = [trimmed];
    const categoryCondition = category
        ? (() => {
            params.push(category);
            return `AND category = $${params.length}`;
        })()
        : '';

    const query = `
        SELECT id, name, description, category, price, metadata,
               ts_rank(search_vector, plainto_tsquery('english', $1)) AS rank
        FROM items
        WHERE search_vector @@ plainto_tsquery('english', $1)
          ${categoryCondition}
        ORDER BY rank DESC
        LIMIT 50;
    `;

    return { query, params };
};

export const db = {
    query: (text: string, params?: unknown[]) => pool.query(text, params),

    createUser: async (email: string, passwordHash: string, username: string, firstName: string, lastName: string) => {
        const query = `
            INSERT INTO users (email, password_hash, username, first_name, last_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *;
        `;
        const res = await pool.query<UserRow>(query, [email, passwordHash, username, firstName, lastName]);
        const user = res.rows[0];
        await cacheUserRecord(user);
        return toPublicUser(user);
    },

    getUserByEmail: async (email: string) => {
        const cacheKey = userAuthByEmailKey(email);
        const cached = await redisGetJson<UserRow>(cacheKey);
        if (cached) {
            return cached;
        }

        const query = 'SELECT * FROM users WHERE lower(email) = lower($1) AND deleted_at IS NULL LIMIT 1';
        const res = await pool.query<UserRow>(query, [email]);
        const user = res.rows[0];

        if (user) {
            await cacheUserRecord(user);
        }

        return user;
    },

    getUserByUsername: async (username: string) => {
        const cacheKey = userAuthByUsernameKey(username);
        const cached = await redisGetJson<UserRow>(cacheKey);
        if (cached) {
            return cached;
        }

        const query = 'SELECT * FROM users WHERE lower(username) = lower($1) AND deleted_at IS NULL LIMIT 1';
        const res = await pool.query<UserRow>(query, [username]);
        const user = res.rows[0];

        if (user) {
            await cacheUserRecord(user);
        }

        return user;
    },

    getUserById: async (id: string) => {
        const cacheKey = userProfileByIdKey(id);
        const cached = await redisGetJson<UserRow>(cacheKey);
        if (cached) {
            return cached;
        }

        const query = `
            SELECT id, email, username, first_name, last_name, role, xp_total, level, streak, created_at, updated_at, registered_at, last_login, ui_preferences
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
            LIMIT 1
        `;
        const res = await pool.query<UserRow>(query, [id]);
        const user = res.rows[0];

        if (user) {
            await redisSetJson(cacheKey, user, USER_CACHE_TTL_SECONDS);
        }

        return user;
    },

    cacheUser: async (user: UserRow) => {
        await cacheUserRecord(user);
    },

    invalidateUserCache: async (user: { id?: string; email?: string; username?: string }) => {
        await invalidateUserCaches(user);
    },

    createItem: async (name: string, description: string, category: string, price: number, metadata: ItemMetadata = {}) => {
        const query = `
            INSERT INTO items (name, description, category, price, metadata)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            RETURNING *;
        `;
        const res = await pool.query(query, [name, description, category, price, JSON.stringify(metadata)]);
        return mapItem(res.rows[0]);
    },

    searchItems: async (searchTerm: string, options?: { category?: string }) => {
        const prepared = buildSearchQuery(searchTerm, options?.category);
        if (!prepared) {
            return [];
        }

        const res = await pool.query(prepared.query, prepared.params);
        return res.rows.map((row) => mapItem(row));
    },

    deleteItem: async (id: string) => {
        const query = 'DELETE FROM items WHERE id = $1 RETURNING id';
        const res = await pool.query<{ id: string }>(query, [id]);
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
        const res = await pool.query<{ xp_total: number; level: number }>(query, [xpToAdd, userId]);
        const updated = res.rows[0];

        if (updated) {
            await invalidateUserCaches({ id: userId });
        }

        return updated;
    },

    getAllLessons: async () => {
        const res = await pool.query('SELECT * FROM items WHERE category = $1 ORDER BY created_at DESC', ['lesson']);
        return res.rows.map((row) => mapItem(row));
    },

    getLessonById: async (id: string) => {
        const res = await pool.query('SELECT * FROM items WHERE id = $1 AND category = $2', [id, 'lesson']);
        const row = res.rows[0];
        return row ? mapItem(row) : null;
    },

    createLesson: async (data: {
        title: string;
        description: string;
        difficulty: string;
        duration: number;
        content: JsonValue[];
        xpReward: number;
    }) => {
        const metadata: ItemMetadata = {
            difficulty: data.difficulty,
            duration: data.duration,
            content: data.content,
            xpReward: data.xpReward,
        };

        const query = `
            INSERT INTO items (name, description, category, price, metadata)
            VALUES ($1, $2, 'lesson', 0, $3::jsonb)
            RETURNING *;
        `;
        const res = await pool.query(query, [data.title, data.description, JSON.stringify(metadata)]);
        return mapItem(res.rows[0]);
    },

    updateLesson: async (id: string, updates: {
        title?: string;
        description?: string;
        difficulty?: string;
        duration?: number;
        content?: JsonValue[];
        xpReward?: number;
    }) => {
        const metadataPatch = stripUndefined({
            difficulty: updates.difficulty,
            duration: updates.duration,
            content: updates.content,
            xpReward: updates.xpReward,
        });

        const query = `
            UPDATE items
            SET name = COALESCE($1, name),
                description = COALESCE($2, description),
                metadata = metadata || $3::jsonb
            WHERE id = $4 AND category = 'lesson'
            RETURNING *;
        `;
        const res = await pool.query(query, [
            updates.title,
            updates.description,
            JSON.stringify(metadataPatch),
            id,
        ]);

        const row = res.rows[0];
        return row ? mapItem(row) : null;
    },

    completeItemWithXp: async (userId: string, itemId: string, xpToAdd: number) => {
        const acquisition = await pool.query(
            'INSERT INTO user_items (user_id, item_id) VALUES ($1, $2) ON CONFLICT DO NOTHING RETURNING item_id',
            [userId, itemId]
        );

        if ((acquisition.rowCount ?? 0) === 0) {
            const user = await db.getUserById(userId);
            return {
                xp_total: user?.xp_total ?? 0,
                level: user?.level ?? 1,
                xpEarned: 0,
            };
        }

        const progress = await db.updateUserXP(userId, xpToAdd);
        return {
            xp_total: progress?.xp_total ?? 0,
            level: progress?.level ?? 1,
            xpEarned: xpToAdd,
        };
    },

    completeLesson: async (userId: string, lessonId: string) => {
        return db.completeItemWithXp(userId, lessonId, 50);
    },

    getAllQuizzes: async () => {
        const res = await pool.query('SELECT * FROM items WHERE category = $1 ORDER BY created_at DESC', ['quiz']);
        return res.rows.map((row) => mapItem(row));
    },

    getQuizById: async (id: string) => {
        const res = await pool.query('SELECT * FROM items WHERE id = $1 AND category = $2', [id, 'quiz']);
        const row = res.rows[0];
        return row ? mapItem(row) : null;
    },

    recordQuizAttempt: async (
        userId: string,
        quizId: string,
        answers: JsonValue,
        score: number,
        totalQuestions: number,
        passed: boolean
    ) => {
        const query = `
            INSERT INTO quiz_attempts (user_id, quiz_id, answers, score, total_questions, passed)
            VALUES ($1, $2, $3::jsonb, $4, $5, $6)
            RETURNING *;
        `;
        const res = await pool.query<QuizAttemptRow>(query, [
            userId,
            quizId,
            JSON.stringify(answers),
            score,
            totalQuestions,
            passed,
        ]);

        return res.rows[0];
    },

    getQuizAttemptsForUser: async (userId: string, quizId: string, limit = 20) => {
        const safeLimit = Math.max(1, Math.min(limit, 100));
        const query = `
            SELECT id, user_id, quiz_id, answers, score, total_questions, passed, submitted_at
            FROM quiz_attempts
            WHERE user_id = $1 AND quiz_id = $2
            ORDER BY submitted_at DESC
            LIMIT $3;
        `;
        const res = await pool.query<QuizAttemptRow>(query, [userId, quizId, safeLimit]);
        return res.rows;
    },

    getUserProgress: async (userId: string): Promise<UserProgress | null> => {
        const user = await db.getUserById(userId);
        if (!user) {
            return null;
        }

        const res = await pool.query<{ item_id: string; category: string | null }>(
            `SELECT ui.item_id, i.category
             FROM user_items ui
             JOIN items i ON i.id = ui.item_id
             WHERE ui.user_id = $1`,
            [userId]
        );

        const lessonsCompleted: string[] = [];
        const quizzesCompleted: string[] = [];

        for (const row of res.rows) {
            if (row.category === 'lesson') {
                lessonsCompleted.push(row.item_id);
                continue;
            }

            if (row.category === 'quiz') {
                quizzesCompleted.push(row.item_id);
            }
        }

        return {
            userId,
            level: user.level,
            xpTotal: user.xp_total,
            lessonsCompleted,
            quizzesCompleted,
            lastActiveDate: new Date().toISOString(),
        };
    },

    getAllUsers: async () => {
        const res = await pool.query('SELECT id, username, email, first_name, last_name, xp_total, level FROM users WHERE deleted_at IS NULL');
        return res.rows;
    },
};
