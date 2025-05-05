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

def load_patient_dataframe(sheet):
    records = sheet.get_all_records()
    return pd.DataFrame(records)

# Load doctor data once globally
@st.cache_data
def load_doctor_data():
    df_profile = pd.read_excel("AVACARE_20_Doctors_Info_and_Availability.xlsx", sheet_name="Doctor_Info")
    df_slots = pd.read_excel("AVACARE_20_Doctors_Info_and_Availability.xlsx", sheet_name="Doctor_Availability")
    return df_profile, df_slots

# --- UI Setup ---
st.set_page_config(page_title="AVACARE Assistant", page_icon="💼")
st.markdown("<h1 style='font-family: Arial; color: #002B5B;'>AVACARE Virtual Assistant</h1>", unsafe_allow_html=True)

# --- Session Initialization ---
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.chat_history = []
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.is_returning = None

def go_back_to(state_name):
    if st.button("⬅️ Go Back"):
        st.session_state.chat_state = state_name
        st.rerun()

# --- Step 1: Communication Mode ---
if st.session_state.chat_state == "choose_mode":
    st.subheader("Step 1: Choose how you'd like to communicate")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Chat"):
            st.session_state.mode = "chat"
            st.session_state.chat_state = "choose_language"
    with col2:
        if st.button("Voice"):
            st.session_state.mode = "voice"
            st.session_state.chat_state = "choose_language"
    with col3:
        if st.button("Call"):
            st.session_state.mode = "ivr"
            st.session_state.chat_state = "choose_language"

# --- Step 2: Language ---
elif st.session_state.chat_state == "choose_language":
    st.subheader("Step 2: Select your preferred language")
    st.session_state.language = st.radio("Language", ["English", "Hindi", "Spanish"])
    if st.button("Continue"):
        st.session_state.chat_state = "greeting"
        st.rerun()
    go_back_to("choose_mode")

# --- Step 3: Greeting ---
elif st.session_state.chat_state == "greeting":
    greetings = {
        "English": "Hi, how are you doing today?",
        "Hindi": "नमस्ते, आज आप कैसे हैं?",
        "Spanish": "Hola, ¿cómo estás hoy?"
    }
    st.subheader("Conversation")
    st.markdown(f"<div style='font-family: Verdana; font-size: 16px;'>{greetings[st.session_state.language]}</div>", unsafe_allow_html=True)
    user_reply = st.text_input("Your Response:")
    if user_reply:
        st.session_state.chat_state = "ask_identity"
        st.rerun()

# --- Step 4: Returning/New ---
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

# --- Step 5A: Returning Patient ---
elif st.session_state.chat_state == "get_returning_info":
    sheet = connect_to_google_sheet()
    patients_df = load_patient_dataframe(sheet)

    st.subheader("Please provide your details")
    name_input = st.text_input("Full Name:", value=st.session_state.name)
    id_input = st.text_input("Patient ID (e.g., AVP-1054):", value=st.session_state.patient_id)

    if name_input and id_input:
        st.session_state.name = name_input
        st.session_state.patient_id = id_input
        match = patients_df[patients_df["Patient_ID"] == id_input]
        if not match.empty:
            st.success(f"Welcome back, {st.session_state.name}. You're verified.")
            st.session_state.chat_state = "main_menu"
            st.rerun()
        else:
            st.error("Patient ID not found.")
    go_back_to("ask_identity")

# --- Step 5B: New Patient ---
elif st.session_state.chat_state == "get_new_info":
    st.subheader("Register as a new patient")
    name_input = st.text_input("Full Name:")
    if name_input:
        sheet = connect_to_google_sheet()
        new_id = register_new_patient(sheet, name_input)
        st.session_state.name = name_input
        st.session_state.patient_id = new_id
        st.success(f"Registered! Your Patient ID is {new_id}")
        st.session_state.chat_state = "main_menu"
        st.rerun()
    go_back_to("ask_identity")

# --- Step 6: Patient Dashboard ---
elif st.session_state.chat_state == "main_menu":
    st.subheader(f"Welcome, {st.session_state.name}")
    option = st.radio("Options", [
        "Book an Appointment",
        "View Appointment History",
        "Update Contact Information",
        "Exit"
    ])
    if option == "Book an Appointment":
        st.session_state.chat_state = "booking_flow"
        st.rerun()
    elif option == "View Appointment History":
        st.info("This section will soon display your previous and upcoming appointments.")
    elif option == "Update Contact Information":
        st.info("Feature coming soon: Update phone number or location.")
    elif option == "Exit":
        st.success("Thank you for using AVACARE.")

# --- Step 7: Booking Flow ---
elif st.session_state.chat_state == "booking_flow":
    st.subheader("Book an Appointment")

    doctor_df, availability_df = load_doctor_data()

    # Step 1: Choose Specialty
    specializations = doctor_df["Specialty"].unique()
    selected_specialty = st.selectbox("Choose a specialization", specializations)

    # Step 2: Choose Doctor
    filtered_doctors = doctor_df[doctor_df["Specialty"] == selected_specialty]
    doctor_names = filtered_doctors["Name"].tolist()
    selected_doctor = st.selectbox("Select a doctor", doctor_names)

    # Step 3: Available Slots
    doctor_id = filtered_doctors[filtered_doctors["Name"] == selected_doctor]["Doctor_ID"].values[0]
    available_slots = availability_df[
        (availability_df["Doctor_ID"] == doctor_id) & (availability_df["Status"] == "Open")
    ]

    if not available_slots.empty:
        slot_options = available_slots["Day"] + " - " + available_slots["Time"]
        selected_slot = st.selectbox("Choose a slot", slot_options)

        if st.button("Confirm Appointment"):
            st.success(f"Appointment booked with Dr. {selected_doctor} on {selected_slot}")
            st.session_state.chat_state = "main_menu"
            st.rerun()
    else:
        st.warning("No slots available for this doctor.")
    go_back_to("main_menu")
