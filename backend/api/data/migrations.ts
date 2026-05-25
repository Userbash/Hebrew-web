import { promises as fs } from 'fs';
import { join } from 'path';
import pkg from 'pg';
import bcrypt from 'bcrypt';
import type { PoolClient, QueryResult } from 'pg';
import { db } from './db.js';

const { Client } = pkg;

const MIGRATIONS_DIR = join(process.cwd(), 'database', 'migrations');
const MIGRATION_LOCK_ID = 88422131;

const degradedModeRequested =
    process.env.BACKEND_ALLOW_DEGRADED_START === '1'
    || process.env.BACKEND_ALLOW_DEGRADED_START === 'true'
    || process.env.BACKEND_ALLOW_DEGRADED_START === 'yes'
    || process.env.CI === 'true';

const defaultAttempts = (process.env.NODE_ENV === 'production' && !degradedModeRequested) ? 30 : 5;
const defaultDelayMs = (process.env.NODE_ENV === 'production' && !degradedModeRequested) ? 2000 : 500;

const DB_RETRY_ATTEMPTS = Math.max(1, Number(process.env.DB_CONNECT_RETRY_ATTEMPTS || String(defaultAttempts)));
const DB_RETRY_DELAY_MS = Math.max(200, Number(process.env.DB_CONNECT_RETRY_DELAY_MS || String(defaultDelayMs)));
const MIGRATION_LOCK_RETRY_ATTEMPTS = Math.max(1, Number(process.env.DB_MIGRATION_LOCK_RETRY_ATTEMPTS || '60'));
const MIGRATION_LOCK_RETRY_DELAY_MS = Math.max(250, Number(process.env.DB_MIGRATION_LOCK_RETRY_DELAY_MS || '1000'));

const DEFAULT_USER_EMAIL = (process.env.DB_DEFAULT_USER_EMAIL || 'user@local.test').trim().toLowerCase();
const DEFAULT_USER_USERNAME = (process.env.DB_DEFAULT_USER_USERNAME || 'standard_user').trim().toLowerCase();
const DEFAULT_USER_PASSWORD = process.env.DB_DEFAULT_USER_PASSWORD || 'ChangeMe123!';
const DEFAULT_USER_FIRST_NAME = (process.env.DB_DEFAULT_USER_FIRST_NAME || 'Standard').trim();
const DEFAULT_USER_LAST_NAME = (process.env.DB_DEFAULT_USER_LAST_NAME || 'User').trim();
const DEFAULT_USER_ROLE = (process.env.DB_DEFAULT_USER_ROLE || 'platform_admin').trim().toLowerCase();
const DEFAULT_USER_BLOCKED = (process.env.DB_DEFAULT_USER_BLOCKED || 'false').trim().toLowerCase() === 'true';

const toLegacyUserRole = (rbacRoleKey: string): 'user' | 'admin' | 'moderator' => {
    if (rbacRoleKey === 'platform_admin' || rbacRoleKey === 'root' || rbacRoleKey === 'security_admin' || rbacRoleKey === 'content_admin') {
        return 'admin';
    }
    if (rbacRoleKey === 'moderator') {
        return 'moderator';
    }
    return 'user';
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const isSafeDbName = (name: string) => /^[A-Za-z0-9_]+$/.test(name);

type Queryable = {
    query: (text: string, params?: unknown[]) => Promise<QueryResult>;
};

const ensureDatabaseExists = async () => {
    if (process.env.DB_AUTO_CREATE !== '1' && process.env.DB_AUTO_CREATE !== 'true') {
        return;
    }

    let dbName = process.env.DB_NAME || 'hebrew_ai_db';
    let host = process.env.DB_HOST || '127.0.0.1';
    let port = parseInt(process.env.DB_PORT || '5432', 10);
    let user = process.env.DB_USER || 'postgres';
    let dbPassword = process.env.DB_PASSWORD || process.env.POSTGRES_PASSWORD || 'postgres';

    if (process.env.DATABASE_URL) {
        try {
            const url = new URL(process.env.DATABASE_URL);
            dbName = url.pathname.replace(/^\//, '') || dbName;
            host = url.hostname || host;
            port = Number(url.port || port);
            user = decodeURIComponent(url.username || user);
            dbPassword = decodeURIComponent(url.password || dbPassword);
        } catch {
            // fallback to DB_* vars
        }
    }

    if (!isSafeDbName(dbName)) {
        console.warn(`[MIGRATIONS] Skip auto-create DB: unsafe DB_NAME '${dbName}'`);
        return;
    }

    const adminClient = new Client({
        host,
        port,
        user,
        ['password']: dbPassword,
        database: 'postgres',
        connectionTimeoutMillis: 2000,
    });

    try {
        await adminClient.connect();
        const existsRes = await adminClient.query('SELECT 1 FROM pg_database WHERE datname = $1 LIMIT 1', [dbName]);
        if ((existsRes.rowCount ?? 0) > 0) {
            return;
        }

        await adminClient.query(`CREATE DATABASE ${dbName}`);
        console.log(`[MIGRATIONS] Created database: ${dbName}`);
    } finally {
        await adminClient.end().catch(() => undefined);
    }
};

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

const ensureSchemaMigrationsTable = async (q: Queryable) => {
    await q.query(`
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

const isMigrationApplied = async (q: Queryable, filename: string) => {
    const res = await q.query('SELECT 1 FROM schema_migrations WHERE filename = $1 LIMIT 1', [filename]);
    return (res.rowCount ?? 0) > 0;
};

const markMigrationApplied = async (q: Queryable, filename: string) => {
    await q.query(
        'INSERT INTO schema_migrations (filename, applied_at) VALUES ($1, CURRENT_TIMESTAMP) ON CONFLICT (filename) DO NOTHING',
        [filename]
    );
};

const ensureDefaultUserSeed = async (q: Queryable) => {
    const enabled = process.env.DB_DEFAULT_USER_ENABLED ?? 'true';
    if (!['1', 'true', 'yes', 'on'].includes(enabled.toLowerCase())) {
        return;
    }

    const passwordHash = await bcrypt.hash(DEFAULT_USER_PASSWORD, 12);

    await q.query('BEGIN');
    try {
      const upserted = await q.query(
          `INSERT INTO users (
              email,
              password_hash,
              username,
              first_name,
              last_name,
              role,
              xp_total,
              level,
              streak,
              failed_login_attempts,
              is_system_blocked,
              access_labels,
              registered_at,
              password_changed_at,
              locked_until,
              deleted_at,
              ui_preferences,
              created_at,
              updated_at
          ) VALUES (
              $1, $2, $3, $4, $5, $6,
              0, 1, 0, 0, $7, '{}'::jsonb,
              CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
              NULL, NULL, '{}'::jsonb,
              CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
          )
          ON CONFLICT (email)
          DO UPDATE SET
              username = EXCLUDED.username,
              first_name = EXCLUDED.first_name,
              last_name = EXCLUDED.last_name,
              role = EXCLUDED.role,
              is_system_blocked = EXCLUDED.is_system_blocked,
              deleted_at = NULL,
              updated_at = CURRENT_TIMESTAMP
          RETURNING id`,
          [
              DEFAULT_USER_EMAIL,
              passwordHash,
              DEFAULT_USER_USERNAME,
              DEFAULT_USER_FIRST_NAME,
              DEFAULT_USER_LAST_NAME,
              toLegacyUserRole(DEFAULT_USER_ROLE),
              DEFAULT_USER_BLOCKED,
          ]
      );

      const userId = upserted.rows[0]?.id;
      if (!userId) {
          await q.query('ROLLBACK');
          return;
      }

      await q.query(
          `INSERT INTO user_roles (user_id, role_id, note, is_active)
           SELECT $1, r.id, 'Seeded default user role assignment', TRUE
           FROM roles r
           WHERE r.role_key = $2
           ON CONFLICT DO NOTHING`,
          [userId, DEFAULT_USER_ROLE]
      );

      await q.query(
          `UPDATE user_roles ur
           SET is_active = TRUE,
               revoked_at = NULL,
               expires_at = NULL,
               note = 'Seeded default user role assignment (reconciled)'
           FROM roles r
           WHERE ur.user_id = $1
             AND ur.role_id = r.id
             AND r.role_key = $2`,
          [userId, DEFAULT_USER_ROLE]
      );

      await q.query('COMMIT');
      console.log(`[MIGRATIONS] Seeded default user '${DEFAULT_USER_EMAIL}' with role '${DEFAULT_USER_ROLE}'`);
    } catch (error) {
      await q.query('ROLLBACK');
      throw error;
    }
};

const acquireMigrationLock = async (client: PoolClient) => {
    for (let attempt = 1; attempt <= MIGRATION_LOCK_RETRY_ATTEMPTS; attempt += 1) {
        const res = await client.query<{ locked: boolean }>('SELECT pg_try_advisory_lock($1) AS locked', [MIGRATION_LOCK_ID]);
        if (res.rows[0]?.locked) {
            return;
        }

        if (attempt < MIGRATION_LOCK_RETRY_ATTEMPTS) {
            console.warn(`[MIGRATIONS] Waiting migration lock (attempt ${attempt}/${MIGRATION_LOCK_RETRY_ATTEMPTS})`);
            await sleep(MIGRATION_LOCK_RETRY_DELAY_MS);
            continue;
        }

        throw new Error('Could not acquire migration lock');
    }
};

const releaseMigrationLock = async (client: PoolClient) => {
    await client.query('SELECT pg_advisory_unlock($1)', [MIGRATION_LOCK_ID]);
};

export const runMigrations = async () => {
    try {
        await ensureDatabaseExists();
    } catch (error) {
        console.warn('[MIGRATIONS] Auto-create database skipped or failed:', error);
    }

    await waitForDatabase();

    const client = await db.connect();
    try {
        await acquireMigrationLock(client);
        await ensureSchemaMigrationsTable(client);

        const migrationFiles = await getMigrationFiles();

        for (const filename of migrationFiles) {
            const alreadyApplied = await isMigrationApplied(client, filename);
            if (alreadyApplied) {
                continue;
            }

            const absolutePath = join(MIGRATIONS_DIR, filename);
            const sql = await fs.readFile(absolutePath, 'utf-8');

            await client.query(sql);
            await markMigrationApplied(client, filename);

            console.log(`[MIGRATIONS] Applied: ${filename}`);
        }

        await ensureDefaultUserSeed(client);

        console.log('[MIGRATIONS] Database schema is up to date');
    } finally {
        try {
            await releaseMigrationLock(client);
        } catch {
            // no-op: unlock can fail if lock was not acquired
        }
        client.release();
    }
};
