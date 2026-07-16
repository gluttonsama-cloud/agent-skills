---
name: plan-and-maintain-decisions
description: Create and execute a task plan while continuously maintaining a decision log. Use when the user asks to plan subsequent work, progress one task at a time, prepare a Proposal or Demo through staged evidence, keep strategic decisions and tradeoffs synchronized with implementation, or continue making progress while external data, stakeholders, or integrations are unavailable.
---

# Plan and Maintain Decisions

Build an evidence-driven task sequence, execute one task at a time, and keep strategic decisions synchronized with the work. Prefer updating existing planning and decision artifacts over creating duplicates.

## 1. Inspect existing context

Before asking questions or editing:

1. Read repository instructions and relevant existing plans, proposals, designs, feasibility notes, and decision records.
2. Separate confirmed facts, user-confirmed scope, current recommendations, working assumptions, and unknowns.
3. Reuse existing artifact locations and conventions. Do not create a new document when an existing one has the same responsibility.
4. Ask only when a missing choice would materially change scope and cannot be inferred safely.

## 2. Establish the artifacts

Maintain two responsibilities, whether they live in separate files or existing project systems:

- **Task plan**: what happens next, in what order, with what output and completion gate.
- **Decision log**: choices that affect product scope, target users, system boundaries, delivery shape, data ownership, architecture, risk posture, or important tradeoffs.

If either artifact is absent and the user asked to create it, adapt the templates in `assets/task-plan-template.md` and `assets/decision-log-template.md`. Keep artifacts concise and link them to each other.

Do not record ordinary implementation details as strategic decisions.

## 3. Build an executable task plan

Give every task a stable ID and define:

- outcome, not merely an activity;
- concrete deliverable;
- completion gate;
- dependencies;
- evidence needed;
- fallback when an external dependency is unavailable.

Order tasks so that cheap scope and evidence checks precede expensive implementation. For Proposal and Demo work, normally use this progression, adapting it to the project:

```text
target user and task
→ existing evidence and capability
→ external contracts or deferred assumptions
→ judgment/product rules
→ Demo scope
→ implementation
→ user validation
→ Proposal consolidation
```

Define separate quality gates for the final deliverables. A finished document is not automatically an acceptable Proposal; a working screen is not automatically a valid Demo.

## 4. Progress one task at a time

When the user requests sequential execution:

1. Select only the earliest incomplete, unblocked task.
2. State the task being executed and the assumptions used.
3. Complete its artifact and acceptance check.
4. Update its status in the task plan.
5. Synchronize any affected decisions and design documents.
6. Report the outcome and name the next task without starting it.

Do not silently work ahead on later tasks. Planning or maintaining shared artifacts needed by the current task does not count as starting another task.

Use statuses such as `pending`, `in progress`, `current baseline`, `waiting for validation`, and `complete`. Do not label a task fully validated when it only produced a working assumption.

## 5. Maintain decisions continuously

Create or update a decision entry whenever work changes any of these:

- target user or primary scenario;
- product scope or non-goals;
- system or ownership boundary;
- source of truth or data responsibility;
- delivery shape, such as Prototype, Demo, pilot, or production;
- architectural direction with meaningful migration cost;
- automation, privacy, permission, or external side-effect policy;
- a prior assumption that new evidence disproves.

Each decision must include:

- stable ID and title;
- status;
- background;
- alternatives considered;
- current choice;
- what to do and not do;
- reasons and consequences;
- evidence state;
- conditions for reconsideration.

Keep history. Mark superseded decisions and link replacements instead of deleting earlier reasoning. Update the log's latest-update marker and maintenance history after substantive changes.

Use status language that distinguishes user-confirmed scope, current recommendations, working assumptions awaiting validation, accepted decisions, rejected decisions, and superseded decisions.

## 6. Continue safely without external inputs

Do not let unavailable data, stakeholders, APIs, or upstream systems stop all useful progress.

Split the affected task into:

- work supported by existing evidence;
- a representative Mock or proposed contract;
- deferred real-world verification.

Mark data and behavior as `Real`, `Mock`, `Planned`, or `Unverified` where confusion is possible. Never invent fill rates, accuracy, user agreement, integration availability, or production readiness.

When the dependency arrives, replay the same cases against real inputs, record differences, and update the plan, decision log, feasibility analysis, and Proposal.

## 7. Keep current and future design separate

For product and architecture work, state:

- **Current design**: the smallest design supported by current evidence and required for this phase.
- **Future design**: compatible expansion directions and stable boundaries, without prematurely implementing unvalidated capabilities.

Do not use extensibility as a reason to expand current scope.

## 8. Apply delivery gates

For a Proposal, require at least:

- explicit user, problem, goals, and non-goals;
- evidence and assumptions clearly separated;
- alternatives and maintained decisions;
- current and future design;
- risks, permissions, privacy, and external dependencies;
- phased implementation and independently testable acceptance criteria;
- honest Demo or validation results when applicable.

For a Demo, require at least:

- one explicit user task and end-to-end main flow;
- representative, safely handled data;
- visible explanation of core judgments;
- clear Real/Mock/Planned boundaries;
- no unapproved production side effects;
- repeatable startup and demonstration steps;
- feedback capture that can inform the Proposal.

## 9. Report concisely

After each task, lead with:

1. what was completed;
2. the current baseline or decision;
3. which artifacts changed;
4. what remains unverified;
5. the single next task.

Do not claim certainty merely because the plan or document is complete.
