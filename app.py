# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
import streamlit as st
def go_back_to(state_name):
    if st.button("🔙 Back"):
        st.session_state.chat_state = state_name
        st.stop()

# Set up the app page
st.set_page_config(page_title="AVACARE Assistant", page_icon="💬")
st.title("Hey! My name is AVA!")

# Initialize session state variables
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "choose_mode"
    st.session_state.mode = None
    st.session_state.language = None

# Step 1: Communication Mode Selection
if st.session_state.chat_state == "choose_mode":
    st.subheader("How you'd like to talk to me")
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
        if st.button("📞Call"):
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
elif st.session_state.chat_state == "greeting":
    # Show previous messages
    st.subheader("💬 Ava Conversation")
    for msg in st.session_state.chat_history:
        st.write(msg)

    # Ask user input
    user_input = st.text_input("You:", key="user_input")
    
    if user_input:
        # Append user's message
        st.session_state.chat_history.append(f"👤 You: {user_input}")

        # Ava responds (basic intent match — you can later expand with NLP)
        if "appointment" in user_input.lower():
            bot_reply = "📅 Ava: Sure! May I know your name and Patient ID (if you have one)?"
        elif "hello" in user_input.lower() or "hi" in user_input.lower():
            bot_reply = "🤖 Ava: Hello there! How can I help you today?"
        elif "help" in user_input.lower():
            bot_reply = "🤖 Ava: I can help you book appointments, view schedules, or update your details."
        else:
            bot_reply = "🤖 Ava: I'm still learning. Could you please rephrase?"

        # Add Ava's reply
        st.session_state.chat_history.append(bot_reply)

        # Clear the input
        st.experimental_rerun()

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
