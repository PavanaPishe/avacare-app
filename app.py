import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    patients = pd.read_csv("AVACARE_Patient_Dataset_Aligned.csv")
    return patients

patients_df = load_data()

# Title
st.title("💬 AVACARE Virtual Assistant (Ava)")

# State setup
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "greeting"
    st.session_state.patient_data = None
    st.session_state.name = ""
    st.session_state.patient_id = ""

# Greeting & channel choice
if st.session_state.chat_state == "greeting":
    st.write("👋 Hello! I'm Ava, your AI scheduling assistant.")
    st.write("How would you like to talk to me today?")
    channel = st.radio("Choose your communication method:", ["💬 Chat", "📞 Voice", "📱 IVR"])

    if channel:
        st.session_state.chat_state = "ask_name"

# Ask for Name and Patient ID
elif st.session_state.chat_state == "ask_name":
    st.session_state.name = st.text_input("May I know your full name?")
    st.session_state.patient_id = st.text_input("And your Patient ID? (e.g., AVP-1054)")

    if st.session_state.name and st.session_state.patient_id:
        matched = patients_df[patients_df["Patient_ID"] == st.session_state.patient_id]
        if not matched.empty:
            st.session_state.patient_data = matched.iloc[0]
            st.session_state.chat_state = "loaded"
        else:
            st.error("❌ Hmm, I couldn't find that ID. Please check again.")

# Data is loaded internally
elif st.session_state.chat_state == "loaded":
    patient = st.session_state.patient_data
    st.success(f"Welcome back, {patient['First_Name']}! 😊")

    # Personalized greeting based on risk
    if patient["Risk_Category"] == "High":
        st.warning("⚠️ I noticed you've missed several appointments. Let’s get you back on track!")

    choice = st.radio("How can I assist you today?", ["📅 Book an appointment", "📋 View next appointment", "❓ Ask a question"])

    if choice == "📅 Book an appointment":
        st.write("Great! I’ll fetch available slots based on your specialty.")
        st.info(f"Your preferred specialty is: **{patient['Suggested_Specialty']}**")
        # You can add booking logic here later

    elif choice == "📋 View next appointment":
        st.success(f"🗓 Your next appointment is on **{patient['Next_Appointment_Date']}**")

    elif choice == "❓ Ask a question":
        st.text_input("Sure, what would you like to know?")
