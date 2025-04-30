# Streamlit Work Permit System

import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Configuration ---
DATA_FILE = "work_permits.csv"

# --- Dropdown Options ---
WORK_TYPES = ["", "Hot Work", "Confined Space Entry", "Working at Height", "Electrical Work", "Excavation", "General Maintenance", "Other"]
RISK_LEVELS = ["", "Low", "Medium", "High"]
PRECAUTIONS = ["", "Use Standard PPE", "Lockout/Tagout Required", "Fire Watch Required", "Atmospheric Testing Needed", "Ventilation Required", "Buddy System Mandatory", "Fall Protection Required", "Other (Specify in Description)"]

# Define expected columns and their types
EXPECTED_COLUMNS = {
    "Permit ID": str,
    "Requester": str,
    "Location": str,
    "Work Type": str, # New
    "Description": str,
    "Risk Assessment": str, # New
    "Precautions": str, # New
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
            df = pd.read_csv(DATA_FILE, dtype=str, keep_default_na=False) # Read all as string initially
            # Ensure all expected columns exist, add if missing
            for col, dtype in EXPECTED_COLUMNS.items():
                if col not in df.columns:
                    df[col] = ""
            # Reorder columns to match expected order and select only expected columns
            df = df[list(EXPECTED_COLUMNS.keys())]
            # Convert to correct types (though reading as string is often safer for consistency)
            # df = df.astype(EXPECTED_COLUMNS)
            # Fill NaN specifically for notes/date which might cause issues if not string
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
        # Ensure DataFrame only contains expected columns before saving
        df_to_save = df[list(EXPECTED_COLUMNS.keys())].copy()
        df_to_save.to_csv(DATA_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def generate_permit_id():
    """Generates a unique permit ID based on timestamp."""
    return f"WP-{datetime.now().strftime("%Y%m%d%H%M%S%f")}"

# --- Load Data ---
if 'df_permits' not in st.session_state:
    st.session_state.df_permits = load_data()

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("Work Permit System")

# --- Sidebar for Navigation/Actions ---
st.sidebar.header("Actions")
app_mode = st.sidebar.selectbox("Choose Mode", ["Issue New Permit", "Review Permits", "View All Permits"])

# --- Function to display permits with feedback ---
def display_permits_with_feedback(df_display):
    """Displays permits with a feedback box for reviewed items."""
    if df_display.empty:
        st.info("No permits to display in this view.")
        return

    # Ensure new columns exist in the dataframe being displayed
    for col in ["Work Type", "Risk Assessment", "Precautions"]:
         if col not in df_display.columns:
             df_display[col] = "" # Add missing columns with default empty string

    for index, permit in df_display.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([3, 2])
            with col1:
                st.subheader(f"Permit ID: {permit.get('Permit ID', 'N/A')}")
                st.write(f"**Requester:** {permit.get('Requester', '')}")
                st.write(f"**Location:** {permit.get('Location', '')}")
                st.write(f"**Work Type:** {permit.get('Work Type', '')}") # Display Work Type
                st.write(f"**Description:** {permit.get('Description', '')}")
                st.write(f"**Risk Assessment:** {permit.get('Risk Assessment', '')}") # Display Risk Assessment
                st.write(f"**Precautions:** {permit.get('Precautions', '')}") # Display Precautions
                st.write(f"**Issue Date:** {permit.get('Issue Date', '')}")
                st.write(f"**Status:** {permit.get('Status', '')}")

            with col2:
                status = permit.get('Status', 'Pending')
                notes = permit.get('Supervisor Notes', '')
                action_date = permit.get('Supervisor Action Date', '')
                if status != "Pending":
                    with st.container(border=True):
                        st.markdown("**Supervisor Feedback**")
                        if notes:
                            st.write(f"**Opinion/Notes:** {notes}")
                        else:
                            st.write("Permit actioned, no notes provided.")
                        if action_date:
                            st.write(f"**Action Date:** {action_date}")
                else:
                    st.markdown("_(Pending Review)_")
            st.divider()

# --- Main Application Logic ---
if app_mode == "Issue New Permit":
    st.header("Issue a New Work Permit")
    with st.form("permit_form", clear_on_submit=True):
        requester = st.text_input("Requester Name")
        location = st.text_input("Work Location")
        # Add dropdowns
        work_type = st.selectbox("Work Type", options=WORK_TYPES)
        description = st.text_area("Work Description")
        risk_assessment = st.selectbox("Risk Assessment", options=RISK_LEVELS)
        precautions = st.selectbox("Precautions", options=PRECAUTIONS)

        submitted = st.form_submit_button("Submit Permit Request")

        if submitted:
            # Basic validation including new fields
            if requester and location and description and work_type and risk_assessment and precautions:
                permit_id = generate_permit_id()
                issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_permit_data = {
                    "Permit ID": permit_id,
                    "Requester": requester,
                    "Location": location,
                    "Work Type": work_type, # Save Work Type
                    "Description": description,
                    "Risk Assessment": risk_assessment, # Save Risk Assessment
                    "Precautions": precautions, # Save Precautions
                    "Issue Date": issue_date,
                    "Status": "Pending",
                    "Supervisor Notes": "",
                    "Supervisor Action Date": ""
                }
                # Ensure all columns are present when creating the new DataFrame row
                for col in EXPECTED_COLUMNS.keys():
                    if col not in new_permit_data:
                        new_permit_data[col] = ""

                new_permit = pd.DataFrame([new_permit_data])
                # Ensure the new permit DataFrame has the same columns as the main one
                new_permit = new_permit[list(EXPECTED_COLUMNS.keys())]

                st.session_state.df_permits = pd.concat([st.session_state.df_permits, new_permit], ignore_index=True)
                save_data(st.session_state.df_permits)
                st.success(f"Permit {permit_id} submitted successfully!")
            else:
                st.warning("Please fill in all fields, including Work Type, Risk Assessment, and Precautions.")

elif app_mode == "Review Permits":
    st.header("Review Pending Work Permits")

    if st.session_state.df_permits.empty:
        st.info("No permits found.")
    else:
        # Ensure the main dataframe has all columns before filtering
        for col in EXPECTED_COLUMNS.keys():
            if col not in st.session_state.df_permits.columns:
                 st.session_state.df_permits[col] = ""

        pending_permits = st.session_state.df_permits[st.session_state.df_permits["Status"] == "Pending"].copy()

        if pending_permits.empty:
            st.info("No permits currently pending review.")
        else:
            permit_ids = pending_permits["Permit ID"].tolist()
            selected_permit_id = st.selectbox("Select Permit to Review", permit_ids, index=None, placeholder="Select a permit...")

            if selected_permit_id:
                permit_index = st.session_state.df_permits.index[st.session_state.df_permits["Permit ID"] == selected_permit_id].tolist()[0]
                permit_details = st.session_state.df_permits.loc[permit_index]

                st.subheader(f"Reviewing Permit: {selected_permit_id}")
                # Display details including new fields
                st.write(f"**Requester:** {permit_details.get('Requester', '')}")
                st.write(f"**Work Type:** {permit_details.get('Work Type', '')}")
                st.write(f"**Risk Assessment:** {permit_details.get('Risk Assessment', '')}")
                st.write(f"**Precautions:** {permit_details.get('Precautions', '')}")
                st.write(f"**Original Location:** {permit_details.get('Location', '')}")
                st.write(f"**Original Description:** {permit_details.get('Description', '')}")
                st.write(f"**Issue Date:** {permit_details.get('Issue Date', '')}")

                with st.form(f"review_form_{selected_permit_id}"):
                    st.markdown("**Supervisor Actions**")
                    # Allow editing description and location (keep editing capability)
                    edited_location = st.text_input("Edit Location (Optional)", value=permit_details.get('Location', ''))
                    edited_description = st.text_area("Edit Description (Optional)", value=permit_details.get('Description', ''))
                    # Display selected Work Type, Risk, Precautions (non-editable in review form for now)
                    st.markdown(f"**Selected Work Type:** {permit_details.get('Work Type', 'N/A')}")
                    st.markdown(f"**Selected Risk Assessment:** {permit_details.get('Risk Assessment', 'N/A')}")
                    st.markdown(f"**Selected Precautions:** {permit_details.get('Precautions', 'N/A')}")

                    supervisor_notes = st.text_area("Supervisor Notes/Opinion", key=f"notes_{selected_permit_id}")

                    col1, col2 = st.columns(2)
                    with col1:
                        approve_button = st.form_submit_button("Approve Permit", use_container_width=True)
                    with col2:
                        reject_button = st.form_submit_button("Reject Permit", use_container_width=True)

                    if approve_button:
                        action_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.df_permits.loc[permit_index, "Status"] = "Approved"
                        st.session_state.df_permits.loc[permit_index, "Supervisor Notes"] = supervisor_notes if supervisor_notes else "Approved without notes."
                        st.session_state.df_permits.loc[permit_index, "Supervisor Action Date"] = action_date
                        st.session_state.df_permits.loc[permit_index, "Location"] = edited_location
                        st.session_state.df_permits.loc[permit_index, "Description"] = edited_description
                        # Keep original Work Type, Risk, Precautions on approval
                        save_data(st.session_state.df_permits)
                        st.success(f"Permit {selected_permit_id} Approved.")
                        st.rerun()

                    if reject_button:
                        if supervisor_notes:
                            action_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.df_permits.loc[permit_index, "Status"] = "Rejected"
                            st.session_state.df_permits.loc[permit_index, "Supervisor Notes"] = supervisor_notes
                            st.session_state.df_permits.loc[permit_index, "Supervisor Action Date"] = action_date
                            # Revert edits on rejection
                            st.session_state.df_permits.loc[permit_index, "Location"] = permit_details.get('Location', '')
                            st.session_state.df_permits.loc[permit_index, "Description"] = permit_details.get('Description', '')
                            save_data(st.session_state.df_permits)
                            st.success(f"Permit {selected_permit_id} Rejected.")
                            st.rerun()
                        else:
                            st.warning("Supervisor notes are required for rejection.")
            else:
                 st.info("Select a pending permit from the dropdown above to review.")

        # Display pending permits using the updated function
        st.subheader("Pending Permits List")
        display_permits_with_feedback(pending_permits)

elif app_mode == "View All Permits":
    st.header("All Permits Overview")
    # Use the updated display function for all permits
    display_permits_with_feedback(st.session_state.df_permits)


# --- Display Raw Data Table (Optional) ---
if st.sidebar.checkbox("Show Raw Permit Data Table"):
    st.subheader("Raw Data Table")
    # Ensure all columns exist before displaying the raw dataframe
    display_df = st.session_state.df_permits.copy()
    for col in EXPECTED_COLUMNS.keys():
        if col not in display_df.columns:
            display_df[col] = ""
    st.dataframe(display_df[list(EXPECTED_COLUMNS.keys())]) # Show in expected order