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
st.markdown("<h1 style='font-family: Arial; color: #002B5B;'>AVACARE Virtual Assistant</h1>", unsafe_allow_html=True)

# --- Session State Initialization ---
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.is_returning = None
    st.session_state.symptom_collected = False
    st.session_state.user_symptom = ""
    st.session_state.recommended_specialty = ""

def go_back_to(state_name):
    if st.button("⬅️ Go Back"):
        st.session_state.chat_state = state_name
        st.rerun()

# --- Step 1: Choose Communication Mode ---
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

# --- Step 2: Choose Language ---
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
    st.markdown(f"**AVA:** {greetings[st.session_state.language]}")
    user_reply = st.text_input("Your Response:")
    if user_reply:
        st.session_state.chat_state = "ask_identity"
        st.rerun()

# --- Step 4: Returning or New ---
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

    st.subheader("Please enter your details")
    name_input = st.text_input("Your Full Name:", value=st.session_state.name)
    id_input = st.text_input("Your Patient ID (e.g., AVP-1054):", value=st.session_state.patient_id)

    if name_input and id_input:
        st.session_state.name = name_input
        st.session_state.patient_id = id_input
        match = patients_df[patients_df["Patient_ID"] == id_input]
        if not match.empty:
            st.success(f"✅ Verified. Welcome back, {st.session_state.name}!")
            st.session_state.chat_state = "main_menu"
            st.rerun()
        else:
            st.error("❌ Patient ID not found.")
    go_back_to("ask_identity")

# --- STEP 5B: New Patient Registration with Full Details ---
elif st.session_state.chat_state == "get_new_info":
    st.subheader("📝 Register as a New Patient")

    sheet = connect_to_google_sheet()

    st.markdown("Please fill in your details below:")

    # Generate a new Patient ID
    new_id = get_next_patient_id(sheet)
    st.markdown(f"**Your Patient ID:** {new_id}")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    symptoms = st.text_input("Describe your symptoms")
    travel_from = st.text_input("Traveling From")
    appointment_date = st.date_input("Preferred Appointment Date")
    insurance_type = st.selectbox("Insurance Type", ["Private", "Public", "None"])
    contact = st.text_input("Contact Number")
    email = st.text_input("Email Address")
    emergency_contact_name = st.text_input("Emergency Contact Name")
    emergency_phone = st.text_input("Emergency Phone Number")
    preferred_mode = st.radio("Preferred Communication Mode", ["Chat", "Call", "Voice"])
    preferred_lang = st.selectbox("Preferred Language", ["English", "Hindi", "Spanish"])
    missed_appointments = st.number_input("Number of Missed Appointments", min_value=0, step=1)
    risk_category = st.selectbox("Risk Category", ["Low", "Moderate", "High"])
    token_payment_status = st.radio("Token Payment Status", ["Paid", "Unpaid"])
    missed_reason = st.text_input("Reason for Previous Missed Appointments (if any)")
    caregiver_needed = st.radio("Do you need a caregiver's help?", ["Yes", "No"])
    uber_needed = st.radio("Do you need an Uber Voucher?", ["Yes", "No"])
    next_appointment = st.date_input("Suggested Next Appointment Date")

    if st.button("Register"):
        row_data = [
            new_id, first_name, last_name, gender, age, symptoms, "",  # We'll fill in Suggested Specialty later
            travel_from, str(appointment_date), insurance_type, contact, email,
            emergency_contact_name, emergency_phone, preferred_mode, preferred_lang,
            missed_appointments, risk_category, token_payment_status,
            missed_reason, caregiver_needed, uber_needed,
            str(next_appointment), "Fresh"
        ]
        sheet.append_row(row_data)
        st.session_state.name = first_name
        st.session_state.patient_id = new_id
        st.success(f"🎉 You're successfully registered! Your Patient ID is {new_id}")
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

# --- Step 7: Ask Symptoms and Recommend Specialty ---
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
            st.success(f"Based on your symptom, you should consult a **{specialty}**.")
            st.session_state.chat_state = "doctor_selection"
            st.rerun()
        else:
            st.warning("Sorry, we couldn't map your symptom. Try again or go back.")
    go_back_to("main_menu")

# --- Step 8: Doctor Selection and Booking ---
elif st.session_state.chat_state == "doctor_selection":
    st.subheader("Select a Doctor and Book Slot")

    doctor_df, availability_df = load_doctor_data()
    specialty = st.session_state.recommended_specialty
    filtered_doctors = doctor_df[doctor_df["Specialty"] == specialty]

    if filtered_doctors.empty:
        st.error("No doctors available for the selected specialty.")
        go_back_to("main_menu")
    else:
        doctor_names = filtered_doctors["Doctor_Name"].tolist()
        selected_doctor = st.selectbox("Choose a doctor", doctor_names)

        doctor_id = filtered_doctors[filtered_doctors["Doctor_Name"] == selected_doctor]["Doctor_ID"].values[0]
        available_slots = availability_df[
            (availability_df["Doctor_ID"] == doctor_id) & (availability_df["Slot_Status"] == "Open")
        ]

        if not available_slots.empty:
            slot_options = available_slots["Date"] + " " + available_slots["Start_Time"]
            selected_slot = st.selectbox("Choose a slot", slot_options)

            if st.button("Confirm Appointment"):
                st.session_state.selected_doctor = selected_doctor
                st.session_state.selected_slot = selected_slot
                st.session_state.chat_state = "payment_page"
                st.rerun()
        else:
            st.warning("No available slots.")
        go_back_to("main_menu")

# --- Step 9: Payment Page ---
elif st.session_state.chat_state == "payment_page":
    st.subheader("💳 Token Payment")

    # Load patient data
    sheet = connect_to_google_sheet()
    patients_df = load_patient_dataframe(sheet)

    patient_record = patients_df[patients_df["Patient_ID"] == st.session_state.patient_id]
    if not patient_record.empty:
        previous_insurance = patient_record.iloc[0].get("Insurance_Type", "Not Provided")
        previous_payment_mode = patient_record.iloc[0].get("Token_Payment_Mode", "Not Available")

        st.info(f"👤 Last Insurance Type: **{previous_insurance}**")
        st.info(f"💳 Last Payment Mode: **{previous_payment_mode}**")

    st.write("To confirm your appointment, please pay a **25% token** upfront.")

    st.session_state.selected_payment_mode = st.radio(
        "Choose a Payment Mode",
        ["UPI", "Net Banking", "Credit Card", "Debit Card", "PayPal", "Apple Pay", "Insurance Portal"]
    )
    paid = st.checkbox("✅ I have completed the 25% payment.")

    if paid:
        # ✅ Mark the selected slot as filled in Google Sheet
        def mark_slot_as_filled(patient_id, selected_doctor, selected_slot):
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials

            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            client = gspread.authorize(creds)
            doc = client.open_by_key("1aFhExzz3_BTNDzJ2h37YqxK6ij8diJCTbAwsPcdJQtM")
            availability_sheet = doc.worksheet("Doctor_Availability")

            all_rows = availability_sheet.get_all_values()
            headers = all_rows[0]
            rows = all_rows[1:]

            doctor_idx = headers.index("Doctor_Name")
            date_idx = headers.index("Date")
            time_idx = headers.index("Start_Time")
            status_idx = headers.index("Slot_Status")

            if " " in selected_slot:
                slot_date, slot_time = selected_slot.split(" ")
            else:
                return

            for i, row in enumerate(rows):
                if row[doctor_idx] == selected_doctor and row[date_idx] == slot_date and row[time_idx] == slot_time:
                    availability_sheet.update_cell(i + 2, status_idx + 1, "Filled")
                    print(f"✅ Slot marked as filled for {selected_doctor} on {selected_slot}")
                    return

        mark_slot_as_filled(
            st.session_state.patient_id,
            st.session_state.selected_doctor,
            st.session_state.selected_slot
        )

        # ✅ Move to confirmation page
        st.session_state.chat_state = "confirmation_page"
        st.rerun()

    else:
        st.warning("Please check the box after completing payment to continue.")

    go_back_to("doctor_selection")

# --- Step 10: Appointment Confirmation ---
elif st.session_state.chat_state == "confirmation_page":
    st.balloons()
    st.subheader("✅ Appointment Confirmed!")
    st.success("Your appointment has been successfully confirmed. Please download your confirmation below.")

    from datetime import datetime
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    try:
        logo_path = "avacare_logo.png"
        c.drawImage(logo_path, 40, height - 100, width=120, preserveAspectRatio=True)
    except:
        pass

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 130, "Appointment Confirmation")

    c.setFont("Helvetica", 12)
    y = height - 170
    details = [
        f"Patient Name     : {st.session_state.name}",
        f"Patient ID       : {st.session_state.patient_id}",
        f"Doctor Name      : Dr. {st.session_state.selected_doctor}",
        f"Specialty        : {st.session_state.recommended_specialty}",
        f"Appointment Slot : {st.session_state.selected_slot}",
        f"Payment Mode     : {st.session_state.selected_payment_mode}",
        f"Confirmed At     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    for line in details:
        c.drawString(60, y, line)
        y -= 20

    c.drawString(60, y - 20, "-" * 50)
    c.drawString(60, y - 40, "Thank you for choosing AVACARE! 🙌")
    c.save()
    buffer.seek(0)

    st.download_button(
        label="📥 Download Confirmation PDF",
        data=buffer,
        file_name=f"AVACARE_Confirmation_{st.session_state.patient_id}.pdf",
        mime="application/pdf"
    )

    go_back_to("main_menu")

