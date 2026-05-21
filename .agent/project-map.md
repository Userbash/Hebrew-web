# Project Map

## Type
- Monorepo-style JavaScript/TypeScript web application.
- Frontend: React 19, Vite 8, TypeScript, Tailwind CSS, React Router, Axios, React Query.
- Backend: Node.js, Express, TypeScript, PostgreSQL client `pg`, JWT cookie auth, bcrypt, Helmet, CORS, rate limiting.
- Infrastructure: Docker Compose with Traefik, Postgres, Redis, backend, frontend.

## Main Tree
```text
.
├── package.json                  # root test runner
├── docker-compose.yml            # production-like stack with Traefik/Postgres/Redis
├── docker-compose.prod.yml
├── frontend-react/
│   ├── package.json              # Vite/React scripts
│   ├── vite.config.ts            # dev proxy /api -> backend
│   ├── src/
│   │   ├── api/                  # axios client and auth schemas
│   │   ├── components/           # auth guard/forms and UI components
│   │   ├── context/              # auth/theme/language providers
│   │   ├── pages/                # page-level React views
│   │   └── App.tsx               # protected dashboard shell
│   └── Dockerfile
├── backend/
│   ├── package.json              # backend build/test/lint scripts
│   ├── server.ts                 # Express bootstrap and route mounting
│   ├── api/
│   │   ├── data/db.ts            # PostgreSQL data access
│   │   ├── middleware/           # auth, security, error handling
│   │   └── routes/               # REST routes under /api
│   └── Dockerfile
├── scripts/
│   ├── bridge/                   # existing host bridge helpers
│   ├── check-bridges.sh          # agent bridge diagnostic
│   ├── gemini-agent.sh           # Gemini CLI wrapper
│   ├── create-gemini-task.sh     # Gemini task file generator
│   └── run-gemini-task.sh        # Gemini task runner
└── tests/
    └── system/                   # deployment/config validation tests
```

## Commands
### Root
- Install root deps: `npm install`
- System/deployment tests: `npm test`

### Frontend
- Install deps: `cd frontend-react && npm install`
- Dev server: `cd frontend-react && npm run dev`
- Build: `cd frontend-react && npm run build`
- Lint: `cd frontend-react && npm run lint`
- Preview: `cd frontend-react && npm run preview`

### Backend
- Install deps: `cd backend && npm install`
- Dev server: `cd backend && npm run dev`
- Build: `cd backend && npm run build`
- Lint: `cd backend && npm run lint`
- Quick API test: `cd backend && npm test`
- Full API test: `cd backend && npm run test:full`

### Agent Automation
- Bridge check: `scripts/check-bridges.sh`
- Create Gemini task: `scripts/create-gemini-task.sh TID path/to/file "task text"`
- Run Gemini task: `scripts/run-gemini-task.sh TID`

## Source Directories
- `frontend-react/src`
- `backend/api`
- `backend/server.ts`
- `tests/system`
- `scripts`

## Generated / Do Not Touch Without Reason
- `.git/`
- `node_modules/`, `backend/node_modules/`, `frontend-react/node_modules/`
- `backend/dist/`, `frontend-react/dist/`
- `tests/.test-results.json`, `tests/.nginx-detection-results.json` are test-runner artifacts.
- Secrets and local environment files: `.env`, `.env.*` if present.

## Potentially Dangerous Zones
- `backend/api/middleware/auth.ts`: JWT cookie validation and auth boundary.
- `backend/api/middleware/security.ts`: rate limiting and security middleware.
- `backend/server.ts`: CORS, Helmet CSP, global middleware and route mounting.
- `backend/api/data/db.ts`: SQL access and database credentials from environment.
- `scripts/bridge/*`: host bridge and command execution helpers.
- Docker socket mount in `docker-compose.yml`: `/var/run/docker.sock:/var/run/docker.sock:ro` for Traefik provider.
- Any future `podman`, `docker`, `flatpak-spawn`, `systemctl`, or shell bridge automation.

## Dependencies
### Frontend runtime
- React, React DOM, React Router, Axios, React Hook Form, Zod, React Query, Framer Motion, lucide-react.

### Frontend build/lint
- Vite, TypeScript, ESLint, Tailwind/PostCSS tooling.

### Backend runtime
- Express, pg, bcrypt, jsonwebtoken, cookie-parser, cors, helmet, compression, express-rate-limit, dotenv.

### Backend build/lint/test
- TypeScript, ESLint, ts-node, nodemon, mocha, node-fetch.

### Root test tools
- yaml, node-fetch.

## External Tools
- Node.js/npm.
- Docker/Podman depending on environment.
- Traefik, Postgres, Redis in Docker Compose.
- Optional `flatpak-spawn --host` bridge when running inside Flatpak VS Code.
- Optional `npx @google/gemini-cli` for external read-only review tasks.

## Validation Policy
- Do not claim a defect-free state.
- Final status must be based only on commands that actually ran.
- External Gemini reports are advisory and must be checked by GPT before changes are accepted.
