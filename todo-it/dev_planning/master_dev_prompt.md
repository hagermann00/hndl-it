# MASTER PROMPT: Todo-It Deep Dive & Nested Responsibility Architecture

## 1. System Assessment & Context

**Target Module:** `c:\iiwii_db\hndl-it\todo-it`
**Current State:** Functional PyQt6 floater with basic `todos.json` storage.
**Objective:** Evolve this into a powerhouse "Nested Responsibility" system (Infinite depth, localized sub-tasks, "rolling" completion status).

## 2. Research & Competitive Analysis (Multi-Scale)

Conduct a deep functional comparison of how the following manage "Responsibility" and "Nesting":

- **Code-Centric:** GitHub Issues (Tasklists, Milestones), GitLab Epics.
- **Productivity-Centric:** OmniFocus (Perspectives), Things3 (Areas), Linear (Cycles/Projects).
- **Enterprise:** Jira (Hierarchy), Asana.

**Key Research Questions:**

1. **Data Structure:** How do they handle infinite nesting without performance degradation (Adjacency List vs. Materialized Path)?
2. **Context Propagation:** How does a child task inherit context (tags, deadlines) from a parent?
3. **"Rolling" Logic:** What are the mathematical rules for a parent being "50% complete" based on varied child weights?

## 3. Multi-LLM Orchestration Strategy

Define a workflow where we use specific LLMs for specific phases of this dev cycle:

- **Gemini 1.5 Pro (Context Window):** Feed it the entire existing `hndl-it` codebase to map dependencies.
- **Claude 3.5 Sonnet (Coding):** Generate the PyQt6 recursive rendering logic (TreeViews vs. Nested Layouts).
- **O1/Reasoning Models:** Architect the JSON schema and "Responsibility" logic (conflict resolution, syncing).

## 4. Residency Production Plan

Produce a development roadmap that includes:

- **Phase 1:** Schema migration (Flat `todos.json` -> Recursive/Relational).
- **Phase 2:** UI Refactor (Visualizing depth without clutter).
- **Phase 3:** Integration (How `hndl-it` agents "see" and "modify" deep sub-tasks).

## 5. Execution Directive

Start by listing the files in `c:\iiwii_db\hndl-it\todo-it`, reading the current schema, and then executing the research phase defined above.
