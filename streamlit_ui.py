import streamlit as st
from dotenv import load_dotenv
from chatbot import ask_rajagiri_bot

load_dotenv()

st.set_page_config(page_title="Rajagiri College Chatbot", page_icon=None, layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Merriweather', serif;
        background-color: #fff9f5;
        color: #000;
    }

    .block-container {
        padding: 2.5rem 5rem;
    }

    .stMarkdown h1 {
        color: #800000;
        font-size: 2.3rem;
        font-weight: 700;
        border-bottom: 2px solid #800000;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }

    .stChatMessage {
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 1.1rem 1.5rem;
        margin-bottom: 1.2rem;
        font-size: 15.5px;
        line-height: 1.7;
    }

    .stChatMessage.user {
        background-color: #f8f5f0;
        border-left: 6px solid #800000;
    }

    .stChatMessage.assistant {
        background-color: #ffffff;
        border-left: 6px solid #d4af37;
    }

    .stTextInput>div>input {
        border: 1px solid #800000;
        border-radius: 5px;
        padding: 0.5rem;
        font-size: 15px;
    }

    .stButton>button {
        background-color: #800000;
        color: white;
        font-weight: 600;
        padding: 0.45rem 1.2rem;
        border-radius: 5px;
    }

    .st-expander {
        background-color: #f9f6f3 !important;
        border: 1px solid #ccc;
        border-radius: 5px;
        margin-top: 1rem;
    }

    .st-expanderHeader {
        font-weight: 600;
        color: #800000;
    }

    a {
        color: #0044cc !important;
        font-weight: 600;
    }

    footer, header, .stDeployButton {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("<h1>Rajagiri College Chatbot</h1>", unsafe_allow_html=True)
st.caption("You may ask about departments, admissions, scholarships, campus activities, or academic policies.")

# ---------------- Session State ----------------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- Chat History ----------------
for h in st.session_state.history:
    with st.chat_message(h["role"]):
        st.markdown(h["content"], unsafe_allow_html=True)

# ---------------- Chat Input ----------------
question = st.chat_input("Enter your query and press Enter…")

if question:
    # Show user message
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Get response
    with st.spinner("Processing your request..."):
        answer, sources = ask_rajagiri_bot(question)

    # Show assistant reply
    st.session_state.history.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

        # Show sources if available
        if sources:
            with st.expander("View Sources"):
                for src in sources:
                    st.markdown(f"- [{src['title']}]({src['link']})")
