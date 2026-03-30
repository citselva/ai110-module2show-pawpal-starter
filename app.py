import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

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

# Seed the widget keys from the stored object — only on first run.
# After that, Streamlit keeps them in sync via the key= parameter.
if "owner_name" not in st.session_state:
    st.session_state.owner_name = st.session_state.owner_data.name

if "pet_name" not in st.session_state:
    first_pet = st.session_state.owner_data.pets[0] if st.session_state.owner_data.pets else None
    st.session_state.pet_name = first_pet.name if first_pet else ""

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# ---------------------------------------------------------------------------

st.subheader("Quick Demo Inputs")

# key= links each widget directly to st.session_state — changes persist across
# re-runs automatically.  No value= needed once the key is seeded above.
owner_name = st.text_input("Owner name", key="owner_name")
pet_name = st.text_input("Pet name", key="pet_name")
species = st.selectbox("Species", ["dog", "cat", "other"])

# Keep the Owner object in sync with whatever the user typed.
st.session_state.owner_data.name = owner_name
if st.session_state.owner_data.pets:
    st.session_state.owner_data.pets[0].name = pet_name
    st.session_state.owner_data.pets[0].species = species

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    st.warning(
        "Not implemented yet. Next step: create your scheduling logic (classes/functions) and call it here."
    )
    st.markdown(
        """
Suggested approach:
1. Design your UML (draft).
2. Create class stubs (no logic).
3. Implement scheduling behavior.
4. Connect your scheduler here and display results.
"""
    )
