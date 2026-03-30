from datetime import date

import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Vault: initialize persistent state exactly once per browser session.
# st.session_state survives every top-to-bottom re-run; this block is the
# "door" — it only executes when the key is absent (i.e., first load).
# ---------------------------------------------------------------------------
if "owner_data" not in st.session_state:
    default_pet = Pet(name="Mochi", species="dog", age=3)
    default_owner = Owner(name="Jordan", available_time_mins=60)
    default_owner.pets.append(default_pet)
    st.session_state.owner_data = default_owner

# Seed widget keys from the stored object — only on first run.
if "owner_name" not in st.session_state:
    st.session_state.owner_name = st.session_state.owner_data.name

if "available_time" not in st.session_state:
    st.session_state.available_time = st.session_state.owner_data.available_time_mins

# ---------------------------------------------------------------------------

st.subheader("Owner Settings")

owner_name = st.text_input("Owner name", key="owner_name")
available_time = st.number_input(
    "Available time (minutes)", min_value=0, max_value=480, key="available_time"
)

# Keep the Owner object in sync with whatever the user typed.
# Pets and their tasks are stored on the Owner object directly — NOT in a
# separate session_state list — so changing the owner name never wipes them.
st.session_state.owner_data.name = owner_name
st.session_state.owner_data.available_time_mins = int(available_time)

st.divider()

# ---------------------------------------------------------------------------
# Add Pet
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        new_pet_name = st.text_input("Pet name")
    with col2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        new_pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
    submitted_pet = st.form_submit_button("Add Pet")

if submitted_pet:
    if new_pet_name.strip():
        new_pet = Pet(
            name=new_pet_name.strip(),
            species=new_pet_species,
            age=int(new_pet_age),
        )
        st.session_state.owner_data.pets.append(new_pet)
        st.success(f"Pet '{new_pet.name}' added!")
    else:
        st.warning("Please enter a pet name.")

st.divider()

# ---------------------------------------------------------------------------
# Add Task
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}

if not st.session_state.owner_data.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names = [p.name for p in st.session_state.owner_data.pets]
        selected_pet_name = st.selectbox("Assign to pet", pet_names)

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col3:
            priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        col4, col5 = st.columns(2)
        with col4:
            frequency = st.selectbox("Frequency", ["one-off", "daily", "weekly"])
        with col5:
            is_required = st.checkbox("Mark as required")
        submitted_task = st.form_submit_button("Add Task")

    if submitted_task:
        if task_title.strip():
            new_task = Task(
                name=task_title.strip(),
                duration=int(duration),
                priority=PRIORITY_MAP[priority_label],
                is_required=is_required,
                frequency=frequency,
            )
            target_pet = next(
                p for p in st.session_state.owner_data.pets if p.name == selected_pet_name
            )
            target_pet.tasks.append(new_task)
            st.success(f"Task '{new_task.name}' added to {target_pet.name}.")
        else:
            st.warning("Please enter a task title.")

st.divider()

# ---------------------------------------------------------------------------
# Current Summary — pulled directly from the Owner/Pet objects
# ---------------------------------------------------------------------------
st.subheader("Current Summary")

owner = st.session_state.owner_data
st.write(f"**Owner:** {owner.name} | **Available time:** {owner.available_time_mins} min")

if not owner.pets:
    st.info("No pets yet. Add one above.")
else:
    today = date.today()
    for pet in owner.pets:
        due_tasks = [t for t in pet.tasks if t.due_date <= today]
        label = f"{pet.get_summary()} — {len(due_tasks)} due today"
        with st.expander(label, expanded=True):
            if not due_tasks:
                st.caption("No tasks due today or earlier for this pet.")
            else:
                st.table(
                    [
                        {
                            "Task": t.name,
                            "Duration (min)": t.duration,
                            "Priority (1-5)": t.priority,
                            "Frequency": t.frequency,
                            "Due": str(t.due_date),
                            "Required": t.is_required,
                            "Done": t.is_completed,
                        }
                        for t in due_tasks
                    ]
                )

st.divider()

# ---------------------------------------------------------------------------
# Generate Schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")
st.caption("Runs the tiered scheduler across all pets and tasks for the owner's time budget.")

if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet with at least one task first.")
    else:
        scheduler = Scheduler(owner)
        result = scheduler.generate_schedule()

        st.success(f"Schedule complete — {result.total_time_used} min used of {owner.available_time_mins} min available.")
        st.markdown(f"**Reasoning:** {result.reasoning}")

        if result.scheduled_tasks:
            st.markdown("**Scheduled tasks:**")
            st.table(
                [
                    {
                        "Task": t.name,
                        "Duration (min)": t.duration,
                        "Priority (1-5)": t.priority,
                        "Required": t.is_required,
                    }
                    for t in result.scheduled_tasks
                ]
            )

        if result.skipped_tasks:
            st.markdown("**Skipped tasks (not enough time):**")
            st.table(
                [
                    {
                        "Task": t.name,
                        "Duration (min)": t.duration,
                        "Priority (1-5)": t.priority,
                    }
                    for t in result.skipped_tasks
                ]
            )
