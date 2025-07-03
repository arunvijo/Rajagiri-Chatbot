import streamlit as st
from dotenv import load_dotenv
from chatbot import ask_rajagiri_bot

load_dotenv()

st.set_page_config(page_title="Rajagiri College Chatbot", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Merriweather', serif;
        background-color: #fdfdfd;
        color: #000;
    }

    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        font-size: 15px;
        line-height: 1.5;
    }

    .stChatMessage.user {
        background-color: #f1f1f1;
        border-left: 6px solid #800000;
        color: #000000;
    }

    .stChatMessage.assistant {
        background-color: #ffffff;
        border-left: 6px solid #007BFF;
        color: #000000;
    }

    .stButton>button {
        background-color: #800000;
        color: white;
        border-radius: 6px;
        font-weight: bold;
    }

    .stTextInput>div>input {
        border-radius: 6px;
        border: 1px solid #800000;
        padding: 0.5rem;
    }

    .stMarkdown h1 {
        color: #800000;
        font-size: 2.2rem;
        font-weight: bold;
    }

    .stMarkdown a {
        color: #007BFF !important;
        font-weight: bold;
    }

    .st-expander {
        background-color: #f9f9f9 !important;
        border: 1px solid #ccc;
        border-radius: 8px;
    }

    .st-expanderHeader {
        font-weight: bold;
    }

    .block-container {
        padding: 2rem 4rem;
    }
</style>

""", unsafe_allow_html=True)

st.markdown("<h1>🎓 Rajagiri College Chatbot</h1>", unsafe_allow_html=True)
st.caption("Ask me about <b>departments</b>, <b>admissions</b>, <b>scholarships</b>, or <b>campus life</b>!", unsafe_allow_html=True)


# ------------------------------  Session State ------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ------------------------------  Chat History ------------------------------
for h in st.session_state.history:
    with st.chat_message(h["role"]):
        st.markdown(h["content"], unsafe_allow_html=True)

# ------------------------------  Chat Input ------------------------------
question = st.chat_input("Type your question and press Enter…")

if question:
    # Display user input
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Get answer
    with st.spinner("Thinking…"):
        answer, sources = ask_rajagiri_bot(question)

    # Display assistant response
    st.session_state.history.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

        # Sources (collapsible)
        if sources:
            with st.expander("🔍 Show sources"):
                for src in sources:
                    st.markdown(f"- [{src['title']}]({src['link']})")