import pkg from 'pg';
const { Pool } = pkg;
import { config } from 'dotenv';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

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

// Connection Pool Configuration
// Uses Master for Writes and potentially Replica for Reads
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

export const db = {
    // Basic query wrapper for protection against SQL injection
    query: (text: string, params?: any[]) => pool.query(text, params),

    // --- USER METHODS ---
    
    createUser: async (email: string, passwordHash: string, firstName: string, lastName: string) => {
        const query = `
            INSERT INTO users (email, password_hash, first_name, last_name)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, first_name, last_name, role;
        `;
        const res = await pool.query(query, [email, passwordHash, firstName, lastName]);
        return res.rows[0];
    },

    getUserByEmail: async (email: string) => {
        const query = 'SELECT * FROM users WHERE email = $1';
        const res = await pool.query(query, [email]);
        return res.rows[0];
    },

    getUserById: async (id: string) => {
        const query = 'SELECT id, email, first_name, last_name, role, xp_total, level FROM users WHERE id = $1';
        const res = await pool.query(query, [id]);
        return res.rows[0];
    },

    // --- ITEM METHODS (Optimized) ---

    createItem: async (name: string, description: string, category: string, price: number) => {
        const query = `
            INSERT INTO items (name, description, category, price)
            VALUES ($1, $2, $3, $4)
            RETURNING *;
        `;
        const res = await pool.query(query, [name, description, category, price]);
        return res.rows[0];
    },

    // Blazing fast search using GIN index and tsvector
    searchItems: async (searchTerm: string) => {
        const query = `
            SELECT id, name, description, category, price, 
                   ts_rank(search_vector, to_tsquery('english', $1)) as rank
            FROM items
            WHERE search_vector @@ to_tsquery('english', $1)
            ORDER BY rank DESC
            LIMIT 50;
        `;
        // Prepare search term for tsquery (replace spaces with & for AND search)
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
        return res.rows[0];
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
            lessonsCompleted: acquisitions, // Simplified for now
            quizzesCompleted: [],
            lastActiveDate: new Date().toISOString()
        };
    },

    getAllUsers: async () => {
        const res = await pool.query('SELECT id, email, first_name, last_name, xp_total, level FROM users');
        return res.rows;
    }
};
