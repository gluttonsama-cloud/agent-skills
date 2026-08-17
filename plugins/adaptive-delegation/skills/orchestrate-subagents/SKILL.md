---
name: orchestrate-subagents
description: Coordinate complex Codex work with selective, cost-aware subagent delegation across planning, implementation, and validation. Use when the user explicitly requests subagents, agents, delegation, or parallel work; when a task has two or more independently ownable workstreams; when an independent review materially reduces risk; or when a Luna coding subagent repeatedly fails to make progress and should be escalated to Sol. Avoid spawning agents for small, tightly sequential, or clarification-blocked tasks.
---

# Orchestrate Subagents

Use parallelism when it shortens the critical path, isolates context, or materially reduces risk. Keep the root agent responsible for decomposition, shared contracts, external side effects, integration, final verification, and user communication.

## Decide Before Spawning

Require a child task to be independently specifiable. Also require at least one clear benefit: reduced wall-clock time, useful context isolation, or independent risk reduction.

For medium or larger work with at least two independent workstreams, default to two direct children. Use a third free slot only for a genuinely independent workstream. Keep work local when it is small, sequential, unclear, approval-sensitive, or faster with one batched tool call.

Treat explicit user invocation as task-level delegation intent. Carry it across planning, implementation, validation, compaction, and follow-up turns while they clearly continue the same task. Do not carry it into unrelated work.

When implementation is authorized and the task is medium or larger, delegate at least one bounded implementation workstream whenever any component or file set can have exclusive ownership. Planning or review children alone do not satisfy an explicit request to delegate implementation. If no implementation can safely be delegated, explain the concrete reason briefly before doing the work locally.

Potential write overlap is an ownership problem, not an automatic reason to keep all implementation at the root. Resolve it by assigning a single child exclusive ownership of the overlapping area, delegating work sequentially, or separating shared contracts from component implementation. Keep tiny fixes local.

If spawning, tell the user briefly what is being delegated and why. Respect higher-priority instructions, current authorization, available tools, and concurrency limits.

## Define the Child Contract

Give every child a bounded task containing:

- outcome and acceptance criteria;
- required inputs and relevant paths;
- allowed read/write scope and exclusive file ownership;
- prohibited actions and whether descendants are allowed;
- validation commands;
- required return format.

Use the role prompts in [roles.md](references/roles.md) when helpful. Preserve read-only status for planning, diagnosis, review, and research unless the user authorized implementation. Do not let a child broaden scope or perform external, destructive, or approval-sensitive actions.

Use `fork_turns: "none"` with self-contained context by default. Use a small positive turn count only when recent context matters. Full-history forks inherit the parent model and reasoning effort, so do not request model overrides with them.

## Route Models

Treat the current `spawn_agent` metadata as authoritative. Use Luna by default and Sol only through the escalation rules below.

| Work shape | Model | Reasoning effort |
|---|---|---|
| Search, inventory, log triage, routine checks, tests, extraction | `gpt-5.6-luna` | `medium` |
| Bounded implementation, debugging, test design, or review requiring judgment | `gpt-5.6-luna` | `high` |
| Architecture, cross-cutting diagnosis, security or data-integrity judgment, conflict resolution | `gpt-5.6-sol` | `medium` |
| Exceptional high-consequence judgment where deeper reasoning is likely to change the outcome | `gpt-5.6-sol` | `high` or `xhigh` |

Keep Luna as the default. Use Sol only when the task is important and reasoning complexity justifies the cost, or when Luna implementation is demonstrably stuck. Do not use `max` or `ultra` by default.

If an override is unavailable, omit the model and reasoning fields to inherit the root model. Never guess model slugs by repeated failures.

## Escalate Stuck Luna Work

Do not let Luna repeat the same unsuccessful approach. Consider a Luna implementation stuck when any of these occurs:

- the same failure signature appears after a targeted correction;
- a retry restates or reapplies substantially the same approach without new evidence;
- focused tests still fail after one bounded Luna retry;
- the child reports that the solution requires architectural, cross-module, security, or data-integrity judgment beyond its bounded task.

On the first failure, send Luna the concrete error, failed acceptance criterion, and one bounded correction request. If it then remains stuck, stop that child and spawn Sol with the original contract plus the failed attempts, evidence, and current workspace state:

- use Sol `medium` for ordinary escalation;
- use Sol `high` or `xhigh` only when failure cost is high and deeper reasoning is likely to add value.

Allow at most one Luna correction cycle before Sol escalation. Do not restart Luna with cosmetic prompt changes. The root agent must verify Sol's result independently.

## Coordinate and Integrate

- Default to direct children and prohibit descendants unless explicitly necessary.
- Assign one writer per overlapping file area; use read-only reviewers where ownership would conflict.
- Prefer an implementer with an exclusive component or file set, while the root owns shared contracts, integration, external effects, and final verification.
- If planning agents already completed, reuse their evidence when contracting implementation agents instead of treating delegation as finished.
- Continue useful root work while children run and prefer longer waits over frequent polling.
- When new user input changes the task, redirect or interrupt children whose work is no longer relevant.
- Treat child output as evidence, inspect changed files, reconcile conflicts, and run root-level tests.
- Before responding, ensure every child is completed, intentionally stopped, or clearly reported as blocked.

Summarize outcomes rather than agent choreography unless the user asks for details.
