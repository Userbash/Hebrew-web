import { promises as fs } from 'fs';
import { join } from 'path';
import { db } from './db.js';

const MIGRATIONS_DIR = join(process.cwd(), 'database', 'migrations');
const DB_RETRY_ATTEMPTS = Math.max(1, Number(process.env.DB_CONNECT_RETRY_ATTEMPTS || '30'));
const DB_RETRY_DELAY_MS = Math.max(200, Number(process.env.DB_CONNECT_RETRY_DELAY_MS || '2000'));

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const waitForDatabase = async () => {
    let lastError: unknown = null;

    for (let attempt = 1; attempt <= DB_RETRY_ATTEMPTS; attempt += 1) {
        try {
            await db.query('SELECT 1');
            return;
        } catch (error) {
            lastError = error;
            console.warn(`[MIGRATIONS] Database is not ready (attempt ${attempt}/${DB_RETRY_ATTEMPTS})`);
            if (attempt < DB_RETRY_ATTEMPTS) {
                await sleep(DB_RETRY_DELAY_MS);
            }
        }
    }

    throw lastError;
};

const ensureSchemaMigrationsTable = async () => {
    await db.query(`
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    `);
};

const getMigrationFiles = async () => {
    const entries = await fs.readdir(MIGRATIONS_DIR, { withFileTypes: true });

    return entries
        .filter((entry) => entry.isFile() && entry.name.endsWith('.sql'))
        .map((entry) => entry.name)
        .sort();
};

const isMigrationApplied = async (filename: string) => {
    const res = await db.query('SELECT 1 FROM schema_migrations WHERE filename = $1 LIMIT 1', [filename]);
    return (res.rowCount ?? 0) > 0;
};

const markMigrationApplied = async (filename: string) => {
    await db.query(
        'INSERT INTO schema_migrations (filename, applied_at) VALUES ($1, CURRENT_TIMESTAMP) ON CONFLICT (filename) DO NOTHING',
        [filename]
    );
};

export const runMigrations = async () => {
    await waitForDatabase();
    await ensureSchemaMigrationsTable();

    const migrationFiles = await getMigrationFiles();

    for (const filename of migrationFiles) {
        const alreadyApplied = await isMigrationApplied(filename);
        if (alreadyApplied) {
            continue;
        }

        const absolutePath = join(MIGRATIONS_DIR, filename);
        const sql = await fs.readFile(absolutePath, 'utf-8');

        await db.query(sql);
        await markMigrationApplied(filename);

        console.log(`[MIGRATIONS] Applied: ${filename}`);
    }

    console.log('[MIGRATIONS] Database schema is up to date');
};
