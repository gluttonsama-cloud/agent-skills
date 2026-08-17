# Reusable delegation roles

Use these as prompt shapes. Begin every assignment with this compact contract:

```text
Outcome:
Inputs and paths:
Allowed reads/writes and file ownership:
Prohibited actions and descendant policy:
Acceptance criteria and validation:
Return format:
```

## Scout

Map relevant files, dependencies, and risks. Stay read-only. Return evidence with paths and concise recommendations.

## Implementer

Own an exclusive component or file set. Implement the bounded change, run focused checks, and report files changed plus test results. Preserve unrelated user edits. On failure, return the exact signature, attempted correction, and new evidence so the root can decide whether to escalate from Luna to Sol.

Use a single-writer implementer when files are coupled or likely to overlap. Sequential delegation is valid: finish and verify one owned change before handing a dependent file set to another writer. The root retains shared contracts, cross-component integration, external effects, and final verification unless the contract explicitly assigns them.

## Test runner

Run specified validation, isolate failures, and return reproducible commands and the smallest useful error excerpts. Do not edit unless explicitly authorized.

## Reviewer

Independently inspect a proposed change for correctness, regressions, security, and missing tests. Return only actionable findings ordered by severity; say explicitly when none are found.

## Researcher

Answer a narrow external or internal research question using authoritative sources. Return supported conclusions, uncertainties, and links or file references. Do not broaden scope.

## Synthesizer

Compare two or more independent findings against explicit criteria. Resolve disagreements with evidence and return a decision-ready recommendation. Use only when synthesis itself is substantial enough to delegate.
