# Project Architecture & Security Guide

This document explains how the Hebrew AI 2025 platform is built, how the security layers work, and how you can manage the system.

## 1. The Isolation Problem & BridgeOS

### Why we need it
Modern development environments (like VS Code in Flatpak or other containers) are isolated from your main computer (the "host"). They can't see your installed programs like Docker, Podman, or system tools. This is good for security, but it makes automation hard.

### How it works
We built **BridgeOS** inside `scripts/bridge/`. It's a secure gateway that allows this IDE to "call out" to the host machine.
- **`bridge.sh`**: The lower level. It detects if you're in a Flatpak and uses `flatpak-spawn --host` to run commands.
- **`exec.sh`**: The security guard. Every command must be in the `whitelist.txt`. If you try to run something else, it blocks it. This prevents any script from doing anything you haven't approved.

---

## 2. The Data Layer (PostgreSQL & Redis)

### Replication (Master-Replica)
Instead of one database, we use two:
1.  **Master (`pg_master`)**: Handles all "Writes" (creating users, saving progress).
2.  **Replica (`pg_replica`)**: A copy of the Master. It can handle "Reads" (searching items, viewing profiles).
This setup means if one database fails, your data stays safe, and it makes the app much faster under heavy load.

### Optimized Schema
- **UUIDs**: We don't use numbers (1, 2, 3) for IDs. We use UUIDs (random strings). This makes it impossible for a hacker to "guess" a user's ID by just adding 1 to their own.
- **Fast Search**: We use PostgreSQL's `tsvector` and `GIN` indexes. This is like having a mini Google inside your database. It pre-indexes every word in your items so searches happen in milliseconds, even with millions of rows.

---

## 3. Backend Security

### Password Hashing
We never store passwords in plain text. We use **bcrypt** with a "cost factor" of 12. This creates a very complex hash that would take years to crack with current hardware.

### SQL Injection Protection
We use **parameterized queries**. Instead of building a string like `"SELECT * FROM users WHERE name = " + user_input`, we send the query and the data separately. The database never treats user input as executable code.

### Session Management
Login is handled via **JWT (JSON Web Tokens)** stored in **HttpOnly Cookies**. This means the browser hides the token from JavaScript, making it immune to most XSS (Cross-Site Scripting) attacks.

---

## 4. How the Scripts Work Together

We've automated the workflow into three main steps:

1.  **`auto_bridge.sh`**: Run this once. It sets up the permissions so the IDE can talk to your host.
2.  **`start_replicated_db.sh`**: This spins up the Master, the Replica, and the Redis cache. It also applies all the table structures automatically.
3.  **`build_abstracted.sh`**: This creates the container images for the app.
4.  **`start_manual.sh`**: This hooks everything together and launches the web interface.

## Project Files at a Glance

- **`/backend`**: The brains. Written in TypeScript so we catch bugs during development, not at runtime.
- **`/frontend-react`**: The face. Fast, responsive, and talks to the API via secure cookies.
- **`/scripts`**: The engine room. All the DevOps logic lives here.

---

### Managing the Whitelist
If you need a new tool (e.g., `kubectl`), just add its name to `scripts/bridge/whitelist.txt`. This is your manual override to keep things safe.
