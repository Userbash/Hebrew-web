# Admin Split Security Checklist

## A. Identity & Session
- [ ] `access`/`refresh` cookies: `HttpOnly=true`
- [ ] Cookies only over TLS: `Secure=true`
- [ ] `SameSite` policy documented and tested
- [ ] Cookie `Domain` verified for app/admin separation
- [ ] Refresh token rotation enabled
- [ ] Short access token TTL configured
- [ ] Global logout invalidates active sessions

## B. Authorization
- [ ] All admin endpoints only under `/api/admin/*`
- [ ] `verifyToken` applied before admin routes
- [ ] `requireRole([root, platform_admin])` enforced
- [ ] Least privilege role matrix approved
- [ ] Destructive actions require step-up auth

## C. Network/Edge
- [ ] Admin frontend on dedicated origin (`admin.*`)
- [ ] Admin API router has dedicated rate-limit
- [ ] CORS allowlist only approved origins
- [ ] Optional IP allowlist/VPN/mTLS for admin origin
- [ ] HSTS, frame-deny, nosniff headers enabled

## D. App Security
- [ ] CSRF protection for state-changing endpoints
- [ ] Input validation and payload limits
- [ ] Audit fields: who/what/when/ip/outcome
- [ ] Error responses do not leak internals
- [ ] Secrets only from env/secret manager

## E. Observability & IR
- [ ] 401/403/429 dashboard for `/api/admin/*`
- [ ] Alerts on brute-force and privilege abuse
- [ ] Audit log integrity checks
- [ ] Incident runbook with rollback path

## F. Release Gates
- [ ] Root tests pass
- [ ] Backend build/lint pass
- [ ] Frontend build/lint pass
- [ ] Auth e2e pass
- [ ] RBAC negative tests pass
- [ ] Rollback rehearsal pass
