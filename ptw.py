import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Login System ---
def login():
    st.title("🔐 Work Permit System - Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username in ["user", "supervisor"] and password == "123456":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun() # Use st.rerun() for newer Streamlit versions
            else:
                st.error("Invalid username or password")

# --- Check Login Status ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    login()
    st.stop()

# --- Configuration ---
DATA_FILE = "work_permits.csv"

# --- Dropdown Options ---
WORK_TYPES = ["","High Pressure", "Hot Work", "Confined Space Entry", "Working at Height", "Electrical Work", "Excavation", "General Maintenance", "Other"]
PRECAUTIONS_OPTIONS = ["Specified tems", "Use Standard PPE", "Lockout/Tagout Required", "Fire Watch Required", "Atmospheric Testing Needed", "Ventilation Required", "Buddy System Mandatory", "Fall Protection Required", "Other (Specify in Description)"]
LIKELIHOOD_OPTIONS = [str(i) for i in range(1, 6)]
SEVERITY_OPTIONS = [str(i) for i in range(1, 6)]

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
    try:
        df_to_save = df[list(EXPECTED_COLUMNS.keys())].copy()
        df_to_save.to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def generate_permit_id():
    return f"WP-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

# --- Risk Assessment Helper Functions ---
def get_risk_level_and_color(risk_score_int):
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

# --- Display logged in user ---
st.sidebar.header(f"Logged in as: {st.session_state.username}")

# --- Sidebar for Navigation/Actions based on login role ---
st.sidebar.header("Actions")

# Determine available options based on login role
if st.session_state.username == "user":
    # Regular user can only issue new permits
    app_mode = "Issue New Permit"  # Default and only option
    st.sidebar.info("You are logged in as a regular user. You can issue new work permits.")
elif st.session_state.username == "supervisor":
    # Supervisor can issue, review, and view all permits
    app_mode = st.sidebar.selectbox(
        "Choose Mode", 
        ["Issue New Permit", "Review Permits", "View All Permits"], 
        key="app_mode_select"
    )
    st.sidebar.info("You are logged in as a supervisor. You can issue, review, and view all permits.")
else:
    # Fallback for any unexpected username
    app_mode = "Issue New Permit"
    st.sidebar.warning("Unknown user role. Limited access provided.")

# Add logout button
if st.sidebar.button("Logout"):
    # Clear session state and rerun to show login screen
    st.session_state.clear()
    st.rerun()

# --- Issue New Permit ---
if app_mode == "Issue New Permit":
    st.header("Issue a New Work Permit")

    # Initialize session state for likelihood and severity if they don't exist
    if "likelihood_new" not in st.session_state:
        st.session_state.likelihood_new = "1"  # Default value
    if "severity_new" not in st.session_state:
        st.session_state.severity_new = "1"    # Default value

    with st.form("permit_form", clear_on_submit=True):
        st.subheader("Step 1: Provide Permit Details")
        requester = st.text_input("Requester Name", key="requester_name_form_input")
        location = st.text_input("Work Location", key="location_form_input")
        work_type = st.selectbox("Work Type", options=WORK_TYPES, key="work_type_form_input", index=0)
        description = st.text_area("Work Description", key="description_form_input")

        st.subheader("Step 2: Specify Precautions")
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
                 if not selected_precautions:
                    error_messages.append("At least one precaution must be selected, or 'Other' specified.")

            if error_messages:
                for msg in error_messages:
                    st.warning(msg)
            else:
                permit_id = generate_permit_id()
                issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                precautions_to_save = ", ".join(final_precautions_list) if final_precautions_list else "None specified"

                # Get Likelihood, Severity, and calculate Risk Assessment from session state for saving
                current_likelihood_for_saving = st.session_state.likelihood_new
                current_severity_for_saving = st.session_state.severity_new
                risk_score_for_saving, _, _ = calculate_risk_assessment_details(
                    current_likelihood_for_saving,
                    current_severity_for_saving
                )

                new_permit_data = {
                    "Permit ID": permit_id, 
                    "Requester": requester,
                    "Location": location,
                    "Work Type": work_type,
                    "Description": description,
                    "Likelihood": current_likelihood_for_saving,
                    "Severity": current_severity_for_saving,
                    "Risk Assessment": str(risk_score_for_saving),
                    "Precautions": precautions_to_save,
                    "Issue Date": issue_date, 
                    "Status": "Pending",
                    "Supervisor Notes": "", 
                    "Supervisor Action Date": ""
                }
                for col_expected in EXPECTED_COLUMNS.keys():
                    if col_expected not in new_permit_data: new_permit_data[col_expected] = ""
                
                new_permit_df_row = pd.DataFrame([new_permit_data])
                new_permit_df_row = new_permit_df_row[list(EXPECTED_COLUMNS.keys())]
                st.session_state.df_permits = pd.concat([st.session_state.df_permits, new_permit_df_row], ignore_index=True)
                save_data(st.session_state.df_permits)
                st.success(f"Permit {permit_id} submitted successfully! The form has been cleared.")
                
                # Reset the dynamic likelihood and severity selectors to default for the next permit
                st.session_state.likelihood_new = "1"
                st.session_state.severity_new = "1"
                # No st.rerun() here, form clear_on_submit and session state reset should handle it.

    # --- Risk Assessment Section (OUTSIDE and AFTER the form) ---
    st.subheader("Step 3: Select Risk Parameters") 
    col_l, col_s = st.columns(2)
    with col_l:
        st.selectbox("Likelihood (1-5)", options=LIKELIHOOD_OPTIONS, key="likelihood_new")
    with col_s:
        st.selectbox("Severity (1-5)", options=SEVERITY_OPTIONS, key="severity_new")

    st.subheader("Step 4: View Calculated Risk") 
    # Dynamic calculation and display using current values from session state
    risk_score_val_int, risk_level_val, risk_color_val = calculate_risk_assessment_details(
        st.session_state.likelihood_new,
        st.session_state.severity_new
    )
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
                if int(st.session_state.likelihood_new) == l_loop and int(st.session_state.severity_new) == s_loop:
                    cell_style += " border: 3px solid black; font-weight: bold;"
            except ValueError: pass
            matrix_html += f"<td style='{cell_style}'>{cell_score}</td>"
        matrix_html += "</tr>"
    matrix_html += "</table>"
    st.markdown(matrix_html, unsafe_allow_html=True)
    st.markdown("---")

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
                    st.text_area("Precautions", value=permit_details.get("Precautions",""), disabled=True, height=100, key=f"rev_prec_{permit_details['Permit ID']}")
                    st.text_input("Issue Date", value=permit_details.get("Issue Date",""), disabled=True, key=f"rev_idate_{permit_details['Permit ID']}")
                
                st.markdown("---Supervisor Review Section---")
                with st.form(f"review_form_{permit_details['Permit ID']}"):
                    supervisor_notes = st.text_area("Supervisor Notes/Opinion", key=f"notes_rev_{permit_details['Permit ID']}")
                    approve_button = st.form_submit_button("Approve Permit")
                    reject_button = st.form_submit_button("Reject Permit")

                    if approve_button:
                        action_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.df_permits.loc[permit_index, "Status"] = "Approved"
                        st.session_state.df_permits.loc[permit_index, "Supervisor Notes"] = supervisor_notes if supervisor_notes else "Approved without notes."
                        st.session_state.df_permits.loc[permit_index, "Supervisor Action Date"] = action_date
                        save_data(st.session_state.df_permits)
                        st.success(f"Permit {selected_permit_id} Approved.")
                        st.rerun()
                    
                    if reject_button:
                        if supervisor_notes:
                            action_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.df_permits.loc[permit_index, "Status"] = "Rejected"
                            st.session_state.df_permits.loc[permit_index, "Supervisor Notes"] = supervisor_notes
                            st.session_state.df_permits.loc[permit_index, "Supervisor Action Date"] = action_date
                            save_data(st.session_state.df_permits)
                            st.success(f"Permit {selected_permit_id} Rejected.")
                            st.rerun()
                        else:
                            st.warning("Supervisor notes are required for rejection.")
            except IndexError:
                st.error("Could not find the selected permit. It might have been removed or changed.")
                st.rerun()
            except Exception as e_review:
                st.error(f"An unexpected error occurred during review: {e_review}")
                # Optionally log the full traceback here for debugging

# --- View All Permits ---
elif app_mode == "View All Permits":
    st.header("All Permits Overview")
    df_permits_all = st.session_state.df_permits
    if df_permits_all.empty:
        st.info("No permits have been issued yet.")
    else:
        st.dataframe(df_permits_all)
        # Optional: Add more detailed view similar to display_permits_with_feedback if needed
        # for index, row in df_permits_all.iterrows():
        #     with st.expander(f"Permit ID: {row['Permit ID']} - Status: {row['Status']}"):
        #         st.write(row)

# --- Display Raw Data Table (Optional) ---
if st.sidebar.checkbox("Show Raw Permit Data Table"):
    st.subheader("Raw Data Table")
    display_df = st.session_state.df_permits.copy()
    for col in EXPECTED_COLUMNS.keys():
        if col not in display_df.columns:
            display_df[col] = ""
    st.dataframe(display_df[list(EXPECTED_COLUMNS.keys())])

