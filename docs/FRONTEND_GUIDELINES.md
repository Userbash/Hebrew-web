# Frontend & UI/UX Guidelines

This document defines the visual standards, design tokens, and audit procedures for the Hebrew AI Platform frontend.

## 1. Brand Design System (2026)

### Philosophy
- **Vibe**: Sophisticated academic minimalism.
- **Target**: Students seeking clarity and visible progress.
- **UX Principles**: Bento-grid layouts, fluid micro-interactions, and progress-driven "aha" moments.

### Design Tokens
- **Colors**:
  - Primary: `#2A5C82` (Deep Academic Blue)
  - Secondary: `#FFD700` (Academic Gold)
  - Background: `#F9FAFB` (Off-white)
  - Text: `#111827` (Charcoal)
- **Typography**: "Inter" font family. Display (700) at 48px, Body (400) at 16px.

## 2. Core Components Standards

### Layouts
- **Hero Sections**: High-impact padding (py-32) with clear CTAs (min-h 44px).
- **Cards**: Use `rounded-[2rem]` or `12px` depending on context, `border-gray-100`, and soft shadows for depth.
- **Grids**: Use responsive grids (1-column mobile, 3-column desktop) for courses and dashboards.

### Forms & Interactions
- **Inputs**: Consistent heights (52px), 12px radius, and visible blue focus rings.
- **States**: Every interactive element must have explicit hover, active, focus, disabled, and loading states.
- **Feedback**: Provide immediate validation feedback on forms.

## 3. UI/UX Audit Checklist

When performing a site audit, flag the following as defects:
- **Horizontal Space**: Content usage below 60% of container width on desktop.
- **Empty Space**: Blank areas wider than 300px or vertical gaps higher than 150px.
- **Hierarchy**: Raw component names in UI, lack of clear H1/H2 separation.
- **Alignment**: Mismatched buttons, uneven margins, or broken content rails.
- **Responsiveness**: Text overflow or broken blocks at 1440px or 768px.

## 4. Testing Strategy

### Area Ownership
- **Planner Agent**: Defines the testing plan and sequences.
- **Codex Agent**: Implements test harnesses and fixtures.
- **Tester Agent**: Generates and runs unit/smoke tests.
- **Reviewer Agent**: Verifies architecture and behavior matches contracts.

### Preferred Libraries
- **Frontend**: Playwright (e2e/visual), @testing-library/react (components).
- **Backend**: Pytest (Python/Bridge), Supertest (Node/API).
