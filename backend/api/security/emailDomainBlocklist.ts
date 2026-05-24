import https from 'https';
import { promises as fs } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DEFAULT_CACHE_FILE_PATH = join(__dirname, '../../..', 'database', 'email-domain-blocklist.cache.txt');
const DEFAULT_CUSTOM_FILE_PATH = join(__dirname, '../../..', 'database', 'email-domain-blocklist.custom.txt');

const DEFAULT_SOURCE_URLS = [
    'https://disposable.github.io/disposable-email-domains/domains.txt',
    'https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/main/disposable_email_blocklist.conf',
];

const EMAIL_DOMAIN_REGEX = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/;

type BlocklistStatus = {
    loaded: boolean;
    sourceCount: number;
    envBlocklistCount: number;
    envAllowlistCount: number;
    customBlocklistCount: number;
    remoteBlocklistCount: number;
    lastUpdatedAt: string | null;
    lastError: string | null;
};

const parseDomainList = (value?: string) => new Set(
    (value || '')
        .split(',')
        .map((item) => item.trim().toLowerCase())
        .map((item) => item.replace(/^@/, '').replace(/^\.+/, '').replace(/\.+$/, ''))
        .filter(Boolean)
        .filter((item) => EMAIL_DOMAIN_REGEX.test(item))
);

const parseSourceUrls = (value?: string) => {
    const configured = (value || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);

    return configured.length > 0 ? configured : DEFAULT_SOURCE_URLS;
};

const normalizeDomain = (input: string) => {
    const trimmed = input.trim().toLowerCase();
    if (!trimmed) {
        return null;
    }

    const withoutComment = trimmed.split('#')[0]?.trim();
    if (!withoutComment) {
        return null;
    }

    const token = withoutComment.split(/\s+/)[0]?.trim();
    if (!token) {
        return null;
    }

    let domain = token;

    if (domain.includes('@')) {
        domain = domain.split('@').pop() || '';
    }

    domain = domain
        .replace(/^https?:\/\//, '')
        .replace(/^\*\./, '')
        .replace(/^@/, '')
        .replace(/^\.+/, '')
        .replace(/\.+$/, '');

    if (!domain) {
        return null;
    }

    if (domain.includes('/')) {
        domain = domain.split('/')[0] || '';
    }

    if (domain.includes(':')) {
        domain = domain.split(':')[0] || '';
    }

    if (!EMAIL_DOMAIN_REGEX.test(domain)) {
        return null;
    }

    return domain;
};

const parseDomainsFromText = (text: string) => {
    const domains = new Set<string>();
    const lines = text.split(/\r?\n/);

    for (const line of lines) {
        const domain = normalizeDomain(line);
        if (domain) {
            domains.add(domain);
        }
    }

    return domains;
};

const fetchTextFromUrl = (url: string, redirects = 0): Promise<string> => {
    if (redirects > 5) {
        return Promise.reject(new Error(`Too many redirects while fetching ${url}`));
    }

    return new Promise((resolve, reject) => {
        const request = https.get(url, {
            timeout: 20000,
            headers: {
                'User-Agent': 'HebrewAI-EmailBlocklist/1.0',
                Accept: 'text/plain,application/json;q=0.9,*/*;q=0.1',
            },
        }, (response) => {
            const statusCode = response.statusCode || 0;

            if (statusCode >= 300 && statusCode < 400 && response.headers.location) {
                const redirectedUrl = new URL(response.headers.location, url).toString();
                response.resume();
                fetchTextFromUrl(redirectedUrl, redirects + 1).then(resolve).catch(reject);
                return;
            }

            if (statusCode < 200 || statusCode >= 300) {
                response.resume();
                reject(new Error(`Failed to fetch ${url}: HTTP ${statusCode}`));
                return;
            }

            const chunks: Buffer[] = [];
            response.on('data', (chunk: Buffer) => chunks.push(chunk));
            response.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
        });

        request.on('timeout', () => {
            request.destroy(new Error(`Timeout while fetching ${url}`));
        });

        request.on('error', (error) => reject(error));
    });
};

const loadDomainsFromFile = async (path: string) => {
    try {
        const content = await fs.readFile(path, 'utf-8');
        return parseDomainsFromText(content);
    } catch {
        return new Set<string>();
    }
};

const writeDomainsToFile = async (path: string, domains: Set<string>) => {
    await fs.mkdir(dirname(path), { recursive: true });
    const content = `${Array.from(domains).sort().join('\n')}\n`;
    await fs.writeFile(path, content, 'utf-8');
};

const isDomainInList = (domain: string, domainList: Set<string>) => {
    if (domainList.has(domain)) {
        return true;
    }

    const parts = domain.split('.');
    for (let index = 1; index < parts.length - 1; index += 1) {
        const suffix = parts.slice(index).join('.');
        if (domainList.has(suffix)) {
            return true;
        }
    }

    return false;
};

const getEmailDomain = (email: string) => {
    const domain = email.split('@')[1] || '';
    return normalizeDomain(domain) || '';
};

const cacheFilePath = process.env.EMAIL_DOMAIN_BLOCKLIST_CACHE_FILE || DEFAULT_CACHE_FILE_PATH;
const customFilePath = process.env.EMAIL_DOMAIN_BLOCKLIST_CUSTOM_FILE || DEFAULT_CUSTOM_FILE_PATH;

const sourceUrls = parseSourceUrls(process.env.EMAIL_DOMAIN_BLOCKLIST_SOURCES);

const envBlocklistDomains = parseDomainList(process.env.EMAIL_DOMAIN_BLOCKLIST);
const envAllowlistDomains = parseDomainList(process.env.EMAIL_DOMAIN_ALLOWLIST);

let customBlocklistDomains = new Set<string>();
let remoteBlocklistDomains = new Set<string>();
let loaded = false;
let lastUpdatedAt: string | null = null;
let lastError: string | null = null;
let refreshInFlight: Promise<void> | null = null;

const autoUpdateEnabled = (process.env.EMAIL_DOMAIN_BLOCKLIST_AUTO_UPDATE || '1') !== '0';
const autoUpdateIntervalMinutes = Math.max(15, Number(process.env.EMAIL_DOMAIN_BLOCKLIST_UPDATE_INTERVAL_MINUTES || '360'));

const ensureLoaded = async () => {
    if (loaded) {
        return;
    }

    const [loadedCustom, loadedCache] = await Promise.all([
        loadDomainsFromFile(customFilePath),
        loadDomainsFromFile(cacheFilePath),
    ]);

    customBlocklistDomains = loadedCustom;
    remoteBlocklistDomains = loadedCache;
    loaded = true;
};

export const refreshEmailDomainBlocklist = async () => {
    await ensureLoaded();

    if (refreshInFlight) {
        return refreshInFlight;
    }

    refreshInFlight = (async () => {
        try {
            const downloadedSets = await Promise.all(sourceUrls.map(async (url) => {
                const content = await fetchTextFromUrl(url);
                return parseDomainsFromText(content);
            }));

            const merged = new Set<string>();
            for (const domainSet of downloadedSets) {
                for (const domain of domainSet) {
                    merged.add(domain);
                }
            }

            remoteBlocklistDomains = merged;
            await writeDomainsToFile(cacheFilePath, remoteBlocklistDomains);
            lastUpdatedAt = new Date().toISOString();
            lastError = null;
        } catch (error: unknown) {
            lastError = error instanceof Error ? error.message : String(error);
            throw error;
        }
    })();

    try {
        await refreshInFlight;
    } finally {
        refreshInFlight = null;
    }
};

export const initEmailDomainBlocklistAutomation = async () => {
    await ensureLoaded();

    if (!autoUpdateEnabled) {
        return;
    }

    try {
        await refreshEmailDomainBlocklist();
    } catch (error) {
        console.error('[EmailBlocklist] initial refresh failed:', error);
    }

    const intervalMs = autoUpdateIntervalMinutes * 60 * 1000;
    const timer = setInterval(() => {
        void refreshEmailDomainBlocklist().catch((error) => {
            console.error('[EmailBlocklist] scheduled refresh failed:', error);
        });
    }, intervalMs);

    timer.unref();
};

export const isBlockedEmailByDomainPolicy = (email: string) => {
    const domain = getEmailDomain(email);

    if (!domain) {
        return true;
    }

    if (isDomainInList(domain, envAllowlistDomains)) {
        return false;
    }

    if (isDomainInList(domain, envBlocklistDomains)) {
        return true;
    }

    if (isDomainInList(domain, customBlocklistDomains)) {
        return true;
    }

    return isDomainInList(domain, remoteBlocklistDomains);
};

export const getEmailDomainBlocklistStatus = (): BlocklistStatus => ({
    loaded,
    sourceCount: sourceUrls.length,
    envBlocklistCount: envBlocklistDomains.size,
    envAllowlistCount: envAllowlistDomains.size,
    customBlocklistCount: customBlocklistDomains.size,
    remoteBlocklistCount: remoteBlocklistDomains.size,
    lastUpdatedAt,
    lastError,
});

export const forceLoadEmailDomainCustomBlocklist = async () => {
    customBlocklistDomains = await loadDomainsFromFile(customFilePath);
};

export const getEmailBlocklistPaths = () => ({
    cacheFilePath,
    customFilePath,
    sourceUrls,
});
