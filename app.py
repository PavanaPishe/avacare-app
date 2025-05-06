import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import requests

# -------------------- GOOGLE SHEETS SETUP --------------------

@st.cache_resource
def connect_to_patient_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1aFhExzz3_BTNDzJ2h37YqxK6ij8diJCTbAwsPcdJQtM")  # Patient Sheet

@st.cache_resource
def connect_to_doctor_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1VVMGuKFvLokIEvFC6DIfnDqAvWCJ-A_fUaiIc_yUf8w")  # Doctor Sheet

def get_weather_forecast(city_raw):
    api_key = st.secrets["weather_api"]["api_key"]
    
    # Clean city: extract "Dallas" from "New Mathewmouth, Dallas, TX"
    city_parts = city_raw.split(',')
    city = city_parts[1].strip() if len(city_parts) > 1 else city_raw.strip()

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        weather_desc = data["weather"][0]["description"].title()
        temperature = data["main"]["temp"]
        return f"The current weather in {city} is {weather_desc} with a temperature of {temperature}°C."
    except Exception as e:
        return f"⚠️ Could not fetch weather data: {str(e)}"

def predict_no_show_risk(patient_record, weather_message, selected_slot):
    risk_score = 0

    # Missed appointments count
    missed = int(str(patient_record.get("Missed_Appointments", "0")).strip())
    if missed >= 2:
        risk_score += 2
    elif missed == 1:
        risk_score += 1

    # Risk category
    category = patient_record.get("Risk_Category", "").lower()
    if "high" in category:
        risk_score += 2
    elif "moderate" in category:
        risk_score += 1

    # Weather condition
    if "rain" in weather_message.lower() or "storm" in weather_message.lower():
        risk_score += 2
    elif "snow" in weather_message.lower():
        risk_score += 1

    # Appointment time logic
    try:
        hour = int(selected_slot.split()[1].split(":")[0])
        if hour < 10:  # early morning slots
            risk_score += 1
    except:
        pass

    # Final risk message
    if risk_score >= 5:
        return "⚠️ High Risk of No-Show"
    elif risk_score >= 3:
        return "🟠 Moderate Risk of No-Show"
    else:
        return "✅ Low Risk of No-Show"



# -------------------- FUNCTIONS --------------------

def get_next_patient_id(sheet):
    records = sheet.worksheet("Sheet1").get_all_records()
    if not records:
        return "AVP-4000"
    last_id = sorted(records, key=lambda r: int(r["Patient_ID"].split("-")[1]))[-1]["Patient_ID"]
    new_number = int(last_id.split("-")[1]) + 1
    return f"AVP-{new_number}"

def load_patient_dataframe(sheet):
    records = sheet.worksheet("Sheet1").get_all_records()
    return pd.DataFrame(records)

def register_new_patient(sheet, row_data):
    sheet.worksheet("Sheet1").append_row(row_data)

def load_doctor_data():
    sheet = connect_to_doctor_sheet()
    info = sheet.worksheet("Doctor_Info").get_all_records()
    avail = sheet.worksheet("Doctor_Availability").get_all_records()
    return pd.DataFrame(info), pd.DataFrame(avail)

def mark_slot_as_filled(doctor_name, slot_datetime):
    sheet = connect_to_doctor_sheet()
    ws = sheet.worksheet("Doctor_Availability")
    data = ws.get_all_values()
    headers, rows = data[0], data[1:]
    doc_idx = headers.index("Doctor_Name")
    date_idx = headers.index("Date")
    time_idx = headers.index("Start_Time")
    status_idx = headers.index("Slot_Status")

    slot_date, slot_time = slot_datetime.split(" ")
    for i, row in enumerate(rows):
        if row[doc_idx] == doctor_name and row[date_idx] == slot_date and row[time_idx] == slot_time:
            ws.update_cell(i + 2, status_idx + 1, "Filled")
            return

# -------------------- UI SETUP --------------------

st.set_page_config(page_title="AVACARE Assistant", page_icon="💼")
st.markdown("<h1 style='color:#002B5B;'>AVACARE Virtual Assistant</h1>", unsafe_allow_html=True)

if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.is_returning = None
    st.session_state.recommended_specialty = ""

def go_back_to(state, key=None):
    if st.button("⬅️ Go Back", key=key or f"go_back_{state}"):
        st.session_state.chat_state = state
        st.rerun()

# -------------------- Step-by-step Flow --------------------

# Step 1: Communication Mode
if st.session_state.chat_state == "choose_mode":
    st.subheader("Step 1: Choose your communication mode")
    col1, col2, col3 = st.columns(3)
    if col1.button("Chat"):
        st.session_state.mode = "chat"
        st.session_state.chat_state = "choose_language"
    if col2.button("Voice"):
        st.session_state.mode = "voice"
        st.session_state.chat_state = "choose_language"
    if col3.button("Call"):
        st.session_state.mode = "call"
        st.session_state.chat_state = "choose_language"

# Step 2: Language
elif st.session_state.chat_state == "choose_language":
    st.subheader("Step 2: Choose your language")
    st.session_state.language = st.radio("Preferred Language:", ["English", "Hindi", "Spanish"])
    if st.button("Continue"):
        st.session_state.chat_state = "greeting"
        st.rerun()
    go_back_to("choose_mode")

# Step 3: Greeting
elif st.session_state.chat_state == "greeting":
    greetings = {
        "English": "Hi, how are you doing today?",
        "Hindi": "नमस्ते, आज आप कैसे हैं?",
        "Spanish": "Hola, ¿cómo estás hoy?"
    }
    st.subheader("Conversation")
    st.markdown(f"**AVA:** {greetings[st.session_state.language]}")

    user_reply = st.text_input("Your Response:")
    if user_reply:
        st.session_state.chat_state = "ask_identity"
        st.rerun()

    go_back_to("choose_language")  # 🔙 Back to language selection


# Step 4: New or Returning
elif st.session_state.chat_state == "ask_identity":
    st.subheader("Are you a returning patient?")
    if st.button("Yes"):
        st.session_state.is_returning = True
        st.session_state.chat_state = "get_returning_info"
    elif st.button("No"):
        st.session_state.is_returning = False
        st.session_state.chat_state = "get_new_info"
# --- Step 5A: Returning Patient ---
elif st.session_state.chat_state == "get_returning_info":
    sheet = connect_to_patient_sheet()
    df = load_patient_dataframe(sheet)

    st.subheader("🔁 Welcome Back! Please enter your details")
    name = st.text_input("Full Name")
    pid = st.text_input("Patient ID (e.g., AVP-4001)")

    if name and pid:
        match = df[df["Patient_ID"] == pid]

        if not match.empty:
            st.session_state.name = name
            st.session_state.patient_id = pid

            # ✅ Adjusted field names to your sheet
            last_date = match.iloc[0].get("Last_Appointment_Date", "")
            missed_count = match.iloc[0].get("Missed_Appointments", 0)
            missed_reason = match.iloc[0].get("Missed_Appointment_Reason", "")

            st.success("✅ Verified.")

            # Show message only if missed > 0
            try:
                if int(missed_count) > 0:
                    st.warning(
                        f"Hi {name}, I see that your last appointment was on **{last_date}**, "
                        f"but it was marked as **missed**. You had mentioned: _'{missed_reason}'_.\n\n"
                        "Hope everything’s okay — let’s make sure we don’t miss the next one! 😊"
                    )
            except:
                pass  # In case conversion fails

            st.session_state.chat_state = "main_menu"
            st.rerun()
        else:
            st.error("❌ Patient ID not found. Please check and try again.")

    go_back_to("ask_identity")



# Step 5B: New Patient
elif st.session_state.chat_state == "get_new_info":
    st.subheader("📝 Register as a New Patient")

    sheet = connect_to_patient_sheet()
    ws = sheet.worksheet("Sheet1")
    new_id = get_next_patient_id(sheet)
    st.write(f"Your Patient ID will be: **{new_id}**")

    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=0, max_value=120)
    symptom = st.text_input("Symptoms")
    contact = st.text_input("Contact Number")
    email = st.text_input("Email Address")
    insurance = st.selectbox("Insurance Type", ["Private", "Public", "Self-Pay"])
    preferred_lang = st.selectbox("Preferred Communication Language", ["English", "Hindi", "Spanish"])
    caregiver = st.radio("Do you need caregiver assistance?", ["Yes", "No"])
    emergency_contact_name = st.text_input("Emergency Contact Name")
    emergency_contact_phone = st.text_input("Emergency Contact Phone")

    if st.button("Register"):
        row = [
            new_id, fname, lname, gender, age, symptom, contact, email, insurance,
            preferred_lang, caregiver, emergency_contact_name, emergency_contact_phone
        ]
        ws.append_row(row)
        st.session_state.name = fname
        st.session_state.patient_id = new_id
        st.success(f"🎉 Welcome {fname}! Your Patient ID is {new_id}")
        st.session_state.chat_state = "main_menu"
        st.rerun()

    go_back_to("ask_identity")


# --- Step 6: Main Menu ---
elif st.session_state.chat_state == "main_menu":
    st.subheader(f"Welcome, {st.session_state.name} 👋")
    st.markdown("What would you like to do?")

    option = st.selectbox("Choose an action", [
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
            st.success("Thank you for using AVACARE. Take care!")
        else:
            st.info("This feature is coming soon!")
        st.rerun()
        
# --- STEP 1: Ask for Symptom ---

elif st.session_state.chat_state == "ask_symptoms":
    st.subheader("What symptoms are you experiencing?")
    symptom = st.text_input("Enter your primary symptom (e.g., fever, back pain, toothache):")

    if symptom:
        symptom_map = {
            "fever": "General Physician",
            "cold": "General Physician",
            "cough": "General Physician",
            "headache": "General Physician",
            "tooth": "Dentist",
            "teeth": "Dentist",
            "cavity": "Dentist",
            "skin rash": "Dermatologist",
            "acne": "Dermatologist",
            "pimples": "Dermatologist",
            "hairfall": "Dermatologist",
            "ear pain": "ENT Specialist",
            "nose": "ENT Specialist",
            "throat": "ENT Specialist",
            "child fever": "Pediatrics",
            "child": "Pediatrics",
            "anxiety": "Psychologist",
            "pain during periods": "Gynecologist",
            "pregnancy": "Gynecologist",
            "back pain": "Orthopedic",
            "muscle strain": "Physiotherapist"
        }
        specialty = symptom_map.get(symptom.lower())
        if specialty:
            st.session_state.recommended_specialty = specialty
            st.success(f"You should consult a **{specialty}**.")
            st.session_state.chat_state = "select_doctor"
            st.rerun()
        else:
            st.warning("Sorry, couldn't map the symptom. Try again.")

# --- STEP 2: Doctor Selection ---
elif st.session_state.chat_state == "select_doctor":
    st.subheader("Select a Doctor and Slot")

    doctor_df, availability_df = load_doctor_data()
    filtered_doctors = doctor_df[doctor_df["Specialty"] == st.session_state.recommended_specialty]

    if filtered_doctors.empty:
        st.error("No doctors available.")
        go_back_to("main_menu")
    else:
        selected_doctor = st.selectbox("Choose Doctor", filtered_doctors["Doctor_Name"])
        doctor_id = filtered_doctors[filtered_doctors["Doctor_Name"] == selected_doctor]["Doctor_ID"].values[0]
        slots = availability_df[
            (availability_df["Doctor_ID"] == doctor_id) & 
            (availability_df["Slot_Status"] == "Open")
        ]

        if not slots.empty:
            slot_options = slots["Date"] + " " + slots["Start_Time"]
            selected_slot = st.selectbox("Choose Slot", slot_options)

            if st.button("Confirm Appointment"):
               st.session_state.selected_doctor = selected_doctor
               st.session_state.selected_slot = selected_slot
               st.session_state.chat_state = "weather_check"
               st.rerun()


# --- STEP 2.5: Weather Check (after slot confirmation) ---
elif st.session_state.chat_state == "weather_check":
    st.subheader("🌦️ Weather Check")

    sheet = connect_to_patient_sheet()
    patients_df = load_patient_dataframe(sheet)

    try:
        patient_record = patients_df[patients_df["Patient_ID"] == st.session_state.patient_id]
        travel_city = patient_record.iloc[0].get("Traveling_From", "Dallas")
        weather_message = get_weather_forecast(travel_city)
        # ✅ AI No-Show Risk Prediction
        risk_msg = predict_no_show_risk(patient_record.iloc[0], weather_message, st.session_state.selected_slot)
        st.info(f"🧠 No-Show Risk Prediction: {risk_msg}")


        st.info(f"📍 Travel City: {travel_city}")
        st.info(f"🌤️ Weather Forecast: {weather_message}")

        if "rain" in weather_message.lower() or "storm" in weather_message.lower():
            st.warning("🌧️ It looks like the weather may be rough. You may consider booking a **telehealth** consultation or **rescheduling** your appointment.")
        elif "snow" in weather_message.lower():
            st.warning("❄️ Snowy conditions detected. A remote consultation might be safer.")
        else:
            st.success("🌤️ Weather looks good for travel. You're all set!")

    except Exception as e:
        st.warning(f"⚠️ Unable to fetch weather info: {e}")

    if st.button("Continue to Payment", key="weather_to_payment"):
       st.session_state.chat_state = "payment"
       st.rerun()


    go_back_to("select_doctor", key="go_back_from_weather")  # optional, gives back navigation
    

# --- STEP 3: Payment ---
elif st.session_state.chat_state == "payment":
    st.subheader("💳 Token Payment")
    st.write("To confirm your appointment, please pay a **25% token**.")

    st.session_state.selected_payment_mode = st.radio(
        "Choose a Payment Mode", 
        ["UPI", "Net Banking", "Credit Card", "Debit Card", "PayPal", "Insurance"]
    )
    paid = st.checkbox("✅ I have paid.")

    if paid:
        mark_slot_as_filled(
            st.session_state.selected_doctor,
            st.session_state.selected_slot
        )
        st.session_state.chat_state = "confirmed"
        st.rerun()

    go_back_to("main_menu", key="go_back_from_payment")

# --- STEP 4: Confirmation ---
elif st.session_state.chat_state == "confirmed":
    from io import BytesIO
    from datetime import datetime
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    st.balloons()
    st.subheader("✅ Appointment Confirmed!")
    st.success("Thank you for using AVACARE!")

    # --- Patient History ---
    sheet = connect_to_patient_sheet()
    df = load_patient_dataframe(sheet)
    patient = df[df["Patient_ID"] == st.session_state.patient_id]

    if not patient.empty:
        last_date = patient.iloc[0].get("Last_Appointment_Date", "N/A")
        missed = patient.iloc[0].get("Missed_Appointments", "0")
        reason = patient.iloc[0].get("Missed_Appointment_Reason", "")

        missed_count = int(str(missed).strip()) if str(missed).strip().isdigit() else 0

        if missed_count > 0:
            st.warning(f"⚠️ I see you had an appointment on **{last_date}** but missed it.\n\n_Reason given:_ **{reason}**\n\nLet’s make sure we meet this time. We're here to help! 😊")

            if "transportation" in reason.lower():
                slot_date = st.session_state.selected_slot.split()[0]
                st.info(f"🚗 As a token of support, we’re providing you with a **40% Uber voucher** valid until your new appointment on **{slot_date}**. Safe travels! 🎟️")

            # --- Smart Rescheduler Suggestion ---
            st.info("🔁 Since you missed a previous appointment, here are the next best available slots:")
            
            # ✅ FIX: Load doctor data
            doctor_df, availability_df = load_doctor_data()
            doc_id = doctor_df[doctor_df["Doctor_Name"] == st.session_state.selected_doctor]["Doctor_ID"].values[0]
            open_slots = availability_df[
                (availability_df["Doctor_ID"] == doc_id) &
                (availability_df["Slot_Status"] == "Open")
            ].sort_values(by=["Date", "Start_Time"]).head(3)

            if not open_slots.empty:
                slot_labels = open_slots["Date"] + " " + open_slots["Start_Time"]
                new_slot = st.radio("📅 Choose a new slot to reschedule:", slot_labels.tolist(), key="resched_radio")

                if st.button("Reschedule to This Slot", key="resched_button"):
                    mark_slot_as_filled(st.session_state.selected_doctor, new_slot)
                    st.session_state.selected_slot = new_slot
                    st.success(f"✅ Appointment rescheduled to {new_slot}")
                    st.rerun()
            else:
                st.warning("No alternative slots available right now. Please try again later.")

        else:
            st.info(f"🎉 Great record! No missed appointments so far. Keep it up, {st.session_state.name}!")

    # --- Appointment Summary ---
    st.write(f"Doctor: {st.session_state.selected_doctor}")
    st.write(f"Slot: {st.session_state.selected_slot}")
    st.write(f"Payment Mode: {st.session_state.selected_payment_mode}")

    # --- PDF Confirmation ---
    required_keys = [
        "name", "patient_id", "selected_doctor",
        "recommended_specialty", "selected_slot", "selected_payment_mode"
    ]

    if all(key in st.session_state for key in required_keys):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w / 2, h - 80, "Appointment Confirmation")

        c.setFont("Helvetica", 12)
        y = h - 130
        lines = [
            f"Patient Name     : {st.session_state.name}",
            f"Patient ID       : {st.session_state.patient_id}",
            f"Doctor Name      : Dr. {st.session_state.selected_doctor}",
            f"Specialty        : {st.session_state.recommended_specialty}",
            f"Appointment Slot : {st.session_state.selected_slot}",
            f"Payment Mode     : {st.session_state.selected_payment_mode}",
            f"Confirmed At     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        for line in lines:
            c.drawString(60, y, line)
            y -= 20

        if "transportation" in reason.lower():
            promo_code = f"UBER-{st.session_state.patient_id[:4]}-{st.session_state.selected_slot.split()[0].replace('-', '')}"
            c.drawString(60, y - 20, "-" * 50)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(60, y - 40, "🚗 Uber Travel Voucher")
            c.setFont("Helvetica", 11)
            c.drawString(60, y - 60, f"Voucher Code : {promo_code}")
            c.drawString(60, y - 80, "Discount     : 40% off on your next Uber ride")
            c.drawString(60, y - 100, f"Valid Until  : {st.session_state.selected_slot.split()[0]}")
            c.drawString(60, y - 120, "Use this code in the Uber app during checkout.")
            y -= 120

        c.drawString(60, y - 40, "-" * 50)
        c.drawString(60, y - 60, "Thank you for choosing AVACARE!")
        c.save()
        buffer.seek(0)

        st.download_button(
            label="📥 Download Confirmation PDF",
            data=buffer,
            file_name=f"AVACARE_Confirmation_{st.session_state.patient_id}.pdf",
            mime="application/pdf"
        )
    else:
        st.error("⚠️ Some appointment details are missing. Please complete booking before downloading the confirmation.")


# --- STEP: Voice Conversation Demo ---
elif st.session_state.chat_state == "voice_demo":
    st.subheader("🎤 AVACARE Voice Assistant (Prototype Demo)")
    st.markdown("Each response from the patient is shown as **transcribed voice reply**.")

    conversation = [
        {"ava": "Hey! I am AVA, how are you today?", "patient": "I'm good, how are you?"},
        {"ava": "I'm great! How can I help you today?", "patient": "I wanted to book an appointment."},
        {"ava": "Alrighty then! Let's start with some details of yours!", "patient": "Sure!"},
        {"ava": "Are you a fresh patient or a returning patient?", "patient": "Fresh."}
    ]

    for i, exchange in enumerate(conversation):
        st.markdown(f"**AVA:** {exchange['ava']}")
        st.markdown(f"**🧑 Patient (transcribed):** {exchange['patient']}")
        st.markdown("---")

    go_back_to("main_menu")
        option = st.selectbox("Choose an action", [
        "📅 Book an Appointment",
        "🧾 View Last Prescription (Coming Soon)",
        "🔁 Reschedule an Appointment (Coming Soon)",
        "📝 Update Contact Info (Coming Soon)",
        "🎤 Try Voice Assistant",   # 👈 Add this line
        "🚪 Exit"
    ])
        if option == "📅 Book an Appointment":
        st.session_state.chat_state = "ask_symptoms"
    elif option == "🎤 Try Voice Assistant":
        st.session_state.chat_state = "voice_demo"
    elif option == "🚪 Exit":
        st.success("Thank you for using AVACARE. Take care!")
    else:
        st.info("This feature is coming soon!")
    st.rerun()

