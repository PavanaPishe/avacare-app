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
