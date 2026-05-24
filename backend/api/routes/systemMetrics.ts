import express, { Request, Response } from 'express';
import os from 'os';
import { statfs } from 'node:fs/promises';
import { db } from '../data/db.js';
import { verifyToken } from '../middleware/auth.js';
import { requirePermission } from '../middleware/authorization.js';
import { asyncHandler } from '../middleware/errorHandler.js';

const router = express.Router();

const round = (value: number, digits = 2) => {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
};

const safePercent = (part: number, total: number) => {
  if (!Number.isFinite(part) || !Number.isFinite(total) || total <= 0) {
    return 0;
  }
  return round((part / total) * 100, 2);
};

const toNumber = (value: unknown) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const formatSeconds = (seconds: number) => {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const days = Math.floor(safeSeconds / 86400);
  const hours = Math.floor((safeSeconds % 86400) / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const secs = safeSeconds % 60;
  return `${days}d ${hours}h ${minutes}m ${secs}s`;
};

const readDisk = async () => {
  try {
    const fsStats = await statfs('/');
    const totalBytes = fsStats.blocks * fsStats.bsize;
    const freeBytes = fsStats.bfree * fsStats.bsize;
    const availableBytes = fsStats.bavail * fsStats.bsize;
    const usedBytes = Math.max(totalBytes - freeBytes, 0);

    const totalInodes = fsStats.files;
    const freeInodes = fsStats.ffree;
    const usedInodes = Math.max(totalInodes - freeInodes, 0);

    return {
      path: '/',
      total_bytes: totalBytes,
      free_bytes: freeBytes,
      available_bytes: availableBytes,
      used_bytes: usedBytes,
      used_percent: safePercent(usedBytes, totalBytes),
      total_inodes: totalInodes,
      free_inodes: freeInodes,
      used_inodes: usedInodes,
      inode_used_percent: safePercent(usedInodes, totalInodes),
    };
  } catch {
    return {
      path: '/',
      total_bytes: 0,
      free_bytes: 0,
      available_bytes: 0,
      used_bytes: 0,
      used_percent: 0,
      total_inodes: 0,
      free_inodes: 0,
      used_inodes: 0,
      inode_used_percent: 0,
    };
  }
};

router.get(
  '/metrics',
  verifyToken,
  requirePermission('system', 'read', 'any'),
  asyncHandler(async (_req: Request, res: Response) => {
    const cpuCount = os.cpus().length || 1;
    const load = os.loadavg();

    const memoryTotal = os.totalmem();
    const memoryFree = os.freemem();
    const memoryUsed = Math.max(memoryTotal - memoryFree, 0);

    const processCpuUsage = process.cpuUsage();
    const processUptimeSeconds = process.uptime();
    const processUptimeMicros = processUptimeSeconds * 1_000_000;
    const processCpuTotalMicros = processCpuUsage.user + processCpuUsage.system;

    const disk = await readDisk();

    const dbProbeStarted = performance.now();
    await db.query('SELECT 1');
    const dbProbeLatencyMs = round(performance.now() - dbProbeStarted, 2);

    const dbStatsRes = await db.query(
      `SELECT
          numbackends,
          xact_commit,
          xact_rollback,
          blks_read,
          blks_hit,
          tup_returned,
          tup_fetched,
          tup_inserted,
          tup_updated,
          tup_deleted,
          deadlocks,
          temp_files,
          temp_bytes,
          blk_read_time,
          blk_write_time,
          stats_reset
       FROM pg_stat_database
       WHERE datname = current_database()`
    );

    const dbStatesRes = await db.query(
      `SELECT COALESCE(state, 'unknown') AS state, COUNT(*)::int AS count
       FROM pg_stat_activity
       WHERE datname = current_database()
       GROUP BY COALESCE(state, 'unknown')`
    );

    const waitingLocksRes = await db.query(
      `SELECT COUNT(*)::int AS waiting_locks
       FROM pg_locks
       WHERE NOT granted`
    );

    const lockWaitingQueriesRes = await db.query(
      `SELECT COUNT(*)::int AS lock_waiting_queries
       FROM pg_stat_activity
       WHERE datname = current_database()
         AND wait_event_type = 'Lock'`
    );

    const longQueriesRes = await db.query(
      `SELECT COUNT(*)::int AS long_queries
       FROM pg_stat_activity
       WHERE datname = current_database()
         AND state = 'active'
         AND now() - query_start > interval '3 seconds'`
    );

    const maxActiveQueryAgeRes = await db.query(
      `SELECT COALESCE(MAX(EXTRACT(EPOCH FROM (NOW() - query_start))), 0) AS max_age_seconds
       FROM pg_stat_activity
       WHERE datname = current_database()
         AND state = 'active'
         AND query_start IS NOT NULL`
    );

    const dbSizeRes = await db.query(
      `SELECT pg_database_size(current_database())::bigint AS database_size_bytes`
    );

    const relationsRes = await db.query(
      `SELECT
          COUNT(*) FILTER (WHERE c.relkind = 'r')::int AS table_count,
          COUNT(*) FILTER (WHERE c.relkind = 'i')::int AS index_count
       FROM pg_class c
       JOIN pg_namespace n ON n.oid = c.relnamespace
       WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
         AND n.nspname !~ '^pg_toast'`
    );

    const dbStats = (dbStatsRes.rows[0] as Record<string, unknown> | undefined) || {};
    const waitingLocks = toNumber((waitingLocksRes.rows[0] as { waiting_locks?: number } | undefined)?.waiting_locks);
    const lockWaitingQueries = toNumber((lockWaitingQueriesRes.rows[0] as { lock_waiting_queries?: number } | undefined)?.lock_waiting_queries);
    const longQueries = toNumber((longQueriesRes.rows[0] as { long_queries?: number } | undefined)?.long_queries);
    const maxActiveQueryAgeSeconds = round(toNumber((maxActiveQueryAgeRes.rows[0] as { max_age_seconds?: number } | undefined)?.max_age_seconds), 3);
    const databaseSizeBytes = toNumber((dbSizeRes.rows[0] as { database_size_bytes?: number } | undefined)?.database_size_bytes);
    const relationStats = (relationsRes.rows[0] as { table_count?: number; index_count?: number } | undefined) || {};
    const tableCount = toNumber(relationStats.table_count);
    const indexCount = toNumber(relationStats.index_count);

    const totalBlocks = toNumber(dbStats.blks_read) + toNumber(dbStats.blks_hit);
    const cacheHitPercent = totalBlocks > 0
      ? safePercent(toNumber(dbStats.blks_hit), totalBlocks)
      : 100;

    const states = dbStatesRes.rows.reduce<Record<string, number>>((acc, row) => {
      const state = String((row as { state?: string }).state || 'unknown');
      const count = toNumber((row as { count?: number }).count);
      acc[state] = count;
      return acc;
    }, {});

    const osUptimeSeconds = os.uptime();
    const siteUptimeSeconds = processUptimeSeconds;
    const cpuLoadPercent1m = safePercent(load[0], cpuCount);

    const processCpuPercent = processUptimeMicros > 0
      ? round((processCpuTotalMicros / processUptimeMicros) * 100, 2)
      : 0;

    const alerts: Array<{ level: 'ok' | 'warn' | 'critical'; code: string; message: string }> = [];

    if (dbProbeLatencyMs > 250 || longQueries > 0) {
      alerts.push({
        level: dbProbeLatencyMs > 500 ? 'critical' : 'warn',
        code: 'db_latency',
        message: `Database response is slower than normal (${dbProbeLatencyMs} ms probe, ${longQueries} long queries).`,
      });
    }

    if (maxActiveQueryAgeSeconds > 8) {
      alerts.push({
        level: maxActiveQueryAgeSeconds > 20 ? 'critical' : 'warn',
        code: 'db_long_query_age',
        message: `Longest active query age is high (${maxActiveQueryAgeSeconds}s).`,
      });
    }

    if (waitingLocks > 0) {
      alerts.push({
        level: waitingLocks > 5 ? 'critical' : 'warn',
        code: 'db_lock_contention',
        message: `Lock contention detected: ${waitingLocks} waiting locks.`,
      });
    }

    if (disk.used_percent >= 90 || disk.inode_used_percent >= 90) {
      alerts.push({
        level: disk.used_percent >= 95 || disk.inode_used_percent >= 95 ? 'critical' : 'warn',
        code: 'disk_pressure',
        message: `Disk pressure is high (space ${disk.used_percent}%, inodes ${disk.inode_used_percent}%).`,
      });
    }

    const memoryUsedPercent = safePercent(memoryUsed, memoryTotal);
    if (memoryUsedPercent >= 90) {
      alerts.push({
        level: memoryUsedPercent >= 95 ? 'critical' : 'warn',
        code: 'memory_pressure',
        message: `Memory pressure is high (${memoryUsedPercent}% used).`,
      });
    }

    if (cpuLoadPercent1m >= 90) {
      alerts.push({
        level: cpuLoadPercent1m >= 100 ? 'critical' : 'warn',
        code: 'cpu_pressure',
        message: `CPU load is elevated (${cpuLoadPercent1m}% of available cores, 1m average).`,
      });
    }

    if (alerts.length === 0) {
      alerts.push({
        level: 'ok',
        code: 'system_ok',
        message: 'No major bottlenecks detected in CPU, memory, disk, or database metrics.',
      });
    }

    res.status(200).json({
      success: true,
      metrics: {
        collected_at: new Date().toISOString(),
        site: {
          uptime_seconds: round(siteUptimeSeconds, 2),
          uptime_human: formatSeconds(siteUptimeSeconds),
          environment: process.env.NODE_ENV || 'development',
          pid: process.pid,
          node_version: process.version,
        },
        system: {
          hostname: os.hostname(),
          platform: os.platform(),
          arch: os.arch(),
          release: os.release(),
          uptime_seconds: osUptimeSeconds,
          uptime_human: formatSeconds(osUptimeSeconds),
          cpu: {
            cores: cpuCount,
            load_1m: round(load[0], 3),
            load_5m: round(load[1], 3),
            load_15m: round(load[2], 3),
            load_percent_1m: cpuLoadPercent1m,
            process_cpu_percent: processCpuPercent,
          },
          memory: {
            total_bytes: memoryTotal,
            used_bytes: memoryUsed,
            free_bytes: memoryFree,
            used_percent: memoryUsedPercent,
            rss_bytes: process.memoryUsage().rss,
            heap_used_bytes: process.memoryUsage().heapUsed,
            heap_total_bytes: process.memoryUsage().heapTotal,
            external_bytes: process.memoryUsage().external,
          },
          disk,
        },
        database: {
          status: dbProbeLatencyMs <= 1000 ? 'up' : 'degraded',
          probe_latency_ms: dbProbeLatencyMs,
          waiting_locks: waitingLocks,
          lock_waiting_queries: lockWaitingQueries,
          long_running_queries: longQueries,
          max_active_query_age_seconds: maxActiveQueryAgeSeconds,
          active_connections: toNumber(dbStats.numbackends),
          cache_hit_percent: cacheHitPercent,
          transaction: {
            commits: toNumber(dbStats.xact_commit),
            rollbacks: toNumber(dbStats.xact_rollback),
          },
          rows: {
            returned: toNumber(dbStats.tup_returned),
            fetched: toNumber(dbStats.tup_fetched),
            inserted: toNumber(dbStats.tup_inserted),
            updated: toNumber(dbStats.tup_updated),
            deleted: toNumber(dbStats.tup_deleted),
          },
          io: {
            blocks_read: toNumber(dbStats.blks_read),
            blocks_hit: toNumber(dbStats.blks_hit),
            temp_files: toNumber(dbStats.temp_files),
            temp_bytes: toNumber(dbStats.temp_bytes),
            read_time_ms: round(toNumber(dbStats.blk_read_time), 2),
            write_time_ms: round(toNumber(dbStats.blk_write_time), 2),
          },
          errors: {
            deadlocks: toNumber(dbStats.deadlocks),
          },
          storage: {
            database_size_bytes: databaseSizeBytes,
            table_count: tableCount,
            index_count: indexCount,
          },
          sessions_by_state: states,
          stats_reset_at: dbStats.stats_reset || null,
        },
        alerts,
      },
    });
  })
);

export default router;
