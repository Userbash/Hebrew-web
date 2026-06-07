# PLAN: CRM & Frontend Rewrite

## 1. Backend Analysis & Atomic Features

Based on the backend implementation (`backend/api/routes/`), the following modules need to be implemented in the frontend:

### Auth & User Context
- **Login / Register / Recover**: Basic authentication flow (`auth.ts`).
- **User Profile**: User dashboard, avatar configuration, progress in courses (`profileAvatar.ts`, `progress.ts`).
- **Session Management**: JWT handling, refresh tokens, auto-logout.

### Store & Cart (Shop)
- **Catalog**: Display items from `items.ts`.
- **Cart**: Local state management for user's cart.
- **Checkout**: Simulated or integrated checkout flow.

### Educational Content
- **Lessons**: Display lesson content and handle completion tracking (`lessons.ts`).
- **Quizzes**: Interactive quiz interface, submit attempts (`quizzes.ts`).
- **Dictionary**: Vocabulary lists and learning interface (`dictionary.ts`).
- **Publications**: Blog or articles view (`publications.ts`).

### Admin Dashboard (CRM)
- **Access Control**: Role-based access control (RBAC) to protect admin routes (`accessControl.ts`).
- **User Management**: CRM view to manage users, ban, change roles (`users.ts`).
- **System Metrics & Logs**: Dashboard for monitoring system health and logs (`systemMetrics.ts`, `logs.ts`, `auditEvents.ts`).
- **AI Orchestrator**: Interface to interact with backend orchestrator (`orchestrator.ts`, `devtoolkit.ts`).

## 2. Technical Stack
- **Framework**: React + Vite (TypeScript)
- **Styling**: Tailwind CSS + CSS Variables for Design System
- **State Management**: Zustand
- **Routing**: React Router DOM (v6)
- **Data Fetching**: Axios + custom hooks
- **Icons**: Lucide React

## 3. Execution Phases
1. **Scaffold & Setup**: Initialize missing packages, routing, and store.
2. **Design System**: Define colors, typography, UI components (Buttons, Inputs, Cards).
3. **Core Pages**: Login page, App Shell layout.
4. **Admin Panel**: Dashboard overview, Sidebar navigation.
