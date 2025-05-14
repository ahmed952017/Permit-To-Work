import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Configuration ---
DATA_FILE = "work_permits.csv"

# --- Dropdown Options ---
WORK_TYPES = ["", "Hot Work", "Confined Space Entry", "Working at Height", "Electrical Work", "Excavation", "General Maintenance", "Other"]
# Filter out the initial empty string for multiselect, but keep "Other" as a distinct choice.
PRECAUTIONS_OPTIONS = ["Use Standard PPE", "Lockout/Tagout Required", "Fire Watch Required", "Atmospheric Testing Needed", "Ventilation Required", "Buddy System Mandatory", "Fall Protection Required", "Other (Specify in Description)"]

# Define expected columns and their types
EXPECTED_COLUMNS = {
    "Permit ID": str,
    "Requester": str,
    "Location": str,
    "Work Type": str,
    "Description": str,
    "Likelihood": str,
    "Severity": str,
    "Risk Assessment": str, # Stores the numerical score as a string
    "Precautions": str, # Will store comma-separated string for multiple selections
    "Issue Date": str,
    "Status": str,
    "Supervisor Notes": str,
    "Supervisor Action Date": str
}

# --- Helper Functions ---
def load_data():
    """Loads permit data from the CSV file, ensuring all columns exist."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype=str, keep_default_na=False)
            for col in EXPECTED_COLUMNS.keys():
                if col not in df.columns:
                    df[col] = ""
            df = df[list(EXPECTED_COLUMNS.keys())]
            df["Supervisor Notes"] = df["Supervisor Notes"].fillna("").astype(str)
            df["Supervisor Action Date"] = df["Supervisor Action Date"].fillna("").astype(str)
            return df
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=list(EXPECTED_COLUMNS.keys()))
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return pd.DataFrame(columns=list(EXPECTED_COLUMNS.keys()))
    else:
        return pd.DataFrame(columns=list(EXPECTED_COLUMNS.keys()))

def save_data(df):
    """Saves permit data to the CSV file."""
    try:
        df_to_save = df[list(EXPECTED_COLUMNS.keys())].copy()
        df_to_save.to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def generate_permit_id():
    """Generates a unique permit ID based on timestamp."""
    return f"WP-{datetime.now().strftime("%Y%m%d%H%M%S%f")}"

# --- Risk Assessment Helper Functions ---
def get_risk_level_and_color(risk_score_int):
    """Determines risk level and color based on the score."""
    if not isinstance(risk_score_int, int):
        return "Invalid", "gray", 0
    if 1 <= risk_score_int <= 4:
        level, color = "Low", "#28a745"  # Green
    elif 5 <= risk_score_int <= 12:
        level, color = "Medium", "#ffc107"  # Orange/Yellow
    elif 13 <= risk_score_int <= 25:
        level, color = "High", "#dc3545"  # Red
    else:
        level, color = "Undefined" if risk_score_int != 0 else "N/A", "gray"
    return level, color

def calculate_risk_assessment_details(likelihood_str, severity_str):
    """Calculates risk score (int), level (str), and color (str)."""
    try:
        l, s = int(likelihood_str), int(severity_str)
        risk_score_int = l * s if (1 <= l <= 5 and 1 <= s <= 5) else 0
    except (ValueError, TypeError):
        risk_score_int = 0
    level, color = get_risk_level_and_color(risk_score_int)
    return risk_score_int, level, color

# --- Load Data ---
if 'df_permits' not in st.session_state:
    st.session_state.df_permits = load_data()

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("Work Permit System")

# --- Sidebar for Navigation/Actions ---
st.sidebar.header("Actions")
app_mode = st.sidebar.selectbox("Choose Mode", ["Issue New Permit", "Review Permits", "View All Permits"], key="app_mode_select")

# --- Issue New Permit ---
if app_mode == "Issue New Permit":
    st.header("Issue a New Work Permit")
    with st.form("permit_form", clear_on_submit=True):
        requester = st.text_input("Requester Name", key="requester_name_new")
        location = st.text_input("Work Location", key="location_new")
        work_type = st.selectbox("Work Type", options=WORK_TYPES, key="work_type_new", index=0)
        description = st.text_area("Work Description", key="description_new")

        st.subheader("Risk Assessment")
        col_l, col_s = st.columns(2)
        with col_l:
            likelihood_val_str = st.selectbox("Likelihood (1-5)", options=[str(i) for i in range(1, 6)], key="likelihood_new", index=0)
        with col_s:
            severity_val_str = st.selectbox("Severity (1-5)", options=[str(i) for i in range(1, 6)], key="severity_new", index=0)

        risk_score_val_int, risk_level_val, risk_color_val = calculate_risk_assessment_details(likelihood_val_str, severity_val_str)
        st.markdown(f"**Calculated Risk Score:** <span style='color:{risk_color_val}; font-size: 1.2em; font-weight:bold;'>{risk_score_val_int}</span> (<span style='color:{risk_color_val}; font-weight:bold;'>{risk_level_val}</span>)", unsafe_allow_html=True)

        st.markdown("---_Risk Matrix Visual_---")
        matrix_html = "<style> table.risk-matrix { border-collapse: collapse; text-align: center; margin-top:10px; } .risk-matrix th, .risk-matrix td { border: 1px solid #ccc; padding: 8px; } .risk-matrix .sev-header { writing-mode: vertical-rl; text-orientation: mixed; text-align:center; font-weight:bold; } .risk-matrix .lik-header { font-weight:bold; } </style>"
        matrix_html += "<table class='risk-matrix'>"
        matrix_html += "<tr><td rowspan='7' class='sev-header'>Severity →</td><td></td><td colspan='5' class='lik-header'>Likelihood →</td></tr>"
        matrix_html += "<tr><td></td>"
        for l_header in range(1, 6):
            matrix_html += f"<td class='lik-header'>{l_header}</td>"
        matrix_html += "</tr>"
        for s_loop in range(5, 0, -1):
            matrix_html += f"<tr><td class='sev-header' style='padding-right:10px; padding-left:5px;'>{s_loop}</td>"
            for l_loop in range(1, 6):
                cell_score = s_loop * l_loop
                _, cell_color = get_risk_level_and_color(cell_score)
                cell_style = f"background-color:{cell_color}; color: {'white' if cell_color in ['#dc3545','#28a745'] else 'black'};"
                try:
                    if int(likelihood_val_str) == l_loop and int(severity_val_str) == s_loop:
                        cell_style += " border: 3px solid black; font-weight: bold;"
                except ValueError: pass
                matrix_html += f"<td style='{cell_style}'>{cell_score}</td>"
            matrix_html += "</tr>"
        matrix_html += "</table>"
        st.markdown(matrix_html, unsafe_allow_html=True)
        st.markdown("---")

        st.subheader("Precautions")
        selected_precautions = st.multiselect("Select Precautions (Multiple Choice Allowed)", options=PRECAUTIONS_OPTIONS, key="precautions_multiselect_new")
        other_precautions_details = ""
        if "Other (Specify in Description)" in selected_precautions:
            other_precautions_details = st.text_input(
                "Please specify other precautions:",
                key="other_precautions_text_new",
                placeholder="Enter details for other precautions"
            )

        submitted = st.form_submit_button("Submit Permit Request")

        if submitted:
            error_messages = []
            if not requester: error_messages.append("Requester Name is required.")
            if not location: error_messages.append("Work Location is required.")
            if not work_type: error_messages.append("Work Type must be selected.")
            if not description: error_messages.append("Work Description is required.")
            
            final_precautions_list = []
            if selected_precautions:
                for p_item in selected_precautions:
                    if p_item == "Other (Specify in Description)":
                        if other_precautions_details:
                            final_precautions_list.append(f"Other: {other_precautions_details}")
                        else:
                            error_messages.append("If 'Other' precaution is selected, please specify the details.")
                    else:
                        final_precautions_list.append(p_item)
            
            if not final_precautions_list and not ("Other (Specify in Description)" in selected_precautions and other_precautions_details):
                 # This condition might need refinement based on whether any precaution is mandatory
                 if not selected_precautions: # If nothing is selected at all
                    error_messages.append("At least one precaution must be selected, or 'Other' specified.")

            if error_messages:
                for msg in error_messages:
                    st.warning(msg)
            else:
                permit_id = generate_permit_id()
                issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                precautions_to_save = ", ".join(final_precautions_list) if final_precautions_list else "None specified"

                new_permit_data = {
                    "Permit ID": permit_id, "Requester": requester, "Location": location,
                    "Work Type": work_type, "Description": description, "Likelihood": likelihood_val_str,
                    "Severity": severity_val_str, "Risk Assessment": str(risk_score_val_int),
                    "Precautions": precautions_to_save,
                    "Issue Date": issue_date, "Status": "Pending",
                    "Supervisor Notes": "", "Supervisor Action Date": ""
                }
                for col_expected in EXPECTED_COLUMNS.keys():
                    if col_expected not in new_permit_data: new_permit_data[col_expected] = ""
                
                new_permit_df_row = pd.DataFrame([new_permit_data])
                new_permit_df_row = new_permit_df_row[list(EXPECTED_COLUMNS.keys())]
                st.session_state.df_permits = pd.concat([st.session_state.df_permits, new_permit_df_row], ignore_index=True)
                save_data(st.session_state.df_permits)
                st.success(f"Permit {permit_id} submitted successfully! The form has been cleared.")

# --- Review Permits ---
elif app_mode == "Review Permits":
    st.header("Review Pending Work Permits")
    df_permits_review = st.session_state.df_permits
    if df_permits_review.empty or df_permits_review[df_permits_review["Status"] == "Pending"].empty:
        st.info("No pending permits to review.")
    else:
        pending_df = df_permits_review[df_permits_review["Status"] == "Pending"].copy()
        permit_ids_list = pending_df["Permit ID"].tolist()
        selected_permit_id = st.selectbox("Select a Permit to Review", options=permit_ids_list, key="select_permit_review", index=0 if permit_ids_list else None)

        if selected_permit_id:
            try:
                permit_index = df_permits_review[df_permits_review["Permit ID"] == selected_permit_id].index[0]
                permit_details = df_permits_review.loc[permit_index].copy()
                st.subheader(f"Reviewing Permit ID: {permit_details['Permit ID']}")
                col1_rev, col2_rev = st.columns(2)
                with col1_rev:
                    st.text_input("Requester", value=permit_details.get("Requester",""), disabled=True, key=f"rev_req_{permit_details['Permit ID']}")
                    st.text_input("Location", value=permit_details.get("Location",""), disabled=True, key=f"rev_loc_{permit_details['Permit ID']}")
                    st.text_input("Work Type", value=permit_details.get("Work Type",""), disabled=True, key=f"rev_wt_{permit_details['Permit ID']}")
                    st.text_area("Description", value=permit_details.get("Description",""), disabled=True, height=150, key=f"rev_desc_{permit_details['Permit ID']}")
                with col2_rev:
                    st.text_input("Likelihood", value=permit_details.get("Likelihood",""), disabled=True, key=f"rev_lh_{permit_details['Permit ID']}")
                    st.text_input("Severity", value=permit_details.get("Severity",""), disabled=True, key=f"rev_sv_{permit_details['Permit ID']}")
                    rev_likelihood, rev_severity = permit_details.get("Likelihood", "0"), permit_details.get("Severity", "0")
                    rev_score_int, rev_level, rev_color = calculate_risk_assessment_details(rev_likelihood, rev_severity)
                    displayed_rev_score = permit_details.get("Risk Assessment", str(rev_score_int))
                    st.markdown(f"**Risk Assessment:** <span style='color:{rev_color};'>{displayed_rev_score} ({rev_level})</span>", unsafe_allow_html=True)
                    st.text_area("Precautions", value=permit_details.get("Precautions",""), disabled=True, height=100, key=f"rev_prec_{permit_details['Permit ID']}") # Displays as saved string
                    st.text_input("Issue Date", value=permit_details.get("Issue Date",""), disabled=True, key=f"rev_idate_{permit_details['Permit ID']}")
                    st.text_input("Current Status", value=permit_details.get("Status",""), disabled=True, key=f"rev_stat_{permit_details['Permit ID']}")

                with st.form(f"review_form_{permit_details['Permit ID']}", clear_on_submit=True):
                    supervisor_notes = st.text_area("Supervisor Notes", key=f"supervisor_notes_{permit_details['Permit ID']}")
                    approve_button, reject_button = st.columns(2)
                    if approve_button.form_submit_button("Approve Permit"):
                        st.session_state.df_permits.loc[permit_index, "Status"] = "Approved"
                        st.session_state.df_permits.loc[permit_index, "Supervisor Notes"] = supervisor_notes if supervisor_notes else "Approved without notes."
                        st.session_state.df_permits.loc[permit_index, "Supervisor Action Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        save_data(st.session_state.df_permits)
                        st.success(f"Permit {selected_permit_id} approved."); st.rerun()
                    if reject_button.form_submit_button("Reject Permit"):
                        if supervisor_notes:
                            st.session_state.df_permits.loc[permit_index, "Status"] = "Rejected"
                            st.session_state.df_permits.loc[permit_index, "Supervisor Notes"] = supervisor_notes
                            st.session_state.df_permits.loc[permit_index, "Supervisor Action Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_data(st.session_state.df_permits)
                            st.success(f"Permit {selected_permit_id} rejected."); st.rerun()
                        else:
                            st.warning("Supervisor notes are required to reject a permit.")
            except IndexError: st.error("Could not find the selected permit.")
            except Exception as e: st.error(f"An error occurred: {e}")

# --- View All Permits ---
elif app_mode == "View All Permits":
    st.header("All Work Permits")
    df_view_all = st.session_state.df_permits.copy()
    if df_view_all.empty:
        st.info("No work permits found.")
    else:
        df_display_all = df_view_all[list(EXPECTED_COLUMNS.keys())].copy()
        st.dataframe(df_display_all, use_container_width=True)
        if st.button("Refresh Data", key="refresh_view_all"): 
            st.session_state.df_permits = load_data(); st.rerun()

