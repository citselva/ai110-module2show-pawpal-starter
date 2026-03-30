# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class in [pawpal_system.py](pawpal_system.py) implements three distinct algorithmic strategies to produce an optimized, conflict-aware daily care plan.

### Tiered Optimization: Composite Sorting Key

Optional tasks are ranked using a composite sort key of `(-priority, duration)`, applied via `sort_tasks()`. This two-dimensional key encodes a specific scheduling philosophy: among tasks of equal priority, shorter tasks are preferred first — a form of Shortest-Job-First (SJF) optimization applied within each priority tier. The practical effect is that the greedy fill phase in `generate_schedule()` maximizes the *number* of tasks that fit within the remaining time budget, rather than simply consuming high-priority time until the budget is exhausted.

The two-phase structure reinforces this:

- **Phase 1** unconditionally schedules all `is_required` tasks, guaranteeing essential care regardless of time constraints. A Time Deficit is surfaced in the reasoning string if required tasks exceed `available_time_mins`.
- **Phase 2** applies the composite sort to optional tasks and greedily fills the remaining budget, skipping any task whose `duration` exceeds what is left.

This separation ensures correctness (required tasks are never dropped) while still optimizing efficiency in the discretionary tier.

### Conflict Detection: Sweep-Line Approach

`detect_conflicts()` implements a classical interval sweep-line algorithm over the subset of tasks that carry an explicit `start_time`. Tasks are first sorted chronologically — zero-padded `HH:MM` strings are lexicographically equivalent to chronological order, making the sort O(n log n) without any parsing overhead. The algorithm then performs a single left-to-right pass, comparing each task's `start_time` against the previous task's computed `end_time`.

`end_time` is derived lazily via a `@property` on `Task`: it parses `start_time` using `datetime.strptime`, adds `duration` minutes via `timedelta`, and formats the result back to `HH:MM`. This approach handles midnight rollover correctly as a side effect of `datetime` arithmetic. Any pair where `curr.start_time < prev.end_time` constitutes an overlap and is appended to the conflict list. The result is O(n) after sorting, with no auxiliary data structures.

After both scheduling phases complete, `generate_schedule()` invokes `detect_conflicts()` on the final scheduled list and appends a `WARNING` entry to the reasoning string for each overlapping pair, surfacing the issue to the UI without blocking schedule generation.

### Automation: `datetime` and `timedelta` for Recurring Tasks

`Task` supports three recurrence modes via the `frequency` field: `'one-off'`, `'daily'`, and `'weekly'`. Completion is handled by `Pet.complete_task()`, which branches on `frequency` and advances `due_date` using `timedelta` rather than creating new `Task` objects:

- `'daily'` tasks advance by `timedelta(days=1)`, resurfacing in tomorrow's schedule.
- `'weekly'` tasks advance by `timedelta(weeks=1)`, resurfacing on the same weekday next week.
- `'one-off'` tasks set `is_completed = True` and are permanently retired.

The `Owner.get_all_tasks()` method enforces temporal relevance by filtering on `task.due_date <= date.today()`, so future-dated recurring tasks are invisible to the scheduler until they become actionable. This creates a perpetual, zero-allocation recurrence system: the task object is mutated in place on each completion, and the scheduler's view automatically narrows to what is due without any background job or polling mechanism.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
