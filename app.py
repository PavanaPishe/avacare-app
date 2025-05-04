import streamlit as st

# Set up the app page
st.set_page_config(page_title="AVACARE Assistant", page_icon="💬")
st.title("Hey! My name is AVA!")

# Back button helper
def go_back_to(state_name):
    if st.button("🔙 Back"):
        st.session_state.chat_state = state_name
        st.rerun()

# -------------------- SESSION STATE INIT --------------------
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None
    st.session_state.chat_history = []

# -------------------- STEP 1: COMMUNICATION MODE --------------------
if st.session_state.chat_state == "choose_mode":
    st.subheader("How would you like to talk to me?")
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

# -------------------- STEP 2: LANGUAGE SELECTION --------------------
elif st.session_state.chat_state == "choose_language":
    st.subheader("🌍 Step 2: Select your preferred language")
    st.session_state.language = st.radio("Available Languages:", ["English", "Hindi", "Spanish"])

    if st.button("✅ Continue"):
        st.session_state.chat_state = "greeting"
        st.rerun()

    go_back_to("choose_mode")

# -------------------- STEP 3: CHAT GREETING --------------------
elif st.session_state.chat_state == "greeting":
    st.subheader("💬 Ava Conversation")

    greeting = {
        "English": "Hi, how are you doing today?",
        "Hindi": "नमस्ते, आज आप कैसे हैं?",
        "Spanish": "Hola, ¿cómo estás hoy?"
    }

    # Show greeting only once
    if not st.session_state.chat_history:
        st.session_state.chat_history.append(f"🤖 Ava: {greeting[st.session_state.language]}")

    # Display history
    for msg in st.session_state.chat_history:
        st.write(msg)

    # Text input with key
user_input = st.text_input("You:", key="user_text")

if user_input and ("last_input" not in st.session_state or st.session_state.last_input != user_input):
    st.session_state.chat_history.append(f"👤 You: {user_input}")

    # Ava's response logic
    if "appointment" in user_input.lower():
        reply = "📅 Ava: Sure! May I know your name and Patient ID (if you have one)?"
    elif "hello" in user_input.lower() or "hi" in user_input.lower():
        reply = "🤖 Ava: Hello there! How can I help you today?"
    elif "help" in user_input.lower():
        reply = "🤖 Ava: I can help you book appointments, view schedules, or update your details."
    else:
        reply = "🤖 Ava: I'm still learning. Could you please rephrase?"

    st.session_state.chat_history.append(reply)
    st.session_state.last_input = user_input  # Store last message

    st.rerun()  # ✅ Correct function now

