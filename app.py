import streamlit as st
def go_back_to(state_name):
    if st.button("🔙 Back"):
        st.session_state.chat_state = state_name
        st.stop()

# Set up the app page
st.set_page_config(page_title="AVACARE Assistant", page_icon="💬")
st.title("💬 Welcome to AVACARE – Your Virtual Healthcare Assistant")

# Initialize session state variables
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None

# Step 1: Communication Mode Selection
if st.session_state.chat_state == "choose_mode":
    st.subheader("🛠️ Step 1: Choose how you'd like to talk to Ava")
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
        if st.button("📞 IVR Call"):
            st.session_state.mode = "ivr"
            st.session_state.chat_state = "choose_language"
elif st.session_state.chat_state == "choose_language":
    st.subheader("🌍 Step 2: Select your preferred language")
    st.session_state.language = st.radio("Available Languages:", ["English", "Hindi", "Spanish"])

    if st.button("✅ Continue"):
        st.success(f"You selected {st.session_state.mode.upper()} mode and {st.session_state.language} language.")
        st.session_state.chat_state = "greeting"

    # Add back button to go to mode selection
    go_back_to("choose_mode")

# Step 2: Language Selection
elif st.session_state.chat_state == "choose_language":
    st.subheader("🌍 Step 2: Select your preferred language")
    st.session_state.language = st.radio(
        "Available Languages:",
        ["English", "Hindi", "Spanish"]
    )

    if st.button("✅ Continue"):
        st.success(f"You selected {st.session_state.mode.upper()} mode and {st.session_state.language} language.")
        st.session_state.chat_state = "greeting"
elif st.session_state.chat_state == "greeting":
    greeting = {
        "English": "Hi, how are you doing today?",
        "Hindi": "नमस्ते, आज आप कैसे हैं?",
        "Spanish": "Hola, ¿cómo estás hoy?"
    }
    st.write(greeting[st.session_state.language])

    # Go back to language selection if needed
    go_back_to("choose_language")

# (Optional) Step 3: Proceed to greeting
elif st.session_state.chat_state == "greeting":
    greeting = {
        "English": "Hi, how are you doing today?",
        "Hindi": "नमस्ते, आज आप कैसे हैं?",
        "Spanish": "Hola, ¿cómo estás hoy?"
    }
    st.write(greeting[st.session_state.language])
