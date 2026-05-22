import api from './client';

export interface AdminSystemMetricsResponse {
  success: boolean;
  metrics: {
    collected_at: string;
    site: {
      uptime_seconds: number;
      uptime_human: string;
      environment: string;
      pid: number;
      node_version: string;
    };
    system: {
      hostname: string;
      platform: string;
      arch: string;
      release: string;
      uptime_seconds: number;
      uptime_human: string;
      cpu: {
        cores: number;
        load_1m: number;
        load_5m: number;
        load_15m: number;
        load_percent_1m: number;
        process_cpu_percent: number;
      };
      memory: {
        total_bytes: number;
        used_bytes: number;
        free_bytes: number;
        used_percent: number;
        rss_bytes: number;
        heap_used_bytes: number;
        heap_total_bytes: number;
        external_bytes: number;
      };
      disk: {
        path: string;
        total_bytes: number;
        free_bytes: number;
        available_bytes: number;
        used_bytes: number;
        used_percent: number;
        total_inodes: number;
        free_inodes: number;
        used_inodes: number;
        inode_used_percent: number;
      };
    };
    database: {
      status: 'up' | 'degraded';
      probe_latency_ms: number;
      waiting_locks: number;
      lock_waiting_queries: number;
      long_running_queries: number;
      max_active_query_age_seconds: number;
      active_connections: number;
      cache_hit_percent: number;
      transaction: {
        commits: number;
        rollbacks: number;
      };
      rows: {
        returned: number;
        fetched: number;
        inserted: number;
        updated: number;
        deleted: number;
      };
      io: {
        blocks_read: number;
        blocks_hit: number;
        temp_files: number;
        temp_bytes: number;
        read_time_ms: number;
        write_time_ms: number;
      };
      errors: {
        deadlocks: number;
      };
      storage: {
        database_size_bytes: number;
        table_count: number;
        index_count: number;
      };
      sessions_by_state: Record<string, number>;
      stats_reset_at: string | null;
    };
    alerts: Array<{
      level: 'ok' | 'warn' | 'critical';
      code: string;
      message: string;
    }>;
  };
}

export const adminSystemApi = {
  metrics: async () => {
    const { data } = await api.get<AdminSystemMetricsResponse>('/admin/system/metrics');
    return data;
  },
};
