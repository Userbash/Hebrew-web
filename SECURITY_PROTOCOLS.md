# Security & Privacy Protocols

This project implements a multi-layer security architecture to ensure data confidentiality, integrity, and availability.

## 1. Authentication & Session Security

### Secure Identity Exchange
- **Frontend to Backend**: Credentials (email/password) are transmitted over TLS-encrypted channels. The backend never logs or stores raw passwords.
- **Session Tokens**: We use **JWT (JSON Web Tokens)** signed with a high-entropy secret key.
- **Storage**: Tokens are exclusively stored in **HttpOnly, Secure, and SameSite: Lax** cookies. 
  - *HttpOnly*: Prevents JavaScript from reading the session token (immune to most XSS).
  - *Secure*: Ensures cookies are only sent over HTTPS.
  - *SameSite*: Mitigates CSRF (Cross-Site Request Forgery) by limiting cookie transmission on cross-site requests.

### Brute-Force Protection
- **Rate Limiting**: The `/api/auth/login` endpoint is limited to 5 attempts per 15 minutes per IP address using `express-rate-limit`.
- **Password Hashing**: We use **bcrypt** with a cost factor of 12. This slow hashing algorithm makes brute-force or rainbow table attacks computationally prohibitive on the backend database.

---

## 2. Database Integrity & Protection

### SQL Injection Defense
- **Strict Parameterization**: Every interaction between the Node.js backend and the PostgreSQL database uses **prepared statements** (`$1`, `$2` placeholders). 
- **Validation**: Input data is validated at the API layer (via Zod schemas) before reaching the database logic.

### Entity Anonymization
- **UUID v4**: We use random UUIDs for all primary keys. This prevents "Insecure Direct Object Reference" (IDOR) attacks where an attacker could guess a user's ID by simply incrementing a number.

---

## 3. Environment Isolation (BridgeOS)

### Host-to-IDE Security
- **Command Whitelisting**: The `exec.sh` bridge enforces a strict whitelist for host machine access. 
- **Auditing**: Every command executed through the bridge is logged in `/var/tmp/bridge_access.log` for transparency and auditing.
- **Flatpak Jailbreak Prevention**: The IDE runs in a sandbox. The bridge only opens specific, audited holes (like `flatpak-spawn`) required for DevOps tasks.

---

## 4. Privacy & Data Transmission

### Transport Layer Security (TLS)
- All production data is transmitted via HTTPS. In development, the system is designed to seamlessly transition to SSL termination via Traefik.

### Least Privilege Principle
- The database user (`admin`) used by the backend is restricted to the application database.
- The replication user (`replicator`) has zero access to the data tables and can only perform WAL streaming.

### Automated Routing & UX Privacy
- **Automatic Panel Redirection**: The system automatically detects user roles and redirects to either the `/admin` or `/dashboard` panel.
- **Landing Page Gating**: Unauthenticated users are presented with a "Welcome/Invite" page, preventing any leak of internal interface structure before login.
- **Browser-Native i18n**: We respect the user's privacy by detecting language preferences locally in the browser (`navigator.language`) rather than tracking IP addresses for geolocation.
