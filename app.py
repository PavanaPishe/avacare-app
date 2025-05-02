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
