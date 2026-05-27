import streamlit as st
import requests

st.set_page_config(page_title="HA! Healthcare AI", layout="wide")

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- LOGIN PAGE ----------
if not st.session_state.logged_in:

    st.title("🩺 HA! - AI Powered Healthcare")
    st.subheader("Patient Login")

    name = st.text_input("Patient Name")
    phone = st.text_input("Mobile Number")
    location = st.text_input("Location")

    if st.button("Login"):
        if name and phone and location:
            st.session_state.logged_in = True
            st.session_state.name = name
            st.session_state.phone = phone
            st.session_state.location = location
            st.rerun()
        else:
            st.error("Please fill all details")

# ---------- CHAT PAGE ----------
else:

    # Sidebar
    with st.sidebar:
        st.title("HA! Options")

        if st.button("🆕 New Chat"):
            st.session_state.messages = []

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.messages = []
            st.rerun()

    st.title(f"Welcome {st.session_state.name} 👋")
    st.caption("AI Powered Healthcare Assistant")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    prompt = st.chat_input("Ask your health question...")

    if prompt:
        # Show user message
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        # 🔥 CALL BACKEND
        try:
            response = requests.post(
                "http://127.0.0.1:8000/chat",
                json={"message": prompt}
            )
            ai_reply = response.json()["response"]
        except:
            ai_reply = "Backend not connected."

        # Show AI reply
        st.session_state.messages.append(
            {"role": "assistant", "content": ai_reply}
        )

        with st.chat_message("assistant"):
            st.markdown(ai_reply)