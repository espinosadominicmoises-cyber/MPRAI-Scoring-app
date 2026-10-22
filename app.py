import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import io
import json
import streamlit.components.v1 as components

st.set_page_config(page_title="IPSC Match Scoring System", layout="wide")

# ==========================================
# BROWSER REFRESH / CLOSE CONFIRMATION PROMPT
# ==========================================
components.html(
    """
    <script>
    window.addEventListener('beforeunload', function (e) {
        e.preventDefault();
        e.returnValue = '';
    });
    </script>
    """,
    height=0,
)

# ==========================================
# SIDEBAR: MATCH SETUP & CONFIGURATION
# ==========================================
st.sidebar.header("⚙️ Match Configuration")

match_name = st.sidebar.text_input("Match Name", value="MPRAI CLUBSHOOT")
match_date = st.sidebar.date_input("Match Date", value=date.today())

division = st.sidebar.selectbox(
    "Division",
    ["Production", "Production Optics", "Standard", "Standard Optics", "Classic", "Open", "Revolver", "PCC"]
)

# Auto-set Power Factor rule per Division
if division in ["Production", "Production Optics", "PCC"]:
    st.sidebar.info(f"ℹ️ {division} is restricted to **Minor** scoring.")
    default_power_options = ["Minor"]
else:
    default_power_options = ["Major", "Minor"]

num_stages = st.sidebar.number_input("How many stages?", min_value=1, max_value=20, value=1)

# Custom Stage Names & Targets
st.sidebar.header("📋 Stage Names & Targets")
stage_names = []
stage_config = {}

for s in range(1, int(num_stages) + 1):
    default_title = f"Stage {s}"
    with st.sidebar.expander(f"Stage {s} Setup", expanded=(s == 1)):
        custom_s_name = st.text_input(f"Stage {s} Title", value=default_title, key=f"s_name_{s}")
        paper = st.number_input(f"Paper Targets", min_value=0, value=0, key=f"p_{s}")
        steel = st.number_input(f"Steel Plates & Poppers", min_value=0, value=0, key=f"st_{s}")
        
        max_stage_points = (paper * 2 + steel) * 5
        total_rounds = (paper * 2) + steel
        stage_names.append(custom_s_name)
        stage_config[custom_s_name] = {
            "paper": paper,
            "steel": steel,
            "max_pts": max_stage_points,
            "total_rounds": total_rounds
        }
        st.caption(f"Max Points: **{max_stage_points} pts** | Total Rounds: **{total_rounds}**")

# ==========================================
# DATA PERSISTENCE (SAVE / LOAD MATCH)
# ==========================================
st.sidebar.divider()
st.sidebar.header("💾 Match Data Persistence")

if "competitors_list" not in st.session_state:
    st.session_state.competitors_list = []
if "scores" not in st.session_state:
    st.session_state.scores = {}

# Export Match State
match_state_data = {
    "match_name": match_name,
    "division": division,
    "competitors": st.session_state.competitors_list,
    "scores": {f"{k[0]}|||{k[1]}": v for k, v in st.session_state.scores.items()}
}
st.sidebar.download_button(
    label="📥 Save Match State (JSON)",
    data=json.dumps(match_state_data, indent=4),
    file_name=f"{match_name}_{division}_backup.json",
    mime="application/json"
)

# Import Match State
uploaded_file = st.sidebar.file_uploader("📂 Load Match State (JSON)", type=["json"])
if uploaded_file is not None:
    try:
        loaded_data = json.load(uploaded_file)
        st.session_state.competitors_list = loaded_data.get("competitors", [])
        raw_scores = loaded_data.get("scores", {})
        
        parsed_scores = {}
        for k, v in raw_scores.items():
            if "|||" in k:
                s_name, comp_name = k.split("|||", 1)
                parsed_scores[(s_name, comp_name)] = v
        st.session_state.scores = parsed_scores
        st.sidebar.success("Match state loaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")

# ==========================================
# MAIN APP HEADER
# ==========================================
st.title(f"🎯 {match_name if match_name else 'IPSC Match Scoring'}")
st.caption(f"Date: {match_date.strftime('%B %d, %Y')} | Division: **{division}**")

# ==========================================
# TOP-LEVEL NAVIGATION TABS
# ==========================================
main_tab_roster, main_tab_scoring = st.tabs(["👤 Competitor Roster", "🎯 Match Scoring & Results"])

# ------------------------------------------
# TAB 1: COMPETITOR ROSTER MANAGEMENT
# ------------------------------------------
with main_tab_roster:
    st.header("👤 Competitor Roster Management")

    cat_options = ["", "L", "LS", "S", "SS", "GS", "J", "SJ"]
    cls_options = ["", "GM", "M", "A", "B", "C", "D", "U"]

    col_add, col_edit = st.columns(2)

    with col_add:
        with st.expander("➕ Add New Competitor", expanded=True):
            with st.form("add_competitor_form", clear_on_submit=True):
                c_name = st.text_input("Competitor Name", value="")
                c_cat = st.selectbox("Cat", cat_options, key="add_cat")
                c_reg = st.text_input("Reg", value="PHI")
                c_cls = st.selectbox("Cls", cls_options, key="add_cls")
                c_tag = st.text_input("Tag", value="")
                c_ics = st.text_input("ICS", value="")
                c_power = st.selectbox("Power", default_power_options, key="add_power")
                c_dq = st.checkbox("Disqualified (DQ)", value=False, key="add_dq")
                
                submit_comp = st.form_submit_button("➕ Add Competitor")
                if submit_comp and c_name:
                    next_id = len(st.session_state.competitors_list) + 1
                    st.session_state.competitors_list.append({
                        "#": next_id, "Competitor": c_name, "Cat": c_cat, 
                        "Reg": c_reg, "Cls": c_cls, "Tag": c_tag, "ICS": c_ics, "Power": c_power, "DQ": c_dq
                    })
                    st.success(f"Added {c_name} successfully!")
                    st.rerun()

    with col_edit:
        with st.expander("✏️ Edit or Delete Competitor", expanded=False):
            if st.session_state.competitors_list:
                comp_names = [c["Competitor"] for c in st.session_state.competitors_list]
                selected_to_edit = st.selectbox("Select Competitor to Edit/Delete", options=comp_names, key="select_edit_comp")
                
                current_data = next(c for c in st.session_state.competitors_list if c["Competitor"] == selected_to_edit)
                
                with st.form("edit_delete_form"):
                    e_name = st.text_input("Competitor Name", value=current_data["Competitor"])
                    e_cat = st.selectbox("Cat", cat_options, index=cat_options.index(current_data["Cat"]) if current_data["Cat"] in cat_options else 0, key="edit_cat")
                    e_reg = st.text_input("Reg", value=current_data["Reg"])
                    e_cls = st.selectbox("Cls", cls_options, index=cls_options.index(current_data["Cls"]) if current_data["Cls"] in cls_options else 0, key="edit_cls")
                    e_tag = st.text_input("Tag", value=current_data["Tag"])
                    e_ics = st.text_input("ICS", value=current_data["ICS"])
                    e_power = st.selectbox("Power", default_power_options, index=default_power_options.index(current_data["Power"]) if current_data["Power"] in default_power_options else 0, key="edit_power")
                    e_dq = st.checkbox("Disqualified (DQ)", value=bool(current_data.get("DQ", False)), key="edit_dq")
                    
                    b_col1, b_col2 = st.columns(2)
                    save_changes = b_col1.form_submit_button("💾 Save Changes")
                    delete_shooter = b_col2.form_submit_button("🗑️ Delete Competitor")
                    
                    if save_changes:
                        current_data["Competitor"] = e_name
                        current_data["Cat"] = e_cat
                        current_data["Reg"] = e_reg
                        current_data["Cls"] = e_cls
                        current_data["Tag"] = e_tag
                        current_data["ICS"] = e_ics
                        current_data["Power"] = e_power
                        current_data["DQ"] = e_dq
                        st.success("Competitor updated successfully!")
                        st.rerun()
                        
                    if delete_shooter:
                        st.session_state.competitors_list = [c for c in st.session_state.competitors_list if c["Competitor"] != selected_to_edit]
                        for idx, c in enumerate(st.session_state.competitors_list, 1):
                            c["#"] = idx
                        st.session_state.scores = {k: v for k, v in st.session_state.scores.items() if k[1] != selected_to_edit}
                        st.warning(f"Deleted {selected_to_edit}!")
                        st.rerun()
            else:
                st.info("No competitors available to edit.")

    st.markdown("### 📋 Official Roster Summary")
    if st.session_state.competitors_list:
        df_roster = pd.DataFrame(st.session_state.competitors_list)
        st.dataframe(df_roster, hide_index=True, use_container_width=True)
    else:
        st.warning("No competitors in roster yet. Add one above to begin.")

# ------------------------------------------
# TAB 2: STAGE SCOREBOARDS & OVERALL STANDINGS
# ------------------------------------------
with main_tab_scoring:
    tabs = stage_names + ["Overall Standings"]
    tab_objects = st.tabs(tabs)

    overall_match_points = {c['Competitor']: 0.0 for c in st.session_state.competitors_list}

    for i, s_name in enumerate(stage_names):
        with tab_objects[i]:
            st.subheader(f"{s_name} Scoreboard")
            cfg = stage_config[s_name]
            total_rounds = cfg['total_rounds']
            st.info(f"Targets: **{cfg['paper']} Paper** ({cfg['paper']*2} shots) | **{cfg['steel']} Steel** ({cfg['steel']} shots) | Total Required Rounds: **{total_rounds}** | Max Points: **{cfg['max_pts']}**")
            
            active_competitors = [c for c in st.session_state.competitors_list if not c['DQ']]

            if not active_competitors:
                st.warning("No active (non-DQ) competitors available.")
                continue

            selected_shooter = st.selectbox("Select Competitor to Enter Score", options=[c['Competitor'] for c in active_competitors], key=f"select_{s_name}")
            shooter_info = next(c for c in active_competitors if c['Competitor'] == selected_shooter)
            pf = shooter_info['Power']

            existing_score = st.session_state.scores.get((s_name, selected_shooter), {})

            with st.form(f"score_form_{s_name}_{selected_shooter}"):
                st.markdown(f"**Scoring for: {selected_shooter} ({pf})**")
                
                f_col1, f_col2 = st.columns(2)
                c_status = f_col1.selectbox("Stage Status", options=["Scored", "Did Not Finish (DNF)"], index=1 if existing_score.get("DNF", False) else 0, key=f"status_{s_name}_{selected_shooter}")
                raw_time = f_col2.number_input("Time (s)", min_value=0.0, value=float(existing_score.get("time", 0.0)), format="%.2f", key=f"time_{s_name}_{selected_shooter}")

                # --- Section 1: Scoring ---
                st.markdown("##### 🎯 Scoring")
                sc1, sc2, sc3, sc4 = st.columns(4)
                
                max_steel = max(0, cfg['steel'])
                max_paper_shots = cfg['paper'] * 2

                plates = sc1.number_input(
                    "Steel Hits", 
                    min_value=0, 
                    max_value=max_steel, 
                    value=min(int(existing_score.get("steel", 0)), max_steel), 
                    disabled=(max_steel == 0),
                    key=f"st_{s_name}_{selected_shooter}"
                )
                
                alpha = sc2.number_input(
                    "Alpha (A)", 
                    min_value=0, 
                    max_value=max_paper_shots, 
                    value=min(int(existing_score.get("A", 0)), max_paper_shots), 
                    disabled=(max_paper_shots == 0),
                    key=f"a_{s_name}_{selected_shooter}"
                )

                charlie = sc3.number_input(
                    "Charlie (C)", 
                    min_value=0, 
                    max_value=max_paper_shots, 
                    value=min(int(existing_score.get("C", 0)), max_paper_shots), 
                    disabled=(max_paper_shots == 0),
                    key=f"c_{s_name}_{selected_shooter}"
                )

                delta = sc4.number_input(
                    "Delta (D)", 
                    min_value=0, 
                    max_value=max_paper_shots, 
                    value=min(int(existing_score.get("D", 0)), max_paper_shots), 
                    disabled=(max_paper_shots == 0),
                    key=f"d_{s_name}_{selected_shooter}"
                )

                # --- Section 2: Penalties ---
                st.markdown("##### ⚠️ Penalties")
                p1, p2, p3, p4 = st.columns(4)

                mike = p1.number_input(
                    "Mike (M)", 
                    min_value=0, 
                    max_value=total_rounds, 
                    value=min(int(existing_score.get("M", 0)), total_rounds), 
                    disabled=(total_rounds == 0),
                    key=f"m_{s_name}_{selected_shooter}"
                )

                no_shoot = p2.number_input("No-Shoot (NS)", min_value=0, value=int(existing_score.get("NS", 0)), key=f"ns_{s_name}_{selected_shooter}")
                fte = p3.number_input("Failure to Engage (FTE)", min_value=0, value=int(existing_score.get("FTE", 0)), key=f"fte_{s_name}_{selected_shooter}")
                proc = p4.number_input("Procedural (Proc)", min_value=0, value=int(existing_score.get("Proc", 0)), key=f"proc_{s_name}_{selected_shooter}")

                # Validation Status Indicators & Checks
                total_paper_hits = alpha + charlie + delta
                total_accounted_rounds = plates + total_paper_hits + mike

                if total_rounds > 0:
                    if total_paper_hits > max_paper_shots:
                        st.error(f"❌ Paper hits ({total_paper_hits}) exceed total required paper shots ({max_paper_shots})!")
                    elif total_accounted_rounds > total_rounds:
                        st.error(f"❌ Total accounted hits & mikes ({total_accounted_rounds}) exceed total stage rounds ({total_rounds})!")
                    elif total_accounted_rounds == total_rounds:
                        st.caption(f"✅ All {total_rounds} stage rounds accounted for!")
                    else:
                        st.caption(f"⚠️ Accounted rounds: **{total_accounted_rounds}** / {total_rounds} ({total_rounds - total_accounted_rounds} remaining)")

                save_score = st.form_submit_button("💾 Save Score")
                if save_score:
                    if total_paper_hits > max_paper_shots:
                        st.error(f"Cannot save: Paper hits ({total_paper_hits}) exceed required paper shots ({max_paper_shots}).")
                    elif total_accounted_rounds > total_rounds:
                        st.error(f"Cannot save: Total hits and mikes ({total_accounted_rounds}) exceed total stage rounds ({total_rounds}).")
                    else:
                        is_dnf = (c_status == "Did Not Finish (DNF)")
                        key = (s_name, selected_shooter)
                        st.session_state.scores[key] = {
                            "time": raw_time, "steel": plates, "A": alpha, "C": charlie,
                            "D": delta, "M": mike, "NS": no_shoot, "FTE": fte, "Proc": proc, "DNF": is_dnf, "PF": pf
                        }
                        st.success(f"Score saved for {selected_shooter}!")

            stage_records = []
            for c in active_competitors:
                c_name = c['Competitor']
                s_data = st.session_state.scores.get((s_name, c_name), None)
                
                if s_data and s_data.get('DNF', False):
                    raw_pts = 0
                    hf = 0.0
                    time_val = s_data.get('time', 0.0)
                elif s_data and s_data['time'] > 0:
                    c_pts = 4 if s_data['PF'] == "Major" else 3
                    d_pts = 2 if s_data['PF'] == "Major" else 1
                    
                    raw_pts = (s_data['steel'] * 5) + (s_data['A'] * 5) + (s_data['C'] * c_pts) + (s_data['D'] * d_pts) - (s_data['M'] * 10) - (s_data['NS'] * 10) - (s_data['FTE'] * 10) - (s_data.get('Proc', 0) * 10)
                    raw_pts = max(0, raw_pts)
                    hf = raw_pts / s_data['time']
                    time_val = s_data['time']
                else:
                    raw_pts = 0
                    hf = 0.0
                    time_val = 0.0

                stage_records.append({
                    "Rank": 0,
                    "Stage %": 0.0,
                    "Stage Points": 0.0,
                    "#": c['#'],
                    "Competitor": c_name,
                    "Cat": c['Cat'], "Reg": c['Reg'], "Cls": c['Cls'], "Tag": c['Tag'], "ICS": c['ICS'],
                    "Raw Points": raw_pts,
                    "Raw Time": time_val,
                    "Hit Factor": hf,
                    "Power": c['Power'],
                    "Steel": s_data['steel'] if s_data else 0,
                    "A": s_data['A'] if s_data else 0,
                    "C": s_data['C'] if s_data else 0,
                    "D": s_data['D'] if s_data else 0,
                    "M": s_data['M'] if s_data else 0,
                    "NS": s_data['NS'] if s_data else 0,
                    "FTE": s_data['FTE'] if s_data else 0,
                    "Proc": s_data.get('Proc', 0) if s_data else 0,
                })

            df_stage = pd.DataFrame(stage_records)
            max_hf = df_stage["Hit Factor"].max() if not df_stage.empty else 0
            
            if max_hf > 0:
                df_stage["Stage Points"] = (df_stage["Hit Factor"] / max_hf) * cfg['max_pts']
                df_stage["Stage %"] = (df_stage["Hit Factor"] / max_hf) * 100
            else:
                df_stage["Stage Points"] = 0.0
                df_stage["Stage %"] = 0.0

            df_stage = df_stage.sort_values(by="Stage Points", ascending=False).reset_index(drop=True)
            df_stage["Rank"] = range(1, len(df_stage) + 1)

            # Stage Display Table (UI view)
            df_stage_view = df_stage[["Rank", "Stage %", "Stage Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Raw Points", "Raw Time", "Hit Factor", "Power"]]
            
            st.dataframe(df_stage_view.style.format({
                "Stage %": "{:.2f}%", 
                "Stage Points": "{:.4f}", 
                "Raw Points": "{:.4f}", 
                "Raw Time": "{:.2f}",
                "Hit Factor": "{:.4f}"
            }), use_container_width=True, hide_index=True)

            # --- Inline Hit Breakdown Inspection ---
            with st.expander(f"🔍 View Hit Breakdown ({s_name})"):
                if not df_stage.empty:
                    inspect_shooter = st.selectbox("Select Competitor to Inspect Hits", options=df_stage["Competitor"].tolist(), key=f"inspect_{s_name}")
                    row_data = df_stage[df_stage["Competitor"] == inspect_shooter].iloc[0]
                    
                    hb_col1, hb_col2, hb_col3, hb_col4, hb_col5, hb_col6, hb_col7, hb_col8 = st.columns(8)
                    hb_col1.metric("Steels", int(row_data["Steel"]))
                    hb_col2.metric("Alpha (A)", int(row_data["A"]))
                    hb_col3.metric("Charlie (C)", int(row_data["C"]))
                    hb_col4.metric("Delta (D)", int(row_data["D"]))
                    hb_col5.metric("Mike (M)", int(row_data["M"]))
                    hb_col6.metric("No-Shoot", int(row_data["NS"]))
                    hb_col7.metric("FTE", int(row_data["FTE"]))
                    hb_col8.metric("Procedural", int(row_data["Proc"]))

            # Print / Export view for Excel
            df_stage_print = df_stage[["Rank", "Stage %", "Stage Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Raw Points", "Raw Time", "Hit Factor", "Power"]].copy()
            df_stage_print["Stage %"] = df_stage_print["Stage %"].round(2).astype(str) + "%"
            df_stage_print["Stage Points"] = df_stage_print["Stage Points"].round(4)
            df_stage_print["Raw Points"] = df_stage_print["Raw Points"].round(4)
            df_stage_print["Raw Time"] = df_stage_print["Raw Time"].round(2)
            df_stage_print["Hit Factor"] = df_stage_print["Hit Factor"].round(4)

            # Dedicated Word Export view
            df_stage_word = df_stage[["Rank", "Stage %", "Stage Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Power"]].copy()
            df_stage_word["Stage %"] = df_stage_word["Stage %"].round(2).astype(str) + "%"
            df_stage_word["Stage Points"] = df_stage_word["Stage Points"].round(4)

            # Streamlined Export Section
            st.markdown("#### 📥 Export Stage Results")
            col_ex1, col_ex2 = st.columns(2)
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_stage_print.to_excel(writer, sheet_name=s_name, index=False)
            excel_data = excel_buffer.getvalue()
            col_ex1.download_button(
                label="📥 Download Excel (.xlsx)",
                data=excel_data,
                file_name=f"{match_name}_{division}_{s_name}_Results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_excel_{s_name}"
            )

            word_html = f"""
            <html>
            <head>
            <meta charset='utf-8'>
            <style>
                @page {{ margin: 0.75in; }}
                body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #000000; margin: 0; padding: 0; }}
                .header-container {{ text-align: left; margin: 0 0 15px 0; padding: 0; }}
                h2 {{ font-family: Arial, sans-serif; font-size: 16pt; font-weight: bold; margin: 0; padding: 0; line-height: 1.1; }}
                h3 {{ font-family: Arial, sans-serif; font-size: 12pt; font-weight: normal; margin: 0; padding: 0; line-height: 1.1; }}
                p {{ font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 0; line-height: 1.1; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-family: Arial, sans-serif; font-size: 7pt; }}
                th, td {{ padding: 2px 4px; border: 1px solid #000000; text-align: center; white-space: nowrap; width: 1%; }}
                th {{ font-weight: bold; }}
                td:nth-child(2), th:nth-child(2), td:nth-child(3), th:nth-child(3) {{ text-align: right; }}
                td:nth-child(5), th:nth-child(5) {{ width: 100%; white-space: normal; text-align: left; }}
            </style>
            </head>
            <body>
                <div class="header-container">
                    <h2>{match_name}</h2>
                    <h3>{division} ({s_name})</h3>
                    <p>Date: {match_date.strftime('%B %d, %Y')}</p>
                </div>
                {df_stage_word.to_html(index=False)}
            </body>
            </html>
            """
            
            col_ex2.download_button(
                label="📥 Download Word (.doc)",
                data=word_html,
                file_name=f"{match_name}_{division}_{s_name}_Results.doc",
                mime="application/msword",
                key=f"dl_word_{s_name}"
            )

            for _, row in df_stage.iterrows():
                overall_match_points[row["Competitor"]] += row["Stage Points"]

    # --- OVERALL STANDINGS SUB-TAB ---
    with tab_objects[-1]:
        st.subheader("🏆 Overall Match Standings")
        active_competitors_list = [c for c in st.session_state.competitors_list if not c['DQ']]
        
        if active_competitors_list:
            df_overall = pd.DataFrame(active_competitors_list)
            df_overall["Points"] = df_overall["Competitor"].map(overall_match_points)
            
            max_overall_pts = df_overall["Points"].max() if not df_overall.empty else 0
            if max_overall_pts > 0:
                df_overall["%"] = (df_overall["Points"] / max_overall_pts) * 100
            else:
                df_overall["%"] = 0.0

            df_overall = df_overall.sort_values(by="Points", ascending=False).reset_index(drop=True)
            df_overall["Rank"] = range(1, len(df_overall) + 1)

            df_overall_display = df_overall[["Rank", "%", "Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Power"]]

            st.dataframe(df_overall_display.style.format({
                "Points": "{:.4f}", 
                "%": "{:.2f}%"
            }), use_container_width=True, hide_index=True)

            df_overall_print = df_overall[["Rank", "%", "Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Power"]].copy()
            df_overall_print["%"] = df_overall_print["%"].round(2).astype(str) + "%"
            df_overall_print["Points"] = df_overall_print["Points"].round(4)

            st.markdown("#### 📥 Export Overall Standings")
            col_o1, col_o2 = st.columns(2)
            
            excel_buffer_o = io.BytesIO()
            with pd.ExcelWriter(excel_buffer_o, engine='xlsxwriter') as writer:
                df_overall_print.to_excel(writer, sheet_name="Overall", index=False)
            excel_data_o = excel_buffer_o.getvalue()
            col_o1.download_button(
                label="📥 Download Excel (.xlsx)",
                data=excel_data_o,
                file_name=f"{match_name}_{division}_Overall_Standings.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            word_html_o = f"""
            <html>
            <head>
            <meta charset='utf-8'>
            <style>
                @page {{ margin: 0.75in; }}
                body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #000000; margin: 0; padding: 0; }}
                .header-container {{ text-align: left; margin: 0 0 15px 0; padding: 0; }}
                h2 {{ font-family: Arial, sans-serif; font-size: 16pt; font-weight: bold; margin: 0; padding: 0; line-height: 1.1; }}
                h3 {{ font-family: Arial, sans-serif; font-size: 12pt; font-weight: normal; margin: 0; padding: 0; line-height: 1.1; }}
                p {{ font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 0; line-height: 1.1; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-family: Arial, sans-serif; font-size: 7pt; }}
                th, td {{ padding: 2px 4px; border: 1px solid #000000; text-align: center; white-space: nowrap; width: 1%; }}
                th {{ font-weight: bold; }}
                td:nth-child(2), th:nth-child(2), td:nth-child(3), th:nth-child(3) {{ text-align: right; }}
                td:nth-child(5), th:nth-child(5) {{ width: 100%; white-space: normal; text-align: left; }}
            </style>
            </head>
            <body>
                <div class="header-container">
                    <h2>{match_name}</h2>
                    <h3>{division} (Overall Standings)</h3>
                    <p>Date: {match_date.strftime('%B %d, %Y')}</p>
                </div>
                {df_overall_print.to_html(index=False)}
            </body>
            </html>
            """
            
            col_o2.download_button(
                label="📥 Download Word (.doc)",
                data=word_html_o,
                file_name=f"{match_name}_{division}_Overall_Standings.doc",
                mime="application/msword"
            )

            # ==========================================
            # INTEGRATED COMPETITOR SUMMARY INSPECTOR & ROSTER EXPORT
            # ==========================================
            st.divider()
            st.markdown("### 🔍 Inspect Competitor Cumulative Breakdown")
            
            ranked_competitors = df_overall["Competitor"].tolist()
            selected_comp_inspect = st.selectbox(
                "Select Competitor to inspect individual performance metrics:", 
                options=ranked_competitors, 
                key="select_cum_inspect"
            )

            # Calculate full cumulative dataset for the entire active roster
            roster_cum_records = []
            for _, c_row in df_overall.iterrows():
                c_name = c_row['Competitor']
                tot_steel, tot_A, tot_C, tot_D = 0, 0, 0, 0
                tot_M, tot_NS, tot_FTE, tot_Proc = 0, 0, 0, 0
                tot_time = 0.0

                for s_name in stage_names:
                    s_data = st.session_state.scores.get((s_name, c_name), {})
                    if s_data:
                        tot_steel += s_data.get('steel', 0)
                        tot_A += s_data.get('A', 0)
                        tot_C += s_data.get('C', 0)
                        tot_D += s_data.get('D', 0)
                        tot_M += s_data.get('M', 0)
                        tot_NS += s_data.get('NS', 0)
                        tot_FTE += s_data.get('FTE', 0)
                        tot_Proc += s_data.get('Proc', 0)
                        tot_time += s_data.get('time', 0.0)

                roster_cum_records.append({
                    "Rank": c_row["Rank"],
                    "%": f"{c_row['%']:.2f}%",
                    "Points": f"{c_row['Points']:.4f}",
                    "#": c_row["#"],
                    "Competitor": c_name,
                    "Cat": c_row["Cat"],
                    "Reg": c_row["Reg"],
                    "Cls": c_row["Cls"],
                    "Tag": c_row["Tag"],
                    "ICS": c_row["ICS"],
                    "Power": c_row["Power"],
                    "A": tot_A + tot_steel,
                    "C": tot_C,
                    "D": tot_D,
                    "M": tot_M,
                    "NS": tot_NS,
                    "FTE": tot_FTE,
                    "P": tot_Proc,
                    "Total Time": f"{tot_time:.2f}"
                })

            df_roster_cum = pd.DataFrame(roster_cum_records)

            if selected_comp_inspect:
                comp_info = df_overall[df_overall["Competitor"] == selected_comp_inspect].iloc[0]
                comp_cum = df_roster_cum[df_roster_cum["Competitor"] == selected_comp_inspect].iloc[0]
                
                # Display Metrics Cards for Selected Competitor
                m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7, m_col8 = st.columns(8)
                m_col1.metric("Rank", f"#{comp_info['Rank']}")
                m_col2.metric("Total Points", f"{comp_info['Points']:.2f}")
                m_col3.metric("Alpha (A)", comp_cum["A"], help="Includes Paper Alpha + Steel Hits")
                m_col4.metric("Charlie (C)", comp_cum["C"])
                m_col5.metric("Delta (D)", comp_cum["D"])
                m_col6.metric("Mikes (M)", comp_cum["M"])
                m_col7.metric("Penalties", comp_cum["NS"] + comp_cum["FTE"] + comp_cum["P"], help="NS + FTE + P")
                m_col8.metric("Total Time", f"{comp_cum['Total Time']}s")

            # Filtered Export View (Only requested columns)
            export_columns = ["Rank", "%", "Points", "#", "Competitor", "A", "C", "D", "M", "NS", "FTE", "P", "Total Time"]
            df_roster_cum_export = df_roster_cum[export_columns].copy()

            # Full Roster Cumulative Breakdown Export Section
            st.markdown("#### 📥 Export Full Roster Cumulative Breakdown")
            sc_col1, sc_col2 = st.columns(2)

            excel_roster_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_roster_buffer, engine='xlsxwriter') as writer:
                df_roster_cum_export.to_excel(writer, sheet_name="Roster_Cumulative_Summary", index=False)
            excel_roster_data = excel_roster_buffer.getvalue()

            sc_col1.download_button(
                label="📥 Download Full Roster Cumulative Excel (.xlsx)",
                data=excel_roster_data,
                file_name=f"{match_name}_{division}_Full_Roster_Cumulative_Summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_roster_cum_excel"
            )

            word_roster_html = f"""
            <html>
            <head>
            <meta charset='utf-8'>
            <style>
                @page {{ margin: 0.75in; }}
                body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #000000; margin: 0; padding: 0; }}
                .header-container {{ text-align: left; margin: 0 0 15px 0; padding: 0; }}
                h2 {{ font-family: Arial, sans-serif; font-size: 16pt; font-weight: bold; margin: 0; padding: 0; line-height: 1.1; }}
                h3 {{ font-family: Arial, sans-serif; font-size: 12pt; font-weight: normal; margin: 0; padding: 0; line-height: 1.1; }}
                p {{ font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 0; line-height: 1.1; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-family: Arial, sans-serif; font-size: 7pt; }}
                th, td {{ padding: 3px 5px; border: 1px solid #000000; text-align: center; white-space: nowrap; }}
                th {{ font-weight: bold; background-color: #f2f2f2; }}
                td:nth-child(5), th:nth-child(5) {{ text-align: left; }}
            </style>
            </head>
            <body>
                <div class="header-container">
                    <h2>{match_name}</h2>
                    <h3>Full Roster Cumulative Hit & Time Summary</h3>
                    <p>Division: {division} | Date: {match_date.strftime('%B %d, %Y')}</p>
                </div>
                {df_roster_cum_export.to_html(index=False)}
            </body>
            </html>
            """

            sc_col2.download_button(
                label="📥 Download Full Roster Cumulative Word (.doc)",
                data=word_roster_html,
                file_name=f"{match_name}_{division}_Full_Roster_Cumulative_Summary.doc",
                mime="application/msword",
                key="dl_roster_cum_word"
            )
        else:
            st.warning("No active competitors available for overall standings.")
