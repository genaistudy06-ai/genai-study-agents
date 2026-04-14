# GitHub Copilot — Workspace Context

## Migration Agent System

This workspace uses a 4-agent Angular → React migration pipeline.
**All migration work starts with:**
```
@MigrateOrchestrator what's next
```

The orchestrator auto-discovers your project structure on every session start.
No hardcoded paths — works in any NX monorepo.

---

## Shared Knowledge Files (Auto-Managed by Agents)

| File | Purpose | Updated By |
|---|---|---|
| `WORKSPACE_MAP.md` | Live project structure map | Orchestrator (session start) |
| `MIGRATION_LEARNINGS.md` | Accumulated patterns and known mistakes | Orchestrator (after each pipeline) |
| `MIGRATION.md` | Module progress tracker | Orchestrator (after each approval) |
| `SESSION_STATE.md` | Mid-pipeline state for resumability | Orchestrator (during pipeline) |
| `REVIEW_REPORT.md` | Latest reviewer gate results | Reviewer |
| `PR_DESCRIPTION.md` | Auto-generated PR description | Reviewer (on approval) |

---

## Quality Standards (Non-Negotiable)

- 100% Vitest coverage — statements, branches, functions, lines
- Zero ESLint errors
- Zero SonarQube critical/major issues
- Cognitive complexity ≤ 15 per function
- `React.memo` on every component
- `useCallback` on every callback prop
- `useMemo` on every derived value
- All props fully typed — no `any`, no unnarrowed `unknown`

---

## Instruction Files

- `.github/instructions/angular-to-react-migration.instructions.md`
- `.github/instructions/angular-to-react-incremental-migration.instructions.md`
