"""
QA Assist — Production-ready Streamlit application
AI-powered test case generation & automation script generator.
"""
import os
import hashlib
import datetime
import io
import json

import streamlit as st
import pandas as pd
from google import genai
from PIL import Image
from dotenv import load_dotenv
load_dotenv()

from shared import configure_model, parse_response, show_results, BASE_PROMPT
import styles
import automation_page
import pipeline_report_page
import in_sprint_page

# ── Bootstrap ──────────────────────────────────────────────────────────────────
API_KEY = os.getenv("GOOGLE_API_KEY", "")
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

st.set_page_config(
    page_title="QA Assist",
    page_icon="🐞",
    layout="wide",
    initial_sidebar_state="expanded",
)
styles.inject()


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@st.cache_data
def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
            # Migration: Ensure admin is always approved
            if "admin" in users and not users["admin"].get("approved"):
                users["admin"]["approved"] = True
            return users
    default = {
        "admin": {
            "password_hash": hash_password("admin123"),
            "full_name": "Administrator",
            "created_at": datetime.datetime.now().isoformat(),
            "sessions": 0,
            "approved": True,
        }
    }
    # Skip save_users here to avoid recursion/cache-clear loop on init
    with open(USERS_FILE, "w") as f:
        json.dump(default, f, indent=2)
    return default


def save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)
    load_users.clear()


def authenticate(username: str, password: str, users: dict) -> tuple[bool, str]:
    if username not in users:
        return False, "Invalid username or password."
    if users[username]["password_hash"] != hash_password(password):
        return False, "Invalid username or password."
    if not users[username].get("approved", False):
        return False, "Your account is pending approval by an admin."
    return True, "Login successful."


def register(username: str, password: str, full_name: str, users: dict):
    if not username or not password:
        return False, "Username and password are required."
    if username in users:
        return False, "Username already exists."
    users[username] = {
        "password_hash": hash_password(password),
        "full_name": full_name or username,
        "created_at": datetime.datetime.now().isoformat(),
        "sessions": 0,
        "approved": False,
    }
    save_users(users)
    return True, "Account created! Please wait for an admin to approve your access."


# ── Session state defaults ─────────────────────────────────────────────────────
for key, val in [("logged_in", False), ("username", ""), ("full_name", ""),
                  ("history", []), ("reg_flash", None)]:
    if key not in st.session_state:
        st.session_state[key] = val


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN / REGISTER GATE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center;padding:3rem 0 1rem">
        <div style="font-size:3rem;margin-bottom:12px">🐞</div>
        <h1 style="background:linear-gradient(135deg,#a78bfa,#67e8f9);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   font-size:2.4rem!important;margin:0">QA Assist</h1>
        <p style="color:#64748b;margin-top:8px;font-size:1rem">
            AI-powered test case generation & automation
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.2, 1])
    with center:

        # ── Flash message after registration (shown above tabs, cleared after) ──
        if st.session_state.reg_flash:
            st.success(st.session_state.reg_flash)
            st.session_state.reg_flash = None

        auth_tab, reg_tab = st.tabs(["🔐  Login", "📝  Register"])
        users = load_users()

        with auth_tab:
            with st.form("login_form"):
                username  = st.text_input("Username", placeholder="Enter your username")
                password  = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Login →", type="primary", use_container_width=True)
            if submitted:
                ok, msg = authenticate(username, password, users)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username   = username
                    st.session_state.full_name  = users[username]["full_name"]
                    users[username]["sessions"] += 1
                    save_users(users)
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            st.caption("Default → username: `admin`  ·  password: `admin123`")

        with reg_tab:
            with st.form("register_form"):
                new_full  = st.text_input("Full Name",        placeholder="e.g. Aryan Singhal")
                new_user  = st.text_input("Username",         placeholder="choose a username")
                new_pass  = st.text_input("Password",         type="password", placeholder="choose a password")
                new_pass2 = st.text_input("Confirm Password", type="password", placeholder="repeat password")
                reg_sub   = st.form_submit_button("Create Account →", type="primary", use_container_width=True)
            if reg_sub:
                if new_pass != new_pass2:
                    st.error("❌ Passwords do not match.")
                else:
                    ok, msg = register(new_user, new_pass, new_full, users)
                    if ok:
                        # Store message and rerun → form fields clear automatically
                        st.session_state.reg_flash = f"✅ {msg}"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
if "_redirect" in st.session_state:
    st.session_state.nav_page = st.session_state.pop("_redirect")

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div style="font-size:1.8rem">🐞</div>
        <h1>QA Assist</h1>
        <p style="color:#64748b;font-size:0.75rem;margin:4px 0 0">AI-Powered Quality Engineering</p>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "🏠  Dashboard",
        "📸  From Screenshot",
        "📝  From Requirements",
        "🤖  Automation Scripts",
        "🚀  In-Sprint Automation",
        "📈  Pipeline Report",
        "📊  Test History",
    ]
    if st.session_state.username == "admin":
        nav_options.append("👥  Users")

    page = st.radio(
        "nav",
        nav_options,
        label_visibility="collapsed",
        key="nav_page",
    )

    st.divider()

    st.markdown(f"""
    <div class="user-card">
        <div style="font-weight:700;color:#e2e8f0;font-size:0.95rem">👤 {st.session_state.full_name}</div>
        <div style="color:#64748b;font-size:0.8rem">@{st.session_state.username}</div>
    </div>
    """, unsafe_allow_html=True)

    # Read live values from persistent store so sidebar is always accurate
    _users_live   = load_users()
    _login_count  = _users_live.get(st.session_state.username, {}).get("sessions", 0)
    _tc_count     = sum(len(h["df"]) for h in st.session_state.history)

    s1, s2 = st.columns(2)
    s1.metric("🔑 Total Logins", _login_count)
    s2.metric("🧪 TCs Made",     _tc_count)


    st.divider()
    if st.button("🚪  Logout", use_container_width=True, type="secondary"):
        for k in ["logged_in", "username", "full_name", "history"]:
            st.session_state[k] = False if k == "logged_in" else ([] if k == "history" else "")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Dashboard":
    styles.section_header("🏠", "Dashboard", f"Welcome back, {st.session_state.full_name}!")

    history    = st.session_state.history
    total_tc   = sum(len(h["df"]) for h in history)
    high_count = sum(len(h["df"][h["df"]["Priority"] == "High"]) for h in history)

    styles.metric_row([
        {"label": "Sessions this login",    "value": len(history)},
        {"label": "Test Cases Generated",   "value": total_tc},
        {"label": "🔴 High Priority Cases", "value": high_count},
    ])

    st.divider()
    st.markdown("### 🚀 Quick Start")

    q1, q2, q3 = st.columns(3)
    cards = [
        ("📸", "From Screenshot",   "Upload any UI screenshot — Gemini Vision analyzes it and generates full test cases automatically.",   "📸  From Screenshot"),
        ("📝", "From Requirements", "Paste ticket text, user stories, or acceptance criteria and get structured test cases instantly.",      "📝  From Requirements"),
        ("🤖", "Automation Scripts","Link your Git repo, upload a screenshot, and generate Selenium / Playwright / WDIO / Cucumber scripts.","🤖  Automation Scripts"),
    ]
    for col, (icon, title, body, dest) in zip([q1, q2, q3], cards):
        with col:
            styles.info_card(icon, title, body)
            if st.button(f"Open →", key=f"qs_{dest}", use_container_width=True):
                st.session_state._redirect = dest
                st.rerun()

    if history:
        st.divider()
        st.markdown("### 🕑 Recent Sessions")
        for h in reversed(history[-5:]):
            with st.expander(f"{h['source']}  ·  **{h['name']}**  ·  {h['timestamp']}  ({len(h['df'])} cases)"):
                st.dataframe(h["df"], use_container_width=True, height=200)


elif page == "📈  Pipeline Report":
    pipeline_report_page.render()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: FROM SCREENSHOT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📸  From Screenshot":
    styles.section_header("📸", "Generate from Screenshot",
                          "Upload any UI / ticket / wireframe screenshot — Gemini Vision will analyze it and produce test cases.")

    up_col, ctx_col = st.columns([1.2, 1])

    with up_col:
        uploaded_file = st.file_uploader("Upload UI Screenshot", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_file:
            st.image(Image.open(uploaded_file), caption="Uploaded Screenshot", use_container_width=True)

    with ctx_col:
        extra = st.text_area(
            "Additional Context (optional)",
            placeholder="E.g. 'This is the checkout page. Focus on payment validation and error messages.'",
            height=160,
        )
        st.caption("💡 Adding context helps the AI generate more targeted test cases.")
        gen_btn = st.button("🔍  Generate Test Cases", type="primary", use_container_width=True,
                            disabled=(uploaded_file is None))

    if gen_btn and uploaded_file:
        image = Image.open(uploaded_file)
        client = configure_model()
        with st.spinner("🔍  Analyzing screenshot with Gemini Vision…"):
            try:
                prompt = BASE_PROMPT + (f"\n\nAdditional context:\n{extra.strip()}" if extra.strip() else "")
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[prompt, image]
                )
                test_cases = parse_response(response.text)
                if not test_cases:
                    st.warning("No test cases generated. Try adding more context.")
                else:
                    df = pd.DataFrame(test_cases)
                    show_results(df, f"tc_{uploaded_file.name}.xlsx")
                    st.session_state.history.append({
                        "source": "📸 Screenshot", "name": uploaded_file.name, "df": df,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "user": st.session_state.username,
                    })
            except json.JSONDecodeError:
                st.error("⚠️ AI returned an unexpected format. Please try again.")
            except Exception as e:
                st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: FROM REQUIREMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📝  From Requirements":
    styles.section_header("📝", "Generate from Requirements",
                          "Paste your ticket, user story, or acceptance criteria — get a full structured test suite instantly.")

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
        focus = st.multiselect(
            "Focus Areas",
            ["Functional", "Security", "Performance", "Accessibility", "Mobile", "API"],
            default=["Functional"],
        )
        env = st.selectbox("Target Environment", ["Web", "Mobile (iOS)", "Mobile (Android)", "API / Backend"])
        st.markdown("<br>", unsafe_allow_html=True)
        gen_req = st.button("🔍  Generate Test Cases", type="primary", use_container_width=True)

    if gen_req:
        if not requirements.strip():
            st.warning("Please enter some requirements first.")
        else:
            client = configure_model()
            with st.spinner("⚙️  Generating test cases from requirements…"):
                try:
                    extra_instr = ""
                    if focus:
                        extra_instr += f"\nFocus areas: {', '.join(focus)}."
                    extra_instr += f"\nTarget environment: {env}."
                    prompt = (BASE_PROMPT + extra_instr
                              + f"\n\nTicket / Feature: {ticket_name or 'Not specified'}"
                              + f"\n\nRequirements:\n{requirements.strip()}")
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt]
                    )
                    test_cases = parse_response(response.text)
                    if not test_cases:
                        st.warning("No test cases generated. Try expanding your requirements.")
                    else:
                        df   = pd.DataFrame(test_cases)
                        name = ticket_name.strip() or "requirements"
                        show_results(df, f"tc_{name}.xlsx")
                        st.session_state.history.append({
                            "source": "📝 Requirements", "name": ticket_name or "Untitled", "df": df,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "user": st.session_state.username,
                        })
                except json.JSONDecodeError:
                    st.error("⚠️ AI returned an unexpected format. Please try again.")
                except Exception as e:
                    st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: AUTOMATION SCRIPTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🤖  Automation Scripts":
    automation_page.render()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: IN-SPRINT AUTOMATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚀  In-Sprint Automation":
    in_sprint_page.render()

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: TEST HISTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊  Test History":
    styles.section_header("📊", "Test History", "All test suites generated in this session.")

    history = st.session_state.history
    if not history:
        st.info("No test cases generated yet. Head to **📸 From Screenshot** or **📝 From Requirements** to get started.")
    else:
        total_tc = sum(len(h["df"]) for h in history)
        styles.metric_row([
            {"label": "Sessions",          "value": len(history)},
            {"label": "Total Test Cases",  "value": total_tc},
            {"label": "Avg Cases/Session", "value": round(total_tc / len(history), 1)},
        ])

        st.divider()
        cl, _ = st.columns([1, 5])
        with cl:
            if st.button("🗑️  Clear All", type="secondary"):
                st.session_state.history = []
                st.rerun()

        for i, h in enumerate(reversed(history)):
            idx = len(history) - 1 - i
            with st.expander(f"**{h['source']}** · {h['name']} · {h['timestamp']} · {len(h['df'])} cases",
                             expanded=(i == 0)):
                show_results(h["df"], f"tc_{h['name'].replace(' ','_')}.xlsx")
                if st.button("🗑️ Remove", key=f"del_{idx}", type="secondary"):
                    st.session_state.history.pop(idx)
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: USERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥  Users":
    if st.session_state.username != "admin":
        st.error("🚫 Access Denied. Admin privileges required.")
        st.stop()
        
    styles.section_header("👥", "User Management", "Manage accounts and update your credentials.")

    users = load_users()
    rows  = [{"Username": u, "Full Name": d.get("full_name","—"),
              "Status": "✅ Approved" if d.get("approved") else "⏳ Pending",
              "Total Logins": d.get("sessions",0), "Created": d.get("created_at","—")[:10]}
             for u, d in users.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.divider()
    
    # ── Approval Section ──
    pending = [u for u, d in users.items() if not d.get("approved")]
    if pending:
        st.markdown("#### ⏳ Pending Approvals")
        for u in pending:
            col_u, col_a = st.columns([3, 1])
            with col_u:
                st.markdown(f"**{users[u]['full_name']}** (@{u})")
            with col_a:
                if st.button(f"Approve", key=f"app_{u}"):
                    users[u]["approved"] = True
                    save_users(users)
                    st.success(f"User `{u}` approved!")
                    st.rerun()
        st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("#### 🔑 Change My Password")
        with st.form("change_pw"):
            old_p  = st.text_input("Current Password",      type="password")
            new_p1 = st.text_input("New Password",          type="password")
            new_p2 = st.text_input("Confirm New Password",  type="password")
            if st.form_submit_button("Update Password", type="primary"):
                me = st.session_state.username
                ok, msg = authenticate(me, old_p, users)
                if not ok:
                    st.error(msg)
                elif new_p1 != new_p2:
                    st.error("New passwords do not match.")
                elif len(new_p1) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    users[me]["password_hash"] = hash_password(new_p1)
                    save_users(users)
                    st.success("✅ Password updated!")

    with right:
        if st.session_state.username == "admin":
            st.markdown("#### 🗑️ Delete User (Admin Only)")
            deletable = [u for u in users if u != "admin"]
            if deletable:
                del_user = st.selectbox("Select user", deletable)
                if st.button("Delete User", type="secondary"):
                    del users[del_user]
                    save_users(users)
                    st.success(f"User `{del_user}` deleted.")
                    st.rerun()
            else:
                st.info("No other users to delete.")
