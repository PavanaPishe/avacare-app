import streamlit as st
import uuid

# Setup
st.set_page_config(page_title="AVACARE AI Assistant", page_icon="💬")
st.title("💬 AVACARE – Virtual Healthcare Assistant")

# Session state for conversation
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "start"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.name = ""
    st.session_state.patient_id = ""
    st.session_state.returning = None

# Step 1: Ask for communication mode
if st.session_state.chat_state == "start":
    st.write("👋 Welcome to AVACARE!")
    st.write("How would you like to communicate with me?")
    st.session_state.mode = st.radio("Choose your preferred method:", ["💬 Chat", "🎙️ Voice", "📞 IVR Call"])

    if st.session_state.mode == "💬 Chat":
        st.success("✅ Chat selected. Proceeding...")
        st.session_state.chat_state = "language"

    elif st.session_state.mode == "🎙️ Voice":
        st.info("🎤 Voice selected. (Simulated voice input - speak into your mic below)")
        st.audio("https://upload.wikimedia.org/wikipedia/commons/4/4f/Sample.ogg")  # Placeholder mic icon
        st.session_state.chat_state = "language"

    elif st.session_state.mode == "📞 IVR Call":
        st.info("📞 Please call **+1-800-AVA-CARE** to use our IVR-powered AI assistant.")
        st.session_state.chat_state = "language"

# Step 2: Language selection
elif st.session_state.chat_state == "language":
    st.write("🌐 What is your preferred language?")
    st.session_state.language = st.radio("Select Language:", ["English", "Hindi", "Spanish"])

    if st.session_state.language:
        st.session_state.chat_state = "greeting"

# Step 3: Gentle greeting
elif st.session_state.chat_state == "greeting":
    greeting_msg = {
        "English": "Hi, how are you doing today?",
        "Hindi": "नमस्ते, आज आप कैसे हैं?",
        "Spanish": "Hola, ¿cómo estás hoy?"
    }
    st.write(greeting_msg[st.session_state.language])
    st.session_state.chat_state = "ask_identity"

# Step 4: Ask for patient identity
elif st.session_state.chat_state == "ask_identity":
    st.write("💡 Please provide your details so I can assist you better.")
    st.session_state.returning = st.radio(
        "Are you a returning patient?",
        ["Yes, I have a Patient ID", "No, I’m a new patient"]
    )

    if st.session_state.returning == "Yes, I have a Patient ID":
        st.session_state.name = st.text_input("Please enter your full name:")
        st.session_state.patient_id = st.text_input("Enter your Patient ID (e.g., AVP-1021):")

        if st.session_state.name and st.session_state.patient_id:
            st.success(f"Thank you, {st.session_state.name}. I'll retrieve your records next.")
            # You’d normally validate here
            st.session_state.chat_state = "stop_here"

    elif st.session_state.returning == "No, I’m a new patient":
        st.session_state.name = st.text_input("Please enter your full name:")
        if st.session_state.name:
            generated_id = "AVP-" + str(uuid.uuid4())[:8].upper()
            st.session_state.patient_id = generated_id
            st.success(f"🎉 Welcome, {st.session_state.name}! Your new Patient ID is **{generated_id}**.")
            # You’d store this in your database or CSV next
            st.session_state.chat_state = "stop_here"

# Final step (placeholder)
elif st.session_state.chat_state == "stop_here":
    st.info("✅ Chatbot is now ready to help you book appointments or answer questions. (Next logic coming soon)")
