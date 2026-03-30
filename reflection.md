# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial design focuses on three core user actions to ensure the app is functional and user-centric:
1. **Profile Setup:** Allowing the user to input pet details and define the owner's specific time "budget" for the day.
2. **Task Management:** Enabling the addition and editing of care tasks with specific durations and priority rankings (1-5).
3. **Smart Scheduling:** Generating a daily plan that fits within the time budget and provides a natural language explanation for why certain tasks were prioritized.

To support these actions, I have structured the system into four decoupled classes using Python `dataclasses`:
* **User**: Stores the owner's profile and the primary time constraint (`available_time_mins`).
* **Pet**: Acts as a container for animal-specific data and manages the collection of `Task` objects.
* **Task**: A lightweight object representing a single activity (e.g., "Meds," "Walk"), carrying the data needed for the scheduling algorithm.
* **Scheduler**: The "Engine" class. It references the `User` and `Pet` to perform the scheduling logic and store the generated `reasoning` for the user.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
After an AI architectural review of my initial skeleton, I made the below changes to improve the system's robustness:
1. **Introduction of `ScheduleResult`**: I shifted from returning a bare `List[Task]` to a structured `ScheduleResult` dataclass. This ensures the UI receives the "reasoning," "total time," and "skipped tasks" in a single transaction, reducing logic duplication in the frontend.
2. **Hard vs. Soft Constraints**: I added an `is_required` boolean to the `Task` class. This allows the scheduler to prioritize essential care (like medication) regardless of the user-assigned priority of optional tasks (like grooming).
3. **Validation Logic**: I implemented a `__post_init__` check in the `User` class to prevent negative time budgets and added a guard clause in the `Scheduler` to handle "zero-time" days gracefully.
4. **Multi-Pet Preparation**: I refined the `Scheduler` to pull tasks directly from the `Pet` object rather than passing an external list, which prevents data detachment and prepares the system for multi-pet scaling.

**Refactored CarePlanner to Scheduler to better align the codebase with the functional requirements and improve naming clarity within the logic layer.**

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

* **Constraints Considered:** My scheduler evaluates three distinct layers of constraints:
    * **Hard Temporal Constraint:** The `available_time_mins` provided by the `Owner`, which acts as the total daily budget.
    * **Categorical Constraint:** The `is_required` flag on the `Task` object, which separates "essential care" from "discretionary activities."
    * **Soft Priority Constraint:** A 1–5 `priority` scale used to rank optional tasks once essential needs are met.
* **Decision Matrix:** I decided that **health and safety (Required Tasks)** must always be the top priority. In my logic, a "Priority 3" medication is inherently more important than a "Priority 5" play session. This ensures the app acts as a responsible care steward rather than a simple task-sorter.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

* **The Tradeoff:** I implemented a **"Mandatory-First Greedy"** algorithm. The scheduler allocates time to *all* required tasks first, even if their cumulative duration exceeds the user's available time. Only after these are secured does the system "fill" the remaining minutes with optional tasks sorted by priority.
* **Reasonability:** This tradeoff is reasonable because pet care requires stewardship over convenience. If a pet needs 15 minutes of medical care but the owner only has 10 minutes, the app should not simply skip the medication to fit the window. By including the task and flagging a **"Time Deficit,"** the app forces the user to acknowledge an unmet essential need, prioritizing the pet's well-being over a "perfect" schedule.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I utilized a dual-model strategy to maintain high architectural standards, separating the "Strategic Design" from the "Technical Implementation":

* **Prompt Engineering & Logic Brainstorming (Gemini):** I used Gemini as a lead consultant to architect the logic. Before generating code, I used Gemini to map out the **Sweep-Line algorithm** and the **Shortest-Job-First (SJF)** sorting tie-breaker. Gemini’s primary role was helping me refine my engineering requirements into "Master Prompts" that would ensure the coding model didn't take shortcuts.
* **Code Generation & Implementation (Claude):** I used Claude for the technical heavy lifting. Using the prompts refined in Gemini, I had Claude generate the core Python classes, the 23-case unit test suite, the Streamlit UI components, and the Mermaid.js UML diagrams. Claude was highly effective at maintaining the "As-Built" context once the initial architectural instructions were clear.

**Most Helpful Prompts:**
* **The "Structural Inference" Prompt:** "Analyze my final `pawpal_system.py` and generate a Mermaid.js diagram that reflects the *actual* methods and relationships implemented, ensuring the documentation matches the production code."
* **The "Boundary Condition" Prompt:** "Generate a pytest suite that specifically targets the edge cases of the conflict detector, such as tasks that share an exact start/end boundary."

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**The "Efficiency vs. Simplicity" Moment:**
While implementing the `detect_conflicts()` method, the AI initially suggested a simple nested loop ($O(n^2)$) to compare every task against every other task for potential overlaps.

* **The Modification:** I rejected the $O(n^2)$ approach as it lacked scalability. I instructed the AI to implement a **Sweep-Line algorithm** instead. This required forcing a chronological sort first ($O(n \log n)$), followed by a single linear pass ($O(n)$) to check for overlaps. This kept the system performant even as the number of tasks increased.
* **Evaluation & Verification:** * **Manual Code Review:** I inspected the resulting logic to ensure the `end_time` was being compared correctly against the subsequent `start_time` without unnecessary iterations.
    * **Automated Testing:** I verified the fix by running a test case with tasks provided in reverse chronological order to ensure the internal sort was functioning correctly before the sweep.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I implemented a structured suite of **23 unit tests** using `pytest` to verify the core scheduling engine and state transitions:

* **Two-Phase Scheduler Logic:** I tested that the `generate_schedule()` method unconditionally includes all `is_required` tasks (Phase 1) before greedily filling the remaining budget with optional tasks (Phase 2).
* **Composite Sorting (SJF):** I verified the `(-priority, duration)` sort key to ensure that among tasks of equal priority, shorter tasks were prioritized to maximize total task density.
* **Interval Conflict Detection:** I tested the sweep-line algorithm against three boundary conditions: genuine overlaps, tasks sharing an exact end/start boundary (which should not flag), and tasks with no start time.
* **Recurrence State Transitions:** I verified that `complete_task()` correctly advanced the `due_date` by the appropriate `timedelta` (Daily/Weekly) while keeping the task active, and properly retired "One-Off" tasks.
* **Temporal Filtering:** I confirmed that `get_all_tasks()` correctly includes overdue tasks but excludes future-dated or completed one-off tasks.

**Why these tests were important:**
In a scheduling application, "silent failures" are the biggest risk. Without these tests, a bug in the recurrence logic could cause a critical medication task to vanish from tomorrow's schedule, or a conflict in the sweep-line sort could lead to an unachievable daily plan.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**Confidence Level: High (95%)**
The current test suite covers all primary success paths and the most common failure modes (time deficits and scheduling overlaps). The 23/23 passing status provides high confidence that the mathematical "contract" of the scheduler is intact.

**Future Edge Cases to Test:**
If I had more time, I would expand the suite to cover:
1. **Midnight Rollover Complexity:** While `datetime` arithmetic handles basic rollover, I would test a task that starts at 23:30 and ends at 00:30 to ensure the UI and conflict detector handle the date-boundary transition gracefully.
2. **Negative Duration/Time Inputs:** Implementing "Fuzz Testing" on the user input fields to ensure the scheduler doesn't crash if a user enters a 0-minute or negative-minute duration.
3. **Timezone Transitions:** Testing behavior during Daylight Savings Time (DST) shifts to ensure recurring tasks don't unintentionally shift by an hour.
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am most satisfied with the **Algorithmic Rigor** of the scheduling engine. Specifically, implementing a **Two-Phase Scheduler** combined with a **Sweep-Line conflict detector** elevated the project from a simple "To-Do list" to a legitimate optimization tool. I am particularly proud of the **(-priority, duration) composite sort key**; it’s a subtle architectural detail that significantly improves the user experience by maximizing the number of tasks completed within a tight time budget. Seeing all 23 test cases pass in under 0.2 seconds validated that the system is both robust and highly performant.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
If I had another iteration, I would focus on **Data Persistence and Multi-Pet Analytics**:
* **Persistence:** Currently, the app relies on Streamlit’s `session_state`, meaning data is lost on a full refresh. I would implement a lightweight SQL (SQLite) or JSON-based storage layer to save owner and pet profiles across sessions.
* **Smart Duration Inference:** I would redesign the `Task` class to include "Actual vs. Estimated" duration tracking. This would allow the system to eventually use historical data to suggest more accurate time blocks for specific pets (e.g., "Max usually takes 45 minutes for a walk, not 30").
* **Visual Timeline:** While the table view is professional, a Gantt-style timeline visualization would make scheduling conflicts even more intuitive for the end-user.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
The most important thing I learned is that **AI is a powerful "force multiplier," but the Human remains the "Strategic Anchor."** Working with Gemini and Claude showed me that while AI can generate code and tests at incredible speeds, it requires a human architect to define the constraints, choose the right algorithms (like opting for $O(n \log n)$ over $O(n^2)$), and verify the "edge-case" boundaries. Being a "Lead Architect" in an AI-driven world isn't about writing every line of code; it's about **curating the logic** and ensuring the final system matches the intended design and quality standards.

## 6. Optional Extensions & Advanced Capabilities

While several features were listed as "Optional Extensions," I integrated them into the core architecture of PawPal+ to ensure a production-ready scheduling engine.

### **a. Challenge Mapping**

| Challenge | Implementation Status | Technical Approach |
|:---|:---|:---|
| **1. Advanced Algorithmic Capability** | ✅ Completed | Implemented a **Two-Phase Scheduler** that guarantees required tasks while optimizing optional ones. |
| **2. Data Persistence** | ✅ Completed | Developed a custom **JSON Serialization** layer for `Task`, `Pet`, and `Owner` objects (see below). |
| **3. Priority-Based Scheduling** | ✅ Completed | Engineered a **Composite Sort Key** `(-priority, duration)` to handle multi-tiered task density optimization. |
| **4. Professional UI & Formatting** | ✅ Completed | Integrated real-time **Conflict Warnings** and **Time Deficit Alerts** using Streamlit's status containers. |
| **5. Multi-Model Comparison** | ✅ Completed | Executed a **Dual-Model Pipeline** using Gemini for strategy/prompting and Claude for technical implementation. |

---

### **b. Deep Dive: Data Persistence (Challenge 2)**

I used **Claude** to architect a serialization layer within `pawpal_system.py`. The primary hurdle was that Python's native `json` library does not support `datetime` or `timedelta` objects.

* **The Strategy:** I implemented custom `to_dict()` and `from_dict()` methods. These methods handle the conversion of temporal objects into ISO strings and back into Python objects during the load/save cycle.
* **The Integration:** I updated `app.py` to automatically check for `pawpal_data.json` on startup. If found, the `Owner` object is rehydrated, ensuring that pet profiles and task histories persist across browser refreshes.
* **The "Zero-Dependency" Decision:** While the AI suggested using `marshmallow`, I opted for a manual mapping to keep the codebase lightweight and maintainable without adding external package overhead.
