"""
in_sprint_page.py — In-Sprint Automation feature
Generates BOTH manual test cases and automation scripts simultaneously from a single ticket.
"""
import os
import json
import datetime
import streamlit as st
import pandas as pd
from google import genai

import styles
import automation_page
import shared

def render():
    styles.section_header(
        "🚀", "In-Sprint Automation",
        "Paste your current sprint ticket to instantly generate both manual test cases and the corresponding automation code."
    )

    # ── State ──────────────────────────────────────────────────────────────────
    for k, v in [("sprint_selected_fw", list(automation_page.FRAMEWORKS.keys())[0]),
                 ("repo_context", ""), ("repo_label", "")]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 1 — Framework selector
    # ══════════════════════════════════════════════════════════════════════════
    styles.step_header("1", "Choose Target Automation Framework")

    fw_names = list(automation_page.FRAMEWORKS.keys())
    row1, row2 = fw_names[:3], fw_names[3:]

    for row in [row1, row2]:
        cols = st.columns(3)
        for col, fw in zip(cols, row):
            meta     = automation_page.FRAMEWORKS[fw]
            selected = st.session_state.sprint_selected_fw == fw
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
                    key=f"sfw_{fw}",
                    use_container_width=True,
                    type="primary" if selected else "secondary",
                ):
                    st.session_state.sprint_selected_fw = fw
                    st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    chosen_fw = st.session_state.sprint_selected_fw

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 2 — Git project (Optional)
    # ══════════════════════════════════════════════════════════════════════════
    styles.step_header("2", "Link Your Git Project (optional)")
    st.caption("The AI will study your project's structure and generate code that matches your style exactly.")

    g_in, g_btn = st.columns([5, 1])
    with g_in:
        git_source = st.text_input(
            "repo_url", label_visibility="collapsed",
            placeholder="https://github.com/your-org/your-tests.git   or   C:/projects/my-tests",
            key="sprint_git_source"
        )
    with g_btn:
        load_repo = st.button("📂  Load", type="primary", use_container_width=True, key="sprint_load_repo")

    if load_repo and git_source.strip():
        with st.spinner("Loading project…"):
            exts = automation_page._detect_extensions(chosen_fw)
            src  = git_source.strip()
            import tempfile
            if os.path.isdir(src):
                files = automation_page._walk_files(src, exts)
                if files:
                    st.session_state.repo_context = automation_page._read_sample_files(files[:20])
                    st.session_state.repo_label   = os.path.basename(src)
                    st.success(f"✅  Loaded {len(files)} files from local folder.")
                else:
                    st.warning("No matching files found for this framework.")
            elif src.startswith(("http://", "https://", "git@")):
                tmp = os.path.join(tempfile.gettempdir(), "qa_assist_repo_sprint")
                ok, msg = automation_page._clone_or_pull(src, tmp)
                if ok:
                    files = automation_page._walk_files(tmp, exts)
                    st.session_state.repo_context = automation_page._read_sample_files(files[:20])
                    st.session_state.repo_label   = src.split("/")[-1].replace(".git","")
                    st.success(f"✅  Cloned and loaded {len(files)} files.")
                else:
                    st.error(f"Clone failed: {msg}")
            else:
                st.warning("Enter a valid Git URL or local folder path.")

    if st.session_state.repo_context:
        with st.expander(f"📁  Project loaded: **{st.session_state.repo_label}**"):
            st.code(st.session_state.repo_context[:4000], language="text")
        if st.button("✕  Clear project", type="secondary", key="sprint_clear_proj"):
            st.session_state.repo_context = ""
            st.session_state.repo_label   = ""
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # STEP 3 — Ticket Details
    # ══════════════════════════════════════════════════════════════════════════
    styles.step_header("3", "Sprint Ticket Details")

    top_l, top_r = st.columns([1.4, 1])
    with top_l:
        ticket_name = st.text_input("Ticket / Feature Name", placeholder="e.g. PROJ-123 – User Login with OTP")
        requirements = st.text_area(
            "Requirements / Acceptance Criteria",
            placeholder=(
                "As a user, I want to log in with my email and OTP so that...\n"
                "Acceptance criteria:\n"
                "- Valid OTP logs the user in\n"
                "- Expired OTP shows error message\n"
                "- 3 failed attempts lock the account for 10 minutes"
            ),
            height=240,
        )

    with top_r:
        st.markdown("**Test Options**")
        use_pom          = st.checkbox("Page Object Model",       value=True, key="sprint_pom")
        add_comments     = st.checkbox("Inline comments",         value=True, key="sprint_com")
        include_negative = st.checkbox("Add negative scenario",   value=True, key="sprint_neg")
        pref_locators = st.multiselect(
            "Preferred Locators",
            automation_page.LOCATOR_TYPES,
            default=["ID", "Data-TestID", "CSS Selector"],
            key="sprint_loc"
        )
        extra_notes = st.text_area(
            "Additional Automation Instructions",
            placeholder="E.g. Avoid XPath completely.",
            height=60,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    gen_col, _ = st.columns([2, 5])
    with gen_col:
        generate = st.button("⚡  Generate Both Manual & Auto", type="primary", use_container_width=True)

    if generate:
        if not requirements.strip():
            st.warning("Please enter the ticket requirements first.")
            st.stop()

        client = shared.configure_model()

        # Build Prompts
        manual_prompt = (shared.BASE_PROMPT 
                        + f"\n\nTicket / Feature: {ticket_name or 'Not specified'}"
                        + f"\n\nRequirements:\n{requirements.strip()}")

        auto_desc = requirements.strip()
        if use_pom:          auto_desc += "\n[Constraint] Use Page Object Model."
        if add_comments:     auto_desc += "\n[Constraint] Add inline comments per step."
        if include_negative: auto_desc += "\n[Constraint] Include a negative / error-path scenario."
        if extra_notes.strip(): auto_desc += f"\n[Extra] {extra_notes.strip()}"

        auto_prompt = automation_page._build_prompt(
            framework=chosen_fw, description=auto_desc,
            repo_context=st.session_state.repo_context,
            screenshot=False, preferred_locators=pref_locators
        )

        # Make API Calls
        col_man, col_auto = st.columns(2)

        with col_man:
            st.markdown("### 📝 Manual Test Cases")
            with st.spinner("Generating Manual Test Cases..."):
                try:
                    res_man = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[manual_prompt]
                    )
                    test_cases = shared.parse_response(res_man.text)
                    if test_cases:
                        df = pd.DataFrame(test_cases)
                        shared.show_results(df, f"tc_{ticket_name or 'sprint'}.xlsx")
                        # Add to history
                        st.session_state.history.append({
                            "source": "🚀 In-Sprint", "name": ticket_name or "Untitled", "df": df,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "user": st.session_state.username,
                        })
                    else:
                        st.warning("No manual test cases were generated.")
                except Exception as e:
                    st.error(f"Failed to generate manual tests: {e}")

        with col_auto:
            st.markdown(f"### 🤖 Automation ({chosen_fw})")
            with st.spinner("Generating Automation Script..."):
                try:
                    res_auto = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[auto_prompt]
                    )
                    script_text = res_auto.text.strip()
                    lang  = automation_page.FRAMEWORKS[chosen_fw]["language"]
                    ext   = automation_page.FRAMEWORKS[chosen_fw]["ext"]
                    fname = (ticket_name.strip() or "sprint_test").replace(" ", "_") + f".{ext}"

                    if "Cucumber" in chosen_fw:
                        blocks = automation_page._split_cucumber(script_text)
                        tab_f, tab_s = st.tabs(["🥒  Feature File", "🔧  Step Definitions"])
                        with tab_f:
                            st.code(blocks["feature"], language="gherkin")
                            st.download_button("📥  Download .feature", blocks["feature"],
                                            file_name=fname, mime="text/plain", key="dl_f")
                        with tab_s:
                            s_lang = "java" if "Java" in chosen_fw else "javascript"
                            s_ext  = "java" if "Java" in chosen_fw else "js"
                            st.code(blocks["steps"], language=s_lang)
                            st.download_button(f"📥  Download steps.{s_ext}", blocks["steps"],
                                            file_name=f"steps_{fname.replace('.feature','')}.{s_ext}",
                                            mime="text/plain", key="dl_s")
                    else:
                        clean = automation_page._extract_code(script_text)
                        st.code(clean, language=lang)
                        st.download_button(f"📥  Download {fname}", clean,
                                        file_name=fname, mime="text/plain", key="dl_clean")

                    st.session_state.auto_history.append({
                        "framework": chosen_fw,
                        "description": requirements[:120],
                        "script": script_text,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "repo": st.session_state.repo_label or "—",
                    })

                except Exception as e:
                    st.error(f"Failed to generate automation script: {e}")
