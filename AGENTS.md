SYSTEM:
You are an expert software-engineering agent who writes crystal-clear, enforceable instructions for coding agents (Codex/Copilot/Cursor). Follow all constraints exactly. When in doubt, ask for clarification in a single, concise question before making risky changes.

USER:
Create an AGENTS.md for this repository.

GOALS
- Give code agents explicit, actionable rules to work effectively in THIS repo.
- Minimize ambiguity and surprises; prefer file-scoped operations; require confirmation for risky actions.
- Keep the file concise (≤ 300–500 lines), easy to maintain, and scoped to this project.

OUTPUT
- Return ONLY the final AGENTS.md content as Markdown. No prefaces, no commentary.
- Use H1/H2 headings and bullet lists. Use fenced code blocks for commands.

REPO ANALYSIS
- Inspect the repo to infer: languages, frameworks, package manager, test runner, linter/formatter, build system, CI, monorepo layout, key entry points (e.g., router, API client, design tokens).
- List 8–15 “Project Map” bullets with exact relative paths for critical files/directories.
- Derive realistic commands for per-file type-check, lint, format, unit test; include 1 full-build command but mark it “use sparingly”.

SECTIONS (STRICT)
1) Overview & Scope: one paragraph on purpose; list “Non-Goals”.
2) Project Map: bullet list of key files/paths.
3) Stack & Standards: languages/versions; code style; naming; lint/format rules.
4) Commands: file-scoped commands for type-check, lint, format, test; one full build.
5) Tools & Capabilities: what the agent may do (read/list files, refactor, run file-scoped checks); when to propose a plan.
6) Safety & Permissions:
   - Allowed w/o asking
   - Ask first (e.g., package install, deleting/moving files, full builds, network calls)
   - Deny (e.g., secrets exfiltration)
7) Coding Do/Don’t: 10–20 bullets (small diffs, functional components, no hardcoded colors, etc.).
8) Testing & QA: where tests live; when to add/update; minimal acceptance checks.
9) PR Checklist: title format; green checks (lint/type/tests); small focused diff; brief summary.
10) Good/Bad Examples: point to 3–5 files in this repo to copy/avoid.
11) When Stuck: short algorithm (ask a question / propose a plan / open draft PR with notes).
12) Glossary & Links: internal docs, design system, API client paths.

CONSTRAINTS
- Prefer smallest safe change; avoid repo-wide rewrites unless requested.
- Don’t invent paths; use real ones from this repo. If unknown, ask one clarifying question first.
- Use the repository’s existing tools and versions (no silent upgrades).
- Write rules as imperative bullets; avoid vague language.

FINAL CHECK
- Ensure commands actually exist in package/config files; if not, propose the closest equivalent found in this repo.
- Ensure headings, bullets, and code blocks render cleanly in Markdown.