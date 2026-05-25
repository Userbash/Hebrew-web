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
        ['password']: requiredInProduction('DB_PASSWORD', ''),
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



    markLessonCompletedProgress: async (userId: string, lessonId: string) => {
        await pool.query(
            `INSERT INTO user_lesson_progress (user_id, lesson_id, status, progress_percent, started_at, completed_at, updated_at)
             VALUES ($1, $2, 'completed', 100, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
             ON CONFLICT (user_id, lesson_id) DO UPDATE
               SET status = 'completed',
                   progress_percent = 100,
                   completed_at = COALESCE(user_lesson_progress.completed_at, CURRENT_TIMESTAMP),
                   updated_at = CURRENT_TIMESTAMP`,
            [userId, lessonId]
        );
    },

    getUserDashboardProgress: async (userId: string) => {
        const totalsRes = await pool.query<{ total_lessons: string; completed_lessons: string; active_lessons: string }>(
            `SELECT
                (SELECT COUNT(*) FROM items WHERE category = 'lesson') AS total_lessons,
                (SELECT COUNT(*) FROM user_lesson_progress WHERE user_id = $1 AND status = 'completed') AS completed_lessons,
                (SELECT COUNT(*) FROM user_lesson_progress WHERE user_id = $1 AND status = 'in_progress') AS active_lessons`,
            [userId]
        );

        const periodsRes = await pool.query<{ week_count: string; month_count: string; half_year_count: string; year_count: string }>(
            `SELECT
                COUNT(*) FILTER (WHERE ui.acquired_at >= NOW() - INTERVAL '7 days') AS week_count,
                COUNT(*) FILTER (WHERE ui.acquired_at >= NOW() - INTERVAL '30 days') AS month_count,
                COUNT(*) FILTER (WHERE ui.acquired_at >= NOW() - INTERVAL '183 days') AS half_year_count,
                COUNT(*) FILTER (WHERE ui.acquired_at >= NOW() - INTERVAL '365 days') AS year_count
             FROM user_items ui
             JOIN items i ON i.id = ui.item_id
             WHERE ui.user_id = $1
               AND i.category IN ('lesson', 'quiz')`,
            [userId]
        );

        const activeLessonsRes = await pool.query<{ lesson_id: string; name: string; updated_at: string; progress_percent: number; duration: string | null }>(
            `SELECT ulp.lesson_id, i.name, ulp.updated_at, ulp.progress_percent, i.metadata->>'duration' AS duration
             FROM user_lesson_progress ulp
             JOIN items i ON i.id = ulp.lesson_id
             WHERE ulp.user_id = $1
               AND ulp.status = 'in_progress'
             ORDER BY ulp.updated_at DESC
             LIMIT 6`,
            [userId]
        );

        const recentActivityRes = await pool.query<{ title: string; happened_at: string; points: number; kind: string }>(
            `SELECT * FROM (
                SELECT i.name AS title, ui.acquired_at AS happened_at,
                       COALESCE((i.metadata->>'xpReward')::int, CASE WHEN i.category='lesson' THEN 50 ELSE 100 END) AS points,
                       i.category AS kind
                FROM user_items ui
                JOIN items i ON i.id = ui.item_id
                WHERE ui.user_id = $1
                ORDER BY ui.acquired_at DESC
                LIMIT 10
            ) t
            ORDER BY happened_at DESC
            LIMIT 5`,
            [userId]
        );

        const totals = totalsRes.rows[0] || { total_lessons: '0', completed_lessons: '0', active_lessons: '0' };
        const periods = periodsRes.rows[0] || { week_count: '0', month_count: '0', half_year_count: '0', year_count: '0' };

        const toProgress = (value: number, target: number) => Math.max(0, Math.min(100, Math.round((value / target) * 100)));

        const weekCount = Number(periods.week_count || 0);
        const monthCount = Number(periods.month_count || 0);
        const halfYearCount = Number(periods.half_year_count || 0);
        const yearCount = Number(periods.year_count || 0);

        return {
            totals: {
                totalLessons: Number(totals.total_lessons || 0),
                completedLessons: Number(totals.completed_lessons || 0),
                activeLessons: Number(totals.active_lessons || 0),
            },
            ranges: {
                week: { completed: weekCount, progressPercent: toProgress(weekCount, 5) },
                month: { completed: monthCount, progressPercent: toProgress(monthCount, 20) },
                halfYear: { completed: halfYearCount, progressPercent: toProgress(halfYearCount, 80) },
                year: { completed: yearCount, progressPercent: toProgress(yearCount, 160) },
            },
            activeLessonItems: activeLessonsRes.rows.map((row) => ({
                lessonId: row.lesson_id,
                title: row.name,
                progressPercent: Number(row.progress_percent || 0),
                duration: row.duration ? Number(row.duration) : null,
                updatedAt: row.updated_at,
            })),
            recentActivities: recentActivityRes.rows.map((row) => ({
                title: row.title,
                happenedAt: row.happened_at,
                xp: Number(row.points || 0),
                kind: row.kind,
            })),
        };
    },

    getUserActiveLessons: async (userId: string) => {
        const res = await pool.query<{ lesson_id: string; title: string; progress_percent: number; status: string; last_activity_at: string; duration: string | null }>(
            `SELECT ulp.lesson_id,
                    i.name AS title,
                    ulp.progress_percent,
                    ulp.status,
                    ulp.last_activity_at,
                    i.metadata->>'duration' AS duration
             FROM user_lesson_progress ulp
             JOIN items i ON i.id = ulp.lesson_id
             WHERE ulp.user_id = $1
               AND ulp.status = 'in_progress'
             ORDER BY ulp.last_activity_at DESC`,
            [userId]
        );
        return res.rows;
    },

    getUserRecentActivity: async (userId: string, limit = 20) => {
        const safeLimit = Math.max(1, Math.min(limit, 100));
        const res = await pool.query<{ id: string; event_type: string; lesson_id: string | null; xp_delta: number | null; created_at: string; metadata: Record<string, unknown> }>(
            `SELECT id::text, event_type, lesson_id::text, xp_delta, created_at, metadata
             FROM user_activity_events
             WHERE user_id = $1
             ORDER BY created_at DESC
             LIMIT $2`,
            [userId, safeLimit]
        );
        return res.rows;
    },

    getUserRangeStats: async (userId: string, range: 'week' | 'month' | 'halfYear' | 'year') => {
        const intervals: Record<typeof range, string> = {
            week: '7 days',
            month: '30 days',
            halfYear: '183 days',
            year: '365 days',
        };
        const res = await pool.query<{ completed: string }>(
            `SELECT COUNT(*) AS completed
             FROM user_lesson_progress
             WHERE user_id = $1
               AND status = 'completed'
               AND completed_at >= NOW() - ($2::interval)`,
            [userId, intervals[range]]
        );
        return Number(res.rows[0]?.completed || 0);
    },

    updateLessonProgressPercent: async (userId: string, lessonId: string, nextPercent: number) => {
        const percent = Math.max(0, Math.min(100, Math.trunc(nextPercent)));
        const res = await pool.query<{ progress_percent: number; status: string }>(
            `INSERT INTO user_lesson_progress (
                user_id, lesson_id, status, progress_percent, started_at, last_activity_at, updated_at
             )
             VALUES ($1, $2, CASE WHEN $3 >= 100 THEN 'completed' ELSE 'in_progress' END, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
             ON CONFLICT (user_id, lesson_id) DO UPDATE
               SET progress_percent = GREATEST(user_lesson_progress.progress_percent, EXCLUDED.progress_percent),
                   status = CASE
                       WHEN GREATEST(user_lesson_progress.progress_percent, EXCLUDED.progress_percent) >= 100 THEN 'completed'
                       WHEN user_lesson_progress.status = 'completed' THEN 'completed'
                       ELSE 'in_progress'
                   END,
                   completed_at = CASE
                       WHEN GREATEST(user_lesson_progress.progress_percent, EXCLUDED.progress_percent) >= 100
                            AND user_lesson_progress.completed_at IS NULL THEN CURRENT_TIMESTAMP
                       ELSE user_lesson_progress.completed_at
                   END,
                   last_activity_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
             RETURNING progress_percent, status`,
            [userId, lessonId, percent]
        );

        return res.rows[0] || { progress_percent: percent, status: percent >= 100 ? 'completed' : 'in_progress' };
    },

    completeLessonWorkflow: async (userId: string, lessonId: string, xpToAdd: number) => {
        const client = await pool.connect();
        try {
            await client.query('BEGIN');

            await client.query(
                `INSERT INTO user_lesson_progress (
                    user_id, lesson_id, status, progress_percent, started_at, completed_at, last_activity_at, updated_at
                 )
                 VALUES ($1, $2, 'completed', 100, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                 ON CONFLICT (user_id, lesson_id) DO UPDATE
                   SET status = 'completed',
                       progress_percent = 100,
                       completed_at = COALESCE(user_lesson_progress.completed_at, CURRENT_TIMESTAMP),
                       last_activity_at = CURRENT_TIMESTAMP,
                       updated_at = CURRENT_TIMESTAMP`,
                [userId, lessonId]
            );

            await client.query(
                `INSERT INTO user_items (user_id, item_id, acquired_at)
                 VALUES ($1, $2, CURRENT_TIMESTAMP)
                 ON CONFLICT (user_id, item_id) DO NOTHING`,
                [userId, lessonId]
            );

            await client.query(
                `INSERT INTO user_activity_events (user_id, event_type, lesson_id, metadata)
                 VALUES ($1, 'lesson_completed', $2, '{}'::jsonb)`,
                [userId, lessonId]
            );

            const xpInsert = await client.query<{ amount: number }>(
                `INSERT INTO user_xp_transactions (user_id, lesson_id, amount, reason, created_at)
                 VALUES ($1, $2, $3, 'lesson_completed', CURRENT_TIMESTAMP)
                 ON CONFLICT (user_id, lesson_id, reason) DO NOTHING
                 RETURNING amount`,
                [userId, lessonId, xpToAdd]
            );

            let xpEarned = 0;
            if ((xpInsert.rowCount ?? 0) > 0) {
                xpEarned = Number(xpInsert.rows[0]?.amount || xpToAdd);
                await client.query(
                    `UPDATE users
                     SET xp_total = xp_total + $1,
                         level = floor((xp_total + $1) / 100) + 1,
                         updated_at = CURRENT_TIMESTAMP
                     WHERE id = $2`,
                    [xpEarned, userId]
                );

                await client.query(
                    `INSERT INTO user_activity_events (user_id, event_type, lesson_id, xp_delta, metadata)
                     VALUES ($1, 'xp_added', $2, $3, jsonb_build_object('reason', 'lesson_completed'))`,
                    [userId, lessonId, xpEarned]
                );
            }

            await client.query('COMMIT');
            await invalidateUserCaches({ id: userId });

            const userRes = await pool.query<{ xp_total: number; level: number }>('SELECT xp_total, level FROM users WHERE id = $1', [userId]);
            const user = userRes.rows[0] || { xp_total: 0, level: 1 };

            return {
                xpEarned,
                xp_total: user.xp_total,
                level: user.level,
            };
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    },

    startLessonProgress: async (userId: string, lessonId: string) => {
        await pool.query(
            `INSERT INTO user_lesson_progress (user_id, lesson_id, status, progress_percent, started_at, last_activity_at, updated_at)
             VALUES ($1, $2, 'in_progress', 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
             ON CONFLICT (user_id, lesson_id) DO UPDATE
               SET status = CASE WHEN user_lesson_progress.status = 'completed' THEN 'completed' ELSE 'in_progress' END,
                   started_at = COALESCE(user_lesson_progress.started_at, CURRENT_TIMESTAMP),
                   last_activity_at = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP`,
            [userId, lessonId]
        );

        await pool.query(
            `INSERT INTO user_activity_events (user_id, event_type, lesson_id, metadata)
             VALUES ($1, 'lesson_started', $2, '{}'::jsonb)`,
            [userId, lessonId]
        );
    },

    getAdminProgressOverview: async () => {
        const res = await pool.query<{ users_total: string; lessons_completed_total: string; quizzes_completed_total: string; active_lessons_total: string }>(
            `SELECT
                (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) AS users_total,
                (SELECT COUNT(*) FROM user_lesson_progress WHERE status='completed') AS lessons_completed_total,
                (SELECT COUNT(*) FROM user_items ui JOIN items i ON i.id = ui.item_id WHERE i.category='quiz') AS quizzes_completed_total,
                (SELECT COUNT(*) FROM user_lesson_progress WHERE status='in_progress') AS active_lessons_total`
        );
        return res.rows[0];
    },

    getAdminProgressUsers: async (limit = 50) => {
        const safeLimit = Math.max(1, Math.min(limit, 500));
        const res = await pool.query(
            `SELECT u.id, u.email, u.username, u.xp_total, u.level,
                    COUNT(*) FILTER (WHERE ulp.status = 'completed') AS completed_lessons,
                    COUNT(*) FILTER (WHERE ulp.status = 'in_progress') AS active_lessons,
                    MAX(ulp.last_activity_at) AS last_activity_at
             FROM users u
             LEFT JOIN user_lesson_progress ulp ON ulp.user_id = u.id
             WHERE u.deleted_at IS NULL
             GROUP BY u.id
             ORDER BY COALESCE(MAX(ulp.last_activity_at), u.updated_at) DESC
             LIMIT $1`,
            [safeLimit]
        );
        return res.rows;
    },

    getAdminProgressUserDetail: async (userId: string) => {
        const [progressRows, eventsRows, xpRows] = await Promise.all([
            pool.query(
                `SELECT lesson_id::text AS lesson_id, status, progress_percent, started_at, completed_at, last_activity_at
                 FROM user_lesson_progress
                 WHERE user_id = $1
                 ORDER BY last_activity_at DESC`,
                [userId]
            ),
            pool.query(
                `SELECT id::text, event_type, lesson_id::text AS lesson_id, xp_delta, created_at, metadata
                 FROM user_activity_events
                 WHERE user_id = $1
                 ORDER BY created_at DESC
                 LIMIT 200`,
                [userId]
            ),
            pool.query(
                `SELECT id::text, lesson_id::text AS lesson_id, amount, reason, created_at
                 FROM user_xp_transactions
                 WHERE user_id = $1
                 ORDER BY created_at DESC
                 LIMIT 200`,
                [userId]
            ),
        ]);

        return {
            lessonProgress: progressRows.rows,
            events: eventsRows.rows,
            xpTransactions: xpRows.rows,
        };
    },

    getAdminLessonProgressAnalytics: async (lessonId: string) => {
        const res = await pool.query<{ started_count: string; completed_count: string; avg_progress_percent: string }>(
            `SELECT
                COUNT(*) AS started_count,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
                COALESCE(AVG(progress_percent), 0)::text AS avg_progress_percent
             FROM user_lesson_progress
             WHERE lesson_id = $1`,
            [lessonId]
        );

        const row = res.rows[0] || { started_count: '0', completed_count: '0', avg_progress_percent: '0' };
        const started = Number(row.started_count || 0);
        const completed = Number(row.completed_count || 0);

        return {
            started,
            completed,
            completionRate: started > 0 ? Math.round((completed / started) * 100) : 0,
            averageProgressPercent: Number(row.avg_progress_percent || 0),
        };
    },

    getAllUsers: async () => {
        const res = await pool.query('SELECT id, username, email, first_name, last_name, xp_total, level FROM users WHERE deleted_at IS NULL');
        return res.rows;
    },
};
