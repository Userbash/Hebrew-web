import { createClient } from 'redis';

let client: any = null;
let connectPromise: Promise<any | null> | null = null;
let disabledUntil = 0;

const RETRY_COOLDOWN_MS = 30_000;
const DEFAULT_TTL_SECONDS = 300;

const runningInContainer = Boolean(process.env.IS_CONTAINER || process.env.CONTAINER || process.env.KUBERNETES_SERVICE_HOST);

const getRedisUrl = () => {
    if (process.env.REDIS_URL) {
        return process.env.REDIS_URL;
    }

    const host = process.env.REDIS_HOST || (runningInContainer ? 'redis' : '127.0.0.1');
    const port = process.env.REDIS_PORT || '6379';
    return `redis://${host}:${port}`;
};

const shouldSkipConnect = () => Date.now() < disabledUntil;

const getClient = async (): Promise<any | null> => {
    if (client?.isOpen) {
        return client;
    }

    if (shouldSkipConnect()) {
        return null;
    }

    if (!connectPromise) {
        connectPromise = (async () => {
            try {
                const redis = createClient({ url: getRedisUrl() });

                redis.on('error', () => {
                    disabledUntil = Date.now() + RETRY_COOLDOWN_MS;
                });

                await redis.connect();
                client = redis;
                disabledUntil = 0;
                return client;
            } catch (_err) {
                disabledUntil = Date.now() + RETRY_COOLDOWN_MS;
                client = null;
                return null;
            } finally {
                connectPromise = null;
            }
        })();
    }

    return connectPromise;
};

export const redisGetJson = async <T>(key: string): Promise<T | null> => {
    try {
        const redis = await getClient();
        if (!redis) {
            return null;
        }

        const value = await redis.get(key);
        if (!value) {
            return null;
        }

        return JSON.parse(value) as T;
    } catch (_err) {
        return null;
    }
};

export const redisSetJson = async (key: string, value: unknown, ttlSeconds: number = DEFAULT_TTL_SECONDS) => {
    try {
        const redis = await getClient();
        if (!redis) {
            return;
        }

        await redis.set(key, JSON.stringify(value), { EX: ttlSeconds });
    } catch (_err) {
        // noop
    }
};

export const redisDel = async (...keys: string[]) => {
    if (keys.length === 0) {
        return;
    }

    try {
        const redis = await getClient();
        if (!redis) {
            return;
        }

        await redis.del(keys);
    } catch (_err) {
        // noop
    }
};
