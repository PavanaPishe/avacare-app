import streamlit as st
import pandas as pd
import uuid

# Title & setup
st.set_page_config(page_title="AVACARE Virtual Assistant", page_icon="💬")
st.title("💬 AVACARE Virtual Assistant (Ava)")

# Load data
@st.cache_data
def load_data():
    patients = pd.read_csv("AVACARE_Patient_Dataset_Aligned.csv")
    xls = pd.ExcelFile("AVACARE_20_Doctors_Info_and_Availability.xlsx")
    doctor_info = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    availability = pd.read_excel(xls, sheet_name=xls.sheet_names[1])
    return patients, doctor_info, availability

patients_df, doctor_info_df, availability_df = load_data()

# Session state setup
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "greeting"
    st.session_state.mode = ""
    st.session_state.returning = None
    st.session_state.patient_data = None
    st.session_state.patient_id = ""
    st.session_state.name = ""

# Step 1: Channel selection
if st.session_state.chat_state == "greeting":
    st.write("👋 Hello! I'm Ava, your AI scheduling assistant.")
    st.session_state.mode = st.radio("How would you like to communicate?", ["💬 Chat", "📞 Voice", "📱 IVR"])

    if st.session_state.mode == "💬 Chat":
        st.session_state.chat_state = "ask_returning"
    elif st.session_state.mode in ["📞 Voice", "📱 IVR"]:
        st.warning("⚠️ Voice and IVR support is coming soon! For now, please continue via Chat.")
        st.session_state.chat_state = "ask_returning"

# Step 2: Ask if returning or new
elif st.session_state.chat_state == "ask_returning":
    st.session_state.returning = st.radio("Are you a returning patient?", ["Yes", "No"])

    if st.session_state.returning == "Yes":
        st.session_state.chat_state = "ask_returning_id"
    elif st.session_state.returning == "No":
        st.session_state.chat_state = "register_new"

# Step 3A: Returning user flow
elif st.session_state.chat_state == "ask_returning_id":
    st.session_state.name = st.text_input("Please enter your full name:")
    st.session_state.patient_id = st.text_input("Please enter your Patient ID (e.g., AVP-1021):")

    if st.session_state.name and st.session_state.patient_id:
        matched = patients_df[patients_df["Patient_ID"] == st.session_state.patient_id]
        if not matched.empty:
            st.session_state.patient_data = matched.iloc[0]
            st.session_state.chat_state = "loaded"
        else:
            st.error("❌ Couldn't find your Patient ID. Please check again or continue as a new patient.")

# Step 3B: New user flow
elif st.session_state.chat_state == "register_new":
    st.session_state.name = st.text_input("Welcome! Please enter your full name to get started:")

    if st.session_state.name:
        # Generate a new unique patient ID
        new_id = "AVP-" + str(uuid.uuid4())[:8].upper()
        st.success(f"Thanks {st.session_state.name}! Your new Patient ID is: {new_id}")
        # You could optionally also collect more details and append to patients_df
        st.session_state.patient_id = new_id
        st.session_state.patient_data = None  # Not from dataset yet
        st.session_state.chat_state = "new_user_ready"
