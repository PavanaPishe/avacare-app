import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------- Google Sheets Setup ----------------
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

# ---------------- Streamlit Setup ----------------
st.set_page_config(page_title="AVACARE Chatbot", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
if "name" not in st.session_state:
    st.session_state.name = ""
if "patient_id" not in st.session_state:
    st.session_state.patient_id = ""
if "is_returning" not in st.session_state:
    st.session_state.is_returning = None
if "symptom_collected" not in st.session_state:
    st.session_state.symptom_collected = False

def add_bot_message(message):
    st.session_state.chat_history.append(("bot", message))

def add_user_message(message):
    st.session_state.chat_history.append(("user", message))

# ---------------- Chat UI ----------------
st.title("💬 AVACARE Assistant")

for sender, message in st.session_state.chat_history:
    if sender == "bot":
        st.markdown(f"🩺 **AVA:** {message}")
    else:
        st.markdown(f"**You:** {message}")

# ---------------- Logic Flow ----------------

if st.session_state.chat_state == "choose_mode":
    add_bot_message("Welcome! Please choose your preferred communication mode.")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💬 Chat"):
            st.session_state.chat_state = "ask_language"
            st.rerun()
    with col2:
        if st.button("🎙️ Voice"):
            st.session_state.chat_state = "ask_language"
            st.rerun()
    with col3:
        if st.button("📞 IVR"):
            st.session_state.chat_state = "ask_language"
            st.rerun()

elif st.session_state.chat_state == "ask_language":
    language = st.radio("Choose your language", ["English", "Hindi", "Spanish"])
    if st.button("Continue"):
        add_bot_message(f"You selected **{language}**. How are you feeling today?")
        st.session_state.chat_state = "ask_identity"
        st.rerun()

elif st.session_state.chat_state == "ask_identity":
    add_bot_message("Are you a returning patient?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.is_returning = True
            st.session_state.chat_state = "get_returning_info"
            st.rerun()
    with col2:
        if st.button("No"):
            st.session_state.is_returning = False
            st.session_state.chat_state = "get_new_info"
            st.rerun()

elif st.session_state.chat_state == "get_returning_info":
    name = st.text_input("Your Full Name:")
    pid = st.text_input("Your Patient ID (e.g., AVP-1054):")
    if name and pid:
        sheet = connect_to_google_sheet()
        df = load_patient_dataframe(sheet)
        if not df[df["Patient_ID"] == pid].empty:
            st.session_state.name = name
            st.session_state.patient_id = pid
            add_bot_message(f"Welcome back, {name}. You're verified ✅")
            st.session_state.chat_state = "main_menu"
            st.rerun()
        else:
            add_bot_message("❌ ID not found. Please check again.")

elif st.session_state.chat_state == "get_new_info":
    name = st.text_input("Enter your Full Name to register:")
    if name:
        sheet = connect_to_google_sheet()
        new_id = register_new_patient(sheet, name)
        st.session_state.name = name
        st.session_state.patient_id = new_id
        add_bot_message(f"Hi {name}! You’ve been registered. Your Patient ID is **{new_id}**.")
        st.session_state.chat_state = "main_menu"
        st.rerun()

elif st.session_state.chat_state == "main_menu":
    choice = st.selectbox("What would you like to do?", [
        "📅 Book an Appointment",
        "🧾 View Last Prescription (Coming Soon)",
        "🔁 Reschedule an Appointment (Coming Soon)",
        "📝 Update Contact Info (Coming Soon)",
        "🚪 Exit"
    ])
    if st.button("Proceed"):
        if choice == "📅 Book an Appointment":
            st.session_state.chat_state = "ask_symptom"
        elif choice == "🚪 Exit":
            add_bot_message("Thank you for using AVACARE. Goodbye!")
        else:
            add_bot_message("This feature is coming soon.")
        st.rerun()

elif st.session_state.chat_state == "ask_symptom":
    symptom = st.text_input("What symptom are you experiencing?")
    if symptom:
        st.session_state.user_symptom = symptom.lower()
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
        specialty = symptom_map.get(st.session_state.user_symptom, None)
        if specialty:
            st.session_state.recommended_specialty = specialty
            add_bot_message(f"Based on your symptom, we recommend a **{specialty}**.")
            st.session_state.chat_state = "select_doctor"
            st.rerun()
        else:
            add_bot_message("We couldn't identify the specialty. Please try a different symptom.")

elif st.session_state.chat_state == "select_doctor":
    doctor_df, availability_df = load_doctor_data()
    specialty = st.session_state.recommended_specialty
    filtered_doctors = doctor_df[doctor_df["Specialty"] == specialty]
    doctor_list = filtered_doctors["Doctor_Name"].tolist()
    selected_doctor = st.selectbox("Choose a doctor", doctor_list)

    doctor_id = filtered_doctors[filtered_doctors["Doctor_Name"] == selected_doctor]["Doctor_ID"].values[0]
    slots = availability_df[
        (availability_df["Doctor_ID"] == doctor_id) & (availability_df["Slot_Status"] == "Open")
    ]
    if not slots.empty:
        slot_options = slots["Date"] + " " + slots["Start_Time"]
        selected_slot = st.selectbox("Choose a time slot", slot_options)
        if st.button("Confirm Appointment"):
            add_bot_message(f"✅ Appointment booked with Dr. {selected_doctor} on {selected_slot}")
            st.session_state.chat_state = "main_menu"
            st.rerun()
    else:
        add_bot_message("⚠️ No slots available for this doctor.")
        st.session_state.chat_state = "main_menu"
        st.rerun()
