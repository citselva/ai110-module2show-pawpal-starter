import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pawpal_system import Task, Pet, Owner, Scheduler

WIDTH = 44


def stars(priority: int) -> str:
    return "\u2605" * priority + "\u2606" * (5 - priority)


def time_bar(used: int, total: int, width: int = 20) -> str:
    if total == 0:
        filled = 0
    else:
        filled = round(used / total * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def print_schedule(owner: "Owner", result) -> None:
    scheduled_set = set(id(t) for t in result.scheduled_tasks)

    print(f"\u2554{'=' * (WIDTH - 2)}\u2557")
    title = f"  Today's Schedule \u2014 {owner.name}"
    print(f"\u2551{title:<{WIDTH - 2}}\u2551")
    print(f"\u255a{'=' * (WIDTH - 2)}\u255d")

    for pet in owner.pets:
        print(f"\n  {pet.name} ({pet.species})")
        for task in pet.tasks:
            scheduled = id(task) in scheduled_set
            tag = "  [REQUIRED]" if task.is_required else ("  SKIPPED" if not scheduled else "")
            print(f"    {task.name:<22} {task.duration:>3} min  {stars(task.priority)}{tag}")

    required_count = sum(1 for t in result.scheduled_tasks if t.is_required)
    available = owner.available_time_mins

    print(f"\n  {'-' * (WIDTH - 4)}")
    bar = time_bar(result.total_time_used, available)
    print(f"  Time  [{bar}]  {result.total_time_used} / {available} min")
    print(
        f"  Tasks  {len(result.scheduled_tasks)} scheduled"
        f"  \u00b7  {len(result.skipped_tasks)} skipped"
        f"  \u00b7  {required_count} required"
    )


# --- Setup ---
buddy = Pet(name="Buddy", species="Dog", age=3, tasks=[
    Task(name="Morning Walk",     duration=30, priority=5, is_required=True),
    Task(name="Teeth Brushing",   duration=10, priority=3),
    Task(name="Trick Training",   duration=20, priority=2),
])

whiskers = Pet(name="Whiskers", species="Cat", age=5, tasks=[
    Task(name="Litter Box Clean", duration=10, priority=5, is_required=True),
    Task(name="Brushing",         duration=15, priority=4),
    Task(name="Laser Toy Play",   duration=10, priority=1),
])

# Three tasks added in deliberately random duration order: 60, 10, 30
# All share priority=3 so the sort must resolve ties by duration ASC.
goldie = Pet(name="Goldie", species="Fish", age=1, tasks=[
    Task(name="Tank Deep Clean",  duration=60, priority=3),
    Task(name="Feed Flakes",      duration=10, priority=3),
    Task(name="Water Test",       duration=30, priority=3),
])

owner = Owner(name="Alex", available_time_mins=75, pets=[buddy, whiskers, goldie])

# --- Schedule ---
scheduler = Scheduler(owner)
result = scheduler.generate_schedule()
print_schedule(owner, result)

# --- Sort verification ---
print(f"\n{'=' * WIDTH}")
print("  sort_tasks() — priority DESC, duration ASC")
print(f"{'=' * WIDTH}")
sorted_tasks = scheduler.sort_tasks()
for t in sorted_tasks:
    status = "done" if t.is_completed else "todo"
    print(f"  priority={t.priority}  {t.duration:>3} min  [{status}]  {t.name}")

# --- Filter verification ---
print(f"\n{'=' * WIDTH}")
print("  filter_tasks(is_completed=False) — incomplete tasks only")
print(f"{'=' * WIDTH}")
incomplete = owner.filter_tasks(is_completed=False)
for t in incomplete:
    print(f"  {t.name:<24} {t.duration:>3} min  priority={t.priority}")

# --- Conflict detection test ---
print(f"\n{'=' * WIDTH}")
print("  detect_conflicts() — overlapping start times")
print(f"{'=' * WIDTH}")
conflict_pet = Pet(name="Rex", species="Dog", age=2, tasks=[
    Task(name="Morning Walk",  duration=30, priority=5, is_required=True,  start_time="09:00"),
    Task(name="Feeding",       duration=20, priority=4, is_required=False, start_time="09:15"),
])
conflict_owner = Owner(name="Sam", available_time_mins=60, pets=[conflict_pet])
conflict_scheduler = Scheduler(conflict_owner)
conflict_result = conflict_scheduler.generate_schedule()
print_schedule(conflict_owner, conflict_result)
print(f"\n  Reasoning: {conflict_result.reasoning}")
