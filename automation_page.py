"""
automation_page.py — QA Automation Script Generator
Handles the 🤖 Automation Scripts sidebar page for QA Assist.
"""
import os
import subprocess
import tempfile
import shutil
import datetime
import streamlit as st
from google import genai
from PIL import Image

import styles
import shared

# ── Framework metadata ─────────────────────────────────────────────────────────
FRAMEWORKS = {
    "Selenium (Python)":       {"icon": "🐍", "ext": "py",      "language": "python",     "description": "Python + Selenium WebDriver + pytest"},
    "Playwright (Python)":     {"icon": "🎭", "ext": "py",      "language": "python",     "description": "Python + Playwright + pytest"},
    "Playwright (JS/TS)":      {"icon": "🎭", "ext": "ts",      "language": "typescript", "description": "TypeScript + Playwright Test runner"},
    "WebdriverIO (JS)":        {"icon": "🌐", "ext": "js",      "language": "javascript", "description": "JavaScript + WDIO + Mocha"},
    "Cucumber (JS + WDIO)":    {"icon": "🥒", "ext": "feature", "language": "gherkin",    "description": "Gherkin feature file + JS step definitions"},
    "Cucumber (Java + Selenium)": {"icon": "☕", "ext": "feature", "language": "gherkin", "description": "Gherkin feature file + Java step definitions"},
}

LOCATOR_TYPES = ["ID", "Class Name", "CSS Selector", "XPath", "Data-TestID", "Link Text", "Tag Name", "Accessibility ID"]


# ── Git helpers ─────────────────────────────────────────────────────────────────
def _clone_or_pull(repo_url: str, local_path: str) -> tuple[bool, str]:
    try:
        if os.path.exists(local_path):
            shutil.rmtree(local_path)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, local_path],
            capture_output=True, text=True, timeout=120,
        )
        return (True, "Cloned successfully.") if result.returncode == 0 else (False, result.stderr.strip())
    except FileNotFoundError:
        return False, "Git is not installed or not on PATH."
    except subprocess.TimeoutExpired:
        return False, "Clone timed out (>2 min). Try a smaller repo."
    except Exception as e:
        return False, str(e)


def _walk_files(root: str, extensions: list[str], max_files: int = 40) -> list[str]:
    collected = []
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fname in filenames:
            if any(fname.endswith(f".{ext}") for ext in extensions):
                collected.append(os.path.join(dirpath, fname))
                if len(collected) >= max_files:
                    return collected
    return collected


def _read_sample_files(paths: list[str], max_chars_each: int = 3000) -> str:
    parts = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_chars_each)
            rel = os.sep.join(p.split(os.sep)[-3:])
            parts.append(f"### File: {rel}\n```\n{content}\n```")
        except Exception:
            pass
    return "\n\n".join(parts)


def _detect_extensions(framework_name: str) -> list[str]:
    if "Cucumber" in framework_name and "Java" in framework_name:
        return ["feature", "java"]
    if "Cucumber" in framework_name:
        return ["feature", "js", "ts"]
    if "WebdriverIO" in framework_name:
        return ["js", "ts", "json"]
    if "Playwright" in framework_name and "Python" in framework_name:
        return ["py"]
    if "Playwright" in framework_name:
        return ["ts", "js"]
    if "Selenium" in framework_name:
        return ["py"]
    return ["py", "js", "ts"]


# ── Prompt builder ──────────────────────────────────────────────────────────────
def _build_prompt(framework: str, description: str, repo_context: str,
                  screenshot: bool, preferred_locators: list[str]) -> str:
    locators_note = (
        f"\n[Locator Preference] Use these locator strategies (in order of priority): {', '.join(preferred_locators)}."
        if preferred_locators else ""
    )
    screenshot_note = (
        "A screenshot of the UI feature is provided — identify exact element labels, "
        "field names, and UI structure from it."
        if screenshot else ""
    )
    repo_note = (
        f"Study the structure of the existing project (framework: {framework}) below — "
        f"naming conventions, import patterns, POM structure, selector styles, assertions — "
        f"and write the new test to match exactly.\n\n"
        f"--- PROJECT CONTEXT ---\n{repo_context}\n--- END CONTEXT ---"
        if repo_context
        else f"No existing project provided. Follow industry best practices for {framework}."
    )

    if "Cucumber" in framework:
        step_lang = "Java (Selenium WebDriver)" if "Java" in framework else "JavaScript/TypeScript (WebdriverIO)"
        return f"""You are a Senior QA Automation Engineer.
{screenshot_note}

{repo_note}

Task: Write a complete Cucumber test for:
\"\"\"{description}\"\"\"

Output TWO code blocks in order:
1. A Gherkin `.feature` file (Feature, Background if needed, Scenario/Scenario Outline, Examples table).
2. Step definitions in {step_lang} implementing every step, with POM if the project uses it.

Include: proper locator strategy{locators_note}, explicit waits, assertions, and teardown.
Output ONLY the two code blocks — no prose outside them.
"""
    return f"""You are a Senior QA Automation Engineer.
{screenshot_note}

{repo_note}

Task: Write a complete, runnable {framework} test script for:
\"\"\"{description}\"\"\"

Requirements:
- Match the existing project style exactly.
- Page Object Model pattern (if applicable).
- Explicit waits only — no hard sleeps.
- Concise inline comments on each major step.
- Immediately runnable — zero TODO placeholders.{locators_note}

Output ONLY the code block — no prose outside it.
"""


# ── Code extraction ─────────────────────────────────────────────────────────────
def _extract_code(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _split_cucumber(text: str) -> dict:
    feature_lines, step_lines = [], []
    in_f = in_s = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```gherkin") or s.startswith("```feature"):
            in_f, in_s = True, False; continue
        if in_f and s == "```":
            in_f = False; continue
        if in_f:
            feature_lines.append(line); continue
        if any(s.startswith(f"```{l}") for l in ("java","javascript","typescript","js","ts")):
            in_s, in_f = True, False; continue
        if in_s and s == "```":
            in_s = False; continue
        if in_s:
            step_lines.append(line)

    return {
        "feature": "\n".join(feature_lines) if feature_lines else text.split("```")[0].strip(),
        "steps":   "\n".join(step_lines)   if step_lines   else "# Step definitions could not be extracted.",
    }


# ── Main renderer ───────────────────────────────────────────────────────────────
def render():
    styles.section_header(
        "🤖", "Automation Script Generator",
        "Choose a framework, link your project, describe the test — get production-ready automation code."
    )

    # ── State ──────────────────────────────────────────────────────────────────
    for k, v in [("selected_fw", list(FRAMEWORKS.keys())[0]),
                 ("repo_context", ""), ("repo_label", ""),
                 ("auto_history", [])]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 1 — Framework selector
    # ══════════════════════════════════════════════════════════════════════════
    styles.step_header("1", "Choose Framework")

    fw_names = list(FRAMEWORKS.keys())
    row1, row2 = fw_names[:3], fw_names[3:]

    for row in [row1, row2]:
        cols = st.columns(3)
        for col, fw in zip(cols, row):
            meta     = FRAMEWORKS[fw]
            selected = st.session_state.selected_fw == fw
            css_cls  = "fw-card active" if selected else "fw-card"
            with col:
                st.markdown(f"""
                <div class="{css_cls}">
                    <div class="fw-icon">{meta['icon']}</div>
                    <div class="fw-name">{fw}</div>
                    <div class="fw-desc">{meta['description']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(
                    "✓ Selected" if selected else "Select",
                    key=f"fw_{fw}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                ):
                    st.session_state.selected_fw = fw
                    st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


    chosen_fw = st.session_state.selected_fw

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 2 — Git project
    # ══════════════════════════════════════════════════════════════════════════
    styles.step_header("2", "Link Your Git Project (optional)")
    st.caption("The AI will study your project's structure and generate code that matches your style exactly.")

    g_in, g_btn = st.columns([5, 1])
    with g_in:
        git_source = st.text_input(
            "repo_url", label_visibility="collapsed",
            placeholder="https://github.com/your-org/your-tests.git   or   C:/projects/my-tests",
        )
    with g_btn:
        load_repo = st.button("📂  Load", type="primary", use_container_width=True)

    if load_repo and git_source.strip():
        with st.spinner("Loading project…"):
            exts = _detect_extensions(chosen_fw)
            src  = git_source.strip()
            if os.path.isdir(src):
                files = _walk_files(src, exts)
                if files:
                    st.session_state.repo_context = _read_sample_files(files[:20])
                    st.session_state.repo_label   = os.path.basename(src)
                    st.success(f"✅  Loaded {len(files)} files from local folder.")
                else:
                    st.warning("No matching files found for this framework.")
            elif src.startswith(("http://", "https://", "git@")):
                tmp = os.path.join(tempfile.gettempdir(), "qa_assist_repo")
                ok, msg = _clone_or_pull(src, tmp)
                if ok:
                    files = _walk_files(tmp, exts)
                    st.session_state.repo_context = _read_sample_files(files[:20])
                    st.session_state.repo_label   = src.split("/")[-1].replace(".git","")
                    st.success(f"✅  Cloned and loaded {len(files)} files.")
                else:
                    st.error(f"Clone failed: {msg}")
            else:
                st.warning("Enter a valid Git URL or local folder path.")

    if st.session_state.repo_context:
        with st.expander(f"📁  Project loaded: **{st.session_state.repo_label}**"):
            st.code(st.session_state.repo_context[:4000], language="text")
        if st.button("✕  Clear project", type="secondary"):
            st.session_state.repo_context = ""
            st.session_state.repo_label   = ""
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 3 — Test description + screenshot
    # ══════════════════════════════════════════════════════════════════════════
    styles.step_header("3", "Describe the Test Case")

    desc_col, img_col = st.columns([1.7, 1])

    with desc_col:
        tc_description = st.text_area(
            "What should the test do?",
            placeholder=(
                "Verify a registered user can log in with valid credentials.\n\n"
                "Steps:\n"
                "1. Navigate to /login\n"
                "2. Enter email 'user@test.com' and password 'Test@1234'\n"
                "3. Click the Login button\n"
                "4. Assert dashboard heading is visible"
            ),
            height=220,
        )
        test_name = st.text_input("Output file name (optional)", placeholder="e.g. login_spec  or  LoginTests")

    with img_col:
        st.markdown("**📸 Upload UI Screenshot**", unsafe_allow_html=False)
        st.caption("The AI analyzes UI elements, labels, and layout to generate more precise selectors.")
        screenshot = st.file_uploader("screenshot", type=["png","jpg","jpeg","webp"],
                                      label_visibility="collapsed", key="auto_ss")
        if screenshot:
            st.image(Image.open(screenshot), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 4 — Advanced options
    # ══════════════════════════════════════════════════════════════════════════
    styles.step_header("4", "Advanced Options")

    with st.expander("⚙️  Configure generation options", expanded=False):
        opt1, opt2, opt3 = st.columns(3)
        with opt1:
            st.markdown("**Test Options**")
            use_pom          = st.checkbox("Page Object Model",       value=True)
            add_comments     = st.checkbox("Inline comments",         value=True)
            include_negative = st.checkbox("Add negative scenario",   value=False)
        with opt2:
            st.markdown("**Locator Strategy**")
            pref_locators = st.multiselect(
                "Preferred Locators",
                LOCATOR_TYPES,
                default=["ID", "Data-TestID", "CSS Selector"],
                label_visibility="collapsed",
            )
            st.caption("Drag to reorder priority (top = highest priority)")
        with opt3:
            st.markdown("**Locator Reference**")
            for lt in LOCATOR_TYPES:
                tip = {
                    "ID":              "Most stable — `#submit-btn`",
                    "Data-TestID":     "Best practice — `[data-testid='btn']`",
                    "CSS Selector":    "Flexible — `.form .submit`",
                    "XPath":           "Powerful but brittle — use sparingly",
                    "Class Name":      "Simple — may not be unique",
                    "Link Text":       "For anchor tags only",
                    "Tag Name":        "Broad — best for tables/lists",
                    "Accessibility ID":"Ideal for mobile / a11y",
                }.get(lt, "")
                is_pref = lt in pref_locators
                color   = "#a78bfa" if is_pref else "#475569"
                check   = "✓ " if is_pref else "○ "
                tip_html = (
                    "  <span style='color:#64748b'>— " + tip + "</span>"
                    if tip else ""
                )
                row_html = (
                    f'<div style="padding:3px 0;color:{color};font-size:0.8rem">'
                    f'{check}<b>{lt}</b>{tip_html}'
                    f'</div>'
                )
                st.markdown(row_html, unsafe_allow_html=True)


        extra_notes = st.text_area(
            "Additional AI Instructions",
            placeholder="E.g. Use Allure annotations. Follow AAA pattern. Avoid XPath completely.",
            height=80,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # GENERATE
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    gen_col, _ = st.columns([2, 5])
    with gen_col:
        generate = st.button("⚡  Generate Automation Script", type="primary", use_container_width=True)

    if generate:
        if not tc_description.strip():
            st.warning("Please describe the test case first (Step 3)."); st.stop()

        client = shared.configure_model()

        full_desc = tc_description.strip()
        if use_pom:          full_desc += "\n[Constraint] Use Page Object Model."
        if add_comments:     full_desc += "\n[Constraint] Add inline comments per step."
        if include_negative: full_desc += "\n[Constraint] Include a negative / error-path scenario."
        if extra_notes.strip(): full_desc += f"\n[Extra] {extra_notes.strip()}"

        prompt = _build_prompt(
            framework=chosen_fw, description=full_desc,
            repo_context=st.session_state.repo_context,
            screenshot=screenshot is not None,
            preferred_locators=pref_locators,
        )

        with st.spinner(f"⚡  Generating {chosen_fw} script…"):
            try:
                parts = [prompt] + ([Image.open(screenshot)] if screenshot else [])
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=parts
                )
                script_text = response.text.strip()

                st.success("✅  Script generated successfully!")
                st.divider()

                lang  = FRAMEWORKS[chosen_fw]["language"]
                ext   = FRAMEWORKS[chosen_fw]["ext"]
                fname = (test_name.strip() or "generated_test") + f".{ext}"

                st.markdown(f"#### 📄 `{fname}` — {chosen_fw}")

                if "Cucumber" in chosen_fw:
                    blocks    = _split_cucumber(script_text)
                    tab_f, tab_s = st.tabs(["🥒  Feature File", "🔧  Step Definitions"])
                    with tab_f:
                        st.code(blocks["feature"], language="gherkin")
                        st.download_button("📥  Download .feature", blocks["feature"],
                                           file_name=fname, mime="text/plain")
                    with tab_s:
                        s_lang = "java" if "Java" in chosen_fw else "javascript"
                        s_ext  = "java" if "Java" in chosen_fw else "js"
                        st.code(blocks["steps"], language=s_lang)
                        st.download_button(f"📥  Download steps.{s_ext}", blocks["steps"],
                                           file_name=f"steps_{fname.replace('.feature','')}.{s_ext}",
                                           mime="text/plain")
                else:
                    clean = _extract_code(script_text)
                    st.code(clean, language=lang)
                    st.download_button(f"📥  Download {fname}", clean,
                                       file_name=fname, mime="text/plain")

                st.session_state.auto_history.append({
                    "framework": chosen_fw,
                    "description": tc_description[:120],
                    "script": script_text,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "repo": st.session_state.repo_label or "—",
                })

            except Exception as e:
                st.error(f"Generation failed: {e}")

    # ── Session history ────────────────────────────────────────────────────────
    if st.session_state.auto_history:
        st.divider()
        st.markdown("### 🕑 Recent Scripts")
        for item in reversed(st.session_state.auto_history[-5:]):
            with st.expander(
                f"**{item['framework']}** · {item['timestamp']} · Repo: {item['repo']}",
                expanded=False,
            ):
                st.caption(item["description"])
                lang = FRAMEWORKS.get(item["framework"], {}).get("language", "text")
                st.code(item["script"], language=lang)
