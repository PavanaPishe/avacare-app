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
st.set_page_config(page_title="AVACARE Assistant", page_icon="💼", layout="centered")

st.markdown("<h1 style='font-family: Arial; color: #002B5B;'>💬 AVACARE Assistant</h1>", unsafe_allow_html=True)

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.language = "English"
    st.session_state.is_returning = None
    st.session_state.selected_action = None

# --- Chat message helper ---
def bot_say(msg):
    st.session_state.messages.append(("AVA", msg))

def user_say(msg):
    st.session_state.messages.append(("You", msg))

for sender, msg in st.session_state.messages:
    icon = "🧠" if sender == "AVA" else "🧑"
    st.markdown(f"**{icon} {sender}:** {msg}")

# --- Chat State Machine ---
if st.session_state.chat_state == "choose_mode":
    bot_say("Welcome! Please choose your preferred communication mode.")
    comm = st.radio("Select Mode", ["Chat", "Voice", "Call"])
    if st.button("Continue"):
        st.session_state.chat_state = "ask_identity"
        st.rerun()

elif st.session_state.chat_state == "ask_identity":
    bot_say("Are you a returning patient?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.is_returning = True
            st.session_state.chat_state = "verify_returning"
            st.rerun()
    with col2:
        if st.button("No"):
            st.session_state.is_returning = False
            st.session_state.chat_state = "register_new"
            st.rerun()

elif st.session_state.chat_state == "verify_returning":
    sheet = connect_to_google_sheet()
    df = load_patient_dataframe(sheet)
    name = st.text_input("Your Full Name:")
    pid = st.text_input("Your Patient ID (e.g., AVP-1054):")
    if st.button("Verify"):
        match = df[df["Patient_ID"] == pid]
        if not match.empty:
            user_say(name)
            st.success("You're verified.")
            st.session_state.name = name
            st.session_state.patient_id = pid
            st.session_state.chat_state = "main_menu"
            st.rerun()
        else:
            st.error("No matching record found.")

elif st.session_state.chat_state == "register_new":
    sheet = connect_to_google_sheet()
    name = st.text_input("Enter your full name:")
    if st.button("Register"):
        new_id = register_new_patient(sheet, name)
        st.success(f"Registered! Your Patient ID is {new_id}")
        st.session_state.name = name
        st.session_state.patient_id = new_id
        st.session_state.chat_state = "main_menu"
        st.rerun()

elif st.session_state.chat_state == "main_menu":
    bot_say(f"Welcome, {st.session_state.name}! What would you like to do today?")
    option = st.radio("Options", [
        "📅 Book an Appointment",
        "🧾 View Last Prescription (Coming Soon)",
        "🔁 Reschedule an Appointment (Coming Soon)",
        "📝 Update Contact Info (Coming Soon)",
        "🚪 Exit"
    ])
    if st.button("Proceed"):
        if option == "📅 Book an Appointment":
            st.session_state.chat_state = "ask_symptoms"
        elif option == "🚪 Exit":
            st.success("Thank you for using AVACARE!")
        else:
            st.info("Feature coming soon.")
        st.rerun()

elif st.session_state.chat_state == "ask_symptoms":
    symptom = st.text_input("What symptom are you experiencing?")
    if st.button("Submit Symptom"):
        symptom_map = {
            "fever": "General Physician",
            "cold": "General Physician",
            "cough": "General Physician",
            "toothache": "Dentist",
            "skin rash": "Dermatologist",
            "ear pain": "ENT Specialist",
            "child fever": "Pediatrics",
            "anxiety": "Psychologist",
            "period pain": "Gynecologist",
            "back pain": "Orthopedic",
            "muscle strain": "Physiotherapist"
        }
        st.session_state.symptom = symptom
        st.session_state.specialty = symptom_map.get(symptom.lower(), None)
        if st.session_state.specialty:
            st.success(f"Based on your symptom, we recommend you see a {st.session_state.specialty}.")
            st.session_state.chat_state = "book_doctor"
            st.rerun()
        else:
            st.warning("Symptom not recognized. Please try a different keyword.")

elif st.session_state.chat_state == "book_doctor":
    doctor_df, availability_df = load_doctor_data()
    spec = st.session_state.specialty
    filtered = doctor_df[doctor_df["Specialty"] == spec]
    if filtered.empty:
        st.error("No doctors available.")
    else:
        doc_names = filtered["Doctor_Name"].tolist()
        doc_choice = st.selectbox("Choose a doctor:", doc_names)
        doc_id = filtered[filtered["Doctor_Name"] == doc_choice]["Doctor_ID"].values[0]
        slots = availability_df[(availability_df["Doctor_ID"] == doc_id) & (availability_df["Slot_Status"] == "Open")]
        if not slots.empty:
            slot_options = slots["Date"] + " " + slots["Start_Time"]
            slot_choice = st.selectbox("Choose an available slot:", slot_options)
            if st.button("Confirm Appointment"):
                st.success(f"Appointment booked with Dr. {doc_choice} on {slot_choice}")
                st.session_state.chat_state = "main_menu"
                st.rerun()
        else:
            st.warning("No slots available.")
