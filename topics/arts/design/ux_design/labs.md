# Studio Practice Labs: User Experience UX Design and Wireframing

## Objective & Studio Setup

This guide takes you through the complete skill arc of UX design and wireframing—from observation and user research to validated interaction design. You will learn to see the structural logic beneath interface surfaces, to build mental models of user behavior, to organize information hierarchies, and to test your assumptions against real user needs.

Unlike visual design that prioritizes aesthetic form, UX design is fundamentally about function, context, and human cognition. Your task is to design systems that feel intuitive because they align with how people actually think and move through digital space. This requires both rigorous observation and iterative testing.

By the end of these labs, you will have produced three complete artifacts: a research synthesis document with user personas, a wireframe system for a multi-screen product, and evidence of validation through usability testing feedback. The practice is cumulative—each exercise builds on the previous one.

### Studio Environment & Tools

You will work primarily in a digital design tool. **Figma** (collaborative, browser-based, free tier available) or **Penpot** (open-source alternative) are the authentic environments for wireframe design in professional practice. Both provide the grid systems, component libraries, and annotation tools necessary for UX work. If neither is available, use **Inkscape** (vector) or **Krita** (raster) as fallbacks, though you will sacrifice some collaborative and prototyping features.

You will also need **paper and pencil** for initial exploration and low-fidelity sketching. This is not optional. Hand sketching forces you to think faster than your tools allow and prevents premature polishing that obscures structural problems.

Gather reference materials: collect screenshots of 5–8 existing apps or websites in the category you will design for. Use the **color picker** tool native to your OS (macOS: Cmd+Shift+3 and crop; Windows: Win+Shift+S; Linux: gnome-screenshot) or your design tool's built-in eyedropper to analyze existing UI color and contrast patterns. Keep a **typography reference document** with the type families, sizes, and weights used in your references. Create a **critique rubric** document (Google Docs, Markdown file, or printed checklist) that you will return to in Exercise 3.

### Assumed Prior Knowledge

You have basic familiarity with your chosen design tool (opening files, drawing shapes, creating text, organizing layers). You understand the vocabulary of visual hierarchy (size, weight, color, position). You have read or are concurrent with the four lesson modules on research, principles, information architecture, and usability testing.

---

## Exercise 1: Observation & Fundamentals Drill – User Research and Mental Model Mapping

### Objective

The first drill teaches you to think like a user researcher. You will observe real people, extract their mental models, and synthesize that observation into actionable design constraints. This is where wireframing begins—not with an interface, but with understanding the problem the interface must solve.

### Part A: Contextual Observation & Interview

Choose a task-specific context and a person who performs that task regularly. Examples: a parent booking a pediatrician appointment, a dancer scheduling rehearsals, a student selecting courses for the next semester, a photographer organizing a portfolio. The task should be specific enough that it has measurable friction points—moments where the person hesitates, backtracks, or expresses frustration.

Arrange a 30-minute observation session. This is best done in person, but remote observation via screen-sharing works. Ask the person to show you how they currently accomplish this task on their phone or computer. Do not lead them. Do not say "now go to X." Instead, ask open-ended questions: "Walk me through what you need to do to accomplish X. Talk me through what you're thinking." Sit quietly and listen. Take notes in a document or notebook. Capture not just what they do, but what they say about why they do it.

Record the following during observation:

- **Entry point:** How did the person arrive at this interface? Email link? App icon? Search? This reveals assumptions about discoverability.
- **Goal clarity:** Did the person immediately know what to do, or did they search for it?
- **Friction points:** Where did they pause, hover, re-read text, or use the back button?
- **Workarounds:** Did they use an alternative path or external tool (notes app, email, phone call) to complete part of the task?
- **Language:** What words did they use to describe actions or sections? ("Get a spot," "Find open times," "Check if they take insurance"?) These are clues to your users' mental model, not your designer's mental model.
- **Emotion cues:** Sighs, clicks of frustration, or comments like "I hate this part" mark pain points.

Write a one-paragraph **observation summary** immediately after the session. Example:

> Sarah needs to book a dental appointment. She opened the practice website (found via Google search), looked for a "Book Appointment" button, and found it in the top-right corner. However, she then had to scroll down to find the "New Patient" vs. "Existing Patient" branching—this was not obvious from the top-level menu. Once she selected "New Patient," she was asked to fill a form with questions about insurance coverage, but she didn't have her insurance card present. She switched to her email to retrieve the information, then returned to the form. The experience felt fragmented. Her language: "I shouldn't have to leave the site to find this information."

### Part B: User Persona Synthesis

Now translate your observations into a user persona—a composite model of your user's goals, constraints, and mental patterns. This is not a demographic profile; it is a cognitive profile.

Create a document (Google Docs, Markdown file, or PDF) with the following structure:

**Persona Name:** Use a realistic first name and age range. Example: "Sarah, 38, busy parent"

**Core Goal (in their words):** Restate their primary task goal using the language they used. Not "book an appointment," but "schedule time with a provider who takes my insurance before work hours."

**Current Pain Points (ranked by severity):**
1. What is the most frustrating aspect of the current process? Example: "Must leave the site to retrieve insurance details."
2. What is the second most frustrating? Example: "Unclear distinction between new and existing patient pathways."
3. What is a minor annoyance? Example: "Provider photos are too small to recognize which doctor I saw last time."

**Workarounds They Use:** What do they do to work around the system's gaps? Example: "I keep my insurance card photo in my photo roll so I don't have to dig through my wallet."

**Success Metric (from their perspective):** How would they know the experience is better? Example: "I can enter my appointment from notification to confirmed in under 3 minutes, without leaving the app."

**Mental Model Sketch:** On a single page, hand-draw a simple flow diagram showing how they currently think about the process. This need not be a formal flowchart. It can be boxes and arrows, or a hand-written series of steps. The goal is to externalize their internal logic, not to create a perfect diagram. Example:

```text
Need appointment
   ↓
Find practice contact info (Google)
   ↓
Choose new vs. existing patient
   ↓
Fill form (need insurance info)
   ↓
Check availability
   ↓
Confirm and add to calendar
```

If you are observing multiple users (3–5 is ideal), create a persona for each distinct mental model. If patterns emerge—for instance, all users have the same pain point about insurance information—note this as a **validation point** that this constraint is real and not idiosyncratic.

### Part C: Design Constraints from Research

Before you sketch a single wireframe, you must extract the **invariant constraints** from your research. These are non-negotiable rules derived from user observation.

Create a bulleted list of 4–6 design constraints. These must be testable and specific:

- **Information availability:** "Insurance verification information must be retrievable or pre-filled before the user is asked to enter it."
- **Mental model alignment:** "The first branching decision must reflect the user's own categorization (new vs. existing), not the organization's backend distinction."
- **Friction reduction:** "The critical path from task initiation to confirmation must be completable in a single session without context switching to external tools."
- **Language consistency:** "Use the user's language ('appointment,' 'available slots') not system language ('session slot,' 'booking node')."
- **Workaround elimination:** "Provide a photo reference for providers large enough to match the user's existing visual memory without opening a separate detail screen."
- **Success validation:** "On completion, the user receives a confirmation they can immediately add to their calendar app (calendar link or export option)."

Write these constraints as imperative statements that your wireframe must satisfy. These become your critique checklist in Exercise 3.

### Deliverables for Exercise 1

1. **Observation notes** (1–2 pages): Raw transcript or summary of the user session, including friction points and direct quotes.
2. **User persona** (1 page): Name, goal, pain points, workarounds, success metric, and mental model sketch.
3. **Design constraints** (1 page): 4–6 specific, testable rules derived from research.

**Time allocation:** 2–3 hours total (30 min observation, 30 min synthesis, 1–2 hours writing and sketching).

---

## Exercise 2: Technique Study, Step by Step – Information Architecture and Wireframe Structure

### Objective

With user research as your foundation, you now build the structural wireframe. This exercise teaches you to organize information hierarchically, design navigation that reflects user mental models, and create a system of reusable interface components. You will work at medium fidelity—enough detail to be testable, not so much that you spend time on polish.

### Part A: Site Map and Navigation Hierarchy

Before opening your design tool, map the entire information architecture on paper. This is your structural skeleton.

On a single large sheet (or multiple taped sheets), draw a tree diagram showing every screen the user will need to reach. Begin with a root node labeled "Entry Point" and branch downward. For the appointment-booking example, your map might look like this:

```text
                        Entry Point (App Home)
                               |
                    ___________|___________
                   |                       |
            [New Patient]          [Existing Patient]
                   |                       |
        ___________|___________    ________|________
       |                       |   |                |
    [Form]              [Browse]  [Quick]     [Rebook]
       |                  |         |            |
    [Review]           [Detail]  [Confirm]  [Confirm]
       |                  |         |            |
  [Confirm]           [Confirm] [Calendar] [Calendar]
       |                  |
  [Calendar]         [Calendar]
```

For each node, write one sentence describing what the user accomplishes on that screen. Example:
- **New Patient:** User selects whether this is their first visit to the practice.
- **Form:** User enters name, contact, reason for visit, insurance information.
- **Review:** User confirms all entered information before submission.

Now identify **decision points** where the user branches into different paths. These are critical: they must be visually and verbally clear. The key question for each decision point is: "Will the user understand why this branching exists and confidently choose the correct path?" Compare against your design constraints from Exercise 1. In the example above, the new vs. existing patient split is a decision point that must be crystal clear and impossible to skip.

Identify **linear sequences** where steps must follow a fixed order. Example: users cannot confirm an appointment before viewing available times. Mark these with arrows that do not branch.

Identify **shortcuts** for returning users. If your persona noted that users often re-book appointments, include a shortcut from the entry point directly to a "quick rebook" screen, skipping the form. This is not laziness—it is respecting the user's mental model and their desire to complete the task quickly when they have done it before.

Create a **navigation inventory** listing every unique screen in your map. For the appointment example:

| Screen Name | Primary Action | Secondary Actions | Required Information Input |
|---|---|---|---|
| Entry Point | Select patient type | Browse FAQs | None |
| New Patient Form | Submit appointment request | Download form PDF, chat support | Name, DOB, reason, insurance |
| Appointment Review | Confirm and book | Edit form, cancel | None (review only) |
| Confirm & Calendar | Add to phone calendar | Share link, print | None (confirmation only) |

This table becomes your specification. Every wireframe screen corresponds to a row. Wireframing is the visual design of this information hierarchy.

### Part B: Low-Fidelity Wireframe Sketching

Open your sketchbook and begin sketching wireframes by hand for each screen in your navigation inventory. Work small and fast—3×5 inch sketches, one per screen. Do not render; use simple rectangles and lines to indicate layout zones.

For each sketch, establish a consistent **spatial grid.** Most interfaces use a 12-column grid or an 8-column grid for mobile. Sketch a faint pencil grid first. Then draw wireframe zones: header area (1 row), main content area (N rows), footer or action buttons (1 row).

Example for the "New Patient Form" screen (mobile, 8-column grid):

```text
┌────────────────────┐
│   [App Logo / Back]│  Header: 1 row
├────────────────────┤
│ New Patient Info   │  Title: 0.5 row
├────────────────────┤
│ [ Name field      ]│  
├────────────────────┤
│ [ DOB field       ]│  Form fields: 4 rows
├────────────────────┤
│ [ Reason field    ]│
├────────────────────┤
│ [ Insurance info  ]│
├────────────────────┤
│ [ Continue button ]│  Call-to-action: 0.5 row
├────────────────────┤
│ [ Cancel button   ]│  Secondary action: 0.5 row
└────────────────────┘
```

As you sketch, ask yourself these questions for each screen:

- **Entry clarity:** Can the user see the primary action immediately without scrolling? (On mobile, this is roughly the top 50% of the screen.)
- **Cognitive load:** Are there more than 3–5 primary interactive elements? If yes, group them or move some to a secondary screen.
- **Mental model alignment:** Does the layout reflect the user's task sequence, or does it reflect your backend data structure?
- **Error recovery:** If the user makes a mistake (selects wrong provider type, enters invalid data), is there an obvious way to go back?

Sketch 3–5 alternate layouts for the most critical screen (usually the entry point or first form). For the appointment example, the entry point might have three variations:

1. **Variation A:** Large buttons for "New Patient" and "Existing Patient" with no additional text.
2. **Variation B:** Same buttons with descriptive text below each ("First time here?" vs. "Already a patient?").
3. **Variation C:** A single entry point with inline text that explains the distinction after selection.

Do not overthink these variations—they should take 5 minutes each. The goal is to generate options quickly, then evaluate them against your design constraints. For the appointment domain, Variation B likely wins because the user's mental model includes the question "Am I a new or existing patient?" and seeing that question verbalized builds confidence.

After sketching all screens, identify **reusable components**—UI elements that appear across multiple screens. Examples:

- Form field (text input) with label and optional helper text.
- Button (primary action, secondary action).
- Card (provider information, available time slot).
- Navigation element (top bar with back button, breadcrumb, or tab bar).
- Modal or overlay (confirmation dialog, error message).

List these components and sketch a reference version of each. This component library will guide your digital wireframing.

### Part C: Medium-Fidelity Digital Wireframing in Figma or Penpot

Now translate your sketches into a digital wireframe system. Open **Figma** (figma.com, sign up free) or **Penpot** (penpot.app, also free and open-source).

**Initial setup:**

1. Create a new file named "Appointment Booking – Wireframes."
2. Set up a **base grid.** In Figma: File → Preferences → Guides → Grids. Create a grid with 12 columns (web) or 8 columns (mobile), 16 or 20 pixel gutter width, and 20 pixel row height. For mobile, typical dimensions are 375×812 pixels (iPhone); for web, 1440×900 pixels (common breakpoint).
3. Create a **color palette** for wireframing. Use only three colors: dark gray (#333333) for text and primary UI, light gray (#EEEEEE) for backgrounds and secondary zones, and a single accent color (#0066CC) for primary interactive elements. Wireframes should not look "pretty"—they should look functional and testable.
4. Create a **typography scale** with one font family (use system fonts like Inter, Roboto, or Helvetica). Define: body text (14px, regular), small text (12px, regular), headings (20px, bold), buttons (14px, bold). Do not vary beyond this. Consistency is clarity.

**Component creation (Figma) or symbol creation (Penpot):**

In Figma, create reusable components for each UI element. Right-click on a shape, select "Create component," and name it. Example component names:

- `Button / Primary`
- `Button / Secondary`
- `Form Field / Text Input`
- `Form Field / Select Dropdown`
- `Card / Provider`
- `Card / Time Slot`
- `Header / Top Bar`
- `Footer / Action Bar`

For `Button / Primary`: draw a rectangle (120 × 48 pixels), fill with #0066CC, add centered text "Continue" in white, 14px bold. This component is now reusable. Whenever you need a button, you drag an instance of this component onto your artboard, and it updates globally if you modify the main component.

Create 5–10 essential components. Do not create a component for every element—only for elements that repeat across screens. This saves time and ensures consistency.

**Screen wireframes:**

Create a new frame (shortcut: F) for each screen in your navigation inventory. Use the naming convention `01 – Entry Point`, `02 – New Patient Form`, `03 – Review`, `04 – Confirm`, etc. This keeps screens in logical order.

For the **Entry Point (mobile layout, 375×812 pixels):**

1. Draw a rectangle at the top (375×60 pixels, background #FFFFFF, border bottom #EEEEEE) for the header. Add text "Appointment Booking" (Poppins, 18px, bold, dark gray, left-aligned with 16px padding).
2. Below the header, add a large heading: "New or Existing Patient?" (20px, bold, centered, 24px top margin).
3. Add two primary buttons vertically stacked, each 320 × 60 pixels, spaced 16 pixels apart (use component instances). Label first button "New Patient," second button "Existing Patient."
4. Below the buttons, add a text link (12px, blue #0066CC) that says "I'm not sure. Help."
5. At the bottom, add a footer area (375×80 pixels, background #EEEEEE) with text "Call us: (555) 123-4567" (12px, gray, centered). This provides an escape hatch for users who cannot navigate the interface.

This is intentionally minimal. Wireframes should not distract with decoration. Every element serves a function.

For the **New Patient Form screen (mobile layout, 375×812 pixels):**

1. Header: "New Patient" (same as Entry Point).
2. Progress indicator (optional but recommended): a simple row of dots or a text label "Step 1 of 2" (12px, gray) showing where the user is in the flow.
3. Form container (320 pixels wide, centered, top margin 20px):
   - Label "Full Name" (12px, bold, dark gray) with a form field component below it (320 × 48 pixels, background white, border #CCCCCC, 12px inside padding). Placeholder text "Enter your full name" (12px, light gray).
   - Repeat for "Date of Birth" with a date picker placeholder.
   - Repeat for "Reason for Visit" with a dropdown icon (↓) indicating a select field.
   - Repeat for "Insurance Provider" with a select dropdown.
   - Below each field, add optional helper text (11px, light gray) if the field requires clarification. Example under "Reason for Visit": "Select the primary reason from the list provided."
4. Action bar at the bottom (fixed to viewport): two buttons (160 pixels each, side by side, 8px gutter): "Cancel" (secondary) and "Continue" (primary).

The form field component should have clear visual states: **default** (white background, light border), **focused** (white background, blue border, blue label text), **filled** (white background, text entered). You do not need to wireframe every state, but be aware that they exist. When you eventually code or prototype this, every state must be handled.

For the **Appointment Review screen:**

1. Header: "Confirm Appointment" with a back button (← icon, 24×24 pixels, left-aligned).
2. Content area showing all entered information in a **read-only card format:**
   - Row 1: "Patient Name" (bold label) → "Sarah Chen" (input text, gray #666666).
   - Row 2: "Date of Birth" → "03/15/1986."
   - Row 3: "Reason for Visit" → "Annual checkup."
   - Row 4: "Insurance" → "Aetna PPO."
   - Each row is 320 pixels wide, 44 pixels tall, with a subtle bottom border (#EEEEEE).
3. Below the card, add a "Change" link (blue, 12px) aligned right. Clicking this returns the user to the form to edit.
4. Action bar: "Back" (secondary) and "Confirm Booking" (primary).

For the **Confirmation & Calendar screen:**

1. Header: "Appointment Booked!" with a checkmark icon (✓, 48×48 pixels, centered, green #22AA22).
2. Confirmation details in a card:
   - "Dr. Sarah Johnson"
   - "Tuesday, March 14, 2024, 2:00 PM"
   - "In-office visit"
   - Confirmation number: "APT-2024-567890"
3. Action buttons:
   - "Add to Calendar" (primary, 320 × 48 pixels) – this would trigger exporting an .ics file or opening the system calendar app.
   - "Share Confirmation" (secondary) – email or SMS.
4. At the bottom, a link: "Back to Home" (12px, blue).

**Link and flow indication:**

In Figma, use the Prototype tab to create interactive flows between screens. Click the frame, select Prototype (top right), and add interactions: "On click" of the "New Patient" button on the Entry Point screen, navigate to frame "02 – New Patient Form." This creates a clickable wireframe prototype that stakeholders and testers can interact with without coding.

### Part D: Annotation and Specification

Wireframes are not specifications until you annotate them. Add text labels and notes that explain the logic to someone who did not create them.

For each screen, add a text box at the bottom (or in a separate layer called "Annotations") with the following information:

**For Entry Point:**
```text
Screen: Entry Point
Purpose: User determines whether they are new or existing patient.
Decision: This branching must be immediately clear. The question phrasing 
("New or Existing Patient?") must match user language from research.
On select, show relevant form.
Fallback: "Help" link connects to FAQ or chat support.
```

**For New Patient Form:**
```text
Screen: New Patient Form
Purpose: Collect required information before booking.
Validation: All fields are required. Show error state if user attempts 
to continue with empty fields (error message in red, #CC0000, 
immediately above the field).
Helper text under "Insurance" field must include: "This helps us verify 
coverage. If you don't have your insurance card, you can enter it later."
On continue, navigate to Review screen.
```

**For Review Screen:**
```text
Screen: Appointment Review
Purpose: User confirms all information before final booking.
Read-only: All fields display user input but are not editable on this screen.
Change link: Clicking "Change" returns user to form (preserve filled data).
On confirm, navigate to Confirmation screen and trigger backend booking.
```

**For Confirmation Screen:**
```text
Screen: Confirmation
Purpose: Confirm booking is complete and provide next steps.
Calendar export: "Add to Calendar" button exports appointment as .ics file 
(compatible with Apple Calendar, Google Calendar, Outlook).
Confirmation number: User should save this or receive via email for reference.
```

Annotations serve two purposes: they communicate intent to developers or other designers, and they force you to clarify your own thinking. If you cannot articulate why a decision exists, the decision is probably wrong.

### Part E: Testing Your Wireframe Structure

Before moving to Exercise 3, perform a **cognitive walkthrough**—a technique from usability research. Imagine you are the user persona from Exercise 1, entering the wireframe for the first time, with no prior knowledge.

Print out or display each wireframe in sequence. For each screen, ask:

1. **Can I see the primary action?** (Is it visually distinct and near the top?)
2. **Do I understand what happens next?** (Is the button label or screen title clear?)
3. **Can I go back if I make a mistake?** (Is there a back button or cancel option?)
4. **Do the labels use my language?** (Would I call this field "Reason for Visit" or would I expect "Chief Complaint" or "What brings you in?"?)

If you stumble or feel confused during this walkthrough, your user will too. Revise the screen before moving to Exercise 3.

Additionally, compare your wireframe set against the design constraints you extracted in Exercise 1. Create a **constraint validation checklist:**

- [ ] Constraint 1: "Insurance verification information must be retrievable or pre-filled before the user is asked to enter it." → Form screen includes helper text directing user to insurance card or option to enter later.
- [ ] Constraint 2: "The first branching decision must reflect user's mental model (new vs. existing)." → Entry Point uses exact phrasing from user observation.
- [ ] Constraint 3: "Critical path must be single session without context switching." → User never needs to leave the app to complete booking; all information is entered within the wireframe system.
- [ ] Constraint 4: "Use user's language." → All labels match terminology from user observation notes.
- [ ] Constraint 5: "Provide visual reference for providers." → Provider detail card (not yet shown but noted in navigation) includes provider photo at sufficient size.
- [ ] Constraint 6: "Confirmation includes calendar export." → Confirmation screen includes "Add to Calendar" button.

If any constraint is not met, revise the wireframe now.

### Deliverables for Exercise 2

1. **Hand-drawn site map** (1–2 pages): Tree diagram of information architecture with decision points and linear sequences marked.
2. **Navigation inventory table** (1 page): Every screen, its primary action, secondary actions, and required inputs.
3. **Low-fidelity sketches** (5–10 pages): Hand-drawn wireframes for each screen plus alternate layouts for critical screens.
4. **Medium-fidelity digital wireframes** (Figma or Penpot file): Full wireframe set with components, all screens connected via prototypes.
5. **Annotations and specifications** (1–2 pages): Notes on each screen explaining decision logic, error handling, and transitions.
6. **Constraint validation checklist** (1 page): Proof that wireframes satisfy design constraints from Exercise 1.

**Time allocation:** 6–8 hours total (1 hour site mapping, 1 hour low-fi sketching, 2 hours component setup, 2 hours screen wireframing, 1 hour annotation, 1 hour validation).

---

## Exercise 3: Finished Piece & Self-Critique – Usability Testing and Iterative Validation

### Objective

Wireframes are hypotheses, not finished designs. Exercise 3 teaches you to test those hypotheses against real users and iterate based on evidence. You will conduct a usability test, observe where your wireframe fails, revise it, and document the full cycle.

### Part A: Usability Test Protocol and Participant Recruitment

A usability test is a structured observation in which a user attempts to complete a task using your wireframe while you observe and note where they struggle. You are testing the wireframe, not the user. If a user cannot complete a task, that is evidence of a design problem, not a user problem.

**Recruit 3–5 participants** who match your user persona from Exercise 1. These should be real people from your target audience, not colleagues or friends who know you. If your persona is "busy parents booking medical appointments," recruit actual parents who have booked appointments in the past year. If your budget is zero, use a network: post in relevant Reddit communities, ask in Facebook groups, or recruit through local schools or organizations. Offer a small incentive ($10–20 USD or equivalent, or free coffee), which increases participation and signals respect for their time.

Create a **screening questionnaire** (Google Form or Typeform) to verify participants match your persona:

```text
1. Have you booked a medical appointment online in the past 6 months?
2. What device do you use most often: smartphone, tablet, or computer?
3. What operating system: iOS, Android, macOS, Windows, or Linux?
4. Have you had frustration with any appointment-booking app? Describe briefly.
```

Recruit participants who answer "yes" to questions 1 and 4, as they have relevant recent experience and can compare your wireframe to existing frustrations.

**Prepare a test environment.** This can be virtual (Zoom screen share) or in person. If virtual, use Zoom or Google Meet. If in person, meet in a neutral space (coffee shop, library, community center) with a table and two chairs. The participant sits in front of a laptop or tablet displaying your Figma prototype. You sit beside or slightly behind them, not directly across (which creates social pressure).

**Write a test script** to ensure consistency across participants. Example:

```text
Greeting & Consent (2 minutes):
"Thank you for coming. I'm testing a new appointment-booking interface. 
I want to watch you try to use it and hear your thoughts. There are no 
right or wrong answers—I'm testing the design, not you. I'll be quiet 
while you work, but I'll ask questions afterward. I'd like to record 
audio during this session for my notes. Is that okay?"
[Obtain verbal or written consent.]

Context Setting (1 minute):
"Imagine you need to book a dental appointment. It's your first time at 
this practice. Walk me through how you would do this using this interface. 
Think out loud—tell me what you're looking for, what you're thinking, 
what's confusing. Ready?"

Task Phase (5–10 minutes):
[User attempts to complete task. You observe silently. Jot notes on 
confusion points, clicks, hesitations.]

Debrief (5 minutes):
"Walk me through what you did. Where did you get stuck? What would have 
helped? Did anything surprise you?"
```

### Part B: Conducting the Test and Observing Failure Points

Deploy your Figma prototype by sharing the link. Set the prototype to **play mode** (click the play icon in the top right of Figma; this enters fullscreen prototype interaction mode). The participant sees only the wireframe interface, not the design tool.

As the participant works, observe and note:

1. **Task completion time:** How long did it take to complete the booking from start to confirmation?
2. **Clicks or interactions:** Which buttons or elements did they click? In what order?
3. **Hesitations:** Where did they pause, re-read text, or hover over elements without clicking?
4. **Backtracking:** Did they use the back button or navigate away from the intended path?
5. **Language reactions:** When they read text (labels, instructions, error messages), did they nod or grimace?
6. **Direct feedback:** Did they verbalize frustration or confusion? Quote them directly.

Example observation note:

```text
Participant 1 (Marcus, 35, busy parent):
- Arrived at Entry Point. Immediately saw "New Patient" button. Clicked it—correct choice.
- On Form screen, filled Name and DOB fields without issue. 
- On Reason for Visit field, hovered over dropdown but didn't click. Seemed unsure.
  [I remained silent.]
- After 3 seconds of hovering, he said, "I'm not sure what 'reason' means. Is this 
  for the doctor, or for scheduling purposes?"
- He then clicked the field and saw options: "Annual Exam," "Acute Problem," 
  "Referral Follow-up." He selected "Acute Problem."
- On Insurance field, immediately switched tabs to retrieve insurance card info. 
  When he returned, the form had not been cleared—good.
- Review screen: He read all fields, then clicked "Confirm Booking." 
- Confirmation screen: He immediately looked for a calendar button. Found "Add to Calendar" 
  and clicked it successfully.
- Total time: 2 minutes 45 seconds.
- Pain point: "Reason for Visit" label was ambiguous. He needed clarification.
```

Conduct 3–5 tests. After each test, review your notes and jot one-line summaries of key issues. Example:

```text
Participant 1: Ambiguous "Reason for Visit" label; unclear field purpose.
Participant 2: Same issue with "Reason for Visit." Also, didn't see the 
  "Help" link at bottom of Entry Point (scrolled past without noticing).
Participant 3: "Reason for Visit" was clear (had seen similar forms before). 
  Suggested that Insurance field show placeholder example: "e.g., Aetna PPO."
Participant 4: Successfully completed task. No major issues. Noted that 
  confirmation number was hard to find in success screen.
Participant 5: Same issues as Participants 1 and 2. High confidence conclusion 
  that "Reason for Visit" label needs improvement.
```

### Part C: Analyzing Test Results and Identifying Patterns

After testing, synthesize your findings into a **issues report** with three categories:

**Critical Issues (block task completion or cause severe confusion):**

Each critical issue has: description, number of participants affected, severity (why it matters), and location (which screen).

```text
Issue 1: "Reason for Visit" label is ambiguous.
Affected: 3 of 5 participants (60%).
Severity: User is unsure whether they should enter the reason (symptom) 
or the type of appointment (annual exam). Confusion delays form completion.
Location: New Patient Form screen, Reason for Visit field.
Evidence: "I'm not sure what 'reason' means. Is this for the doctor, 
or for scheduling purposes?" (Participant 1)
```

**Minor Issues (create friction but do not block completion):**

```text
Issue 2: "Help" link is not discovered by users.
Affected: 2 of 5 participants (40%).
Severity: Provides fallback support for confused users, but placement is 
ineffective (below the fold on mobile).
Location: Entry Point screen, bottom of content area.
Evidence: Participants 2 and 4 scrolled to bottom during task but didn't 
see or interact with the link.
```

**Positive Observations (what worked well):**

```text
Positive 1: "Add to Calendar" button was immediately understood and accessed.
Affected: 4 of 5 participants (80%).
Severity: Calendar integration is a key success metric. High success here 
indicates strong affordance.
Location: Confirmation screen, action buttons.
Evidence: Participants clicked "Add to Calendar" without hesitation, 
confirming the button label and location are clear.
```

Create a prioritized list of changes. Address critical issues first, then minor issues. Use this formula:

**Priority Score = (Number of Participants Affected / Total Participants) × Severity (1–5)**

```text
Issue 1 (Reason for Visit): (3/5) × 5 = 3.0 — Highest priority.
Issue 2 (Help link): (2/5) × 2 = 0.8 — Lower priority.
Positive 1: Continue.
```

### Part D: Iterative Revision of Wireframes

Based on your priority list, make specific changes to your wireframes. Document each change with a before-and-after comparison.

**Revision 1: "Reason for Visit" label clarity**

**Before:**
```text
Label: "Reason for Visit"
Field type: Dropdown
Options: "Annual Exam," "Acute Problem," "Referral Follow-up"
Helper text: None
```

**After:**
```text
Label: "Reason for Visit"
Field type: Dropdown
Helper text: "Select the type of appointment you need. This helps us schedule 
the right amount of time and prepare necessary information."
Options: "Annual Exam (routine check-up)," 
         "Acute Problem (pain, illness, injury)," 
         "Referral Follow-up (visiting based on another doctor's recommendation)"
```

The change: add helper text that explains the field's purpose (not which information to enter, but *why* we're asking). Make dropdown options longer and more descriptive so users can understand without opening the dropdown first. This directly addresses the ambiguity Participants 1, 2, and 5 expressed.

In Figma, update the wireframe:

1. Select the helper text under "Reason for Visit."
2. Edit the text to match the new helper text above.
3. Expand the dropdown options to show longer descriptive text.
4. Add a small annotation note: "Revision based on user test feedback: Participants confused by generic label. Added context and descriptive option text to clarify field purpose."

**Revision 2: "Help" link visibility**

**Before:**
```text
Location: Bottom of Entry Point screen (requires scroll on mobile)
Styling: 12px blue link text, standard
Visibility: Below fold (60% of users scrolled past without seeing)
```

**After:**
```text
Location: Entry Point screen, below buttons but before footer
Styling: Same (12px blue link, maintains visual hierarchy)
Visibility: Include in a small "Need help?" section with a question icon (?) 
           and short text: "Not sure which option to choose? Chat with us."
```

Change: Move the help link slightly higher and contextualize it with a question-mark icon and short label. The icon acts as a visual cue that this is optional assistance. In Figma:

1. Select the "Help" link.
2. Create a container around it (a subtle card or just grouped elements).
3. Add a question-mark icon (you can use a Unicode character "?" or draw a simple circle with "?") to the left of the link.
4. Add a small text label above: "Questions?"
5. This grouping makes the help option more noticeable without cluttering the main flow.

**Revision 3: Confirmation number visibility**

**Before:**
```text
Confirmation number is displayed in a text field: 
"APT-2024-567890" (12px gray text, left-aligned within card)
```

**After:**
```text
Confirmation number is displayed in a larger, more prominent code block:
- Background: Light gray (#F5F5F5)
- Border: 1px solid #CCCCCC
- Font: Monospace (Courier, 14px)
- Text: "APT-2024-567890" in dark gray, center-aligned
- Label above: "Your confirmation number (save this for reference)"
- Copy button: To the right of the number, an icon (📋 or "Copy")
```

This change makes the confirmation number scannable and memorable. Users can easily copy it to their clipboard without manually selecting and copying text.

Implement in Figma: Create a component for a code block and use it on the Confirmation screen.

### Part E: Second Round of Testing (Optional but Recommended)

With revisions made, conduct a second round of testing with 2–3 new participants (or the same participants if they are willing). Focus on the specific issues you revised:

- Do participants still struggle with "Reason for Visit"?
- Do they now notice the "Help" link?
- Is the confirmation number more discoverable?

Document the second round of results in a brief report comparing to the first round. Example:

```text
Revision Validation:

Issue 1 (Reason for Visit) — Revised:
First round: 3/5 participants (60%) confused.
Second round: 1/3 participants (33%) confused. The revised helper text 
helped, but one participant still wasn't sure whether to select based on 
symptom or appointment type. Recommend further clarification: add an 
example or use even more specific language.

Issue 2 (Help link) — Revised:
First round: 2/5 participants (40%) didn't discover the link.
Second round: 3/3 participants (100%) noticed the "Questions?" section 
with the icon. 1 participant clicked it; 2 saw it but didn't need it.
Revision successful.

Positive 1 (Add to Calendar) — No revision:
First round: 4/5 success (80%).
Second round: 3/3 success (100%). Maintained.
```

If a second round is not feasible due to time or recruitment constraints, document this limitation in your final report.

### Part F: Final Wireframe Version with Revision Notes

Create a final version of your wireframes incorporating all revisions. In Figma, create a new page called "Final – Revised Wireframes" and copy your screens there, then apply the revisions. Keep the original wireframes as a separate page for reference (labeled "Original – Initial Wireframes").

For each revised screen, add an annotation layer with the revision rationale:

```text
Screen: New Patient Form (Revised)
Changes from original:
1. "Reason for Visit" field: Added helper text clarifying field purpose. 
   Expanded dropdown options with descriptive text. 
   Based on user test feedback: 60% of participants initially confused by label.
2. Field validation: Error state now includes inline help text in addition to 
   red border, explaining why the field is required.

Evidence: Second round testing with revised labels reduced confusion to 33%.
```

Annotate all revised screens. This creates an audit trail showing your design process and evidence-based decision-making.

### Part G: Self-Critique and Final Validation

Before submitting, perform a final self-critique using the **UX critique rubric** (created in Exercise 1) plus a comprehensive checklist:

**Rubric Score (rate each 1–5, with 5 being excellent):**

| Criterion | Score | Evidence / Notes |
|---|---|---|
| **User Research Integration** | 4 | Research from Exercise 1 directly informed wireframe structure. Entry point branching mirrors user mental model. |
| **Information Architecture Clarity** | 5 | Site map is complete and unambiguous. Navigation hierarchy is shallow (max 3 clicks to any action). |
| **Mental Model Alignment** | 4 | Labels and flow use user language from observation. One pain point (Reason for Visit) required iteration. |
| **Error Handling & Recovery** | 3 | Form validation is clear, but error messages could be more specific. Added in revision. |
| **Affordance & Interaction** | 4 | Interactive elements (buttons, links, fields) are visually distinct. Test feedback confirmed most affordances work. |
| **Accessibility** | 3 | Wireframes use sufficient color contrast (#0066CC on white meets WCAG AA). Font sizes are readable (min 14px body). No assessment of screen reader compatibility (would require coded prototype). |
| **Consistency** | 5 | All screens use the same grid, typography, and component library. Consistency is high. |
| **Testability & Validation** | 5 | Usability testing was conducted. Issues were identified and addressed. Second round validates improvements. |

**Comprehensive Checklist:**

- [ ] **Information Architecture:** Site map captures all necessary user paths. No missing screens or shortcuts. Validated against user research constraints.
- [ ] **Navigation:** Users can reach any screen in 3 clicks or fewer. Back buttons and cancel options exist on all forms.
- [ ] **Forms:** All required fields are labeled. Helper text explains field purpose or required format. Error states are clear (red text or border). Validation happens before submission, with specific error messages (not generic "Error").
- [ ] **Language:** All labels, button text, and instructions use language from user research. No jargon or system-centric terms (e.g., "session" instead of "appointment").
- [ ] **Hierarchy:** Primary action (e.g., "Confirm Booking") is visually distinct from secondary actions (e.g., "Cancel"). Text hierarchy is clear (headings > body > help text).
- [ ] **Components:** Reusable UI components are consistent across screens. If a button appears different on two screens, there is a documented reason.
- [ ] **Prototyping:** Wireframe is interactive in Figma/Penpot. All screens are linked and playable. No broken links.
- [ ] **Annotation:** Every screen is annotated with purpose and decision logic. Revisions are documented with evidence.
- [ ] **Testing:** Usability testing was conducted with participants matching the user persona. Results are documented with direct quotes and observations. Revisions were made based on findings.
- [ ] **Validation:** Revised wireframes were tested (or at minimum re-validated via cognitive walkthrough). Issues were resolved or documented as trade-offs.

If any item scores below 3 or shows a failed checklist, make final revisions before submission.

### Part H: Design Process Report

Write a summary report (2–3 pages) documenting your complete design process for this project. Structure:

**1. Research Summary (0.5 page)**
- User persona: Name, goal, pain points.
- Key insights from user observation.
- Design constraints extracted.

**2. Design Exploration (0.5 page)**
- Site map and navigation hierarchy.
- Low-fidelity iterations (describe the 3–5 alternate layouts tested).
- Decision rationale for final structure.

**3. Wireframe Specification (0.5 page)**
- Overview of medium-fidelity wireframe system.
- Key components and their purpose.
- Design decisions (why this grid? why this typography scale?).

**4. Usability Testing & Iteration (1 page)**
- Test protocol and participant demographics.
- Critical findings from first round (3–5 issues with severity ratings).
- Revisions made and rationale.
- Results from second round testing (if conducted) showing improvement.

**5. Final Design & Lessons (0.5 page)**
- Final wireframe version and what changed from original.
- Key lesson learned from testing (what assumption proved wrong?).
- Recommendation for next phase (high-fidelity design, development, or further testing).

Example excerpt:

```text
Research Summary:
User persona: Sarah, 38, busy parent. Goal: Book pediatrician appointment 
in under 3 minutes. Key pain point: Unclear new vs. existing patient flow. 
Insurance information must be accessible during form completion.

Design Exploration:
Explored three entry-point layouts. Variation A (large buttons with no context) 
performed worst during cognitive walkthrough—user hesitated before selecting. 
Variation B (buttons + descriptive text) won, clearly stating the distinction 
users were trying to make. Final design uses Variation B.

Critical Findings:
Issue 1 (Reason for Visit ambiguity) affected 60% of participants. Caused 
hesitation and confusion about what information to enter. Severity: High.
Issue 2 (Help link invisibility) affected 40% of participants. No block to 
task completion but undermined fallback support. Severity: Low.

Revision:
Added helper text to Reason for Visit explaining field purpose. Provided 
descriptive option text. Second round: confusion reduced to 33%.
```

### Deliverables for Exercise 3

1. **Usability test protocol** (1 page): Script, screening questions, test environment description.
2. **Raw test observations** (3–5 pages): Notes from each participant session with timing, quotes, and issue identification.
3. **Issues report** (2 pages): Critical issues, minor issues, and positive observations ranked by priority score. Each issue includes description, participant count, severity, and evidence.
4. **Revised wireframes** (Figma/Penpot file): New page with all revisions applied. Original page preserved for comparison.
5. **Revision documentation** (1–2 pages): Before-and-after comparison for each major change with rationale.
6. **Second-round testing results** (optional, 1 page): Validation of revisions with new or returning participants.
7. **Self-critique rubric** (1 page): Scores and evidence for each criterion.
8. **Design process report** (2–3 pages): Complete narrative of research, exploration, testing, and iteration.

**Time allocation:** 8–12 hours total (2 hours test preparation and recruitment, 3–4 hours conducting tests, 2 hours analysis, 2 hours revision, 1–2 hours documentation).

---

## Critique Checklist & Common Fixes

This section serves as a diagnostic tool during your self-critique in Exercise 3 and as a guide for peer feedback if collaborating with other designers.

### Diagnostic Checklist: Does Your Wireframe Pass These Tests?

**Information Architecture & Navigation**

- [ ] **The site map is complete.** Every user action or decision point is represented. No "magic" transitions where users appear on a new screen without understanding how they got there.
- [ ] **Navigation depth is shallow.** Users reach any critical action (booking confirmation, finding contact info) in 3 clicks or fewer. If a path requires more than 3 clicks, ask: Is this a secondary user journey that belongs on a separate path, or can I flatten the hierarchy?
- [ ] **Decision points are unambiguous.** At every branching point (new vs. existing patient, urgent vs. routine), the user confidently knows which path to take. If you hesitated during cognitive walkthrough, so will users.
- [ ] **Back buttons and escape routes exist.** Users can undo or cancel actions. On forms, there is always a "Back" button and a "Cancel" button. Users should never feel trapped.

**Form Design & Data Entry**

- [ ] **All form fields are labeled.** No mystery inputs. Labels are outside the form field (above or to the left), not inside as placeholder text, because placeholder text disappears when the user starts typing.
- [ ] **Helper text explains why, not how.** "Insurance information is required to verify coverage" (why) is better than "Enter your insurance provider's name" (how, stated as fact).
- [ ] **Required vs. optional fields are marked.** Use either "(required)" or "(optional)" suffix, or a visual indicator like a red asterisk. Do not leave users guessing.
- [ ] **Error messages are specific and instructive.** "Error" is not specific. "Email must include '@' symbol" is specific. "Phone number must be 10 digits" is specific. Error text should appear in red (#CC0000) and immediately above or inline with the problem field.
- [ ] **Field validation happens at the right time.** Show inline validation as the user types (e.g., "Password must include a number"), or validate on blur (when the user moves to the next field). Do not wait until submit to tell them everything is wrong.
- [ ] **Buttons are clearly labeled with action language.** "Submit," "Continue," "Confirm Booking" are action labels. "Yes," "OK," "Next" are weak and context-dependent.

**Language & Mental Model Alignment**

- [ ] **Labels match user terminology.** If users say "find a provider," your interface should say "Find a Provider," not "Browse Healthcare Practitioners." Extract terminology from user research (Exercise 1). Do not use system-centric language.
- [ ] **Instructions are task-oriented.** "Select the type of appointment you need" is task-oriented (the user's perspective). "Choose appointment category from the system list" is system-oriented (the backend's perspective).
- [ ] **Microcopy (error messages, help text, button labels) is consistent.** If you say "Appointment" in one place, do not say "Session" elsewhere. Create a terminology glossary and stick to it.
- [ ] **Jargon is eliminated or explained.** Users are not system administrators. They do not understand "API," "node," "session ID," or "bandwidth." If technical terms are necessary, define them inline or link to a glossary.

**Visual Hierarchy & Affordance**

- [ ] **The primary action is visually dominant.** The most important button (e.g., "Confirm Booking") is larger, more prominent, or in a bolder color than secondary buttons. Squint at your wireframe—can you spot the primary action immediately?
- [ ] **Interactive elements are distinguishable.** Buttons look like buttons (rectangular, bordered, or filled with color). Links look like links (blue, underlined). Form fields look like form fields (bordered rectangles or input-specific styling). Do not make a button look like plain text.
- [ ] **Text hierarchy is clear.** Headings (20–24px) are significantly larger than body text (14px). Subheadings (18px) are clearly between headings and body. Do not use more than three sizes on a single screen.
- [ ] **Color is used purposefully.** Accent color (#0066CC in wireframes) is reserved for primary actions and interactive elements. Do not color every element. Light gray (#EEEEEE) is for secondary backgrounds or dividers. Dark gray (#333333) is for text. This restraint makes the accent color meaningful.

**Error Handling & Edge Cases**

- [ ] **Empty states are handled.** If a user has no appointments booked, the screen does not show a blank page. It shows a helpful message: "You have no upcoming appointments. Ready to book one? Click here." This is better than a blank state.
- [ ] **Network errors are anticipated.** In the annotation for server-dependent screens, note: "If the booking server is unavailable, show error screen with message: 'We're having trouble booking your appointment. Try again or call [number].'" This is not wireframed in detail but is documented so developers know to handle it.
- [ ] **Validation failures are handled gracefully.** If a user enters invalid data (wrong email format, insurance card format unrecognized), do not simply reject it. Show specific feedback and an option to proceed manually or get help: "We couldn't verify this insurance information. You can enter it manually or chat with us for help."

**Accessibility & Inclusion**

- [ ] **Text contrast is sufficient.** Dark gray (#333333) on white (#FFFFFF) meets WCAG AA standard (4.5:1 contrast ratio). Light gray text on light backgrounds does not. Test with a contrast checker (WebAIM Contrast Checker).
- [ ] **Font sizes are readable.** Body text is minimum 14px (wireframes do not need to test smaller sizes, but developers should know the target). Links and buttons are at least 48×48 pixels (or sufficient touch target size) on mobile.
- [ ] **Color is not the only indicator.** If you mark errors in red, also use error icon or text. If you mark success in green, also use checkmark or text. Users who are colorblind need a second cue.
- [ ] **Interactive elements are keyboard accessible.** Buttons must be clickable. Form fields must be focusable (users can tab through them). Links must be underlined or otherwise distinguishable from body text. This is not fully testable in wireframes but should be documented for development.

### Common Issues & Fixes

**Issue: Users Are Confused by Ambiguous Labels**

Symptom: Usability test reveals that multiple users hesitate before clicking or selecting, re-read text, or ask for clarification.

Cause: Label is too generic, jargon-heavy, or does not align with user mental model.

**Fix Option 1: Rewrite the label to be more specific.**
- Before: "Services"
- After: "Find a Service or Specialist"

**Fix Option 2: Add helper text that explains the field's purpose.**
- Before: "Category"
- After: "Category (Choose the type of care you need: preventive, urgent, or specialist referral)"

**Fix Option 3: Use examples in placeholder text or as dropdown options.**
- Before: Dropdown with single-word options: "Annual," "Acute," "Follow-up"
- After: Dropdown with descriptive options: "Annual Exam (routine check-up)," "Acute Problem (pain or illness)," "Follow-up (from another doctor's referral)"

**Issue: Users Miss Important Information or Buttons**

Symptom: Users scroll past a button or section they need, or they do not discover help or fallback options.

Cause: Element is placed below the fold (requires scrolling on mobile) or lacks visual prominence. It competes with other elements for attention.

**Fix Option 1: Move the element higher on the screen.**
- Before: Help link at bottom of screen (requires scrolling).
- After: Help icon and "Questions?" label below the main action buttons, visually grouped and within viewport.

**Fix Option 2: Increase visual prominence.**
- Before: Help link in 11px gray text, left-aligned.
- After: Help link in 12px blue text, with a question-mark icon to the left, contained in a subtle box or section.

**Fix Option 3: Provide multiple access points.**
- Before: Help is only available via a small link.
- After: Help is available via link, via a floating "Chat" button in bottom right, and via phone number in footer.

**Issue: Form Completion Is Slow or Error-Prone**

Symptom: Usability test shows users taking longer than expected to fill out forms, or they abandon the form without completing it.

Cause: Too many required fields, unclear field purposes, lack of guidance, or missing data already in the system.

**Fix Option 1: Reduce the number of fields.**
- Before: Form asks for Name, DOB, Address, Phone, Email, Insurance Provider, Insurance ID, Group Number, Co-pay, Deductible.
- After: Form asks for Name, DOB, Reason for Visit. Insurance info is optional on first form; it can be collected after appointment confirmation.

**Fix Option 2: Pre-fill data when possible.**
- Before: User enters phone number, even though the system already has it.
- After: If user is logged in, pre-fill phone and email. User sees "Confirm: 555-123-4567?" instead of blank input.

**Fix Option 3: Provide clear guidance at each step.**
- Before: Form shows 10 blank fields with no indication of progress.
- After: Form shows progress indicator ("Step 1 of 2: Basic Info") and displays 3–4 fields per step. User can see the end of the journey.

**Fix Option 4: Use conditional fields.**
- Before: All users see all fields regardless of their path.
- After: If user selects "New Patient," they see the Full Form. If user selects "Existing Patient," they see a Quick Rebook form with fewer fields.

**Issue: Wireframe Does Not Meet Design Constraints**

Symptom: During final validation (Part G of Exercise 3), you realize a wireframe design does not satisfy a constraint from Exercise 1.

Cause: Constraint was lost or overlooked during wireframing. This is common when moving from research to design.

**Fix: Return to the constraint and redesign the screen to satisfy it.**

Example:
- Constraint (from Exercise 1): "Insurance verification information must be retrievable or pre-filled before the user is asked to enter it."
- Wireframe: Form asks user to enter insurance provider name in a text field.
- Problem: User cannot retrieve their insurance card during form completion (they are in a waiting room). The form violates the constraint.
- Fix: Add a note below the insurance field: "Don't have your insurance card? You can enter it after your appointment, or we can collect it by phone. Chat with us for help." This acknowledges the constraint and provides an escape route. Alternatively, pre-populate the field with common insurance providers, allowing users to select instead of typing.

**Issue: Navigation Is Too Deep**

Symptom: Usability test reveals that users need to click more than 3 times to reach certain actions, or they get lost and use the back button repeatedly.

Cause: Information hierarchy is too tall (many levels) instead of wide (more options at each level). Site map has too many screens in linear sequence.

**Fix Option 1: Flatten the hierarchy.**
- Before: Home → Services → Specialists → Cardiology → Find Cardiologist
- After: Home → Find Cardiology Specialist (all-in-one screen with filter options)

**Fix Option 2: Add shortcuts.**
- Before: Users must go through the full booking flow every time.
- After: Returning users see a "Quick Rebook" shortcut on the home screen, jumping directly to available times.

**Fix Option 3: Combine screens where logical.**
- Before: Screen 1 shows appointment type. Screen 2 shows available times. Screen 3 shows provider details. User must click through all three.
- After: Single screen shows appointment type, available times, and provider details side by side. User can make all decisions on one screen.

**Issue: Wireframe Contains Unnecessary Decoration or Too Much Detail**

Symptom: Wireframe looks "pretty" and finished, but it obscures structural decisions. Testers focus on design aesthetics instead of usability. Wireframe cannot be easily modified.

Cause: Over-specification. You added color gradients, shadow effects, or pixel-perfect alignment that belong in high-fidelity design, not wireframes.

**Fix: Simplify.**
- Before: Buttons have gradient fills, drop shadows, and 2px borders.
- After: Buttons have flat fills (#0066CC) with no shadow. Wireframe is functional, not beautiful.

The goal of wireframes is to communicate structure and test assumptions, not to look polished. If your wireframe is so detailed that it took 40 hours, you over-designed. A complete wireframe system for a 4–5 screen flow should take 4–8 hours in a tool like Figma.

**Issue: Test Results Are Inconsistent or Unclear**

Symptom: After usability testing, you have contradictory feedback. Participant 1 loved a feature; Participant 2 hated it. You are unsure whether to revise.

Cause: Either the sample size is too small (n=2–3), or the feature serves different user mental models. This is actually useful information.

**Fix Option 1: Test with more participants.**
- If you tested n=3 and had split feedback, test n=5 total. If 4 out of 5 prefer one approach, it is likely the right choice.

**Fix Option 2: Segment the feedback by user profile.**
- If feedback splits along demographic or behavioral lines (tech-savvy users like feature X; non-tech-savvy users do not), consider whether you need two versions of the experience or whether a redesign works for both.

**Fix Option 3: Dig deeper in debrief.**
- Ambiguous feedback often means you asked an ambiguous question. In a second test, ask specific follow-up: "If this feature were available, would you use it?" instead of "What do you think of this feature?"

---

## Final Summary: The Design Process in Practice

Wireframing is not an art form or a tool skill. It is a disciplined approach to solving human problems through systematic observation, structured thinking, and iterative testing. This lab sequence teaches you that cycle:

**Research → Constraints → Exploration → Validation → Iteration.**

By the end of these three exercises, you have produced artifacts that communicate to developers and stakeholders, evidence that your design decisions are rooted in user research, and proof that your wireframe works in practice. You have learned to see wireframes not as final designs but as testable hypotheses.

The discipline continues beyond these labs: every design you create in professional practice should follow this cycle. Test your assumptions. Listen to users. Revise. The best designers are not the most artistic; they are the most rigorous in their research and the most willing to throw away their assumptions when users show them they are wrong.
