# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial design identifies four distinct classes to separate data management from scheduling logic, ensuring the system follows the Single Responsibility Principle:

1.  **User**: Acts as the "Owner" profile, holding the global constraints such as `available_time_mins` (the daily time "budget").
2.  **Pet**: Stores animal-specific metadata (species, age, requirements) and serves as the link between the owner and the care activities.
3.  **Task**: A granular data object representing a single unit of work (e.g., "Meds," "Walk"). It holds attributes for `duration_mins`, `priority_level` (1-5), and `category`.
4.  **CarePlanner**: The "Engine" of the application. It processes the `User` budget and the `Task` list to calculate an optimized schedule and generate natural language reasoning for the owner.

**The system focuses on three core user actions:**
* **Profile Setup:** Entering pet details and defining the owner's total time "budget" for the day.
* **Task Management:** Adding and editing care tasks with specific durations and priority rankings.
* **Smart Scheduling:** Generating a constrained daily plan that fits the time budget and provides an explanation for the task selection.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
