import {
    forceLoadEmailDomainCustomBlocklist,
    getEmailBlocklistPaths,
    getEmailDomainBlocklistStatus,
    refreshEmailDomainBlocklist,
} from '../api/security/emailDomainBlocklist.js';

const run = async () => {
    const paths = getEmailBlocklistPaths();

    console.log('[EmailBlocklist] update started');
    console.log('[EmailBlocklist] cache file:', paths.cacheFilePath);
    console.log('[EmailBlocklist] custom file:', paths.customFilePath);
    console.log('[EmailBlocklist] sources:', paths.sourceUrls.join(', '));

    await forceLoadEmailDomainCustomBlocklist();
    await refreshEmailDomainBlocklist();

    const status = getEmailDomainBlocklistStatus();
    console.log('[EmailBlocklist] update finished');
    console.log('[EmailBlocklist] custom domains:', status.customBlocklistCount);
    console.log('[EmailBlocklist] remote domains:', status.remoteBlocklistCount);
    console.log('[EmailBlocklist] last updated at:', status.lastUpdatedAt);
};

run().catch((error) => {
    console.error('[EmailBlocklist] update failed:', error);
    process.exit(1);
});
