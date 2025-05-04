import streamlit as st

# Setup
st.set_page_config(page_title="AVACARE AI Assistant", page_icon="💬")
st.title("💬 AVACARE – Virtual Healthcare Assistant")

# State
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "start"
    st.session_state.mode = ""
    st.session_state.language = ""

# Step 1: Communication mode
if st.session_state.chat_state == "start":
    st.write("👋 Welcome! How would you like to communicate?")
    st.session_state.mode = st.radio("Select mode:", ["💬 Chat", "🎙️ Voice", "📞 IVR Call"])

    if st.session_state.mode:
        st.session_state.chat_state = "language"

# Step 2: Language selection
elif st.session_state.chat_state == "language":
    st.session_state.language = st.radio("Choose your preferred language:", ["English", "Hindi", "Spanish"])
    if st.session_state.language:
        st.session_state.chat_state = "respond_in_mode"

# Step 3: Handle based on selected mode
elif st.session_state.chat_state == "respond_in_mode":
    
    # 1️⃣ CHAT MODE
    if st.session_state.mode == "💬 Chat":
        st.success(f"You selected Chat in {st.session_state.language}")
        st.write("Hi, how are you doing today?")
        # Continue with chatbot input...

    # 2️⃣ VOICE MODE
    elif st.session_state.mode == "🎙️ Voice":
        st.info("🎙️ Please record your message below:")
        st.audio("https://upload.wikimedia.org/wikipedia/commons/4/4f/Sample.ogg")  # Placeholder mic icon

        st.success("✅ Got your voice input!")

        # Simulated bot voice response (choose based on language)
        st.write("🔊 Ava is responding with a voice message:")
        if st.session_state.language == "English":
            st.audio("https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav")
        elif st.session_state.language == "Hindi":
            st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")  # Replace with real Hindi bot TTS later
        elif st.session_state.language == "Spanish":
            st.audio("https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg10.wav")

    # 3️⃣ IVR MODE
    elif st.session_state.mode == "📞 IVR Call":
        st.success(f"📞 Please call our AI Assistant at: +1-800-AVA-CARE")
        st.info(f"When you call, Ava will speak to you in **{st.session_state.language}**.")

        # Simulated sample of how Ava would sound in IVR
        st.write("Here’s how Ava would respond in your language over the call:")
        if st.session_state.language == "Hindi":
            st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3")  # Placeholder Hindi voice
        elif st.session_state.language == "English":
            st.audio("https://www2.cs.uic.edu/~i101/SoundFiles/CantinaBand3.wav")
        elif st.session_state.language == "Spanish":
            st.audio("https://www2.cs.uic.edu/~i101/SoundFiles/ImperialMarch60.wav")

    st.write("⚙️ [Next step: Collect patient info based on this mode & language...]")
