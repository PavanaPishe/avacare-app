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

@st.cache_data
def load_doctor_data():
    df_profile = pd.read_excel("AVACARE_20_Doctors_Info_and_Availability.xlsx", sheet_name="Doctor_Info")
    df_slots = pd.read_excel("AVACARE_20_Doctors_Info_and_Availability.xlsx", sheet_name="Doctor_Availability")
    return df_profile, df_slots

# --- UI Setup ---
st.set_page_config(page_title="AVACARE Assistant", page_icon="💼")
st.markdown("<h1 style='font-family: Arial; color: #002B5B;'>Hey! My name is AVA!</h1>", unsafe_allow_html=True)

if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.chat_history = []
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.is_returning = None
    st.session_state.selected_action = None
    st.session_state.symptoms = ""

def go_back_to(state_name):
    if st.button("⬅️ Go Back"):
        st.session_state.chat_state = state_name
        st.rerun()
# --- STEP 1: Communication Mode ---
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

# --- STEP 2: Language ---
elif st.session_state.chat_state == "choose_language":
    st.subheader("Step 2: Select your preferred language")
    st.session_state.language = st.radio("Language", ["English", "Hindi", "Spanish"])
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
    st.subheader("AVA Assistant")
    st.markdown(f"<div style='font-family: Verdana; font-size: 16px;'>{greetings[st.session_state.language]}</div>", unsafe_allow_html=True)
    user_reply = st.text_input("Your Response:")
    if user_reply:
        st.session_state.chat_history.append(f"You: {user_reply}")
        st.session_state.chat_state = "ask_identity"
        st.rerun()

# --- STEP 4: Ask if Returning ---
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

# --- STEP 5A: Returning Patient Verification ---
elif st.session_state.chat_state == "get_returning_info":
    sheet = connect_to_google_sheet()
    patients_df = load_patient_dataframe(sheet)

    st.subheader("Verify Your Identity")
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

# --- STEP 5B: New Patient Registration ---
elif st.session_state.chat_state == "get_new_info":
    st.subheader("Register as a New Patient")
    name_input = st.text_input("Full Name:")
    if name_input:
        sheet = connect_to_google_sheet()
        new_id = register_new_patient(sheet, name_input)
        st.session_state.name = name_input
        st.session_state.patient_id = new_id
        st.success(f"You're registered! Your Patient ID is {new_id}")
        st.session_state.chat_state = "main_menu"
        st.rerun()
    go_back_to("ask_identity")

# --- STEP 6: Main Menu After Verification ---
elif st.session_state.chat_state == "main_menu":
    st.subheader(f"Hello, {st.session_state.name} 👋")
    st.markdown("Please choose what you'd like to do next:")

    st.session_state.selected_action = st.radio("Available Actions", [
        "📅 Book an Appointment",
        "🧾 View Last Prescription (Coming Soon)",
        "🔁 Reschedule an Appointment (Coming Soon)",
        "📝 Update Contact Info (Coming Soon)",
        "🚪 Exit"
    ])

    if st.button("Proceed"):
        if st.session_state.selected_action == "📅 Book an Appointment":
            st.session_state.chat_state = "ask_symptoms"
        elif st.session_state.selected_action == "🚪 Exit":
            st.success("Thank you for using AVACARE! Stay well.")
        else:
            st.info("This feature is coming soon!")
        st.rerun()
# --- Step 7: Booking Flow with Symptom Mapping ---
elif st.session_state.chat_state == "booking_flow":
    st.subheader("🩺 Book an Appointment")

    # 1. Ask for symptom
    if "symptom_collected" not in st.session_state:
        st.session_state.symptom_collected = False

    if not st.session_state.symptom_collected:
        symptom = st.text_input("Please tell me your primary symptom:")
        if symptom:
            st.session_state.user_symptom = symptom.lower()

            # Simple symptom-to-specialty mapping
            symptom_map = {
                "fever": "General Physician",
                "cold": "General Physician",
                "cough": "General Physician",
                "toothache": "Dentist",
                "skin rash": "Dermatologist",
                "ear pain": "ENT Specialist",
                "child fever": "Pediatrics",
                "anxiety": "Psychologist",
                "pain during periods": "Gynecologist",
                "back pain": "Orthopedic",
                "muscle strain": "Physiotherapist"
            }

            # Assign recommended specialty
            recommended_specialty = symptom_map.get(st.session_state.user_symptom, None)
            if recommended_specialty:
                st.session_state.recommended_specialty = recommended_specialty
                st.success(f"Based on your symptom, we recommend you see a **{recommended_specialty}**.")
                st.session_state.symptom_collected = True
                st.rerun()
            else:
                st.warning("Sorry, we couldn't map your symptom. Please try a different description.")
        go_back_to("main_menu")

    else:
        doctor_df, availability_df = load_doctor_data()
        specialty = st.session_state.recommended_specialty

        # Filter doctors
        filtered_doctors = doctor_df[doctor_df["Specialty"] == specialty]
        doctor_names = filtered_doctors["Doctor_Name"].tolist()
        selected_doctor = st.selectbox("Choose a doctor:", doctor_names)

        # Show open slots
        doctor_id = filtered_doctors[filtered_doctors["Doctor_Name"] == selected_doctor]["Doctor_ID"].values[0]
        available_slots = availability_df[
            (availability_df["Doctor_ID"] == doctor_id) & (availability_df["Slot_Status"] == "Open")
        ]

        if not available_slots.empty:
            slot_options = available_slots["Date"] + " " + available_slots["Start_Time"]
            selected_slot = st.selectbox("Choose an available time:", slot_options)

            if st.button("Confirm Appointment"):
                st.success(f"✅ Appointment booked with Dr. {selected_doctor} on {selected_slot}")
                st.session_state.chat_state = "main_menu"
                st.session_state.symptom_collected = False  # Reset for next time
                st.rerun()
        else:
            st.warning("No open slots available for this doctor.")
        go_back_to("main_menu")


