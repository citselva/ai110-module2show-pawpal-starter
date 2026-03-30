# PawPal+ Phase 5: Formal Test Plan
## Scheduler & Task Logic — Strategy Document

**Version:** 1.0
**Date:** 2026-03-29
**Scope:** `pawpal_system.py` — `Scheduler`, `Pet`, `Owner`, and `Task` classes
**Out of Scope:** Streamlit UI (`app.py`), session state persistence

---

## How to Read This Document

Each test case below follows a four-field structure:

| Field | Purpose |
|---|---|
| **Test Objective** | The specific logical path being proven |
| **Setup Data** | The exact `Task` / `Pet` / `Owner` objects needed |
| **Success Criteria** | The exact expected state or return value |
| **Failure Impact** | The real-world risk to the pet owner if this path is broken |

Test cases are grouped into five behavioral suites that cover the full scheduler execution path, from sort input to final state mutation.

---

## Suite 1: Sort Stability

**Target method:** `Scheduler.sort_tasks()`
**Sort key:** `lambda t: (-t.priority, t.duration)`

---

### TC-SORT-01: Primary key — higher priority first

**Test Objective:** Verify that a task with `priority=5` always precedes a task with `priority=3` regardless of duration or insertion order.

**Setup Data:**
```python
low  = Task(name="Play",      duration=5,  priority=3)
high = Task(name="Medication", duration=30, priority=5)
tasks = [low, high]  # intentionally wrong order
result = scheduler.sort_tasks(tasks)
```

**Success Criteria:**
```python
result[0].name == "Medication"
result[1].name == "Play"
```

**Failure Impact:** Low-priority activities (play, grooming) could be scheduled before life-critical medication. A pet misses essential treatment.

---

### TC-SORT-02: Secondary key (tie-breaker) — shorter task first among equal priority

**Test Objective:** Verify that when two tasks share the same `priority`, the task with the shorter `duration` is sorted first (Shortest Job First tie-breaking).

**Setup Data:**
```python
long_task  = Task(name="Bath",  duration=45, priority=4)
short_task = Task(name="Brush", duration=10, priority=4)
tasks = [long_task, short_task]
result = scheduler.sort_tasks(tasks)
```

**Success Criteria:**
```python
result[0].name == "Brush"   # duration=10 wins the tie
result[1].name == "Bath"
```

**Failure Impact:** Longer low-value tasks consume the time budget before shorter high-value tasks run. The owner completes fewer tasks than the time budget allows—a silent efficiency loss.

---

### TC-SORT-03: Source list is not mutated

**Test Objective:** Verify that `sort_tasks()` returns a **new** list and does not sort the original in place.

**Setup Data:**
```python
tasks = [
    Task(name="A", duration=5, priority=1),
    Task(name="B", duration=5, priority=5),
]
original_first = tasks[0].name
result = scheduler.sort_tasks(tasks)
```

**Success Criteria:**
```python
tasks[0].name == original_first   # source list unchanged
result[0].name == "B"             # sorted copy is correct
```

**Failure Impact:** If the source list is mutated, downstream code (the UI display list, for example) shows tasks in the wrong order. Bug would be intermittent and hard to trace.

---

## Suite 2: Boundary Collisions in Conflict Detection

**Target method:** `Scheduler.detect_conflicts()`
**Comparison operator:** `curr.start_time < prev.end_time` (strict less-than)

---

### TC-CONF-01: True overlap is detected

**Test Objective:** Verify that two tasks with genuinely overlapping windows produce a conflict tuple.

**Setup Data:**
```python
task_a = Task(name="Feed",    duration=30, priority=5, start_time="09:00")
task_b = Task(name="Walk",    duration=20, priority=4, start_time="09:15")
# task_a window: 09:00–09:30 | task_b starts at 09:15 — inside task_a
conflicts = scheduler.detect_conflicts([task_a, task_b])
```

**Success Criteria:**
```python
len(conflicts) == 1
conflicts[0] == (task_a, task_b)
```

**Failure Impact:** Owners receive a schedule with double-booked tasks. A caregiver attempting to follow it would have to choose, potentially abandoning a required task.

---

### TC-CONF-02: Adjacent tasks (exact boundary) are NOT flagged as a conflict

**Test Objective:** Verify the strict `<` operator: a task starting exactly when the previous one ends is considered adjacent, not overlapping.

**Setup Data:**
```python
task_a = Task(name="Feed",   duration=30, priority=5, start_time="08:00")
task_b = Task(name="Walk",   duration=20, priority=4, start_time="08:30")
# task_a ends at 08:30 | task_b starts at 08:30
# "08:30" < "08:30" is False → no conflict expected
conflicts = scheduler.detect_conflicts([task_a, task_b])
```

**Success Criteria:**
```python
len(conflicts) == 0
```

**Failure Impact:** False-positive conflict warnings erode owner trust. If every back-to-back schedule triggers a WARNING, owners learn to ignore them—and miss real conflicts when they occur.

---

### TC-CONF-03: Tasks without `start_time` are silently excluded

**Test Objective:** Verify that tasks missing a `start_time` do not raise an exception and do not participate in conflict detection.

**Setup Data:**
```python
timed    = Task(name="Feed",  duration=30, priority=5, start_time="09:00")
untimed  = Task(name="Pill",  duration=5,  priority=5)  # start_time=None
conflicts = scheduler.detect_conflicts([timed, untimed])
```

**Success Criteria:**
```python
len(conflicts) == 0   # untimed task ignored, no crash
```

**Failure Impact:** An unhandled `AttributeError` or `TypeError` would crash the scheduler entirely, leaving the owner with no schedule at all.

---

### TC-CONF-04: Known Limitation — Midnight Rollover Blind Spot (Documentation Test)

**Test Objective:** Document the known limitation where a task crossing midnight (`23:50` + 30 min = `00:20`) is **not** detected as conflicting with a task at `00:05`, due to lexicographic string sorting placing `"00:05"` before `"23:50"`.

**Setup Data:**
```python
late_task  = Task(name="Midnight Med", duration=30, priority=5, start_time="23:50")
# end_time = "00:20" (crosses midnight correctly via timedelta)
early_task = Task(name="Morning Pill", duration=10, priority=5, start_time="00:05")
# Lexicographic sort: "00:05" < "23:50" → early_task is prev, late_task is curr
# Check: "23:50" < "00:15" → False → NO CONFLICT REPORTED (incorrect)
conflicts = scheduler.detect_conflicts([late_task, early_task])
```

**Success Criteria (documenting actual behavior):**
```python
len(conflicts) == 0   # blind spot confirmed — no conflict detected despite real overlap
```

**Expected Correct Behavior (for future fix):** `len(conflicts) == 1`

**Failure Impact:** An owner who schedules a late-night medication that runs into the early morning will receive no overlap warning. The missed conflict could result in double-dosing or skipped medication.

---

## Suite 3: State Transitions — `complete_task()`

**Target method:** `Pet.complete_task(task)`

---

### TC-STATE-01: One-off task is permanently retired

**Test Objective:** Verify that completing a `frequency='one-off'` task sets `is_completed = True` and the task no longer appears in `get_all_tasks()`.

**Setup Data:**
```python
task = Task(name="Vet Visit", duration=60, priority=5, frequency='one-off')
pet  = Pet(name="Buddy", species="Dog", age=3, tasks=[task])
owner = Owner(name="Alex", available_time_mins=120, pets=[pet])

pet.complete_task(task)
remaining = owner.get_all_tasks()
```

**Success Criteria:**
```python
task.is_completed == True
task not in remaining
```

**Failure Impact:** A one-off vet visit that was already completed continues to appear in every future schedule, causing confusion and unnecessary scheduling pressure.

---

### TC-STATE-02: Daily task advances `due_date` by exactly one day

**Test Objective:** Verify that completing a `frequency='daily'` task sets `due_date` to `today + 1 day` and does NOT set `is_completed`.

**Setup Data:**
```python
from datetime import date, timedelta
today = date.today()

task = Task(name="Feed", duration=10, priority=5, frequency='daily', due_date=today)
pet  = Pet(name="Whiskers", species="Cat", age=2, tasks=[task])

pet.complete_task(task)
```

**Success Criteria:**
```python
task.is_completed == False               # not retired
task.due_date == today + timedelta(days=1)  # resurfaces tomorrow
```

**Failure Impact:** If `is_completed` is incorrectly set to `True`, the pet is never fed again (task retired). If `due_date` does not advance, the task appears every single day until manually cleared.

---

### TC-STATE-03: Weekly task advances `due_date` by exactly seven days

**Test Objective:** Verify that completing a `frequency='weekly'` task sets `due_date` to `today + 7 days`.

**Setup Data:**
```python
today = date.today()
task = Task(name="Bath", duration=20, priority=3, frequency='weekly', due_date=today)
pet  = Pet(name="Rex", species="Dog", age=5, tasks=[task])

pet.complete_task(task)
```

**Success Criteria:**
```python
task.is_completed == False
task.due_date == today + timedelta(weeks=1)
```

**Failure Impact:** A weekly medication (e.g., flea treatment) that advances by the wrong interval could resurface in 1 day (over-treatment) or never resurface (under-treatment). Both outcomes are medically harmful.

---

### TC-STATE-04: Completed daily task is excluded from today's schedule

**Test Objective:** Verify that after `complete_task()` advances `due_date` to tomorrow, `get_all_tasks()` no longer returns it for today's schedule.

**Setup Data:**
```python
today = date.today()
task  = Task(name="Feed", duration=10, priority=5, frequency='daily', due_date=today)
pet   = Pet(name="Buddy", species="Dog", age=3, tasks=[task])
owner = Owner(name="Alex", available_time_mins=60, pets=[pet])

pet.complete_task(task)
remaining = owner.get_all_tasks()
```

**Success Criteria:**
```python
task not in remaining   # due_date is tomorrow, filtered out by get_all_tasks()
```

**Failure Impact:** A task that was just completed reappears in the same session's schedule, creating confusing duplicate entries and misleading the owner about what still needs to be done.

---

## Suite 4: Constraint Exhaustion

**Target method:** `Scheduler.generate_schedule()`

---

### TC-SCHED-01: Zero available time — all tasks skipped

**Test Objective:** Verify the early-exit guard: when `available_time_mins == 0`, the scheduler skips all tasks and returns the appropriate `ScheduleResult`.

**Setup Data:**
```python
task  = Task(name="Walk", duration=30, priority=5)
pet   = Pet(name="Buddy", species="Dog", age=3, tasks=[task])
owner = Owner(name="Alex", available_time_mins=0, pets=[pet])

result = Scheduler(owner).generate_schedule()
```

**Success Criteria:**
```python
result.scheduled_tasks == []
result.total_time_used == 0
result.skipped_tasks == [task]
"No time available" in result.reasoning
```

**Failure Impact:** If the guard is missing, the scheduler enters Phase 1, schedules the required task anyway, and sets `total_time_used = 30` — contradicting `available_time_mins = 0`. The owner's reported schedule is invalid.

---

### TC-SCHED-02: Required tasks exceed budget — Time Deficit flagged

**Test Objective:** Verify that required tasks are always scheduled even when their total duration exceeds `available_time_mins`, and that the reasoning string contains the "Time Deficit" warning.

**Setup Data:**
```python
med   = Task(name="Medication", duration=15, priority=5, is_required=True)
owner = Owner(name="Alex", available_time_mins=10, pets=[
    Pet(name="Buddy", species="Dog", age=3, tasks=[med])
])

result = Scheduler(owner).generate_schedule()
```

**Success Criteria:**
```python
med in result.scheduled_tasks         # required task is always included
result.total_time_used == 15          # actual time used, not capped
"Time Deficit" in result.reasoning    # user is informed
```

**Failure Impact:** If required tasks are capped at the time budget, a pet's medication is silently skipped with no indication to the owner. This is the core safety guarantee of the scheduler.

---

### TC-SCHED-03: Available time exactly equals required task duration

**Test Objective:** Verify the boundary where `required_time == available_time_mins`: no deficit is reported, and the remaining time for optional tasks is exactly zero.

**Setup Data:**
```python
med      = Task(name="Medication", duration=30, priority=5, is_required=True)
optional = Task(name="Play",       duration=10, priority=3)
owner    = Owner(name="Alex", available_time_mins=30, pets=[
    Pet(name="Buddy", species="Dog", age=3, tasks=[med, optional])
])

result = Scheduler(owner).generate_schedule()
```

**Success Criteria:**
```python
med in result.scheduled_tasks
optional in result.skipped_tasks    # no remaining time for optional tasks
result.total_time_used == 30
"Time Deficit" not in result.reasoning
```

**Failure Impact:** An off-by-one error here could either incorrectly schedule the optional task (exceeding the budget) or incorrectly flag a deficit when the schedule is perfectly balanced.

---

### TC-SCHED-04: Optional tasks are greedily filled by priority

**Test Objective:** Verify that when multiple optional tasks compete for limited remaining time, higher-priority tasks are selected first.

**Setup Data:**
```python
low_pri  = Task(name="Groom", duration=10, priority=2)
high_pri = Task(name="Play",  duration=10, priority=4)
# Only 10 minutes remain after required tasks
owner = Owner(name="Alex", available_time_mins=10, pets=[
    Pet(name="Buddy", species="Dog", age=3, tasks=[low_pri, high_pri])
])

result = Scheduler(owner).generate_schedule()
```

**Success Criteria:**
```python
high_pri in result.scheduled_tasks   # priority=4 is scheduled
low_pri in result.skipped_tasks      # priority=2 is skipped
```

**Failure Impact:** A lower-priority grooming session fills the slot before a higher-priority play/enrichment session. The owner unknowingly delivers a suboptimal care experience.

---

### TC-SCHED-05: Negative `available_time_mins` raises `ValueError`

**Test Objective:** Verify that `Owner.__post_init__` rejects negative time budgets at construction time, before the scheduler is ever called.

**Setup Data:**
```python
import pytest

with pytest.raises(ValueError, match="cannot be negative"):
    Owner(name="Alex", available_time_mins=-1, pets=[])
```

**Success Criteria:** A `ValueError` is raised with a message referencing "cannot be negative".

**Failure Impact:** If negative time is allowed to reach the scheduler, `remaining` would go negative immediately, causing all optional tasks to be skipped (if `duration <= negative` is always False) — or producing incorrect `total_time_used` values with no error surfaced to the user.

---

## Suite 5: Cross-Cutting — `get_all_tasks()` Date Filtering

**Target method:** `Owner.get_all_tasks()`

---

### TC-FILTER-01: Future-dated tasks are excluded

**Test Objective:** Verify that tasks with `due_date > today` do not appear in `get_all_tasks()`, so they cannot enter the scheduler.

**Setup Data:**
```python
from datetime import date, timedelta
future = date.today() + timedelta(days=1)

task  = Task(name="Future Med", duration=10, priority=5, due_date=future)
owner = Owner(name="Alex", available_time_mins=60, pets=[
    Pet(name="Buddy", species="Dog", age=3, tasks=[task])
])

result = owner.get_all_tasks()
```

**Success Criteria:**
```python
task not in result
```

**Failure Impact:** Future tasks that appear in today's schedule inflate the task list and create a false sense of urgency. Worse, if the task is `is_required`, it could trigger a spurious Time Deficit warning.

---

### TC-FILTER-02: Overdue tasks (past `due_date`) are included

**Test Objective:** Verify that tasks with `due_date < today` (overdue) are included in `get_all_tasks()`, since `due_date <= today` is the filter condition.

**Setup Data:**
```python
yesterday = date.today() - timedelta(days=1)
task  = Task(name="Overdue Bath", duration=20, priority=3, due_date=yesterday)
owner = Owner(name="Alex", available_time_mins=60, pets=[
    Pet(name="Buddy", species="Dog", age=3, tasks=[task])
])

result = owner.get_all_tasks()
```

**Success Criteria:**
```python
task in result
```

**Failure Impact:** Overdue tasks (e.g., a missed vaccination appointment) silently disappear from the schedule. The owner has no indication that a critical task was skipped on a prior day.

---

## Known Limitations Summary

| ID | Limitation | Location | Real-World Risk |
|---|---|---|---|
| L-01 | Midnight Rollover Blind Spot | `detect_conflicts()` — lexicographic string sort | Cross-midnight task overlaps are never flagged |
| L-02 | No partial-task scheduling | `generate_schedule()` Phase 2 | A 31-minute optional task is skipped even if 30 minutes remain |
| L-03 | Required tasks not sorted by priority among themselves | `generate_schedule()` Phase 1 | A Priority-3 required task consumes time before a Priority-5 required task |
| L-04 | `complete_task()` does not validate task ownership | `Pet.complete_task()` | Completing a task on the wrong pet silently mutates state |

---

## Existing Test Coverage Baseline

```
tests/test_pawpal.py
├── test_task_toggle()       — covers Task.toggle_complete()
└── test_pet_task_addition() — covers basic list append
```

**Current coverage:** ~5% of scheduler logic paths
**After Phase 5 implementation:** Target 100% coverage of all 14 test cases above

---

*End of Test Plan — Phase 5, Step 1*
