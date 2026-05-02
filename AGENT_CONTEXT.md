# 🤖 QA Assist — Agent Context & Architecture
> **Notice to AI Agents:** Read this document BEFORE attempting to modify, debug, or extend the QA Assist codebase. It outlines the architectural design, state management, and strict coding conventions of the project.

---

## 1. System Overview & Tech Stack
QA Assist is a multi-page, production-ready Streamlit application serving as an AI-powered QA engineering companion. 
- **Frontend / Framework:** Streamlit
- **AI Integration:** Google GenAI SDK (`google-genai` library, specifically using `gemini-2.5-flash`). Do NOT use the deprecated `google-generativeai` package.
- **Data Handling:** Pandas (for DataFrame manipulation) and Openpyxl (for rich Excel exports).
- **Styling:** Vanilla CSS injected via Streamlit markdown (no Tailwind).

---

## 2. File Structure & Responsibilities

### `app.py`
The entry point and primary orchestrator. 
- **Responsibilities:**
  - Streamlit page config and routing.
  - Authentication gate (Login / Register logic).
  - Sidebar navigation and dynamic rendering (e.g., hiding "Users" tab from non-admins).
  - Renders the `Dashboard`, `From Screenshot`, `From Requirements`, `Test History`, and `Users` pages.
  - Central helper functions for Gemini client init (`configure_model()`) and Excel formatting (`build_excel()`).

### `automation_page.py`
Modularized page logic specifically for the "Automation Scripts" tab.
- **Responsibilities:**
  - Manages the heavy workflow of generating test automation code.
  - Contains `FRAMEWORKS` dictionary for supported automation stacks (Selenium, Playwright, Cucumber, WDIO).
  - Handles `git clone` subprocesses to fetch user repositories and walk their files to extract structural context (POM, naming conventions).
  - Builds and submits the strict prompt logic to Gemini.

### `pipeline_report_page.py`
Standalone module for the "📈 Pipeline Report" tab. No AI/Gemini calls — pure data parsing and formatting.
- **Responsibilities:**
  - Accepts Allure result files: individual `.json` files OR a `.zip` archive of the `allure-results/` folder.
  - Parses each JSON into a flat row (test name, status, suite, feature, error message, stack trace, duration, timestamps).
  - Renders live metrics (pass rate, counts), filterable dataframe, and a **Debug Panel** showing per-test stack traces in `st.expander()` blocks.
  - Exports a rich multi-sheet Excel (`build_report_excel()`): Summary (with BarChart) → ❌ Failed → ⚠️ Broken → ⏭️ Skipped → 📋 All Tests.
  - Key parsing helper: `parse_uploads(uploaded_files)` → returns `(df, errors)`.

### `styles.py`
Centralized CSS payload.
- **Responsibilities:**
  - Injects a premium, dark-mode, glassmorphic UI via `st.markdown()`.
  - Overrides default Streamlit borders (removes red/blue focus outlines).
  - Exposes Python helper functions like `info_card()` or `step_header()` that wrap Streamlit `st.markdown()` calls to generate styled HTML components.

### `users.json`
Local persistent database for user accounts.
- **Responsibilities:**
  - Stores SHA-256 hashed passwords, session counts, and basic user metadata. 

---

## 3. State Management (`st.session_state`)

Streamlit's `st.session_state` is heavily utilized. When making changes, ensure you do not overwrite these without cause:
- `logged_in` (bool): Guard for the auth gate.
- `username` (str): Current user's ID (e.g., "admin").
- `full_name` (str): Display name.
- `history` (list[dict]): Ephemeral storage for test cases generated *during the current session*. Rendered on the Dashboard and Test History pages.
- `reg_flash` (str | None): Used for the redirect-flash-message pattern after a successful registration.
- `selected_fw` (str): The currently chosen automation framework in `automation_page.py`.
- `repo_context` (str): The stringified code content parsed from the user's uploaded/cloned Git repository, used as context for the AI.
- `auto_history` (list[dict]): Ephemeral storage for automation scripts generated during the session.

---

## 4. Key Architectural Patterns

### 4.1 Caching (Performance)
- **`@st.cache_data`**: Applied to `load_users()` to prevent constant disk I/O on every UI interaction. The cache is manually cleared via `load_users.clear()` inside `save_users()`.
- **`@st.cache_resource`**: Applied to `configure_model()` to ensure the `genai.Client()` is only initialized once and kept in memory.

### 4.2 Streamlit "Magic" Avoidance
- Do NOT use ternary operators that return Streamlit DeltaGenerators on a single line (e.g., `st.success() if ok else st.error()`). This causes Streamlit's magic renderer to dump object metadata to the UI. Always use explicit `if/else` blocks.

### 4.3 UI Layout & Aesthetics
- The app uses a strict 3-column or 2-column grid system for inputs to prevent vertical bloat. 
- Never use raw `st.write()` for headers. Use `styles.section_header()` or `styles.step_header()`.
- Focus outlines are globally disabled in `styles.py`.

### 4.4 Advanced Excel Formatting
- Dataframes are exported to Excel using `openpyxl`.
- The `build_excel()` function in `app.py` manually applies background colors, frozen panes, bold text, column width constraints, and dynamic Priority-based conditional coloring (Red/Yellow/Green) directly to the `.xlsx` binary buffer before downloading.

---

## 5. Modifying or Adding AI Prompts
If you are adjusting the prompt to Gemini:
- Maintain the strict instruction: `Return ONLY a raw JSON array (no markdown fences)`.
- Use the `gemini-2.5-flash` model.
- Always include `st.spinner()` context blocks during generation to maintain UX.
- In `automation_page.py`, ensure that code-fences (` ``` `) are properly stripped via the internal extraction methods before being rendered to the user.
