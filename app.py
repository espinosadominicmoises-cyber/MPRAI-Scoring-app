import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import io

st.set_page_config(page_title="IPSC Match Scoring System", layout="wide")

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
        stage_names.append(custom_s_name)
        stage_config[custom_s_name] = {
            "paper": paper,
            "steel": steel,
            "max_pts": max_stage_points
        }
        st.caption(f"Max Points: **{max_stage_points} pts**")

# ==========================================
# DOCUMENT DESIGN & TEMPLATE CUSTOMIZER
# ==========================================
st.sidebar.divider()
st.sidebar.header("🎨 Print & Layout Customizer")
custom_header_text = st.sidebar.text_input("Document Banner Title", value="MPRAI CLUBSHOOT")
custom_footer_text = st.sidebar.text_input("Document Footer Note", value="Certified Match Score Sheet - IPSC Rules Applied")
show_logo_badge = st.sidebar.checkbox("Show Official Logos Header", value=True)

# ==========================================
# MAIN APP HEADER
# ==========================================
st.title(f"🎯 {match_name if match_name else 'IPSC Match Scoring'}")
st.caption(f"Date: {match_date.strftime('%B %d, %Y')} | Division: **{division}**")

# ==========================================
# COMPETITOR ROSTER MANAGEMENT
# ==========================================
if "competitors_list" not in st.session_state:
    st.session_state.competitors_list = []

cat_options = ["", "L", "LS", "S", "SS", "GS", "J", "SJ"]

st.header("👤 Competitor Roster Management")

with st.expander("➕ Add New Competitor", expanded=False):
    with st.form("add_competitor_form", clear_on_submit=True):
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 1, 1, 1, 1])
        c_name = col1.text_input("Competitor Name", value="")
        c_cat = col2.selectbox("Cat", cat_options)
        c_reg = col3.text_input("Reg", value="PHI")
        c_cls = col4.selectbox("Cls", ["", "GM", "M", "A", "B", "C", "D", "U"])
        c_tag = col5.text_input("Tag", value="")
        c_ics = col6.text_input("ICS", value="")
        c_power = col7.selectbox("Power", default_power_options)
        
        submit_comp = st.form_submit_button("➕ Add Competitor")
        if submit_comp and c_name:
            next_id = len(st.session_state.competitors_list) + 1
            st.session_state.competitors_list.append({
                "#": next_id, "Competitor": c_name.upper(), "Cat": c_cat, 
                "Reg": c_reg, "Cls": c_cls, "Tag": c_tag, "ICS": c_ics, "Power": c_power
            })
            st.success(f"Added {c_name.upper()} successfully!")
            st.rerun()

if st.session_state.competitors_list:
    st.subheader("✏️ Edit or Delete Competitors")
    comp_names = [c["Competitor"] for c in st.session_state.competitors_list]
    selected_to_edit = st.selectbox("Select Competitor to Edit/Delete", options=comp_names)
    
    current_data = next(c for c in st.session_state.competitors_list if c["Competitor"] == selected_to_edit)
    
    with st.form("edit_delete_form"):
        ec1, ec2, ec3, ec4, ec5, ec6, ec7 = st.columns([3, 1, 1, 1, 1, 1, 1])
        e_name = ec1.text_input("Competitor Name", value=current_data["Competitor"])
        e_cat = ec2.selectbox("Cat", cat_options, index=cat_options.index(current_data["Cat"]) if current_data["Cat"] in cat_options else 0)
        e_reg = ec3.text_input("Reg", value=current_data["Reg"])
        e_cls = ec4.selectbox("Cls", ["", "GM", "M", "A", "B", "C", "D", "U"], index=["", "GM", "M", "A", "B", "C", "D", "U"].index(current_data["Cls"]) if current_data["Cls"] in ["", "GM", "M", "A", "B", "C", "D", "U"] else 0)
        e_tag = ec5.text_input("Tag", value=current_data["Tag"])
        e_ics = ec6.text_input("ICS", value=current_data["ICS"])
        e_power = ec7.selectbox("Power", default_power_options, index=0 if current_data["Power"] in default_power_options else 0)
        
        b_col1, b_col2 = st.columns(2)
        save_changes = b_col1.form_submit_button("💾 Save Changes")
        delete_shooter = b_col2.form_submit_button("🗑️ Delete Competitor")
        
        if save_changes:
            current_data["Competitor"] = e_name.upper()
            current_data["Cat"] = e_cat
            current_data["Reg"] = e_reg
            current_data["Cls"] = e_cls
            current_data["Tag"] = e_tag
            current_data["ICS"] = e_ics
            current_data["Power"] = e_power
            st.success("Competitor updated successfully!")
            st.rerun()
            
        if delete_shooter:
            st.session_state.competitors_list = [c for c in st.session_state.competitors_list if c["Competitor"] != selected_to_edit]
            for idx, c in enumerate(st.session_state.competitors_list, 1):
                c["#"] = idx
            st.warning(f"Deleted {selected_to_edit}!")
            st.rerun()

    st.markdown("### Official Roster Summary")
    df_roster = pd.DataFrame(st.session_state.competitors_list)
    st.dataframe(df_roster, hide_index=True, use_container_width=True)
else:
    st.warning("No competitors in roster yet. Add one above to begin.")

# Initialize Score Database
if "scores" not in st.session_state:
    st.session_state.scores = {}

# ==========================================
# STAGE SCOREBOARDS & OVERALL STANDINGS
# ==========================================
st.divider()
tabs = stage_names + ["Overall Standings"]
tab_objects = st.tabs(tabs)

overall_match_points = {c['Competitor']: 0.0 for c in st.session_state.competitors_list}

for i, s_name in enumerate(stage_names):
    with tab_objects[i]:
        st.subheader(f"{s_name} Scoreboard")
        cfg = stage_config[s_name]
        st.info(f"Targets: **{cfg['paper']} Paper** | **{cfg['steel']} Steel** | Max Stage Points: **{cfg['max_pts']}**")
        
        if not st.session_state.competitors_list:
            st.warning("Please add competitors to the roster first.")
            continue

        selected_shooter = st.selectbox("Select Competitor to Enter Score", options=[c['Competitor'] for c in st.session_state.competitors_list], key=f"select_{s_name}")
        shooter_info = next(c for c in st.session_state.competitors_list if c['Competitor'] == selected_shooter)
        pf = shooter_info['Power']

        with st.form(f"score_form_{s_name}_{selected_shooter}"):
            st.markdown(f"**Scoring for: {selected_shooter} ({pf})**")
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
            raw_time = c1.number_input("Time (s)", min_value=0.0, value=0.0, format="%.2f", key=f"time_{s_name}_{selected_shooter}")
            plates = c2.number_input("Steel Hits", min_value=0, max_value=cfg['steel'] if cfg['steel'] > 0 else 100, value=0, key=f"st_{s_name}_{selected_shooter}")
            alpha = c3.number_input("Alpha (A)", min_value=0, value=0, key=f"a_{s_name}_{selected_shooter}")
            charlie = c4.number_input("Charlie (C)", min_value=0, value=0, key=f"c_{s_name}_{selected_shooter}")
            delta = c5.number_input("Delta (D)", min_value=0, value=0, key=f"d_{s_name}_{selected_shooter}")
            mike = c6.number_input("Mike (M)", min_value=0, value=0, key=f"m_{s_name}_{selected_shooter}")
            no_shoot = c7.number_input("No-Shoot", min_value=0, value=0, key=f"ns_{s_name}_{selected_shooter}")
            fte = c8.number_input("FTE", min_value=0, value=0, key=f"fte_{s_name}_{selected_shooter}")
            
            save_score = st.form_submit_button("💾 Save Score")
            if save_score:
                key = (s_name, selected_shooter)
                st.session_state.scores[key] = {
                    "time": raw_time, "steel": plates, "A": alpha, "C": charlie,
                    "D": delta, "M": mike, "NS": no_shoot, "FTE": fte, "PF": pf
                }
                st.success(f"Score saved for {selected_shooter}!")

        stage_records = []
        for c in st.session_state.competitors_list:
            c_name = c['Competitor']
            s_data = st.session_state.scores.get((s_name, c_name), None)
            
            if s_data and s_data['time'] > 0:
                c_pts = 4 if s_data['PF'] == "Major" else 3
                d_pts = 2 if s_data['PF'] == "Major" else 1
                
                raw_pts = (s_data['steel'] * 5) + (s_data['A'] * 5) + (s_data['C'] * c_pts) + (s_data['D'] * d_pts) - (s_data['M'] * 10) - (s_data['NS'] * 10) - (s_data['FTE'] * 10)
                raw_pts = max(0, raw_pts)
                hf = raw_pts / s_data['time']
            else:
                raw_pts = 0
                hf = 0.0

            stage_records.append({
                "Rank": 0,
                "Stage %": 0.0,
                "Stage Points": 0.0,
                "#": c['#'],
                "Competitor": c_name,
                "Cat": c['Cat'], "Reg": c['Reg'], "Cls": c['Cls'], "Tag": c['Tag'], "ICS": c['ICS'],
                "Raw Points": raw_pts,
                "Raw Time": s_data['time'] if s_data else 0.0,
                "Hit Factor": hf,
                "Power": c['Power'],
                "Steel": s_data['steel'] if s_data else 0,
                "A": s_data['A'] if s_data else 0,
                "C": s_data['C'] if s_data else 0,
                "D": s_data['D'] if s_data else 0,
                "M": s_data['M'] if s_data else 0,
                "NS": s_data['NS'] if s_data else 0,
                "FTE": s_data['FTE'] if s_data else 0,
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
        }), use_container_width=True)

        # Separate Section: Hit Breakdown per Competitor
        st.markdown("#### 📋 Hit Breakdown per Competitor")
        df_hit_breakdown = df_stage[["#", "Competitor", "Raw Time", "Steel", "A", "C", "D", "M", "NS", "FTE", "Raw Points", "Hit Factor"]]
        st.dataframe(df_hit_breakdown.style.format({
            "Raw Time": "{:.2f}",
            "Raw Points": "{:.4f}",
            "Hit Factor": "{:.4f}"
        }), use_container_width=True)

        # Print / Export view for Stage (Renaming Rank column to blank header `""` and rounding numbers for file export)
        df_stage_print = df_stage[["Rank", "Stage %", "Stage Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Raw Points", "Raw Time", "Hit Factor", "Power"]].copy()
        df_stage_print = df_stage_print.rename(columns={"Rank": ""})
        
        # Explicit rounding for exported files
        df_stage_print["Stage %"] = df_stage_print["Stage %"].round(2).astype(str) + "%"
        df_stage_print["Stage Points"] = df_stage_print["Stage Points"].round(4)
        df_stage_print["Raw Points"] = df_stage_print["Raw Points"].round(4)
        df_stage_print["Raw Time"] = df_stage_print["Raw Time"].round(2)
        df_stage_print["Hit Factor"] = df_stage_print["Hit Factor"].round(4)

        with st.expander(f"🖨️ Print & Export Center - {s_name} ({division})"):
            logos_html = """
            <div style="display: flex; justify-content: flex-end; gap: 15px; align-items: center; margin-bottom: 10px;">
                <div style="border: 2px solid #b8860b; border-radius: 50%; width: 55px; height: 55px; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; text-align: center; background: #222; color: gold;">MPRAI</div>
                <div style="border: 2px solid #002b49; border-radius: 8px; width: 65px; height: 45px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; background: #002b49; color: white;">PPSA</div>
                <div style="border: 2px solid #b8860b; border-radius: 8px; width: 45px; height: 55px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; background: #111; color: gold;">I.P.S.C.</div>
            </div>
            """ if show_logo_badge else ""

            st.markdown(f"""
            <div style="border: 2px solid #333; padding: 20px; border-radius: 4px; background-color: #fff; color: #111;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h2 style="margin: 0 0 5px 0; color: #111; font-size: 22px; font-weight: bold;">{custom_header_text}</h2>
                        <h3 style="margin: 0 0 5px 0; color: #111; font-size: 18px; font-weight: bold;">{division} ({s_name})</h3>
                        <p style="margin: 0; font-size: 14px; color: #333;">Date: {match_date.strftime('%B %d, %Y')}</p>
                    </div>
                    <div>{logos_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_stage_print, use_container_width=True)

            st.markdown(f"""
            <div style="text-align: center; font-size: 12px; color: #333; margin-top: 15px;">
                {custom_footer_text}
            </div>
            """, unsafe_allow_html=True)

            # Export Buttons
            col_ex1, col_ex2 = st.columns(2)
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_stage_print.to_excel(writer, sheet_name=s_name, index=False)
            excel_data = excel_buffer.getvalue()
            col_ex1.download_button(
                label="📥 Download Excel (.xlsx)",
                data=excel_data,
                file_name=f"{match_name}_{division}_{s_name}_Results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            word_html = f"""
            <html><head><meta charset='utf-8'></head><body>
            <h2 style="text-align: center;">{custom_header_text}</h2>
            <h3 style="text-align: center;">{match_name} - {division} ({s_name})</h3>
            <p style="text-align: center;">Date: {match_date.strftime('%B %d, %Y')}</p>
            {df_stage_print.to_html(index=False)}
            <br><p style="text-align: center; font-size: 10px;">{custom_footer_text}</p>
            </body></html>
            """
            col_ex2.download_button(
                label="📥 Download Word (.doc)",
                data=word_html,
                file_name=f"{match_name}_{division}_{s_name}_Results.doc",
                mime="application/msword"
            )

        for _, row in df_stage.iterrows():
            overall_match_points[row["Competitor"]] += row["Stage Points"]

# ==========================================
# OVERALL STANDINGS TAB
# ==========================================
with tab_objects[-1]:
    st.subheader("🏆 Overall Match Standings")
    if st.session_state.competitors_list:
        df_overall = pd.DataFrame(st.session_state.competitors_list)
        df_overall["Points"] = df_overall["Competitor"].map(overall_match_points)
        
        max_overall_pts = df_overall["Points"].max() if not df_overall.empty else 0
        if max_overall_pts > 0:
            df_overall["%"] = (df_overall["Points"] / max_overall_pts) * 100
        else:
            df_overall["%"] = 0.0

        df_overall = df_overall.sort_values(by="Points", ascending=False).reset_index(drop=True)
        df_overall["Rank"] = range(1, len(df_overall) + 1)

        # Standard Overall Display format (UI view)
        df_overall_display = df_overall[["Rank", "%", "Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Power"]]

        st.dataframe(df_overall_display.style.format({
            "Points": "{:.4f}", 
            "%": "{:.2f}%"
        }), use_container_width=True)

        # Print / Export view for Overall (Renaming Rank column to blank header `""` and rounding numbers for file export)
        df_overall_print = df_overall[["Rank", "%", "Points", "#", "Competitor", "Cat", "Reg", "Cls", "Tag", "ICS", "Power"]].copy()
        df_overall_print = df_overall_print.rename(columns={"Rank": ""})
        
        # Explicit rounding for exported files
        df_overall_print["%"] = df_overall_print["%"].round(2).astype(str) + "%"
        df_overall_print["Points"] = df_overall_print["Points"].round(4)

        with st.expander(f"🖨️ Print & Export Center - Overall Standings ({division})"):
            logos_html = """
            <div style="display: flex; justify-content: flex-end; gap: 15px; align-items: center; margin-bottom: 10px;">
                <div style="border: 2px solid #b8860b; border-radius: 50%; width: 55px; height: 55px; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; text-align: center; background: #222; color: gold;">MPRAI</div>
                <div style="border: 2px solid #002b49; border-radius: 8px; width: 65px; height: 45px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; background: #002b49; color: white;">PPSA</div>
                <div style="border: 2px solid #b8860b; border-radius: 8px; width: 45px; height: 55px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; background: #111; color: gold;">I.P.S.C.</div>
            </div>
            """ if show_logo_badge else ""

            st.markdown(f"""
            <div style="border: 2px solid #333; padding: 20px; border-radius: 4px; background-color: #fff; color: #111;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h2 style="margin: 0 0 5px 0; color: #111; font-size: 22px; font-weight: bold;">{custom_header_text}</h2>
                        <h3 style="margin: 0 0 5px 0; color: #111; font-size: 18px; font-weight: bold;">{division} (Overall Standings)</h3>
                        <p style="margin: 0; font-size: 14px; color: #333;">Date: {match_date.strftime('%B %d, %Y')}</p>
                    </div>
                    <div>{logos_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_overall_print, use_container_width=True)

            st.markdown(f"""
            <div style="text-align: center; font-size: 12px; color: #333; margin-top: 15px;">
                {custom_footer_text}
            </div>
            """, unsafe_allow_html=True)

            # Export Buttons for Overall
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
            <html><head><meta charset='utf-8'></head><body>
            <h2 style="text-align: center;">{custom_header_text}</h2>
            <h3 style="text-align: center;">{match_name} - {division} (Overall Standings)</h3>
            <p style="text-align: center;">Date: {match_date.strftime('%B %d, %Y')}</p>
            {df_overall_print.to_html(index=False)}
            <br><p style="text-align: center; font-size: 10px;">{custom_footer_text}</p>
            </body></html>
            """
            col_o2.download_button(
                label="📥 Download Word (.doc)",
                data=word_html_o,
                file_name=f"{match_name}_{division}_Overall_Standings.doc",
                mime="application/msword"
            )