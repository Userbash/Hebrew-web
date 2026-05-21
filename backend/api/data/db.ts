import pkg from 'pg';
const { Pool } = pkg;
import { config } from 'dotenv';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

config({ path: join(__dirname, '../../..', '.env') });

// Connection Pool Configuration
// Uses Master for Writes and potentially Replica for Reads
const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    user: process.env.DB_USER || 'admin',
    password: process.env.DB_PASSWORD || 'master_pass_2025',
    database: process.env.DB_NAME || 'hebrew_db',
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
    }
};
