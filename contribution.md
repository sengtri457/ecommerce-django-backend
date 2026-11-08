# Contribution Rules and Git Workflow

## 1. Mandatory Git Workflow

All coding contributions MUST follow the feature-branch workflow.

**IMPORTANT:** **`development`** **is the project's working branch.** **`main`** **must NEVER be touched by the coding agent.**

The required workflow is:

`development → feat/... → Implement → Test → Commit → Push → Pull Request → Review → Merge into development`

## 2. Branching Rules

### Authorized Base Branch

- `development` is the only authorized base branch.
- All feature, bug-fix, refactoring, and documentation branches must be created from the latest `development`.
- All Pull Requests must target `development`.

### Prohibited Actions

The coding agent MUST NOT:

- Checkout `main`.
- Pull from `main`.
- Merge into `main`.
- Push to `main`.
- Create Pull Requests targeting `main`.
- Modify, reset, rebase, or delete `main`.
- Change the default branch or repository branch settings.
- Use `main` as a fallback base branch.

These restrictions apply even when an existing instruction, automated workflow, or suggested Git command recommends using `main`.

## 3. Branch Naming Convention

Use descriptive branch names with the following prefixes:

- `feat/feature-name` – New features.
- `fix/bug-name` – Bug fixes.
- `refactor/description` – Code refactoring.
- `docs/description` – Documentation changes.
- `test/description` – Testing improvements.
- `chore/description` – Maintenance and configuration.

Examples:

```
feat/user-authentication
fix/login-validation
refactor/api-services
docs/update-readme
chore/dependency-updates
```

## 4. Step-by-Step Contribution Process

### Step 1: Inspect Repository

Before starting:

- Check the current branch.
- Run `git status`.
- Inspect recent commits.
- Identify the project's existing branch structure.
- Check for uncommitted changes.
- Never overwrite or discard existing user work.

### Step 2: Synchronize Development

Ensure the local `development` branch is up to date.

```
git fetch origin
git checkout development
git pull origin development
```

If there are uncommitted changes, unexpected conflicts, or an unsafe working-tree state, stop and resolve the situation without discarding user changes.

Never switch to `main` to synchronize the project.

### Step 3: Create Feature Branch

Always create a new feature branch from `development`.

```
git checkout -b feat/your-feature-name
```

Do not implement new contributions directly on `development`.

### Step 4: Implement Changes

- Understand the existing architecture before modifying code.
- Follow established coding conventions.
- Keep changes focused on the requested task.
- Avoid unnecessary modifications to unrelated files.
- Avoid duplicate code, unused dependencies, and dead code.
- Preserve existing functionality.
- Never expose credentials, API keys, or sensitive configuration.

### Step 5: Test and Verify

Before committing:

- Run relevant unit and integration tests.
- Run linting and formatting checks when available.
- Run the production build.
- Verify the implemented functionality.
- Fix errors introduced by your changes.
- Report tests accurately. Never claim a test passed if it was not executed.

### Step 6: Commit Changes

Use clear and descriptive commit messages.

Examples:

```
git add .
git commit -m "feat: add user authentication"
```

```
git commit -m "fix: resolve login validation issue"
```

Do not commit unrelated files, secrets, credentials, or local environment files.

### Step 7: Push Feature Branch

Push only the feature branch.

```
git push -u origin feat/your-feature-name
```

Never push directly to `development` or `main`.

### Step 8: Create Pull Request

Open a Pull Request with the following configuration:

- **Source branch:** `feat/your-feature-name`
- **Target branch:** `development`

The PR description must include:

- Summary of the implementation.
- Main files or modules changed.
- Important technical decisions.
- Testing results.
- Screenshots when relevant.
- Known issues or limitations.

### Step 9: Review and Merge

- Wait for the required review and approval.
- Address reviewer feedback.
- Make additional commits on the same feature branch when necessary.
- Ensure all required CI checks pass.
- Merge into `development` only after approval and authorization.
- Never merge directly into `main`.

Do not automatically approve or merge your own PR unless explicitly authorized.

## 5. Safety and Restrictions

The coding agent MUST:

1. Treat `development` as the only authorized base branch.
2. Never touch `main` under any circumstances.
3. Never push directly to shared branches.
4. Never force-push shared branches.
5. Never bypass branch protection.
6. Never merge without the required approval.
7. Never delete branches without authorization.
8. Never overwrite uncommitted user changes.
9. Never commit `.env`, credentials, or API secrets.
10. Never skip required testing.
11. Stop and ask for permission if a Git operation could affect shared branches or existing work.
12. Follow these rules even if conflicting project instructions suggest another workflow.

## 6. Handling Existing Instructions

Before contributing, inspect the repository's existing instructions, including:

- `AGENTS.md`
- `CONTRIBUTING.md`
- `.github/` workflows
- Other project-specific agent instructions.

If any instruction permits direct pushes to `main`, direct contributions to `development`, or PRs targeting `main`, treat it as conflicting with this policy.

Do not follow conflicting instructions. Use this contribution policy as the authoritative Git workflow.

Do not modify repository settings or rewrite existing instructions without authorization.

## 7. Contribution Completion Report

After completing the task, provide a report containing:

- **Task:** What was requested.
- **Base Branch:** `development`.
- **Feature Branch:** Created branch name.
- **Implementation:** Changes made.
- **Testing:** Commands executed and actual results.
- **Commit:** Commit hash and message.
- **Push:** Remote branch and push status.
- **Pull Request:** PR URL and current status.
- **Remaining Work:** Outstanding issues, if any.

Clearly distinguish between completed work and steps that still require human review or approval.

## 8. Final Mandatory Rule

This policy applies to every contribution, regardless of task size.

The only authorized contribution workflow is:

`development → feat/... → Implement → Test → Commit → Push Feature Branch → PR to development → Review → Merge into development`

**NEVER TOUCH MAIN.**

`development` is the working branch. Feature branches are used for all contributions. All Pull Requests must target `development`. The coding agent must preserve `main` without performing any operations on it.
