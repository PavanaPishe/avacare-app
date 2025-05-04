import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets Setup ---
@st.cache_resource
def connect_to_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1aFhExzz3_BTNDzJ2h37YqxK6ij8diJCTbAwsPcdJQtM").sheet1
    return sheet

def get_next_patient_id(sheet):
    records = sheet.get_all_records()
    if not records:
        return "AVP-4000"
    last_id = sorted(records, key=lambda r: int(r["Patient_ID"].split("-")[1]))[-1]["Patient_ID"]
    new_number = int(last_id.split("-")[1]) + 1
    return f"AVP-{new_number}"

def register_new_patient(sheet, name):
    new_id = get_next_patient_id(sheet)
    sheet.append_row([name, new_id])
    return new_id

# --- Streamlit UI Config ---
st.set_page_config(page_title="AVACARE Assistant", page_icon="💼")
st.markdown("<h1 style='font-family: Arial; color: #002B5B;'>Welcome to AVACARE Virtual Assistant</h1>", unsafe_allow_html=True)

# --- Session State ---
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.chat_history = []
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.is_returning = None

# --- Navigation Helper ---
def go_back_to(state_name):
    if st.button("⬅️ Go Back"):
        st.session_state.chat_state = state_name
        st.rerun()

# --- STEP 1: Communication Mode ---
if st.session_state.chat_state == "choose_mode":
    st.subheader("Step 1: Select Your Communication Mode")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💬 Chat"):
            st.session_state.mode = "chat"
            st.session_state.chat_state = "choose_language"
    with col2:
        if st.button("🎙️ Voice"):
            st.session_state.mode = "voice"
            st.session_state.chat_state = "choose_language"
    with col3:
        if st.button("📞 Call"):
            st.session_state.mode = "ivr"
            st.session_state.chat_state = "choose_language"

# --- STEP 2: Language Selection ---
elif st.session_state.chat_state == "choose_language":
    st.subheader("Step 2: Select Preferred Language")
    st.session_state.language = st.radio("Choose a language:", ["English", "Hindi", "Spanish"])
    if st.button("Continue"):
        st.session_state.chat_state = "greeting"
        st.rerun()
    go_back_to("choose_mode")

# --- STEP 3: Greeting ---
elif st.session_state.chat_state == "greeting":
    greetings = {
        "English": "Hi, how are you doing today?",
        "Hindi": "नमस्ते, आज आप कैसे हैं?",
        "Spanish": "Hola, ¿cómo estás hoy?"
    }
    st.subheader("AVA Conversation")
    st.markdown(f"<div style='font-family: Verdana; font-size: 16px;'>{greetings[st.session_state.language]}</div>", unsafe_allow_html=True)
    user_reply = st.text_input("Your Response:")
    if user_reply:
        st.session_state.chat_history.append(f"You: {user_reply}")
        st.session_state.chat_state = "ask_identity"
        st.rerun()

# --- STEP 4: Patient Type ---
elif st.session_state.chat_state == "ask_identity":
    st.subheader("Are you a returning patient?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.is_returning = True
            st.session_state.chat_state = "get_returning_info"
    with col2:
        if st.button("No"):
            st.session_state.is_returning = False
            st.session_state.chat_state = "get_new_info"

# --- STEP 5A: Returning Patient ---
elif st.session_state.chat_state == "get_returning_info":
    st.subheader("Please provide your details")
    st.session_state.name = st.text_input("Your Full Name:")
    st.session_state.patient_id = st.text_input("Your Patient ID (e.g., AVP-1054):")

    if st.session_state.name and st.session_state.patient_id:
        sheet = connect_to_google_sheet()
        records = sheet.get_all_records()
        match = next((rec for rec in records if rec["Patient_ID"] == st.session_state.patient_id), None)
        if match:
            st.success(f"Welcome back, {st.session_state.name}! You're verified.")
        else:
            st.error("Patient ID not found. Please try again.")
    go_back_to("ask_identity")

# --- STEP 5B: New Patient ---
elif st.session_state.chat_state == "get_new_info":
    st.subheader("Let's get you registered")
    st.session_state.name = st.text_input("Your Full Name:")
    if st.session_state.name:
        sheet = connect_to_google_sheet()
        new_id = register_new_patient(sheet, st.session_state.name)
        st.session_state.patient_id = new_id
        st.success(f"Thanks, {st.session_state.name}. You’ve been registered with Patient ID: {new_id}")
    go_back_to("ask_identity")

# --- STEP 6: PATIENT DASHBOARD ---
elif st.session_state.chat_state == "main_menu":
    st.subheader(f"Welcome, {st.session_state.name}")
    st.markdown("Please select one of the following options to proceed:")

    option = st.radio("Available Actions", [
        "Book an Appointment",
        "View Appointment History",
        "Update Contact Information",
        "Exit Session"
    ])

    if option == "Book an Appointment":
        st.session_state.chat_state = "booking_flow"
        st.rerun()

    elif option == "View Appointment History":
        st.write("This section will display past and upcoming appointments. (Coming soon)")

    elif option == "Update Contact Information":
        st.write("Feature to update your contact or location details will be available soon.")

    elif option == "Exit Session":
        st.success("Thank you for using AVACARE. You may now close the session.")

