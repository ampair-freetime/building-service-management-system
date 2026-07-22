---
name: building-service-management
description: Develop and maintain this repository's FastAPI backend and Vue 3 frontend. Use for features, fixes, API endpoints, UI views, service integrations, tests, configuration, containers, or architecture changes in the Building Service Management System.
---

# Building Service Management

## Work in the monorepo

- Keep the FastAPI application in `Backend/app` and its tests in `Backend/tests`.
- Keep the Vue 3 application in `Frontend/src`; use Vue Composition API and Vite.
- Put versioned API endpoints under `Backend/app/api/v1/endpoints` and register them in `Backend/app/api/v1/router.py`.
- Put environment-backed backend settings in `Backend/app/core/config.py`.
- Put frontend API calls in `Frontend/src/services` instead of calling `fetch` directly from views.
- Use `/api/v1` as the shared API prefix and `VITE_API_BASE_URL` as the browser-side base URL.

## Implement changes

1. Inspect the affected backend and frontend paths before editing.
2. Preserve separation between route handling, validation schemas, business logic, and persistence as each domain grows.
3. Define explicit Pydantic request and response models for API contracts.
4. Keep UI views focused on presentation and orchestration; extract reusable behavior into components or composables.
5. Add or update focused tests for changed backend behavior.
6. Update `.env.example` when introducing configuration.
7. Verify backend changes with `pytest` and `ruff check .` from `Backend`.
8. Verify frontend changes with `npm run build` from `Frontend`.

## Follow project conventions

- Prefer async FastAPI route handlers for I/O-bound work.
- Inject dependencies through FastAPI rather than constructing infrastructure in endpoint functions.
- Return stable, versioned JSON contracts and appropriate HTTP status codes.
- Never commit secrets, local `.env` files, virtual environments, dependencies, or build output.
- Keep Docker and local-development commands aligned when dependencies or ports change.
