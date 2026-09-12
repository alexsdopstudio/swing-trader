# ADR-004 — Branch and pull request development workflow

Status: accepted

## Context

The project is designed to be developed by both humans and AI coding agents. Direct feature work on `main` makes review, rollback, experiment attribution, and project memory harder to reason about. The repository therefore needs a predictable development protocol that every contributor can follow.

## Decision

All logical changes are developed on dedicated branches and merged through pull requests into `main`.

Branch names use an approved type prefix and lowercase kebab-case. Commit subjects and PR titles follow Conventional Commits. CI validates branch names, PR titles, and commit subjects. Pull requests must pass required CI checks before merge.

Squash merge is the preferred merge strategy so that the reviewed PR title becomes the single clean commit on `main`. The source branch should be deleted after merge.

## Consequences

- `main` remains a reviewed integration branch rather than a working branch.
- AI agents must create a branch and PR even when they have direct write access.
- Changes are easier to audit and associate with plans, ADRs, and experiments.
- Contributors must keep PRs focused enough to review as one logical change.
- CI may reject otherwise valid code if naming or commit conventions are not followed; this is intentional.

## Enforcement

Repository-level instructions live in `CONTRIBUTING.md` and `AGENTS.md`. `.github/workflows/pr-conventions.yml` checks naming conventions on pull requests. GitHub branch protection/rulesets should also require pull requests and passing checks when repository administration permissions are available.
