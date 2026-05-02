"""
pipeline_report_page.py — Allure Report Refinement
Parses Allure JSON result files (from a ZIP or individual uploads) and
produces a clean, debug-friendly Excel workbook with colour-coded sheets.
"""
import io
import json
import zipfile
import datetime

import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

import styles


# ── Constants ──────────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "passed":  {"bg": "D1FAE5", "fg": "065F46"},   # green
    "failed":  {"bg": "FEE2E2", "fg": "991B1B"},   # red
    "broken":  {"bg": "FEF3C7", "fg": "92400E"},   # amber
    "skipped": {"bg": "E0E7FF", "fg": "3730A3"},   # indigo
}

HEADER_PURPLE = "4F46E5"
WHITE = "FFFFFF"


# ── Allure JSON parsing ─────────────────────────────────────────────────────────
def _extract_label(labels: list, name: str) -> str:
    for lbl in labels:
        if lbl.get("name") == name:
            return lbl.get("value", "")
    return ""


def _ms_to_sec(ms: int | None) -> float:
    if ms is None:
        return 0.0
    return round(ms / 1000, 2)


def _parse_result(data: dict) -> dict:
    """Convert one Allure result JSON dict into a flat row."""
    status_details = data.get("statusDetails") or {}
    labels         = data.get("labels") or []
    start          = data.get("start")
    stop           = data.get("stop")
    duration_ms    = (stop - start) if (start and stop) else None

    return {
        "Test Name":     data.get("name", "—"),
        "Full Name":     data.get("fullName", "—"),
        "Status":        (data.get("status") or "unknown").lower(),
        "Suite":         _extract_label(labels, "suite") or _extract_label(labels, "parentSuite") or "—",
        "Feature":       _extract_label(labels, "feature") or "—",
        "Story":         _extract_label(labels, "story") or "—",
        "Severity":      _extract_label(labels, "severity") or "normal",
        "Duration (s)":  _ms_to_sec(duration_ms),
        "Error Message": (status_details.get("message") or "").strip()[:500],
        "Stack Trace":   (status_details.get("trace")   or "").strip()[:2000],
        "Start Time":    datetime.datetime.fromtimestamp(start  / 1000).strftime("%Y-%m-%d %H:%M:%S") if start else "—",
        "Stop Time":     datetime.datetime.fromtimestamp(stop   / 1000).strftime("%Y-%m-%d %H:%M:%S") if stop  else "—",
    }


def _load_json_files(files: list) -> list[dict]:
    """Parse a list of (filename, bytes) tuples into row dicts."""
    rows = []
    for fname, raw in files:
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "name" in data:
                rows.append(_parse_result(data))
        except Exception:
            pass
    return rows


def parse_uploads(uploaded_files) -> tuple[pd.DataFrame, list[str]]:
    """Accept Streamlit UploadedFile objects (JSON or ZIP). Returns (df, errors)."""
    file_pairs: list[tuple[str, bytes]] = []
    errors: list[str] = []

    for f in uploaded_files:
        name: str = f.name.lower()
        raw: bytes = f.read()
        if name.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for member in zf.namelist():
                        if member.endswith(".json") and not member.endswith("categories.json") \
                                and "environment" not in member:
                            file_pairs.append((member, zf.read(member)))
            except zipfile.BadZipFile:
                errors.append(f"⚠️  {f.name} is not a valid ZIP archive.")
        elif name.endswith(".json"):
            file_pairs.append((f.name, raw))
        else:
            errors.append(f"⚠️  {f.name} is not a .json or .zip file — skipped.")

    if not file_pairs:
        return pd.DataFrame(), errors

    rows = _load_json_files(file_pairs)
    if not rows:
        errors.append("No valid Allure result files were found inside the uploads.")
        return pd.DataFrame(), errors

    df = pd.DataFrame(rows)
    # Normalise status column
    df["Status"] = df["Status"].str.lower().str.strip()
    return df, errors


# ── Excel builder ───────────────────────────────────────────────────────────────
def _thin_border():
    s = Side(style="thin", color="D1D5DB")
    return Border(left=s, right=s, top=s, bottom=s)


def _style_header_row(ws, header_fill_hex: str = HEADER_PURPLE):
    hf   = PatternFill("solid", fgColor=header_fill_hex)
    hfnt = Font(color=WHITE, bold=True, size=10)
    aln  = Alignment(horizontal="center", vertical="center", wrap_text=True)
    brd  = _thin_border()
    for cell in ws[1]:
        cell.fill      = hf
        cell.font      = hfnt
        cell.alignment = aln
        cell.border    = brd


def _set_col_widths(ws, widths: dict):
    for col_letter, w in widths.items():
        ws.column_dimensions[col_letter].width = w


def _apply_data_styles(ws, df: pd.DataFrame, status_col_idx: int | None = None):
    brd  = _thin_border()
    wrap = Alignment(wrap_text=True, vertical="top")
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), start=2):
        for cell in row:
            cell.border    = brd
            cell.alignment = wrap
        if status_col_idx is not None:
            status_val = str(row[status_col_idx - 1].value or "").lower()
            colors     = STATUS_COLORS.get(status_val, {})
            if colors:
                row[status_col_idx - 1].fill = PatternFill("solid", fgColor=colors["bg"])
                row[status_col_idx - 1].font = Font(bold=True, color=colors["fg"])


def _add_summary_sheet(wb: Workbook, df: pd.DataFrame):
    ws = wb.create_sheet("📊 Summary", 0)
    ws.sheet_view.showGridLines = False
    ws.row_dimensions[1].height = 40

    # Title
    ws.merge_cells("A1:E1")
    title_cell = ws["A1"]
    title_cell.value     = "Allure Report — Execution Summary"
    title_cell.font      = Font(bold=True, size=14, color=WHITE)
    title_cell.fill      = PatternFill("solid", fgColor=HEADER_PURPLE)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Summary table headers
    headers = ["Status", "Count", "Percentage", "Avg Duration (s)", "Max Duration (s)"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=c, value=h)
        cell.fill      = PatternFill("solid", fgColor="1E1B4B")
        cell.font      = Font(color=WHITE, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border    = _thin_border()

    total = len(df)
    for r_offset, status in enumerate(["passed", "failed", "broken", "skipped"], start=4):
        sub    = df[df["Status"] == status]
        count  = len(sub)
        pct    = f"{round(count / total * 100, 1)}%" if total else "0%"
        avg_d  = round(sub["Duration (s)"].mean(), 2) if count else 0
        max_d  = round(sub["Duration (s)"].max(), 2)  if count else 0
        colors = STATUS_COLORS.get(status, {})

        row_data = [status.capitalize(), count, pct, avg_d, max_d]
        for c, val in enumerate(row_data, 1):
            cell = ws.cell(row=r_offset, column=c, value=val)
            cell.border    = _thin_border()
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if colors and c == 1:
                cell.fill = PatternFill("solid", fgColor=colors["bg"])
                cell.font = Font(bold=True, color=colors["fg"])

    # Totals row
    total_row = 4 + 4
    ws.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=total_row, column=2, value=total).font   = Font(bold=True)
    ws.cell(row=total_row, column=3, value="100%").font  = Font(bold=True)
    for c in range(1, 4):
        ws.cell(row=total_row, column=c).border    = _thin_border()
        ws.cell(row=total_row, column=c).alignment = Alignment(horizontal="center")

    # Column widths
    for col_l, w in zip(["A","B","C","D","E"], [20, 12, 16, 22, 22]):
        ws.column_dimensions[col_l].width = w

    # Bar chart
    chart = BarChart()
    chart.type    = "col"
    chart.title   = "Test Results"
    chart.y_axis.title = "Count"
    chart.x_axis.title = "Status"
    chart.style   = 10
    chart.width   = 18
    chart.height  = 12
    data = Reference(ws, min_col=2, min_row=3, max_row=7)
    cats = Reference(ws, min_col=1, min_row=4, max_row=7)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    ws.add_chart(chart, "G3")


def _add_full_sheet(wb: Workbook, df: pd.DataFrame, title: str,
                    sheet_name: str, header_color: str = HEADER_PURPLE,
                    exclude_cols: list[str] | None = None):
    show_df = df.copy()
    if exclude_cols:
        show_df = show_df.drop(columns=[c for c in exclude_cols if c in show_df.columns])

    ws = wb.create_sheet(sheet_name)
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"

    # Write header + data
    for c_idx, col in enumerate(show_df.columns, 1):
        ws.cell(row=1, column=c_idx, value=col)
    for r_idx, row in enumerate(show_df.itertuples(index=False), start=2):
        for c_idx, val in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)

    _style_header_row(ws, header_color)

    # Find Status column index
    try:
        status_col_idx = list(show_df.columns).index("Status") + 1
    except ValueError:
        status_col_idx = None

    _apply_data_styles(ws, show_df, status_col_idx)

    # Column widths
    widths = {
        "Test Name": 40, "Full Name": 40, "Status": 12, "Suite": 25,
        "Feature": 22, "Story": 22, "Severity": 12, "Duration (s)": 15,
        "Error Message": 55, "Stack Trace": 70, "Start Time": 22, "Stop Time": 22,
    }
    for c_idx, col in enumerate(show_df.columns, 1):
        w = widths.get(col, 18)
        ws.column_dimensions[get_column_letter(c_idx)].width = w

    ws.auto_filter.ref = ws.dimensions
    return ws


def build_report_excel(df: pd.DataFrame) -> bytes:
    """Build a multi-sheet styled Excel from the full Allure results DataFrame."""
    wb = Workbook()
    # Remove default blank sheet
    wb.remove(wb.active)

    # Sheet 1 — Summary
    _add_summary_sheet(wb, df)

    # Sheet 2 — Failed Tests (with full trace)
    failed = df[df["Status"] == "failed"].sort_values("Duration (s)", ascending=False)
    if not failed.empty:
        _add_full_sheet(wb, failed, "Failed Tests", "❌ Failed", header_color="991B1B")

    # Sheet 3 — Broken Tests
    broken = df[df["Status"] == "broken"].sort_values("Duration (s)", ascending=False)
    if not broken.empty:
        _add_full_sheet(wb, broken, "Broken Tests", "⚠️ Broken", header_color="92400E")

    # Sheet 4 — Skipped
    skipped = df[df["Status"] == "skipped"]
    if not skipped.empty:
        _add_full_sheet(wb, skipped, "Skipped", "⏭️ Skipped", header_color="3730A3",
                        exclude_cols=["Stack Trace"])

    # Sheet 5 — All Tests (without stack trace to keep it light)
    _add_full_sheet(wb, df.sort_values(["Status", "Suite"]), "All Tests",
                    "📋 All Tests", exclude_cols=["Stack Trace"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── Streamlit page renderer ─────────────────────────────────────────────────────
def render():
    styles.section_header(
        "🚀", "Pipeline Report Refinement",
        "Upload Allure result files or a ZIP archive — get a clean, debuggable Excel report instantly."
    )

    # ── Step 1: Upload ─────────────────────────────────────────────────────────
    styles.step_header("1", "Upload Allure Results")
    st.caption(
        "Supported: individual **`.json`** result files from `allure-results/` folder, "
        "or a **`.zip`** archive of the entire `allure-results/` directory."
    )

    uploaded = st.file_uploader(
        "Upload Allure Results",
        type=["json", "zip"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="allure_upload",
    )

    if not uploaded:
        st.markdown("""
        <div class="qa-card" style="text-align:center;padding:40px">
            <div style="font-size:3rem;margin-bottom:12px">📂</div>
            <div style="font-weight:700;color:#e2e8f0;margin-bottom:8px">No files uploaded yet</div>
            <div style="color:#64748b;font-size:0.88rem">
                Drag &amp; drop your <code>allure-results/*.json</code> files above,<br>
                or zip the entire <code>allure-results</code> folder and upload the ZIP.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Step 2: Parse ──────────────────────────────────────────────────────────
    styles.step_header("2", "Parse & Preview Results")

    with st.spinner("🔍  Parsing Allure result files…"):
        df, errors = parse_uploads(uploaded)

    for e in errors:
        st.warning(e)

    if df.empty:
        st.error("❌  No valid Allure result data found. Check that you uploaded the correct files.")
        return

    # ── Metrics row ────────────────────────────────────────────────────────────
    total   = len(df)
    passed  = len(df[df["Status"] == "passed"])
    failed  = len(df[df["Status"] == "failed"])
    broken  = len(df[df["Status"] == "broken"])
    skipped = len(df[df["Status"] == "skipped"])
    pass_rt = f"{round(passed / total * 100, 1)}%" if total else "—"

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("📋 Total",    total)
    m2.metric("✅ Passed",   passed)
    m3.metric("❌ Failed",   failed)
    m4.metric("⚠️ Broken",   broken)
    m5.metric("⏭️ Skipped",  skipped)
    m6.metric("🎯 Pass Rate", pass_rt)

    st.divider()

    # ── Filters ────────────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns(3)
    with f1:
        statuses   = ["All"] + sorted(df["Status"].unique().tolist())
        sel_status = st.selectbox("Filter Status", statuses)
    with f2:
        suites   = ["All"] + sorted(df["Suite"].unique().tolist())
        sel_suite = st.selectbox("Filter Suite", suites)
    with f3:
        features    = ["All"] + sorted(df["Feature"].unique().tolist())
        sel_feature = st.selectbox("Filter Feature", features)

    view = df.copy()
    if sel_status  != "All": view = view[view["Status"]  == sel_status]
    if sel_suite   != "All": view = view[view["Suite"]   == sel_suite]
    if sel_feature != "All": view = view[view["Feature"] == sel_feature]

    # Colour-code the status column display
    def _color_status(val):
        colors = {
            "passed":  "background-color:#D1FAE5;color:#065F46;font-weight:700",
            "failed":  "background-color:#FEE2E2;color:#991B1B;font-weight:700",
            "broken":  "background-color:#FEF3C7;color:#92400E;font-weight:700",
            "skipped": "background-color:#E0E7FF;color:#3730A3;font-weight:700",
        }
        return colors.get(str(val).lower(), "")

    display_cols = ["Test Name", "Suite", "Feature", "Status", "Severity",
                    "Duration (s)", "Error Message"]
    styled_view  = view[display_cols].style.applymap(_color_status, subset=["Status"])
    st.dataframe(styled_view, use_container_width=True, height=420)

    # ── Failed details expander ────────────────────────────────────────────────
    failed_df = df[df["Status"].isin(["failed", "broken"])]
    if not failed_df.empty:
        st.divider()
        styles.step_header("3", f"Debug Panel — {len(failed_df)} Failed / Broken Tests")
        for _, row in failed_df.iterrows():
            status_badge = "❌" if row["Status"] == "failed" else "⚠️"
            with st.expander(
                f"{status_badge} `{row['Test Name']}`  ·  Suite: **{row['Suite']}**  ·  {row['Duration (s)']}s",
                expanded=False,
            ):
                d1, d2, d3 = st.columns(3)
                d1.markdown(f"**Status:** `{row['Status']}`")
                d2.markdown(f"**Severity:** `{row['Severity']}`")
                d3.markdown(f"**Duration:** `{row['Duration (s)']}s`")

                st.markdown("**🔴 Error Message**")
                st.code(row["Error Message"] or "No message captured.", language="text")

                if row["Stack Trace"] and row["Stack Trace"].strip():
                    st.markdown("**📋 Stack Trace**")
                    st.code(row["Stack Trace"], language="text")

                st.caption(f"Full name: `{row['Full Name']}`  ·  Feature: `{row['Feature']}`")
    else:
        st.success("🎉 All tests passed! No failures to debug.")

    # ── Download ────────────────────────────────────────────────────────────────
    st.divider()
    styles.step_header("4" if failed_df.empty else "4", "Download Report")

    ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    fname = f"allure_report_{ts}.xlsx"

    with st.spinner("📊  Building Excel report…"):
        xlsx_bytes = build_report_excel(df)

    dl1, dl2, _ = st.columns([1, 1, 3])
    with dl1:
        st.download_button(
            "📥  Download Excel Report",
            data=xlsx_bytes,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
    with dl2:
        st.download_button(
            "📄  Download CSV",
            data=df.drop(columns=["Stack Trace"]).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name=fname.replace(".xlsx", ".csv"),
            mime="text/csv",
        )
    st.caption(
        "The Excel report contains 5 sheets: **Summary** (with bar chart), "
        "**❌ Failed**, **⚠️ Broken**, **⏭️ Skipped**, and **📋 All Tests**."
    )
