import streamlit as st
import pandas as pd
import os

# Set up UI config
st.set_page_config(page_title="AVACARE Assistant", page_icon="💼")
st.markdown("<h1 style='font-family: Arial; color: #002B5B;'>Welcome to AVACARE Virtual Assistant</h1>", unsafe_allow_html=True)

# Session State Initialization
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.chat_history = []
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.is_returning = None

# Load Patient Data
@st.cache_data
def load_patients():
    return pd.read_csv("AVACARE_Patient_Dataset.csv")

@st.cache_data
def get_next_patient_id(patients_df):
    last_id = patients_df["Patient_ID"].str.extract(r'AVP-(\d+)').dropna()
    max_id = last_id.astype(int).max()[0] if not last_id.empty else 1000
    return f"AVP-{max_id + 1}"

patients_df = load_patients()

# Navigation helper
def go_back_to(state_name):
    if st.button("⬅️ Go Back"):
        st.session_state.chat_state = state_name
        st.rerun()

# --- STEP 1: COMMUNICATION MODE ---
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

# --- STEP 2: LANGUAGE SELECTION ---
elif st.session_state.chat_state == "choose_language":
    st.subheader("Step 2: Select Preferred Language")
    st.session_state.language = st.radio("Choose a language:", ["English", "Hindi", "Spanish"])
    if st.button("Continue"):
        st.session_state.chat_state = "greeting"
        st.rerun()
    go_back_to("choose_mode")

# --- STEP 3: GREETING BASED ON LANGUAGE ---
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

# --- STEP 4: PATIENT CHECK ---
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

# --- STEP 5A: RETURNING PATIENT ---
elif st.session_state.chat_state == "get_returning_info":
    st.subheader("Please provide your details")
    st.session_state.name = st.text_input("Your Full Name:")
    st.session_state.patient_id = st.text_input("Your Patient ID (e.g., AVP-1054):")

    if st.session_state.name and st.session_state.patient_id:
        match = patients_df[patients_df["Patient_ID"] == st.session_state.patient_id]
        if not match.empty:
            st.success(f"Welcome back, {st.session_state.name}! You're verified.")
            # You can now proceed to appointment or menu
        else:
            st.error("Patient ID not found. Please try again.")
    go_back_to("ask_identity")

# --- STEP 5B: NEW PATIENT REGISTRATION ---
elif st.session_state.chat_state == "get_new_info":
    st.subheader("Let's get you registered")
    st.session_state.name = st.text_input("Your Full Name:")
    if st.session_state.name:
        new_id = get_next_patient_id(patients_df)
        st.session_state.patient_id = new_id
        st.success(f"Thanks, {st.session_state.name}. You’ve been registered with Patient ID: {new_id}")
        # You can now store this to DB or DataFrame
    go_back_to("ask_identity")
