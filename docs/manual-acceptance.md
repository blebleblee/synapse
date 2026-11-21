# Manual Acceptance Checklist

**Objective:** Validate real-use learner journey and primary application workflows.
**Estimated Time:** 15–20 minutes

*Note: Automated stabilization is complete for the current backlog. This manual acceptance is the next milestone to ensure UX and real-world behavior are correct.*

## Session Workflow

Follow these steps sequentially to simulate a realistic learning session.

### 1. Curriculum Selection
- **Action:** Open the application and select an existing curriculum from the main interface.
- **Expected Result:** The curriculum loads correctly, showing the topic tree and available lessons.
- **Status:** [ ] PASS / [ ] FAIL / [ ] CONFUSING
- **Notes:**

### 2. Lesson Rendering
- **Action:** Read a lesson that includes math formulas and Mermaid diagrams.
- **Expected Result:** Markdown, KaTeX math, and Mermaid diagrams are rendered cleanly without raw code blocks leaking.
- **Status:** [ ] PASS / [ ] FAIL / [ ] CONFUSING
- **Notes:**

### 3. Navigation & Search
- **Action:** Use the search feature to find a specific concept, then click a result to navigate to it.
- **Expected Result:** The application directly opens the corresponding lesson containing the search result snippet.
- **Status:** [ ] PASS / [ ] FAIL / [ ] CONFUSING
- **Notes:**

### 4. Progress Tracking & Resume
- **Action:** Mark the current lesson as complete. Reload the browser tab.
- **Expected Result:** The lesson remains marked as complete in the UI, and the application automatically resumes to the same lesson and topic.
- **Status:** [ ] PASS / [ ] FAIL / [ ] CONFUSING
- **Notes:**

### 5. AI Provider Configuration
- **Action:** Open Settings and configure a Socratic Mentor AI provider (e.g., Local Ollama or a Cloud API key).
- **Expected Result:** The UI accepts and saves the provider. (If using a cloud provider, note that this will use your credentials and may incur costs).
- **Status:** [ ] PASS / [ ] FAIL / [ ] CONFUSING
- **Notes:**

### 6. Socratic Mentor Interaction
- **Action:** Open the Mentor chat. Ask a question about the current lesson context, followed by a clarifying follow-up question. (Requires AI provider).
- **Expected Result:** The mentor responds contextually, correctly identifying the current lesson and maintaining conversational history.
- **Status:** [ ] PASS / [ ] FAIL / [ ] CONFUSING
- **Notes:**

### 7. Content Generation
- **Action:** Generate a small curriculum unit or summary, and open the result in the reader. (Requires AI provider).
- **Expected Result:** Generation completes successfully (showing progress), and the newly authored content is readable and formatted correctly.
- **Status:** [ ] PASS / [ ] FAIL / [ ] CONFUSING
- **Notes:**

### 8. General UX Observations
- **Action:** Note any confusing controls, misleading error messages, or broken UI elements during the session.
- **Notes:** 

---

## Issue Template

If a defect or confusing behavior is found, please report it using the format below:

**Action:** (What did you do?)
**Expected:** (What should have happened?)
**Actual:** (What actually happened?)
**Evidence:** (Console errors, screenshots, or visual description)
