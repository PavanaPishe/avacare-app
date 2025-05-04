import streamlit as st

st.set_page_config(page_title="AVACARE AI Scheduler", layout="centered")

st.title("👩‍⚕️ AVACARE – AI Scheduling Assistant")
st.subheader("Hello! I'm AVACARE. How can I help you today?")

user_input = st.text_input("🗣 Type here (e.g., 'Book an appointment', 'What is my schedule?')")

if user_input:
    st.write("🤖 Thinking... (AI response will come here)")
    st.success("This is just a prototype. In the real version, I'd use AI to check patient risk, doctor availability, and book a slot.")

st.markdown("---")
st.markdown("📌 *Prototype developed using Streamlit (Free Tool)*")
import streamlit as st
import pandas as pd

# Title
st.title("AVACARE Scheduler - Data Overview")

# Load datasets
@st.cache_data
def load_data():
    patients = pd.read_csv("AVACARE_Patient_Dataset_Aligned.csv")
    doctors = pd.read_csv("AVACARE_20_Doctors_Info_and_Availability.xlsx", sheet_name="Doctor_Info")
    availability = pd.read_excel("AVACARE_20_Doctors_Info_and_Availability.xlsx", sheet_name="Doctor_Availability")
    return patients, doctors, availability

patients_df, doctors_df, availability_df = load_data()

# Display sample data
st.subheader("📋 Patient Records")
st.dataframe(patients_df.head())

st.subheader("🩺 Doctor Profiles")
st.dataframe(doctors_df.head())

st.subheader("📅 Doctor Availability")
st.dataframe(availability_df.head())
import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    patients = pd.read_csv("AVACARE_Patient_Dataset_Aligned.csv")
    return patients

patients_df = load_data()

# Chat UI starts here
st.title("💬 AVA - Your AI Health Assistant")

if "chat_state" not in st.session_state:
    st.session_state.chat_state = "start"
    st.session_state.patient_data = None

# Start chatbot
if st.session_state.chat_state == "start":
    st.write("👋 Hello! I'm Ava, your scheduling assistant. How would you like to speak with me?")
    option = st.radio("Choose a communication mode:", ["Text Chat", "Voice Call", "IVR"])

    if option:
        st.session_state.chat_state = "ask_name"

# Ask for name and ID
elif st.session_state.chat_state == "ask_name":
    name = st.text_input("Great! May I know your full name?")
    patient_id = st.text_input("And your Patient ID? (e.g., AVP-1054)")

    if name and patient_id:
        match = patients_df[patients_df["Patient_ID"] == patient_id]
        if not match.empty:
            st.session_state.patient_data = match.iloc[0]
            st.session_state.chat_state = "loaded"
        else:
            st.error("Hmm... I couldn't find your ID. Please double check.")

# Tailored reply once data is loaded
elif st.session_state.chat_state == "loaded":
    patient = st.session_state.patient_data
    st.success(f"Welcome back, {patient['First_Name']}! How can I help you today?")
    
    action = st.radio("Would you like to:", ["📅 Book a new appointment", "🔁 View your next visit", "💬 Ask a question"])
    
    if action == "📅 Book a new appointment":
        st.write("Sure! Let me check available slots for your preferred specialty.")
        # You can add slot filtering logic here using patient['Suggested_Specialty']

    elif action == "🔁 View your next visit":
        st.info(f"🗓 Your next appointment is on {patient['Next_Appointment_Date']}")

    elif action == "💬 Ask a question":
        st.text_input("Type your question here...")

