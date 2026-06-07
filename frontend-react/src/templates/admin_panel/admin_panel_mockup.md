# Admin Panel Mockup Template

## Purpose
Design the admin shell around the live backend contract that already exists in this repo.

## Backend-Aligned Sections
- Dashboard: `/api/admin/health`, `/api/admin/system/metrics`, `/api/admin/logs`, `/api/admin/audit/events`
- Users: `/api/admin/users`, `/api/users/profile`, `/api/users/preferences`
- Groups & Access: `/api/admin/access/catalog`, `/api/admin/access/roles`
- Publications: `/api/admin/publications`, `/api/publications`
- API Logs: `/api/admin/logs`, `/api/admin/logs/codes`
- Audit Trail: `/api/admin/audit/events`
- System Health: `/api/admin/system/metrics`

## Visual Direction
- Shell layout with fixed left navigation and dense content workspace.
- Dark admin rail, light working surface, and restrained accent colors.
- High-density tables for admin data, with cards for health and summary metrics.
- Keep destructive actions visually separated and explicit.

## Interaction Rules
- Default to read-only summaries first, then expandable detail.
- Group admin actions by role scope and resource type.
- Use inline badges for `root`, `platform_admin`, `security_admin`, and `content_admin` visibility.
- Keep search, filters, and bulk actions above tables.
- Preserve keyboard-first navigation and visible focus states.
